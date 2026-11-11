import xml.etree.ElementTree as ET
from fractions import Fraction

from music_ai.musicxml_ticks import notated_length, restore


def _note(dur: int, typ: str, tuplet: tuple[int, int] | None = None, chord: bool = False) -> str:
    tm = (
        f"<time-modification><actual-notes>{tuplet[0]}</actual-notes>"
        f"<normal-notes>{tuplet[1]}</normal-notes></time-modification>"
        if tuplet
        else ""
    )
    c = "<chord/>" if chord else ""
    return f"<note>{c}<pitch><step>C</step><octave>4</octave></pitch><duration>{dur}</duration><type>{typ}</type>{tm}</note>"


def _score(*body: str) -> ET.Element:
    return ET.fromstring(
        "<score-partwise><part id='P1'><measure number='1'>"
        "<attributes><divisions>480</divisions></attributes>"
        + "".join(body)
        + "</measure></part></score-partwise>"
    )


def _durations(root: ET.Element) -> list[tuple[str, int]]:
    return [
        (e.tag, int(e.findtext("duration")))
        for e in root.find("part/measure")
        if e.find("duration") is not None
    ]


def test_notated_length_with_tuplet_and_dots():
    n = ET.fromstring(
        "<note><type>16th</type><time-modification><actual-notes>9</actual-notes><normal-notes>8</normal-notes></time-modification></note>"
    )
    assert notated_length(n) == Fraction(2, 9)
    assert notated_length(ET.fromstring("<note><type>quarter</type><dot/></note>")) == Fraction(
        3, 2
    )


def test_rounded_tuplet_run_and_backup_become_exact():
    # nine 9:8 sixteenths stored as 107 ticks each (963), then a backup of 963 to the bar start
    root = _score(
        *[_note(107, "16th", (9, 8))] * 9,
        "<backup><duration>963</duration></backup>",
        _note(960, "half"),
    )
    n = restore(root)
    assert n == 9
    assert root.findtext("part/measure/attributes/divisions") == str(480 * 9)
    d = _durations(root)
    assert all(t == 960 for _, t in d[:9])  # 2/9 quarter at 4320 per quarter
    assert d[9] == ("backup", 9 * 960)  # back exactly to the start
    assert d[10] == ("note", 2 * 4320)


def test_tiny_forward_is_dropped():
    root = _score(
        _note(55, "32nd", (13, 12)),
        "<forward><duration>1</duration></forward>",
        _note(55, "32nd", (13, 12)),
    )
    restore(root)
    assert _durations(root)[1] == ("forward", 0)


def test_exact_file_unchanged_apart_from_resolution():
    root = _score(_note(480, "quarter"), _note(240, "eighth"), _note(240, "eighth"))
    assert restore(root) == 0
    assert [t for _, t in _durations(root)] == [480, 240, 240]


def test_forward_over_part_of_a_septuplet_snaps_to_the_tuplet_grid():
    # a voice skips two notes of a 7:4 sixteenth group (2/7 quarter = 137.14 ticks, stored 137)
    root = _score("<forward><duration>137</duration></forward>", *[_note(69, "16th", (7, 4))] * 5)
    restore(root)
    d = _durations(root)
    assert d[0] == ("forward", 2 * 480)  # 2/7 quarter at 480*7 per quarter
    assert all(t == 480 for _, t in d[1:])
