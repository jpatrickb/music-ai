"""Descriptive style statistics for piano scores, computed from timed notes.

Works on `omr_lab.kern.Note` lists (from `parse_kern`, or built from any other parser), so the
same numbers can describe a composer corpus and an LLM-generated piece.

Harmony is estimated per beat window by chord-template fitting: every pitch sounding in the
window is weighted by how long it sounds there, and the window gets the template (12 roots x
triad and seventh-chord qualities) that best covers that weight. From that come:

- inversion rates (bass = lowest sounding pitch in the window, relative to the fitted root),
- seventh-chord rate, harmonic-change rate (fraction of beats whose chord differs from the
  previous beat's),
- non-chord-tone (NCT) rates: share of sounding weight outside the fitted chord, and share of
  melody notes (highest right-hand note per attack) outside it.

Hand statistics need a two-staff piano layout (right hand = *staff1, the top staff): simultaneous-attack span per hand, left-hand bass leaps, melody steps/leaps, and
attack density.

These are estimates, not an analysis: template fitting can't tell an accented passing tone
from a chord tone, and beat windows blur fast harmonic rhythm. They are meant for comparing
corpora and generated pieces measured the same way.
"""

from __future__ import annotations

import itertools
from collections import Counter, defaultdict
from dataclasses import dataclass
from fractions import Fraction
from statistics import median

from omr_lab.kern import KernScore, Note, merge_ties

# (name, intervals above the root). Order matters for ties: triads before sevenths.
CHORD_TYPES: list[tuple[str, tuple[int, ...]]] = [
    ("maj", (0, 4, 7)),
    ("min", (0, 3, 7)),
    ("dim", (0, 3, 6)),
    ("dom7", (0, 4, 7, 10)),
    ("maj7", (0, 4, 7, 11)),
    ("min7", (0, 3, 7, 10)),
    ("hdim7", (0, 3, 6, 10)),
    ("dim7", (0, 3, 6, 9)),
]
MISSING_TONE_PENALTY = 0.15  # per absent template tone, as a fraction of the window's weight


@dataclass(frozen=True)
class Chord:
    root: int  # pitch class
    kind: str
    intervals: tuple[int, ...]

    @property
    def pcs(self) -> frozenset[int]:
        return frozenset((self.root + i) % 12 for i in self.intervals)

    @property
    def is_seventh(self) -> bool:
        return len(self.intervals) == 4


@dataclass(frozen=True)
class BeatHarmony:
    start: Fraction
    end: Fraction
    chord: Chord
    bass_midi: int
    inversion: str  # "root", "first", "second", "third", "nct-bass"
    weight: float  # total sounding weight in the window (quarter-note x voices)
    nct_weight: float


def fit_chord(weights: dict[int, float]) -> Chord | None:
    """Best chord template for a {pitch class: sounding weight} map (None if < 2 classes)."""
    if len([w for w in weights.values() if w > 0]) < 2:
        return None
    total = sum(weights.values())
    best: tuple[float, int, Chord] | None = None
    for order, (kind, ivs) in enumerate(CHORD_TYPES):
        for root in range(12):
            chord = Chord(root, kind, ivs)
            pcs = chord.pcs
            covered = sum(w for pc, w in weights.items() if pc in pcs)
            missing = sum(1 for pc in pcs if weights.get(pc, 0) <= 0)
            score = covered - (total - covered) - MISSING_TONE_PENALTY * total * missing
            key = (score, -order)
            if best is None or key > (best[0], best[1]):
                best = (score, -order, chord)
    return best[2] if best else None


def inversion_of(chord: Chord, bass_midi: int) -> str:
    rel = (bass_midi - chord.root) % 12
    if rel == 0:
        return "root"
    names = ["root", "first", "second", "third"]
    for i, iv in enumerate(chord.intervals):
        if iv == rel:
            return names[i]
    return "nct-bass"


