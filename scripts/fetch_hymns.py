"""Fetch public-domain hymn settings from the Open Hymnal Project and convert them to **kern.

The Open Hymnal ABC files interleave the four voices line by line with inline ``[V: ...]`` fields,
which music21 can't read, so each file is first regrouped into standard multi-voice ABC (one block
per voice, then parsed with music21 and written as two-staff
kern: treble staff split into soprano / alto, bass staff into tenor / bass. The words (ABC ``w:``
lines under the soprano, which music21 doesn't attach) are aligned to the soprano notes here and
written as one ``**text`` spine per verse; refrain words printed only under verse 1 stay in verse 1.

Raw downloads go to data/hymns/raw/ (gitignored); the kern files, which are public domain, go to
experiments/generation/sources/hymns/ (tracked).

Usage:
    uv run scripts/fetch_hymns.py
"""

from __future__ import annotations

import re
import sys
import urllib.request
from fractions import Fraction
from pathlib import Path

import music21

from music_ai.kern import parse_kern

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "hymns" / "raw"
OUT = ROOT / "experiments" / "generation" / "sources" / "hymns"
BASE = "http://openhymnal.org/Abc/"
HYMNS = {  # slug: Open Hymnal file name
    "adeste-fideles": "O_Come_All_Ye_Faithful-Adeste_Fideles-Portugese_Hymn.abc",
    "mendelssohn": "Hark_The_Herald_Angels_Sing-Mendelssohn.abc",
    "antioch": "Joy_To_The_World-Antioch.abc",
    "stille-nacht": "Silent_Night-Stille_Nacht.abc",
    "the-first-nowell": "The_First_Noel-The_First_Noel.abc",
}
METER = {  # source meter overrides: this Silent Night is notated 3/4 but every bar is a 6/8 bar
    "stille-nacht": "6/8",
}
VOICES = ["S1V1", "S1V2", "S2V1", "S2V2"]  # soprano, alto, tenor, bass
_INLINE_V = re.compile(r"^\[V:\s*(\S+?)\]\s*")
_SYLLABLE = re.compile(r"\*|_|\||[^\s\-*_|]+-?")  # ABC lyric tokens: skip, hold, bar, syllable
_VERSE_NO = re.compile(r"^\d+\.~?")


def lyric_lines(abc: str) -> list[list[list[str]]]:
    """Per soprano music line, the syllable slots of each ``w:`` line under it (one per verse).

    A slot is a syllable (trailing ``-`` if the word continues), or ``*`` / ``_`` for a note with
    no new syllable. ``|`` (align to the next bar) is dropped: hymn lyrics are written one slot per
    note anyway.
    """
    lines: list[list[list[str]]] = []
    current = None
    for line in abc.splitlines():
        if m := _INLINE_V.match(line):
            current = m.group(1)
            if current == VOICES[0]:
                lines.append([])
        elif line.startswith("w:") and current == VOICES[0] and lines:
            toks = _SYLLABLE.findall(re.sub(r"%.*", "", line[2:]))
            slots = [_VERSE_NO.sub("", t).replace("~", " ").strip() for t in toks if t != "|"]
            lines[-1].append([t or "*" for t in slots])  # a bare verse number holds a silent slot
    return lines


def align_lyrics(abc: str, soprano: music21.stream.Part) -> list[dict[Fraction, str]]:
    """Humdrum ``**text`` tokens per verse, keyed by soprano note onset.

    Each note that starts a syllable (not a tie continuation) takes one slot. A word continued
    across notes is written ``Si-`` then ``-lent``, as Humdrum does.
    """
    notes = [n for n in soprano.flatten().notes if n.tie is None or n.tie.type == "start"]
    lines = lyric_lines(abc)
    n_verses = max(len(ws) for ws in lines)
    verses: list[dict[Fraction, str]] = [{} for _ in range(n_verses)]
    pos = 0
    for ws in lines:
        width = len(ws[0]) if ws else 0
        for v, slots in enumerate(ws):
            if len(slots) != width:
                raise ValueError(f"verse {v + 1}: {len(slots)} slots on a {width}-note line")
            cont = False
            for n, slot in zip(notes[pos : pos + width], slots, strict=True):
                if slot in ("*", "_"):
                    continue
                tok = ("-" if cont else "") + slot
                cont = slot.endswith("-")
                verses[v][Fraction(n.offset).limit_denominator(64)] = tok
        pos += width
    if pos != len(notes):
        raise ValueError(f"lyrics cover {pos} of {len(notes)} soprano notes")
    return verses


