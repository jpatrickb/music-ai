"""Tests for experiments/generation/validate_notation.py (not a package, so put its dir on sys.path)."""

import sys
from fractions import Fraction
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import validate_notation as vn


def tsv(*rows: str) -> str:
    """Join kern rows; fields inside each row are already tab-separated."""
    return "\n".join(rows)


GOOD_ABC = """X:1
M:3/4
L:1/8
K:G
V:1 clef=treble
"G"G2 A2 B2 | "C"c2 B2 A2 | "D7""_V7"A6 |]
V:2 clef=bass
G,6 | E,6 | D,6 |]
"""

GOOD_KERN = tsv(
    "**kern\t**kern",
    "*clefF4\t*clefG2",
    "*M4/4\t*M4/4",
    "=1\t=1",
    "2C\t2e 2g 2cc",
    "2GG\t2d 2g 2b",
    "=2\t=2",
    "1C\t1e 1g 1cc",
    "==\t==",
    "*-\t*-",
)


def run(fmt: str, text: str):  # returns vn.Result (module loaded by path)
    return vn.validate(vn.Score(fmt, text, "test"), svg_dir=None, index=0)


def test_good_abc_passes() -> None:
    r = run("abc", GOOD_ABC)
    assert r.errors == [] and r.warnings == []


def test_good_kern_passes() -> None:
    assert run("kern", GOOD_KERN).errors == []


def test_abc_short_middle_bar_reported_in_correct_voice() -> None:
    r = run("abc", GOOD_ABC.replace('"C"c2 B2 A2', '"C"c2 B2'))
    assert r.errors == [
        "voice/spine 1, bar 2: 2 quarter notes, time signature 3/4 needs 3",
        "bar 2: voices have different lengths in quarter notes (voice 1: 2, voice 2: 3)",
    ]


def test_abc_pickup_bar_allowed() -> None:
    text = "X:1\nM:4/4\nL:1/4\nK:C\nG | c d e f | g4 |]\n"
    assert run("abc", text).errors == []


def test_abc_roman_numeral_without_prefix_warns() -> None:
    r = run("abc", GOOD_ABC.replace('"_V7"', '"V7"'))
    assert r.errors == []
    assert any('"V7" is not a chord symbol' in w for w in r.warnings)


def test_kern_field_count_mismatch() -> None:
    r = run("kern", GOOD_KERN.replace("2GG\t2d 2g 2b", "2GG"))
    assert any("1 fields but 2 active spines" in e for e in r.errors)


def test_kern_missing_terminator() -> None:
    r = run("kern", GOOD_KERN.replace("\n*-\t*-", ""))
    assert "missing *- spine terminators" in r.errors


def test_kern_split_and_merge_tracked() -> None:
    text = tsv(
        "**kern\t**kern",
        "*M2/4\t*M2/4",
        "=1\t=1",
        "*\t*^",
        "2C\t2e\t4g",
        ".\t.\t4a",
        "*\t*v\t*v",
        "=2\t=2",
        "2C\t2e",
        "==\t==",
        "*-\t*-",
    )
    r = vn.Result(vn.Score("kern", text, "t"))
    vn.check_kern_spines(r.score, r)
    assert r.errors == []


@pytest.mark.parametrize(("name", "fmt"), [("x.abc", "abc"), ("x.krn", "kern"), ("x.kern", "kern")])
def test_extract_scores_by_suffix(tmp_path: Path, name: str, fmt: str) -> None:
    p = tmp_path / name
    p.write_text("anything")
    assert [s.fmt for s in vn.extract_scores(p)] == [fmt]


def test_extract_scores_from_markdown_skips_fragments(tmp_path: Path) -> None:
    p = tmp_path / "doc.md"
    p.write_text("```abc\nX:1\n```\n\n```abc-fragment\nC D\n```\n\n```kern\n**kern\n```\n")
    assert [s.fmt for s in vn.extract_scores(p)] == ["abc", "kern"]


def test_abc_overlong_first_bar_caught() -> None:
    text = "X:1\nM:4/4\nL:1/4\nK:C\nc d e f g | c d e f | c4 |]\n"
    assert any("bar 1" in e for e in run("abc", text).errors)


def test_kern_meter_change_checked_against_new_meter() -> None:
    text = tsv(
        "**kern",
        "*M4/4",
        "=1",
        "1c",
        "*M3/4",
        "=2",
        "2.c",
        "=3",
        "2.c",
        "==",
        "*-",
    )
    assert run("kern", text).errors == []


