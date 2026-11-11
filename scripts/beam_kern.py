"""Add beams (L/J) to **kern files that have none; see music_ai.kern_beam.

Usage:
    uv run scripts/beam_kern.py FILE... [--in-place]   # default: print to stdout
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from music_ai.kern_beam import add_beams


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("paths", nargs="+", type=Path)
    ap.add_argument("--in-place", action="store_true")
    args = ap.parse_args(argv)
    for p in args.paths:
        out = add_beams(p.read_text(encoding="utf-8"))
        if args.in_place:
            p.write_text(out, encoding="utf-8")
        else:
            sys.stdout.write(out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
