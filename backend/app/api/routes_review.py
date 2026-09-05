"""Swipe-review endpoints: list photos for an event, serve edited images,
and record keep/delete decisions."""
from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel, ConfigDict
from sqlalchemy.orm import Session

from app.db.models import Decision, Event, Photo
from app.db.session import get_session

router = APIRouter(prefix="/api", tags=["review"])


class PhotoOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    captured_at: datetime
    decision: Decision


class DecisionRequest(BaseModel):
    decision: Decision


@router.get("/events/{event_id}/photos", response_model=list[PhotoOut])
def list_photos(event_id: int, db: Session = Depends(get_session)) -> list[PhotoOut]:
    event = db.get(Event, event_id)
    if event is None:
        raise HTTPException(status_code=404, detail="Event not found")
    return event.photos


@router.get("/photos/{photo_id}/image")
def get_photo_image(photo_id: int, db: Session = Depends(get_session)) -> FileResponse:
    photo = db.get(Photo, photo_id)
    if photo is None or not photo.edited_path:
        raise HTTPException(status_code=404, detail="Photo not found")
    return FileResponse(photo.edited_path)


@router.post("/photos/{photo_id}/decision", response_model=PhotoOut)
def set_decision(
    photo_id: int, request: DecisionRequest, db: Session = Depends(get_session)
) -> PhotoOut:
    photo = db.get(Photo, photo_id)
    if photo is None:
        raise HTTPException(status_code=404, detail="Photo not found")
    photo.decision = request.decision
    db.commit()
    db.refresh(photo)
    return photo
