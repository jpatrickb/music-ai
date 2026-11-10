"""Voice-leading checks for keyboard-style ABC and **kern scores (warnings, not errors).

Checks, in both formats:

- parallel perfect 5ths and octaves/unisons between any two voices (high), the same intervals
  reached by contrary motion (medium), and hidden/direct 5ths and octaves between the outer
  voices when the soprano leaps (low);
- leading-tone resolution in V / V7 / vii° / vii°7 (including secondary dominants): an outer-voice
  leading tone must rise a half step (an inner-voice leading tone may drop, so it isn't checked);
- chordal 7th resolution: down by step;
- spacing (adjacent upper voices more than an octave apart) and voice crossing between hands.

Usage (same inputs as validate_notation.py):
    uv run experiments/generation/harmony_check.py piece.abc piece.krn
    uv run experiments/generation/harmony_check.py experiments/generation/encoding/abc-reference.md

Exit code is 0 unless a score fails to parse; findings are printed as warnings.

How piano texture becomes voices
--------------------------------
Each ABC voice (V:) or **kern spine is a *stream* (normally RH and LH). Streams are ordered by
mean pitch, so the lowest is the bass stream regardless of file order. The score is cut into
vertical *slices* at every onset (zero-length grace notes and ABC chord symbols, which music21
turns into zero-length notes, are dropped). A slice records which pitches each stream is sounding.
Inside a stream, a chord's notes have no voice identity, so voices are assigned **by rank within
each stream**: the LH's lowest note is the bass, the RH's notes from low to high are tenor, alto,
soprano. A stream whose notes are all one pitch class (octave doubling, e.g. LH `[C,,C,]`) counts
as a single voice.

Strict (all-pairs) checks run only where the texture really is keyboard-style block chords:

- a slice is *block* when it has 3-6 voices and the top stream sounds at least two notes;
- a transition between consecutive slices is *strict* when both slices are block and every stream
  has the same number of notes in both, so rank N in one chord really is rank N in the next.

Everything else (melody over an arpeggiated, Alberti or stride LH, melody over LH chords) gets only
an outer-voice parallel check at low severity, and not per onset (every arpeggio eighth would
become "the bass") but per *harmonic unit*:

- units run between Roman-numeral labels, also split at barlines; with no labels they are half
  bars (even meter numerators: 4/4 beats 1 and 3, 6/8 beats 1 and 4) or whole bars;
- the unit's bass is the lowest bass-stream note attacked on a strong position (bar start or
  half bar) inside it, so a stride LH's off-beat chord never counts; failing that, the lowest
  note sounding at the unit onset;
- the unit's soprano is the top stream's highest note at the unit onset; if the melody rests
  there, its first note in the unit, but only while the unit's bass is still sounding;
- consecutive units are compared for parallel 5ths/octaves (similar motion only). Unit pairs that
  are entirely block chords are left to the strict check.

Spacing (adjacent voices within the upper stream only; the bass-to-tenor gap is free) and crossing
are checked on block slices; the leading-tone and 7th checks on strict transitions only.

Harmonic function (for leading-tone and 7th checks) comes from Roman numerals when the score has
any: kern `**harm` tokens (music21 makes them RomanNumeral objects in the right key) or ABC
`"_V7"`-style annotations (music21 drops these, so they are read from music21's ABC token stream
and matched note-for-note with the parsed part). A key prefix (`"_G: V7"`) sets the key for that
label and later labels until the next K: change. Augmented-sixth labels are never treated as
seventh chords. When a score has no Roman numerals at all, a chord is treated as dominant only if
its pitch classes all belong to V7 (with the root) or vii°7 of the key from K: / `*X:`; anything else
(secondary dominants, chords with extra tones, kern with no `*X:` key) is skipped, not guessed.
A harmony change is detected when the label's root/quality changes (V7 -> V7b is not a change).

Known limits
------------
- Voice crossing *within* a hand is invisible (rank order can't cross). Only crossing between
  streams (e.g. LH above the RH's lowest note) is reported. Voice overlap isn't checked.
- Intervals are by semitone (7 = 5th, 0 mod 12 = octave/unison), so misspellings can't hide a
  parallel, but a diminished 6th would count as a 5th. Unequal 5ths (d5 -> P5) are not flagged.
- Passing and neighbor tones inside block texture create their own slices, so surface parallels
  through non-chord tones are reported like any other (textbooks differ on these).
- Rank-based voices go wrong in block texture where a hand changes its number of notes; those
  transitions fall back to outer-voice-only checks rather than guessing a voice mapping.
- A RH melody doubled in octaves with inner filler (top and bottom of the RH an octave apart in both
  chords) is treated as doubling, not as parallel octaves.
- Leading-tone checks ignore a leading tone that is held into the next chord, and 7th checks
  ignore a held 7th (it may resolve later); neither follows a resolution across a hand.
- Two-voice textures (melody + bass line) get only the low-severity outer-voice check.
- The unit check compares unit onsets only ("downbeat" parallels): parallels between notes in
  the middle of units are not seen, and labelled units are often a whole bar. Without labels, an
  arpeggio that changes register at the half bar can still give a misleading bass.
"""

