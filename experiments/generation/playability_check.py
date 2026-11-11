"""Playability and copying checks for generated two-staff piano pieces in **kern.

Concrete problems a pianist would flag, not style targets:

- hand-span    notes struck together in one hand spanning more than a 9th (high) or a 9th
               itself (low: needs large hands). An octave or less is never flagged.
- fast-leap    a jump within one hand between consecutive attacks that is large for the time
               available: more than a 10th within an eighth note, or more than two octaves
               within a quarter (low; stride and big Romantic textures do this on purpose).
- hand-cross   the right hand's lowest sounding note below the left hand's highest (low).
- chromatic-clash  the same letter name with different accidentals sounding at once in the two
               hands, e.g. A natural under A flat (medium), or in consecutive attacks across the
               hands within one beat, a cross relation (low).
- copy         (with --against) melody or bass runs of 9 notes whose intervals and rhythm match
               an excerpt (transposition-invariant). With --background (the composer's other
               pieces, minus the excerpts' sources), runs that also occur there are generic
               figuration and are ignored. 3+ distinctive runs or a 12+ note run is flagged
               high (above chance overlap, calibrated on pieces that never saw the excerpts);
               fewer is low. Without a background,
               any shared run is reported as medium.

Usage:
    uv run experiments/generation/playability_check.py piece.krn [more.krn ...]
    uv run experiments/generation/playability_check.py piece.krn --against ex1.krn ex2.krn \\
        --background data/kern/mozart-sonatas --exclude sonata15-1.krn sonata12-1.krn
"""

from __future__ import annotations

import argparse
import itertools
import re
import sys
from dataclasses import dataclass
from fractions import Fraction
from pathlib import Path

from music_ai.kern import KernScore, Note, merge_ties, parse_kern
from music_ai.style_stats import hands

SPAN_LOW, SPAN_HIGH = 13, 15  # semitones: a 9th is 13-14; more than that is high
COPY_N = 8  # steps per n-gram, i.e. runs of 9 notes
COPY_STRONG_RUNS, COPY_STRONG_LEN = 3, 12  # above the chance overlap seen in 002 arm A


@dataclass(frozen=True)
class Finding:
    check: str
    severity: str  # "high" | "medium" | "low"
    bar: int | None
    onset: Fraction
    reason: str

    def __str__(self) -> str:
        where = f"bar {self.bar}" if self.bar is not None else "-"
        return f"{where:>7}  {self.severity:<6} {self.check:<15} {self.reason}"


def _attacks(notes: list[Note]) -> list[tuple[Fraction, list[Note]]]:
    groups: dict[Fraction, list[Note]] = {}
    for n in notes:
        if n.midi is not None and n.tie not in ("continue", "end") and not n.grace:
            groups.setdefault(n.onset, []).append(n)
    return [(t, sorted(groups[t], key=lambda n: n.midi or 0)) for t in sorted(groups)]


def _letter_alter(name: str) -> tuple[str, int]:
    m = re.match(r"([A-G])(#+|-+)?", name)
    assert m
    acc = m.group(2) or ""
    return m.group(1), (len(acc) if acc.startswith("#") else -len(acc))


def check_hand_spans(rh: list[Note], lh: list[Note]) -> list[Finding]:
    out = []
    for label, part in (("RH", rh), ("LH", lh)):
        for t, group in _attacks(part):
            span = (group[-1].midi or 0) - (group[0].midi or 0)
            if span >= SPAN_LOW:
                sev = "high" if span >= SPAN_HIGH else "low"
                out.append(
                    Finding(
                        "hand-span",
                        sev,
                        group[0].measure,
                        t,
                        f"{label} {group[0].name}-{group[-1].name} spans {span} semitones",
                    )
                )
    return out


def check_fast_leaps(rh: list[Note], lh: list[Note]) -> list[Finding]:
    out = []
    for label, part in (("RH", rh), ("LH", lh)):
        att = _attacks(part)
        for (t0, g0), (t1, g1) in itertools.pairwise(att):
            # Compare the nearest notes of the two attacks: the smallest move the hand must make.
            leap = min(abs((a.midi or 0) - (b.midi or 0)) for a in g0 for b in g1)
            gap = t1 - t0
            if (leap > 16 and gap <= Fraction(1, 2)) or (leap > 24 and gap <= 1):
                out.append(
                    Finding(
                        "fast-leap",
                        "low",
                        g1[0].measure,
                        t1,
                        f"{label} jumps {leap} semitones in {gap} quarter(s) "
                        f"({g0[0].name} -> {g1[0].name})",
                    )
                )
    return out


