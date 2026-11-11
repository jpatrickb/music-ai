"""Fetch original songs from the OpenScore Lieder corpus (CC0) that Liszt transcribed for piano,
and convert them to **kern, for comparing an original melody with an arrangement of it.

Downloads go to data/lieder/mxl/ and kern to data/lieder/kern/ (both gitignored; the scores are
CC0, but they're study material, not project sources). Conversion needs humlib's musicxml2hum
(see scripts/musicxml_to_kern.py).

Usage:
    uv run scripts/fetch_lieder.py
"""

from __future__ import annotations

import subprocess
import sys
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "lieder"
BASE = "https://raw.githubusercontent.com/OpenScore/Lieder/main/"
SONGS = {  # slug: path in the OpenScore Lieder repo (Liszt's piano version in the comment)
    "schumann-widmung": "scores/Schumann,_Robert/Myrthen,_Op.25/01_Widmung/lc6885211.mxl",  # S.566
    "schubert-standchen-d957": (  # S.560/7
        "scores/Schubert,_Franz/Schwanengesang,_D.957/04_Ständchen/lc5004835.mxl"
    ),
    "schubert-erlkonig": "scores/Schubert,_Franz/_/Der_Erlkönig,_D.328/lc29062370.mxl",  # S.558/4
    "schubert-ave-maria": (  # S.558/12
        "scores/Schubert,_Franz/Op.52/6_Ellens_Gesang_III,_D.839_(Ave_Maria)/lc6389103.mxl"
    ),
}
# Not included yet: Liszt's song "Pace non trovo" S.270b (lc30065840; piano version S.161/5).
# Its conversion fails the note check: from about beat 94 notes land 1/3 beat early.


def main() -> int:
    (OUT / "mxl").mkdir(parents=True, exist_ok=True)
    for slug, path in SONGS.items():
        dest = OUT / "mxl" / f"{slug}.mxl"
        if not dest.exists():
            url = BASE + urllib.parse.quote(path)
            with urllib.request.urlopen(url, timeout=60) as r:
                dest.write_bytes(r.read())
        print(f"{slug}: {dest.stat().st_size // 1024} KB")
    mxl = sorted((OUT / "mxl").glob("*.mxl"))
    cmd = ["uv", "run", "scripts/musicxml_to_kern.py", *map(str, mxl), "--out", str(OUT / "kern")]
    return subprocess.run(cmd, cwd=ROOT, check=False).returncode


if __name__ == "__main__":
    sys.exit(main())
