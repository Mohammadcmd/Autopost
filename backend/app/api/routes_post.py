"""Caption draft + the final "publish this event" action."""
from __future__ import annotations

import json
from datetime import date as date_type

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.config import settings
from app.db.models import Decision, Event, PostRecord, PostStatus
from app.db.session import get_session
from app.posting.facebook import FacebookClient
from app.posting.instagram import InstagramClient

router = APIRouter(prefix="/api/events", tags=["post"])


class CaptionOut(BaseModel):
    caption: str
    kept_photo_count: int


class CaptionUpdateRequest(BaseModel):
    caption: str


class PostResult(BaseModel):
    dry_run: bool
    instagram: dict
    facebook: dict


def _kept_photos(event: Event) -> list:
    return [p for p in event.photos if p.decision == Decision.KEEP]


@router.get("/{event_id}/caption", response_model=CaptionOut)
def get_caption(event_id: int, db: Session = Depends(get_session)) -> CaptionOut:
    event = db.get(Event, event_id)
    if event is None:
        raise HTTPException(status_code=404, detail="Event not found")
    return CaptionOut(caption=event.caption_draft or "", kept_photo_count=len(_kept_photos(event)))


@router.put("/{event_id}/caption", response_model=CaptionOut)
def update_caption(
    event_id: int, request: CaptionUpdateRequest, db: Session = Depends(get_session)
) -> CaptionOut:
    event = db.get(Event, event_id)
    if event is None:
        raise HTTPException(status_code=404, detail="Event not found")
    event.caption_draft = request.caption
    db.commit()
    return CaptionOut(caption=event.caption_draft, kept_photo_count=len(_kept_photos(event)))


@router.post("/{event_id}/post", response_model=PostResult)
def post_event(event_id: int, db: Session = Depends(get_session)) -> PostResult:
    event = db.get(Event, event_id)
    if event is None:
        raise HTTPException(status_code=404, detail="Event not found")

    kept = _kept_photos(event)
    if not kept:
        raise HTTPException(status_code=400, detail="No kept photos to post")

    caption = event.caption_draft or ""
    event_date = date_type.fromisoformat(event.event_date)

    instagram = InstagramClient(settings.meta_access_token, settings.ig_business_account_id)
    image_urls = [
        f"{settings.public_base_url}/api/photos/{p.id}/image" for p in kept
    ] if settings.public_base_url else [f"<no PUBLIC_BASE_URL configured for photo {p.id}>" for p in kept]
    instagram_result = instagram.create_post(image_urls, caption)

    facebook = FacebookClient(settings.meta_access_token, settings.meta_page_id)
    album_name = event.website_event_name or f"Event on {event.event_date}"
    facebook_result = facebook.post_album(album_name, [p.edited_path for p in kept], caption)

    dry_run = instagram.dry_run or facebook.dry_run
    event.post_status = PostStatus.DRY_RUN if dry_run else PostStatus.POSTED

    db.add(
        PostRecord(
            event_id=event.id,
            platform="instagram",
            dry_run=instagram.dry_run,
            status="dry_run" if instagram.dry_run else "posted",
            payload_json=json.dumps(instagram_result),
        )
    )
    db.add(
        PostRecord(
            event_id=event.id,
            platform="facebook",
            dry_run=facebook.dry_run,
            status="dry_run" if facebook.dry_run else "posted",
            payload_json=json.dumps(facebook_result),
        )
    )
    db.commit()

    return PostResult(dry_run=dry_run, instagram=instagram_result, facebook=facebook_result)
