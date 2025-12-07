# backend/app/routers/courses.py

from typing import List, Optional

from fastapi import APIRouter, HTTPException, Query

from ..deps import get_courses_as_models
from ..models import CourseSummary, CourseDetail

router = APIRouter(
    prefix="/courses",
    tags=["courses"],
)


@router.get("", response_model=List[CourseSummary])
async def list_courses(
    q: Optional[str] = Query(
        default=None,
        description="Optional search term to match in course name (case-insensitive).",
    ),
    group: Optional[str] = Query(
        default=None,
        description="Optional filter by course group (e.g. GROUNDINGS, METHODS).",
    ),
    semester: Optional[int] = Query(
        default=None,
        description="Optional filter by semester (1, 2, ...). Dataset is already semester 1 only.",
    ),
) -> List[CourseSummary]:
    """
    List all first-semester, non-ENHANCE courses.

    Optional filters:
    - q: substring search on course name (case-insensitive)
    - group: exact group match
    - semester: exact semester match (for future flexibility)
    """
    courses = get_courses_as_models()
    filtered: List[CourseDetail] = []

    for c in courses:
        if semester is not None and c.semester != semester:
            continue
        if group is not None and c.group != group:
            continue
        if q is not None and q.lower() not in c.name.lower():
            continue
        filtered.append(c)

    # Downcast to CourseSummary for the response
    return [CourseSummary.model_validate(c.model_dump()) for c in filtered]


@router.get("/{code}", response_model=CourseDetail)
async def get_course_by_code(code: str) -> CourseDetail:
    """
    Return full details for a single course by its code.

    For now, neighbors (graph-based) are not populated yet.
    """
    courses = get_courses_as_models()
    for c in courses:
        if c.code == code:
            return c

    raise HTTPException(status_code=404, detail="Course not found")
