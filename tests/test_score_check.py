import music21

from music_ai.score_check import compare, music21_events


def _score(*notes: music21.note.GeneralNote) -> music21.stream.Score:
    part = music21.stream.Part()
    for n in notes:
        part.append(n)
    return music21.stream.Score([part])


KERN = "**kern\n4c\n4e\n*-\n"


def test_identical_notes_match():
    s = _score(music21.note.Note("C4", quarterLength=1), music21.note.Note("E4", quarterLength=1))
    m = compare(music21_events(s), KERN)
    assert m.ok and m.expected == m.got == 2


def test_shifted_note_is_rejected():
    s = _score(music21.note.Note("C4", quarterLength=2), music21.note.Note("E4", quarterLength=1))
    m = compare(music21_events(s), KERN)
    assert not m.ok
    assert "missing 1" in m.detail and "extra 1" in m.detail


def test_written_out_tremolo_accepted():
    n = music21.note.Note("C4", quarterLength=1)
    n.expressions.append(music21.expressions.Tremolo())
    m = compare(music21_events(_score(n)), "**kern\n8c\n8c\n*-\n")
    assert m.ok and "tremolo" in m.detail


def test_extra_note_outside_tremolo_rejected():
    n = music21.note.Note("C4", quarterLength=1)
    m = compare(music21_events(_score(n)), "**kern\n8c\n8c\n*-\n")
    assert not m.ok


def test_tied_pieces_count_as_one_note():
    s = _score(music21.note.Note("C4", quarterLength=2))
    m = compare(music21_events(s), "**kern\n[4c\n4c]\n*-\n")
    assert m.ok


def test_untied_note_in_partly_tied_chord_is_an_attack():
    first = music21.chord.Chord(["C4", "E4"], quarterLength=1)
    first.notes[0].tie = music21.tie.Tie("start")
    second = music21.chord.Chord(["C4", "G4"], quarterLength=1)
    second.notes[0].tie = music21.tie.Tie("stop")  # C4 held over; G4 newly struck
    m = compare(music21_events(_score(first, second)), "**kern\n[4c 4e\n4c] 4g\n*-\n")
    assert m.ok, m.detail
