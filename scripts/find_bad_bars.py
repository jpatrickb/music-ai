"""List bars in a MusicXML file whose stored lengths don't add up: a diagnostic for files that
scripts/musicxml_to_kern.py rejects. (Rounded tuplet lengths, the usual cause, are repaired
automatically there by ``music_ai.musicxml_ticks``; a bar written longer than its time signature,
like a free cadenza, is legitimate.)

Two problems are reported, both judged by music21's reading of the file:
- a voice that runs past the end of its bar (more beats than the time signature allows);
- notes of an odd length: a fraction of a quarter whose numerator is above 9 (other than 12 or
  15), e.g. 107/480 or 11/96, which no ordinary note or common tuplet produces. Typically a
  cadenza run typed as a tuplet with an irregular ratio.

Secondary voices that stop partway through a bar are normal and not reported.

Usage:
    uv run scripts/find_bad_bars.py FILE.mxl|FILE.musicxml [...]
"""

from __future__ import annotations

import sys
import warnings
from fractions import Fraction

import music21


def _q(x: float | Fraction) -> Fraction:
    return Fraction(x).limit_denominator(10_000)


def _odd(q: Fraction) -> bool:
    return q.denominator > 1 and q.numerator > 9 and q.numerator not in (12, 15)


def bad_bars(score: music21.stream.Score) -> list[str]:
    out = []
    for pi, part in enumerate(score.parts):
        staff = part.partName or f"staff {pi + 1}"
        if len(score.parts) == 2:
            staff = ("RH", "LH")[pi]
        ts = None
        for m in part.getElementsByClass("Measure"):
            ts = m.timeSignature or ts or m.getContextByClass("TimeSignature")
            bar = _q(ts.barDuration.quarterLength) if ts else None
            for vi, v in enumerate(m.voices or [m], 1):
                notes = [n for n in v.notesAndRests if not n.duration.isGrace]
                end = max((_q(n.offset) + _q(n.quarterLength) for n in notes), default=0)
                where = f"bar {m.number} {staff}" + (f" voice {vi}" if m.voices else "")
                if bar is not None and end > bar:
                    out.append(
                        f"{where}: too long, {float(end):g} beats in a {float(bar):g}-beat bar"
                    )
                odd = [n for n in notes if _odd(_q(n.quarterLength))]
                if odd:
                    names = [n.pitches[0].nameWithOctave if n.pitches else "rest" for n in odd]
                    out.append(
                        f"{where}: {len(odd)} notes of odd length "
                        f"({_q(odd[0].quarterLength)} of a quarter), starting {names[0]}"
                    )
    return out


def main(argv: list[str] | None = None) -> int:
    paths = argv if argv is not None else sys.argv[1:]
    found = 0
    for path in paths:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            score = music21.converter.parse(path, forceSource=True)
        problems = bad_bars(score)
        found += len(problems)
        print(f"{path}: {len(problems) or 'no'} problems")
        for p in problems:
            print("  ", p)
    return 1 if found else 0


if __name__ == "__main__":
    sys.exit(main())