def beat_length(meter: tuple[int, int]) -> Fraction:
    num, den = meter
    unit = Fraction(4, den)
    if den >= 8 and num % 3 == 0 and num > 3:  # compound meter: dotted beat
        return unit * 3
    return unit


def beat_windows(score: KernScore) -> list[tuple[Fraction, Fraction]]:
    """Beat windows aligned to barlines; a pickup before the first barline is aligned to it."""
    meters = score.meters or [(Fraction(0), (4, 4))]

    def meter_at(t: Fraction) -> tuple[int, int]:
        m = meters[0][1]
        for start, mt in meters:
            if start <= t:
                m = mt
        return m

    anchors = sorted({Fraction(0), score.duration, *(b.onset for b in score.barlines)})
    anchors = [a for a in anchors if a <= score.duration]
    windows: list[tuple[Fraction, Fraction]] = []
    for i, (a, b) in enumerate(itertools.pairwise(anchors)):
        if b <= a:
            continue
        step = beat_length(meter_at(a))
        if i == 0 and a == 0 and score.barlines and b == score.barlines[0].onset:
            starts, t = [], b  # pickup: count beats back from the first barline
            while t - step > a:
                t -= step
                starts.append(t)
            edges: list[Fraction] = [a, *reversed(starts), b]
        else:
            edges = [a]
            t = a + step
            while t < b:
                edges.append(t)
                t += step
            edges.append(b)
        windows.extend((e0, e1) for e0, e1 in itertools.pairwise(edges))
    return windows


def harmony_by_beat(
    notes: list[Note], windows: list[tuple[Fraction, Fraction]]
) -> list[BeatHarmony]:
    pitched = sorted(
        (n for n in merge_ties(notes) if not n.is_rest and not n.grace),
        key=lambda n: n.onset,
    )
    out: list[BeatHarmony] = []
    i0 = 0
    for start, end in windows:
        while i0 < len(pitched) and pitched[i0].onset < start - 64:  # notes can't last > 64
            i0 += 1
        weights: dict[int, float] = defaultdict(float)
        bass: int | None = None
        for n in pitched[i0:]:
            if n.onset >= end:
                break
            overlap = min(n.end, end) - max(n.onset, start)
            if overlap <= 0 or n.midi is None:
                continue
            weights[n.midi % 12] += float(overlap)
            bass = n.midi if bass is None else min(bass, n.midi)
        chord = fit_chord(weights)
        if chord is None or bass is None:
            continue
        total = sum(weights.values())
        nct = sum(w for pc, w in weights.items() if pc not in chord.pcs)
        out.append(BeatHarmony(start, end, chord, bass, inversion_of(chord, bass), total, nct))
    return out


def hands(notes: list[Note]) -> tuple[list[Note], list[Note]] | None:
    """(right hand, left hand) for a two-staff layout, else None.

    Uses *staffN markers (staff 1 = top = RH). Files without them but with exactly two **kern
    spines fall back to spine order: kern lists spines bottom staff first, so the higher spine
    index is the RH. Pitch can't decide this, because the hands may cross.
    """
    played = [n for n in notes if not n.is_rest and not n.grace]
    by_staff: dict[int, list[Note]] = defaultdict(list)
    for n in played:
        if n.staff is not None:
            by_staff[n.staff].append(n)
    if not by_staff:
        for n in played:
            by_staff[-n.spine].append(n)  # negate so that sorting puts the top spine first
    if len(by_staff) != 2:
        return None
    top, bottom = sorted(by_staff)
    return by_staff[top], by_staff[bottom]


def _attacks(notes: list[Note]) -> list[list[int]]:
    """MIDI pitches attacked together, per onset, in time order (tie continuations dropped)."""
    groups: dict[Fraction, list[int]] = defaultdict(list)
    for n in notes:
        if n.midi is not None and n.tie not in ("continue", "end"):
            groups[n.onset].append(n.midi)
    return [sorted(groups[t]) for t in sorted(groups)]


