"""Style statistics per corpus collection, plus the pilot-001 generated pieces for comparison.

Computes omr_lab.style_stats.piece_stats for every .krn file in data/kern/ (see
scripts/fetch_kern_corpus.py) and for the generated samples of experiment 001 (kern through
omr_lab.kern; ABC through music21, which reads ABC reliably), then prints the median of each
statistic per collection. Per-piece results go to outputs/corpus/style_stats.jsonl.

Usage:
    uv run scripts/corpus_style_stats.py
"""

from __future__ import annotations

import json
import sys
from collections import defaultdict
from concurrent.futures import ProcessPoolExecutor
from fractions import Fraction
from pathlib import Path
from statistics import median

import music21

from omr_lab.kern import Barline, KernScore, Note, parse_kern
from omr_lab.style_stats import piece_stats

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "kern"
PILOT = ROOT / "experiments" / "001-gen-abc-vs-kern-pilot" / "samples"
OUT = ROOT / "outputs" / "corpus"

COLUMNS = [  # (header, path into the stats dict, format)
    ("root", ("inversion", "root"), "pct"),
    ("1st", ("inversion", "first"), "pct"),
    ("2nd", ("inversion", "second"), "pct"),
    ("7th", ("seventh_rate",), "pct"),
    ("chg", ("harmonic_change_rate",), "pct"),
    ("NCTw", ("nct_weight_rate",), "pct"),
    ("melNCT", ("melody_nct_rate",), "pct"),
    ("RHsp95", ("hands", "rh_span", "p95"), "num"),
    ("RH>8va", ("hands", "rh_span_over_octave"), "pct"),
    ("LHlp50", ("hands", "lh_leap", "p50"), "num"),
    ("LHlp95", ("hands", "lh_leap", "p95"), "num"),
    ("step", ("hands", "melody_step_rate"), "pct"),
    ("RHchd", ("hands", "rh_chord_rate"), "pct"),
]


def abc_to_score(text: str) -> KernScore:
    """Adapter: music21-parsed ABC -> KernScore (top part = staff 1, next = staff 2)."""
    sc = music21.converter.parse(text, format="abc")
    def real_notes(part):  # chord symbols ("C", "G7") are Chord subclasses: not played notes
        return [n for n in part.flatten().notes if not isinstance(n, music21.harmony.Harmony)]

    parts = [p for p in sc.parts if real_notes(p)]
    score = KernScore()
    for idx, part in enumerate(parts):
        for el in real_notes(part):
            onset = Fraction(el.offset).limit_denominator(1000)
            dur = Fraction(el.duration.quarterLength).limit_denominator(1000)
            tie = None
            if el.tie is not None:
                tie = {"start": "start", "continue": "continue", "stop": "end"}.get(el.tie.type)
            for p in el.pitches:
                score.notes.append(
                    Note(
                        onset,
                        dur,
                        p.midi,
                        p.nameWithOctave,
                        idx,
                        "0",
                        idx + 1,
                        None,
                        None,
                        tie,
                        el.duration.isGrace,
                    )
                )
    if parts:
        for m in parts[0].getElementsByClass("Measure"):
            score.barlines.append(
                Barline(Fraction(m.offset).limit_denominator(1000), m.number, "=")
            )
        for ts in parts[0].recurse().getElementsByClass("TimeSignature"):
            off = Fraction(ts.getOffsetInHierarchy(parts[0])).limit_denominator(1000)
            score.meters.append((off, (ts.numerator, ts.denominator)))
    score.barlines = [b for b in score.barlines if b.onset > 0]
    score.duration = max((n.end for n in score.notes), default=Fraction(0))
    return score


def run(job: tuple[str, str]) -> dict:
    collection, path = job
    text = Path(path).read_text(encoding="utf-8", errors="replace")
    score = abc_to_score(text) if path.endswith(".abc") else parse_kern(text)
    return {"collection": collection, "file": path, "stats": piece_stats(score)}


def get(d: dict | None, path: tuple[str, ...]):
    for k in path:
        if d is None:
            return None
        d = d.get(k)
    return d


def main() -> int:
    manifest = json.loads((DATA / "manifest.json").read_text())
    jobs = [(n, str(p)) for n in manifest for p in sorted((DATA / n).rglob("*.krn"))]
    jobs += [("pilot-kern", str(p)) for p in sorted((PILOT / "kern").glob("*.krn"))]
    jobs += [("pilot-abc", str(p)) for p in sorted((PILOT / "abc").glob("*.abc"))]

    with ProcessPoolExecutor() as pool:
        results = list(pool.map(run, jobs, chunksize=4))
    OUT.mkdir(parents=True, exist_ok=True)
    with (OUT / "style_stats.jsonl").open("w") as fh:
        for r in results:
            fh.write(json.dumps(r) + "\n")

    by_coll: dict[str, list[dict]] = defaultdict(list)
    for r in results:
        by_coll[r["collection"]].append(r["stats"])
    print(f"{'collection':18} {'n':>4} " + " ".join(f"{h:>6}" for h, _, _ in COLUMNS))
    for coll, rows in by_coll.items():
        cells = []
        for _, path, fmt in COLUMNS:
            vals = [v for v in (get(r, path) for r in rows) if v is not None]
            if not vals:
                cells.append(f"{'-':>6}")
                continue
            m = median(vals)
            cells.append(f"{100 * m:5.0f}%" if fmt == "pct" else f"{m:6.1f}")
        print(f"{coll:18} {len(rows):4} " + " ".join(cells))
    print(
        "\nMedians over pieces. pct columns are % of harmonized beats (inversions, 7th, chg),\n"
        "of sounding weight (NCTw), of melody notes (melNCT, step), or of attacks (RH>8va,\n"
        "RHchd). RHsp95: 95th-percentile RH chord span in semitones; LHlp50/95: LH bass leap."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
