"""A small, dependency-free reader for Humdrum **kern scores.

Turns a kern file into a flat list of timed notes (onset and duration in quarter notes, MIDI
pitch, staff, spine, bar) for analysis. It exists because music21's kern parser mis-times real
scores that use spine splits (*^ / *v), bars split around repeats, and irregular bars; this
reader follows the Humdrum timing model directly instead.

Timing model: every **kern spine holds its current event until it ends. A data line starts at
the current time t; each non-null token starts an event at t, and the next line starts at the
earliest end time over all **kern spines. Grace notes have zero duration, so a line of grace
notes does not advance time. Non-kern spines (**harm, **dynam, ...) don't affect timing.

Not handled (rare in the corpora used here): *+ spine additions mid-file are supported only in
the common form (followed by an exclusive-interpretation line), and tuplet display tokens
other than reciprocal durations (e.g. 3%2) are read as their sounding duration only.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field, replace
from fractions import Fraction

PITCH_CLASS = {"c": 0, "d": 2, "e": 4, "f": 5, "g": 7, "a": 9, "b": 11}

_DUR_RE = re.compile(r"(\d+)(?:%(\d+))?")
_PITCH_RE = re.compile(r"(c+|d+|e+|f+|g+|a+|b+|C+|D+|E+|F+|G+|A+|B+)(#+|-+|n)?")
_METER_RE = re.compile(r"^\*M(\d+)/(\d+)")
_STAFF_RE = re.compile(r"^\*staff(\d+)")
_PART_RE = re.compile(r"^\*part(\d+)")
_BAR_NUM_RE = re.compile(r"^=+(\d+)")


class KernError(ValueError):
    """The file's spine structure can't be followed (e.g. wrong number of tokens on a line)."""


@dataclass(frozen=True)
class Note:
    onset: Fraction  # quarter notes from the start
    duration: Fraction  # quarter notes; 0 for grace notes
    midi: int | None  # None for rests
    name: str | None  # spelled pitch like "C#4" / "B-3"; None for rests
    spine: int  # 0-based index of the top-level **kern spine, left to right
    voice: str  # sub-spine path after splits, e.g. "0", "0.1"
    staff: int | None  # from *staffN
    part: int | None  # from *partN
    measure: int | None  # last numbered barline before the note (None before the first)
    tie: str | None = None  # "start", "continue", "end"
    grace: bool = False

    @property
    def is_rest(self) -> bool:
        return self.midi is None

    @property
    def end(self) -> Fraction:
        return self.onset + self.duration


@dataclass(frozen=True)
class Barline:
    onset: Fraction
    number: int | None
    token: str


@dataclass
class KernScore:
    notes: list[Note] = field(default_factory=list)
    barlines: list[Barline] = field(default_factory=list)
    meters: list[tuple[Fraction, tuple[int, int]]] = field(default_factory=list)
    keys: list[tuple[Fraction, str]] = field(default_factory=list)  # *G:, *e-:, ...
    duration: Fraction = Fraction(0)
    warnings: list[str] = field(default_factory=list)

    def pitched(self, include_grace: bool = False) -> list[Note]:
        return [n for n in self.notes if not n.is_rest and (include_grace or not n.grace)]


@dataclass
class _Spine:
    kind: str  # "**kern", "**harm", ... ("" until known, for *+)
    top: int  # top-level kern spine index (-1 for non-kern)
    voice: str
    end: Fraction | None = Fraction(0)  # when the last event's longest note ends
    staff: int | None = None
    part: int | None = None
    end_min: Fraction | None = Fraction(0)  # when its shortest note ends

    def split(self) -> tuple[_Spine, _Spine]:
        return (
            replace(self, voice=f"{self.voice}.0"),
            replace(self, voice=f"{self.voice}.1"),
        )


def parse_duration(token: str) -> Fraction | None:
    """Reciprocal kern duration -> quarter notes. '4' = 1, '8.' = 3/4, '0' = 8, '3%2' = 8/3.

    Augmentation dots count wherever they sit in the token: '4.gg' and '4gg.' are both legal.
    """
    m = _DUR_RE.search(token)
    if not m:
        return None
    num, den = m.group(1), m.group(2)
    dots = token.count(".")
    if set(num) == {"0"}:  # 0 = breve, 00 = longa, 000 = maxima
        base = Fraction(8 * 2 ** (len(num) - 1))
    else:
        base = Fraction(4 * int(den or 1), int(num))
    return base * (2 - Fraction(1, 2**dots))


def parse_pitch(token: str) -> tuple[int, str] | None:
    """Kern pitch -> (MIDI number, spelled name). 'c' = C4 = 60, 'CC#' = C#2 = 37."""
    m = _PITCH_RE.search(token)
    if not m:
        return None
    letters, acc = m.group(1), m.group(2) or ""
    letter = letters[0]
    octave = 3 + len(letters) if letter.islower() else 4 - len(letters)
    alter = 0 if acc in ("", "n") else (len(acc) if acc[0] == "#" else -len(acc))
    midi = 12 * (octave + 1) + PITCH_CLASS[letter.lower()] + alter
    name = letter.upper() + ("#" * alter if alter > 0 else "-" * -alter) + str(octave)
    return midi, name


