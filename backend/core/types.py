from typing import List, Literal, TypedDict, Optional


class StudentProfile(TypedDict, total=False):
    """
    Internal typing-only representation of the student profile.

    All fields are optional (total=False) so we can handle partial updates.
    """
    interests: List[str]
    avoid: List[str]
    goals: List[str]
    language_preference: Literal["EN", "IT", "ANY"]
    workload_tolerance: Literal["low", "medium", "high"]
    preferred_exam_types: List[str]
    liked_courses: List[str]       # course codes
    disliked_courses: List[str]    # course codes
    ready_for_recommendations: bool


class ChatMessage(TypedDict):
    """
    Minimal chat message model compatible with OpenAI messages.
    """
    role: Literal["system", "user", "assistant"]

    content: str


class GraphNode(TypedDict):
    code: str
    label: str
    score: float
    is_recommended: bool
    group: Optional[str]


class EdgeReason(TypedDict):
    type: str
    value: str
    contribution: float


class GraphEdge(TypedDict):
    source: str
    target: str
    weight: float
    concepts: List[str]
    reasons: List[EdgeReason]


class GraphView(TypedDict):
    nodes: List[GraphNode]
    edges: List[GraphEdge]
