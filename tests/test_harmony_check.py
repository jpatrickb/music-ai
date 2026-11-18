"""Tests for harmony_check.py: hand-built ABC and **kern fixtures with known voice leading."""

from __future__ import annotations

import pytest

from music_ai.harmony_check import (
    abc_annotations,
    check_text,
    main,
    parse_abc_figure,
)


def abc(rh: str, lh: str, key: str = "C", length: str = "1/4", meter: str = "4/4") -> str:
    return (
        f"X:1\nT:t\nM:{meter}\nL:{length}\nK:{key}\nV:1 clef=treble\nV:2 clef=bass\n"
        f"V:1\n{rh}\nV:2\n{lh}\n"
    )


def kern(rows: list[str], harm: bool = False, key: str = "C") -> str:
    """rows: 'LH | HARM | RH' strings ('|' separated, HARM only when harm=True)."""
    spines = ["**kern", "**harm", "**kern"] if harm else ["**kern", "**kern"]
    n = len(spines)

    def line(*fields: str) -> str:
        return "\t".join(fields)

    def every(token: str, harm_token: str | None = None) -> str:
        fields = [token] * n
        if harm:
            fields[1] = harm_token if harm_token is not None else token
        return line(*fields)

    out = [line(*spines)]
    out.append(line("*staff2", "*staff2", "*staff1") if harm else line("*staff2", "*staff1"))
    out.append(every("*k[]", "*"))
    out.append(every(f"*{key}:"))
    out.append(every("*M4/4", "*"))
    out.append(every("=1"))
    for r in rows:
        if r.startswith("="):
            out.append(every(r))
            continue
        fields = [f.strip() for f in r.split("|")]
        out.append(line(*fields))
    out.append(every("=="))
    out.append(every("*-"))
    return "\n".join(out) + "\n"


def kinds(findings) -> list[tuple[str, tuple[str, ...]]]:
    return sorted((f.check, f.voices) for f in findings)


# --- parallels -------------------------------------------------------------------------------

PARALLELS = {("parallel-5th", ("bass", "alto")), ("parallel-8ve", ("bass", "soprano"))}


def test_parallel_fifths_and_octaves_abc():
    findings = check_text(abc("[EGc] [FAd] |", "C, D, |"), "abc")
    assert set(kinds(findings)) == PARALLELS
    assert all(f.severity == "high" and f.bar == 1 and f.beat == 2 for f in findings)


def test_parallel_fifths_and_octaves_kern():
    findings = check_text(kern(["4C | 4e 4g 4cc", "4D | 4f 4a 4dd", "2r | 2r"]), "kern")
    assert set(kinds(findings)) == PARALLELS


def test_bar_and_beat_reported_in_second_bar():
    text = abc("[EGc]4 | [EGc]2 [EGc] [FAd] |", "C,4 | C,2 C, D, |")
    findings = check_text(text, "abc")
    assert {(f.bar, f.beat) for f in findings} == {(2, 4)}
    k = kern(["1C | 1e 1g 1cc", "=2", "2C | 2e 2g 2cc", "4C | 4e 4g 4cc", "4D | 4f 4a 4dd"])
    assert {(f.bar, f.beat) for f in check_text(k, "kern")} == {(2, 4)}


def test_clean_cadence_has_no_findings():
    text = abc('"C"[EGc] "F"[FAc] "C/G"[EGc] "G7"[FGB] | "C"[EGc]4 |]', "C, F, G, G,, | C,4 |]")
    assert check_text(text, "abc") == []
    k = kern(
        [
            "4C | 4e 4g 4cc",
            "4F | 4f 4a 4cc",
            "4G | 4e 4g 4cc",
            "4GG | 4f 4g 4b",
            "=2",
            "1C | 1e 1g 1cc",
        ]
    )
    assert check_text(k, "kern") == []


