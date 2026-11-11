"""Map where an arrangement states each phrase of an original tune (see music_ai.melody_map).

Usage:
    uv run scripts/melody_map.py ORIGINAL.krn ARRANGEMENT.krn [--staff N] [--control OTHER.krn]

``transp`` is semitones up from the original's key (0-11), not a key name. ``--staff`` is the
original's staff holding the tune (1 = top staff: the voice in a song, the
soprano in a hymn). ``--control`` searches the same phrases in an unrelated piece, to show how
much coverage arises by chance.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from music_ai.kern import parse_kern
from music_ai.melody_map import map_phrases, melody_line, split_phrases


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("original", type=Path)
    ap.add_argument("arrangement", type=Path)
    ap.add_argument("--staff", type=int, default=1)
    ap.add_argument("--min-coverage", type=float, default=0.8)
    ap.add_argument("--min-shape", type=float, default=0.75)
    ap.add_argument("--min-evidence", type=float, default=60.0)
    ap.add_argument("--control", type=Path)
    args = ap.parse_args(argv)
    orig = parse_kern(args.original.read_text(encoding="utf-8"))
    phrases = split_phrases(melody_line(orig, args.staff))
    print(f"{args.original.stem}: {len(phrases)} phrases")
    for ph in phrases:
        names = " ".join(str(m.midi) for m in ph.notes[:8])
        print(
            f"  P{ph.index}: {len(ph.notes)} notes ({names}{' ...' if len(ph.notes) > 8 else ''})"
        )
    for target in [args.arrangement] + ([args.control] if args.control else []):
        arr = parse_kern(target.read_text(encoding="utf-8"))
        matches = map_phrases(
            phrases,
            arr,
            min_coverage=args.min_coverage,
            min_shape=args.min_shape,
            min_evidence=args.min_evidence,
        )
        print(f"\n{target.stem}: {len(matches)} phrase statements")
        print("  bars      phrase  scale  transp  staff  register  position  coverage  shape  bits")
        for m in matches:
            scale = {0.5: "x1/2", 1.0: "x1", 2.0: "x2"}[float(m.scale)]
            print(
                f"  {m.bar:>3}-{m.last_bar:<4}  P{m.phrase:<5} {scale:<6} +{m.transposition:<2}st   "
                f"{m.staff!s:<5}  {m.register:>4}      {m.position:<8}  "
                f"{m.coverage:>6.0%}  {m.shape:>6.0%}  {m.evidence:>4.0f}"
            )
    return 0


if __name__ == "__main__":
    sys.exit(main())
