"""Evaluate experiment 002's generated pieces: validity, voice leading, playability, copying,
and descriptive style statistics, per task and arm.

Reads experiments/002-gen-real-excerpts/samples/{A,B}/T{n}-{k}.krn. Copy checks compare every
sample (both arms; arm A never saw the excerpts, so it is the control) against the task's
excerpts, with the composer's other pieces in data/kern/ as the background of common figuration.
Writes per-sample results to outputs/002-gen-real-excerpts/eval.jsonl and prints summaries.

Usage:
    uv run scripts/eval_002.py
"""

from __future__ import annotations

import json
import sys
from collections import defaultdict
from pathlib import Path
from statistics import median

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "experiments" / "generation"))

import harmony_check as hc
import playability_check as pc
import validate_notation as vn

from music_ai.kern import parse_kern
from music_ai.style_stats import piece_stats

EXP = ROOT / "experiments" / "002-gen-real-excerpts"
EXCERPTS = ROOT / "data" / "excerpts" / "002"
KERN = ROOT / "data" / "kern"
OUT = ROOT / "outputs" / "002-gen-real-excerpts"

TASKS = {  # excerpts, background collections, excerpt source files to leave out
    "T1": (
        ["chopin-prelude-op28-4.krn", "chopin-prelude-op28-15.krn"],
        ["chopin-preludes", "chopin-mazurkas"],
        {"prelude28-04.krn", "prelude28-15.krn"},
    ),
    "T2": (
        ["mozart-k545-i.krn", "mozart-k332-i.krn"],
        ["mozart-sonatas"],
        {"sonata15-1.krn", "sonata12-1.krn"},
    ),
    "T3": (
        ["bach-invention-1.krn", "bach-invention-8.krn"],
        ["bach-inventions", "bach-wtc"],
        {"inven01.krn", "inven08.krn"},
    ),
    "T4": (
        ["joplin-maple-leaf.krn", "joplin-entertainer.krn"],
        ["joplin"],
        {"mapleleaf.krn", "entertainer.krn"},
    ),
}


def load(path: Path):
    return parse_kern(path.read_text(encoding="utf-8", errors="replace"))


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    rows = []
    for task, (ex_names, bg_colls, exclude) in TASKS.items():
        excerpts = {n: load(EXCERPTS / n) for n in ex_names}
        bg_files = [
            f for c in bg_colls for f in sorted((KERN / c).rglob("*.krn")) if f.name not in exclude
        ]
        background = pc.background_ngrams([load(f) for f in bg_files])
        for arm in ("A", "B"):
            for path in sorted((EXP / "samples" / arm).glob(f"{task}-*.krn")):
                text = path.read_text(encoding="utf-8")
                score_v = vn.Score("kern", text, str(path))
                v = vn.validate(score_v, None, 0)
                rep = hc.check_score(score_v)
                ks = parse_kern(text)
                play = pc.check_score(ks, excerpts, background)
                bars = max((b.number or 0 for b in ks.barlines), default=0)
                rows.append(
                    {
                        "task": task,
                        "arm": arm,
                        "file": path.name,
                        "valid": not v.errors,
                        "errors": v.errors,
                        "bars": bars,
                        "harmony": {
                            s: sum(f.severity == s for f in rep.findings)
                            for s in ("high", "medium", "low")
                        },
                        "harmony_error": rep.error,
                        "play": [str(f) for f in play if f.check != "copy"],
                        "play_high": sum(f.severity == "high" for f in play if f.check != "copy"),
                        "copy": [f.reason for f in play if f.check == "copy"],
                        "copy_high": sum(f.severity == "high" for f in play if f.check == "copy"),
                        "stats": piece_stats(ks),
                    }
                )
    with (OUT / "eval.jsonl").open("w") as fh:
        for r in rows:
            fh.write(json.dumps(r) + "\n")

    print(
        f"{'sample':10} {'ok':3} {'bars':>4} {'harm h/m/l':>10} {'play hi':>7} {'copy hi':>7}"
        f" {'root':>5} {'1st':>4} {'NCTw':>5} {'melNCT':>6}"
    )
    for r in rows:
        s, h = r["stats"], r["harmony"]
        print(
            f"{r['arm']}-{r['file'][:-4]:8} {'✓' if r['valid'] else '✗':3} {r['bars']:4}"
            f" {h['high']:>3}/{h['medium']}/{h['low']:<4} {r['play_high']:7} {r['copy_high']:7}"
            f" {100 * (s['inversion']['root'] or 0):4.0f}% {100 * (s['inversion']['first'] or 0):3.0f}%"
            f" {100 * (s['nct_weight_rate'] or 0):4.0f}% {100 * (s.get('melody_nct_rate') or 0):5.0f}%"
        )

    print("\nMedians per task and arm (descriptive only, not quality):")
    groups = defaultdict(list)
    for r in rows:
        groups[(r["task"], r["arm"])].append(r["stats"])
    for (task, arm), ss in sorted(groups.items()):

        def med(f, ss=ss):
            vals = [f(s) for s in ss if f(s) is not None]
            return 100 * median(vals) if vals else float("nan")

        print(
            f"  {task} {arm}: root {med(lambda s: s['inversion']['root']):3.0f}%  "
            f"NCT weight {med(lambda s: s['nct_weight_rate']):3.0f}%  "
            f"melody NCT {med(lambda s: s.get('melody_nct_rate')):3.0f}%  "
            f"7th {med(lambda s: s['seventh_rate']):3.0f}%"
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
