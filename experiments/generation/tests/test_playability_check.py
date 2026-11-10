"""Tests for playability_check.py on small hand-built two-staff kern fixtures."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from playability_check import background_ngrams, check_score, line_of, longest_shared_run

from omr_lab.kern import parse_kern


def piano(*rows: str) -> str:
    """rows: 'LH\\tRH' data lines; adds headers and a final barline."""
    head = ["**kern\t**kern", "*staff2\t*staff1", "*M4/4\t*M4/4", "=1\t=1"]
    return "\n".join([*head, *rows, "==\t==", "*-\t*-"]) + "\n"


def checks(text: str, **kw) -> list[tuple[str, str]]:
    return [(f.check, f.severity) for f in check_score(parse_kern(text), **kw)]


def test_clean_piece_has_no_findings():
    assert checks(piano("2C\t2e 2g 2cc", "2G\t2d 2g 2b")) == []


def test_hand_span_thresholds():
    assert checks(piano("1C\t1c 1cc")) == []  # octave
    assert checks(piano("1C\t1c 1dd")) == [("hand-span", "low")]  # 9th
    assert checks(piano("1C\t1e 1ccc")) == [("hand-span", "high")]  # pilot 001 kern T3 ending


def test_fast_leap():
    # C3 -> D1 is 22 semitones: flagged within an eighth note...
    assert ("fast-leap", "low") in checks(piano("8C\t2cc", "8DDD\t.", "4C\t.", "2C\t2cc"))
    # ...but with a quarter note of time it is normal stride motion.
    assert ("fast-leap", "low") not in checks(piano("4C\t2cc", "4DDD\t.", "2C\t2cc"))


def test_hand_crossing():
    assert ("hand-cross", "low") in checks(piano("1g\t1e"))


def test_simultaneous_chromatic_clash():
    # Pilot 001 ABC T4 bar 3: A natural in the bass under A flat in the RH.
    assert ("chromatic-clash", "medium") in checks(piano("1A\t1c 1a-"))


def test_cross_relation():
    assert ("chromatic-clash", "low") in checks(piano("4F\t4a", "4D\t4f#", "2C\t2e"))


def test_copy_detection_is_transposition_invariant():
    tune = ["c", "d", "e", "f", "g", "a", "b", "cc", "dd"]
    up = ["d", "e", "f#", "g", "a", "b", "cc#", "dd", "ee"]  # same tune a step higher
    a = parse_kern(piano(*[f"4C\t4{n}" for n in tune]))
    b = parse_kern(piano(*[f"4D\t4{n}" for n in up]))
    rh = [n for n in a.notes if n.staff == 1]
    rh_b = [n for n in b.notes if n.staff == 1]
    assert longest_shared_run(line_of(rh, True), line_of(rh_b, True)) == 9
    # No background: reported, but only as possibly generic.
    found = check_score(a, excerpts={"ex.krn": b})
    assert any(f.check == "copy" and f.severity == "medium" for f in found)
    # Background without the tune: one distinctive 9-note run is within chance -> low.
    other = parse_kern(piano(*[f"4C\t4{n}" for n in ["c", "e", "g", "e", "c", "g", "e", "c", "c"]]))
    bg = background_ngrams([other])
    found = check_score(a, excerpts={"ex.krn": b}, background=bg)
    assert [f.severity for f in found if f.check == "copy"] == ["low"]
    # A 13-note shared run is beyond chance -> high.
    long_a = tune + ["ee", "dd", "cc", "b"]
    long_b = up + ["ff#", "ee", "dd", "cc#"]
    a13 = parse_kern(piano(*[f"4C\t4{n}" for n in long_a]))
    b13 = parse_kern(piano(*[f"4D\t4{n}" for n in long_b]))
    found = check_score(a13, excerpts={"ex.krn": b13}, background=bg)
    assert any(f.check == "copy" and f.severity == "high" for f in found)


def test_shared_run_found_in_background_is_generic():
    # A plain scale shared with the excerpt is also in the composer's other pieces: not copying.
    scale = ["c", "d", "e", "f", "g", "a", "b", "cc", "dd"]
    a = parse_kern(piano(*[f"4C\t4{n}" for n in scale]))
    ex = parse_kern(
        piano(*[f"4F\t4{n}" for n in ["f", "g", "a", "b-", "cc", "dd", "ee", "ff", "gg"]])
    )
    other = parse_kern(
        piano(*[f"4G\t4{n}" for n in ["g", "a", "b", "cc", "dd", "ee", "ff#", "gg", "aa"]])
    )
    found = check_score(a, excerpts={"ex": ex}, background=background_ngrams([other]))
    assert not any(f.check == "copy" for f in found)


def test_no_copy_for_different_rhythm():
    a = parse_kern(piano(*[f"4C\t4{p}" for p in "cdefgab"], "4C\t4cc", "4C\t4dd"))
    b = parse_kern(piano(*[f"8C\t8{p}" for p in "cdefgab"], "8C\t8cc", "8C\t8dd", "2C\t2r"))
    assert not any(f.check == "copy" for f in check_score(a, excerpts={"ex": b}))


def test_letter_alter_reads_flats_and_sharps():
    from playability_check import _letter_alter

    assert _letter_alter("A-4") == ("A", -1)
    assert _letter_alter("F##3") == ("F", 2)
    assert _letter_alter("B--2") == ("B", -2)
    assert _letter_alter("C4") == ("C", 0)