def _sounding(notes: list[Note], t: Fraction) -> list[Note]:
    return [n for n in notes if n.onset <= t < n.end]


def check_hand_crossing(rh: list[Note], lh: list[Note]) -> list[Finding]:
    rh_m, lh_m = merge_ties(rh), merge_ties(lh)
    out = []
    for t in sorted({n.onset for n in rh_m} | {n.onset for n in lh_m}):
        r, left = _sounding(rh_m, t), _sounding(lh_m, t)
        if not r or not left:
            continue
        lo = min(r, key=lambda n: n.midi or 0)
        hi = max(left, key=lambda n: n.midi or 0)
        if (lo.midi or 0) < (hi.midi or 0):
            out.append(
                Finding("hand-cross", "low", lo.measure, t, f"RH {lo.name} is below LH {hi.name}")
            )
    return out


def check_chromatic_clashes(rh: list[Note], lh: list[Note]) -> list[Finding]:
    rh_m, lh_m = merge_ties(rh), merge_ties(lh)
    out = []
    seen: set[tuple[Fraction, str]] = set()
    for t in sorted({n.onset for n in rh_m} | {n.onset for n in lh_m}):
        for a in _sounding(rh_m, t):
            for b in _sounding(lh_m, t):
                la, aa = _letter_alter(a.name or "")
                lb, ab = _letter_alter(b.name or "")
                if la == lb and aa != ab and (t, la) not in seen:
                    seen.add((t, la))
                    out.append(
                        Finding(
                            "chromatic-clash",
                            "medium",
                            max(a.measure or 0, b.measure or 0) or None,
                            t,
                            f"RH {a.name} sounds against LH {b.name}",
                        )
                    )
    # Cross relations: consecutive attacks within a beat, different hands, same letter.
    events = sorted(
        [(n.onset, "RH", n) for n in rh_m if not n.grace]
        + [(n.onset, "LH", n) for n in lh_m if not n.grace],
        key=lambda e: e[0],
    )
    for i, (t0, h0, n0) in enumerate(events):
        for t1, h1, n1 in events[i + 1 :]:
            if t1 - t0 > 1:
                break
            if h1 == h0 or t1 == t0 or n0.end > t1:  # simultaneous ones are handled above
                continue
            l0, a0 = _letter_alter(n0.name or "")
            l1, a1 = _letter_alter(n1.name or "")
            if l0 == l1 and a0 != a1 and (t1, l1) not in seen:
                seen.add((t1, l1))
                out.append(
                    Finding(
                        "chromatic-clash",
                        "low",
                        n1.measure,
                        t1,
                        f"cross relation: {h0} {n0.name} then {h1} {n1.name}",
                    )
                )
    return out


def line_of(notes: list[Note], top: bool) -> list[tuple[int, Fraction]]:
    """Melody (top note per attack) or bass (bottom note) as (MIDI, inter-onset time) pairs."""
    att = _attacks(merge_ties(notes))
    pitches = [(g[-1] if top else g[0]).midi or 0 for _, g in att]
    times = [t for t, _ in att]
    iois = [b - a for a, b in itertools.pairwise(times)] + [Fraction(0)]
    return list(zip(pitches, iois, strict=True))


def longest_shared_run(a: list[tuple[int, Fraction]], b: list[tuple[int, Fraction]]) -> int:
    """Longest run of consecutive notes whose intervals and rhythm match (in notes)."""

    def steps(line: list[tuple[int, Fraction]]) -> list[tuple[int, Fraction]]:
        return [(q[0] - p[0], p[1]) for p, q in itertools.pairwise(line)]

    sa, sb = steps(a), steps(b)
    best = 0
    prev = [0] * (len(sb) + 1)
    for x in sa:
        cur = [0] * (len(sb) + 1)
        for j, y in enumerate(sb, 1):
            if x == y:
                cur[j] = prev[j - 1] + 1
                best = max(best, cur[j])
        prev = cur
    return best + 1 if best else 0


Line = list[tuple[int, Fraction]]


def step_ngrams(line: Line, n: int = COPY_N) -> set[tuple[tuple[int, Fraction], ...]]:
    """Transposition-invariant n-grams of (interval, inter-onset time) steps."""
    steps = [(q[0] - p[0], p[1]) for p, q in itertools.pairwise(line)]
    return {tuple(steps[i : i + n]) for i in range(len(steps) - n + 1)}


