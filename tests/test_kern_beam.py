from music_ai.kern import parse_kern
from music_ai.kern_beam import add_beams, beat_unit


def kern(*rows: str) -> str:
    return "\n".join(rows) + "\n"


def data(text: str) -> list[str]:
    return [ln for ln in text.splitlines() if ln and ln[0] not in "*=!"]


def test_beams_eighths_per_beat_in_simple_meter():
    out = add_beams(kern("**kern", "*M2/4", "=1", "8c", "8d", "8e", "8f", "==", "*-"))
    assert data(out) == ["8cL", "8dJ", "8eL", "8fJ"]


def test_compound_meter_beams_in_threes():
    out = add_beams(kern("**kern", "*M6/8", "=1", "8c", "8d", "8e", "8f", "8g", "8a", "==", "*-"))
    assert data(out) == ["8cL", "8d", "8eJ", "8fL", "8g", "8aJ"]


def test_rests_and_long_notes_break_beams_and_single_notes_stay_flagged():
    out = add_beams(
        kern("**kern", "*M4/4", "=1", "8c", "8r", "4d", "8e", "16f", "16g", "4a", "==", "*-")
    )
    assert data(out) == ["8c", "8r", "4d", "8eL", "16f", "16gJ", "4a"]


def test_syncopated_beat_and_chords():
    out = add_beams(kern("**kern", "*M2/4", "=1", "16c 16e", "8d", "16e", "4f", "==", "*-"))
    assert data(out) == ["16cL 16e", "8d", "16eJ", "4f"]


def test_barline_breaks_beam_and_spines_are_independent():
    out = add_beams(
        kern(
            "**kern\t**kern",
            "*M1/4\t*M1/4",
            "=1\t=1",
            "8C\t4c",
            "8D\t.",
            "=2\t=2",
            "8E\t8e",
            "8F\t8f",
            "==\t==",
            "*-\t*-",
        )
    )
    assert data(out) == ["8CL\t4c", "8DJ\t.", "8EL\t8eL", "8FJ\t8fJ"]


def test_split_spines_beam_separately():
    out = add_beams(
        kern("**kern", "*M1/4", "*^", "=1\t=1", "8c\t4e", "8d\t.", "*v\t*v", "==", "*-")
    )
    assert data(out) == ["8cL\t4e", "8dJ\t."]


def test_already_beamed_file_is_unchanged_and_notes_never_change():
    beamed = kern("**kern", "*M2/4", "=1", "8cL", "8dJ", "8e", "8f", "==", "*-")
    assert add_beams(beamed) == beamed
    plain = kern("**kern", "*M3/4", "=1", "8.c", "16d", "12e", "12f", "12g", "8a", "8b", "==", "*-")
    assert parse_kern(add_beams(plain)).notes == parse_kern(plain).notes


def test_beat_unit():
    assert beat_unit(4, 4) == 1 and beat_unit(6, 8) == beat_unit(3, 8) == 1.5
