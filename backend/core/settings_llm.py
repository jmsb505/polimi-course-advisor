import os


# Core configuration for OpenAI usage in this project.
# All of these can be overridden via environment variables.


# Chat reply model (natural language advisor responses)
OPENAI_MODEL_REPLY: str = os.getenv("OPENAI_MODEL_REPLY", "gpt-4o-mini")

# Profile extraction model (JSON structured output).
# Defaults to the same as the reply model unless explicitly overridden.
OPENAI_MODEL_PROFILE: str = os.getenv("OPENAI_MODEL_PROFILE", OPENAI_MODEL_REPLY)

# Temperatures
# - Replies: a bit of creativity.
# - Profile: deterministic updates.
try:
    OPENAI_TEMPERATURE_REPLY: float = float(
        os.getenv("OPENAI_TEMPERATURE_REPLY", "0.7")
    )
except ValueError:
    OPENAI_TEMPERATURE_REPLY = 0.7

try:
    OPENAI_TEMPERATURE_PROFILE: float = float(
        os.getenv("OPENAI_TEMPERATURE_PROFILE", "0.0")
    )
except ValueError:
    OPENAI_TEMPERATURE_PROFILE = 0.0


def ensure_openai_api_key() -> None:
    """
    Optional helper to fail fast if OPENAI_API_KEY is missing.

    You can call this during startup or right before making LLM calls.
    """
    if not os.getenv("OPENAI_API_KEY"):
        raise RuntimeError(
            "OPENAI_API_KEY environment variable is not set. "
            "Set it before using the LLM-backed features."
        )