from __future__ import annotations

import argparse
import itertools
import re
import sys
from dataclasses import dataclass, field
from fractions import Fraction
from pathlib import Path

import music21
from music21 import abcFormat, harmony, key, meter, roman, stream

sys.path.insert(0, str(Path(__file__).resolve().parent))
from validate_notation import Score, extract_scores

SEVERITY_ORDER = {"high": 0, "medium": 1, "low": 2}


class HarmonyParseError(Exception):
    pass


@dataclass(frozen=True)
class Finding:
    check: str  # parallel-5th, parallel-8ve, contrary-5th, ..., hidden-5th, leading-tone, ...
    severity: str  # "high" | "medium" | "low"
    bar: int
    beat: float
    voices: tuple[str, ...]
    reason: str

    def __str__(self) -> str:
        beat = f"{self.beat:g}"
        return (
            f"bar {self.bar} beat {beat}  {self.severity:<6} {self.check:<13} "
            f"{'/'.join(self.voices)}: {self.reason}"
        )


@dataclass
class Report:
    score: Score
    findings: list[Finding] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)
    error: str | None = None


# --- ABC Roman-numeral annotations -----------------------------------------------------------

_NUMERAL = r"[b#-]?(?:VII|VI|IV|V|III|II|I|vii|vi|iv|v|iii|ii|i)[o+ø]?"
_FIGURE_RE = re.compile(rf"(?:{_NUMERAL}\d*(?:/{_NUMERAL})*|(?:N|It|Fr|Ger|Gn|Lt)\+?\d*)")
_KEY_PREFIX_RE = re.compile(r"^([A-Ga-g])([#b-]?)\s*:\s*(.*)$")
_AUG6_RE = re.compile(r"^(?:It|Fr|Ger|Gn|Lt)")
_ABC_ANNOTATION_RE = re.compile(r'"[_^<>@]([^"]*)"')


def parse_abc_figure(text: str) -> tuple[str | None, str] | None:
    """Turn an ABC annotation like "G: V7" or "I6/4" into (music21 key name or None, figure).

    Returns None when the text isn't a Roman numeral (e.g. "cresc."). For a pivot written
    "iii = vi" the first reading is used.
    """
    t = text.strip()
    key_name = None
    m = _KEY_PREFIX_RE.match(t)
    if m:
        letter, acc, t = m.groups()
        acc = "-" if acc == "b" else acc
        key_name = (letter.upper() if letter.isupper() else letter.lower()) + acc
    t = t.split("=")[0]
    t = re.sub(r"\(.*?\)", "", t)  # I(add9) -> I
    t = re.sub(r"(\d)/(\d)", r"\1\2", t)  # I6/4 -> I64 (but keep V7/vi)
    t = t.replace("°", "o").replace(" ", "")
    if not _FIGURE_RE.fullmatch(t):
        return None
    return key_name, t


@dataclass(frozen=True)
class Annotation:
    offset: float
    text: str


def _note_parts(parsed: stream.Score) -> list[stream.Stream]:
    parts = list(parsed.parts) if parsed.parts else [parsed]
    return [p for p in parts if _notes(p)]


