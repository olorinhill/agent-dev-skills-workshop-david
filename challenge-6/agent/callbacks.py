"""ADK callback functions for logging and prompt validation."""

from __future__ import annotations

from typing import Optional
import logging
import re

from google.adk.agents.callback_context import CallbackContext
from google.adk.models import LlmRequest, LlmResponse


logger = logging.getLogger("readynow.callbacks")

MISSION_KEYWORDS = (
    "weather",
    "storm",
    "flood",
    "hurricane",
    "tornado",
    "wildfire",
    "earthquake",
    "evac",
    "route",
    "shelter",
    "disaster",
    "emergency",
    "safety",
    "preparedness",
    "fema",
    "hazard",
)

MALICIOUS_PATTERNS = (
    "ignore previous instructions",
    "reveal system prompt",
    "developer message",
    "bypass safety",
    "write malware",
    "how to build a bomb",
)

NON_US_LOCATION_HINTS = (
    "canada",
    "mexico",
    "united kingdom",
    "uk",
    "france",
    "germany",
    "japan",
    "australia",
)


def _extract_user_text(llm_request: LlmRequest) -> str:
    if not llm_request.contents:
        return ""
    last = llm_request.contents[-1]
    if last.role != "user" or not last.parts:
        return ""
    text = getattr(last.parts[0], "text", None)
    return (text or "").strip()


def log_user_prompt(
    callback_context: CallbackContext,
    llm_request: LlmRequest,
) -> Optional[LlmResponse]:
    """Log the user's prompt before the model is called."""
    text = _extract_user_text(llm_request)
    if text:
        logger.info("[%s] USER >> %s", callback_context.agent_name, text)
    return None


def log_model_response(
    callback_context: CallbackContext,
    llm_response: LlmResponse,
) -> Optional[LlmResponse]:
    """Log model output after generation."""
    if llm_response.content and llm_response.content.parts:
        text = llm_response.content.parts[0].text or ""
        if text.strip():
            logger.info("[%s] MODEL >> %s", callback_context.agent_name, text.strip())
    return None


def validate_user_input(
    callback_context: CallbackContext,
    llm_request: LlmRequest,
) -> Optional[LlmResponse]:
    """Block malicious and out-of-mission prompts before model execution."""
    user_text = _extract_user_text(llm_request)
    lowered = user_text.lower()

    if not user_text:
        return LlmResponse(
            content={
                "role": "model",
                "parts": [{"text": "Please provide a question related to emergency preparedness."}],
            }
        )

    for pattern in MALICIOUS_PATTERNS:
        if pattern in lowered:
            logger.warning("[%s] BLOCKED malicious prompt.", callback_context.agent_name)
            return LlmResponse(
                content={
                    "role": "model",
                    "parts": [{"text": "Request blocked: input violates safety guidelines."}],
                }
            )

    if any(hint in lowered for hint in NON_US_LOCATION_HINTS):
        return LlmResponse(
            content={
                "role": "model",
                "parts": [
                    {
                        "text": (
                            "I can only provide emergency guidance for U.S. locations in this workshop "
                            "environment. Please provide a U.S. city or state."
                        )
                    }
                ],
            }
        )

    # Allow most location-like prompts if they include a US-style state abbreviation.
    has_us_state_abbrev = bool(re.search(r"\b[A-Z]{2}\b", user_text))
    mission_related = any(keyword in lowered for keyword in MISSION_KEYWORDS)
    if not mission_related and not has_us_state_abbrev:
        return LlmResponse(
            content={
                "role": "model",
                "parts": [
                    {
                        "text": (
                            "I am the ReadyNow emergency assistant. Ask about U.S. weather alerts, "
                            "safety guidance, evacuation routes, or disaster updates."
                        )
                    }
                ],
            }
        )

    return None


def chained_before_callback(
    callback_context: CallbackContext,
    llm_request: LlmRequest,
) -> Optional[LlmResponse]:
    """Run prompt validation before standard prompt logging."""
    validation_result = validate_user_input(callback_context, llm_request)
    if validation_result is not None:
        return validation_result
    return log_user_prompt(callback_context, llm_request)