def test_abc_too_few_barlines_checked_by_token_counter() -> None:
    # One `|` only, so music21 builds no measures; the token counter checks it instead.
    r = run("abc", "X:1\nM:4/4\nL:1/4\nK:C\nc d e | c4 |]\n")
    assert r.errors == [] and r.warnings == []


def test_abc_short_voice_overlong_bar_caught_by_token_counter() -> None:
    r = run("abc", "X:1\nM:4/4\nL:1/4\nK:C\nc d e f g | c4 |]\n")
    assert r.errors == ["voice 1, bar 1: 5 quarter notes, time signature 4/4 needs 4 (token count)"]


SHORT_TWO_VOICE = """X:1
M:4/4
L:1/4
K:C
V:1 clef=treble
V:2 clef=bass
V:1
"C"[EGc] "F"[FAc] "C/G"[EGc] "G7"[FGB] | "C"[EGc]4 |]
V:2
"_I"C, "_IV"F, "_I6/4"G, "_V7"G,, | "_I"C,4 |]
"""


def test_abc_short_two_voice_example_checked() -> None:
    r = run("abc", SHORT_TWO_VOICE)
    assert r.errors == [] and r.warnings == []


def test_abc_short_two_voice_error_in_second_voice() -> None:
    r = run("abc", SHORT_TWO_VOICE.replace('"_I"C,4 |]', '"_I"C,2 C, C, C, |]'))
    assert r.errors == [
        "bar 2: voices have different lengths in quarter notes (voice 1: 4, voice 2: 5)",
        "voice 2, bar 2: 5 quarter notes, time signature 4/4 needs 4 (token count)",
    ]


def test_abc_token_counter_gives_up_keeps_not_checked_warning() -> None:
    r = run("abc", "X:1\nM:4/4\nL:1/4\nK:C\nc d e f & C D E F | c4 |]\n")
    assert any("token counter gave up" in w and "NOT checked" in w for w in r.warnings)


def test_abc_voice_reentry_warns() -> None:
    text = SHORT_TWO_VOICE + "V:1\n[EGc]4 |]\n"
    assert any("voice 1 resumes after another voice" in w for w in run("abc", text).warnings)


# --- token-level ABC counter ------------------------------------------------------------------


def bar_lengths(body: str, header: str = "M:4/4\nL:1/8\n") -> dict[str, list[Fraction]]:
    """Bar lengths per voice, in quarter notes."""
    bars, _ = vn.abc_bars(f"X:1\n{header}K:C\n{body}\n")
    return {v: [b.length * 4 for b in bs] for v, bs in bars.items()}


@pytest.mark.parametrize(
    ("body", "expected"),
    [
        ("c8 |]", [4]),  # L:1/8, so c8 is a whole note
        (
            "c/ c// c//c3/2 c/4 |]",
            [Fraction(1, 4) + Fraction(1, 8) * 2 + Fraction(3, 4) + Fraction(1, 8)],
        ),
        ("z2 x2 c4 |]", [4]),  # z rest, x invisible rest
        ("(3cde c2 c4 |]", [4]),  # triplet of eighths = 1 quarter
        ("(3:2:2c2d c2 c4 |]", [4]),  # 2 notes in the time of 2 of 3: (c2 + d) * 2/3 = 1 quarter
        ("c>d c<d c>>d c2 |]", [4]),  # broken rhythm keeps each pair at 2 units
        ("[CEG]2 [C2E2G2] [CEG]/ [CEG]/ [CEG]3 |]", [4]),  # chord length: first note x suffix
        ('{ag}c2 {/a}"G"!trill!.c2 c4 |]', [4]),  # grace notes take no time
        ('"^a|b [c]"c8 |]', [4]),  # barline/bracket chars inside quotes are ignored
        ("c4- c4 | c8 |]", [4, 4]),  # tie
        ("(cdef) g4 |]", [4]),  # slur
        ("c8 % comment | c c |\n|]", [4]),  # % comment hides the rest of the line
        ("|: c8 |1 c8 :|2 c8 |]", [4, 4, 4]),  # repeats and endings
        ("c8 | [1 c8 :| [2 c8 |]", [4, 4, 4]),  # [1 [2 endings
        ("c8 | Z2 | c8 |]", [4, 4, 4, 4]),  # Z2 multi-bar rest
        ("c4\nc4 |]", [4]),  # a bar may span lines
    ],
)
def test_abc_bar_lengths(body: str, expected: list[Fraction]) -> None:
    assert bar_lengths(body) == {"1": expected}


