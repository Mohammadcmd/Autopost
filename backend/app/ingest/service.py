"""Shared "ingest one newly-seen path" logic, used by both the manual scan
API endpoint and the background StorageWatcher so there's exactly one
implementation of the detect -> cluster -> edit -> match pipeline."""
from __future__ import annotations

import logging
from pathlib import Path

from sqlalchemy.orm import Session

from app.config import settings
from app.db.models import Event, ImportSession, Photo
from app.editing.pipeline import EditingPipeline
from app.events import get_default_event_source
from app.ingest.clustering import (
    TimestampedPhoto,
    choose_primary_burst,
    find_event_day,
    find_images,
    split_into_bursts,
)
from app.ingest.exif import read_capture_datetime
from app.posting.caption import generate_caption
from app.posting.local_llm import LocalLLMClient
from app.posting.style import CaptionStyle

logger = logging.getLogger(__name__)

_pipeline = EditingPipeline()


class NoEventFoundError(Exception):
    pass


def ingest_path(root: str | Path, db: Session) -> ImportSession:
    """Scan ``root`` for the most recent burst of photos worth calling an
    event, edit them, try to match them to a real-world event, and persist
    everything. Raises ``NoEventFoundError`` if nothing usable is found."""
    root = Path(root)
    images = find_images(root)
    photos = [
        TimestampedPhoto(path=str(p), captured_at=read_capture_datetime(p)) for p in images
    ]

    result = find_event_day(
        photos,
        min_photos=settings.min_photos_per_event,
        max_lookback_days=settings.max_lookback_days,
    )
    if result is None:
        raise NoEventFoundError(f"No photos found under {root}")

    event_date, day_photos = result
    bursts = split_into_bursts(day_photos, gap_minutes=settings.burst_gap_minutes)
    event_photos = choose_primary_burst(bursts)

    session = ImportSession(source_path=str(root))
    db.add(session)
    db.flush()

    event = Event(
        session_id=session.id,
        event_date=event_date.isoformat(),
        start_time=event_photos[0].captured_at,
        end_time=event_photos[-1].captured_at,
    )
    db.add(event)
    db.flush()

    event_source = get_default_event_source()
    website_event = event_source.find_event(event.start_time, event.end_time)
    if website_event:
        event.website_event_name = website_event.name
        event.website_event_description = website_event.description
        event.website_event_location = website_event.location
        event.website_event_organizations = website_event.organizations

    media_dir = settings.media_dir / f"session_{session.id}" / f"event_{event.id}"
    for tp in event_photos:
        dest = media_dir / Path(tp.path).name
        try:
            _pipeline.process_file(tp.path, dest)
        except Exception:
            logger.exception("Failed to edit photo %s; skipping it", tp.path)
            continue
        db.add(
            Photo(
                event_id=event.id,
                original_path=tp.path,
                edited_path=str(dest),
                captured_at=tp.captured_at,
            )
        )

    event.caption_draft = generate_caption(
        website_event,
        event_date,
        len(event_photos),
        organizations=website_event.organizations if website_event else [],
        hashtags=settings.caption_hashtags,
        style=CaptionStyle.load(settings.caption_style_file),
        llm=LocalLLMClient(settings.local_llm_base_url, settings.local_llm_model),
    )

    db.commit()
    db.refresh(session)
    return session
