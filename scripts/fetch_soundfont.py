"""Download the Salamander Grand Piano SoundFont (a sampled Yamaha C5, 16 velocity layers) used by
`scripts/render_scores.py` for audio.

Salamander Grand Piano by Alexander Holm, CC BY 3.0; SF2 version assembled by the FreePats
project (https://freepats.zenvoid.org/Piano/acoustic-grand-piano.html). About 310 MB to download
and 1.2 GB unpacked, into `data/soundfonts/salamander/` (gitignored).

Usage:
    uv run scripts/fetch_soundfont.py
"""

from __future__ import annotations

import tarfile
import tempfile
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
URL = (
    "https://freepats.zenvoid.org/Piano/SalamanderGrandPiano/"
    "SalamanderGrandPiano-SF2-V3+20200602.tar.xz"
)
DEST = ROOT / "data" / "soundfonts" / "salamander"
SF2 = DEST / "SalamanderGrandPiano-SF2-V3+20200602" / "SalamanderGrandPiano-V3+20200602.sf2"


def main() -> None:
    if SF2.exists():
        print(f"already present: {SF2}")
        return
    DEST.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        archive = Path(tmp) / "salamander.tar.xz"
        print(f"downloading {URL}")
        urllib.request.urlretrieve(URL, archive)
        with tarfile.open(archive) as tar:
            tar.extractall(DEST, filter="data")  # untrusted archive: no links out, no devices
    print(SF2)


if __name__ == "__main__":
    main()
