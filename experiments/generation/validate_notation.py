"""Validate ABC and **kern scores mechanically with real parsers.

Checks each score with music21 (parse + per-measure duration vs. time signature) and
Verovio (load; optional SVG render). Accepts .abc / .krn files, or Markdown files, in which
case every fenced code block tagged ```abc or ```kern is validated. Blocks tagged
```abc-fragment / ```kern-fragment are skipped (for partial snippets that aren't full scores).

Usage:
    uv run experiments/generation/validate_notation.py piece.abc piece.krn
    uv run experiments/generation/validate_notation.py experiments/generation/encoding/abc-reference.md
    uv run experiments/generation/validate_notation.py piece.abc --svg outputs/renders
"""

from __future__ import annotations

import argparse
import os
import re
import sys
import tempfile
from concurrent.futures import ProcessPoolExecutor
from concurrent.futures.process import BrokenProcessPool
from dataclasses import dataclass, field
from fractions import Fraction
from pathlib import Path

import music21
import verovio

from music_ai.kern import malformed_pitch

FENCE_RE = re.compile(r"^```(abc|kern)[ \t]*\n(.*?)^```[ \t]*$", re.MULTILINE | re.DOTALL)


@dataclass
class Score:
    fmt: str  # "abc" or "kern"
    text: str
    label: str  # e.g. "file.md:123"


@dataclass
class Result:
    score: Score
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


def extract_scores(path: Path) -> list[Score]:
    text = path.read_text(encoding="utf-8")
    suffix = path.suffix.lower()
    if suffix == ".abc":
        return [Score("abc", text, str(path))]
    if suffix in {".krn", ".kern"}:
        return [Score("kern", text, str(path))]
    if suffix == ".md":
        scores = []
        for m in FENCE_RE.finditer(text):
            line = text.count("\n", 0, m.start()) + 1
            scores.append(Score(m.group(1), m.group(2), f"{path}:{line}"))
        return scores
    raise ValueError(f"unsupported file type: {path}")


def check_music21(score: Score, result: Result) -> None:
    try:
        parsed = music21.converter.parse(
            score.text, format="abc" if score.fmt == "abc" else "humdrum"
        )
    except Exception as e:  # noqa: BLE001 -- music21 raises many exception types
        result.errors.append(f"music21 failed to parse: {type(e).__name__}: {e}")
        return

    parts = list(parsed.parts) if hasattr(parsed, "parts") and parsed.parts else [parsed]
    # ABC voices declared in the header show up as extra empty parts; ignore them.
    parts = [p for p in parts if p.recurse().notes]
    if not parts:
        result.errors.append("music21 parsed no notes")
        return

    declared = declared_abc_meters(score.text) if score.fmt == "abc" else None
    unmeasured: list[int] = []  # 0-based indices of parts music21 built no measures for
    spans: list[tuple[str, list[Fraction]]] = []  # bar lengths per measured part, for alignment

    for i, part in enumerate(parts, 1):
        label = part_label(part, i, score.fmt)
        measures = list(part.getElementsByClass(music21.stream.Measure))
        if not measures:
            # music21 only builds ABC measures when a voice has >= 2 regular `|` barlines (`|]`
            # doesn't count), so very short tunes land here. So does a garbled parse, e.g. an ABC
            # voice re-entered after another voice (V:1, V:2, V:1).
            unmeasured.append(i - 1)
            if score.fmt == "kern":
                result.warnings.append(
                    f"{label}: music21 built no measures, so bar durations were NOT checked"
                )
            continue
        if any(not isinstance(n, music21.harmony.Harmony) for n in part.recurse().notes):
            # (a part holding only harmony objects, e.g. analysis, has no rhythm to align)
            spans.append(
                (
                    label,
                    [Fraction(note_span(m)).limit_denominator(64) for m in measures],
                )
            )
        for j, m in enumerate(measures):
            # m.timeSignature is the measure's own signature (bar 1, meter changes);
            # getContextByClass only looks backwards from inside the measure, so it misses it.
            ts = m.timeSignature or m.getContextByClass(music21.meter.TimeSignature)
            if ts is None:
                continue
            if declared is not None and m.timeSignature and ts.ratioString not in declared:
                # music21 "repairs" an overlong ABC bar by splitting it and inventing a meter
                # for the overflow (e.g. 5 beats in 4/4 -> a 4/4 bar plus a 1/4 bar).
                result.errors.append(
                    f"{label}, bar {j}: overflows the meter (music21 split it and "
                    f"invented a {ts.ratioString} bar for the excess)"
                )
                continue
            expected = Fraction(ts.barDuration.quarterLength).limit_denominator(64)
            actual = Fraction(note_span(m)).limit_denominator(64)
            if actual == expected:
                continue
            # A short first measure (pickup) or last measure is legal.
            if actual < expected and j in (0, len(measures) - 1):
                continue
            # Positional bar count: music21's own measure numbers depend on pickup detection.
            result.errors.append(
                f"{label}, bar {j + 1}: {float(actual):g} quarter notes, "
                f"time signature {ts.ratioString} needs {float(expected):g}"
            )

    if score.fmt == "abc":
        check_abc_tokens(score, result, unmeasured, len(parts), spans)
    elif not unmeasured:
        result.errors.extend(bar_alignment_errors(spans))


