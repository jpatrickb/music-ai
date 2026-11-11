"""Where does an arrangement state each phrase of the original tune, and how is it changed?

``melody_fidelity`` asks whether a whole tune is present nearly note for note. Real arrangements
(Liszt's song transcriptions, hymn arrangements) move phrases between hands and registers, stretch
or compress the rhythm, add introductions, interludes and cadenzas between them, and ornament the
line. So this works phrase by phrase:

1. The tune is split into phrases at rests and at long notes (``split_phrases``).
2. Each phrase is searched for anywhere in the arrangement, at rhythm scales ×½, ×1 and ×2, in any
   key. A match follows the phrase's contour: each next note is the one at the right time and
   pitch class closest to where the melodic interval says it should be, so the line is tracked in
   its own register even inside a thick texture.
3. For each match it reports: bars, rhythm scale, transposition, the staff and register carrying
   it, whether the tune sits on top, in the middle or at the bottom of the texture, **coverage**
   (share of the phrase present, by duration) and **shape** (share of matched notes at exactly
   the expected interval from the previous one, not just the right pitch class).

4. Matches are linked into runs (phrase k, then k+1 soon after, same scale and key) and a run is
   kept if its total **evidence** is high enough. A matched note's evidence is log2(12 / k),
   k the number of pitch classes starting at that moment: a hit in a texture where every pitch
   class sounds says nothing.

Calibration (2026-11-11): four Schubert/Liszt tunes against four Liszt piano transcriptions.
At the default ``min_evidence`` of 60 bits, none of the 12 mismatched tune/arrangement pairs
matched a single phrase, while the true pairs found 13/14 (Ständchen), 33/34 (Erlkönig),
13/16 (Die Forelle) and 10/28 (Liebestraum No. 3, where the tune is often inside the texture).
Everything is descriptive.
"""

from __future__ import annotations

from bisect import bisect_left, bisect_right
from dataclasses import dataclass
from fractions import Fraction
from math import log2
from statistics import median

from music_ai.kern import KernScore, Note, merge_ties
from music_ai.melody_fidelity import MelodyNote

SCALES = (Fraction(1, 2), Fraction(1), Fraction(2))


@dataclass(frozen=True)
class Phrase:
    index: int
    notes: tuple[MelodyNote, ...]  # onsets relative to the phrase's first note
    bar: int | None  # bar in the original where it starts


@dataclass(frozen=True)
class PhraseMatch:
    phrase: int
    onset: Fraction
    bar: int | None
    last_bar: int | None
    scale: Fraction  # 2 = rhythm doubled (augmentation), 1/2 = halved (diminution)
    transposition: int  # semitones up, 0-11
    staff: int | None  # staff carrying most matched notes (1 = top staff)
    register: int  # mean MIDI pitch of the matched notes
    position: str  # "top", "middle" or "bottom": where most matched notes sit in the texture
    coverage: float
    shape: float
    evidence: float  # bits: sum over matched notes of log2(12 / pitch classes starting nearby)


def bar_of(score: KernScore, onset: Fraction) -> int:
    """The printed bar number at ``onset``: the number on the last barline at or before it, so
    references match the score a player reads (a cadenza written over several kern bars keeps
    one number; a pickup is bar 0). An unnumbered barline is one more than the barline before
    it (musicxml2hum numbers only the first, ``=1`` then plain ``=``); with no numbers at all,
    bars are counted, and notes before the first barline are bar 0."""
    bars = sorted(
        (b for b in score.barlines if not b.token.startswith("==")), key=lambda b: b.onset
    )
    i = bisect_right([b.onset for b in bars], onset)
    current = 0
    for b in bars[:i]:
        current = b.number if b.number is not None else current + 1
    return current


def melody_line(score: KernScore, staff: int = 1) -> list[tuple[Note, Note | None]]:
    """The top line of one staff as (note, following rest or None) pairs, in time order."""
    events = sorted((n for n in score.notes if n.staff == staff), key=lambda n: n.onset)
    pitched = [n for n in merge_ties([n for n in events if not n.is_rest])]
    by_onset: dict[Fraction, Note] = {}
    for n in pitched:
        if n.grace:
            continue
        if n.onset not in by_onset or (n.midi or 0) > (by_onset[n.onset].midi or 0):
            by_onset[n.onset] = n
    line = [by_onset[o] for o in sorted(by_onset)]
    rests = sorted((n for n in events if n.is_rest), key=lambda n: n.onset)
    out = []
    for i, n in enumerate(line):
        nxt = line[i + 1].onset if i + 1 < len(line) else None
        gap = next((r for r in rests if n.end <= r.onset and (nxt is None or r.onset < nxt)), None)
        out.append((n, gap))
    return out


