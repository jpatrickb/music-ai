"""Restore exact note lengths in MusicXML that an exporter rounded to whole ticks.

MusicXML gives every note both its notated value (``<type>``, ``<dot>``, ``<time-modification>``)
and a length in ticks (``<duration>``, in ``<divisions>`` per quarter). With 480 ticks per quarter,
a sixteenth in a 9:8 tuplet is 106⅔ ticks, which MuseScore writes as 107, then compensates with
``<forward>``/``<backup>`` elements a few ticks long. Readers (music21, humlib) trust the ticks,
so tuplet runs and everything after them in the bar drift slightly, and converters reject the
resulting impossible lengths.

``restore`` rewrites a score at a finer resolution (``<divisions>`` times the least common
multiple of all tuplet sizes in the file) where every tuplet length is a whole number of ticks:
- a note's length comes from its notated value when that is within ``TOLERANCE`` ticks of the
  stored length, else the stored length is kept;
- a ``<backup>``/``<forward>`` lands on the exact position it was rounded from (a position some
  earlier note in the bar started or ended at, within ``TOLERANCE``), and a ``<forward>`` of
  ``TOLERANCE`` ticks or fewer, which no notation produces, is a rounding correction and becomes 0.
The notes, their order and the notation are unchanged.
"""

from __future__ import annotations

import xml.etree.ElementTree as ET
from fractions import Fraction
from math import lcm

TOLERANCE = 3  # ticks, at the file's original resolution

_TYPES = {
    "maxima": Fraction(32),
    "long": Fraction(16),
    "breve": Fraction(8),
    "whole": Fraction(4),
    "half": Fraction(2),
    "quarter": Fraction(1),
    "eighth": Fraction(1, 2),
    "16th": Fraction(1, 4),
    "32nd": Fraction(1, 8),
    "64th": Fraction(1, 16),
    "128th": Fraction(1, 32),
    "256th": Fraction(1, 64),
    "512th": Fraction(1, 128),
    "1024th": Fraction(1, 256),
}


def notated_length(note: ET.Element) -> Fraction | None:
    """Quarter notes implied by a note's type, dots and tuplet ratio; None if it has no type."""
    t = (note.findtext("type") or "").strip()
    if t not in _TYPES:
        return None
    q = dot = _TYPES[t]
    for _ in note.findall("dot"):
        dot /= 2
        q += dot
    tm = note.find("time-modification")
    if tm is not None:
        q = q * int(tm.findtext("normal-notes") or 1) / int(tm.findtext("actual-notes") or 1)
    return q


def _ticks(q: Fraction, div: int) -> str:
    t = q * div
    if t.denominator != 1:
        raise ValueError(f"{q} quarters is not a whole number of ticks at {div} per quarter")
    return str(t.numerator)


def restore(root: ET.Element) -> int:
    """Rewrite ``root`` (a ``score-partwise``) in place; returns how many lengths were changed."""
    factor = lcm(1, *(int(t.text or 1) for t in root.iter("actual-notes")))
    changed = 0
    for part in root.iter("part"):
        div = 0
        for measure in part.iter("measure"):
            for d in measure.iter("divisions"):
                div = int(d.text or 1)
                d.text = str(div * factor)
            changed += _restore_measure(measure, div, factor)
    return changed


def _restore_measure(measure: ET.Element, div: int, factor: int) -> int:
    new_div = div * factor
    changed = 0
    cur_old, cur_new = 0, Fraction(0)
    start_old, start_new = 0, Fraction(0)
    seen = {0: Fraction(0)}  # tick position at the old resolution -> exact position

    def near_seen(old: int) -> int | None:
        k = min(seen, key=lambda s: abs(s - old))
        return k if abs(k - old) <= TOLERANCE else None

    for el in measure:
        dur = el.find("duration")
        if dur is None or el.tag not in ("note", "backup", "forward"):
            if el.tag in ("direction", "harmony", "figured-bass"):
                for o in el.iter("offset"):
                    o.text = str(round(float(o.text or 0) * factor))
            continue
        old = int(dur.text or 0)
        if el.tag == "note":
            exact = notated_length(el)
            if exact is None or abs(exact * div - old) > TOLERANCE:
                exact = Fraction(old, div)
            elif exact * div != old:
                changed += 1
            dur.text = _ticks(exact, new_div)
            if el.find("chord") is None:
                start_old, start_new = cur_old, cur_new
                cur_old, cur_new = cur_old + old, cur_new + exact
            seen.setdefault(start_old, start_new)
            seen[start_old + old] = start_new + exact
            continue
        target_old = cur_old - old if el.tag == "backup" else cur_old + old
        k = near_seen(target_old)
        if el.tag == "forward" and old <= TOLERANCE:
            target_new = cur_new  # the exporter's rounding correction
        elif k is not None:
            target_new = seen[k]
        else:
            target_new = cur_new + (Fraction(old, div) * (1 if el.tag == "forward" else -1))
        amount = target_new - cur_new if el.tag == "forward" else cur_new - target_new
        dur.text = _ticks(amount, new_div)
        cur_old, cur_new = target_old, target_new
        seen.setdefault(cur_old, cur_new)
    return changed
