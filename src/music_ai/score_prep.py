"""Prepare a music21 score read from MusicXML so kern converters place every note correctly.

User-uploaded MusicXML is often slightly inconsistent in ways that don't change the music but
do confuse converters (see scripts/musicxml_to_kern.py). Each function here fixes one such
inconsistency without changing any sounding note; the conversion is then verified note for note
(``music_ai.score_check``), so a mistake here can only cause a rejection, never a silent error.
"""

from __future__ import annotations

from fractions import Fraction

import music21


def drop_orphan_pedals(score: music21.stream.Score) -> int:
    dropped = 0
    for sp in list(score.recurse().getElementsByClass(music21.spanner.Spanner)):
        if type(sp).__name__ != "PedalMark":
            continue
        try:
            for el in sp.getSpannedElements():
                el.getOffsetInHierarchy(score)
        except music21.sites.SitesException:
            sp.activeSite.remove(sp)
            dropped += 1
    return dropped


def _q(x: float | Fraction) -> Fraction:
    return Fraction(x).limit_denominator(100_000)


def _content(m: music21.stream.Measure) -> Fraction:
    """Where the last note or rest in a measure ends, in quarters from the bar start."""
    return max(
        (_q(n.getOffsetInHierarchy(m)) + _q(n.quarterLength) for n in m.recurse().notesAndRests),
        default=Fraction(0),
    )


def _aligned_bars(score: music21.stream.Score) -> list[tuple[music21.stream.Measure, ...]] | None:
    """The measures of all parts grouped by bar, or None if the parts don't line up."""
    parts = [list(p.getElementsByClass("Measure")) for p in score.parts]
    if not all(parts) or len({len(ms) for ms in parts}) != 1:
        return None
    return list(zip(*parts, strict=True))


def _meter_for(length: Fraction) -> str:
    """A time signature spanning ``length`` quarters (6 -> 6/4, 4.5 -> 9/8, 4.625 -> 37/32)."""
    den = 4
    while (length * den / 4).denominator != 1:
        den *= 2
    return f"{(length * den / 4).numerator}/{den}"


def drop_overlapping_rests(score: music21.stream.Score) -> int:
    """Remove rests that overlap a note, or an earlier kept rest, in the same voice (notes claim
    their time first). Overlaps are impossible in one voice, and some converters read such rests
    one after another, pushing the rest of the piece late. Rests don't sound, so nothing audible
    changes; the gaps are refilled by ``fill_voice_gaps``."""
    dropped = 0
    for m in score.recurse().getElementsByClass("Measure"):
        for v in m.voices or [m]:
            notes = [n for n in v.notes if not n.duration.isGrace]
            busy = [(_q(n.offset), _q(n.offset) + _q(n.quarterLength)) for n in notes]
            for r in sorted(v.getElementsByClass("Rest"), key=lambda n: _q(n.offset)):
                start, end = _q(r.offset), _q(r.offset) + _q(r.quarterLength)
                if any(s < end and start < e for s, e in busy):
                    _move_spanners_off(r, v)
                    v.remove(r)
                    dropped += 1
                else:
                    busy.append((start, end))
    return dropped


def _move_spanners_off(el: music21.base.Music21Object, voice: music21.stream.Stream) -> None:
    """Before removing ``el``, point any spanner (pedal, ottava, slur...) that starts or ends on
    it at the nearest other note or rest in the same voice, so no spanner refers to something
    missing from the score."""
    others = [n for n in voice.notesAndRests if n is not el]
    if not others:
        return
    nearest = min(others, key=lambda n: abs(_q(n.offset) - _q(el.offset)))
    for sp in el.getSpannerSites():
        sp.replaceSpannedElement(el, nearest)


