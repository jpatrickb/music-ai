"""One-off: build feedback/ from the blind-judging exports of experiments 001 and 002.

The judging pages kept ratings in their own databases; export each page's ``ratings`` and
``prefs`` collections as JSON files (one file per document, e.g. ``<dir>/ratings/T1-A.json``) and
pass the export directories. Generation metadata (briefs, context files, commits) comes from the
two experiment READMEs and is written out here. Later experiments write their generations at run
time and their judging pages store generation ids directly, so they won't need this.

Usage:
    uv run scripts/backfill_feedback.py --db001 DIR --db002 DIR
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from omr_lab.feedback import Feedback, Generation, Preference, Rating, check, save

ROOT = Path(__file__).resolve().parents[1]
GEN = "experiments/generation"
MODEL = "claude-opus-5-5"
GENERATOR = "claude-code-teammate"  # one fresh agent per piece, no code execution
RATER = "owner"

E1 = "001-gen-abc-vs-kern-pilot"
TASKS_001 = {  # brief, theory/style context (besides the format's encoding reference)
    "T1": (
        (
            "8 bars, C major, 4/4, keyboard style (RH 3-note chords, LH bass). A deceptive cadence "
            "(V7–vi) at bar 4, then an authentic cadence I–IV–I6/4–V7–I to end. Roman-numeral "
            "analysis."
        ),
        ["theory/01-voice-leading-fundamentals.md", "theory/02-cadences-and-substitutions.md"],
    ),
    "T2": (
        (
            "8 bars, G major, 3/4, keyboard style. Use V7/V and V7/vi, each resolving correctly; end "
            "with a PAC. Roman-numeral analysis."
        ),
        ["theory/01-voice-leading-fundamentals.md", "theory/03-secondary-dominants.md"],
    ),
    "T3": (
        (
            "16 bars, A-flat major, 4/4, Romantic style (melody over arpeggiated LH). Modulate to C "
            "major by common-tone modulation around bar 8; final cadence in C uses a German "
            "augmented sixth."
        ),
        [
            "theory/01-voice-leading-fundamentals.md",
            "theory/06-common-tone-modulation.md",
            "theory/07-augmented-sixth-chords.md",
            "styles/01-baroque-classical-romantic.md",
        ],
    ),
    "T4": (
        (
            "12-bar blues in F, 4/4, stride piano (LH bass note / chord alternation, RH blues melody "
            "with blue notes), standard 12-bar form, swing feel."
        ),
        ["styles/03-ragtime-blues-stride.md"],
    ),
}

E2 = "002-gen-real-excerpts"
T01, T02, T03 = (
    "theory/01-voice-leading-fundamentals.md",
    "theory/02-cadences-and-substitutions.md",
    "theory/03-secondary-dominants.md",
)
TASKS_002 = {  # brief, context (both arms), excerpts (arm B only)
    "T1": (
        (
            "A Romantic piano prelude in G minor in the style of Chopin's Preludes Op. 28, 16–24 "
            "bars, any meter. One main idea and one consistent accompaniment texture throughout, a "
            "singing melody over the left hand, expressive chromatic harmony, and a clear final "
            "authentic cadence in G minor."
        ),
        [
            T01,
            T03,
            "theory/04-borrowed-chords-modal-mixture.md",
            "styles/01-baroque-classical-romantic.md",
        ],
        ["chopin-prelude-op28-4.krn", "chopin-prelude-op28-15.krn"],
    ),
    "T2": (
        (
            "The exposition of a Classical piano sonata first movement in D major in the style of "
            "Mozart, 28–40 bars, 4/4. First theme in D major, a transition that modulates, a second "
            "theme in A major, and a closing section ending with a perfect authentic cadence in A "
            "major. Use typical Classical accompaniment figures (e.g. Alberti bass)."
        ),
        [
            T01,
            T02,
            T03,
            "theory/05-pivot-chord-modulation.md",
            "styles/01-baroque-classical-romantic.md",
        ],
        ["mozart-k545-i.krn", "mozart-k332-i.krn"],
    ),
    "T3": (
        (
            "A two-part invention in E minor in the style of J. S. Bach, 14–20 bars, 4/4. Two "
            "independent contrapuntal voices (one per hand), built on a short subject stated in one "
            "voice and imitated in the other, with sequences and a cadence in a related key (e.g. G "
            "major or B minor) before returning to end in E minor."
        ),
        [T01, "styles/01-baroque-classical-romantic.md"],
        ["bach-invention-1.krn", "bach-invention-8.krn"],
    ),
    "T4": (
        (
            "A classic piano rag in F major in the style of Scott Joplin, 2/4: a 4-bar introduction, "
            "a 16-bar A strain and a 16-bar B strain (36 bars; write out any repeats). Left hand in "
            "the oom-pah pattern (bass note or octave on the beat, chord on the off-beat), right "
            "hand syncopated, with chromatic passing tones and a secondary dominant."
        ),
        [T01, T03, "styles/03-ragtime-blues-stride.md"],
        ["joplin-maple-leaf.krn", "joplin-entertainer.krn"],
    ),
}
CORRECTED_002 = {  # fixed after judging; the rating applies to the as-generated version
    "A/T1-3": "2 notes",
    "B/T2-2": "40 notes",
}


def docs(directory: Path) -> list[dict]:
    return [json.loads(p.read_text()) for p in sorted(directory.glob("*.json"))]


def scores(d: dict) -> dict[str, int]:
    return {k: d[k] for k in ("brief", "musicality", "playability") if d.get(k) is not None}


def backfill_001(fb: Feedback, db: Path) -> None:
    for task, (brief, ctx) in TASKS_001.items():
        for fmt, ext in (("abc", "abc"), ("kern", "krn")):
            fb.generations.append(
                Generation(
                    id=f"001/{fmt}/{task}",
                    experiment=E1,
                    task=task,
                    arm=fmt,
                    output=f"experiments/{E1}/samples/{fmt}/{task}.{ext}",
                    brief=brief,
                    context=[f"{GEN}/encoding/{fmt}-reference.md", *(f"{GEN}/{c}" for c in ctx)],
                    prompt=None,
                    model=MODEL,
                    generator=GENERATOR,
                    created="2026-11-09",
                    commit="c4b9e42+dirty",
                    fmt=fmt,
                )
            )
    for d in docs(db / "ratings"):
        fb.ratings.append(
            Rating(
                f"001/{d['format']}/{d['task']}",
                RATER,
                d["updatedAt"][:10],
                scores(d),
                d.get("notes", ""),
                source="judging page 001",
            )
        )
    for d in docs(db / "prefs"):
        order, task = d["order"], d["task"]
        fb.preferences.append(
            Preference(
                [f"001/{order[s]}/{task}" for s in sorted(order)],
                f"001/{order[d['choice']]}/{task}",
                RATER,
                d["updatedAt"][:10],
                source="judging page 001",
            )
        )


def backfill_002(fb: Feedback, db: Path) -> None:
    exp = f"experiments/{E2}"
    for task, (brief, ctx, excerpts) in TASKS_002.items():
        for arm in ("A", "B"):
            context = [f"{GEN}/encoding/kern-reference.md", *(f"{GEN}/{c}" for c in ctx)]
            if arm == "B":  # cut at run time from data/kern (gitignored; see the 002 README)
                context += [f"data/excerpts/002/{x}" for x in excerpts]
            for k in (1, 2, 3):
                key = f"{arm}/{task}-{k}"
                fixed = CORRECTED_002.get(key)
                fb.generations.append(
                    Generation(
                        id=f"002/{key}",
                        experiment=E2,
                        task=task,
                        arm=arm,
                        output=f"{exp}/samples/{key}.krn",
                        brief=brief,
                        context=context,
                        prompt=f"{exp}/prompt.md",
                        model=MODEL,
                        generator=GENERATOR,
                        created="2026-11-10",
                        commit="d42233b+dirty",
                        as_generated=f"{exp}/samples/as-generated/{arm}-{task}-{k}.krn"
                        if fixed
                        else None,
                        edits=f"pitch spelling fixed after judging ({fixed}): f#f# -> ff#, "
                        "g#g# -> gg#, cc#cc# -> ccc#"
                        if fixed
                        else None,
                    )
                )
    by_id = {g.id: g for g in fb.generations}
    for d in docs(db / "ratings"):
        arm, rest = d["sample"].split("-", 1)  # "A-T1-1"
        gid = f"002/{arm}/{rest}"
        fb.ratings.append(
            Rating(
                gid,
                RATER,
                d["updatedAt"][:10],
                scores(d),
                d.get("notes", ""),
                heard=by_id[gid].as_generated,
                source="judging page 002",
            )
        )
    for d in docs(db / "prefs"):
        ids = [f"002/{s.replace('-', '/', 1)}" for _, s in sorted(d["order"].items())]
        fb.preferences.append(
            Preference(
                ids,
                f"002/{d['preferredSample'].replace('-', '/', 1)}",
                RATER,
                d["updatedAt"][:10],
                source="judging page 002",
            )
        )


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--db001", type=Path, required=True)
    ap.add_argument("--db002", type=Path, required=True)
    ap.add_argument("--out", type=Path, default=ROOT / "feedback")
    args = ap.parse_args(argv)
    fb = Feedback()
    backfill_001(fb, args.db001)
    backfill_002(fb, args.db002)
    problems = check(fb, ROOT)
    for p in problems:
        print("problem:", p, file=sys.stderr)
    if problems:
        return 1
    save(fb, args.out)
    print(
        f"{len(fb.generations)} generations, {len(fb.ratings)} ratings, "
        f"{len(fb.preferences)} preferences -> {args.out}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
