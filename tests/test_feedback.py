import pytest

from music_ai.feedback import Feedback, Generation, Preference, Rating, check, load, save


def gen(id_: str, output: str = "out.krn") -> Generation:
    return Generation(
        id=id_,
        experiment="999-test",
        task="T1",
        arm="A",
        output=output,
        brief="b",
        context=[],
        prompt="prompt.md",
        model="m",
        generator="g",
        created="2026-11-10",
        commit="abc",
    )


def test_round_trip(tmp_path):
    fb = Feedback(
        [gen("999/A/T1-1"), gen("999/A/T1-2")],
        [Rating("999/A/T1-1", "owner", "2026-11-10", {"musicality": 4}, notes="nice ♭6")],
        [Preference(["999/A/T1-1", "999/A/T1-2"], "999/A/T1-2", "owner", "2026-11-10")],
    )
    save(fb, tmp_path)
    assert load(tmp_path) == fb
    assert check(fb) == []


def test_check_finds_bad_references_and_scores():
    fb = Feedback(
        [gen("x"), gen("x")],
        [Rating("y", "owner", "d", {"musicality": 6})],
        [Preference(["x", "z"], "w", "owner", "d")],
    )
    problems = "\n".join(check(fb))
    for expected in [
        "duplicate generation id x",
        "unknown generation y",
        "musicality=6",
        "unknown generation z",
        "choice w",
    ]:
        assert expected in problems


def test_check_missing_files(tmp_path):
    (tmp_path / "prompt.md").write_text("")
    assert check(Feedback([gen("x", "nope.krn")]), tmp_path) == ["x: missing file nope.krn"]


def test_load_rejects_unknown_fields(tmp_path):
    (tmp_path / "ratings.jsonl").write_text('{"generation": "x", "bogus": 1}\n')
    with pytest.raises(ValueError, match="ratings.jsonl:1"):
        load(tmp_path)


def test_committed_feedback_is_consistent():
    from pathlib import Path

    root = Path(__file__).resolve().parents[1]
    fb = load(root / "feedback")
    assert fb.generations, "feedback/ should not be empty"
    assert check(fb, root) == []
