# backend/app/routers/ranking.py

from typing import Any, Dict, List

from fastapi import APIRouter, HTTPException, Query

from ..deps import get_courses_raw, get_graph
from ..models import StudentProfileIn, RankedCourseOut

# Import Course dataclass for type conversion
from ...core.models import Course
# Assumes Phase 2 exposed rank_courses here; adjust path/name if needed.
from ...core.ranking import rank_courses as core_rank_courses  # type: ignore

router = APIRouter(
    prefix="/rank",
    tags=["ranking"],
)


def _normalize_reason_tags(raw: Any) -> List[str]:
    """
    Normalize various reason_tags shapes into a list of strings.

    Supported forms:
    - list of strings (['interest_match', 'graph_central'])
    - dict of flags ({'interest_match': True, 'low_conflict': False})
    - single non-list, non-dict value ('interest_match')
    """
    if raw is None:
        return []

    if isinstance(raw, list):
        return [str(x) for x in raw]

    if isinstance(raw, dict):
        tags: List[str] = []
        for k, v in raw.items():
            # Only keep keys whose value is truthy
            if bool(v):
                tags.append(str(k))
        return tags

    # Fallback: single value
    return [str(raw)]


@router.post("", response_model=List[RankedCourseOut])
async def rank_courses_endpoint(
    profile: StudentProfileIn,
    top_k: int = Query(
        default=10,
        ge=1,
        le=50,
        description="Number of courses to return.",
    ),
) -> List[RankedCourseOut]:
    """
    Rank courses for a given student profile using the existing
    PageRank-based ranking logic from Phase 2.

    We treat the Phase 2 output as "ranking annotations" and merge
    them with the canonical course metadata from courses.json.
    """
    courses_raw = get_courses_raw()
    graph = get_graph()

    # Convert raw dicts to Course objects for core logic
    course_objects = []
    for item in courses_raw:
        ssd_raw = item.get("ssd", []) or []
        ssd_list = [str(s).strip() for s in ssd_raw if s] if isinstance(ssd_raw, list) else [str(ssd_raw).strip()]
        
        c_obj = Course(
            code=str(item.get("code", "")).strip(),
            name=str(item.get("name", "")).strip(),
            cfu=float(item.get("cfu", 0)),
            semester=int(item.get("semester", 0)),
            language=str(item.get("language", "") or "UNKNOWN").strip().upper(),
            group=str(item.get("group", "") or "UNKNOWN").strip(),
            ssd=ssd_list,
            description=str(item.get("description", "") or "").strip(),
            raw=item
        )
        course_objects.append(c_obj)

    # Index course metadata by code for quick lookup
    index_by_code: Dict[str, Dict[str, Any]] = {
        c["code"]: c for c in courses_raw if "code" in c
    }

    try:
        ranked_items = core_rank_courses(
            course_objects,
            graph,
            profile.model_dump(),
            top_k,
        )
    except Exception as exc:  # pragma: no cover - defensive
        raise HTTPException(status_code=500, detail=f"Ranking failed: {exc}") from exc

    results: List[RankedCourseOut] = []

    for item in ranked_items:
        if not isinstance(item, dict):
            # Skip completely broken items instead of crashing
            continue

        code = item.get("code")
        if not code or code not in index_by_code:
            # If the ranker returns something weird, just skip it
            continue

        base = index_by_code[code]

        score = item.get("score", 0.0)
        reason_raw = item.get("reason_tags") or item.get("reasons") or item.get("debug")

        merged = {
            "code": base.get("code"),
            "name": base.get("name"),
            "cfu": base.get("cfu", 0),
            "semester": base.get("semester", 1),
            "language": base.get("language", "UNKNOWN"),
            "group": base.get("group", "UNKNOWN"),
            "alpha_group_last": base.get("alpha_group_last"),
            "score": float(score),
            "reason_tags": _normalize_reason_tags(reason_raw),
        }

        # Let Pydantic enforce the final schema
        results.append(RankedCourseOut.model_validate(merged))

    return results