def split_phrases(line: list[tuple[Note, Note | None]], min_notes: int = 7) -> list[Phrase]:
    """Phrases end at a rest, or at a note at least twice the median length followed by another
    note. Fragments shorter than ``min_notes`` join the next phrase."""
    if not line:
        return []
    med = median(n.duration for n, _ in line)
    groups: list[list[Note]] = [[]]
    for i, (n, rest) in enumerate(line):
        groups[-1].append(n)
        last = i == len(line) - 1
        ends_phrase = rest is not None or n.duration >= 2 * med
        if not last and ends_phrase and len(groups[-1]) >= min_notes:
            groups.append([])
    if len(groups) > 1 and len(groups[-1]) < min_notes:
        groups[-2].extend(groups.pop())
    phrases = []
    for i, g in enumerate(groups):
        t0 = g[0].onset
        notes = tuple(MelodyNote(n.onset - t0, n.duration, n.midi) for n in g)  # type: ignore[arg-type]
        phrases.append(Phrase(i, notes, None))
    return phrases


def _texture_position(notes: list[Note]) -> dict[int, str]:
    """id(note) -> top / bottom / middle among the notes sounding at any point while it lasts.

    Judging only at the note's start misses figuration that begins just after it (a tune note
    on the beat under sixteenths that fill the beat above it would wrongly count as "top"). A
    note sounding for more than a quarter is judged over its first quarter, so a long held
    note isn't buried by everything that happens while it rings."""
    order = sorted(notes, key=lambda n: n.onset)
    starts = [n.onset for n in order]
    out = {}
    for n in order:
        until = n.onset + min(n.duration, Fraction(1))
        lo = bisect_left(starts, n.onset - 16)
        sounding = [
            m.midi
            for m in order[lo : bisect_left(starts, until)]
            if m.end > n.onset and m is not n
        ]
        if not sounding or all(n.midi >= x for x in sounding):  # type: ignore[operator]
            out[id(n)] = "top"
        elif all(n.midi <= x for x in sounding):  # type: ignore[operator]
            out[id(n)] = "bottom"
        else:
            out[id(n)] = "middle"
    return out


def map_phrases(
    phrases: list[Phrase],
    arrangement: KernScore,
    tolerance: Fraction = Fraction(1, 8),
    min_coverage: float = 0.8,
    min_shape: float = 0.75,
    min_evidence: float = 60.0,
    max_gap: Fraction = Fraction(16),
) -> list[PhraseMatch]:
    """All non-overlapping statements of each phrase (see the module docstring), in time order."""
    notes = sorted(
        (n for n in merge_ties(arrangement.pitched()) if not n.grace and n.duration > 0),
        key=lambda n: n.onset,
    )
    if not notes:
        return []
    onsets = [n.onset for n in notes]
    position = _texture_position(notes)
    found: list[PhraseMatch] = []
    for ph in phrases:
        total = sum(m.duration for m in ph.notes) or Fraction(1)
        candidates = []
        first = ph.notes[0]
        for anchor in notes:
            for scale in SCALES:
                hit, shape_ok, bits, matched = _follow(ph, anchor, scale, notes, onsets, tolerance)
                cov = float(hit / total)
                shape = shape_ok / max(len(matched) - 1, 1)
                if cov >= min_coverage and shape >= min_shape:
                    staffs = [x.staff for x in matched]
                    pos = [position[id(x)] for x in matched]
                    candidates.append(
                        PhraseMatch(
                            phrase=ph.index,
                            onset=anchor.onset,
                            bar=bar_of(arrangement, anchor.onset),
                            last_bar=bar_of(arrangement, matched[-1].onset),
                            scale=scale,
                            transposition=((anchor.midi or 0) - (first.midi or 0)) % 12,
                            staff=max(set(staffs), key=staffs.count),
                            register=round(sum(x.midi or 0 for x in matched) / len(matched)),
                            position=max(set(pos), key=pos.count),
                            coverage=cov,
                            shape=shape,
                            evidence=bits,
                        )
                    )
        found.extend(candidates)
    return _chains(found, phrases, min_evidence, max_gap)