def part_label(part: music21.stream.Stream, index: int, fmt: str) -> str:
    """How errors name a part. music21 lists kern spines right to left but keeps the column in
    part.id ("spine_0" = leftmost), so kern parts are named by column, counting from 1."""
    m = re.fullmatch(r"spine_(\d+)", str(part.id))
    if fmt == "kern" and m:
        return f"spine {int(m.group(1)) + 1}"
    return f"voice/spine {index}"


def bar_alignment_errors(voices: list[tuple[str, list[Fraction]]]) -> list[str]:
    """Voices that disagree on bar count, or on the length of the same bar.

    voices: (label, bar lengths in quarter notes) per voice/spine. A pickup or short final bar is
    only fine when every voice has the same short length, so any difference is an error.
    """
    if len(voices) < 2:
        return []
    counts = {len(bars) for _, bars in voices}
    if len(counts) > 1:
        detail = ", ".join(f"{label}: {len(bars)}" for label, bars in voices)
        return [f"voices have different bar counts ({detail})"]
    errors = []
    for j in range(counts.pop()):
        lengths = [bars[j] for _, bars in voices]
        if len(set(lengths)) > 1:
            detail = ", ".join(f"{label}: {float(bars[j]):g}" for label, bars in voices)
            errors.append(f"bar {j + 1}: voices have different lengths in quarter notes ({detail})")
    return errors


def note_span(measure: music21.stream.Measure) -> float:
    """Where the measure's last note or rest ends, in quarter notes.

    Not measure.duration: that includes harmony objects, and music21 gives every RomanNumeral
    (kern **harm) a default quarter-note length, so a label on the last eighth of a bar would
    make it look an eighth too long. ABC chord symbols are Harmony objects too.
    """
    end = 0.0
    for el in measure.recurse().notesAndRests:
        if isinstance(el, music21.harmony.Harmony):
            continue
        end = max(end, el.getOffsetInHierarchy(measure) + el.quarterLength)
    return end


def check_abc_tokens(
    score: Score,
    result: Result,
    unmeasured: list[int],
    n_parts: int,
    spans: list[tuple[str, list[Fraction]]],
) -> None:
    """Run the token-level ABC bar counter: voice re-entry warnings and cross-voice bar alignment
    always, and bar lengths for the voices music21 built no measures for (unmeasured: their
    0-based part indices). spans: music21's bar lengths, the alignment fallback."""
    try:
        bars, warnings = abc_bars(score.text)
    except AbcCountError as e:
        result.warnings.extend(
            f"voice/spine {i + 1}: music21 built no measures and the token counter gave up "
            f"({e}), so bar durations were NOT checked"
            for i in unmeasured
        )
        if not unmeasured:  # music21 measured every voice; align on its bars instead
            result.errors.extend(bar_alignment_errors(spans))
        return
    result.warnings.extend(warnings)
    result.errors.extend(
        bar_alignment_errors([(f"voice {v}", [b.length * 4 for b in bs]) for v, bs in bars.items()])
    )
    if not unmeasured:
        return
    voices = list(bars.values())  # in order of first appearance, like music21's parts
    if len(voices) == n_parts:  # same voices: check only the ones music21 didn't
        voices = [voices[i] for i in unmeasured]
    for voice_bars in voices:
        result.errors.extend(abc_bar_errors(voice_bars))


