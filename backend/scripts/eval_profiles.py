from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, List

# Add repo root to sys.path to allow imports from backend
repo_root = Path(__file__).resolve().parents[2]
if str(repo_root) not in sys.path:
    sys.path.append(str(repo_root))

from backend.core.models import load_courses
from backend.core.graph import build_course_graph
from backend.core.ranking import rank_courses


def generate_markdown_report(results: List[Dict[str, Any]], top_k: int) -> str:
    md = "# Course Advisor Evaluation Report\n\n"
    md += f"Generated on: {Path(__file__).name}\n"
    md += f"Parameters: top_k={top_k}\n\n"

    for res in results:
        name = res["scenario"]
        profile = res["profile"]
        recommendations = res["recommendations"]

        md += f"## Scenario: {name}\n"
        md += "**Profile Summary:**\n"
        md += f"- **Interests:** {', '.join(profile.get('interests', [])) or 'None'}\n"
        md += f"- **Goals:** {', '.join(profile.get('goals', [])) or 'None'}\n"
        md += f"- **Avoid:** {', '.join(profile.get('avoid', [])) or 'None'}\n"
        md += f"- **Lang Pref:** {profile.get('language_preference', 'ANY')}\n\n"

        md += "| # | Code | Name | Group | Lang | Score | Why? |\n"
        md += "|---|------|------|-------|------|-------|------|\n"

        for idx, rec in enumerate(recommendations, start=1):
            tags = [k for k, v in rec["reason_tags"].items() if v]
            tags_str = ", ".join(tags) if tags else "-"
            md += (
                f"| {idx} | {rec['code']} | {rec['name']} | {rec['group']} | "
                f"{rec['language']} | {rec['score']:.4f} | {tags_str} |\n"
            )
        
        md += "\n---\n\n"

    return md


def main() -> None:
    parser = argparse.ArgumentParser(description="Run evaluation on predefined student profiles.")
    parser.add_argument("--top-k", type=int, default=8, help="Number of recommendations per profile.")
    parser.add_argument("--input", type=str, default=str(repo_root / "backend" / "data" / "eval_profiles.json"), help="Path to input profiles JSON.")
    parser.add_argument("--out-dir", type=str, default=str(repo_root / "backend" / "reports"), help="Directory to save reports.")
    args = parser.parse_args()

    input_path = Path(args.input)
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    # 1. Load data
    courses_path = repo_root / "backend" / "data" / "courses.json"
    if not courses_path.exists():
        print(f"Error: courses.json not found at {courses_path}")
        sys.exit(1)

    print(f"Loading courses and building graph...")
    courses = load_courses(courses_path)
    graph = build_course_graph(courses)
    print(f"Loaded {len(courses)} courses and built graph.")

    # 2. Load profiles
    if not input_path.exists():
        print(f"Error: Input profiles not found at {input_path}")
        sys.exit(2)

    with open(input_path, "r", encoding="utf-8") as f:
        scenarios = json.load(f)

    # 3. Run evaluation
    all_results = []
    print(f"Running evaluation for {len(scenarios)} scenarios...")

    for scene in scenarios:
        name = scene["name"]
        profile = scene["profile"]
        
        print(f"  - Ranking for: {name}")
        ranked = rank_courses(courses, graph, profile, top_k=args.top_k)
        
        all_results.append({
            "scenario": name,
            "profile": profile,
            "recommendations": ranked
        })

    # 4. Save reports
    json_out = out_dir / "eval_report.json"
    with open(json_out, "w", encoding="utf-8") as f:
        json.dump(all_results, f, indent=2, ensure_ascii=False)

    md_out = out_dir / "eval_report.md"
    md_content = generate_markdown_report(all_results, args.top_k)
    with open(md_out, "w", encoding="utf-8") as f:
        f.write(md_content)

    print(f"\nEvaluation complete!")
    print(f"JSON Report: {json_out}")
    print(f"Markdown Report: {md_out}")


if __name__ == "__main__":
    main()
