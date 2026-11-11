"""Is the tune still there? Find statements of a source melody inside an arrangement.

An arrangement may add an introduction, change key for a later verse, move the tune to another
octave or the left hand, and shift notes slightly off the beat. So the search is
transposition-invariant (pitch classes), octave-free, and allows each note to land within a small
timing tolerance of where the source puts it. For every place the tune could start, it measures:

- **coverage**: the share of the tune (weighted by note length) found at the right time and pitch
  class anywhere in the texture;
- **top coverage**: the share where the matching note is also the highest sounding note, i.e. the
  tune is on top where a listener hears it most easily.

Statements are the best non-overlapping windows with coverage at or above a threshold. This
answers "is the tune there and audible", not "is the arrangement good".

Defaults (provisional): a sixteenth-note timing tolerance and 85% coverage. Dense textures match
any tune by chance to some degree: across the 24 pieces of experiment 002 against the five hymn
tunes, chance coverage peaked at 79% (57% on top) with these settings, and at 88% with an
eighth-note tolerance. Recalibrate once there are real arrangements.
"""

from __future__ import annotations

from bisect import bisect_left, bisect_right
from dataclasses import dataclass
from fractions import Fraction

from music_ai.kern import KernScore, Note, merge_ties

ANCHORS = 4  # how many of the tune's opening notes may anchor a candidate start


@dataclass(frozen=True)
class MelodyNote:
    onset: Fraction  # quarter notes from the tune's first note
    duration: Fraction
    midi: int


@dataclass(frozen=True)
class Statement:
    onset: Fraction  # where the tune's first note falls in the arrangement
    bar: int | None  # bar of the first matched note
    transposition: int  # semitones up from the source key, 0-11
    coverage: float
    top_coverage: float


def extract_melody(score: KernScore, staff: int = 1) -> list[MelodyNote]:
    """The top line of one staff: at each onset, the highest note that starts there, if it is the
    highest note sounding. For a hymn setting, staff 1's top line is the soprano (the tune)."""
    notes = [n for n in merge_ties(score.pitched()) if n.staff == staff]
    top = _top_flags(notes)
    by_onset: dict[Fraction, Note] = {}
    for n, is_top in zip(notes, top, strict=True):
        if is_top and (n.onset not in by_onset or n.midi > by_onset[n.onset].midi):
            by_onset[n.onset] = n
    line = [by_onset[o] for o in sorted(by_onset)]
    if not line:
        return []
    t0 = line[0].onset
    return [MelodyNote(n.onset - t0, n.duration, n.midi) for n in line]  # type: ignore[arg-type]


def _top_flags(notes: list[Note]) -> list[bool]:
    """For each note: is it at least as high as every note sounding when it starts?"""
    order = sorted(range(len(notes)), key=lambda i: notes[i].onset)
    flags = [False] * len(notes)
    active: list[int] = []
    for i in order:
        n = notes[i]
        active = [j for j in active if notes[j].onset + notes[j].duration > n.onset]
        others = [notes[j].midi for j in active] + [
            m.midi for m in notes if m.onset == n.onset and m is not n
        ]
        flags[i] = all(n.midi >= x for x in others)  # type: ignore[operator]
        active.append(i)
    return flags


def find_statements(
    melody: list[MelodyNote],
    arrangement: KernScore,
    tolerance: Fraction = Fraction(1, 4),
    min_coverage: float = 0.85,
) -> list[Statement]:
    """Non-overlapping statements of ``melody`` in ``arrangement`` (see the module docstring)."""
    if not melody:
        return []
    notes = sorted(merge_ties(arrangement.pitched()), key=lambda n: n.onset)
    if not notes:
        return []
    top = dict(zip(map(id, notes), _top_flags(notes), strict=True))
    onsets = [n.onset for n in notes]
    total = sum(m.duration for m in melody) or Fraction(1)
    span = melody[-1].onset + melody[-1].duration
    # Candidate start points: wherever one of the tune's first few notes could be. Anchoring on the
    # first note alone misses statements whose opening (often a pickup) is changed or reharmonized.
    keys = {
        (a.onset - m.onset, (a.midi - m.midi) % 12)  # type: ignore[operator]
        for m in melody[:ANCHORS]
        for a in notes
    }
    candidates: dict[tuple[Fraction, int], Statement] = {}
    for key in keys:
        start, t = key
        bar = None
        hit = top_hit = Fraction(0)
        for m in melody:
            target = start + m.onset
            pc = (m.midi + t) % 12
            lo, hi = (
                bisect_left(onsets, target - tolerance),
                bisect_right(onsets, target + tolerance),
            )
            matches = [n for n in notes[lo:hi] if n.midi % 12 == pc]  # type: ignore[operator]
            if matches:
                if bar is None:
                    bar = min(matches, key=lambda n: n.onset).measure
                hit += m.duration
                if any(top[id(n)] for n in matches):
                    top_hit += m.duration
        candidates[key] = Statement(start, bar, t, float(hit / total), float(top_hit / total))

    chosen: list[Statement] = []
    for s in sorted(candidates.values(), key=lambda s: (-s.coverage, -s.top_coverage, s.onset)):
        if s.coverage < min_coverage:
            break
        if all(s.onset + span <= c.onset or c.onset + span <= s.onset for c in chosen):
            chosen.append(s)
    return sorted(chosen, key=lambda s: s.onset)
