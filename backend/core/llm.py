from __future__ import annotations

import json
from typing import Any, Dict, List, Optional

from openai import OpenAI, OpenAIError, RateLimitError

from .types import ChatMessage, StudentProfile
from .settings_llm import (
    OPENAI_MODEL_PROFILE,
    OPENAI_MODEL_REPLY,
    OPENAI_TEMPERATURE_PROFILE,
    OPENAI_TEMPERATURE_REPLY,
    ensure_openai_api_key,
)


class LLMServiceError(Exception):
    """Raised when the LLM service (OpenAI) is unavailable or returns an error."""
    pass


# Single shared client instance; reads OPENAI_API_KEY from the environment.
client = OpenAI()


def generate_reply(messages: List[ChatMessage]) -> str:
    """
    Given a list of chat messages (including a system prompt),
    ask the LLM for the next assistant reply.
    """
    ensure_openai_api_key()

    try:
        completion = client.chat.completions.create(
            model=OPENAI_MODEL_REPLY,
            messages=messages,
            temperature=OPENAI_TEMPERATURE_REPLY,
        )

        message = completion.choices[0].message
        content = message.content or ""
        return content
    except RateLimitError as exc:
        # Typical case: insufficient_quota / rate limiting.
        raise LLMServiceError(
            "LLM quota exceeded or temporarily unavailable. Please check your OpenAI plan/billing."
        ) from exc
    except OpenAIError as exc:
        # Any other OpenAI-related error.
        raise LLMServiceError("LLM call failed. Please try again later.") from exc


def extract_profile(
    messages: List[ChatMessage],
    previous_profile: Optional[StudentProfile] = None,
) -> StudentProfile:
    """
    Given the chat history and the previous profile, ask the LLM to return
    an updated StudentProfile as strict JSON.

    Uses Chat Completions JSON mode (response_format={"type": "json_object"}).
    """
    ensure_openai_api_key()

    # System instructions for profile extraction.
    system_instructions = (
        "You are a strict JSON-producing assistant that extracts a student profile "
        "for a Politecnico di Milano MSc student from the conversation.\n\n"
        "Your ONLY output must be a single JSON object with these optional fields:\n"
        "  - interests: string[]\n"
        "  - avoid: string[]\n"
        "  - goals: string[]\n"
        "  - language_preference: \"EN\" | \"IT\" | \"ANY\"\n"
        "  - workload_tolerance: \"low\" | \"medium\" | \"high\"\n"
        "  - preferred_exam_types: string[]\n"
        "  - liked_courses: string[]  # course codes\n"
        "  - disliked_courses: string[]  # course codes\n"
        "  - ready_for_recommendations: boolean  # true only when you have enough information "
        "to propose concrete courses or the student explicitly asks for recommendations.\n\n"
        "Rules:\n"
        "  - Do NOT include any explanation text, comments, or Markdown.\n"
        "  - Omit fields you are not confident about.\n"
        "  - Use uppercase EN/IT/ANY for language_preference.\n"
        "  - Use lowercase for workload_tolerance.\n"
        "  - Set ready_for_recommendations to true ONLY when the profile is rich enough "
        "to support concrete course suggestions (e.g., interests + some goals and preferences), "
        "or when the student explicitly asks for recommendations.\n"
    )

    api_messages: List[Dict[str, Any]] = [
        {"role": "system", "content": system_instructions},
    ]

    # Reuse the existing conversation messages after our system prompt.
    for m in messages:
        api_messages.append({"role": m["role"], "content": m["content"]})

    # Provide the previous profile (if any) as an additional hint.
    if previous_profile:
        api_messages.append(
            {
                "role": "user",
                "content": (
                    "Here is the current known profile as JSON. "
                    "Update it if needed, keeping consistent fields:\n"
                    f"{json.dumps(previous_profile, ensure_ascii=False)}"
                ),
            }
        )
    # Final instruction to enforce pure JSON output.
    api_messages.append(
        {
            "role": "user",
            "content": (
                "Now respond ONLY with the updated profile as a single JSON object, "
                "with no surrounding text."
            ),
        }
    )

    try:
        completion = client.chat.completions.create(
            model=OPENAI_MODEL_PROFILE,
            messages=api_messages,
            temperature=OPENAI_TEMPERATURE_PROFILE,
            response_format={"type": "json_object"},
        )
        raw = completion.choices[0].message.content or "{}"
        data = json.loads(raw)
    except RateLimitError as exc:
        raise LLMServiceError(
            "LLM quota exceeded or temporarily unavailable. Please check your OpenAI plan/billing."
        ) from exc
    except OpenAIError as exc:
        raise LLMServiceError("LLM call failed while extracting profile.") from exc
    except Exception:
        # JSON parsing or other local error: fall back to previous_profile or empty.
        if previous_profile is not None:
            return dict(previous_profile)
        return {}

    return _normalize_profile(data, previous_profile)


