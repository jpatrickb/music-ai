"""Check a converted **kern file against an independent reading of its source.

Converters (humlib's ``musicxml2hum``, converter21) can silently drop, shift or invent notes, and
user-uploaded MusicXML is often slightly broken. The check: the multiset of (onset, MIDI pitch)
over all sounding notes must be identical in music21's reading of the source and in
``music_ai.kern``'s reading of the kern. Only attacks count: a tie continuation is skipped on both
sides (a converter may split a long note into tied pieces), and grace notes are excluded (no
duration in kern).

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
    pieces: Counter[Event]  # every written note, tied pieces separately
    attacks: Counter[Event]  # tie continuations skipped
    tremolos: list[tuple[Fraction, Fraction, int]]  # (start, end, midi) of tremolo-marked notes


def _bar_starts(score: music21.stream.Score) -> list[list[tuple[music21.stream.Measure, Fraction]]]:
    """Per part, each measure with its start time. A bar lasts as long as its longest voice in any
    part (so a free cadenza bar written longer than its time signature keeps its length), which
    music21's own measure offsets don't always respect when the staves disagree."""
    parts = [list(p.getElementsByClass("Measure")) for p in score.parts]
    if not all(parts) or len({len(ms) for ms in parts}) != 1:
        # no bars, or ragged parts: each part as one span at music21's own offsets
        return [[(p, Fraction(0))] for p in score.parts]
    out: list[list[tuple[music21.stream.Measure, Fraction]]] = [[] for _ in parts]
    t = Fraction(0)
    for i in range(len(parts[0])):
        length = Fraction(0)
        for pi, ms in enumerate(parts):
            m = ms[i]
            out[pi].append((m, t))
            for n in m.recurse().notesAndRests:
                length = max(length, _q(n.getOffsetInHierarchy(m)) + _q(n.quarterLength))
        if length == 0:
            ts = parts[0][i].getContextByClass("TimeSignature")
            length = _q(ts.barDuration.quarterLength) if ts else Fraction(0)
        t += length
    return out


def music21_events(score: music21.stream.Score) -> Source:
    pieces: Counter[Event] = Counter()
    attacks: Counter[Event] = Counter()
    tremolos = []
    for part in _bar_starts(score):
        for m, start_of_bar in part:
            for n in m.recurse().notes:
                if n.duration.isGrace:
                    continue
                start = start_of_bar + _q(n.getOffsetInHierarchy(m))
                trem = any(isinstance(e, music21.expressions.Tremolo) for e in n.expressions)
                chord = isinstance(n, music21.chord.Chord)
                for x in n.notes if chord else [n]:
                    midi = x.pitch.midi
                    pieces[(start, midi)] += 1
                    if trem:
                        tremolos.append((start, start + _q(n.quarterLength), midi))
                    # a chord-level tie only speaks for notes when none carries its own
                    per_note = chord and any(y.tie is not None for y in n.notes)
                    tie = x.tie if (per_note or not chord) else n.tie
                    if tie is None or tie.type not in ("stop", "continue"):
                        attacks[(start, midi)] += 1
    return Source(pieces, attacks, tremolos)


def kern_events(text: str, attacks_only: bool = False) -> Counter[Event]:
    skip = ("continue", "end") if attacks_only else ()
    return Counter(
        (_q(n.onset), n.midi)
        for n in parse_kern(text).pitched()
        if n.duration > 0 and n.tie not in skip
    )


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
    """Verified if the written notes match exactly, or, failing that, the attacks do (a converter
    may re-tie a long note into pieces, or drop a tie that has no start). Extra notes that are a
    written-out tremolo are allowed when nothing is missing."""
    best = None
    for expected, got in (
        (source.pieces, kern_events(text)),
        (source.attacks, kern_events(text, attacks_only=True)),
    ):
        if got == expected:
            return Match(True, expected.total(), got.total(), "")
        extra = got - expected
        if not (expected - got) and all(_in_tremolo(e, source.tremolos) for e in extra):
            note = f"{extra.total()} extra notes are written-out tremolos"
            return Match(True, expected.total(), got.total(), note)
        diff = (expected - got).total() + extra.total()
        if best is None or diff < best[0]:
            best = (diff, expected, got)
    _, expected, got = best
    missing = sorted((expected - got).elements())[:3]
    extra = sorted((got - expected).elements())[:3]
    fmt = ", ".join
    detail = (
        f"missing {(expected - got).total()} (e.g. {fmt(f'{float(o):g}:{m}' for o, m in missing)}); "
        f"extra {(got - expected).total()} (e.g. {fmt(f'{float(o):g}:{m}' for o, m in extra)})"
    )
    return Match(False, expected.total(), got.total(), detail)
