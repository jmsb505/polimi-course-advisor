from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, TypedDict, Union

from .models import Course
from .text_utils import (
    tokens_from_name_and_description,
    jaccard_similarity,
)


# ---------- Types ----------

class NeighborJSON(TypedDict):
    code: str
    weight: float


# JSON-facing graph format:
# {
#   "088983": [{"code": "123456", "weight": 0.7}, ...],
#   "123456": [{"code": "088983", "weight": 0.7}, ...],
# }
GraphJSON = Dict[str, List[NeighborJSON]]

# Internal adjacency format for algorithms:
# {
#   "088983": {"123456": 0.7, "234567": 0.3},
#   ...
# }
GraphAdjacency = Dict[str, Dict[str, float]]


@dataclass
class GraphBuildConfig:
    w_group: float = 0.6
    w_ssd: float = 0.9
    w_text: float = 1.0
    text_sim_threshold: float = 0.18
    min_edge_weight: float = 0.2


# ---------- Conversion helpers ----------

def adjacency_to_json(graph: GraphAdjacency) -> GraphJSON:
    """
    Convert internal adjacency (dict-of-dicts) to JSON-friendly format.
    Neighbors are sorted by descending weight, then by code.
    """
    out: GraphJSON = {}
    for code, neighbors in graph.items():
        items = [
            NeighborJSON(code=n_code, weight=float(weight))
            for n_code, weight in neighbors.items()
        ]
        items.sort(key=lambda x: (-x["weight"], x["code"]))
        out[code] = items
    return out


def json_to_adjacency(graph_json: GraphJSON) -> GraphAdjacency:
    """
    Convert JSON-friendly graph to internal adjacency representation.
    """
    graph: GraphAdjacency = {}
    for code, neighbors in graph_json.items():
        inner: Dict[str, float] = {}
        for n in neighbors:
            n_code = str(n["code"])
            weight = float(n["weight"])
            if n_code == code:
                continue
            if weight <= 0:
                continue
            inner[n_code] = inner.get(n_code, 0.0) + weight
        graph[code] = inner
    return graph


# ---------- Persistence helpers ----------

def save_graph_json(graph: GraphAdjacency, path: Union[str, Path]) -> None:
    """
    Save adjacency dict to a JSON file in the project-standard format.
    """
    p = Path(path)
    graph_json = adjacency_to_json(graph)
    with p.open("w", encoding="utf-8") as f:
        json.dump(graph_json, f, indent=2, sort_keys=True)


def load_graph_json(path: Union[str, Path]) -> GraphAdjacency:
    """
    Load graph from JSON file into adjacency dict.
    """
    p = Path(path)
    with p.open("r", encoding="utf-8") as f:
        graph_json: GraphJSON = json.load(f)
    return json_to_adjacency(graph_json)


# ---------- Graph statistics ----------

def graph_stats(graph: GraphAdjacency) -> tuple[int, int, float]:
    """
    Return (num_nodes, num_undirected_edges, avg_degree).
    """
    num_nodes = len(graph)
    if num_nodes == 0:
        return 0, 0, 0.0

    total_directed_edges = sum(len(neighbors) for neighbors in graph.values())
    undirected_edges = total_directed_edges // 2
    avg_degree = total_directed_edges / num_nodes
    return num_nodes, undirected_edges, avg_degree


# ---------- Graph construction ----------

def _add_undirected_edge(
    graph: GraphAdjacency,
    code_a: str,
    code_b: str,
    weight: float,
) -> None:
    """
    Add or update an undirected edge between two course codes.
    """
    if code_a == code_b:
        return
    if weight <= 0:
        return

    if code_a not in graph:
        graph[code_a] = {}
    if code_b not in graph:
        graph[code_b] = {}

    graph[code_a][code_b] = graph[code_a].get(code_b, 0.0) + weight
    graph[code_b][code_a] = graph[code_b].get(code_a, 0.0) + weight


def build_course_graph(
    courses: List[Course],
    config: GraphBuildConfig | None = None,
) -> GraphAdjacency:
    """
    Build an undirected, weighted graph where each course is a node
    and edges have weights determined by:
        - same group
        - shared SSD
        - text similarity (name + description)
    """
    if config is None:
        config = GraphBuildConfig()

    # Initialize nodes so even courses with no edges appear in the graph
    graph: GraphAdjacency = {}
    for c in courses:
        if not c.code:
            continue
        graph.setdefault(c.code, {})

    # Precompute helpful views
    n = len(courses)
    tokens_map = {}
    group_map = {}
    ssd_map = {}

    for c in courses:
        if not c.code:
            continue
        tokens_map[c.code] = tokens_from_name_and_description(c.name, c.description)
        group_map[c.code] = (c.group or "").upper().strip()
        ssd_map[c.code] = set(s.strip() for s in c.ssd if s.strip())

    # Pairwise comparison (O(n^2), fine for a few dozen courses)
    for i in range(n):
        c_i = courses[i]
        code_i = c_i.code
        if not code_i:
            continue

        group_i = group_map.get(code_i, "")
        ssd_i = ssd_map.get(code_i, set())
        tokens_i = tokens_map.get(code_i, set())

        for j in range(i + 1, n):
            c_j = courses[j]
            code_j = c_j.code
            if not code_j:
                continue

            group_j = group_map.get(code_j, "")
            ssd_j = ssd_map.get(code_j, set())
            tokens_j = tokens_map.get(code_j, set())

            weight = 0.0

            # Same group
            if group_i and group_j and group_i == group_j:
                weight += config.w_group

            # Shared SSD
            if ssd_i and ssd_j and (ssd_i & ssd_j):
                weight += config.w_ssd

            # Text similarity
            sim = jaccard_similarity(tokens_i, tokens_j)
            if sim >= config.text_sim_threshold:
                weight += config.w_text * sim

            if weight >= config.min_edge_weight:
                _add_undirected_edge(graph, code_i, code_j, weight)

    return graph
