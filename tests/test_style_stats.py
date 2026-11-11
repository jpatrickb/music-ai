from fractions import Fraction as F

import pytest

from music_ai.kern import parse_kern
from music_ai.style_stats import (
    Chord,
    beat_length,
    beat_windows,
    fit_chord,
    inversion_of,
    piece_stats,
)


def kern(*rows: str) -> str:
    return "\n".join(rows) + "\n"


def test_fit_chord_triad_and_seventh():
    c = fit_chord({0: 1.0, 4: 1.0, 7: 1.0})
    assert (c.root, c.kind) == (0, "maj")
    g7 = fit_chord({7: 1.0, 11: 1.0, 2: 1.0, 5: 1.0})
    assert (g7.root, g7.kind) == (7, "dom7")
    am = fit_chord({9: 1.0, 0: 1.0, 4: 1.0})
    assert (am.root, am.kind) == (9, "min")


def test_fit_chord_passing_tone_does_not_change_the_chord():
    # C major with a short D passing tone.
    c = fit_chord({0: 2.0, 4: 2.0, 7: 2.0, 2: 0.25})
    assert (c.root, c.kind) == (0, "maj")


def test_fit_chord_needs_two_pitch_classes():
    assert fit_chord({0: 3.0}) is None


@pytest.mark.parametrize(
    ("bass", "inv"), [(48, "root"), (52, "first"), (55, "second"), (50, "nct-bass")]
)
def test_inversion_of_triad(bass, inv):
    assert inversion_of(Chord(0, "maj", (0, 4, 7)), bass) == inv


def test_inversion_of_seventh_third_inversion():
    assert inversion_of(Chord(7, "dom7", (0, 4, 7, 10)), 53) == "third"  # F under G7


@pytest.mark.parametrize(
    ("meter", "beat"),
    [
        ((4, 4), F(1)),
        ((3, 4), F(1)),
        ((2, 2), F(2)),
        ((6, 8), F(3, 2)),
        ((12, 8), F(3, 2)),
        ((3, 8), F(1, 2)),
    ],
)
def test_beat_length(meter, beat):
    assert beat_length(meter) == beat


def test_beat_windows_align_pickup_to_first_barline():
    s = parse_kern(kern("**kern", "*M3/4", "4g", "=1", "2.c", "==", "*-"))
    assert beat_windows(s) == [(F(0), F(1)), (F(1), F(2)), (F(2), F(3)), (F(3), F(4))]


PIANO_HEADER = ("**kern\t**kern", "*staff2\t*staff1", "*M4/4\t*M4/4")


def test_root_position_progression():
    # I - IV - V - I, bass on the root each time, RH block chords.
    s = parse_kern(
        kern(
            *PIANO_HEADER,
            "=1\t=1",
            "4C\t4e 4g 4cc",
            "4F\t4f 4a 4cc",
            "4G\t4d 4g 4b",
            "4C\t4e 4g 4cc",
            "==\t==",
            "*-\t*-",
        )
    )
    st = piece_stats(s)
    assert st["inversion"]["root"] == 1.0
    assert st["harmonic_change_rate"] == 1.0
    assert st["nct_weight_rate"] == 0.0
    h = st["hands"]
    assert h["rh_chord_rate"] == 1.0
    assert h["rh_span"]["max"] == 9.0  # D4..B4
    assert h["lh_leap"]["max"] == 7.0  # G2..C3
    assert st["melody_nct_rate"] == 0.0


def test_inversions_and_melody_nct():
    # C major over E (first inversion) for a whole bar; the melody has one passing D.
    s = parse_kern(
        kern(
            "**kern\t**kern\t**kern",
            "*staff2\t*staff1\t*staff1",
            "*M4/4\t*M4/4\t*M4/4",
            "=1\t=1\t=1",
            "1E\t1c 1g\t4cc",
            ".\t.\t8dd",
            ".\t.\t8ee",
            ".\t.\t4cc",
            ".\t.\t4cc",
            "==\t==\t==",
            "*-\t*-\t*-",
        )
    )
    st = piece_stats(s)
    assert st["inversion"]["first"] == 1.0
    assert st["melody_nct_rate"] == pytest.approx(1 / 5)
    assert 0 < st["nct_weight_rate"] < 0.1


def test_hands_none_for_four_voice_chorale():
    s = parse_kern(
        kern(
            "**kern\t**kern\t**kern\t**kern",
            "*M4/4\t*M4/4\t*M4/4\t*M4/4",
            "4C\t4G\t4e\t4cc",
            "*-\t*-\t*-\t*-",
        )
    )
    st = piece_stats(s)
    assert st["hands"] is None
    assert st["inversion"]["root"] == 1.0


def test_span_over_octave_detected():
    s = parse_kern(kern(*PIANO_HEADER, "1C\t1c 1eee", "*-\t*-"))
    assert piece_stats(s)["hands"]["rh_span_over_octave"] == 1.0


def test_hands_fall_back_to_spine_order_without_staff_markers():
    from music_ai.style_stats import hands

    s = parse_kern(kern("**kern\t**kern", "1C\t1e 1g", "*-\t*-"))
    rh, lh = hands(s.notes)
    assert [n.name for n in rh] == ["E4", "G4"]
    assert [n.name for n in lh] == ["C3"]
