"""FastAPI frontend for testing a deployed ReadyNow agent."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple
import os

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

import vertexai
from vertexai import agent_engines


def get_remote_agent(resource_name: str, project_id: str, location: str) -> Any:
    """Fetch an already deployed Agent Engine by full resource name."""
    client = vertexai.Client(project=project_id, location=location)

    # SDK surfaces can vary across versions, so use guarded fallbacks.
    if hasattr(client, "agent_engines") and hasattr(client.agent_engines, "get"):
        return client.agent_engines.get(resource_name)

    if hasattr(agent_engines, "get"):
        return agent_engines.get(resource_name)

    raise RuntimeError("Current SDK version does not expose an agent engine get() method.")


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
        session = remote_agent.create_session(user_id=user_id)
        session_id = session["id"] if isinstance(session, dict) else session.id

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


class ChatRequest(BaseModel):
    message: str
    user_id: str = "frontend-user"


app = FastAPI(title="ReadyNow Frontend", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

STATIC_DIR = Path(__file__).resolve().parent / "static"
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


def _load_remote_agent():
    project_id = os.getenv("GOOGLE_CLOUD_PROJECT", "").strip()
    location = os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1").strip() or "us-central1"
    resource_name = os.getenv("AGENT_ENGINE_RESOURCE_NAME", "").strip()

    if not project_id:
        raise ValueError("GOOGLE_CLOUD_PROJECT is required.")
    if not resource_name:
        raise ValueError("AGENT_ENGINE_RESOURCE_NAME is required.")

    return get_remote_agent(resource_name=resource_name, project_id=project_id, location=location)


@app.get("/")
def index() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/healthz")
def healthz() -> dict:
    return {"ok": True}


@app.post("/api/chat")
def chat(request: ChatRequest):
    if not request.message.strip():
        raise HTTPException(status_code=400, detail="message must be non-empty")

    try:
        remote_agent = _load_remote_agent()
        final_text, events = stream_remote_query(
            remote_agent=remote_agent,
            message=request.message.strip(),
            user_id=request.user_id.strip() or "frontend-user",
        )
    except Exception as exc:  # pragma: no cover - runtime environment dependent
        raise HTTPException(status_code=500, detail=f"Agent query failed: {exc}") from exc

    return {
        "answer": final_text,
        "authors": list_authors(events),
        "event_count": len(events),
    }
