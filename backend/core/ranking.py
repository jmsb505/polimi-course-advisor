from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Set

from .models import Course, StudentProfile, RankedCourse
from .types import GraphView, GraphNode, GraphEdge
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
    interest_weight = 2.0
    if interest_token_sets:
        for code in nodes:
            tokens = tokens_map.get(code, set())
            if not tokens:
                continue

            score = 0.0
            for q in interest_token_sets:
                if not q:
                    continue
                sim = jaccard_similarity(tokens, q)
                if sim > 0:
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
            final_score *= 1.15

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
) -> tuple[List[str], List[str]]:
    """
    Recover the likely reasons for an edge existence based on metadata.
    Since we only store a float weight, we re-check group/SSD/text logic.
    """
    concepts: List[str] = []
    reasons: List[str] = []

    # Check Shared Group
    group_a = (course_a.group or "").strip()
    group_b = (course_b.group or "").strip()
    if group_a and group_b and group_a == group_b:
        concepts.append(f"Same Group: {group_a}")
        reasons.append("shared_group")

    # Check Shared SSD
    ssd_a = set(course_a.ssd)
    ssd_b = set(course_b.ssd)
    common_ssd = ssd_a.intersection(ssd_b)
    if common_ssd:
        # Just pick one for brevity
        concepts.append(f"Shared SSD: {next(iter(common_ssd))}")
        reasons.append("shared_ssd")

    # Heuristic for high text similarity if weight is significantly higher than structural components
    # (This is approximate, as we don't know the exact config used)
    if weight >= 0.5:
        concepts.append("High text similarity")
        reasons.append("text_similarity")

    # Fallbacks
    if not concepts:
        concepts.append("Related content")
    if not reasons:
        reasons.append("graph_edge")

    # Deduplicate while preserving order
    return list(dict.fromkeys(concepts)), list(dict.fromkeys(reasons))


def build_graph_view_for_recommendations(
    recommended_codes: List[str],
    graph: GraphAdjacency,
    courses: List[Course],
    pagerank_scores: Dict[str, float] | None = None,
    max_neighbors_per_node: int = 4,
) -> GraphView:
    """
    Construct a subgraph containing recommended courses and their top neighbors.
    """
    recommended_set = set(recommended_codes)
    nodes_by_code: Dict[str, GraphNode] = {}
    edges_list: List[GraphEdge] = []
    seen_pairs: Set[tuple[str, str]] = set()

    # Index courses for quick lookup
    courses_map = {c.code: c for c in courses if c.code}

    # Helper to create a node
    def make_node(code: str, is_rec: bool) -> GraphNode:
        c_obj = courses_map.get(code)
        label = c_obj.name if c_obj else code
        grp = c_obj.group if c_obj else None
        
        # Use provided PageRank score if avail, else 0.0
        sc = 0.0
        if pagerank_scores and code in pagerank_scores:
            sc = pagerank_scores[code]

        return GraphNode(
            code=code,
            label=label,
            score=sc,
            is_recommended=is_rec,
            group=grp,
        )

    # 1. Add all recommended courses
    for code in recommended_codes:
        if code not in nodes_by_code:
            nodes_by_code[code] = make_node(code, True)

    # 2. For each recommended course, find top neighbors
    for code in recommended_codes:
        if code not in graph:
            continue
        
        # Sort neighbors by weight descending
        neighbors = sorted(
            graph[code].items(),
            key=lambda item: item[1],
            reverse=True
        )
        # Take top K
        top_neighbors = neighbors[:max_neighbors_per_node]

        for nbr_code, w in top_neighbors:
            # Ensure neighbor node exists
            if nbr_code not in nodes_by_code:
                nodes_by_code[nbr_code] = make_node(nbr_code, False)

            # Create edge
            pair = tuple(sorted((code, nbr_code)))
            if pair in seen_pairs:
                continue
            seen_pairs.add(pair) # type: ignore

            # Determine concepts/reasons
            c_a = courses_map.get(code)
            c_b = courses_map.get(nbr_code)
            
            concepts: List[str] = []
            reasons: List[str] = ["graph_edge"]
            
            if c_a and c_b:
                concepts, reasons = _edge_concepts_for_pair(c_a, c_b, w)

            edges_list.append(
                GraphEdge(
                    source=code,
                    target=nbr_code,
                    weight=w,
                    concepts=concepts,
                    reasons=reasons,
                )
            )

    return GraphView(
        nodes=list(nodes_by_code.values()),
        edges=edges_list,
    )
