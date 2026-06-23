"""FastAPI frontend for testing a deployed ReadyNow agent."""

from __future__ import annotations

from pathlib import Path
import os
import sys

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from lib.remote_client import get_remote_agent, list_authors, stream_remote_query  # noqa: E402


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
