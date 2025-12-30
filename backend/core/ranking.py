from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Set

from .models import Course, StudentProfile, RankedCourse
from .types import GraphView, GraphNode, GraphEdge, EdgeReason
from .graph import GraphAdjacency
from .pagerank import personalized_pagerank
from .text_utils import (
    tokens_from_name_and_description,
    tokens_from_phrase,
    jaccard_similarity,
)


@dataclass
class ProfileSignals:
    personalization: Dict[str, float]
    liked_courses: Set[str]
    liked_neighbors: Set[str]
    interest_matched: Set[str]


def _build_profile_signals(
    graph: GraphAdjacency,
    courses: List[Course],
    profile: StudentProfile,
    tokens_map: Dict[str, Set[str]],
) -> ProfileSignals:
    nodes = list(graph.keys())

    liked_raw = profile.get("liked_courses", []) or []
    liked_courses = {code for code in liked_raw if code in nodes}

    disliked_raw = profile.get("disliked_courses", []) or []
    disliked_courses = {code for code in disliked_raw if code in nodes}

    # Interests + goals as seeds
    interests = profile.get("interests", []) or []
    goals = profile.get("goals", []) or []
    interest_phrases = list(interests) + list(goals)
    interest_token_sets: List[Set[str]] = [
        tokens_from_phrase(p) for p in interest_phrases if p and p.strip()
    ]

    personalization: Dict[str, float] = {node: 0.0 for node in nodes}
    liked_neighbors: Set[str] = set()
    interest_matched: Set[str] = set()

    # Strong seeds: liked courses
    liked_course_weight = 3.0
    liked_neighbor_weight = 1.0

    for code in liked_courses:
        if code not in personalization:
            personalization[code] = 0.0
        personalization[code] += liked_course_weight

        for nbr, w in graph.get(code, {}).items():
            personalization[nbr] = personalization.get(nbr, 0.0) + liked_neighbor_weight * w
            liked_neighbors.add(nbr)

    # Interests/goals
    interest_weight = 20.0
    if interest_token_sets:
        for code in nodes:
            tokens = tokens_map.get(code, set())
            if not tokens:
                continue

            score = 0.0
            for q in interest_token_sets:
                if not q:
                    continue
                # Use intersection over query length (Query Coverage)
                # If the course has the interest keyword, score should be high (1.0),
                # regardless of how long the course description is.
                intersection_size = len(tokens & q)
                if intersection_size > 0:
                    sim = intersection_size / len(q)
                    score += sim

            if score > 0:
                personalization[code] = personalization.get(code, 0.0) + interest_weight * score
                interest_matched.add(code)

    # Disliked courses: zero out in personalization
    for code in disliked_courses:
        personalization[code] = 0.0

    return ProfileSignals(
        personalization=personalization,
        liked_courses=liked_courses,
        liked_neighbors=liked_neighbors,
        interest_matched=interest_matched,
    )


def _build_avoid_tokens(profile: StudentProfile) -> Set[str]:
    avoid_phrases = profile.get("avoid", []) or []
    result: Set[str] = set()
    for p in avoid_phrases:
        if not p or not p.strip():
            continue
        result |= tokens_from_phrase(p)
    return result


def rank_courses(
    courses: List[Course],
    graph: GraphAdjacency,
    profile: StudentProfile,
    top_k: int = 10,
) -> List[RankedCourse]:
    """
    Rank courses for a given student profile using personalized PageRank
    plus simple local bonuses/penalties.
    """
    if not courses or not graph:
        return []

    # Map codes to courses and tokens
    code_to_course: Dict[str, Course] = {
        c.code: c for c in courses if c.code
    }
    tokens_map: Dict[str, Set[str]] = {
        code: tokens_from_name_and_description(c.name, c.description)
        for code, c in code_to_course.items()
    }

    # Build personalization vector + signal sets
    signals = _build_profile_signals(graph, courses, profile, tokens_map)

    # Run personalized PageRank
    scores = personalized_pagerank(graph, personalization=signals.personalization)

    # Avoid tokens and language preference
    avoid_tokens = _build_avoid_tokens(profile)
    lang_pref = (profile.get("language_preference") or "ANY").upper().strip()
    disliked_set = set(profile.get("disliked_courses", []) or [])

    ranked: List[RankedCourse] = []

    for code, course in code_to_course.items():
        if code not in scores:
            continue

        # Hard filters
        if not course.description:
            # Skip courses with missing description (can be relaxed later)
            continue

        if lang_pref in {"EN", "IT"}:
            # Keep unknown language courses, but prefer exact matches later
            if course.language and course.language not in {lang_pref, "UNKNOWN"}:
                continue

        if code in disliked_set:
            # Hard skip disliked courses
            continue

        base_score = scores[code]
        if base_score <= 0.0:
            continue

        tokens = tokens_map.get(code, set())
        tags: Dict[str, bool] = {}
        final_score = base_score

        # Bonuses/penalties
        if code in signals.liked_courses:
            tags["liked_course"] = True
            final_score *= 1.20

        if code in signals.liked_neighbors and code not in signals.liked_courses:
            tags["liked_neighbor"] = True
            final_score *= 1.10

        if code in signals.interest_matched:
            tags["matched_interest"] = True
            final_score *= 2.0

        if lang_pref in {"EN", "IT"} and course.language == lang_pref:
            tags["language_bonus"] = True
            final_score *= 1.05

        if avoid_tokens and tokens.intersection(avoid_tokens):
            tags["avoid_penalty"] = True
            final_score *= 0.70

        ranked.append(
            RankedCourse(
                code=code,
                name=course.name,
                group=course.group,
                language=course.language,
                cfu=float(course.cfu),
                score=float(final_score),
                reason_tags=tags,
            )
        )

    # Sort and truncate
    ranked.sort(key=lambda rc: (-rc["score"], rc["code"]))

    if top_k is not None and top_k > 0:
        ranked = ranked[:top_k]

    return ranked


