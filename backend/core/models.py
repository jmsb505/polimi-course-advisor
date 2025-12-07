from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, TypedDict, Union


@dataclass
class Course:
    code: str
    name: str
    cfu: float
    semester: int
    language: str
    group: str
    ssd: List[str]
    description: str
    # Keep the raw dict around in case we need extra fields later
    raw: Dict[str, Any]


def load_courses(path: Union[str, Path]) -> List[Course]:
    """
    Load courses from a JSON file like backend/data/courses.json.
    Returns a list of Course instances with some light normalization.
    """
    p = Path(path)
    with p.open("r", encoding="utf-8") as f:
        data = json.load(f)

    courses: List[Course] = []
    for item in data:
        code = str(item.get("code", "")).strip()
        name = str(item.get("name", "")).strip()
        description = str(item.get("description", "") or "").strip()
        language = str(item.get("language", "") or "UNKNOWN").strip().upper()
        group = str(item.get("group", "") or "UNKNOWN").strip()

        cfu_raw = item.get("cfu", 0)
        try:
            cfu = float(cfu_raw)
        except (TypeError, ValueError):
            cfu = 0.0

        sem_raw = item.get("semester", 0)
        try:
            semester = int(sem_raw)
        except (TypeError, ValueError):
            semester = 0

        ssd_raw = item.get("ssd", []) or []
        if isinstance(ssd_raw, list):
            ssd_list = [str(s).strip() for s in ssd_raw if s]
        else:
            ssd_list = [str(ssd_raw).strip()]

        courses.append(
            Course(
                code=code,
                name=name,
                cfu=cfu,
                semester=semester,
                language=language,
                group=group,
                ssd=ssd_list,
                description=description,
                raw=item,
            )
        )

    return courses


class StudentProfile(TypedDict, total=False):
    interests: List[str]
    avoid: List[str]
    goals: List[str]
    language_preference: str      # "EN", "IT", "ANY"
    workload_tolerance: str       # "low" | "medium" | "high"
    preferred_exam_types: List[str]
    liked_courses: List[str]
    disliked_courses: List[str]


class RankedCourse(TypedDict):
    code: str
    name: str
    group: str
    language: str
    cfu: float
    score: float
    # Simple tag flags like:
    #   - matched_interest
    #   - liked_course
    #   - liked_neighbor
    #   - avoided_keyword
    reason_tags: Dict[str, bool]