def _tie(sub: str) -> str | None:
    if "[" in sub:
        return "start"
    if "_" in sub:
        return "continue"
    if "]" in sub:
        return "end"
    return None


def _apply_tandem(sp: _Spine, tok: str, t: Fraction, score: KernScore, first: bool) -> None:
    if m := _STAFF_RE.match(tok):
        sp.staff = int(m.group(1))
    elif m := _PART_RE.match(tok):
        sp.part = int(m.group(1))
    elif first and (m := _METER_RE.match(tok)):
        score.meters.append((t, (int(m.group(1)), int(m.group(2)))))
    elif first and tok.endswith(":") and len(tok) <= 5 and tok[1:2].isalpha():
        score.keys.append((t, tok[1:-1]))


def _manipulate(
    spines: list[_Spine], toks: list[str], t: Fraction, score: KernScore
) -> list[_Spine]:
    out: list[_Spine] = []
    i = 0
    first_kern_seen = False
    while i < len(toks):
        tok, sp = toks[i], spines[i]
        if tok == "*^":
            out.extend(sp.split())
        elif tok == "*v":
            j = i
            while j + 1 < len(toks) and toks[j + 1] == "*v":
                j += 1
            group = spines[i : j + 1]
            ends = [s.end for s in group if s.end is not None]
            mins = [s.end_min for s in group if s.end_min is not None]
            voice = sp.voice.rsplit(".", 1)[0] if j > i else sp.voice
            out.append(
                replace(
                    sp,
                    voice=voice,
                    end=max(ends) if ends else None,
                    end_min=min(mins) if mins else None,
                )
            )
            i = j
        elif tok == "*-":
            pass
        elif tok == "*x" and i + 1 < len(toks) and toks[i + 1] == "*x":
            out.extend([spines[i + 1], sp])
            i += 1
        elif tok == "*+":
            out.extend([sp, _Spine("", -1, "new")])
        else:
            is_first_kern = sp.kind == "**kern" and not first_kern_seen
            _apply_tandem(sp, tok, t, score, is_first_kern)
            out.append(sp)
        if sp.kind == "**kern":
            first_kern_seen = True
        i += 1
    return out


