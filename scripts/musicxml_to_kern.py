"""Convert MusicXML files to **kern, keeping only conversions verified against the source.

Two established converters are tried in turn: humlib's ``musicxml2hum`` (with repairs for its
known header bugs, ``music_ai.musicxml2hum_fix``), then converter21 (music21's Humdrum writer).
A result is kept only if every note (onset and pitch) matches music21's own reading of the source
(``music_ai.score_check``); otherwise the file is reported as rejected, with the differences.
Rejections are usually flaws in the source (overfull bars, mis-sized tuplets) or notation kern
spells differently (tremolos written out as notes).

humlib is built locally (gitignored); if it's missing, only converter21 is used:
    mkdir -p data/tools && cd data/tools && git clone --depth 1 https://github.com/craigsapp/humlib
    cd humlib && make library musicxml2hum

Usage:
    uv run scripts/musicxml_to_kern.py IN.musicxml|IN.mxl [...] --out DIR
"""

from __future__ import annotations

import argparse
import contextlib
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


def via_humlib(path: Path) -> str:
    with tempfile.NamedTemporaryFile(suffix=".musicxml") as tmp:
        tmp.write(read_musicxml(path))
        tmp.flush()
        out = subprocess.run([str(TOOL), tmp.name], capture_output=True, text=True, check=True)
    if not out.stdout.strip():
        raise ValueError("no output")
    return repair(out.stdout)


def via_converter21(score: music21.stream.Score) -> str:
    with tempfile.TemporaryDirectory() as d:
        dest = Path(d) / "out.krn"
        quiet = io.StringIO()  # it prints every measure it pads
        with contextlib.redirect_stdout(quiet), contextlib.redirect_stderr(quiet):
            score.write("humdrum", fp=dest)
        return dest.read_text(encoding="utf-8")


def convert(path: Path) -> tuple[str | None, str]:
    """(verified kern or None, report line)."""
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        score = music21.converter.parse(path, forceSource=True)
    expected = music21_events(score)
    tried = []
    attempts = [("converter21", lambda: via_converter21(score))]
    if TOOL.exists():
        attempts.insert(0, ("musicxml2hum", lambda: via_humlib(path)))
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
