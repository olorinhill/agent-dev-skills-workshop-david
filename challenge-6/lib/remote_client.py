"""Utilities for deployed Agent Engine interactions."""

from __future__ import annotations

from typing import Any, Dict, Iterable, List, Sequence, Tuple
import os

import vertexai
from vertexai import agent_engines


DEFAULT_REQUIREMENTS = [
    "google-cloud-aiplatform[agent_engines,adk]==1.148.1",
    "google-adk==1.18.0",
    "requests==2.32.3",
]


def get_remote_agent(
    resource_name: str,
    project_id: str,
    location: str,
) -> Any:
    """Fetch an already deployed Agent Engine by full resource name."""
    client = vertexai.Client(project=project_id, location=location)

    # SDK surfaces can vary across versions, so use guarded fallbacks.
    if hasattr(client, "agent_engines") and hasattr(client.agent_engines, "get"):
        return client.agent_engines.get(resource_name)

    if hasattr(agent_engines, "get"):
        return agent_engines.get(resource_name)

    raise RuntimeError("Current SDK version does not expose an agent engine get() method.")


def deploy_agent(
    root_agent: Any,
    project_id: str,
    location: str,
    staging_bucket: str,
    display_name: str = "readynow-emergency-assistant",
    description: str = "Challenge 6 FEMA ReadyNow emergency preparedness assistant.",
    requirements: Sequence[str] | None = None,
) -> Any:
    """Deploy a local ADK agent to Vertex AI Agent Engine."""
    client = vertexai.Client(project=project_id, location=location)
    app = agent_engines.AdkApp(agent=root_agent, enable_tracing=True)
    deployment = client.agent_engines.create(
        agent=app,
        config={
            "display_name": display_name,
            "description": description,
            "requirements": list(requirements or DEFAULT_REQUIREMENTS),
            "staging_bucket": staging_bucket,
        },
    )
    return deployment


def create_remote_session(remote_agent: Any, user_id: str) -> str:
    """Create a remote session and normalize dict/object response variants."""
    session = remote_agent.create_session(user_id=user_id)
    return session["id"] if isinstance(session, dict) else session.id


def _extract_text(event: Dict[str, Any]) -> str:
    content = event.get("content") or {}
    parts = content.get("parts") or []
    if not parts:
        return ""
    return str(parts[0].get("text") or "").strip()


def stream_remote_query(
    remote_agent: Any,
    message: str,
    user_id: str = "student",
    session_id: str | None = None,
) -> Tuple[str, List[Dict[str, Any]]]:
    """Stream a query to a deployed agent and return final text plus full events."""
    if session_id is None:
        session_id = create_remote_session(remote_agent, user_id=user_id)

    events: List[Dict[str, Any]] = []
    final_text = ""
    for event in remote_agent.stream_query(
        user_id=user_id,
        session_id=session_id,
        message=message,
    ):
        events.append(event)
        text = _extract_text(event)
        if text:
            final_text = text
    return final_text, events


def list_authors(events: Iterable[Dict[str, Any]]) -> List[str]:
    """Collect unique event authors in appearance order."""
    ordered: List[str] = []
    for event in events:
        author = str(event.get("author") or "").strip()
        if author and author not in ordered:
            ordered.append(author)
    return ordered


def env_required(name: str) -> str:
    """Read a required environment variable or raise a clear error."""
    value = os.getenv(name, "").strip()
    if not value:
        raise ValueError(f"Missing required environment variable: {name}")
    return value
