"""Read capture timestamps out of image files."""
from __future__ import annotations

from datetime import datetime
from pathlib import Path

from PIL import ExifTags, Image

_DATETIME_TAGS = {"DateTimeOriginal", "DateTimeDigitized", "DateTime"}
_TAG_ID_BY_NAME = {v: k for k, v in ExifTags.TAGS.items()}


def read_capture_datetime(path: str | Path) -> datetime:
    """Return the best-known capture time for an image.

    Falls back to the file's modification time when no EXIF timestamp is
    present (e.g. screenshots, PNGs, or stripped-metadata files).
    """
    path = Path(path)
    try:
        with Image.open(path) as img:
            exif = img.getexif()
            for tag_name in _DATETIME_TAGS:
                tag_id = _TAG_ID_BY_NAME.get(tag_name)
                if tag_id is not None and tag_id in exif:
                    raw = exif[tag_id]
                    parsed = _parse_exif_datetime(raw)
                    if parsed is not None:
                        return parsed
    except Exception:
        pass
    return datetime.fromtimestamp(path.stat().st_mtime)


def _parse_exif_datetime(raw: str) -> datetime | None:
    # EXIF datetimes look like "2024:07:04 13:05:22"
    try:
        return datetime.strptime(raw, "%Y:%m:%d %H:%M:%S")
    except (ValueError, TypeError):
        return None