def parse_kern(text: str) -> KernScore:
    score = KernScore()
    spines: list[_Spine] | None = None
    n_kern = 0
    t = Fraction(0)
    measure: int | None = None

    for lineno, raw in enumerate(text.splitlines(), 1):
        line = raw.rstrip("\r")
        if not line or line.startswith("!"):
            continue
        toks = line.split("\t")

        if spines is None:
            if not line.startswith("**"):
                continue
            spines = []
            for tok in toks:
                top = n_kern if tok == "**kern" else -1
                n_kern += tok == "**kern"
                spines.append(_Spine(tok, top, str(top)))
            continue

        if len(toks) != len(spines):
            raise KernError(f"line {lineno}: {len(toks)} tokens for {len(spines)} spines")

        if line.startswith("**"):  # exclusive interpretations for spines added by *+
            for sp, tok in zip(spines, toks, strict=True):
                if not sp.kind and tok.startswith("**"):
                    sp.kind = tok
                    if tok == "**kern":
                        sp.top, sp.voice, n_kern = n_kern, str(n_kern), n_kern + 1
                        sp.end = sp.end_min = t
            continue

        if line.startswith("*"):
            spines = _manipulate(spines, toks, t, score)
            if not spines:
                break
            continue

        if line.startswith("="):
            tok = next((tk for tk, sp in zip(toks, spines) if sp.kind == "**kern"), toks[0])
            m = _BAR_NUM_RE.match(tok)
            number = int(m.group(1)) if m else None
            if number is not None:
                measure = number
            score.barlines.append(Barline(t, number, tok))
            for sp in spines:  # notes crossing a barline mean the timing went wrong
                if sp.kind == "**kern" and sp.end_min is not None and sp.end_min > t:
                    score.warnings.append(
                        f"line {lineno}: spine {sp.top} has a note crossing the barline at {t}"
                    )
            continue

        # Data line.
        timed = False
        for sp, tok in zip(spines, toks, strict=True):
            if sp.kind != "**kern" or tok == ".":
                continue
            if sp.end_min is not None and sp.end_min > t:
                score.warnings.append(
                    f"line {lineno}: spine {sp.top} starts an event at {t} while the previous "
                    f"one lasts until {sp.end_min}"
                )
            durs: list[Fraction] = []
            prev_dur: Fraction | None = None
            # A chord with any grace subtoken is a grace chord (encoders often mark only one).
            grace = "q" in tok or "Q" in tok
            for sub in tok.split(" "):
                if not sub or sub == ".":
                    continue
                dur = Fraction(0) if grace else (parse_duration(sub) or prev_dur)
                if dur is None:
                    score.warnings.append(f"line {lineno}: no duration in {sub!r}")
                    continue
                prev_dur = dur
                durs.append(dur)
                if "r" in sub:
                    midi, name = None, None
                else:
                    p = parse_pitch(sub)
                    if p is None:
                        score.warnings.append(f"line {lineno}: no pitch in {sub!r}")
                        continue
                    midi, name = p
                score.notes.append(
                    Note(
                        t,
                        dur,
                        midi,
                        name,
                        sp.top,
                        sp.voice,
                        sp.staff,
                        sp.part,
                        measure,
                        _tie(sub),
                        grace,
                    )
                )
            if durs:
                sp.end_min, sp.end = t + min(durs), t + max(durs)
                timed = timed or max(durs) > 0

        if timed:
            for sp, tok in zip(spines, toks, strict=True):
                if sp.kind == "**kern" and tok == "." and sp.end is not None and sp.end <= t:
                    score.warnings.append(f"line {lineno}: spine {sp.top} has no event at {t}")
                    sp.end = sp.end_min = None  # don't let a silent spine stall time
        if not timed:
            continue  # all-null or grace-only lines take no time
        # The next line starts when the earliest still-sounding note ends, in any spine. (A
        # chord's short note can end while a longer one keeps the spine busy.)
        candidates = [
            e
            for sp in spines
            if sp.kind == "**kern"
            for e in (sp.end_min, sp.end)
            if e is not None and e > t
        ]
        if candidates:
            t = min(candidates)

    if spines is None:
        raise KernError("no exclusive interpretation line (**kern ...) found")
    score.duration = max([t] + [n.end for n in score.notes])
    return score


def merge_ties(notes: list[Note]) -> list[Note]:
    """Join tied notes into single notes (per voice and pitch). Untied notes pass through."""
    out: list[Note] = []
    open_ties: dict[tuple[int, str, int | None], int] = {}  # (spine, voice, midi) -> index in out
    for n in sorted(notes, key=lambda n: n.onset):
        if n.is_rest or n.tie is None:
            out.append(n)
            continue
        key = (n.spine, n.voice, n.midi)
        if n.tie == "start" or key not in open_ties:
            open_ties[key] = len(out)
            out.append(replace(n, tie=None))
            continue
        i = open_ties[key]
        head = out[i]
        out[i] = replace(head, duration=n.end - head.onset)
        if n.tie == "end":
            del open_ties[key]
    return out
