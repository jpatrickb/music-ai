"""Evaluate experiment 003's hymn arrangements: validity, voice leading, playability, copying from
the texture excerpts, melody fidelity (is the tune there, how often, in which keys, on top?), and
descriptive style statistics.

Reads experiments/003-gen-hymn-arrangements/samples/H{n}-{k}.krn. Renders are judged with beams
added (music_ai.kern_beam), so checks run on the beamed text too (beaming never changes notes).
Writes per-sample results to outputs/003-gen-hymn-arrangements/eval.jsonl and prints a summary.

Usage:
    uv run scripts/eval_003.py
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

from music_ai import harmony_check as hc
from music_ai import playability_check as pc
from music_ai import validate_notation as vn
from music_ai.kern import parse_kern
from music_ai.kern_beam import add_beams
from music_ai.melody_fidelity import extract_melody, find_statements
from music_ai.style_stats import piece_stats

EXP = ROOT / "experiments" / "003-gen-hymn-arrangements"
SOURCES = ROOT / "experiments" / "generation" / "sources" / "hymns"
EXCERPTS = ROOT / "data" / "excerpts" / "003"
KERN = ROOT / "data" / "kern"
OUT = ROOT / "outputs" / "003-gen-hymn-arrangements"
HYMNS = {
    "H1": "adeste-fideles",
    "H2": "mendelssohn",
    "H3": "antioch",
    "H4": "stille-nacht",
    "H5": "the-first-nowell",
}
EXCLUDE = {"prelude28-17.krn", "prelude28-13.krn"}  # excerpt sources, not background


def seconds(text: str, quarters: float) -> float | None:
    m = re.search(r"^\*MM(\d+(?:\.\d+)?)", text, re.MULTILINE)
    return round(quarters * 60 / float(m.group(1))) if m else None


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    excerpts = {p.name: parse_kern(p.read_text()) for p in sorted(EXCERPTS.glob("*.krn"))}
    bg_files = [
        f
        for c in ("chopin-preludes", "chopin-mazurkas")
        for f in sorted((KERN / c).rglob("*.krn"))
        if f.name not in EXCLUDE
    ]
    background = pc.background_ngrams([parse_kern(f.read_text(errors="replace")) for f in bg_files])
    rows = []
    for task, slug in HYMNS.items():
        melody = extract_melody(parse_kern((SOURCES / f"{slug}.krn").read_text()))
        for path in sorted((EXP / "samples").glob(f"{task}-*.krn")):
            text = add_beams(path.read_text(encoding="utf-8"))
            score_v = vn.Score("kern", text, str(path))
            v = vn.validate(score_v, None, 0)
            row: dict = {
                "task": task,
                "file": path.name,
                "valid": not v.errors,
                "errors": v.errors[:10],
            }
            try:
                ks = parse_kern(text)
            except Exception as e:  # noqa: BLE001 (report and keep going)
                row["parse_error"] = f"{type(e).__name__}: {e}"
                rows.append(row)
                continue
            rep = hc.check_score(score_v)
            play = pc.check_score(ks, excerpts, background)
            statements = find_statements(melody, ks)
            row.update(
                bars=max((b.number or 0 for b in ks.barlines), default=0),
                seconds=seconds(text, float(ks.duration)),
                harmony={
                    s: sum(f.severity == s for f in rep.findings) for s in ("high", "medium", "low")
                },
                harmony_error=rep.error,
                play=[str(f) for f in play if f.check != "copy"],
                play_high=sum(f.severity == "high" for f in play if f.check != "copy"),
                copy=[f.reason for f in play if f.check == "copy"],
                statements=[
                    {
                        "bar": s.bar,
                        "transposition": s.transposition,
                        "coverage": round(s.coverage, 2),
                        "top": round(s.top_coverage, 2),
                    }
                    for s in statements
                ],
                stats=piece_stats(ks),
            )
            rows.append(row)
    with (OUT / "eval.jsonl").open("w") as fh:
        for r in rows:
            fh.write(json.dumps(r) + "\n")

    print(
        f"{'sample':8} {'ok':3} {'bars':>4} {'sec':>4} {'harm h/m/l':>10} {'play hi':>7}  statements"
    )
    for r in rows:
        if "parse_error" in r:
            print(f"{r['file'][:-4]:8} parse error: {r['parse_error']}")
            continue
        h = r["harmony"]
        st = ", ".join(
            f"b{s['bar']}{'+' + str(s['transposition']) if s['transposition'] else ''}"
            f" {s['coverage']:.0%}/{s['top']:.0%}"
            for s in r["statements"]
        )
        print(
            f"{r['file'][:-4]:8} {'✓' if r['valid'] else '✗':3} {r['bars']:4} {r['seconds'] or '-':>4}"
            f" {h['high']:>3}/{h['medium']}/{h['low']:<4} {r['play_high']:7}  {st or 'none'}"
        )
        for e in r["errors"][:3]:
            print("    error:", e)
    return 0


if __name__ == "__main__":
    sys.exit(main())