def test_contrary_fifths_flagged_medium():
    findings = check_text(abc("[CEG] [DGd] |", "C, G,, |"), "abc")
    assert kinds(findings) == [("contrary-5th", ("bass", "soprano"))]
    assert findings[0].severity == "medium"


def test_hidden_fifth_outer_voices_low():
    findings = check_text(abc("[EGc] [Fda] |", "C, D, |"), "abc")
    assert kinds(findings) == [("hidden-5th", ("bass", "soprano"))]
    assert findings[0].severity == "low"
    k = kern(["4C | 4e 4g 4cc", "4D | 4f 4dd 4aa", "2r | 2r"])
    assert kinds(check_text(k, "kern")) == [("hidden-5th", ("bass", "soprano"))]


def test_hidden_octave_with_stepwise_soprano_is_fine():
    # V7 -> I: bass G2 -> C3 and soprano B4 -> C5 arrive on an octave, soprano by step.
    assert check_text(abc("[FGB] [EGc] |", "G,, C, |"), "abc") == []


def test_octave_leap_with_same_pitch_classes_is_not_parallel():
    assert check_text(abc("[EGc] [egc'] |", "C, C |"), "abc") == []


# --- texture gating --------------------------------------------------------------------------


def test_melody_over_alberti_bass_has_no_strict_findings():
    # Melody G A B c over an Alberti bass; rank-based voices would invent parallels here.
    text = abc("g2 a2 b2 c'2 |", "C,G,E,G, D,A,F,A, |", length="1/8")
    assert not [f for f in check_text(text, "abc") if f.severity != "low"]


def test_melody_over_lh_block_chords_only_outer_voices_low():
    # RH single melody, LH three-note chords: not keyboard-style block chords.
    text = abc("g a |", "[C,E,G,] [D,F,A,] |", length="1/2")
    findings = check_text(text, "abc")
    assert all(f.severity == "low" and f.voices == ("bass", "soprano") for f in findings)


def test_rh_octave_doubling_is_one_voice():
    findings = check_text(abc("[Gg]2 [Aa]2 |", "C,2 D,2 |"), "abc")
    assert not [f for f in findings if f.check.endswith("8ve")]
    # outer voices G5/C3 -> A5/D3 are still parallel 5ths, reported at low confidence
    assert kinds(findings) == [("parallel-5th", ("bass", "soprano"))]
    assert findings[0].severity == "low"


# Regression shapes from the pilot outputs (experiments/001-gen-abc-vs-kern-pilot): per-onset
# "bass" in arpeggio and stride textures produced false outer-voice parallels.

ARPEGGIO_RH = "a4 g2 e2 |"  # melody A5, G5, E5
ARPEGGIO_LH = "A,,E,A,C ECA,E, |"  # A minor arpeggio; old checker: C4-G5 -> A3-E5 "5ths"


@pytest.mark.parametrize("label", ["", '"_vi"'])
def test_arpeggiated_lh_with_melody_doubling_arpeggio_tone_is_clean(label):
    text = abc(ARPEGGIO_RH, label + ARPEGGIO_LH, length="1/8")
    assert check_text(text, "abc") == []


def test_arpeggiated_lh_kern_melody_doubling_arpeggio_tone_is_clean():
    # Pilot kern/T3 bar 5: melody E-flat5 -> A-flat5 while the arpeggio steps E-flat3 -> A-flat3.
    k = kern(
        [
            "8AA- | I | 4ee-",
            "8E- | . | .",
            "8A- | . | 4aa-",
            "8c | . | .",
            "8e- | . | 4gg",
            "8c | . | .",
            "8A- | . | 4ff",
            "8E- | . | .",
        ],
        harm=True,
        key="A-",
    )
    assert check_text(k, "kern") == []