def background_ngrams(scores: list[KernScore]) -> dict[str, set]:
    """Melody and bass n-grams of a reference corpus (e.g. the composer's other pieces).

    Shared runs that also occur here are common figuration (scales, Alberti bass), not copying.
    """
    bg: dict[str, set] = {"melody": set(), "bass": set()}
    for sc in scores:
        split = hands(sc.notes)
        if split is None:
            continue
        bg["melody"] |= step_ngrams(line_of(split[0], True))
        bg["bass"] |= step_ngrams(line_of(split[1], False))
    return bg


def check_copying(
    score: KernScore,
    excerpts: dict[str, KernScore],
    background: dict[str, set] | None = None,
) -> list[Finding]:
    """Flag melody/bass runs of COPY_N+1 notes shared with an excerpt.

    With a background corpus, only runs absent from it count ("distinctive"), and those are
    flagged high. Without one, any shared run is reported as medium: it may be generic.
    """
    split = hands(score.notes)
    if split is None:
        return []
    out = []
    for name, ex in excerpts.items():
        ex_split = hands(ex.notes)
        if ex_split is None:
            continue
        for label, top, mine, theirs in (
            ("melody", True, split[0], ex_split[0]),
            ("bass", False, split[1], ex_split[1]),
        ):
            a, b = line_of(mine, top), line_of(theirs, top)
            shared = step_ngrams(a) & step_ngrams(b)
            if not shared:
                continue
            run = longest_shared_run(a, b)
            if background is None:
                out.append(
                    Finding(
                        "copy",
                        "medium",
                        None,
                        Fraction(0),
                        f"{label} shares a {run}-note run with {name} (no background "
                        "corpus given, so this may be generic figuration)",
                    )
                )
                continue
            distinctive = shared - background[label]
            if distinctive:
                # Calibrated on 002 arm A (never saw the excerpts): chance overlap there was at
                # most 1 distinctive run and 9-note runs, so only more than that is flagged high.
                strong = len(distinctive) >= COPY_STRONG_RUNS or run >= COPY_STRONG_LEN
                out.append(
                    Finding(
                        "copy",
                        "high" if strong else "low",
                        None,
                        Fraction(0),
                        f"{label} shares {len(distinctive)} distinctive {COPY_N + 1}-note "
                        f"runs with {name} that its background corpus doesn't contain "
                        f"(longest shared run {run} notes)",
                    )
                )
    return out


def check_score(
    score: KernScore,
    excerpts: dict[str, KernScore] | None = None,
    background: dict[str, set] | None = None,
) -> list[Finding]:
    split = hands(score.notes)
    if split is None:
        return [Finding("layout", "high", None, Fraction(0), "not a two-staff piano score")]
    rh, lh = split
    findings = (
        check_hand_spans(rh, lh)
        + check_fast_leaps(rh, lh)
        + check_hand_crossing(rh, lh)
        + check_chromatic_clashes(rh, lh)
        + check_copying(score, excerpts or {}, background)
    )
    order = {"high": 0, "medium": 1, "low": 2}
    return sorted(findings, key=lambda f: (order[f.severity], f.onset))


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    ap.add_argument("paths", nargs="+", type=Path)
    ap.add_argument("--against", nargs="*", type=Path, default=[], help="excerpts for copy check")
    ap.add_argument(
        "--background",
        nargs="*",
        type=Path,
        default=[],
        help="files/dirs of the composer's other pieces: shared runs found there are generic",
    )
    ap.add_argument(
        "--exclude",
        nargs="*",
        default=[],
        help="background file names to leave out (the excerpts' source pieces)",
    )
    args = ap.parse_args(argv)
    excerpts = {p.name: parse_kern(p.read_text(encoding="utf-8")) for p in args.against}
    bg_files = [
        f
        for p in args.background
        for f in (sorted(p.rglob("*.krn")) if p.is_dir() else [p])
        if f.name not in set(args.exclude)
    ]
    background = (
        background_ngrams(
            [parse_kern(f.read_text(encoding="utf-8", errors="replace")) for f in bg_files]
        )
        if bg_files
        else None
    )
    worst = 0
    for p in args.paths:
        findings = check_score(parse_kern(p.read_text(encoding="utf-8")), excerpts, background)
        counts = {s: sum(f.severity == s for f in findings) for s in ("high", "medium", "low")}
        print(f"{p}: {counts['high']} high, {counts['medium']} medium, {counts['low']} low")
        for f in findings:
            print(f"  {f}")
        worst = max(worst, 1 if counts["high"] else 0)
    return worst


if __name__ == "__main__":
    sys.exit(main())
