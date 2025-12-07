from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Set

from .models import Course, StudentProfile, RankedCourse
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
