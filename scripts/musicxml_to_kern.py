"""Convert MusicXML files to **kern with humlib's ``musicxml2hum``, repairing its known bugs
(``music_ai.musicxml2hum_fix``). Output is checked with ``music_ai.kern.parse_kern``.

humlib is built locally (gitignored):
    mkdir -p data/tools && cd data/tools && git clone --depth 1 https://github.com/craigsapp/humlib
    cd humlib && make library musicxml2hum

Usage:
    uv run scripts/musicxml_to_kern.py IN.musicxml [...] --out DIR
"""

from __future__ import annotations

import argparse
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path

from music_ai.kern import KernError, parse_kern
from music_ai.musicxml2hum_fix import repair

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


def convert(path: Path) -> str:
    with tempfile.NamedTemporaryFile(suffix=".musicxml") as tmp:
        tmp.write(read_musicxml(path))
        tmp.flush()
        out = subprocess.run([str(TOOL), tmp.name], capture_output=True, text=True, check=True)
    if not out.stdout.strip():
        raise ValueError(f"{path}: musicxml2hum produced no output")
    return repair(out.stdout)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("inputs", nargs="+", type=Path)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args(argv)
    if not TOOL.exists():
        print(f"missing {TOOL}; see the docstring to build it", file=sys.stderr)
        return 1
    args.out.mkdir(parents=True, exist_ok=True)
    failed = []
    for p in args.inputs:
        try:
            text = convert(p)
            ks = parse_kern(text)
        except (subprocess.CalledProcessError, ValueError, KernError) as e:
            print(f"{p.stem}: FAILED ({type(e).__name__}: {str(e).splitlines()[0][:100]})")
            failed.append(p.stem)
            continue
        bars = sum(not b.token.startswith("==") for b in ks.barlines)
        (args.out / f"{p.stem}.krn").write_text(text, encoding="utf-8")
        print(f"{p.stem}: {bars} bars, {len(ks.pitched())} notes, {len(ks.warnings)} warnings")
        for w in ks.warnings[:3]:
            print("  ", w)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