ABC_METER_RE = re.compile(r"(?:^|\[)M:\s*([^\]\s%]+)", re.MULTILINE)


def declared_abc_meters(text: str) -> set[str]:
    """Meters written in the ABC source as M: fields (header, body line, or inline [M:...])."""
    aliases = {"C": "4/4", "C|": "2/2"}
    return {aliases.get(m, m) for m in ABC_METER_RE.findall(text)}


# --- Token-level ABC bar counter --------------------------------------------------------------
# music21 builds no ABC measures for voices with fewer than 2 regular `|` barlines, so this
# counter sums note lengths straight from the source text instead. It covers the subset the
# encoding docs teach; anything it doesn't recognise raises AbcCountError rather than guessing.


class AbcCountError(ValueError):
    """The token counter met syntax it doesn't handle; its bar lengths can't be trusted."""


@dataclass
class AbcBar:
    voice: str
    length: Fraction  # in whole notes
    meter: Fraction | None  # bar length the meter requires, in whole notes; None for M:none
    meter_str: str
    line: int


@dataclass
class _AbcVoiceState:
    meter: Fraction | None
    meter_str: str
    unit: Fraction  # L:, or the default derived from the header meter


ABC_LINE_FIELD_RE = re.compile(r"^([A-Za-z]):(.*)$")
ABC_INLINE_FIELD_RE = re.compile(r"\[([A-Za-z]):([^\]]*)\]")
# |  ||  |]  [|  |:  :|  :|:  ::  plus an optional ending number (|1, :|2, [1,3)
ABC_BARLINE_RE = re.compile(r"(?::*\[?\|+\]?:*|:{2,})(?:\s*\[?\d+(?:[,-]\d+)*)?")
ABC_ENDING_RE = re.compile(r"\[\d+(?:[,-]\d+)*")
ABC_NOTE_RE = re.compile(r"(?:\^{1,2}|_{1,2}|=)?[A-Ga-g][',]*|[zx]")
ABC_LENGTH_RE = re.compile(r"(\d*)(/*)(\d*)")
ABC_TUPLET_RE = re.compile(r"\((\d)(?::(\d*))?(?::(\d*))?")
ABC_MULTIREST_RE = re.compile(r"[ZX](\d*)")
# Single-letter decorations (~ T H L M P S O u v, user-defined H-W h-w), spacer y, ties, slurs,
# staccato dots, backquotes and line continuations carry no duration.
ABC_SKIP_CHARS = set(" \t-().~`\\yHIJKLMNOPQRSTUVWhijklmnopqrstuvw")


def _abc_meter(value: str) -> tuple[Fraction | None, str]:
    value = value.split("%")[0].strip()
    value = {"C": "4/4", "C|": "2/2"}.get(value, value)
    if value.lower() in {"", "none"}:
        return None, "none"
    try:
        num, den = value.split("/")
        return Fraction(sum(int(n) for n in num.split("+")), int(den)), value
    except ValueError as e:
        raise AbcCountError(f"unsupported meter M:{value}") from e


def _abc_length(text: str, pos: int) -> tuple[Fraction, int]:
    """Parse a length multiplier at pos (`2`, `/`, `//`, `/4`, `3/2`); returns (multiplier, end)."""
    m = ABC_LENGTH_RE.match(text, pos)
    num, slashes, den = m.groups()
    mult = Fraction(int(num) if num else 1)
    if slashes:
        if den and len(slashes) > 1:
            raise AbcCountError(f"ambiguous length {m.group()!r}")
        mult /= int(den) if den else 2 ** len(slashes)
    elif den:  # unreachable: ABC_LENGTH_RE puts leading digits in num
        raise AbcCountError(f"bad length {m.group()!r}")
    return mult, m.end()


