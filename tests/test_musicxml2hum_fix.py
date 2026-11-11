import pytest

from music_ai.kern import parse_kern
from music_ai.musicxml2hum_fix import repair

SHORT_HEADER = """**kern\t**dynam
*clefF4\t*clefG2\t*clefG2\t*
=1\t=1\t=1\t=1
4C\t4c\t4cc\tp
*-\t*-\t*-\t*-
"""

MISSING_SPLIT = """**kern\t**kern
*clefF4\t*clefG2
=1\t=1
4C\t4E\t4c
4D\t4F\t4d
*\t*\t*^
4C\t4E\t4c\t4e
*v\t*v\t*\t*
*\t*v\t*v
4C\t4c
*-\t*-
"""


def test_short_header_padded_with_kern():
    fixed = repair(SHORT_HEADER)
    assert fixed.splitlines()[0] == "**kern\t**kern\t**kern\t**dynam"
    assert len(parse_kern(fixed).pitched()) == 3


def test_missing_opening_split_inserted_where_later_merge_shows():
    fixed = repair(MISSING_SPLIT)
    assert "*^\t*" in fixed.splitlines()
    ks = parse_kern(fixed)
    assert len(ks.pitched()) == 12
    assert ks.duration == 4


def test_clean_file_unchanged():
    clean = "**kern\t**kern\n4C\t4c\n*-\t*-\n"
    assert repair(clean) == clean


def test_unresolvable_widening_raises():
    with pytest.raises(ValueError):
        repair("**kern\t**kern\n*clefF4\t*clefG2\n4C\t4E\t4c\n*-\t*-\t*-\n")
