from fractions import Fraction as F

import pytest

from omr_lab.kern import (
    KernError,
    malformed_pitch,
    merge_ties,
    parse_duration,
    parse_kern,
    parse_pitch,
)


def kern(*rows: str) -> str:
    return "\n".join(rows) + "\n"


@pytest.mark.parametrize(
    ("tok", "quarters"),
    [
        ("4c", F(1)),
        ("8.c", F(3, 4)),
        ("2..c", F(7, 2)),
        ("16c", F(1, 4)),
        ("12c", F(1, 3)),  # triplet eighth
        ("6c", F(2, 3)),  # triplet quarter
        ("1c", F(4)),
        ("0c", F(8)),  # breve
        ("00c", F(16)),  # longa
        ("3%2c", F(8, 3)),  # rational: 2/3 of a whole note
        ("4gg.", F(3, 2)),  # dot after the pitch (Scarlatti edition)
        ("c", None),
    ],
)
def test_parse_duration(tok, quarters):
    assert parse_duration(tok) == quarters


@pytest.mark.parametrize(
    ("tok", "midi", "name"),
    [
        ("4c", 60, "C4"),
        ("4cc", 72, "C5"),
        ("4C", 48, "C3"),
        ("4CC#", 37, "C#2"),
        ("8b-", 70, "B-4"),
        ("4f##", 67, "F##4"),
        ("4dn", 62, "D4"),
        ("4B-L", 58, "B-3"),  # beam signifier after the pitch
        ("4AAAA", 21, "A0"),  # lowest piano key
    ],
)
def test_parse_pitch(tok, midi, name):
    assert parse_pitch(tok) == (midi, name)


def test_two_staves_chord_and_timing():
    s = parse_kern(
        kern(
            "**kern\t**kern",
            "*staff2\t*staff1",
            "*M4/4\t*M4/4",
            "*C:\t*C:",
            "=1\t=1",
            "2C\t4c 4e 4g",
            ".\t4d",
            "2G\t2e",
            "==\t==",
            "*-\t*-",
        )
    )
    assert s.meters == [(F(0), (4, 4))]
    assert s.keys == [(F(0), "C")]
    assert s.duration == F(4)
    onsets = [(n.onset, n.name, n.staff) for n in s.notes]
    assert onsets == [
        (F(0), "C3", 2),
        (F(0), "C4", 1),
        (F(0), "E4", 1),
        (F(0), "G4", 1),
        (F(1), "D4", 1),
        (F(2), "G3", 2),
        (F(2), "E4", 1),
    ]
    assert all(n.measure == 1 for n in s.notes)
    assert not s.warnings


def test_spine_split_and_merge():
    # One staff splits into two voices for a bar, then merges back.
    s = parse_kern(
        kern(
            "**kern",
            "=1",
            "*^",
            "2e\t1c",
            "2f\t.",
            "*v\t*v",
            "=2",
            "1g",
            "*-",
        )
    )
    got = [(n.onset, n.name, n.voice) for n in s.notes]
    assert got == [
        (F(0), "E4", "0.0"),
        (F(0), "C4", "0.1"),
        (F(2), "F4", "0.0"),
        (F(4), "G4", "0"),
    ]
    assert s.duration == F(8)
    assert not s.warnings


def test_grace_notes_take_no_time():
    s = parse_kern(kern("**kern", "8qd", "4c", "4e", "*-"))
    assert [(n.onset, n.duration, n.grace) for n in s.notes] == [
        (F(0), F(0), True),
        (F(0), F(1), False),
        (F(1), F(1), False),
    ]
    assert s.duration == F(2)


def test_irregular_and_split_bars_are_timed_as_written():
    # A bar split by a repeat sign, and an 8-beat bar of breves (both appear in the Bach chorales).
    s = parse_kern(
        kern(
            "**kern",
            "*M4/4",
            "=7",
            "2g",
            "=:|!",
            "2a",
            "=8",
            "0b",
            "==",
            "*-",
        )
    )
    assert [(n.onset, n.measure) for n in s.notes] == [(F(0), 7), (F(2), 7), (F(4), 8)]
    assert [b.number for b in s.barlines] == [7, None, 8, None]
    assert s.duration == F(12)


