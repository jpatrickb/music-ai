"""Run the notation validator over the downloaded **kern corpus and summarize per collection.

Reads data/kern/manifest.json (from scripts/fetch_kern_corpus.py), validates every .krn file
with music_ai.validate_notation in parallel, and writes per-file results to
outputs/corpus/validation.jsonl plus a per-collection summary table on stdout.

Usage:
    uv run scripts/corpus_report.py                 # all collections
    uv run scripts/corpus_report.py joplin -j 4
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from collections import Counter, defaultdict
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

from music_ai import validate_notation as vn

DATA = ROOT / "data" / "kern"
OUT = ROOT / "outputs" / "corpus"


def first_kind(msg: str) -> str:
    """Bucket an error message for the summary: drop the location, mask the numbers."""
    body = msg.split(": ", 1)[-1] if msg.startswith(("spine", "voice", "bar")) else msg
    return re.sub(r"\d+(\.\d+)?(/\d+)?", "N", body)[:60]


def check_file(collection: str, path: str) -> dict:
    text = Path(path).read_text(encoding="utf-8", errors="replace")
    score = vn.Score("kern", text, path)
    try:
        r = vn.validate(score, None, 0)
        errors, warnings = r.errors, r.warnings
    except Exception as e:  # noqa: BLE001 -- a parser crash is itself a finding
        errors, warnings = [f"validator crashed: {type(e).__name__}: {e}"], []
    return {
        "collection": collection,
        "file": str(Path(path).relative_to(DATA)),
        "ok": not errors,
        "errors": errors,
        "warnings": warnings,
    }


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    ap.add_argument("names", nargs="*", help="collection names (default: all in manifest)")
    ap.add_argument("-j", "--jobs", type=int, default=max(1, (os.cpu_count() or 2) - 2))
    args = ap.parse_args(argv)

    manifest = json.loads((DATA / "manifest.json").read_text())
    names = args.names or list(manifest)
    jobs = [(n, str(p)) for n in names for p in sorted((DATA / n).rglob("*.krn"))]
    OUT.mkdir(parents=True, exist_ok=True)

    results: list[dict] = []
    with ProcessPoolExecutor(args.jobs) as pool:
        futures = [pool.submit(check_file, n, p) for n, p in jobs]
        for i, f in enumerate(as_completed(futures), 1):
            results.append(f.result())
            if i % 100 == 0:
                print(f"  {i}/{len(jobs)}", file=sys.stderr)

    results.sort(key=lambda r: (r["collection"], r["file"]))
    with (OUT / "validation.jsonl").open("w") as fh:
        for r in results:
            fh.write(json.dumps(r) + "\n")

    by_coll: dict[str, list[dict]] = defaultdict(list)
    for r in results:
        by_coll[r["collection"]].append(r)
    print(f"{'collection':20} {'files':>5} {'pass':>5}  top error kinds")
    total_ok = 0
    for n in names:
        rs = by_coll[n]
        ok = sum(r["ok"] for r in rs)
        total_ok += ok
        kinds = Counter(first_kind(e) for r in rs for e in r["errors"]).most_common(3)
        print(f"{n:20} {len(rs):5} {ok:5}  " + "; ".join(f"{k} ×{c}" for k, c in kinds))
    print(f"\n{total_ok}/{len(results)} files passed; details in {OUT / 'validation.jsonl'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
