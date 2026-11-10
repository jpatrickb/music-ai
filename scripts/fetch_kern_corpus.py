"""Download public **kern (Humdrum) score collections into data/kern/.

Each collection is a git repository, shallow-cloned and checked out at a pinned commit so the
corpus is reproducible. Run with no pins to fetch the latest commit, then copy the printed SHAs
into COLLECTIONS to freeze them. Writes data/kern/manifest.json (collection, repo, commit,
license file, number of .krn files).

The files are data only: nothing from the downloaded repositories is executed. They stay under
data/ (gitignored) because the encodings carry their own licenses; check each repo's license
before redistributing anything.

Usage:
    uv run scripts/fetch_kern_corpus.py              # all collections
    uv run scripts/fetch_kern_corpus.py chopin-preludes joplin
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from dataclasses import asdict, dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEST = ROOT / "data" / "kern"


@dataclass(frozen=True)
class Collection:
    name: str
    repo: str  # GitHub owner/name
    composer: str
    era: str
    commit: str | None = None  # pinned SHA; None = latest default branch


# Keyboard music only (song collections with melody-only parts are left out).
COLLECTIONS: list[Collection] = [
    Collection(
        "bach-370-chorales",
        "craigsapp/bach-370-chorales",
        "Bach",
        "baroque",
        "a95574f9e93b4d72a96cd390a059df4f8471ddb6",
    ),
    Collection(
        "bach-wtc",
        "humdrum-tools/bach-wtc",
        "Bach",
        "baroque",
        "0b4f4d84b90b254615e7ac09730ec473c9611cb6",
    ),
    Collection(
        "bach-inventions",
        "humdrum-tools/inventions",
        "Bach",
        "baroque",
        "93183f6fdb9ab7aa1fa601e3aa200b40763469cf",
    ),
    Collection(
        "scarlatti-sonatas",
        "craigsapp/scarlatti-keyboard-sonatas",
        "Scarlatti",
        "baroque",
        "567731b13020802a422bd5aa49347ee3dac3ea25",
    ),
    Collection(
        "haydn-sonatas",
        "craigsapp/haydn-piano-sonatas",
        "Haydn",
        "classical",
        "299abc8f11eed4982f9fcddf2fc519b7b50b6214",
    ),
    Collection(
        "mozart-sonatas",
        "craigsapp/mozart-piano-sonatas",
        "Mozart",
        "classical",
        "0f1f49d914494f8461709b2a2642153bb240c6da",
    ),
    Collection(
        "beethoven-sonatas",
        "craigsapp/beethoven-piano-sonatas",
        "Beethoven",
        "classical",
        "2d6627b8a2b085145b2be48e640fbb993771542b",
    ),
    Collection(
        "hummel-preludes",
        "craigsapp/hummel-preludes",
        "Hummel",
        "classical",
        "afdbebf863bc14b98d471ecca83adce22856520e",
    ),
    Collection(
        "chopin-preludes",
        "craigsapp/chopin-preludes",
        "Chopin",
        "romantic",
        "f8fb01f09d717e84929fb8b2950f96dd6bc05686",
    ),
    Collection(
        "chopin-mazurkas",
        "craigsapp/chopin-mazurkas",
        "Chopin",
        "romantic",
        "fc3a8fb6cba7fdad2183fee67853789bbfadb3a0",
    ),
    Collection(
        "scriabin",
        "craigsapp/scriabin",
        "Scriabin",
        "romantic",
        "7daa1136a4edfaf8d2bfadee973c33f3b76b6760",
    ),
    Collection(
        "joplin",
        "craigsapp/joplin",
        "Joplin",
        "ragtime",
        "ad0840eb97e89fac7e89a94325a3d7526b0dc200",
    ),
]

LICENSE_NAMES = ("LICENSE", "LICENSE.txt", "LICENSE.md", "COPYING", "license.txt")


def git(*args: str, cwd: Path | None = None) -> str:
    out = subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True, text=True)
    return out.stdout.strip()


def fetch(c: Collection) -> dict:
    path = DEST / c.name
    url = f"https://github.com/{c.repo}.git"
    if not (path / ".git").exists():
        path.mkdir(parents=True, exist_ok=True)
        git("init", "-q", cwd=path)
        git("remote", "add", "origin", url, cwd=path)
    ref = c.commit or "HEAD"
    git("fetch", "-q", "--depth", "1", "origin", ref, cwd=path)
    git("checkout", "-q", "--detach", "FETCH_HEAD", cwd=path)
    sha = git("rev-parse", "HEAD", cwd=path)
    if c.commit and sha != c.commit:
        raise RuntimeError(f"{c.name}: expected {c.commit}, got {sha}")
    lic = next((n for n in LICENSE_NAMES if (path / n).exists()), None)
    n_krn = sum(1 for _ in path.rglob("*.krn"))
    return {**asdict(c), "commit": sha, "license_file": lic, "krn_files": n_krn}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    ap.add_argument("names", nargs="*", help="collection names (default: all)")
    args = ap.parse_args(argv)
    known = {c.name: c for c in COLLECTIONS}
    unknown = [n for n in args.names if n not in known]
    if unknown:
        ap.error(f"unknown collections: {', '.join(unknown)}; known: {', '.join(known)}")
    chosen = [known[n] for n in args.names] if args.names else COLLECTIONS

    DEST.mkdir(parents=True, exist_ok=True)
    manifest_path = DEST / "manifest.json"
    manifest = json.loads(manifest_path.read_text()) if manifest_path.exists() else {}
    failed = 0
    for c in chosen:
        try:
            entry = fetch(c)
        except (subprocess.CalledProcessError, RuntimeError) as e:
            detail = e.stderr.strip() if isinstance(e, subprocess.CalledProcessError) else str(e)
            print(f"FAIL {c.name}: {detail}", file=sys.stderr)
            failed += 1
            continue
        manifest[c.name] = entry
        print(
            f"{c.name:20} {entry['commit'][:10]}  {entry['krn_files']:4} .krn  "
            f"license: {entry['license_file'] or '-'}"
        )
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