def test_non_kern_spines_are_ignored_for_timing():
    s = parse_kern(kern("**kern\t**harm\t**dynam", "4c\tI\tp", "4d\t.\t.", "*-\t*-\t*-"))
    assert [n.onset for n in s.notes] == [F(0), F(1)]
    assert {n.spine for n in s.notes} == {0}


def test_rests_and_ties():
    s = parse_kern(kern("**kern", "4r", "[4c", "4c]", "4c", "*-"))
    assert s.notes[0].is_rest
    merged = merge_ties(s.pitched())
    assert [(n.onset, n.duration) for n in merged] == [(F(1), F(2)), (F(3), F(1))]


def test_tie_continue():
    s = parse_kern(kern("**kern", "[4c", "4c_", "4c]", "*-"))
    assert [(n.onset, n.duration) for n in merge_ties(s.notes)] == [(F(0), F(3))]


def test_overlap_is_warned():
    s = parse_kern(kern("**kern\t**kern", "2c\t4e", "4d\t4f", "*-\t*-"))
    assert any("while the previous one lasts" in w for w in s.warnings)


def test_wrong_token_count_raises():
    with pytest.raises(KernError):
        parse_kern(kern("**kern\t**kern", "4c", "*-\t*-"))


def test_exchange_spines():
    s = parse_kern(kern("**kern\t**kern", "*x\t*x", "4c\t4e", "*-\t*-"))
    assert [(n.spine, n.name) for n in s.notes] == [(1, "C4"), (0, "E4")]


def test_chord_with_one_grace_subtoken_is_a_grace_chord():
    # Chopin op. 28/21 bar 23: only the first chord note carries the q.
    s = parse_kern(kern("**kern\t**kern", "4C\t4e", ".\tccq 4aa 4ccc", "4D\t4b", "*-\t*-"))
    assert [(n.onset, n.grace) for n in s.notes] == [
        (F(0), False),
        (F(0), False),
        (F(1), True),
        (F(1), True),
        (F(1), True),
        (F(1), False),
        (F(1), False),
    ]
    assert s.duration == F(2)
    assert not s.warnings


def test_mixed_duration_chord_advances_after_shortest_note():
    # Beethoven op. 28/ii bar 74: a 32nd and an eighth in one chord, then more 32nds.
    s = parse_kern(kern("**kern", "32cc 8ee", "32ff", "32gg", "32aa", "*-"))
    assert [(n.onset, n.duration, n.name) for n in s.notes] == [
        (F(0), F(1, 8), "C5"),
        (F(0), F(1, 2), "E5"),
        (F(1, 8), F(1, 8), "F5"),
        (F(1, 4), F(1, 8), "G5"),
        (F(3, 8), F(1, 8), "A5"),
    ]
    assert not s.warnings


def test_grace_note_beside_a_timed_note_takes_no_time():
    # Chopin op. 28/4 bar 11: LH chord and RH grace note on one line, the main note on the next.
    s = parse_kern(kern("**kern\t**kern", "8C\t8bq", ".\t4a", "8C\t.", "*-\t*-"))
    assert [(n.onset, n.name) for n in s.notes] == [
        (F(0), "C3"),
        (F(0), "B4"),
        (F(0), "A4"),
        (F(1, 2), "C3"),
    ]
    assert not s.warnings


@pytest.mark.parametrize(
    ("sub", "bad"),
    [
        ("4ff#", False),
        ("8.ccc#L", False),
        ("4BB-", False),
        ("4r", False),
        ("4f#f#", True),  # meant ff# (F#5); Verovio reads a double sharp
        ("16cc#cc#", True),
        ("4fg", True),
    ],
)
def test_malformed_pitch(sub, bad):
    assert malformed_pitch(sub) is bad


def test_malformed_pitch_is_warned():
    s = parse_kern(kern("**kern", "*M1/4", "=1", "4f#f#", "*-"))
    assert any("malformed pitch" in w for w in s.warnings)
