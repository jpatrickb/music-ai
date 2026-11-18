"""My feedback on generated music, stored as training/evaluation data.

Three append-only JSONL tables live in ``feedback/`` at the repo root (see its README):

- ``generations.jsonl``: one record per generated piece: what was asked, what context and model
  produced it, and where the output file is.
- ``ratings.jsonl``: a rater's scores and written notes on one generation.
- ``preferences.jsonl``: a rater's pick among a set of generations for the same brief (the shape
  preference-learning methods such as DPO or a reward model train on).

Records refer to generations by ``id`` (e.g. ``"002/B/T1-1"``). :func:`check` verifies the
references and score ranges, so a broken import fails loudly instead of corrupting the data.

The written notes on ratings are kept out of git: pass ``notes_dir`` (the scripts use the
gitignored ``data/feedback/``) and :func:`save` writes them to ``rating-notes.jsonl`` there,
leaving ``notes`` empty in the tracked table; :func:`load` merges them back when that file exists.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field, fields
from pathlib import Path
from typing import Any

SCORE_MIN, SCORE_MAX = 1, 5
TABLES = {
    "generations": "generations.jsonl",
    "ratings": "ratings.jsonl",
    "preferences": "preferences.jsonl",
}
NOTES_FILE = "rating-notes.jsonl"  # in notes_dir; keyed like ratings by (generation, rater, source)


@dataclass
class Generation:
    id: str  # "<experiment>/<arm>/<task>-<k>", unique
    experiment: str  # experiment folder name, e.g. "002-gen-real-excerpts"
    task: str
    arm: str
    output: str  # repo-relative path of the generated file as it is now
    brief: str
    context: list[str]  # repo-relative files the generator read
    prompt: str | None  # repo-relative path of the prompt template (None: not recorded)
    model: str
    generator: str  # how it was run, e.g. "claude-code-teammate"
    created: str  # ISO date
    commit: str  # code/context commit it ran from ("+dirty" if uncommitted changes)
    fmt: str = "kern"
    as_generated: str | None = None  # path of the original if `output` was corrected later
    edits: str | None = None  # what changed between as_generated and output, and why


@dataclass
class Rating:
    generation: str
    rater: str
    created: str
    scores: dict[str, int]  # e.g. {"brief": 4, "musicality": 3, "playability": 5}, 1-5
    notes: str = ""
    blind: bool = True
    heard: str | None = None  # path of the version actually judged, if not `output`
    source: str = ""  # where it was collected, e.g. "judging page 002"


@dataclass
class Preference:
    candidates: list[str]  # generation ids shown together, same brief
    chosen: str
    rater: str
    created: str
    blind: bool = True
    source: str = ""


@dataclass
class Feedback:
    generations: list[Generation] = field(default_factory=list)
    ratings: list[Rating] = field(default_factory=list)
    preferences: list[Preference] = field(default_factory=list)


_TYPES = {"generations": Generation, "ratings": Rating, "preferences": Preference}


def _from_dict(cls: type, d: dict[str, Any]) -> Any:
    names = {f.name for f in fields(cls)}
    unknown = set(d) - names
    if unknown:
        raise ValueError(f"{cls.__name__}: unknown fields {sorted(unknown)}")
    return cls(**d)


def _note_key(d: dict[str, Any] | Rating) -> tuple[str, str, str]:
    if isinstance(d, Rating):
        return (d.generation, d.rater, d.source)
    return (d["generation"], d["rater"], d.get("source", ""))


def load(directory: Path, notes_dir: Path | None = None) -> Feedback:
    """Read all three tables (missing files count as empty), plus the rating notes in
    ``notes_dir`` if given and present."""
    fb = Feedback()
    for table, name in TABLES.items():
        path = directory / name
        if not path.exists():
            continue
        rows = getattr(fb, table)
        for n, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            if line.strip():
                try:
                    rows.append(_from_dict(_TYPES[table], json.loads(line)))
                except (ValueError, TypeError) as e:
                    raise ValueError(f"{path}:{n}: {e}") from e
    notes_path = notes_dir / NOTES_FILE if notes_dir is not None else None
    if notes_path is not None and notes_path.exists():
        by_key = {_note_key(r): r for r in fb.ratings}
        for n, line in enumerate(notes_path.read_text(encoding="utf-8").splitlines(), 1):
            if line.strip():
                d = json.loads(line)
                rating = by_key.get(_note_key(d))
                if rating is None:
                    raise ValueError(f"{notes_path}:{n}: notes for unknown rating {_note_key(d)}")
                rating.notes = d["notes"]
    return fb


def _write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    lines = [json.dumps(r, ensure_ascii=False) for r in rows]
    path.write_text("".join(x + "\n" for x in lines), encoding="utf-8")


def save(fb: Feedback, directory: Path, notes_dir: Path | None = None) -> None:
    """Write all three tables, one JSON object per line, in a stable order. With ``notes_dir``,
    rating notes go to ``notes_dir / NOTES_FILE`` instead of the ratings table."""
    directory.mkdir(parents=True, exist_ok=True)
    for table, name in TABLES.items():
        rows = [asdict(r) for r in getattr(fb, table)]
        if table == "ratings" and notes_dir is not None:
            for row in rows:
                row["notes"] = ""
        _write_jsonl(directory / name, rows)
    if notes_dir is not None:
        notes_dir.mkdir(parents=True, exist_ok=True)
        notes = [
            {"generation": r.generation, "rater": r.rater, "source": r.source, "notes": r.notes}
            for r in fb.ratings
            if r.notes
        ]
        _write_jsonl(notes_dir / NOTES_FILE, notes)


def check(fb: Feedback, root: Path | None = None) -> list[str]:
    """Problems with the data: duplicate ids, dangling references, out-of-range scores, and (if
    ``root`` is given) files that don't exist. Paths under ``data/`` are skipped: that directory is
    gitignored and rebuilt by scripts (e.g. excerpts cut at run time). Empty list = OK."""
    problems: list[str] = []
    ids: set[str] = set()
    for g in fb.generations:
        if g.id in ids:
            problems.append(f"duplicate generation id {g.id}")
        ids.add(g.id)
        if root is not None:
            for p in (g.output, g.as_generated, g.prompt, *g.context):
                if p and not p.startswith("data/") and not (root / p).exists():
                    problems.append(f"{g.id}: missing file {p}")
    seen: set[tuple[str, str, str]] = set()
    for r in fb.ratings:
        if r.generation not in ids:
            problems.append(f"rating of unknown generation {r.generation}")
        key = (r.generation, r.rater, r.source)
        if key in seen:
            problems.append(f"duplicate rating {key}")
        seen.add(key)
        for k, v in r.scores.items():
            if not isinstance(v, int) or not SCORE_MIN <= v <= SCORE_MAX:
                problems.append(f"rating of {r.generation}: {k}={v!r} not in 1-5")
        if root is not None and r.heard and not (root / r.heard).exists():
            problems.append(f"rating of {r.generation}: missing file {r.heard}")
    for p in fb.preferences:
        for c in p.candidates:
            if c not in ids:
                problems.append(f"preference over unknown generation {c}")
        if p.chosen not in p.candidates:
            problems.append(f"preference choice {p.chosen} not among its candidates")
    return problems
