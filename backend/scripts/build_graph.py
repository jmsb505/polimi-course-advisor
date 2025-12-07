from __future__ import annotations

from pathlib import Path

from backend.core.models import load_courses
from backend.core.graph import build_course_graph, save_graph_json, graph_stats, GraphBuildConfig


def main() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    data_dir = repo_root / "backend" / "data"
    courses_path = data_dir / "courses.json"
    graph_path = data_dir / "graph.json"

    print(f"[build_graph] Loading courses from: {courses_path}")
    courses = load_courses(courses_path)
    print(f"[build_graph] Total courses: {len(courses)}")

    config = GraphBuildConfig()
    print(
        "[build_graph] Using config: "
        f"w_group={config.w_group}, w_ssd={config.w_ssd}, "
        f"w_text={config.w_text}, text_sim_threshold={config.text_sim_threshold}, "
        f"min_edge_weight={config.min_edge_weight}"
    )

    graph = build_course_graph(courses, config=config)
    num_nodes, num_edges, avg_degree = graph_stats(graph)
    print(f"[build_graph] Graph nodes: {num_nodes}")
    print(f"[build_graph] Undirected edges: {num_edges}")
    print(f"[build_graph] Average degree: {avg_degree:.2f}")

    save_graph_json(graph, graph_path)
    print(f"[build_graph] Saved graph to: {graph_path}")


if __name__ == "__main__":
    main()
