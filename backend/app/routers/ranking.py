# backend/app/routers/ranking.py

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query

from ..deps import get_courses_raw, get_graph
from ..models import StudentProfileIn, RankedCourseOut
from ..schemas_chat import ChatRequest, ChatResponse, StudentProfileModel

# Import Core definitions
from ...core.models import Course
from ...core.ranking import rank_courses as core_rank_courses  # type: ignore
from ...core.llm import generate_reply, extract_profile, LLMServiceError
from ...core.types import ChatMessage

# Router prefix is empty here so we can define /rank and /chat explicitly.
# main.py mounts this router with prefix="/api".
router = APIRouter(
    tags=["ranking"],
)

SYSTEM_PROMPT_ADVISOR = """
You are a helpful but honest course advisor for the Computer Science and Engineering MSc
at Politecnico di Milano.

Your job:
- Help the student reason about their interests, dislikes, and career goals.
- Encourage them to clarify things like preferred topics, workload tolerance,
  exam formats, and language preferences.
- Never invent course codes, credits, or rules. The final recommendations come from
  a separate ranking system; you can comment on and explain them, but not fabricate new ones.
- Use clear, concise language. Default to English unless the student clearly prefers Italian.
- Be transparent when you are unsure or lack information.
"""


def _normalize_reason_tags(raw: Any) -> List[str]:
    """
    Normalize various reason_tags shapes into a list of strings.
    """
    if raw is None:
        return []

    if isinstance(raw, list):
        return [str(x) for x in raw]

    if isinstance(raw, dict):
        tags: List[str] = []
        for k, v in raw.items():
            if bool(v):
                tags.append(str(k))
        return tags

    return [str(raw)]


def get_recommendations_for_profile(profile: dict, top_k: int) -> List[Dict[str, Any]]:
    """
    Helper that encapsulates the existing ranking logic used by /api/rank.
    Uses the same globals (courses, graph, etc.) and returns a list of course dicts.
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
            profile,
            top_k,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Ranking failed: {exc}") from exc

    results: List[Dict[str, Any]] = []

    for item in ranked_items:
        if not isinstance(item, dict):
            continue

        code = item.get("code")
        if not code or code not in index_by_code:
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
        results.append(merged)

    return results


@router.post("/rank", response_model=List[RankedCourseOut])
async def rank_endpoint(
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
    """
    # Reuse valid logic
    recommendations_dicts = get_recommendations_for_profile(profile.model_dump(), top_k)
    return [RankedCourseOut.model_validate(r) for r in recommendations_dicts]


@router.post("/chat", response_model=ChatResponse)
async def chat_endpoint(payload: ChatRequest) -> ChatResponse:
    """
    LLM-backed chat endpoint.

    Steps:
    - Ensure a system prompt is present.
    - Call the LLM to generate the next assistant reply.
    - Call the LLM again (JSON mode) to produce an updated StudentProfile.
    - Call the ranking helper to get top-N course recommendations.
    """

    # 1) Build messages for the LLM, injecting our system prompt if needed.
    incoming_messages = [m.model_dump() for m in payload.messages]

    has_system = any(m["role"] == "system" for m in incoming_messages)

    messages_for_llm: List[ChatMessage] = []
    if not has_system:
        messages_for_llm.append(
            {
                "role": "system",
                "content": SYSTEM_PROMPT_ADVISOR,
            }
        )

    messages_for_llm.extend(
        [
            {"role": m["role"], "content": m["content"]}
            for m in incoming_messages
        ]
    )

    # 2) Prepare previous profile dict (if any).
    previous_profile_dict = None
    if payload.current_profile is not None:
        previous_profile_dict = payload.current_profile.to_profile_dict()

    try:
        # 3) Generate the assistant's natural-language reply.
        reply_text = generate_reply(messages_for_llm)

        # 4) Ask the LLM for an updated profile (including this new reply in the history).
        messages_for_profile: List[ChatMessage] = list(messages_for_llm)
        messages_for_profile.append(
            {
                "role": "assistant",
                "content": reply_text,
            }
        )

        updated_profile_dict = extract_profile(
            messages_for_profile,
            previous_profile=previous_profile_dict,
        )
    except LLMServiceError as exc:
        # Surface as a 503 so the frontend can show a nice error message.
        raise HTTPException(status_code=503, detail=str(exc))

    # 5) Convert the updated profile dict into the API-facing Pydantic model.
    updated_profile_model = StudentProfileModel(
        interests=updated_profile_dict.get("interests", []),
        avoid=updated_profile_dict.get("avoid", []),
        goals=updated_profile_dict.get("goals", []),
        language_preference=updated_profile_dict.get("language_preference", "ANY"), # type: ignore
        workload_tolerance=updated_profile_dict.get("workload_tolerance"), # type: ignore
        preferred_exam_types=updated_profile_dict.get("preferred_exam_types", []),
        liked_courses=updated_profile_dict.get("liked_courses", []),
        disliked_courses=updated_profile_dict.get("disliked_courses", []),
        ready_for_recommendations=updated_profile_dict.get("ready_for_recommendations"),
    )

    # 6) Compute recommendations using the same logic as /api/rank.
    profile_for_ranking = updated_profile_model.to_profile_dict()
    top_k = payload.top_k

    # Only compute recommendations when the LLM says the profile is ready.
    if updated_profile_model.ready_for_recommendations:
        recommendations = get_recommendations_for_profile(
            profile_for_ranking,
            top_k=top_k,
        )
    else:
        recommendations = []

    return ChatResponse(
        reply=reply_text,
        updated_profile=updated_profile_model,
        recommendations=recommendations,
    )
