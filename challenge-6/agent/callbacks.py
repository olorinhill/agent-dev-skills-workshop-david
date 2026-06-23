"""ADK callback functions for logging and Model Armor-backed validation."""

from __future__ import annotations

from functools import lru_cache
from typing import Optional
import logging
import os
import re

from google.adk.agents.callback_context import CallbackContext
from google.adk.models import LlmRequest, LlmResponse
from google.api_core.client_options import ClientOptions
from google.cloud import modelarmor_v1


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


@lru_cache(maxsize=4)
def _get_model_armor_client(location: str) -> modelarmor_v1.ModelArmorClient:
    return modelarmor_v1.ModelArmorClient(
        transport="rest",
        client_options=ClientOptions(api_endpoint=f"modelarmor.{location}.rep.googleapis.com"),
    )


def _build_model_armor_template_name() -> str:
    template_value = os.getenv("MODEL_ARMOR_TEMPLATE_ID", "").strip()
    if not template_value:
        raise ValueError("MODEL_ARMOR_TEMPLATE_ID is missing.")
    if template_value.startswith("projects/"):
        return template_value

    project_id = os.getenv("MODEL_ARMOR_PROJECT_ID", os.getenv("GOOGLE_CLOUD_PROJECT", "")).strip()
    location = os.getenv("MODEL_ARMOR_LOCATION", os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1")).strip()
    if not project_id:
        raise ValueError("GOOGLE_CLOUD_PROJECT (or MODEL_ARMOR_PROJECT_ID) is missing.")
    if not location:
        raise ValueError("GOOGLE_CLOUD_LOCATION (or MODEL_ARMOR_LOCATION) is missing.")
    return f"projects/{project_id}/locations/{location}/templates/{template_value}"


def _is_model_armor_match_found(filter_match_state: object) -> bool:
    # Some SDK/runtime combinations expose enums as integers, others as enum names.
    try:
        if int(filter_match_state) == 2:
            return True
    except (TypeError, ValueError):
        pass

    state_str = str(filter_match_state).upper()
    return "MATCH_FOUND" in state_str and "NO_MATCH_FOUND" not in state_str


def _sanitize_with_model_armor(user_text: str) -> Optional[LlmResponse]:
    template_name = _build_model_armor_template_name()
    location = template_name.split("/")[3]
    client = _get_model_armor_client(location)

    request = modelarmor_v1.SanitizeUserPromptRequest(
        name=template_name,
        user_prompt_data=modelarmor_v1.DataItem(text=user_text),
    )
    response = client.sanitize_user_prompt(request=request)
    result = response.sanitization_result
    if _is_model_armor_match_found(result.filter_match_state):
        logger.warning("Blocked by Model Armor policy. match_state=%s", result.filter_match_state)
        return LlmResponse(
            content={
                "role": "model",
                "parts": [{"text": "Request blocked by Model Armor safety policy."}],
            }
        )
    return None


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
    """Block unsafe and out-of-mission prompts before model execution."""
    user_text = _extract_user_text(llm_request)
    lowered = user_text.lower()

    if not user_text:
        return LlmResponse(
            content={
                "role": "model",
                "parts": [{"text": "Please provide a question related to emergency preparedness."}],
            }
        )

    try:
        model_armor_result = _sanitize_with_model_armor(user_text)
    except Exception as exc:  # pragma: no cover - depends on cloud service/runtime
        logger.exception("[%s] Model Armor validation failed: %s", callback_context.agent_name, exc)
        return LlmResponse(
            content={
                "role": "model",
                "parts": [
                    {
                        "text": (
                            "Request blocked: Model Armor safety validation is temporarily unavailable. "
                            "Please try again later."
                        )
                    }
                ],
            }
        )

    if model_armor_result is not None:
        return model_armor_result

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
