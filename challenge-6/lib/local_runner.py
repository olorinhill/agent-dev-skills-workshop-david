"""Helpers for local ADK execution inside notebooks or scripts."""

from __future__ import annotations

from typing import Any, Dict, Iterable, List, Tuple

from vertexai.preview import reasoning_engines


def make_local_app(agent: Any, enable_tracing: bool = False) -> reasoning_engines.AdkApp:
    """Create a local ADK app wrapper."""
    return reasoning_engines.AdkApp(agent=agent, enable_tracing=enable_tracing)


def _extract_text(event: Dict[str, Any]) -> str:
    content = event.get("content") or {}
    parts = content.get("parts") or []
    if not parts:
        return ""
    return str(parts[0].get("text") or "").strip()


def stream_local_query(
    app: reasoning_engines.AdkApp,
    message: str,
    user_id: str = "student",
    session_id: str | None = None,
) -> Tuple[str, List[Dict[str, Any]]]:
    """Run a local query and return the final text plus all events."""
    if session_id is None:
        session = app.create_session(user_id=user_id)
        session_id = session["id"] if isinstance(session, dict) else session.id

    events: List[Dict[str, Any]] = []
    final_text = ""
    for event in app.stream_query(user_id=user_id, session_id=session_id, message=message):
        events.append(event)
        text = _extract_text(event)
        if text:
            final_text = text

    return final_text, events


def list_authors(events: Iterable[Dict[str, Any]]) -> List[str]:
    """Collect unique event author names in order."""
    ordered: List[str] = []
    for event in events:
        author = str(event.get("author") or "").strip()
        if author and author not in ordered:
            ordered.append(author)
    return ordered