def regroup(abc: str) -> str:
    """Open Hymnal interleaved ABC -> standard multi-voice ABC music21 can parse."""
    header: list[str] = []
    body: dict[str, list[str]] = {v: [] for v in VOICES}
    current = None
    started = False
    for line in abc.splitlines():
        if line.startswith("X:"):
            started = True
        if not started or line.startswith("%"):
            continue
        if m := _INLINE_V.match(line):
            current = m.group(1)
            music = line[m.end() :]
            music = re.sub(r"\[Q:[^]]*\]", "", music)  # tempo goes in the header
            music = re.sub(r"![^!]*!", "", music)  # decorations
            music = music.replace(".-", "-").replace(".(", "(").replace("'", "")
            music = re.sub(r"\bx", "z", music)  # invisible rests
            music = re.sub(r"%.*", "", music)
            body[current].append(music)
        elif re.match(r"^[A-Z]:", line) and not line.startswith("V:"):
            header.append(re.sub(r"\s*%.*", "", line))
    if tempo := re.search(r"\[Q:([^]]*)\]", abc):
        header.insert(-1, f"Q:{tempo.group(1)}")
    out = [h for h in header if not h.startswith("K:")]
    out += [h for h in header if h.startswith("K:")]
    for i, v in enumerate(VOICES, 1):  # music21 only splits voices with numeric ids
        out.append(f"V:{i}")
        out += body[v]
    return "\n".join(out) + "\n"


def kern_duration(ql: Fraction) -> str:
    for dots in range(3):
        base = ql / (2 - Fraction(1, 2**dots))
        recip = Fraction(4) / base
        if recip.denominator == 1 and recip.numerator in (1, 2, 4, 8, 16, 32):
            return f"{recip.numerator}{'.' * dots}"
    raise ValueError(f"no kern duration for {ql} quarters")


def kern_pitch(p: music21.pitch.Pitch) -> str:
    step, octave = p.step, p.octave
    letters = step.lower() * (octave - 3) if octave >= 4 else step.upper() * (4 - octave)
    alter = int(p.alter)
    return letters + ("#" * alter if alter > 0 else "-" * -alter)


def note_token(n: music21.note.GeneralNote) -> str:
    dur = kern_duration(Fraction(n.quarterLength))
    if n.isRest:
        return dur + "r"
    tok = dur + kern_pitch(n.pitch)
    if n.tie is not None:
        tok = {"start": "[" + tok, "stop": tok + "]", "continue": tok + "_"}[n.tie.type]
    return tok


