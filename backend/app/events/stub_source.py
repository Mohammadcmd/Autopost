"""A local, file-backed EventSource used until the real website API exists."""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from app.events.base import EventInfo, EventSource


class StubEventSource(EventSource):
    """Matches a time window against events listed in a local JSON file.

    The JSON file is a list of objects: ``name``, ``description``,
    ``location``, ``start`` (ISO 8601), ``end`` (ISO 8601). This keeps the
    rest of the pipeline (caption drafting, the review UI) fully testable
    before the real events website's API contract is known.
    """

    def __init__(self, events_file: str | Path) -> None:
        self._events_file = Path(events_file)

    def _load_events(self) -> list[dict]:
        if not self._events_file.exists():
            return []
        with self._events_file.open() as f:
            return json.load(f)

    def find_event(self, start: datetime, end: datetime) -> EventInfo | None:
        best_match: EventInfo | None = None
        best_overlap = 0.0

        for raw in self._load_events():
            event_start = datetime.fromisoformat(raw["start"])
            event_end = datetime.fromisoformat(raw["end"])

            overlap_start = max(start, event_start)
            overlap_end = min(end, event_end)
            overlap_seconds = (overlap_end - overlap_start).total_seconds()

            if overlap_seconds > best_overlap:
                best_overlap = overlap_seconds
                best_match = EventInfo(
                    name=raw["name"],
                    description=raw.get("description", ""),
                    location=raw.get("location", ""),
                    start=event_start,
                    end=event_end,
                )

        return best_match if best_overlap > 0 else None