def _abc_tuplet_q(p: int, meter: Fraction | None, meter_str: str) -> int:
    if p in (3, 6):
        return 2
    if p in (2, 4, 8):
        return 3
    top = int(meter_str.split("/")[0]) if meter and "/" in meter_str else 0
    compound = top % 3 == 0 and top > 3
    return 3 if compound else 2


def abc_bars(text: str) -> tuple[dict[str, list[AbcBar]], list[str]]:
    """Sum the length of every bar of every voice in an ABC tune, from the tokens.

    Returns ({voice id: bars in order}, warnings). Handles L:/M: (header, body lines, inline
    fields), V: blocks, tuplets, broken rhythm, chords, grace notes, rests, multi-bar rests, ties,
    decorations, quoted strings, and endings. Raises AbcCountError on anything else.
    """
    header_meter: tuple[Fraction | None, str] = (None, "none")
    header_unit: Fraction | None = None
    in_header = True
    voices: dict[str, _AbcVoiceState] = {}
    bars: dict[str, list[AbcBar]] = {}
    music_order: list[str] = []  # voices in the order their music blocks appear
    warnings: list[str] = []

    voice = "1"
    bar_len = Fraction(0)
    bar_has_content = False
    last_dur: Fraction | None = None  # length of the previous note/rest/chord, for > and <
    next_factor = Fraction(1)  # pending broken-rhythm factor for the next note
    tuplet_left, tuplet_factor = 0, Fraction(1)

    def state() -> _AbcVoiceState:
        if voice not in voices:
            meter, meter_str = header_meter
            # ABC default unit length: 1/16 for meters under 3/4, else 1/8. Fixed by the header
            # meter; a later M: change doesn't alter it.
            default = (
                Fraction(1, 16) if meter is not None and meter < Fraction(3, 4) else Fraction(1, 8)
            )
            voices[voice] = _AbcVoiceState(meter, meter_str, header_unit or default)
        return voices[voice]

    def unit() -> Fraction:
        return state().unit

    def push_bar(line: int) -> None:
        nonlocal bar_len, bar_has_content, last_dur
        if bar_has_content:
            st = state()
            bars.setdefault(voice, []).append(AbcBar(voice, bar_len, st.meter, st.meter_str, line))
        bar_len, bar_has_content, last_dur = Fraction(0), False, None

    def set_field(key: str, value: str, line: int) -> None:
        nonlocal header_meter, header_unit, voice, in_header
        if key == "M":
            if in_header:
                header_meter = _abc_meter(value)
            else:
                state().meter, state().meter_str = _abc_meter(value)
        elif key == "L":
            u = _abc_length(value.split("%")[0].strip(), 0)[0]
            if in_header:
                header_unit = u
            else:
                state().unit = u
        elif key == "K":
            in_header = False
        elif key == "V":
            if in_header:
                return  # a declaration only
            push_bar(line)
            voice = value.split()[0] if value.split() else "1"

    def add_event(dur: Fraction, line: int) -> None:
        nonlocal bar_len, bar_has_content, last_dur, next_factor, tuplet_left
        if music_order[-1:] != [voice]:
            if voice in music_order:
                warnings.append(
                    f"line {line}: voice {voice} resumes after another voice; music21 garbles "
                    "this (write all of one voice, then the next)"
                )
            music_order.append(voice)
        dur *= next_factor
        next_factor = Fraction(1)
        if tuplet_left:
            dur *= tuplet_factor
            tuplet_left -= 1
        bar_len += dur
        bar_has_content = True
        last_dur = dur

    for n, raw in enumerate(text.splitlines(), 1):
        if raw.startswith("%"):
            continue
        field_m = ABC_LINE_FIELD_RE.match(raw)
        if field_m:
            set_field(field_m.group(1), field_m.group(2), n)
            continue
        if in_header:
            continue  # before K: (e.g. stray text); nothing musical yet
        i = 0
        while i < len(raw):
            c = raw[i]
            if c == "%":
                break
            if c == '"':
                end = raw.find('"', i + 1)
                if end < 0:
                    raise AbcCountError(f"line {n}: unterminated quoted string")
                i = end + 1
            elif c in "!+":
                end = raw.find(c, i + 1)
                if end < 0:
                    raise AbcCountError(f"line {n}: unterminated {c}decoration{c}")
                i = end + 1
            elif c == "{":
                end = raw.find("}", i + 1)  # grace notes take no time
                if end < 0:
                    raise AbcCountError(f"line {n}: unterminated grace group")
                i = end + 1
            elif m := ABC_INLINE_FIELD_RE.match(raw, i):
                set_field(m.group(1), m.group(2), n)
                i = m.end()
            elif m := ABC_BARLINE_RE.match(raw, i):
                push_bar(n)
                i = m.end()
            elif m := ABC_ENDING_RE.match(raw, i):
                i = m.end()
            elif c == "[":
                end = raw.find("]", i + 1)
                if end < 0:
                    raise AbcCountError(f"line {n}: unterminated chord")
                inner = re.sub(r'"[^"]*"|![^!]*!', "", raw[i + 1 : end])
                first = ABC_NOTE_RE.search(inner)
                if first is None:
                    raise AbcCountError(f"line {n}: chord with no notes")
                note_mult, _ = _abc_length(inner, first.end())
                chord_mult, i = _abc_length(raw, end + 1)
                add_event(unit() * note_mult * chord_mult, n)
            elif m := ABC_NOTE_RE.match(raw, i):
                mult, i = _abc_length(raw, m.end())
                add_event(unit() * mult, n)
            elif m := ABC_TUPLET_RE.match(raw, i):
                p = int(m.group(1))
                q = (
                    int(m.group(2))
                    if m.group(2)
                    else _abc_tuplet_q(p, state().meter, state().meter_str)
                )
                tuplet_left = int(m.group(3)) if m.group(3) else p
                tuplet_factor = Fraction(q, p)
                i = m.end()
            elif c in "<>":
                j = i
                while j < len(raw) and raw[j] == c:
                    j += 1
                if last_dur is None:
                    raise AbcCountError(f"line {n}: broken rhythm {c} without a preceding note")
                short = Fraction(1, 2 ** (j - i))
                first_f, second_f = (2 - short, short) if c == ">" else (short, 2 - short)
                bar_len += last_dur * (first_f - 1)
                next_factor = second_f
                i = j
            elif m := ABC_MULTIREST_RE.match(raw, i):
                push_bar(n)
                st = state()
                for _ in range(int(m.group(1) or 1)):
                    bars.setdefault(voice, []).append(
                        AbcBar(voice, st.meter or Fraction(0), st.meter, st.meter_str, n)
                    )
                i = m.end()
            elif c in ABC_SKIP_CHARS:
                i += 1
            elif c == "&":
                raise AbcCountError(f"line {n}: voice overlay `&` is not supported")
            else:
                raise AbcCountError(f"line {n}: unrecognised character {c!r}")
    push_bar(len(text.splitlines()))
    return bars, warnings


