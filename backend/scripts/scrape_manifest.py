"""
Phase 1 scraper for the CSE T2I Manifesto (AY 2025/26).

For now this is just a skeleton that sets up CLI args and the output path.
The actual scraping logic will be filled in later steps.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


# Manifest URL for CSE (542), track T2I, AY 2025/26, all semesters, EN.
MANIFEST_URL = (
    "https://onlineservices.polimi.it/manifesti/manifesti/controller/"
    "ManifestoPublic.do?evn_default=EVENTO&aa=2025&k_cf=225&k_corso_la=542"
    "&ac_ins=0&k_indir=T2I&lang=EN&tipoCorso=ALL_TIPO_CORSO&semestre=ALL_SEMESTRI"
    "&sede=ALL_SEDI"
)


def default_output_path() -> Path:
    """
    Default JSON output: backend/data/courses.json (relative to repo root).
    """
    # This file: backend/scripts/scrape_manifest.py
    scripts_dir = Path(__file__).resolve().parent
    backend_dir = scripts_dir.parent
    data_dir = backend_dir / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir / "courses.json"


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Scrape Polimi Manifesto for CSE T2I first-semester courses."
    )

    parser.add_argument(
        "--output",
        type=Path,
        default=default_output_path(),
        help="Path to the JSON file to write (default: backend/data/courses.json).",
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Do not hit the network, just print what would be done.",
    )

    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)

    print("[scrape_manifest] Target manifest URL:")
    print(f"  {MANIFEST_URL}")
    print(f"[scrape_manifest] Output JSON will be written to: {args.output}")

    if args.dry_run:
        print("[scrape_manifest] Dry run: no HTTP requests, no JSON written yet.")
        return 0

    # Actual scraping logic will be implemented in later steps.
    print(
        "[scrape_manifest] Scraper is not implemented yet. "
        "Run again after Phase 1 steps 2–4."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
