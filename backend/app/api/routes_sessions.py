"""Trigger and list import sessions (the detected "event" for a device)."""
from __future__ import annotations

from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict
from sqlalchemy.orm import Session

from app.db.models import ImportSession
from app.db.session import get_session
from app.ingest.service import NoEventFoundError, ingest_path

router = APIRouter(prefix="/api/sessions", tags=["sessions"])


class ScanRequest(BaseModel):
    path: str


class EventSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    event_date: str
    photo_count: int
    website_event_name: str | None
    post_status: str


class SessionSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    source_path: str
    created_at: datetime
    events: list[EventSummary]


@router.post("/scan", response_model=SessionSummary)
def scan_path(request: ScanRequest, db: Session = Depends(get_session)) -> SessionSummary:
    """Manually trigger a scan of a path, exactly as the storage watcher
    would for a freshly-inserted card. This is what makes the whole pipeline
    testable without real hardware."""
    root = Path(request.path)
    if not root.exists():
        raise HTTPException(status_code=404, detail=f"Path not found: {root}")

    try:
        return ingest_path(root, db)
    except NoEventFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("", response_model=list[SessionSummary])
def list_sessions(db: Session = Depends(get_session)) -> list[SessionSummary]:
    return db.query(ImportSession).order_by(ImportSession.created_at.desc()).all()