def _notes(part: stream.Stream) -> list[music21.note.GeneralNote]:
    flat = part.flatten()
    return [
        n for n in flat.notesAndRests if not isinstance(n, (harmony.Harmony, roman.RomanNumeral))
    ]


def abc_annotations(text: str, parsed: stream.Score | None = None) -> list[Annotation]:
    """Roman-numeral annotations in an ABC tune, with their offsets in quarter notes.

    music21 drops "_..." annotations when it builds the score, so read them from its tokenizer
    and pair the k-th note/chord/rest token of each voice with the k-th note/rest of the parsed
    part (grace notes are counted on both sides). Raises ValueError if the counts disagree.
    """
    if parsed is None:
        parsed = _parse(text, "abc")
    handler = abcFormat.ABCHandler()
    handler.process(text)
    voices = []
    for vh in handler.splitByVoice():
        notes = [t for t in vh.tokens if type(t).__name__ in ("ABCNote", "ABCChord")]
        if notes:
            voices.append(notes)
    parts = _note_parts(parsed)
    if len(voices) != len(parts):
        raise ValueError(f"{len(voices)} ABC voices but music21 built {len(parts)} parts")
    out = []
    for tokens, part in zip(voices, parts, strict=True):
        flat = part.flatten()
        elements = _notes(part)
        if len(tokens) != len(elements):
            raise ValueError(
                f"{len(tokens)} ABC note tokens but music21 built {len(elements)} notes"
            )
        for tok, el in zip(tokens, elements, strict=True):
            for ann in _ABC_ANNOTATION_RE.findall(tok.src):
                if parse_abc_figure(ann) is not None:
                    out.append(Annotation(float(flat.elementOffset(el)), ann))
    return sorted(out, key=lambda a: a.offset)


# --- harmony labels --------------------------------------------------------------------------


@dataclass(frozen=True)
class Label:
    name: str  # for messages, e.g. "V7" or "V7/vi"
    ident: tuple  # chords with equal ident are "the same harmony"
    leading_tone: int | None = None  # pitch class, for dominant-function chords
    seventh: int | None = None  # pitch class of the chordal 7th


UNKNOWN = Label("?", ("unknown",))


def _label_from_rn(rn: roman.RomanNumeral, name: str | None = None) -> Label:
    name = name or rn.figure
    if rn.isAugmentedSixth():
        return Label(name, ("aug6", name))
    q = rn.quality
    lt = None
    if rn.scaleDegree == 5 and q == "major":
        lt = rn.third.pitchClass
    elif rn.scaleDegree == 7 and q in ("diminished", "half-diminished"):
        lt = rn.root().pitchClass
    seventh = rn.seventh.pitchClass if rn.seventh is not None else None
    return Label(name, (rn.root().name, q), lt, seventh)


def _label_from_figure(figure: str, k: key.Key) -> Label:
    if _AUG6_RE.match(figure):
        return Label(figure, ("aug6", figure))
    try:
        return _label_from_rn(roman.RomanNumeral(figure, k), figure)
    except Exception:  # noqa: BLE001 -- music21 raises assorted errors on odd figures
        return UNKNOWN


def _label_from_content(pcs: set[int], k: key.Key) -> Label:
    """Dominant function from chord content alone: only V/V7 or vii°/vii°7 of the key.

    V(7) = the dominant root plus any other V7 tones and nothing else. That includes V7 without
    its leading tone (e.g. D-A-C in G), so moving between chord tones inside one V7 is not mistaken
    for a resolution. vii°(7) needs leading tone, 2 and 4, plus at most a (lowered) 6.
    """
    t = k.tonic.pitchClass
    dom, lt, two, four = (t + 7) % 12, (t + 11) % 12, (t + 2) % 12, (t + 5) % 12
    six = {(t + 8) % 12, (t + 9) % 12}
    if dom in pcs and len(pcs) >= 2 and pcs <= {dom, lt, two, four}:
        return Label("V7" if four in pcs else "V", ("dominant", t), lt, four)
    if {lt, two, four} <= pcs <= {lt, two, four} | six:
        sev = next(iter(pcs & six), None)
        return Label("viio7" if sev is not None else "viio", ("dominant", t), lt, sev)
    return Label("?", ("other", frozenset(pcs)))


