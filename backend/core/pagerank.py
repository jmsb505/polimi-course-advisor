from __future__ import annotations

from typing import Dict, Optional

from .graph import GraphAdjacency


def _normalize_vector(vec: Dict[str, float]) -> Dict[str, float]:
    total = sum(vec.values())
    if total <= 0:
        return {k: 0.0 for k in vec}
    return {k: v / total for k, v in vec.items()}


def pagerank(
    graph: GraphAdjacency,
    damping: float = 0.85,
    tol: float = 1e-6,
    max_iter: int = 100,
    personalization: Optional[Dict[str, float]] = None,
) -> Dict[str, float]:
    """
    Generic PageRank on a weighted graph.

    - graph: adjacency dict {node: {neighbor: weight}}
    - damping: typical value 0.85
    - tol: stop when L1 diff between iterations is below this
    - personalization: if provided, a dict {node: raw_score} that will be
      normalized to a probability distribution and used as teleport vector.
      If None, use uniform teleport over all nodes.
    """
    if not graph:
        return {}

    nodes = sorted(graph.keys())
    n = len(nodes)

    # Outgoing weight (for normalization)
    out_weight: Dict[str, float] = {}
    for node in nodes:
        neigh = graph.get(node, {})
        out_weight[node] = float(sum(neigh.values()))

    # Teleport / personalization vector
    if personalization is not None:
        # Filter to known nodes, normalize later
        p = {node: float(personalization.get(node, 0.0)) for node in nodes}
        p = _normalize_vector(p)
        # If everything ended up zero, fall back to uniform
        if all(v == 0.0 for v in p.values()):
            p = {node: 1.0 / n for node in nodes}
    else:
        p = {node: 1.0 / n for node in nodes}

    # Initial rank: start from teleport distribution
    r = p.copy()

    for _ in range(max_iter):
        r_new = {node: 0.0 for node in nodes}

        # Teleportation part: every node gets (1 - d) * p_i
        for node in nodes:
            r_new[node] += (1.0 - damping) * p[node]

        # Distribute rank over edges
        dangling_mass = 0.0

        for node in nodes:
            rank = r[node]
            w_out = out_weight.get(node, 0.0)

            if w_out > 0.0:
                # Spread rank to neighbors proportionally to edge weights
                neighbors = graph.get(node, {})
                for nbr, w in neighbors.items():
                    if nbr not in r_new:
                        # In case of some weird asymmetry in graph keys
                        r_new[nbr] = 0.0
                    r_new[nbr] += damping * rank * (w / w_out)
            else:
                # Dangling node: accumulate for redistribution via p
                dangling_mass += rank

        if dangling_mass > 0.0:
            # Redistribute dangling mass according to teleport distribution
            for node in nodes:
                r_new[node] += damping * dangling_mass * p[node]

        # Check convergence
        diff = sum(abs(r_new[node] - r[node]) for node in nodes)
        r = r_new
        if diff < tol:
            break

    # Normalize once more for sanity
    return _normalize_vector(r)


def global_pagerank(
    graph: GraphAdjacency,
    damping: float = 0.85,
    tol: float = 1e-6,
    max_iter: int = 100,
) -> Dict[str, float]:
    """
    Convenience wrapper: uniform teleportation over all nodes.
    """
    return pagerank(
        graph=graph,
        damping=damping,
        tol=tol,
        max_iter=max_iter,
        personalization=None,
    )


def personalized_pagerank(
    graph: GraphAdjacency,
    personalization: Dict[str, float],
    damping: float = 0.85,
    tol: float = 1e-6,
    max_iter: int = 100,
) -> Dict[str, float]:
    """
    Convenience wrapper: teleportation according to a given personalization vector.
    """
    return pagerank(
        graph=graph,
        damping=damping,
        tol=tol,
        max_iter=max_iter,
        personalization=personalization,
    )
