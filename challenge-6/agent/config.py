"""Runtime configuration helpers for Challenge 6."""

from __future__ import annotations

from dataclasses import dataclass
import os


DEFAULT_LOCATION = "us-central1"
DEFAULT_MODEL = "gemini-2.5-flash"


@dataclass(frozen=True)
class RuntimeConfig:
    project_id: str
    location: str
    model: str
    maps_api_key: str
    model_armor_template_id: str
    model_armor_project_id: str
    model_armor_location: str


def load_runtime_config() -> RuntimeConfig:
    """Load required runtime settings from environment variables."""
    project_id = os.getenv("GOOGLE_CLOUD_PROJECT", "").strip()
    location = os.getenv("GOOGLE_CLOUD_LOCATION", DEFAULT_LOCATION).strip() or DEFAULT_LOCATION
    model = os.getenv("GEMINI_MODEL", DEFAULT_MODEL).strip() or DEFAULT_MODEL
    maps_api_key = os.getenv("GOOGLE_MAPS_API_KEY", "").strip()
    model_armor_template_id = os.getenv("MODEL_ARMOR_TEMPLATE_ID", "").strip()
    model_armor_project_id = os.getenv("MODEL_ARMOR_PROJECT_ID", project_id).strip() or project_id
    model_armor_location = os.getenv("MODEL_ARMOR_LOCATION", location).strip() or location

    return RuntimeConfig(
        project_id=project_id,
        location=location,
        model=model,
        maps_api_key=maps_api_key,
        model_armor_template_id=model_armor_template_id,
        model_armor_project_id=model_armor_project_id,
        model_armor_location=model_armor_location,
    )