def abc_bar_errors(bars: list[AbcBar]) -> list[str]:
    """Bars whose length doesn't match the meter (a short first or last bar is allowed)."""
    errors = []
    for j, bar in enumerate(bars):
        if bar.meter is None or bar.length == bar.meter:
            continue
        if bar.length < bar.meter and j in (0, len(bars) - 1):
            continue
        errors.append(
            f"voice {bar.voice}, bar {j + 1}: {float(bar.length * 4):g} quarter notes, "
            f"time signature {bar.meter_str} needs {float(bar.meter * 4):g} (token count)"
        )
    return errors


ABC_QUOTED_RE = re.compile(r'"([^"]*)"')
ABC_HEADER_RE = re.compile(r"^[A-Za-z]:")


def check_abc_quotes(score: Score, result: Result) -> None:
    """Quoted strings are chord symbols unless prefixed with ^ _ < > @ (free-text annotations).

    music21 silently drops quoted strings that aren't valid chord symbols (e.g. "V7/vi"), so a
    Roman numeral written without a prefix disappears from the parsed score.
    """
    for n, line in enumerate(score.text.splitlines(), 1):
        if line.startswith("%") or ABC_HEADER_RE.match(line):
            continue
        for text in ABC_QUOTED_RE.findall(line):
            if text and text[0] not in "^_<>@" and text[0] not in "ABCDEFG":
                result.warnings.append(
                    f'line {n}: "{text}" is not a chord symbol; use "_{text}" or "^{text}" '
                    "for an annotation"
                )


