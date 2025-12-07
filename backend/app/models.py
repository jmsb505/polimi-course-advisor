# backend/app/models.py

from typing import List, Optional
from pydantic import BaseModel, Field


class AlphaGroupLast(BaseModel):
    # "from" is a reserved keyword, so we alias it
    from_: str = Field(alias="from")
    to: str
    lecturer: str

    class Config:
        populate_by_name = True


class CourseBase(BaseModel):
    code: str
    name: str
    cfu: float
    semester: int
    language: str
    group: str


class CourseSummary(CourseBase):
    alpha_group_last: Optional[AlphaGroupLast] = None


class CourseDetail(CourseSummary):
    description: Optional[str] = None
    # Optional debug info, e.g. graph neighbors; filled later
    neighbors: Optional[List[str]] = None


class StudentProfileIn(BaseModel):
    """
    Payload coming from the frontend describing the student.
    All fields are optional and default to empty / None.
    """
    interests: List[str] = []
    avoid: List[str] = []
    goals: List[str] = []
    language_preference: Optional[str] = None
    workload_tolerance: Optional[str] = None
    preferred_exam_types: List[str] = []
    liked_courses: List[str] = []
    disliked_courses: List[str] = []


class RankedCourseOut(CourseSummary):
    score: float
    reason_tags: List[str] = []
