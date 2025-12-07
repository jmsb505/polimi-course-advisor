from __future__ import annotations

from pathlib import Path

from backend.core.models import load_courses, StudentProfile
from backend.core.graph import load_graph_json
from backend.core.ranking import rank_courses


def main() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    data_dir = repo_root / "backend" / "data"
    courses_path = data_dir / "courses.json"
    graph_path = data_dir / "graph.json"

    print(f"[test_ranking] Loading courses from: {courses_path}")
    courses = load_courses(courses_path)
    print(f"[test_ranking] Loaded {len(courses)} courses")

    print(f"[test_ranking] Loading graph from: {graph_path}")
    graph = load_graph_json(graph_path)
    print(f"[test_ranking] Graph nodes: {len(graph)}")

    # Fake profile for Phase 2 testing
    profile: StudentProfile = {
        "interests": ["machine learning", "data science", "optimization"],
        "avoid": ["pure theory"],
        "goals": ["industry AI job"],
        "language_preference": "EN",
        "workload_tolerance": "medium",
        "liked_courses": [],      # e.g. ["088983"] to bias towards a known course
        "disliked_courses": [],
    }

    print(f"[test_ranking] Profile: {profile}")

    ranked = rank_courses(courses, graph, profile, top_k=10)
    print(f"[test_ranking] Got {len(ranked)} recommended courses")

    print("[test_ranking] Top recommendations:")
    for idx, rc in enumerate(ranked, start=1):
        tags = [k for k, v in rc["reason_tags"].items() if v]
        tags_str = ",".join(sorted(tags)) if tags else "-"
        print(
            f"  {idx:2d}. {rc['code']} | {rc['name']} | "
            f"group={rc['group']} | lang={rc['language']} | "
            f"cfu={rc['cfu']:.1f} | score={rc['score']:.5f} | tags={tags_str}"
        )


if __name__ == "__main__":
    main()
