"""Render `**kern` samples to a PDF score, an MP3, and a PNG preview of page 1, so they can be
read and heard on GitHub without any music software.

Beams are added first (music_ai.kern_beam), as on the judging pages; notes are unchanged.
Verovio engraves the SVG pages and the MIDI; two external tools finish the job:

- `rsvg-convert` (librsvg, `brew install librsvg`): SVG pages -> one PDF, page 1 -> PNG
- MuseScore 4's `mscore` CLI: MIDI -> MP3 (default piano sound)

Writes `<name>.pdf`, `<name>.mp3` and `<name>-p1.png` into the experiment's `renders/` folder
(or `--out`), where `<name>` keeps the arm folder, e.g. `samples/B/T1-1.krn` -> `B-T1-1`.

Usage:
    uv run scripts/render_scores.py experiments/003-gen-hymn-arrangements/samples/H4-2.krn
"""

from __future__ import annotations

import argparse
import base64
import shutil
import subprocess
import tempfile
from pathlib import Path

import verovio

from music_ai.kern_beam import add_beams

MSCORE_CANDIDATES = [
    "mscore",
    "/Applications/MuseScore 4.app/Contents/MacOS/mscore",
]

# Letter-ish pages at a readable size; Verovio units are tenths of a mm.
VEROVIO_OPTIONS = {
    "inputFrom": "humdrum",
    "pageWidth": 2159,
    "pageHeight": 2794,
    "pageMarginTop": 100,
    "pageMarginBottom": 100,
    "pageMarginLeft": 100,
    "pageMarginRight": 100,
    "scale": 40,
    "footer": "none",
}


def find_tool(candidates: list[str]) -> str:
    for c in candidates:
        path = shutil.which(c) or (c if Path(c).exists() else None)
        if path:
            return path
    raise SystemExit(f"not found: {candidates[0]}")


def experiment_dir(sample: Path) -> Path:
    """The `experiments/NNN-slug/` folder a sample lives under."""
    for parent in sample.resolve().parents:
        if parent.parent.name == "experiments":
            return parent
    raise SystemExit(f"{sample} is not under experiments/NNN-slug/")


def output_stem(sample: Path) -> str:
    """`samples/B/T1-1.krn` -> `B-T1-1`; `samples/H4-2.krn` -> `H4-2` (keeps the arm in the name)."""
    parent = sample.parent.name
    return sample.stem if parent == "samples" else f"{parent}-{sample.stem}"


def render(sample: Path, out_dir: Path, rsvg: str, mscore: str) -> list[Path]:
    verovio.enableLog(verovio.LOG_WARNING)
    tk = verovio.toolkit()
    tk.setOptions(VEROVIO_OPTIONS)
    if not tk.loadData(add_beams(sample.read_text())):
        raise SystemExit(f"verovio could not load {sample}")

    out_dir.mkdir(parents=True, exist_ok=True)
    stem = output_stem(sample)
    pdf, mp3, png = (out_dir / f"{stem}.pdf", out_dir / f"{stem}.mp3", out_dir / f"{stem}-p1.png")

    with tempfile.TemporaryDirectory() as tmp:
        pages = []
        for n in range(1, tk.getPageCount() + 1):
            page = Path(tmp) / f"page{n:02d}.svg"
            page.write_text(tk.renderToSVG(n))
            pages.append(page)
        subprocess.run([rsvg, "-f", "pdf", "-o", str(pdf), *map(str, pages)], check=True)
        subprocess.run(
            [rsvg, "-f", "png", "-w", "1200", "-b", "white", "-o", str(png), str(pages[0])],
            check=True,
        )

        midi = Path(tmp) / f"{stem}.mid"
        midi.write_bytes(base64.b64decode(tk.renderToMIDI()))
        subprocess.run([mscore, "-o", str(mp3), str(midi)], check=True, capture_output=True)

    return [pdf, mp3, png]


def main() -> None:
    ap = argparse.ArgumentParser(description="Render kern samples to PDF, MP3 and a PNG preview.")
    ap.add_argument("samples", nargs="+", type=Path, help="kern files under experiments/")
    ap.add_argument("--out", type=Path, help="output folder (default: <experiment>/renders/)")
    args = ap.parse_args()

    rsvg = find_tool(["rsvg-convert"])
    mscore = find_tool(MSCORE_CANDIDATES)
    for sample in args.samples:
        out_dir = args.out or experiment_dir(sample) / "renders"
        for path in render(sample, out_dir, rsvg, mscore):
            print(path)


if __name__ == "__main__":
    main()