def to_kern(
    score: music21.stream.Score,
    title: str,
    source: str,
    meter: str | None = None,
    lyrics: list[dict[Fraction, str]] | None = None,
) -> str:
    parts = list(score.parts)
    if len(parts) != 4:
        raise ValueError(f"expected 4 voices, got {len(parts)}")
    s, a, t, b = parts
    order = [t, b, s, a]  # LH staff split (tenor, bass), RH staff split (soprano, alto)
    events: list[dict[Fraction, music21.note.GeneralNote]] = []
    for p in order:
        ev = {}
        for n in p.flatten().notesAndRests:
            ev[Fraction(n.offset).limit_denominator(64)] = n
        events.append(ev)
    ts = s.recurse().getElementsByClass("TimeSignature")[0]
    ks = s.recurse().getElementsByClass("KeySignature")[0]
    key = ks.asKey("major")
    bar_len = Fraction(ts.barDuration.quarterLength)
    meter = meter or ts.ratioString
    acc = [p.name.lower() for p in ks.alteredPitches]
    mm = score.recurse().getElementsByClass("MetronomeMark")
    lines = [
        f"!!!OTL: {title}",
        f"!!!SMS: {source}",
        "!!!YEC: Public domain",
        "**kern\t**kern",
        "*part1\t*part1",
        "*staff2\t*staff1",
        "*clefF4\t*clefG2",
        f"*k[{''.join(acc)}]\t*k[{''.join(acc)}]",
        f"*{key.tonic.name}:\t*{key.tonic.name}:",
        f"*M{meter}\t*M{meter}",
    ]
    if mm:
        lines.append(f"*MM{int(mm[0].number)}\t*MM{int(mm[0].number)}")
    lines.append("*^\t*^")
    # Barlines from the meter, not music21's measures (it starts a measure at every source line
    # break, even mid-bar). A short first measure is a pickup.
    first = s.getElementsByClass("Measure").first()
    pickup = Fraction(first.duration.quarterLength).limit_denominator(64) % bar_len
    end = max(o + Fraction(ev[o].quarterLength).limit_denominator(64) for ev in events for o in ev)
    bars = [Fraction(0)] if pickup else []
    t = pickup
    while t < end:
        bars.append(t)
        t += bar_len
    line_onset: dict[int, Fraction] = {}  # data line index -> onset, for aligning lyrics
    for i, start in enumerate(bars):
        stop = bars[i + 1] if i + 1 < len(bars) else end
        if start or not pickup:
            n = i if pickup else i + 1
            lines.append("\t".join([f"={n}"] * 4))
        onsets = sorted({o for ev in events for o in ev if start <= o < stop})
        for o in onsets:
            line_onset[len(lines)] = o
            lines.append("\t".join(note_token(ev[o]) if o in ev else "." for ev in events))
    lines += ["==\t==\t==\t==", "*v\t*v\t*\t*", "*\t*v\t*v", "*-\t*-"]
    verses = lyrics or []
    out = [
        ln if ln.startswith("!!") else _text_fields(ln, verses, line_onset.get(i))
        for i, ln in enumerate(lines)
    ]
    return "\n".join(out) + "\n"


def _text_fields(line: str, verses: list[dict[Fraction, str]], onset: Fraction | None) -> str:
    """``line`` with one **text field per verse appended (lyrics aligned to the soprano)."""
    if not verses:
        return line
    if line.startswith("**"):
        extra = ["**text"] * len(verses)
    elif line.startswith("*-"):
        extra = ["*-"] * len(verses)
    elif line.startswith("*"):
        extra = ["*"] * len(verses)
    elif line.startswith("="):
        extra = [line.split("\t")[0]] * len(verses)
    else:
        extra = [v.get(onset, ".") if onset is not None else "." for v in verses]
    return "\t".join([line, *extra])


def main() -> int:
    RAW.mkdir(parents=True, exist_ok=True)
    OUT.mkdir(parents=True, exist_ok=True)
    for slug, name in HYMNS.items():
        raw = RAW / name
        if not raw.exists():
            with urllib.request.urlopen(BASE + name, timeout=30) as r:
                raw.write_bytes(r.read())
        abc = raw.read_text(encoding="latin-1")
        grouped = regroup(abc)
        score = music21.converter.parse(grouped, format="abc")
        title = re.search(r"^T:\s*(.+)$", abc, re.MULTILINE).group(1).strip()
        source = f"Open Hymnal Project, {BASE}{name}"
        lyrics = align_lyrics(abc, score.parts[0])
        text = to_kern(score, title, source, METER.get(slug), lyrics)
        ks = parse_kern(text)
        if ks.warnings:
            print(f"{slug}: {len(ks.warnings)} warnings, e.g. {ks.warnings[0]}", file=sys.stderr)
        (OUT / f"{slug}.krn").write_text(text, encoding="utf-8")
        n_m21 = len(score.recurse().notes)
        print(f"{slug}: {len(ks.pitched())} notes (music21 {n_m21}), {ks.duration} quarters")
    return 0


if __name__ == "__main__":
    sys.exit(main())