# --------- helpers ---------


LIST_FIELDS = [
    "interests",
    "avoid",
    "goals",
    "preferred_exam_types",
    "liked_courses",
    "disliked_courses",
]


def _normalize_profile(
    data: Dict[str, Any],
    previous_profile: Optional[StudentProfile] = None,
) -> StudentProfile:
    """
    Merge the model-produced JSON with the previous profile and clean it up.

    - Merges list fields (deduping while preserving order).
    - Normalizes enums (language_preference, workload_tolerance).
    - Drops unknown fields.
    """
    merged: StudentProfile = {}

    if previous_profile:
        merged.update(previous_profile)

    # Handle list fields
    for field in LIST_FIELDS:
        new_values = data.get(field)
        if isinstance(new_values, list):
            merged[field] = _merge_lists(
                list(merged.get(field, [])),  # type: ignore[literal-required]
                [str(x).strip() for x in new_values if str(x).strip()],
            )

    # language_preference
    lang = data.get("language_preference")
    if isinstance(lang, str):
        lang_up = lang.upper()
        if lang_up in {"EN", "IT", "ANY"}:
            merged["language_preference"] = lang_up

    # workload_tolerance
    wt = data.get("workload_tolerance")
    if isinstance(wt, str):
        wt_low = wt.lower()
        if wt_low in {"low", "medium", "high"}:
            merged["workload_tolerance"] = wt_low  # type: ignore[assignment]

    # ready_for_recommendations
    rfr = data.get("ready_for_recommendations")
    if isinstance(rfr, bool):
        merged["ready_for_recommendations"] = rfr

    return merged



def _merge_lists(existing: List[str], new: List[str]) -> List[str]:
    """
    Append new items that are not already present (case-sensitive).
    """
    seen = set(existing)
    for item in new:
        if item not in seen:
            existing.append(item)
            seen.add(item)
    return existing



def generate_course_explanations(
    profile: StudentProfile,
    courses: List[Dict[str, Any]],
) -> Dict[str, str]:
    """
    Ask the LLM to briefly explain why each recommended course fits the student profile.
    Returns a dict mapping course code -> explanation string.
    """
    if not courses:
        return {}
        
    ensure_openai_api_key()

    # Simplify courses for the prompt to save tokens
    simple_courses = []
    for c in courses:
        simple_courses.append({
            "code": c.get("code"),
            "name": c.get("name"),
            "group": c.get("group"),
        })

    payload = {
        "student_profile": profile,
        "courses": simple_courses,
    }

    system_instructions = (
        "You are an academic advisor for a Politecnico di Milano MSc program. "
        "Given a student profile and a list of courses, explain briefly why each course fits the student. "
        "Write very concise, 1-2 sentence explanations, focused on interests, dislikes, and goals. "
        "Respond ONLY with JSON of the form:\n"
        "{ \"explanations\": { \"COURSE_CODE\": \"explanation\", ... } }"
    )

    messages = [
        {"role": "system", "content": system_instructions},
        {"role": "user", "content": json.dumps(payload, ensure_ascii=False)},
    ]

    try:
        completion = client.chat.completions.create(
            model=OPENAI_MODEL_REPLY, # reuse the reply model (usually cheap/fast)
            messages=messages, # type: ignore
            temperature=0.7,
            response_format={"type": "json_object"},
        )
        raw = completion.choices[0].message.content or "{}"
        data = json.loads(raw)
        explanations = data.get("explanations", {})
        return {str(k): str(v) for k, v in explanations.items()}
    except Exception:
        # If anything fails (rate limit, parsing), safely return empty dict
        # so we don't block the response.
        return {}