def _edge_concepts_for_pair(
    course_a: Course,
    course_b: Course,
    weight: float
) -> tuple[List[str], List[EdgeReason]]:
    """
    Recover the likely reasons for an edge existence based on metadata.
    """
    concepts: List[str] = []
    reasons: List[EdgeReason] = []

    # Check Shared Group
    group_a = (course_a.group or "").strip()
    group_b = (course_b.group or "").strip()
    if group_a and group_b and group_a == group_b:
        concepts.append(f"Same Group: {group_a}")
        reasons.append({
            "type": "shared_group",
            "value": group_a,
            "contribution": 0.6  # Default w_group
        })

    # Check Shared SSD
    ssd_a = set(course_a.ssd)
    ssd_b = set(course_b.ssd)
    common_ssd = ssd_a.intersection(ssd_b)
    if common_ssd:
        ssd_val = next(iter(common_ssd))
        concepts.append(f"Shared SSD: {ssd_val}")
        reasons.append({
            "type": "shared_ssd",
            "value": ssd_val,
            "contribution": 0.9  # Default w_ssd
        })

    # Text similarity estimation
    base_structural = 0.0
    if group_a and group_b and group_a == group_b: base_structural += 0.6
    if common_ssd: base_structural += 0.9
    
    estimated_text_contrib = weight - base_structural
    if estimated_text_contrib > 0.1:
        concepts.append("High text similarity")
        reasons.append({
            "type": "text_similarity",
            "value": f"score: {estimated_text_contrib:.2f}",
            "contribution": float(estimated_text_contrib)
        })

    # Fallbacks
    if not concepts:
        concepts.append("Related content")
        reasons.append({
            "type": "other",
            "value": "graph_edge",
            "contribution": weight
        })

    return concepts, reasons


def build_graph_view_for_recommendations(
    recommended_codes: List[str],
    graph: GraphAdjacency,
    courses: List[Course],
    pagerank_scores: Dict[str, float] | None = None,
    max_neighbors_per_node: int = 4,
    node_cap: int = 40,
    edge_cap: int = 120,
) -> GraphView:
    """
    Construct a high-quality subgraph containing recommended courses, 
    their top neighbors, and bridge nodes.
    """
    recommended_set = set(recommended_codes)
    courses_map = {c.code: c for c in courses if c.code}

    selected_nodes: Set[str] = set(recommended_codes)
    
    # 1. Add top neighbors for each recommended node
    for code in recommended_codes:
        if code not in graph:
            continue
        # Get neighbors sorted by weight desc
        neighbors = sorted(graph[code].items(), key=lambda x: -x[1])
        for nbr_code, _ in neighbors[:max_neighbors_per_node]:
            selected_nodes.add(nbr_code)

    # 2. Add bridge nodes (connected to 2+ recommended nodes)
    bridge_candidates: Dict[str, int] = {}
    for code in recommended_codes:
        if code not in graph:
            continue
        for nbr_code in graph[code]:
            if nbr_code not in recommended_set:
                bridge_candidates[nbr_code] = bridge_candidates.get(nbr_code, 0) + 1
    
    for node, count in bridge_candidates.items():
        if count >= 2:
            selected_nodes.add(node)

    # 3. Node list construction (capped)
    scored_nodes = []
    for code in selected_nodes:
        is_rec = code in recommended_set
        score = (pagerank_scores or {}).get(code, 0.0)
        scored_nodes.append((code, is_rec, score))

    # Stable sort: recommended desc, score desc, code asc
    scored_nodes.sort(key=lambda x: (-int(x[1]), -x[2], x[0]))

    # Apply node cap
    final_node_codes = [x[0] for x in scored_nodes[:node_cap]]
    final_node_set = set(final_node_codes)

    # 4. Edge construction
    candidate_edges = []
    seen_pairs = set()
    for code in final_node_codes:
        if code not in graph:
            continue
        for nbr_code, w in graph[code].items():
            if nbr_code in final_node_set:
                pair = tuple(sorted((code, nbr_code)))
                if pair not in seen_pairs:
                    seen_pairs.add(pair)
                    candidate_edges.append((code, nbr_code, w))

    # Stable sort: weight desc, source code
    candidate_edges.sort(key=lambda x: (-x[2], x[0], x[1]))

    # Apply edge cap
    final_edges = candidate_edges[:edge_cap]

    # 5. Build final objects
    nodes_out: List[GraphNode] = []
    for code, is_rec, score in scored_nodes[:node_cap]:
        c_obj = courses_map.get(code)
        nodes_out.append({
            "code": code,
            "label": c_obj.name if c_obj else code,
            "score": score,
            "is_recommended": is_rec,
            "group": c_obj.group if c_obj else None,
        })

    edges_out: List[GraphEdge] = []
    for src, tgt, w in final_edges:
        c_a = courses_map.get(src)
        c_b = courses_map.get(tgt)
        if c_a and c_b:
            concepts, reasons = _edge_concepts_for_pair(c_a, c_b, w)
            edges_out.append({
                "source": src,
                "target": tgt,
                "weight": w,
                "concepts": concepts,
                "reasons": reasons,
            })
        else:
            edges_out.append({
                "source": src,
                "target": tgt,
                "weight": w,
                "concepts": ["Related content"],
                "reasons": [{"type": "other", "value": "graph_edge", "contribution": w}],
            })

    return {
        "nodes": nodes_out,
        "edges": edges_out,
    }
