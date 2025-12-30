from typing import List, Literal, Optional

from pydantic import BaseModel


class ChatMessageModel(BaseModel):
    role: Literal["system", "user", "assistant"]
    content: str


class StudentProfileModel(BaseModel):
    """
    API-facing version of StudentProfile.

    - All fields default to empty/None so the client can send partial profiles.
    - We'll convert this to the internal dict/TypedDict form when calling ranking/LLM.
    """
    interests: List[str] = []
    avoid: List[str] = []
    goals: List[str] = []
    language_preference: Literal["EN", "IT", "ANY"] = "ANY"
    workload_tolerance: Optional[Literal["low", "medium", "high"]] = None
    preferred_exam_types: List[str] = []
    liked_courses: List[str] = []
    disliked_courses: List[str] = []
    ready_for_recommendations: Optional[bool] = None

    def to_profile_dict(self) -> dict:
        """
        Convert to a plain dict, dropping empty/None values
        to stay compatible with any existing ranking code that
        expects only present fields.
        """
        data = self.model_dump()
        return {
            key: value
            for key, value in data.items()
            if value not in (None, [], "")
        }


class ChatRequest(BaseModel):
    """
    Request payload for /api/chat.

    - messages: full chat history (user+assistant, plus optional system).
    - current_profile: the profile accumulated so far (optional).
    - top_k: how many courses to recommend this turn.
    """
    messages: List[ChatMessageModel]
    current_profile: Optional[StudentProfileModel] = None
    top_k: int = 5



class GraphNode(BaseModel):
    code: str
    label: str
    score: float
    is_recommended: bool
    group: Optional[str] = None


class EdgeReason(BaseModel):
    type: str  # "shared_group" | "shared_ssd" | "text_similarity" | "keyword_overlap" | "other"
    value: str
    contribution: float


class GraphEdge(BaseModel):
    source: str
    target: str
    weight: float
    concepts: List[str]
    reasons: List[EdgeReason]


class GraphView(BaseModel):
    nodes: List[GraphNode]
    edges: List[GraphEdge]


class CourseRecommendation(BaseModel):
    code: str
    name: str
    score: float
    group: Optional[str] = None
    explanation: Optional[str] = None
    cfu: float = 0.0
    semester: int = 1
    language: str = "UNKNOWN"
    reason_tags: List[str] = []


class ChatResponse(BaseModel):
    """
    Response payload for /api/chat.

    - reply: assistant's natural-language reply.
    - updated_profile: merged profile after this turn.
    - recommendations: list of CourseRecommendation objects.
    - graph_view: optional subgraph visualization data.
    """
    reply: str
    updated_profile: StudentProfileModel
    recommendations: List[CourseRecommendation]
    graph_view: Optional[GraphView] = None
    run_id: Optional[str] = None
