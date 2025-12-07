from __future__ import annotations

from pathlib import Path

from backend.core.models import load_courses
from backend.core.graph import load_graph_json
from backend.core.pagerank import global_pagerank


def main() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    data_dir = repo_root / "backend" / "data"
    courses_path = data_dir / "courses.json"
    graph_path = data_dir / "graph.json"

    print(f"[test_pagerank] Loading courses from: {courses_path}")
    courses = load_courses(courses_path)
    code_to_course = {c.code: c for c in courses}

    print(f"[test_pagerank] Loading graph from: {graph_path}")
    graph = load_graph_json(graph_path)
    print(f"[test_pagerank] Nodes in graph: {len(graph)}")

    scores = global_pagerank(graph)
    print(f"[test_pagerank] Computed PageRank scores for {len(scores)} nodes")

    # Sort by score descending, then code
    top = sorted(scores.items(), key=lambda kv: (-kv[1], kv[0]))[:10]

    print("[test_pagerank] Top courses by global PageRank:")
    for rank, (code, score) in enumerate(top, start=1):
        course = code_to_course.get(code)
        name = course.name if course else "UNKNOWN"
        group = course.group if course else "UNKNOWN"
        lang = course.language if course else "UNKNOWN"
        print(f"  {rank:2d}. {code} | {name} | group={group} | lang={lang} | score={score:.5f}")


if __name__ == "__main__":
    main()
