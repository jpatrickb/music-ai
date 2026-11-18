from music_ai.dynamics import DEFAULT, LEVEL_STEP, LEVELS, Mark, dynamic_marks, velocity_curve


def kern(*rows: str) -> str:
    return "\n".join(rows) + "\n"


def test_marks_come_from_dynam_spines_only_with_line_numbers():
    text = kern(
        "**kern\t**dynam",
        "*M4/4\t*",
        "=1\t=1",
        "4c\tp",
        "4d\t.",
        "4e\t<",
        "4f\t[",
        "=2\t=2",
        "1g\tf",
        "*-\t*-",
    )
    assert dynamic_marks(text) == [Mark(4, "p"), Mark(6, "<"), Mark(7, "["), Mark(9, "f")]


def test_marks_follow_spine_splits():
    text = kern(
        "**dynam\t**kern",
        "*^\t*",
        "p\tmf\t4c",
        "*v\t*v\t*",
        "f\t4d",
        "*-\t*-",
    )
    assert [m.token for m in dynamic_marks(text)] == ["p", "mf", "f"]


def test_no_marks_gives_the_default_everywhere():
    v = velocity_curve([])
    assert v(0) == v(100) == DEFAULT


def test_markings_are_steps():
    v = velocity_curve([(0.0, "p"), (4.0, "f")])
    assert v(0) == v(3.9) == LEVELS["p"]
    assert v(4.0) == v(10) == LEVELS["f"]


def test_crescendo_ramps_to_the_next_marking():
    v = velocity_curve([(0.0, "p"), (2.0, "<"), (4.0, "["), (4.0, "f")])
    assert v(1.9) == LEVELS["p"]
    assert v(3.0) == round((LEVELS["p"] + LEVELS["f"]) / 2)
    assert v(4.0) == LEVELS["f"]


def test_hairpin_without_a_following_marking_moves_one_step_and_stays():
    v = velocity_curve([(0.0, "mf"), (1.0, ">"), (3.0, "]")])
    assert v(3.0) == v(8.0) == LEVELS["mf"] - LEVEL_STEP
    assert LEVELS["mf"] - LEVEL_STEP < v(2.0) < LEVELS["mf"]


def test_accent_bumps_only_its_own_onset():
    v = velocity_curve([(0.0, "p"), (2.0, "sfz")])
    assert v(2.0) > LEVELS["p"]
    assert v(2.5) == LEVELS["p"]