def _quantiles(xs: list[float]) -> dict[str, float | None]:
    if not xs:
        return {"p50": None, "p95": None, "max": None}
    s = sorted(xs)
    return {
        "p50": float(median(s)),
        "p95": float(s[min(len(s) - 1, int(0.95 * len(s)))]),
        "max": float(s[-1]),
    }


def _frac(n: int, d: int) -> float | None:
    return n / d if d else None


def piece_stats(score: KernScore) -> dict:
    """All style statistics for one piece, as a flat-ish JSON-able dict."""
    notes = score.notes
    windows = beat_windows(score)
    harm = harmony_by_beat(notes, windows)
    inv = Counter(h.inversion for h in harm)
    n_h = len(harm)
    changes = sum(1 for a, b in itertools.pairwise(harm) if a.end == b.start and a.chord != b.chord)
    contiguous = sum(1 for a, b in itertools.pairwise(harm) if a.end == b.start)
    total_w = sum(h.weight for h in harm)
    stats: dict = {
        "beats": len(windows),
        "harmonized_beats": n_h,
        "inversion": {
            k: _frac(inv[k], n_h) for k in ("root", "first", "second", "third", "nct-bass")
        },
        "seventh_rate": _frac(sum(h.chord.is_seventh for h in harm), n_h),
        "harmonic_change_rate": _frac(changes, contiguous),
        "nct_weight_rate": (sum(h.nct_weight for h in harm) / total_w) if total_w else None,
    }

    split = hands(notes)
    if split is None:
        stats["hands"] = None
        return stats
    rh, lh = split
    rh_att, lh_att = _attacks(rh), _attacks(lh)
    rh_spans = [g[-1] - g[0] for g in rh_att if len(g) > 1]
    lh_spans = [g[-1] - g[0] for g in lh_att if len(g) > 1]
    bass_line = [g[0] for g in lh_att]
    bass_leaps = [abs(b - a) for a, b in itertools.pairwise(bass_line)]
    melody = [g[-1] for g in rh_att]
    mel_iv = [abs(b - a) for a, b in itertools.pairwise(melody)]

    # Melody NCTs: highest RH note per attack vs the fitted chord of its beat.
    rh_onsets = sorted({n.onset for n in rh if n.tie not in ("continue", "end")})
    mel_nct = mel_n = 0
    j = 0
    for t, pitch in zip(rh_onsets, melody, strict=False):
        while j < n_h and harm[j].end <= t:
            j += 1
        if j < n_h and harm[j].start <= t < harm[j].end:
            mel_n += 1
            mel_nct += (pitch % 12) not in harm[j].chord.pcs

    n_beats = max(1, len(windows))
    stats["melody_nct_rate"] = _frac(mel_nct, mel_n)
    stats["hands"] = {
        "rh_span": _quantiles([float(x) for x in rh_spans]),
        "lh_span": _quantiles([float(x) for x in lh_spans]),
        "rh_span_over_octave": _frac(sum(s > 12 for s in rh_spans), len(rh_spans)),
        "lh_span_over_octave": _frac(sum(s > 12 for s in lh_spans), len(lh_spans)),
        "rh_chord_rate": _frac(sum(len(g) >= 3 for g in rh_att), len(rh_att)),
        "lh_leap": _quantiles([float(x) for x in bass_leaps]),
        "lh_leap_over_octave": _frac(sum(x > 12 for x in bass_leaps), len(bass_leaps)),
        "melody_step_rate": _frac(sum(0 < x <= 2 for x in mel_iv), len(mel_iv)),
        "melody_leap_rate": _frac(sum(x > 4 for x in mel_iv), len(mel_iv)),
        "rh_attacks_per_beat": len(rh_att) / n_beats,
        "lh_attacks_per_beat": len(lh_att) / n_beats,
    }
    return stats
