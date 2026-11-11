"""Convert MusicXML files to **kern, keeping only conversions verified against the source.

Steps, per file:
1. Restore exact note lengths where the exporter rounded tuplets to whole ticks
   (``music_ai.musicxml_ticks``); the notation itself is unchanged.
2. Read the result with music21, dropping only pedal marks whose start or end note music21
   couldn't place (they crash converter21 and don't affect which notes sound).
3. Convert with humlib's ``musicxml2hum`` (with repairs for its known header bugs,
   ``music_ai.musicxml2hum_fix``), then, if that fails the check, converter21.
4. Keep a result only if every sounding note (onset and pitch, ties merged) matches music21's
   reading (``music_ai.score_check``); otherwise report the file as rejected, with differences.

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


def drop_orphan_pedals(score: music21.stream.Score) -> int:
    dropped = 0
    for sp in list(score.recurse().getElementsByClass(music21.spanner.Spanner)):
        if type(sp).__name__ != "PedalMark":
            continue
        try:
            for el in sp.getSpannedElements():
                el.getOffsetInHierarchy(score)
        except music21.sites.SitesException:
            sp.activeSite.remove(sp)
            dropped += 1
    return dropped


def via_humlib(xml_path: Path) -> str:
    out = subprocess.run([str(TOOL), str(xml_path)], capture_output=True, text=True, check=True)
    if not out.stdout.strip():
        raise ValueError("no output")
    return repair(out.stdout)


def fill_voice_gaps(score: music21.stream.Score) -> None:
    """Hidden rests where an extra voice starts partway into a bar (a deleted rest in MuseScore),
    which converters otherwise misplace. Rests don't sound, so the check is unaffected."""
    for m in score.recurse().getElementsByClass("Measure"):
        for v in m.voices:
            v.makeRests(fillGaps=True, inPlace=True, hideRests=True, timeRangeFromBarDuration=True)


def via_converter21(score: music21.stream.Score) -> str:
    score = copy.deepcopy(score)
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
    attempts = [("converter21", lambda: via_converter21(score))]
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
