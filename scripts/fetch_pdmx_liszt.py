"""Extract selected Liszt piano scores from PDMX and convert them to **kern.

PDMX (Long et al., Zenodo record 15571083) is public-domain MusicXML from MuseScore user uploads,
so quality varies; only rows in its ``no_license_conflict`` subset are used, and the most-rated
upload of each piece is picked. Needs ``data/pdmx/PDMX.csv`` and ``data/pdmx/mxl.tar.gz``
(download from Zenodo; gitignored) and humlib's musicxml2hum (see scripts/musicxml_to_kern.py).

Output: data/liszt/mxl/<slug>.mxl and data/liszt/kern/<slug>.krn (gitignored).

Usage:
    uv run scripts/fetch_pdmx_liszt.py
"""

from __future__ import annotations

import csv
import subprocess
import sys
import tarfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PDMX = ROOT / "data" / "pdmx"
OUT = ROOT / "data" / "liszt"
PIECES = {  # slug: PDMX title (or its start) (the original song, where there is one, is in fetch_lieder.py)
    "liszt-standchen-s560-7": "Schubert/Liszt - Ständchen",
    "liszt-erlkonig-s558-4": "Erlkönig - F. Schubert arr. F. Liszt",
    "liszt-forelle-s564": "Schubert/Liszt - Die Forelle",
    "liszt-liebestraum-3-s541": "Franz Liszt: Liebestraum No.3 in A-flat major",
    "liszt-o-lieb-song-s298": "O lieb so lang du lieben kannst S.298 (Liszt Franz)",
    "liszt-consolation-1-s172": "Franz Liszt - Consolations I.",
    "liszt-consolation-4-s172": "Franz Liszt: Consolation No.4 in D-flat major",
    "liszt-benediction-s173-3": "Liszt Bénédiction de Dieu dans la solitude S. 173/3 (piano",
}


def select() -> dict[str, str]:
    """slug -> mxl path inside the archive (most-rated no-conflict row per title)."""
    best: dict[str, tuple[int, str]] = {}
    with open(PDMX / "PDMX.csv", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            title = (r.get("title") or "").strip()
            slug = next((s for s, t in PIECES.items() if title.startswith(t)), None)
            if slug is None or r.get("subset:no_license_conflict") != "True":
                continue
            n = int(r.get("n_ratings") or 0)
            if slug not in best or n > best[slug][0]:
                best[slug] = (n, (r["mxl"] or "").removeprefix("./"))
    missing = set(PIECES) - set(best)
    if missing:
        raise SystemExit(f"not found in PDMX (no-conflict subset): {sorted(missing)}")
    return {s: p for s, (_, p) in best.items()}


def main() -> int:
    paths = select()
    (OUT / "mxl").mkdir(parents=True, exist_ok=True)
    todo = {p: s for s, p in paths.items() if not (OUT / "mxl" / f"{s}.mxl").exists()}
    if todo:
        with tarfile.open(PDMX / "mxl.tar.gz", "r:gz") as tar:
            for m in tar:
                name = m.name.removeprefix("./")
                if name in todo and m.isfile():
                    f = tar.extractfile(m)
                    assert f is not None
                    (OUT / "mxl" / f"{todo.pop(name)}.mxl").write_bytes(f.read())
                    if not todo:
                        break
    if todo:
        raise SystemExit(f"not found in mxl.tar.gz: {sorted(todo.values())}")
    mxl = sorted((OUT / "mxl").glob("*.mxl"))
    cmd = ["uv", "run", "scripts/musicxml_to_kern.py", *map(str, mxl), "--out", str(OUT / "kern")]
    return subprocess.run(cmd, cwd=ROOT, check=False).returncode


if __name__ == "__main__":
    sys.exit(main())