def _verovio_render(fmt: str, text: str, want_svg: bool) -> tuple[bool, str, str]:
    """Runs in a child process: Verovio's C++ core can abort() on malformed input.

    Returns (loaded, svg, log). Verovio's own warnings and humlib's messages (e.g. "Inconsistent
    rhythm analysis" for a time-misaligned kern score, which still loads) are written straight to
    file descriptor 2, not to tk.getLog(), so capture fd 2 for the duration of the call.
    """
    verovio.enableLog(verovio.LOG_WARNING)
    tk = verovio.toolkit()
    tk.setOptions({"inputFrom": "abc" if fmt == "abc" else "humdrum"})
    with tempfile.TemporaryFile() as captured:
        sys.stderr.flush()
        saved_fd = os.dup(2)
        os.dup2(captured.fileno(), 2)
        try:
            ok = bool(tk.loadData(text))
            svg = tk.renderToSVG(1) if ok and want_svg else ""
        finally:
            os.dup2(saved_fd, 2)
            os.close(saved_fd)
        captured.seek(0)
        log = captured.read().decode("utf-8", errors="replace")
    return ok, svg, log + tk.getLog()


def check_verovio(score: Score, result: Result, svg_dir: Path | None, index: int) -> None:
    with ProcessPoolExecutor(max_workers=1) as pool:
        try:
            ok, svg, log = pool.submit(
                _verovio_render, score.fmt, score.text, svg_dir is not None
            ).result()
        except BrokenProcessPool:
            result.errors.append("verovio crashed on this input")
            return
    result.warnings.extend(verovio_messages(log))
    if not ok:
        result.errors.append("verovio failed to load the score")
        return
    if svg_dir is not None:
        svg_dir.mkdir(parents=True, exist_ok=True)
        stem = re.sub(r"[^A-Za-z0-9]+", "_", score.label).strip("_")[-80:]
        out = svg_dir / f"{index:03d}_{stem}.svg"
        out.write_text(svg, encoding="utf-8")
        result.warnings.append(f"rendered {out}")


def verovio_messages(log: str) -> list[str]:
    """Group Verovio/humlib log output into one warning per message.

    A message starts with a "Error:"/"Warning:"-style prefix and may continue on further lines
    (humlib adds "Expected durationFromStart ..." and the offending "Line: ..." row).
    """
    messages: list[list[str]] = []
    for line in log.splitlines():
        line = line.strip()
        if not line:
            continue
        if re.match(r"^\[?(Error|Warning|Info|Debug)\b", line, re.IGNORECASE) or not messages:
            messages.append([line])
        else:
            messages[-1].append(line)
    counts: dict[str, int] = {}
    for m in messages:
        text = " | ".join(m).replace("\t", " ")
        if not VEROVIO_KNOWN_LIMITS_RE.search(text):
            counts[text] = counts.get(text, 0) + 1
    return [f"verovio: {text}" + (f" (x{k})" if k > 1 else "") for text, k in counts.items()]


# Verovio's ABC importer warns about features it can't render (it stacks voices on one staff,
# ignores key changes, ...). Those are known render limitations, not
# problems with the score, and they fire on every multi-voice tune, so they're dropped. So is the
# missing-T: notice.
VEROVIO_KNOWN_LIMITS_RE = re.compile(
    r"ABC import: (Multi-voice music is not supported|Annotations are not fully support"
    r"|Key changes not supported|Tempo definitions are not fully supported"
    r"|Title field missing)"
)


