"""Check a converted **kern file against an independent reading of its source.

Converters (humlib's ``musicxml2hum``, converter21) can silently drop, shift or invent notes, and
user-uploaded MusicXML is often slightly broken. The check: the multiset of (onset, MIDI pitch)
over all sounding notes must be identical in music21's reading of the source and in
``music_ai.kern``'s reading of the kern. Grace notes are excluded (they have no duration in kern).

One allowed difference: kern writes a single-note tremolo out as repeated notes, where music21
keeps one note with a ``Tremolo`` mark. Extra kern notes are accepted only if each falls strictly
inside such a note's span at the same pitch, and only if no source note is missing.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from fractions import Fraction

import music21

from music_ai.kern import parse_kern

Event = tuple[Fraction, int]


def _q(x: float | Fraction) -> Fraction:
    return Fraction(x).limit_denominator(100_000)


@dataclass
class Source:
    events: Counter[Event]
    tremolos: list[tuple[Fraction, Fraction, int]]  # (start, end, midi) of tremolo-marked notes


def music21_events(score: music21.stream.Score) -> Source:
    events: Counter[Event] = Counter()
    tremolos = []
    for n in score.flatten().notes:
        if n.duration.isGrace:
            continue
        trem = any(isinstance(e, music21.expressions.Tremolo) for e in n.expressions)
        start = _q(n.offset)
        for p in n.pitches:
            events[(start, p.midi)] += 1
            if trem:
                tremolos.append((start, start + _q(n.quarterLength), p.midi))
    return Source(events, tremolos)


def kern_events(text: str) -> Counter[Event]:
    return Counter((_q(n.onset), n.midi) for n in parse_kern(text).pitched() if n.duration > 0)


@dataclass
class Match:
    ok: bool
    expected: int  # notes in the source
    got: int  # notes in the kern
    detail: str  # first differences, when not ok


def _in_tremolo(e: Event, tremolos: list[tuple[Fraction, Fraction, int]]) -> bool:
    onset, midi = e
    return any(s < onset < end and m == midi for s, end, m in tremolos)


def compare(source: Source, text: str) -> Match:
    expected = source.events
    got = kern_events(text)
    if got == expected:
        return Match(True, expected.total(), got.total(), "")
    extra = got - expected
    if not (expected - got) and all(_in_tremolo(e, source.tremolos) for e in extra):
        note = f"{extra.total()} extra notes are written-out tremolos"
        return Match(True, expected.total(), got.total(), note)
    missing = sorted((expected - got).elements())[:3]
    extra = sorted((got - expected).elements())[:3]
    fmt = ", ".join
    detail = (
        f"missing {(expected - got).total()} (e.g. {fmt(f'{float(o):g}:{m}' for o, m in missing)}); "
        f"extra {(got - expected).total()} (e.g. {fmt(f'{float(o):g}:{m}' for o, m in extra)})"
    )
    return Match(False, expected.total(), got.total(), detail)
