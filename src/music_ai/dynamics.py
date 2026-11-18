"""Dynamics from a `**kern` score's `**dynam` spines, as a MIDI velocity curve over time.

Verovio's MIDI gives every note the same velocity, which makes playback flat. This reads the
dynamic markings and hairpins a score already has and turns them into a velocity for any moment,
so a renderer can set each note's velocity from its onset time.

`**dynam` tokens used:

- markings `ppp` ... `fff`, `fp`, `sf`/`sfz`/`fz` (accents: a one-note bump, not a new level)
- `<` / `>` start a crescendo / diminuendo, `[` / `]` end it

A hairpin moves linearly from the level where it starts to the next marking, if that marking
comes at or within `HAIRPIN_REACH` seconds of the hairpin's end; otherwise it moves one level
(`LEVEL_STEP`) and stays there. The velocity table is the usual General MIDI-style spacing; it's a
playback convenience, not an analysis of the score.
"""

from __future__ import annotations

import bisect
from collections.abc import Callable
from dataclasses import dataclass

LEVELS = {"ppp": 20, "pp": 33, "p": 49, "mp": 64, "mf": 80, "f": 96, "ff": 112, "fff": 124}
ACCENTS = {"sf": 16, "sfz": 16, "fz": 16, "rfz": 12, "fp": 0}
LEVEL_STEP = 16
HAIRPIN_REACH = 1.0  # seconds
DEFAULT = LEVELS["mf"]


@dataclass(frozen=True)
class Mark:
    line: int  # 1-based line in the kern text
    token: str  # a single dynam token: "p", "<", "[", "sfz", ...


def dynamic_marks(text: str) -> list[Mark]:
    """Every non-null token in a `**dynam` spine, in line order, following spine splits/merges."""
    kinds: list[str] | None = None
    marks: list[Mark] = []
    for n, line in enumerate(text.splitlines(), start=1):
        if not line or line.startswith("!"):
            continue
        toks = line.split("\t")
        if line.startswith("**"):
            kinds = toks
            continue
        if kinds is None or len(toks) != len(kinds):
            continue
        if line.startswith("*"):
            kinds = _manipulate(kinds, toks)
            continue
        if line.startswith("="):
            continue
        for kind, tok in zip(kinds, toks, strict=True):
            if kind == "**dynam" and tok != ".":
                marks.extend(Mark(n, t) for t in tok.split() if t)
    return marks


def _manipulate(kinds: list[str], toks: list[str]) -> list[str]:
    out: list[str] = []
    i = 0
    while i < len(toks):
        tok, kind = toks[i], kinds[i]
        if tok == "*^":
            out += [kind, kind]
        elif tok == "*v":
            while i + 1 < len(toks) and toks[i + 1] == "*v" and kinds[i + 1] == kind:
                i += 1
            out.append(kind)
        elif tok == "*-":
            pass
        elif tok == "*x" and i + 1 < len(toks) and toks[i + 1] == "*x":
            out += [kinds[i + 1], kind]
            i += 1
        elif tok == "*+":
            out += [kind, "new"]
        else:
            out.append(kind)
        i += 1
    return out


def velocity_curve(
    timed: list[tuple[float, str]], default: int = DEFAULT
) -> Callable[[float], int]:
    """A function from time (seconds) to MIDI velocity, given (time, dynam token) pairs.

    Accent tokens bump only notes starting within 50 ms of the accent.
    """
    timed = sorted(timed, key=lambda p: p[0])
    points: list[tuple[float, float]] = [(0.0, float(default))]  # breakpoints of a step/ramp curve
    accents: list[tuple[float, int]] = []
    level = float(default)
    hairpin: tuple[float, float, int] | None = None  # (start time, start level, direction)

    def set_level(t: float, v: float) -> None:
        nonlocal level
        points.append((t, level))  # hold the old level up to t
        points.append((t, v))
        level = v

    for i, (t, tok) in enumerate(timed):
        if tok in LEVELS:
            set_level(t, LEVELS[tok])
        elif tok in ACCENTS:
            accents.append((t, ACCENTS[tok]))
            if tok == "fp":
                accents.append((t, LEVELS["f"] - int(level)))
                set_level(t, LEVELS["p"])
        elif tok[0] in "<>":
            hairpin = (t, level, 1 if tok[0] == "<" else -1)
            points.append((t, level))
        elif tok[0] in "[]" and hairpin is not None:
            start, from_level, direction = hairpin
            nxt = next(((u, k) for u, k in timed[i + 1 :] if k in LEVELS), None)
            if nxt is not None and nxt[0] - t <= HAIRPIN_REACH:
                target = float(LEVELS[nxt[1]])
                end = nxt[0]
            else:
                target = from_level + direction * LEVEL_STEP
                end = t
            target = max(1.0, min(127.0, target))
            points.append((max(end, start), target))
            level = target
            hairpin = None

    times = [p[0] for p in points]

    def velocity(t: float) -> int:
        j = bisect.bisect_right(times, t) - 1
        t0, v0 = points[j]
        if j + 1 < len(points):
            t1, v1 = points[j + 1]
            if t1 > t0:
                v0 += (v1 - v0) * (t - t0) / (t1 - t0)
        bump = sum(b for u, b in accents if abs(u - t) <= 0.05)
        return max(1, min(127, round(v0 + bump)))

    return velocity