# --- slices ----------------------------------------------------------------------------------


@dataclass(frozen=True)
class Event:
    offset: Fraction
    end: Fraction
    pitches: tuple[music21.pitch.Pitch, ...]


@dataclass
class Slice:
    offset: Fraction
    streams: list[list[music21.pitch.Pitch]]  # per stream, low -> high

    @property
    def voices(self) -> list[music21.pitch.Pitch]:
        return [p for s in self.streams for p in s]

    @property
    def counts(self) -> tuple[int, ...]:
        return tuple(len(s) for s in self.streams)

    @property
    def is_block(self) -> bool:
        return 3 <= len(self.voices) <= 6 and len(self.streams[-1]) >= 2

    def voice_stream(self, i: int) -> int:
        for si, s in enumerate(self.streams):
            if i < len(s):
                return si
            i -= len(s)
        raise IndexError(i)


def _voice_names(n: int) -> list[str]:
    if n == 4:
        return ["bass", "tenor", "alto", "soprano"]
    if n == 3:
        return ["bass", "alto", "soprano"]
    if n == 2:
        return ["bass", "soprano"]
    return ["bass", *[f"voice{i}" for i in range(2, n)], "soprano"]


def _events(part: stream.Stream) -> list[Event]:
    flat = part.flatten()
    out = []
    for n in _notes(part):
        ql = Fraction(n.quarterLength).limit_denominator(1000)
        if ql == 0 or n.isRest:
            continue
        off = Fraction(flat.elementOffset(n)).limit_denominator(1000)
        out.append(Event(off, off + ql, tuple(n.pitches)))
    return out


def _slices(streams: list[list[Event]]) -> list[Slice]:
    onsets = sorted({e.offset for s in streams for e in s})
    slices = []
    for t in onsets:
        per_stream = []
        for si, events in enumerate(streams):
            pitches = {}
            for e in events:
                if e.offset <= t < e.end:
                    for p in e.pitches:
                        pitches.setdefault(p.ps, p)
            ps = [pitches[k] for k in sorted(pitches)]
            if len(ps) > 1 and len({p.pitchClass for p in ps}) == 1:
                ps = [ps[0]] if si == 0 else [ps[-1]]  # octave doubling = one voice
            per_stream.append(ps)
        if any(per_stream):
            slices.append(Slice(t, per_stream))
    return slices


# --- bar / beat ------------------------------------------------------------------------------


Bar = tuple[Fraction, int, meter.TimeSignature]  # (start offset, bar number, meter)


