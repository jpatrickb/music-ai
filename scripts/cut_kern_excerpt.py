"""Cut a bar range out of a **kern file as a standalone, valid kern score.

The excerpt keeps the exclusive interpretations and the clef, key signature, key, meter and
staff/part assignments in force at the first bar, then the lines from barline `=first` up to
(not including) barline `=last+1`, and closes with a final barline. Comments are dropped. The
start and end must fall where the file has its base spine layout (no *^ split open), which is
checked.

Usage:
    uv run scripts/cut_kern_excerpt.py data/kern/joplin/kern/mapleleaf.krn 1 16 -o out.krn
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

# Tandem interpretations carried into the excerpt header, in this order.
CATEGORIES = [
    ("staff", re.compile(r"^\*staff")),
    ("part", re.compile(r"^\*part")),
    ("instrument", re.compile(r"^\*I[a-z]")),
    ("clef", re.compile(r"^\*clef")),
    ("keysig", re.compile(r"^\*k\[")),
    ("key", re.compile(r"^\*[a-gA-G][#-]?:$")),
    ("meter", re.compile(r"^\*M\d")),
    ("tempo", re.compile(r"^\*MM\d")),
]


class ExcerptError(ValueError):
    pass


def _bar_number(line: str) -> int | None:
    m = re.match(r"^=+(\d+)", line)
    return int(m.group(1)) if m else None


def cut(text: str, first: int, last: int) -> str:
    lines = [ln.rstrip("\r") for ln in text.splitlines()]
    try:
        excl_i = next(i for i, ln in enumerate(lines) if ln.startswith("**"))
    except StopIteration as e:
        raise ExcerptError("no **kern header") from e
    exclusive = lines[excl_i].split("\t")
    n = len(exclusive)
    state: dict[str, list[str]] = {name: ["*"] * n for name, _ in CATEGORIES}

    start = end = None
    for i in range(excl_i + 1, len(lines)):
        ln = lines[i]
        toks = ln.split("\t")
        if start is None and ln.startswith("*") and len(toks) == n:
            for j, tok in enumerate(toks):
                for name, rx in CATEGORIES:
                    if rx.match(tok):
                        state[name][j] = tok
        if ln.startswith("="):
            num = _bar_number(ln)
            if start is None and num == first:
                if len(toks) != n:
                    raise ExcerptError(f"bar {first} starts inside a spine split")
                start = i
            elif start is not None and num is not None and num > last:
                end = i
                break
    if start is None:
        raise ExcerptError(f"bar {first} not found")
    if end is None:
        end = next(
            (i for i in range(len(lines) - 1, start, -1) if lines[i].startswith("==")), len(lines)
        )
    if len(lines[end].split("\t")) != n:
        raise ExcerptError(f"bar {last} ends inside a spine split")

    header = [lines[excl_i]]
    for name, _ in CATEGORIES:
        if any(tok != "*" for tok in state[name]):
            header.append("\t".join(state[name]))
    body = [ln for ln in lines[start:end] if ln and not ln.startswith("!")]
    footer = ["\t".join(["=="] * n), "\t".join(["*-"] * n)]
    return "\n".join(header + body + footer) + "\n"


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    ap.add_argument("path", type=Path)
    ap.add_argument("first", type=int)
    ap.add_argument("last", type=int)
    ap.add_argument("-o", "--out", type=Path)
    args = ap.parse_args(argv)
    out = cut(args.path.read_text(encoding="utf-8", errors="replace"), args.first, args.last)
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(out, encoding="utf-8")
    else:
        sys.stdout.write(out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
