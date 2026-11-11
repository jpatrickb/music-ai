"""Add beams to ``**kern`` that has none.

LLM-written kern rarely has beam markers (``L`` opens a beam, ``J`` closes it), and Verovio does
not beam kern on its own, so every eighth and sixteenth renders with its own flag. This adds the
standard beaming: consecutive notes shorter than a quarter, in the same spine (or sub-spine) and the
same beat, are beamed together. Rests and longer notes break a beam. The beat is a quarter in
simple meters (x/4, x/2) and a dotted quarter in compound meters (6/8, 9/8, 12/8, 3/8).

Files that already contain beam markers are returned unchanged.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from fractions import Fraction

from music_ai.kern import parse_duration

_METER_RE = re.compile(r"^\*M(\d+)/(\d+)$")
_HAS_BEAM_RE = re.compile(r"[LJ]")


@dataclass
class _Col:
    kind: str
    t: Fraction = Fraction(0)  # time since the start of the bar, in quarter notes
    beat: Fraction = Fraction(1)
    group: list[tuple[int, int]] = field(default_factory=list)  # (line, column) of open group
    group_beat: int | None = None

    def copy(self) -> _Col:
        return _Col(self.kind, self.t, self.beat)


def beat_unit(numerator: int, denominator: int) -> Fraction:
    """Beam unit in quarter notes: a dotted quarter in compound meters, else a quarter."""
    if denominator == 8 and numerator % 3 == 0:
        return Fraction(3, 2)
    return Fraction(1)


def _beamable(tok: str) -> Fraction | None:
    """Duration if every note of the token is shorter than a quarter, else None (rests, grace
    notes, longer notes and tokens without a duration all break beams)."""
    if "r" in tok or "q" in tok or "Q" in tok:
        return None
    durs = [parse_duration(sub) for sub in tok.split(" ") if sub]
    if not durs or any(d is None or d >= 1 for d in durs):
        return None
    return min(durs)  # type: ignore[type-var]


def _duration(tok: str) -> Fraction:
    if "q" in tok or "Q" in tok:
        return Fraction(0)
    durs = [d for sub in tok.split(" ") if sub and (d := parse_duration(sub)) is not None]
    return min(durs) if durs else Fraction(0)


def add_beams(text: str) -> str:
    """Return ``text`` with ``L``/``J`` beam markers added (see the module docstring)."""
    lines = text.split("\n")
    marks: dict[tuple[int, int], str] = {}
    cols: list[_Col] | None = None
    for n, line in enumerate(lines):
        if not line or line.startswith("!"):
            continue
        toks = line.split("\t")
        if cols is None:
            if line.startswith("**"):
                cols = [_Col(k) for k in toks]
            continue
        if line.startswith("*"):
            for c, tok in zip(cols, toks, strict=False):
                if m := _METER_RE.match(tok):
                    c.beat = beat_unit(int(m.group(1)), int(m.group(2)))
            if any(t in ("*^", "*v", "*x", "*-", "*+") for t in toks):
                for c in cols:
                    _close(c, marks)
                cols = _restructure(cols, toks)
            continue
        if line.startswith("="):
            for c in cols:
                _close(c, marks)
                c.t = Fraction(0)
            continue
        for i, (c, tok) in enumerate(zip(cols, toks, strict=False)):
            if c.kind != "**kern" or tok == ".":
                continue
            if c.kind == "**kern" and _HAS_BEAM_RE.search(tok):
                return text  # already beamed by hand
            d = _beamable(tok)
            beat = int(c.t // c.beat)
            if d is None or beat != c.group_beat:
                _close(c, marks)
            if d is not None:
                c.group.append((n, i))
                c.group_beat = beat
            c.t += _duration(tok)
    if cols:
        for c in cols:
            _close(c, marks)
    for (n, i), mark in marks.items():
        toks = lines[n].split("\t")
        subs = toks[i].split(" ")
        subs[0] += mark
        toks[i] = " ".join(subs)
        lines[n] = "\t".join(toks)
    return "\n".join(lines)


def _close(c: _Col, marks: dict[tuple[int, int], str]) -> None:
    if len(c.group) >= 2:
        marks[c.group[0]] = "L"
        marks[c.group[-1]] = "J"
    c.group = []
    c.group_beat = None


def _restructure(cols: list[_Col], toks: list[str]) -> list[_Col]:
    """Columns after a spine-manipulator line (*^ split, *v merge, *x exchange, *- end)."""
    if "*+" in toks:
        raise ValueError("*+ (add spine) is not supported")
    new: list[_Col] = []
    i = 0
    while i < len(toks):
        t = toks[i]
        if t == "*^":
            new += [cols[i].copy(), cols[i].copy()]
        elif t == "*v":
            new.append(cols[i].copy())
            while i + 1 < len(toks) and toks[i + 1] == "*v":
                i += 1
        elif t == "*x" and i + 1 < len(toks) and toks[i + 1] == "*x":
            new += [cols[i + 1], cols[i]]
            i += 1
        elif t != "*-":
            new.append(cols[i])
        i += 1
    return new
