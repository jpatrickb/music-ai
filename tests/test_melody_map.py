from music_ai.kern import parse_kern
from music_ai.melody_map import map_phrases, melody_line, split_phrases

# A tune of two 8-note phrases separated by a rest.
TUNE = "**kern\n*staff1\n*M4/4\n=1\n" + "\n".join(
    ["8c", "8d", "8e", "8f", "8g", "8a", "8b", "8cc", "=2", "2r", "2r", "=3"]
    + ["8cc", "8b", "8a", "8g", "8f", "8e", "8d", "8c", "=4", "1r", "*-"]
)


def test_split_phrases_at_rests():
    phrases = split_phrases(melody_line(parse_kern(TUNE), staff=1))
    assert [len(p.notes) for p in phrases] == [8, 8]


def test_tune_found_an_octave_down_in_the_left_hand_under_chords():
    phrases = split_phrases(melody_line(parse_kern(TUNE), staff=1))
    up = ["8C", "8D", "8E", "8F", "8G", "8A", "8B", "8c"]
    down = list(reversed(up))
    lh = up + ["2r", "2r"] + down + ["1r"]
    rh = ["2eee 2ggg", ".", ".", ".", "2ddd 2fff", ".", ".", "."] + ["2r", "2r"]
    rh += ["2eee 2ggg", ".", ".", ".", "2ddd 2fff", ".", ".", "."] + ["1r"]
    rows = [f"{a}\t{b}" for a, b in zip(lh, rh, strict=True)]
    for bar, i in ((2, 8), (3, 10), (4, 18)):
        rows.insert(i + bar - 2, f"={bar}\t={bar}")
    arr = parse_kern("**kern\t**kern\n*staff2\t*staff1\n=1\t=1\n" + "\n".join(rows) + "\n*-\t*-\n")
    matches = map_phrases(phrases, arr, min_evidence=0)
    assert [m.phrase for m in matches] == [0, 1]
    assert all(m.staff == 2 and m.coverage == 1 and m.shape == 1 for m in matches)
    assert all(m.position == "bottom" for m in matches)


def test_unrelated_piece_has_no_convincing_run():
    phrases = split_phrases(melody_line(parse_kern(TUNE), staff=1))
    other = "**kern\n*staff1\n" + "\n".join(["4e", "4e", "4e", "4e"] * 6) + "\n*-\n"
    assert map_phrases(phrases, parse_kern(other)) == []


def test_bar_of_counts_on_from_a_single_numbered_barline():
    from fractions import Fraction

    from music_ai.melody_map import bar_of

    ks = parse_kern("**kern\n=1\n4c\n=\n4d\n=\n4e\n*-\n")
    assert [bar_of(ks, Fraction(t)) for t in (0, 1, 2)] == [1, 2, 3]
    numbered = parse_kern("**kern\n4c\n=1\n4d\n=2\n4e\n=2\n4f\n*-\n")  # pickup; bar 2 split
    assert [bar_of(numbered, Fraction(t)) for t in (0, 1, 2, 3)] == [0, 1, 2, 2]
