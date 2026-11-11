from fractions import Fraction as F

from music_ai.kern import parse_kern
from music_ai.melody_fidelity import extract_melody, find_statements


def kern(*rows: str) -> str:
    return "\n".join(rows) + "\n"


# Soprano C D E F over an alto line, two staves.
SOURCE = kern(
    "**kern\t**kern",
    "*staff2\t*staff1",
    "*M4/4\t*M4/4",
    "*\t*^",
    "=1\t=1\t=1",
    "1C\t4c\t4G",
    ".\t4d\t4B",
    ".\t4e\t2c",
    ".\t4f\t.",
    "==\t==\t==",
    "*\t*v\t*v",
    "*-\t*-",
)


def test_extract_melody_takes_the_soprano():
    mel = extract_melody(parse_kern(SOURCE))
    assert [m.midi for m in mel] == [60, 62, 64, 65]
    assert [m.onset for m in mel] == [0, 1, 2, 3]


def test_finds_two_statements_one_transposed_up_a_step_and_an_octave():
    mel = extract_melody(parse_kern(SOURCE))
    arr = parse_kern(
        kern(
            "**kern\t**kern",
            "*staff2\t*staff1",
            "*M4/4\t*M4/4",
            "=1\t=1",  # intro: unrelated
            "1C\t1g",
            "=2\t=2",  # verse 1 in C, tune on top
            "1C\t4c 4cc",
            ".\t4dd",
            ".\t4ee",
            ".\t4ff",
            "=3\t=3",  # verse 2 in D, tune an octave higher, the last note a sixteenth late
            "1D\t4ddd",
            ".\t4eee",
            ".\t4fff#",
            ".\t16r",
            ".\t8.ggg",
            "==\t==",
            "*-\t*-",
        )
    )
    found = find_statements(mel, arr)
    assert [(s.onset, s.bar, s.transposition) for s in found] == [(F(4), 2, 0), (F(8), 3, 2)]
    assert all(s.coverage == 1.0 and s.top_coverage == 1.0 for s in found)


def test_tune_in_the_bass_counts_but_not_on_top():
    mel = extract_melody(parse_kern(SOURCE))
    arr = parse_kern(
        kern(
            "**kern\t**kern",
            "*staff2\t*staff1",
            "*M4/4\t*M4/4",
            "=1\t=1",
            "4C\t1gg",
            "4D\t.",
            "4E\t.",
            "4F\t.",
            "==\t==",
            "*-\t*-",
        )
    )
    (s,) = find_statements(mel, arr)
    assert s.coverage == 1.0 and s.top_coverage == 0.0


def test_no_statement_when_the_tune_is_missing():
    mel = extract_melody(parse_kern(SOURCE))
    arr = parse_kern(kern("**kern", "*M4/4", "=1", "4c", "4c", "4c", "4c", "==", "*-"))
    assert find_statements(mel, arr) == []


def test_statement_found_when_its_first_note_is_changed():
    mel = extract_melody(parse_kern(SOURCE))
    arr = parse_kern(
        kern(
            "**kern\t**kern",
            "*staff2\t*staff1",
            "*M4/4\t*M4/4",
            "=1\t=1",
            "1G\t4ee",  # the tune's first note (C) is replaced by E; the rest is the tune
            ".\t4dd",
            ".\t4ee",
            ".\t4ff",
            "==\t==",
            "*-\t*-",
        )
    )
    (s,) = find_statements(mel, arr, min_coverage=0.7)
    assert (s.onset, s.transposition) == (0, 0)
    assert s.coverage == s.top_coverage == 0.75
