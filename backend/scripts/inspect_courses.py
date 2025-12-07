"""
Quick inspector for backend/data/courses.json.

Usage:
  python backend/scripts/inspect_courses.py
  python backend/scripts/inspect_courses.py --path some/other.json
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, List, Dict


def default_courses_path() -> Path:
    scripts_dir = Path(__file__).resolve().parent
    backend_dir = scripts_dir.parent
    return backend_dir / "data" / "courses.json"


def parse_args(argv: List[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Inspect scraped courses.json.")
    parser.add_argument(
        "--path",
        type=Path,
        default=default_courses_path(),
        help="Path to courses JSON (default: backend/data/courses.json).",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=5,
        help="Number of sample courses to print (default: 5).",
    )
    return parser.parse_args(argv)


def load_courses(path: Path) -> List[Dict[str, Any]]:
    if not path.exists():
        raise FileNotFoundError(f"Courses JSON not found at {path}")
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, list):
        raise ValueError("courses.json is not a list of course objects")
    return data


def main(argv: List[str] | None = None) -> int:
    args = parse_args(argv)

    print(f"[inspect_courses] Loading courses from: {args.path}")
    courses = load_courses(args.path)
    n = len(courses)
    print(f"[inspect_courses] Total courses: {n}")

    semesters = sorted({c.get("semester") for c in courses})
    print(f"[inspect_courses] Semesters present: {semesters}")

    non_sem1 = [c for c in courses if c.get("semester") != 1]
    print(f"[inspect_courses] Courses with semester != 1: {len(non_sem1)}")

    groups = sorted({(c.get("group") or "").strip() for c in courses})
    print(f"[inspect_courses] Groups ({len(groups)}): {', '.join(g for g in groups if g)}")

    languages = sorted({(c.get("language") or "").strip() for c in courses})
    print(f"[inspect_courses] Languages: {', '.join(languages)}")

    with_alpha = [c for c in courses if c.get("alpha_group_last")]
    without_alpha = [c for c in courses if not c.get("alpha_group_last")]
    print(f"[inspect_courses] alpha_group_last present: {len(with_alpha)}")
    print(f"[inspect_courses] alpha_group_last missing: {len(without_alpha)}")

    print()
    print(f"[inspect_courses] Sample of {min(args.limit, n)} courses:")
    for c in courses[: args.limit]:
        ag = c.get("alpha_group_last") or {}
        print(
            f"  {c.get('code')} | {c.get('name')} | group={c.get('group')} | "
            f"sem={c.get('semester')} | CFU={c.get('cfu')} | lang={c.get('language')}"
        )
        if ag:
            print(
                f"    alpha_group_last: from={ag.get('from')} to={ag.get('to')} "
                f"lecturer={ag.get('lecturer')}"
            )
        else:
            print("    alpha_group_last: None")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