def _chains(
    candidates: list[PhraseMatch], phrases: list[Phrase], min_evidence: float, max_gap: Fraction
) -> list[PhraseMatch]:
    """Keep matches that belong to a convincing run of the tune.

    Real statements come in order: phrase k, then phrase k+1 (or k+2, if one is changed beyond
    recognition) starting soon after k ends, at the same rhythm scale and key. Each match extends
    the best run ending in such a predecessor; a run's evidence is the sum of its matches'. Runs
    are taken best first, without overlapping each other, while their evidence is at least
    ``min_evidence``.
    """
    spans = {ph.index: ph.notes[-1].onset + ph.notes[-1].duration for ph in phrases}
    cands = sorted(candidates, key=lambda c: c.onset)
    best: list[float] = []
    prev: list[int | None] = []
    for i, c in enumerate(cands):
        best.append(c.evidence)
        prev.append(None)
        for j in range(i - 1, -1, -1):
            d = cands[j]
            end_d = d.onset + spans[d.phrase] * d.scale
            if c.onset - end_d > max_gap:
                if d.onset + spans[d.phrase] * 2 * 2 < c.onset - max_gap:  # far enough back
                    break
                continue
            if (
                c.phrase - d.phrase in (1, 2)
                and d.scale == c.scale
                and d.transposition == c.transposition
                and c.onset >= end_d - spans[d.phrase] * d.scale / 4
                and best[j] + c.evidence > best[i]
            ):
                best[i], prev[i] = best[j] + c.evidence, j
    order = sorted(range(len(cands)), key=lambda i: -best[i])
    used: list[tuple[Fraction, Fraction]] = []
    kept: list[PhraseMatch] = []
    for i in order:
        if best[i] < min_evidence:
            break
        run = []
        k: int | None = i
        while k is not None:
            run.append(cands[k])
            k = prev[k]
        lo = min(m.onset for m in run)
        hi = max(m.onset + spans[m.phrase] * m.scale for m in run)
        if any(lo < u_hi and u_lo < hi for u_lo, u_hi in used):
            continue
        used.append((lo, hi))
        kept.extend(run)
    return sorted(kept, key=lambda c: (c.onset, c.phrase))


def _follow(
    ph: Phrase,
    anchor: Note,
    scale: Fraction,
    notes: list[Note],
    onsets: list[Fraction],
    tolerance: Fraction,
) -> tuple[Fraction, int, float, list[Note]]:
    """Track the phrase from ``anchor``, taken as its first note (which fixes the key and
    register): (matched duration, notes at the exact expected interval, evidence in bits,
    matched notes). A matched note's evidence is log2(12 / k), k the number of pitch classes
    starting within the timing window: a hit where all twelve are present says nothing."""
    first = ph.notes[0]
    t0 = anchor.onset
    shift = (anchor.midi or 0) - (first.midi or 0)
    tol = tolerance * max(scale, Fraction(1))
    hit = first.duration
    shape_ok = 0
    bits = 0.0
    matched = [anchor]
    prev_src, prev_arr = first.midi or 0, anchor.midi or 0
    for m in ph.notes[1:]:
        target = t0 + m.onset * scale
        lo, hi = bisect_left(onsets, target - tol), bisect_right(onsets, target + tol)
        want = prev_arr + ((m.midi or 0) - prev_src)
        pcs = [n for n in notes[lo:hi] if (n.midi or 0) % 12 == ((m.midi or 0) + shift) % 12]
        if not pcs:
            continue
        best = min(pcs, key=lambda n: (abs((n.midi or 0) - want), abs(n.onset - target)))
        present = {(n.midi or 0) % 12 for n in notes[lo:hi]}
        bits += log2(12 / len(present))
        hit += m.duration
        if best.midi == want:
            shape_ok += 1
        matched.append(best)
        prev_src, prev_arr = m.midi or 0, best.midi or 0
    return hit, shape_ok, bits, matched
