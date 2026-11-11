"""Record experiment 003 in feedback/: its generations, and (after judging) the ratings and
preferences exported from the judging page.

Re-running replaces 003's records, so it is safe to run once after generation and again after
judging. The judging page stores each rating under the generation id (``003/A/H1-1``) with
scores 1-5 for brief / musicality / playability, plus ``difficulty`` (1-5, descriptive) and
``wouldPlay`` (yes / fixes / no), which go into the rating's scores and notes respectively.

Usage:
    uv run scripts/record_003.py [--db DIR]   # DIR holds ratings/*.json and prefs/*.json
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from music_ai.feedback import Generation, Preference, Rating, check, load, save

ROOT = Path(__file__).resolve().parents[1]
EXP = "003-gen-hymn-arrangements"
GEN = "experiments/generation"
HYMNS = {
    "H1": ("O Come, All Ye Faithful", "adeste-fideles", "G major"),
    "H2": ("Hark! The Herald Angels Sing", "mendelssohn", "F major"),
    "H3": ("Joy to the World", "antioch", "D major"),
    "H4": ("Silent Night", "stille-nacht", "B-flat major"),
    "H5": ("The First Noel", "the-first-nowell", "D major"),
}
BRIEF = (
    'An advanced solo-piano arrangement of "{t}" from the hymnal setting above. About 2–3 minutes '
    "at your chosen tempo: an introduction, at least two complete statements of the tune with the "
    "second clearly varied in texture and harmony, an optional key change before the last "
    "statement, and an ending. Keep the tune's notes and rhythm recognisable and mostly on top. "
    "Start in the hymnal's key ({k}). Write for an advanced amateur pianist who will practise it: "
    "noticeably more demanding and richer than the hymnal setting, with flowing accompaniment and "
    "a full texture at the climax, but idiomatic and comfortable under the hands."
)
CONTEXT = [
    f"{GEN}/encoding/kern-reference.md",
    f"{GEN}/arranging/01-hymn-arrangement.md",
    f"{GEN}/theory/01-voice-leading-fundamentals.md",
    f"{GEN}/theory/02-cadences-and-substitutions.md",
    f"{GEN}/theory/03-secondary-dominants.md",
    f"{GEN}/theory/04-borrowed-chords-modal-mixture.md",
    f"{GEN}/theory/05-pivot-chord-modulation.md",
    f"{GEN}/styles/01-baroque-classical-romantic.md",
]
EXCERPTS = [
    "data/excerpts/003/chopin-prelude-op28-17.krn",
    "data/excerpts/003/chopin-prelude-op28-13.krn",
]
SCORES = ("brief", "musicality", "playability", "difficulty")
SOURCE = "judging page 003"


def generations() -> list[Generation]:
    out = []
    for path in sorted((ROOT / "experiments" / EXP / "samples").glob("H*-*.krn")):
        task = path.stem.split("-")[0]
        title, slug, key = HYMNS[task]
        out.append(
            Generation(
                id=f"003/A/{path.stem}",
                experiment=EXP,
                task=task,
                arm="A",
                output=str(path.relative_to(ROOT)),
                brief=BRIEF.format(t=title, k=key),
                context=[*CONTEXT, f"{GEN}/sources/hymns/{slug}.krn", *EXCERPTS],
                prompt=f"experiments/{EXP}/prompt.md",
                model="claude-opus-5-5",
                generator="claude-code-teammate",
                created="2026-11-10",
                commit="70af713+dirty",
            )
        )
    return out


def judging(db: Path) -> tuple[list[Rating], list[Preference]]:
    ratings, prefs = [], []
    for p in sorted((db / "ratings").glob("*.json")):
        d = json.loads(p.read_text())
        notes = d.get("notes", "")
        if d.get("wouldPlay"):
            notes = f"[would play: {d['wouldPlay']}] {notes}".strip()
        scores = {k: d[k] for k in SCORES if d.get(k) is not None}
        ratings.append(
            Rating(
                d["generation"],
                "owner",
                d["updatedAt"][:10],
                scores,
                notes,
                blind=False,
                source=SOURCE,
            )
        )
    for p in sorted((db / "prefs").glob("*.json")):
        d = json.loads(p.read_text())
        if d.get("chosen"):
            prefs.append(
                Preference(
                    [d["order"][s] for s in sorted(d["order"])],
                    d["chosen"],
                    "owner",
                    d["updatedAt"][:10],
                    blind=False,
                    source=SOURCE,
                )
            )
    return ratings, prefs


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--db", type=Path)
    args = ap.parse_args(argv)
    fb = load(ROOT / "feedback")
    fb.generations = [g for g in fb.generations if g.experiment != EXP] + generations()
    if args.db:
        ratings, prefs = judging(args.db)
        fb.ratings = [r for r in fb.ratings if r.source != SOURCE] + ratings
        fb.preferences = [p for p in fb.preferences if p.source != SOURCE] + prefs
    problems = check(fb, ROOT)
    for p in problems:
        print("problem:", p, file=sys.stderr)
    if problems:
        return 1
    save(fb, ROOT / "feedback")
    n = sum(g.experiment == EXP for g in fb.generations)
    print(
        f"003: {n} generations; feedback/ now {len(fb.generations)} generations, "
        f"{len(fb.ratings)} ratings, {len(fb.preferences)} preferences"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