@pytest.mark.parametrize("label", [("", ""), ('"_I"', '"_ii"')])
def test_arpeggio_bass_parallel_octaves_with_melody_still_caught(label):
    # Arpeggio roots C3 -> D3 under melody C5 -> D5: real parallel octaves across the half bars.
    lh = f"{label[0]}C,G,E,G, {label[1]}D,A,F,A, |"
    findings = check_text(abc("c4 d4 |", lh, length="1/8"), "abc")
    assert kinds(findings) == [("parallel-8ve", ("bass", "soprano"))]
    assert (findings[0].bar, findings[0].beat, findings[0].severity) == (1, 3, "low")


STRIDE_LH = "F,,2 [A,C_E]2 C,2 [A,C_E]2 |"  # bass on 1 and 3, chord on 2 and 4


@pytest.mark.parametrize("label", ["", '"_I7"'])
def test_stride_with_melody_doubling_chord_bottom_is_clean(label):
    # Melody A4 doubles the off-beat chord's A3, then F4 over the F2 bass (pilot kern/T4 bar 4).
    text = abc("f2 a2 f2 a2 |", label + STRIDE_LH, key="F", length="1/8")
    assert check_text(text, "abc") == []


def test_stride_kern_melody_doubling_chord_bottom_is_clean():
    k = kern(
        [
            "4FF | I7 | 4f",
            "4A 4c 4e- | . | 4a",
            "4C | . | 4f",
            "4A 4c 4e- | . | 4a",
            "=2",
            "4FF | I7 | 4f",
            "4A 4c 4e- | . | 4a",
            "4C | . | 4f",
            "4A 4c 4e- | . | 4a",
        ],
        harm=True,
        key="F",
    )
    assert check_text(k, "kern") == []


def test_stride_bass_parallel_octaves_with_melody_still_caught():
    # Strong-beat bass C3 -> D3 under melody C5 -> D5.
    text = abc("c4 d4 |", "C,2 [E,G,]2 D,2 [F,A,]2 |", length="1/8")
    assert kinds(check_text(text, "abc")) == [("parallel-8ve", ("bass", "soprano"))]
    labelled = abc("c4 d4 |", '"_I"C,2 [E,G,]2 "_ii"D,2 [F,A,]2 |', length="1/8")
    assert kinds(check_text(labelled, "abc")) == [("parallel-8ve", ("bass", "soprano"))]


def test_melody_entering_after_the_bass_moved_is_not_paired_with_it():
    # Kern swing demo shape: the RH rests on beat 3, enters on beat 4 (D5) over B2, after the
    # beat-3 bass D3 has gone. C3-C5 -> D3-D5 would be a parallel that never sounds.
    assert check_text(abc("c4 z2 d2 |", "C,4 D,2 B,,2 |", length="1/8"), "abc") == []


def test_spacing_ignores_gap_between_lh_and_rh():
    # LH dyad F2-C3 under RH F4-A4-C5 (pilot abc/T4 2nd ending): the C3-F4 gap is free.
    assert check_text(abc("[FAc]2 |", "[F,,C,]2 |"), "abc") == []


def test_chord_symbols_are_ignored():
    # music21 turns "C" and "F" into zero-length chord-symbol notes in the C3 octave.
    text = abc('"C"[EGc] "Dm"[FAd] |', "C, D, |")
    assert set(kinds(check_text(text, "abc"))) == PARALLELS


# --- leading tone and seventh ---------------------------------------------------------------


@pytest.mark.parametrize("annotated", [True, False])
def test_unresolved_leading_tone_in_soprano_abc(annotated):
    lh = '"_V"G,, "_I"C, |' if annotated else "G,, C, |"
    findings = check_text(abc("[DGB] [CEG] |", lh), "abc")
    assert kinds(findings) == [("leading-tone", ("soprano",))]
    assert findings[0].severity == "medium"


def test_unresolved_leading_tone_in_soprano_kern():
    k = kern(["4GG | V | 4d 4g 4b", "4C | I | 4c 4e 4g", "2r | . | 2r"], harm=True)
    assert kinds(check_text(k, "kern")) == [("leading-tone", ("soprano",))]


