"""Cross-check omr_lab.kern against music21 on corpus files that music21 reads correctly.

For each file that passed the validator (outputs/corpus/validation.jsonl, from
scripts/corpus_report.py), compares the multiset of (onset, MIDI pitch) for all pitched,
non-grace notes from both readers. Tied notes are compared unmerged (music21 keeps them
separate too). Also reports parse failures and warnings from omr_lab.kern across all files.

Usage:
    uv run scripts/crosscheck_kern_reader.py
"""

from __future__ import annotations

import json
import sys
from collections import Counter
from concurrent.futures import ProcessPoolExecutor
from fractions import Fraction
from pathlib import Path

import music21

from omr_lab.kern import KernError, parse_kern

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "kern"


def ours(text: str) -> Counter:
    s = parse_kern(text)
    return Counter((Fraction(n.onset), n.midi) for n in s.pitched())


def theirs(text: str) -> Counter:
    sc = music21.converter.parse(text, format="humdrum")
    c: Counter = Counter()
    for el in sc.flatten().notes:
        if el.duration.isGrace:
            continue
        off = Fraction(el.offset).limit_denominator(10_000)
        for p in el.pitches:
            c[(off, p.midi)] += 1
    return c


def compare(rel: str) -> dict:
    text = (DATA / rel).read_text(encoding="utf-8", errors="replace")
    a, b = ours(text), theirs(text)
    ours_clean = not parse_kern(text).warnings
    only_a, only_b = a - b, b - a
    return {
        "file": rel,
        "match": not only_a and not only_b,
        "notes": sum(b.values()),
        "only_ours": sorted(only_a.items())[:3],
        "only_music21": sorted(only_b.items())[:3],
        "n_diff": sum(only_a.values()) + sum(only_b.values()),
        "ours_clean": ours_clean,
    }


def parse_all(rel: str) -> dict:
    text = (DATA / rel).read_text(encoding="utf-8", errors="replace")
    try:
        s = parse_kern(text)
    except KernError as e:
        return {"file": rel, "error": str(e), "warnings": []}
    return {"file": rel, "error": None, "warnings": s.warnings}


def main() -> int:
    rows = [json.loads(line) for line in (ROOT / "outputs/corpus/validation.jsonl").open()]
    passing = [r["file"] for r in rows if r["ok"]]
    with ProcessPoolExecutor() as pool:
        results = list(pool.map(compare, passing, chunksize=4))
        parsed = list(pool.map(parse_all, [r["file"] for r in rows], chunksize=8))

    bad = [r for r in results if not r["match"]]
    total = sum(r["notes"] for r in results)
    print(f"music21-valid files: {len(results)}, notes compared: {total}")
    print(f"files where the readers disagree: {len(bad)}")
    clean = sum(r["ours_clean"] for r in bad)
    print(f"  of those, omr_lab.kern timing is self-consistent (no warnings) in {clean}")
    for r in sorted(bad, key=lambda r: -r["n_diff"])[:15]:
        print(f"  {r['file']}: {r['n_diff']} diffs; ours {r['only_ours']} m21 {r['only_music21']}")

    errs = [p for p in parsed if p["error"]]
    warned = [p for p in parsed if p["warnings"]]
    print(f"\nall {len(parsed)} files: {len(errs)} structural errors, {len(warned)} with warnings")
    for p in errs[:10]:
        print(f"  ERROR {p['file']}: {p['error']}")
    kinds = Counter(
        w.split(": ", 1)[1].split(" at ")[0][:50] for p in warned for w in p["warnings"]
    )
    for k, c in kinds.most_common(8):
        print(f"  warning ×{c}: {k}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