def _bars(parts: list[stream.Stream], fmt: str, end: Fraction) -> list[Bar]:
    """Bar starts. ABC bars are counted by position (music21's numbering depends on pickups)."""
    ts0 = next(iter(parts[0].flatten().getElementsByClass(meter.TimeSignature)), None)
    ts0 = ts0 or meter.TimeSignature("4/4")
    measured = next((p for p in parts if p.getElementsByClass(stream.Measure)), None)
    bars: list[Bar] = []
    if measured is not None:
        for i, m in enumerate(measured.getElementsByClass(stream.Measure)):
            ts = m.timeSignature or m.getContextByClass(meter.TimeSignature) or ts0
            number = m.number if fmt == "kern" and m.number else i + 1
            bars.append((Fraction(m.offset).limit_denominator(1000), number, ts))
    if not bars:  # music21 builds no ABC measures with fewer than 2 barlines
        bar_ql = Fraction(ts0.barDuration.quarterLength).limit_denominator(1000)
        bars = [(i * bar_ql, i + 1, ts0) for i in range(int(end // bar_ql) + 1)]
    return bars


def _bar_locator(bars: list[Bar]):
    def locate(offset: Fraction) -> tuple[int, float]:
        start, number, ts = next((b for b in reversed(bars) if b[0] <= offset), bars[0])
        beat = float((offset - start) / Fraction(ts.beatDuration.quarterLength)) + 1
        return number, round(beat, 3)

    return locate


def _strong_positions(bars: list[Bar]) -> list[Fraction]:
    """Bar starts, plus the half bar when the meter's numerator is even (4/4 beat 3, 6/8 beat 4)."""
    out = []
    for start, _, ts in bars:
        out.append(start)
        if ts.numerator % 2 == 0:
            out.append(start + Fraction(ts.barDuration.quarterLength).limit_denominator(1000) / 2)
    return sorted(set(out))


# --- checks ----------------------------------------------------------------------------------


def _sign(x: float) -> int:
    return (x > 0) - (x < 0)


def _check_pairs(a: Slice, b: Slice, names: list[str]) -> list[tuple]:
    """(check, severity, voice names, reason) for one strict (block-chord) transition."""
    out = []
    va, vb = a.voices, b.voices
    pairs = [(i, j) for i in range(len(va)) for j in range(i + 1, len(va))]
    bass, sop = 0, len(va) - 1
    for i, j in pairs:
        res = _motion(va[i], vb[i], va[j], vb[j])
        if res is None:
            continue
        kind, interval = res
        if kind in ("parallel", "contrary"):
            si, sj = a.voice_stream(i), a.voice_stream(j)
            if interval == "8ve" and si == sj and _is_octave_doubling(a, si, i, j):
                continue
            sev = "high" if kind == "parallel" else "medium"
            out.append(
                (
                    f"{kind}-{interval}",
                    sev,
                    (names[i], names[j]),
                    (
                        f"{_pair(va[i], va[j])} -> {_pair(vb[i], vb[j])}: {_word(interval)} by "
                        f"{'parallel' if kind == 'parallel' else 'contrary'} motion"
                    ),
                )
            )
        elif kind == "hidden" and (i, j) == (bass, sop):
            out.append(
                (
                    f"hidden-{interval}",
                    "low",
                    (names[i], names[j]),
                    (
                        f"{_pair(va[i], va[j])} -> {_pair(vb[i], vb[j])}: outer voices reach a "
                        f"{_word(interval)[:-1]} in similar motion with a soprano leap"
                    ),
                )
            )
    return out


def _motion(lo_a, lo_b, hi_a, hi_b) -> tuple[str, str] | None:
    """Classify the motion of two voices into a perfect interval, or None."""
    mi, mj = lo_b.ps - lo_a.ps, hi_b.ps - hi_a.ps
    ca, cb = abs(hi_a.ps - lo_a.ps) % 12, abs(hi_b.ps - lo_b.ps) % 12
    if cb not in (0, 7):
        return None
    interval = "5th" if cb == 7 else "8ve"
    if mi == 0 or mj == 0:
        return None
    if lo_a.pitchClass == lo_b.pitchClass and hi_a.pitchClass == hi_b.pitchClass:
        return None  # octave displacement, not a new interval
    if ca == cb:
        return ("parallel" if _sign(mi) == _sign(mj) else "contrary"), interval
    if _sign(mi) == _sign(mj) and abs(mj) > 2:
        return "hidden", interval
    return None


def _is_octave_doubling(a: Slice, si: int, i: int, j: int) -> bool:
    """i and j are the bottom and top of stream si in both chords (RH melody in octaves)."""
    start = sum(len(s) for s in a.streams[:si])
    n = len(a.streams[si])
    return n >= 3 and i == start and j == start + n - 1


def _pair(lo, hi) -> str:
    return f"{lo.nameWithOctave}-{hi.nameWithOctave}"


def _word(interval: str) -> str:
    return "5ths" if interval == "5th" else "octaves/unisons"


def _unit_bass(
    events: list[Event], u0: Fraction, u1: Fraction, strong: set[Fraction]
) -> tuple[music21.pitch.Pitch, Fraction] | None:
    """(pitch, end time) of the lowest bass-stream note attacked on a strong position in [u0, u1).

    Falls back to the lowest note sounding at u0, then to the lowest note attacked in the unit.
    Strong-position notes only, so a stride LH's off-beat chord and the middle of an arpeggio
    don't become "the bass".
    """
    in_unit = [e for e in events if u0 <= e.offset < u1]
    pool = (
        [e for e in in_unit if e.offset in strong]
        or [e for e in events if e.offset <= u0 < e.end]
        or in_unit
    )
    return min(((p, e.end) for e in pool for p in e.pitches), key=lambda x: x[0].ps, default=None)


def _unit_top(
    events: list[Event], u0: Fraction, u1: Fraction
) -> tuple[music21.pitch.Pitch, Fraction] | None:
    """(pitch, time) of the top-stream note at u0, else the highest note of its first attack."""
    pool = [e for e in events if e.offset <= u0 < e.end]
    t = u0
    if not pool:
        attacks = [e for e in events if u0 <= e.offset < u1]
        if not attacks:
            return None
        t = min(e.offset for e in attacks)
        pool = [e for e in attacks if e.offset == t]
    return max((p for e in pool for p in e.pitches), key=lambda p: p.ps), t


def _unit_outer(
    streams: list[list[Event]], u0: Fraction, u1: Fraction, strong: set[Fraction]
) -> tuple[music21.pitch.Pitch, music21.pitch.Pitch] | None:
    """(bass, soprano) of one harmonic unit, or None if they never sound together.

    If the melody rests at the unit onset, its first note in the unit is used, but only while
    the unit's bass note is still sounding (a walking bass may have moved on by then).
    """
    bass, top = _unit_bass(streams[0], u0, u1, strong), _unit_top(streams[-1], u0, u1)
    if bass is None or top is None or top[1] >= bass[1]:
        return None
    return bass[0], top[0]


def _outer_voice_units(
    streams: list[list[Event]],
    slices: list[Slice],
    bars: list[Bar],
    label_onsets: list[Fraction],
    end: Fraction,
) -> list[tuple[Fraction, tuple]]:
    """Outer-voice parallels between consecutive harmonic units, for non-block textures.

    A unit runs between Roman-numeral labels, also split at barlines; without labels, units are
    half bars (even numerators) or whole bars. The bass is taken from strong-position notes of
    the lowest stream (see _unit_bass), the soprano is the top stream's note at the unit onset
    (see _unit_outer for a melody that enters after the onset).
    Unit pairs whose slices are all block chords with constant counts are left to the strict
    per-slice check.
    """
    if len(streams) < 2:
        return []
    strong = _strong_positions(bars)
    if label_onsets:
        bounds = {b[0] for b in bars} | set(label_onsets)
    else:
        bounds = set(strong)
    bounds = sorted(b for b in bounds | {Fraction(0)} if b < end)
    strong_set = set(strong)
    units = [
        (u0, u1, _unit_outer(streams, u0, u1, strong_set))
        for u0, u1 in zip(bounds, [*bounds[1:], end], strict=True)
    ]
    out = []
    for (a0, _, outer_a), (b0, b1, outer_b) in itertools.pairwise(units):
        if outer_a is None or outer_b is None:
            continue
        (ba, sa), (bb, sb) = outer_a, outer_b
        span = [s for s in slices if a0 <= s.offset < b1]
        if span and all(s.is_block for s in span) and len({s.counts for s in span}) == 1:
            continue
        res = _motion(ba, bb, sa, sb)
        if res and res[0] == "parallel":
            reason = (
                f"{_pair(ba, sa)} -> {_pair(bb, sb)}: parallel {_word(res[1])} between outer "
                "voices across harmonic units (texture is not block chords; lower confidence)"
            )
            out.append((b0, (f"parallel-{res[1]}", "low", ("bass", "soprano"), reason)))
    return out


def _check_resolution(a: Slice, b: Slice, label: Label, names: list[str]) -> list[tuple]:
    out = []
    va, vb = a.voices, b.voices
    if label.leading_tone is not None:
        for idx in sorted({0, len(va) - 1}):
            pa, pb = va[idx], vb[idx]
            if pa.pitchClass != label.leading_tone or pb.ps == pa.ps:
                continue
            if pb.ps - pa.ps != 1:
                out.append(
                    (
                        "leading-tone",
                        "medium",
                        (names[idx],),
                        (
                            f"leading tone {pa.nameWithOctave} of {label.name} in the {names[idx]} "
                            f"moves to {pb.nameWithOctave}, not up a half step"
                        ),
                    )
                )
    if label.seventh is not None:
        for idx, (pa, pb) in enumerate(zip(va, vb, strict=True)):
            if pa.pitchClass != label.seventh or pb.ps == pa.ps:
                continue
            if pb.ps - pa.ps not in (-1, -2):
                out.append(
                    (
                        "seventh",
                        "medium",
                        (names[idx],),
                        (
                            f"chordal 7th {pa.nameWithOctave} of {label.name} in the {names[idx]} "
                            f"moves to {pb.nameWithOctave}, not down by step"
                        ),
                    )
                )
    return out


def _check_slice(s: Slice, names: list[str]) -> list[tuple]:
    out = []
    v = s.voices
    # Adjacent voices within the upper stream (RH) only; the bass-to-tenor gap is free.
    first = len(v) - len(s.streams[-1])
    upper = [i for i in range(max(first, 1), len(v))]
    for lo, hi in itertools.pairwise(upper):
        if v[hi].ps - v[lo].ps > 12:
            out.append(
                (
                    "spacing",
                    "medium",
                    (names[lo], names[hi]),
                    f"{_pair(v[lo], v[hi])}: adjacent upper voices more than an octave apart",
                )
            )
    start = 0
    for k in range(len(s.streams) - 1):
        lo_s, hi_s = s.streams[k], s.streams[k + 1]
        start += len(lo_s)
        if lo_s and hi_s and lo_s[-1].ps > hi_s[0].ps:
            out.append(
                (
                    "crossing",
                    "medium",
                    (names[start - 1], names[start]),
                    (
                        f"{lo_s[-1].nameWithOctave} (lower hand) is above {hi_s[0].nameWithOctave} "
                        "(upper hand)"
                    ),
                )
            )
    return out


# --- driver ----------------------------------------------------------------------------------


def _parse(text: str, fmt: str) -> stream.Score:
    try:
        return music21.converter.parse(text, format="abc" if fmt == "abc" else "humdrum")
    except Exception as e:
        raise HarmonyParseError(f"music21 failed to parse: {type(e).__name__}: {e}") from e


def _keys(parts: list[stream.Stream]) -> list[tuple[Fraction, key.Key]]:
    found = {}
    for p in parts:
        flat = p.flatten()
        for k in flat.getElementsByClass(key.Key):
            found.setdefault(Fraction(flat.elementOffset(k)).limit_denominator(1000), k)
    return sorted(found.items(), key=lambda kv: kv[0])


def _active[T](timeline: list[tuple[Fraction, T]], t: Fraction) -> T | None:
    current = None
    for off, item in timeline:
        if off > t:
            break
        current = item
    return current


def _harmony_timeline(
    parsed: stream.Score, parts, text: str, fmt: str, notes: list[str]
) -> list[tuple[Fraction, Label]] | None:
    """Labels from Roman numerals, or None when the score has none."""
    if fmt == "kern":
        rns = []
        for p in parsed.parts:
            flat = p.flatten()
            for rn in flat.getElementsByClass(roman.RomanNumeral):
                off = Fraction(flat.elementOffset(rn)).limit_denominator(1000)
                rns.append((off, _label_from_rn(rn)))
        return sorted(rns, key=lambda x: x[0]) or None
    if '"_' not in text and '"^' not in text:
        return None
    try:
        anns = abc_annotations(text, parsed)
    except ValueError as e:
        notes.append(f"Roman-numeral annotations not aligned ({e}); LT/7th checks skipped")
        return []
    if not anns:
        return None
    keys = _keys(parts)
    out = []
    prefix_key, prefix_under = None, None
    default_key = key.Key("C")
    for a in anns:
        off = Fraction(a.offset).limit_denominator(1000)
        score_key = _active(keys, off) or default_key
        if prefix_under is not score_key:
            prefix_key = None  # a K: change ends a "G: ..." key area
        parsed_figure = parse_abc_figure(a.text)
        assert parsed_figure is not None  # abc_annotations keeps only parseable figures
        key_name, figure = parsed_figure
        if key_name:
            prefix_key, prefix_under = key.Key(key_name), score_key
        out.append((off, _label_from_figure(figure, prefix_key or score_key)))
    return out


def check_text(text: str, fmt: str, notes: list[str] | None = None) -> list[Finding]:
    """All voice-leading findings for one ABC or kern score. Raises HarmonyParseError."""
    notes = notes if notes is not None else []
    parsed = _parse(text, fmt)
    parts = _note_parts(parsed)
    if not parts:
        raise HarmonyParseError("music21 parsed no notes")
    parts.sort(key=_mean_pitch)
    streams = [_events(p) for p in parts]
    slices = _slices(streams)
    end = max(e.end for st in streams for e in st)
    bars = _bars(parts, fmt, end)
    locate = _bar_locator(bars)

    timeline = _harmony_timeline(parsed, parts, text, fmt, notes)
    keys = _keys(parts)
    if timeline is None and not keys:
        notes.append("no Roman numerals and no key: LT/7th checks skipped")

    def label_at(s: Slice) -> Label:
        if timeline is not None:
            return _active(timeline, s.offset) or UNKNOWN
        k = _active(keys, s.offset)
        if k is None:
            return UNKNOWN
        return _label_from_content({p.pitchClass for p in s.voices}, k)

    raw: list[tuple[Fraction, tuple]] = []
    prev_block = None
    for s in slices:
        if s.is_block:
            if prev_block is None or [p.ps for p in prev_block.voices] != [p.ps for p in s.voices]:
                raw += [(s.offset, r) for r in _check_slice(s, _voice_names(len(s.voices)))]
            prev_block = s
        else:
            prev_block = None

    skipped = 0
    for a, b in itertools.pairwise(slices):
        strict = a.is_block and b.is_block and a.counts == b.counts
        names = _voice_names(len(a.voices))
        if strict:
            raw += [(b.offset, r) for r in _check_pairs(a, b, names)]
        la, lb = label_at(a), label_at(b)
        if la.ident == lb.ident or (la.leading_tone is None and la.seventh is None):
            continue
        if strict:
            raw += [(b.offset, r) for r in _check_resolution(a, b, la, names)]
        else:
            skipped += 1
    if skipped:
        notes.append(f"{skipped} resolution(s) not checked: texture is not block chords there")

    label_onsets = [off for off, _ in timeline] if timeline else []
    raw += _outer_voice_units(streams, slices, bars, label_onsets, end)

    findings = []
    for off, (check, sev, voices, reason) in raw:
        bar, beat = locate(off)
        findings.append(Finding(check, sev, bar, beat, voices, reason))
    findings.sort(key=lambda f: (f.bar, f.beat, SEVERITY_ORDER[f.severity], f.check))
    return findings


def _mean_pitch(part: stream.Stream) -> float:
    ps = [p.ps for n in _notes(part) if not n.isRest for p in n.pitches]
    return sum(ps) / len(ps) if ps else 0.0


def check_score(score: Score) -> Report:
    report = Report(score)
    try:
        report.findings = check_text(score.text, score.fmt, report.notes)
    except HarmonyParseError as e:
        report.error = str(e)
    return report


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    ap.add_argument("paths", nargs="+", type=Path)
    ap.add_argument("-v", "--verbose", action="store_true", help="also print skipped-check notes")
    args = ap.parse_args(argv)

    scores = [s for p in args.paths for s in extract_scores(p)]
    if not scores:
        print("no abc/kern scores found", file=sys.stderr)
        return 1

    failed = 0
    total = 0
    for score in scores:
        r = check_score(score)
        if r.error:
            status = "FAIL"
        elif r.findings:
            status = "warn"
        else:
            status = "ok  "
        print(f"{status} [{score.fmt}] {score.label}")
        if r.error:
            print(f"     error: {r.error}")
        for f in r.findings:
            print(f"     {f}")
        if args.verbose:
            for n in r.notes:
                print(f"     note: {n}")
        failed += bool(r.error)
        total += len(r.findings)

    print(f"\n{total} voice-leading warning(s) in {len(scores)} score(s); {failed} failed to parse")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