def test_abc_default_unit_length_from_meter() -> None:
    assert bar_lengths("c8 |]", header="M:2/4\n") == {"1": [2]}  # under 3/4: L defaults to 1/16
    assert bar_lengths("c8 |]", header="M:3/4\n") == {"1": [4]}  # 3/4 and up: 1/8


def test_abc_meter_change_line_and_inline_fields() -> None:
    bars, _ = vn.abc_bars(
        "X:1\nM:4/4\nL:1/4\nK:C\nc4 |\nM:3/4\nK:C\nc3 | [M:2/4] c2 | [L:1/8] c4 |]\n"
    )
    assert [(b.length * 4, b.meter_str) for b in bars["1"]] == [
        (4, "4/4"),
        (3, "3/4"),
        (2, "2/4"),
        (2, "2/4"),
    ]
    assert all(vn.abc_bar_errors(bs) == [] for bs in bars.values())


def test_abc_meter_change_keeps_unit_length() -> None:
    # Default L comes from the header meter (4/4 -> 1/8); M:2/4 later must not switch it to 1/16.
    assert bar_lengths("c8 |\nM:2/4\nK:C\nc4 |]", header="M:4/4\n") == {"1": [4, 2]}


def test_abc_tuplet_default_q_compound_meter() -> None:
    # (2 = 2 notes in the time of 3; (5 in compound 6/8 = 5 in the time of 3.
    assert bar_lengths("(2cd c3 |]", header="M:6/8\nL:1/8\n") == {"1": [3]}
    assert bar_lengths("(5cdefg c3 |]", header="M:6/8\nL:1/8\n") == {"1": [3]}


def test_abc_voices_counted_separately() -> None:
    body = "V:1\nc8 | c8 |]\nV:2\nC,4 C,4 | C,8 |]"
    assert bar_lengths(body) == {"1": [4, 4], "2": [4, 4]}


def test_abc_header_voice_declarations_and_trailing_fields_ignored() -> None:
    bars, warnings = vn.abc_bars('X:1\nM:4/4\nL:1/4\nV:1 name="RH"\nK:C\nc4 |]\nw: la\n')
    assert [b.length for b in bars["1"]] == [1] and warnings == []


def test_abc_bar_errors_allow_short_first_and_last_only() -> None:
    bars, _ = vn.abc_bars("X:1\nM:4/4\nL:1/4\nK:C\nc | c3 | c4 | c2 |]\n")
    assert vn.abc_bar_errors(bars["1"]) == [
        "voice 1, bar 2: 3 quarter notes, time signature 4/4 needs 4 (token count)"
    ]


@pytest.mark.parametrize("body", ["c d & e f |]", "c8 #", '"unterminated c8 |]', "> c |]"])
def test_abc_unsupported_syntax_raises(body: str) -> None:
    with pytest.raises(vn.AbcCountError):
        vn.abc_bars(f"X:1\nM:4/4\nL:1/4\nK:C\n{body}\n")


def test_abc_counter_agrees_with_reference_doc() -> None:
    # Every complete ABC example in the encoding doc has only full 4/4 or 12/8 bars.
    doc = Path(__file__).resolve().parents[1] / "encoding" / "abc-reference.md"
    scores = vn.extract_scores(doc)
    assert scores
    for s in scores:
        bars, warnings = vn.abc_bars(s.text)
        assert warnings == [], s.label
        assert all(vn.abc_bar_errors(bs) == [] for bs in bars.values()), s.label
        assert len({len(bs) for bs in bars.values()}) == 1, s.label  # voices have equal bar counts


# --- kern harmony spine and Verovio log -------------------------------------------------------


def test_kern_harm_label_on_last_eighth_not_overlong() -> None:
    # music21 gives RomanNumerals a quarter-note length, so a label at beat 4.5 used to make
    # bar 1 measure 4.5 quarters.
    text = tsv(
        "**kern\t**harm\t**kern",
        "*staff2\t*staff2\t*staff1",
        "*clefF4\t*\t*clefG2",
        "*C:\t*C:\t*C:",
        "*M4/4\t*\t*M4/4",
        "=1\t=1\t=1",
        "4C\tI\t4e 4g 4cc",
        "4F\tIV\t4f 4a 4cc",
        "4.G\tV\t4.d 4.g 4.b",
        "8GG\tV7\t8f",
        "=2\t=2\t=2",
        "1C\tI\t1e 1g 1cc",
        "==\t==\t==",
        "*-\t*-\t*-",
    )
    assert run("kern", text).errors == []


