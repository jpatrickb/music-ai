"""Repairs for known bugs in humlib's ``musicxml2hum`` output.

With a tempo text at the start of a multi-staff score, ``musicxml2hum`` can write a short
exclusive-interpretation line (``**kern **dynam`` over four data columns), or drop the opening
``*^`` when a staff starts with two voices. ``repair`` fixes both, inferring the split spine from
the first later merge, and raises when it can't tell.
"""

from __future__ import annotations


def repair(text: str) -> str:
    """Apply all repairs; text without these problems comes back unchanged."""
    return repair_header(text)


def repair_header(text: str) -> str:
    """Pad a short ``**`` line to the width of the line after it (see module docstring)."""
    lines = text.split("\n")
    i = next(i for i, ln in enumerate(lines) if ln.startswith("**"))
    head = lines[i].split("\t")
    width = len(lines[i + 1].split("\t"))
    if len(head) < width:
        kern = [h for h in head if h == "**kern"]
        other = [h for h in head if h != "**kern"]
        if head != kern + other:
            raise ValueError(f"can't repair header {head!r}: non-kern spine before a kern spine")
        lines[i] = "\t".join(["**kern"] * (width - len(other)) + other)
    elif len(head) > width:
        raise ValueError(f"header has {len(head)} spines, next line {width}")
    return "\n".join(_insert_missing_split(lines, i))


def _insert_missing_split(lines: list[str], start: int) -> list[str]:
    """Insert a dropped opening ``*^``: the first line one field wider than the header.

    Which spine split is read from the first later merge (``*v *v``) over that width; if there is
    none, the file is left alone and ``parse_kern`` will reject it.
    """
    width = len(lines[start].split("\t"))
    for j in range(start + 1, len(lines)):
        fields = lines[j].split("\t")
        if lines[j].startswith("!!") or not lines[j]:
            continue
        if len(fields) == width:
            if any(f in ("*^", "*v", "*-", "*+", "*x") for f in fields):
                return lines  # spine structure changes explicitly before any widening
            continue
        if len(fields) != width + 1:
            return lines
        for k in range(j + 1, len(lines)):
            f = lines[k].split("\t")
            if "*v" in f and f[f.index("*v") + 1 : f.index("*v") + 2] == ["*v"]:
                pos = f.index("*v")
                if pos >= width:
                    break
                split = ["*"] * width
                split[pos] = "*^"
                return [*lines[:j], "\t".join(split), *lines[j:]]
        raise ValueError(f"line {j + 1}: widened to {width + 1} fields with no merge to infer from")
    return lines