def test_inner_leading_tone_may_drop():
    assert check_text(abc("[Bdg] [Gce] |", '"_V"G,, "_I"C, |'), "abc") == []


def test_unresolved_seventh_abc_and_kern():
    findings = check_text(abc("[FBd] [Gce] |", '"_V7"G,, "_I"C, |'), "abc")
    assert kinds(findings) == [("seventh", ("tenor",))]
    k = kern(["4GG | V7 | 4f 4b 4dd", "4C | I | 4g 4cc 4ee", "2r | . | 2r"], harm=True)
    assert kinds(check_text(k, "kern")) == [("seventh", ("tenor",))]


def test_secondary_dominant_resolution_uses_annotation():
    # V7/vi -> vi resolves correctly (G# up, D down); same voicing labelled wrongly is flagged.
    good = abc("[E^Gd] [EAc] |", '"_V7/vi"E, "_vi"A, |')
    assert check_text(good, "abc") == []
    # Bad: the 7th D rises to E.
    bad = abc("[E^Gd] [Ace] |", '"_V7/vi"E, "_vi"A, |')
    assert ("seventh", ("soprano",)) in kinds(check_text(bad, "abc"))


def test_augmented_sixth_is_not_treated_as_a_seventh_chord():
    text = abc("[_E^Fc] [EGc] |", '"_Ger+6"_A, "_I6/4"G, |')
    assert check_text(text, "abc") == []


def test_unknown_function_is_skipped():
    # E7 in C without an annotation: not V of the key, so its rising 7th (D -> E) is not judged.
    assert check_text(abc("[E^Gd] [EAe] |", "E, A, |"), "abc") == []


def test_key_area_prefix_sets_key_for_annotation():
    # "G: V7" makes F# the leading tone; F# in the soprano falls to D: flagged.
    text = abc("[Ac^f] [GBd] |", '"_G: V7"D, "_I"G,, |')
    assert ("leading-tone", ("soprano",)) in kinds(check_text(text, "abc"))


# --- spacing and crossing --------------------------------------------------------------------


def test_spacing_more_than_an_octave():
    findings = check_text(abc("[Ceg]2 |", "C,2 |"), "abc")
    assert kinds(findings) == [("spacing", ("tenor", "alto"))]


def test_voice_crossing_between_hands():
    findings = check_text(abc("[CGc]2 |", "E2 |"), "abc")
    assert kinds(findings) == [("crossing", ("bass", "tenor"))]


# --- ABC annotation parsing ------------------------------------------------------------------


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("V7", (None, "V7")),
        ("G: V7", ("G", "V7")),
        ("Ab: I(add9)", ("A-", "I")),
        ("I6/4", (None, "I64")),
        ("vii°", (None, "viio")),
        ("V7/vi", (None, "V7/vi")),
        ("iii = vi", (None, "iii")),
        ("Ger+6", (None, "Ger+6")),
        ("cresc.", None),
        ("Swing", None),
    ],
)
def test_parse_abc_figure(text, expected):
    assert parse_abc_figure(text) == expected


def test_abc_annotations_align_past_grace_notes_and_tuplets():
    text = abc("c4 |", '(3C,D,E, {F,}"_V"G,, z |', length="1/4")
    anns = abc_annotations(text)
    assert [(a.offset, a.text) for a in anns] == [(2.0, "V")]


# --- CLI ------------------------------------------------------------------------------------


def test_cli_exit_codes(tmp_path, capsys):
    bad_voice_leading = tmp_path / "p.abc"
    bad_voice_leading.write_text(abc("[EGc] [FAd] |", "C, D, |"))
    assert main([str(bad_voice_leading)]) == 0
    out = capsys.readouterr().out
    assert "parallel-5th" in out and "bar 1 beat 2" in out

    garbage = tmp_path / "g.krn"
    garbage.write_text("not a humdrum file\n")
    assert main([str(garbage)]) == 1