def mark_irregular_bars(score: music21.stream.Score) -> list[int]:
    """Give a bar whose real length (its longest staff) differs from its time signature a time
    signature of that length, so every tool agrees where bars start: a free cadenza written longer
    than the meter, or a bar left short. Targets come from the original signatures (a bar's own,
    else the one in force); only changed bars, and the bar after each to restore its original,
    are touched. The first bar, which may be a pickup, is left alone. Short staves in a changed
    bar get a hidden rest to fill it. Returns the bar numbers changed."""
    bars = _aligned_bars(score)
    if bars is None:
        return []
    targets: list[str | None] = []
    lengths: list[Fraction] = []
    changed: set[int] = set()
    for i, group in enumerate(bars):
        ts = group[0].timeSignature or group[0].getContextByClass("TimeSignature")
        length = max(_content(m) for m in group)
        lengths.append(length)
        if ts is None or length == 0 or i == 0 or length == _q(ts.barDuration.quarterLength):
            targets.append(ts.ratioString if ts else None)
        else:
            targets.append(_meter_for(length))
            changed.add(i)
    for i, group in enumerate(bars):
        if i not in changed and (i - 1) not in changed:
            continue
        for m in group:
            for t in list(m.getElementsByClass("TimeSignature")):
                m.remove(t)
            if targets[i] is not None:
                m.insert(0, music21.meter.TimeSignature(targets[i]))
            if i in changed:
                for v in m.voices or [m]:
                    end = max(
                        (_q(n.offset) + _q(n.quarterLength) for n in v.notesAndRests),
                        default=Fraction(0),
                    )
                    if end < lengths[i]:
                        r = music21.note.Rest(quarterLength=lengths[i] - end)
                        r.style.hideObjectOnPrint = True
                        v.insert(end, r)
    return sorted(bars[i][0].number for i in changed)


def fill_voice_gaps(score: music21.stream.Score) -> None:
    """Hidden rests where a voice starts partway into a bar (a deleted rest in MuseScore) or stops
    short, up to the bar's real length: its longest staff, not music21's bar duration, which
    follows a time-signature lookup that can be wrong. Converters otherwise misplace what follows.
    Rests don't sound, so the check is unaffected."""
    bars = _aligned_bars(score)
    lengths: dict[int, Fraction] = {}
    if bars is not None:
        for group in bars:
            length = max(_content(m) for m in group)
            lengths.update({id(m): length for m in group})
    for m in score.recurse().getElementsByClass("Measure"):
        length = lengths.get(id(m)) or _content(m)
        for v in m.voices:
            if length:
                v.makeRests(
                    refStreamOrTimeRange=[0, length], fillGaps=True, hideRests=True, inPlace=True
                )


def move_spanner_ends_off_rests(score: music21.stream.Score) -> int:
    """Point marks that start or end on a rest at the nearest note in the same staff (by time).
    converter21 re-splits some rests (e.g. in tuplets) while writing and then can't find a mark's
    end; used only as a fallback when it crashes that way. Pedal marks and hairpins with no note
    to move to are dropped. No notes change."""
    staff_notes = []
    for part in score.parts:
        notes = [n for n in part.recurse().notes if not n.duration.isGrace]
        staff_notes.append((part, [(_q(n.getOffsetInHierarchy(score)), n) for n in notes]))
    moved = 0
    for sp in list(score.spannerBundle):
        for el in list(sp.getSpannedElements()):
            if not isinstance(el, music21.note.Rest):
                continue
            target = None
            try:
                t = _q(el.getOffsetInHierarchy(score))
                part = el.getContextByClass("Part")
                notes = next((ns for p, ns in staff_notes if p is part), [])
                if notes:
                    target = min(notes, key=lambda on: abs(on[0] - t))[1]
            except music21.sites.SitesException:
                pass
            if target is not None:
                sp.replaceSpannedElement(el, target)
                moved += 1
            elif type(sp).__name__ in ("PedalMark", "Crescendo", "Diminuendo"):
                score.spannerBundle.remove(sp)
                for site in list(sp.sites.get()):
                    if hasattr(site, "remove") and sp in site:
                        site.remove(sp)
                break
    return moved