def test_kern_misaligned_rhythm_surfaces_verovio_log() -> None:
    # RH bar 1 sums to 3 quarters, LH to 4. Each spine alone passes (a short first bar is a legal
    # pickup); the cross-spine check catches it, and Verovio loads it but logs the misalignment.
    text = GOOD_KERN.replace("2GG\t2d 2g 2b", "2GG\t4d 4g 4b")
    r = run("kern", text)
    assert r.errors == [
        "bar 1: voices have different lengths in quarter notes (spine 2: 3, spine 1: 4)"
    ]
    assert any(
        w.startswith("verovio: ") and "Inconsistent rhythm analysis" in w for w in r.warnings
    )


def test_verovio_messages_grouped_deduped_and_filtered() -> None:
    log = (
        "Error: Inconsistent rhythm analysis occurring near line 7\n"
        "Expected durationFromStart to be: 3 but found it to be 4\n"
        "Line: 1C\t1e\n\n"
        "[Warning] ABC import: Multi-voice music is not supported\n"
        "[Warning] Something else\n"
        "[Warning] Something else\n"
    )
    assert vn.verovio_messages(log) == [
        (
            "verovio: Error: Inconsistent rhythm analysis occurring near line 7 | Expected "
            "durationFromStart to be: 3 but found it to be 4 | Line: 1C 1e"
        ),
        "verovio: [Warning] Something else (x2)",
    ]


# --- cross-voice bar alignment ----------------------------------------------------------------


def test_bar_alignment_errors_unit() -> None:
    f = Fraction
    assert vn.bar_alignment_errors([("a", [f(3), f(4)])]) == []  # one voice: nothing to compare
    assert vn.bar_alignment_errors([("a", [f(3), f(4)]), ("b", [f(3), f(4)])]) == []
    assert vn.bar_alignment_errors([("a", [f(4), f(4)]), ("b", [f(4)])]) == [
        "voices have different bar counts (a: 2, b: 1)"
    ]
    assert vn.bar_alignment_errors([("a", [f(4), f(1, 2)]), ("b", [f(4), f(3, 2)])]) == [
        "bar 2: voices have different lengths in quarter notes (a: 0.5, b: 1.5)"
    ]


def test_abc_pickup_in_one_voice_only_is_error() -> None:
    # V:1 has a 1-beat pickup, V:2 a full first bar: each voice alone is legal.
    text = SHORT_TWO_VOICE.replace(
        '"C"[EGc] "F"[FAc] "C/G"[EGc] "G7"[FGB] |',
        '"G7"[FGB] | "C"[EGc] "F"[FAc] "C/G"[EGc] "G7"[FGB] |',
    ).replace('"_I"C,4 |]', '"_I"C,4 | C,4 |]')
    r = run("abc", text)
    assert r.errors == [
        "bar 1: voices have different lengths in quarter notes (voice 1: 1, voice 2: 4)"
    ]


def test_abc_pickup_in_all_voices_passes() -> None:
    text = "X:1\nM:4/4\nL:1/4\nK:C\nV:1\nG | c4 | c3 |]\nV:2\nG, | C,4 | C,3 |]\n"
    r = run("abc", text)
    assert r.errors == [] and r.warnings == []


def test_abc_different_bar_counts_is_error() -> None:
    r = run("abc", SHORT_TWO_VOICE.replace('"_I"C,4 |]', '"_I"C,4 | C,4 |]'))
    assert r.errors == ["voices have different bar counts (voice 1: 2, voice 2: 3)"]


def test_kern_different_bar_counts_is_error() -> None:
    r = run("kern", GOOD_KERN.replace("=2\t=2", "=2\t."))  # barline missing in spine 2
    assert "voices have different bar counts (spine 2: 1, spine 1: 2)" in r.errors


def test_kern_pickup_in_all_spines_passes() -> None:
    text = tsv(
        "**kern\t**kern",
        "*M4/4\t*M4/4",
        "2C\t4e",
        ".\t4f",
        "=1\t=1",
        "1C\t1e",
        "==\t==",
        "*-\t*-",
    )
    assert run("kern", text).errors == []