def check_kern_spines(score: Score, result: Result) -> None:
    """Cheap structural check: every data line has as many tab-separated fields as active spines."""
    spines = None
    for n, line in enumerate(score.text.splitlines(), 1):
        if not line or line.startswith("!!"):
            continue
        fields = line.split("\t")
        if spines is None:
            if not all(f.startswith("**") for f in fields):
                result.errors.append(f"line {n}: first non-comment line must be ** headers")
                return
            spines = len(fields)
            continue
        if len(fields) != spines:
            result.errors.append(f"line {n}: {len(fields)} fields but {spines} active spines")
            return
        if all(f.startswith("*") for f in fields):
            if all(f == "*-" for f in fields):
                return
            # *^ splits one spine into two; *v merges adjacent spines.
            spines += fields.count("*^")
            merges = fields.count("*v")
            if merges:
                runs = re.findall(r"(?:\*v\t?)+", "\t".join(fields) + "\t")
                spines -= sum(r.count("*v") - 1 for r in runs)
    result.errors.append("missing *- spine terminators")


def check_kern_pitches(score: Score, result: Result) -> None:
    """Error on misspelled pitches such as ``f#f#`` for F#5 (should be ``ff#``), which Verovio
    renders and plays as a double sharp in the wrong octave."""
    kinds: list[str] | None = None
    for n, line in enumerate(score.text.splitlines(), 1):
        if not line or line.startswith("!"):
            continue
        fields = line.split("\t")
        if line.startswith("**"):
            kinds = fields
            continue
        if kinds is None or line.startswith(("*", "=")):
            if line.startswith("*") and kinds is not None:
                kinds = _next_kinds(kinds, fields)
            continue
        for tok, kind in zip(fields, kinds, strict=False):
            if kind != "**kern" or tok == ".":
                continue
            for sub in tok.split(" "):
                if "r" not in sub and malformed_pitch(sub):
                    result.errors.append(
                        f"line {n}: malformed pitch {sub!r} (repeat the letter for the octave, "
                        "then the accidental once: ff# = F#5)"
                    )


def _next_kinds(kinds: list[str], fields: list[str]) -> list[str]:
    """Spine data types after a tandem-interpretation line (handles *^, *v runs and *-)."""
    new, i = [], 0
    while i < len(fields) and i < len(kinds):
        f = fields[i]
        if f == "*^":
            new += [kinds[i], kinds[i]]
        elif f == "*v":
            while i + 1 < len(fields) and fields[i + 1] == "*v":
                i += 1
            new.append(kinds[i])
        elif f != "*-":
            new.append(kinds[i])
        i += 1
    return new


def validate(score: Score, svg_dir: Path | None, index: int) -> Result:
    result = Result(score)
    if score.fmt == "kern":
        check_kern_spines(score, result)
        if result.errors:
            # Verovio's humdrum reader abort()s on broken spine structure, which kills the worker
            # and makes macOS pop a "Python quit unexpectedly" dialog. Report the spine error only.
            return result
        check_kern_pitches(score, result)
    else:
        check_abc_quotes(score, result)
    check_music21(score, result)
    check_verovio(score, result, svg_dir, index)
    return result


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    ap.add_argument("paths", nargs="+", type=Path)
    ap.add_argument("--svg", type=Path, default=None, help="directory to write SVG renders into")
    args = ap.parse_args(argv)

    scores = [s for p in args.paths for s in extract_scores(p)]
    if not scores:
        print("no abc/kern scores found", file=sys.stderr)
        return 1

    failed = 0
    for i, score in enumerate(scores):
        r = validate(score, args.svg, i)
        status = "FAIL" if r.errors else "ok  "
        print(f"{status} [{score.fmt}] {score.label}")
        for e in r.errors:
            print(f"     error: {e}")
        for w in r.warnings:
            print(f"     {w}")
        failed += bool(r.errors)

    print(f"\n{len(scores) - failed}/{len(scores)} scores passed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
