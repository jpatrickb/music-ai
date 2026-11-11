"""Convert MusicXML files to **kern, keeping only conversions verified against the source.

Steps, per file:
1. Restore exact note lengths where the exporter rounded tuplets to whole ticks
   (``music_ai.musicxml_ticks``); the notation itself is unchanged.
2. Read the result with music21, dropping only pedal marks whose start or end note music21
   couldn't place (they crash converter21 and don't affect which notes sound).
3. Convert with humlib's ``musicxml2hum`` (with repairs for its known header bugs,
   ``music_ai.musicxml2hum_fix``). If that fails the check, convert with converter21 after
   ``music_ai.score_prep``: overlapping rests dropped, bars longer or shorter than their time
   signature (free cadenzas) given a local one, voice gaps filled with hidden rests. If
   converter21 crashes on a mark (pedal, hairpin) that ends on a rest, retry with such marks
   moved to the nearest note.
4. Keep a result only if every sounding note (onset and pitch; tied pieces, or attacks) matches
   music21's reading (``music_ai.score_check``); otherwise report the file as rejected, with the
   differences. Nothing unverified is written.

humlib is built locally (gitignored); if it's missing, only converter21 is used:
    mkdir -p data/tools && cd data/tools && git clone --depth 1 https://github.com/craigsapp/humlib
    cd humlib && make library musicxml2hum

Usage:
    uv run scripts/musicxml_to_kern.py IN.musicxml|IN.mxl [...] --out DIR
"""

from __future__ import annotations

import argparse
import contextlib
import copy
import io
import subprocess
import sys
import tempfile
import warnings
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path

import converter21
import music21

from music_ai.kern import KernError
from music_ai.musicxml2hum_fix import repair
from music_ai.musicxml_ticks import restore
from music_ai.score_check import Match, compare, music21_events
from music_ai.score_prep import (
    drop_orphan_pedals,
    drop_overlapping_rests,
    fill_voice_gaps,
    mark_irregular_bars,
    move_spanner_ends_off_rests,
)

ROOT = Path(__file__).resolve().parents[1]
TOOL = ROOT / "data" / "tools" / "humlib" / "bin" / "musicxml2hum"


def read_musicxml(path: Path) -> bytes:
    """The score XML, unzipping a compressed ``.mxl`` (its container.xml names the score file)."""
    if path.suffix.lower() != ".mxl":
        return path.read_bytes()
    with zipfile.ZipFile(path) as z:
        container = ET.fromstring(z.read("META-INF/container.xml"))
        root = next(e for e in container.iter() if e.tag.endswith("rootfile"))
        return z.read(root.attrib["full-path"])


def exact_musicxml(path: Path) -> tuple[bytes, int]:
    """The score with rounded tuplet lengths restored, and how many notes that changed."""
    root = ET.fromstring(read_musicxml(path))
    n = restore(root)
    return ET.tostring(root, encoding="utf-8", xml_declaration=True), n


def via_humlib(xml_path: Path) -> str:
    out = subprocess.run([str(TOOL), str(xml_path)], capture_output=True, text=True, check=True)
    if not out.stdout.strip():
        raise ValueError("no output")
    return repair(out.stdout)


def via_converter21(score: music21.stream.Score, rest_spanners: bool = False) -> str:
    score = copy.deepcopy(score)
    if rest_spanners:
        move_spanner_ends_off_rests(score)
    drop_overlapping_rests(score)
    mark_irregular_bars(score)
    fill_voice_gaps(score)
    with tempfile.TemporaryDirectory() as d:
        dest = Path(d) / "out.krn"
        quiet = io.StringIO()  # it prints every measure it pads
        with contextlib.redirect_stdout(quiet), contextlib.redirect_stderr(quiet):
            score.write("humdrum", fp=dest)
        return dest.read_text(encoding="utf-8")


def convert(path: Path) -> tuple[str | None, str]:
    """(verified kern or None, report line)."""
    xml, restored = exact_musicxml(path)
    with tempfile.TemporaryDirectory() as d:
        xml_path = Path(d) / "score.musicxml"
        xml_path.write_bytes(xml)
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            score = music21.converter.parse(xml_path, forceSource=True)
        pedals = drop_orphan_pedals(score)
        expected = music21_events(score)
        notes = [f"{restored} rounded lengths restored"] if restored else []
        notes += [f"{pedals} broken pedal marks dropped"] if pedals else []
        text, report = _attempt(xml_path, score, expected)
    if notes:
        report += " [" + "; ".join(notes) + "]"
    return text, report


def _attempt(xml_path: Path, score: music21.stream.Score, expected) -> tuple[str | None, str]:
    tried = []
    attempts = [
        ("converter21", lambda: via_converter21(score)),
        ("converter21, marks moved off rests", lambda: via_converter21(score, rest_spanners=True)),
    ]
    if TOOL.exists():
        attempts.insert(0, ("musicxml2hum", lambda: via_humlib(xml_path)))
    for name, run in attempts:
        try:
            text = run()
            m: Match = compare(expected, text)
        except (subprocess.CalledProcessError, ValueError, KernError, Exception) as e:  # noqa: BLE001
            tried.append(f"{name}: failed ({type(e).__name__})")
            continue
        if m.ok:
            note = f"; {m.detail}" if m.detail else ""
            return text, f"verified via {name} ({m.expected} notes{note})"
        tried.append(f"{name}: {m.got} notes vs {m.expected}; {m.detail}")
    return None, "REJECTED\n    " + "\n    ".join(tried)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("inputs", nargs="+", type=Path)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args(argv)
    converter21.register()
    args.out.mkdir(parents=True, exist_ok=True)
    rejected = 0
    for p in args.inputs:
        text, report = convert(p)
        dest = args.out / f"{p.stem}.krn"
        if text is None:
            rejected += 1
            dest.unlink(missing_ok=True)  # never leave an unverified file behind
        else:
            dest.write_text(text, encoding="utf-8")
        print(f"{p.stem}: {report}")
    return 1 if rejected else 0


if __name__ == "__main__":
    sys.exit(main())
