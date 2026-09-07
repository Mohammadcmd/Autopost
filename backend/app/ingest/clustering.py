"""Group photos from a storage device into a single "event".

Strategy:
1. Walk every image under the source path and read its capture timestamp.
2. Group photos by calendar date. Starting from the most recent date present
   (or "today" if scanning live media), walk backward day by day until a date
   with at least ``min_photos`` photos is found.
3. Within that day, split photos into bursts using a time-gap threshold, so
   two unrelated events on the same day aren't merged. The largest burst is
   treated as "the event".
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta
from pathlib import Path

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".heic", ".heif", ".tif", ".tiff", ".raw", ".cr2", ".nef", ".arw"}


@dataclass(frozen=True)
class TimestampedPhoto:
    path: str
    captured_at: datetime


def find_images(root: str | Path) -> list[Path]:
    root = Path(root)
    if not root.exists():
        return []
    return sorted(
        p for p in root.rglob("*") if p.is_file() and p.suffix.lower() in IMAGE_EXTENSIONS
    )


def group_by_date(photos: list[TimestampedPhoto]) -> dict[date, list[TimestampedPhoto]]:
    groups: dict[date, list[TimestampedPhoto]] = {}
    for photo in photos:
        groups.setdefault(photo.captured_at.date(), []).append(photo)
    for day_photos in groups.values():
        day_photos.sort(key=lambda p: p.captured_at)
    return groups


def find_event_day(
    photos: list[TimestampedPhoto],
    *,
    start_date: date | None = None,
    min_photos: int = 1,
    max_lookback_days: int = 365,
) -> tuple[date, list[TimestampedPhoto]] | None:
    """Return the most recent date (walking backward) with enough photos."""
    groups = group_by_date(photos)
    if not groups:
        return None

    if start_date is None:
        start_date = max(groups.keys())

    for offset in range(max_lookback_days + 1):
        day = start_date - timedelta(days=offset)
        day_photos = groups.get(day, [])
        if len(day_photos) >= min_photos:
            return day, day_photos

    return None


def split_into_bursts(
    day_photos: list[TimestampedPhoto], *, gap_minutes: float = 45
) -> list[list[TimestampedPhoto]]:
    """Split a day's photos into bursts separated by a time gap."""
    if not day_photos:
        return []

    ordered = sorted(day_photos, key=lambda p: p.captured_at)
    bursts: list[list[TimestampedPhoto]] = [[ordered[0]]]
    gap = timedelta(minutes=gap_minutes)

    for prev, current in zip(ordered, ordered[1:]):
        if current.captured_at - prev.captured_at > gap:
            bursts.append([])
        bursts[-1].append(current)

    return bursts


def choose_primary_burst(
    bursts: list[list[TimestampedPhoto]],
) -> list[TimestampedPhoto]:
    """Pick the largest burst as "the event" photos."""
    if not bursts:
        return []
    return max(bursts, key=len)


def detect_event(
    root: str | Path,
    *,
    start_date: date | None = None,
    min_photos: int = 1,
    max_lookback_days: int = 365,
    gap_minutes: float = 45,
) -> list[TimestampedPhoto]:
    """End-to-end helper: scan a path and return the detected event's photos."""
    from app.ingest.exif import read_capture_datetime

    image_paths = find_images(root)
    photos = [
        TimestampedPhoto(path=str(p), captured_at=read_capture_datetime(p))
        for p in image_paths
    ]

    result = find_event_day(
        photos,
        start_date=start_date,
        min_photos=min_photos,
        max_lookback_days=max_lookback_days,
    )
    if result is None:
        return []

    _day, day_photos = result
    bursts = split_into_bursts(day_photos, gap_minutes=gap_minutes)
    return choose_primary_burst(bursts)
