from fractions import Fraction

import music21

from music_ai.score_prep import (
    _meter_for,
    drop_overlapping_rests,
    fill_voice_gaps,
    mark_irregular_bars,
)


def _part(*bars: list[music21.note.GeneralNote], ts: str = "2/4") -> music21.stream.Part:
    p = music21.stream.Part()
    for i, notes in enumerate(bars, 1):
        m = music21.stream.Measure(number=i)
        if i == 1:
            m.insert(0, music21.meter.TimeSignature(ts))
        t = 0.0
        for n in notes:
            m.insert(t, n)
            t += n.quarterLength
        p.append(m)
    return p


def _n(q: float, pitch: str = "C4") -> music21.note.Note:
    return music21.note.Note(pitch, quarterLength=q)


def test_meter_for():
    assert _meter_for(Fraction(6)) == "6/4"
    assert _meter_for(Fraction(9, 2)) == "9/8"
    assert _meter_for(Fraction(37, 8)) == "37/32"


def test_overlapping_rest_dropped_but_notes_kept():
    m = music21.stream.Measure(number=1)
    m.insert(0, music21.note.Rest(quarterLength=2))
    m.insert(1, music21.note.Rest(quarterLength=1))  # overlaps the first rest
    m.insert(1.5, _n(0.5))  # overlaps the first rest: the note wins
    p = music21.stream.Part([m])
    assert drop_overlapping_rests(music21.stream.Score([p])) == 2
    assert [type(e).__name__ for e in m.notesAndRests] == ["Note"]


def test_long_cadenza_bar_gets_its_own_meter_then_original_returns():
    # bar 2 is a 6-beat cadenza in 2/4 in the left hand; the right hand stops at 4 beats
    rh = _part([_n(2)], [_n(1) for _ in range(4)], [_n(2)])
    lh = _part([_n(2)], [_n(3), _n(3)], [_n(2)])
    score = music21.stream.Score([rh, lh])
    assert mark_irregular_bars(score) == [2]
    for p in (rh, lh):
        bars = list(p.getElementsByClass("Measure"))
        assert bars[1].timeSignature.ratioString == "6/4"
        assert bars[2].timeSignature.ratioString == "2/4"
    # the short right hand was filled with a hidden rest to the bar's real length
    assert rh.measure(2).highestTime == 6


def test_voice_gap_filled_to_real_bar_length():
    m = music21.stream.Measure(number=1)
    m.insert(0, music21.meter.TimeSignature("3/4"))
    v1, v2 = music21.stream.Voice(), music21.stream.Voice()
    v1.append([_n(1), _n(1), _n(1)])
    v2.insert(2.75, _n(0.25, "E4"))  # starts late, with nothing before it
    m.insert(0, v1)
    m.insert(0, v2)
    fill_voice_gaps(music21.stream.Score([music21.stream.Part([m])]))
    rests = [r for r in v2.notesAndRests if r.isRest]
    assert rests and rests[0].offset == 0 and all(r.style.hideObjectOnPrint for r in rests)
