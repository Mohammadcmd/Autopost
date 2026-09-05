"""HTTP client skeleton for the real events website's API.

The website's actual API contract isn't defined yet, so this assumes a
plausible shape (``GET {base_url}/api/events?start=...&end=...`` returning a
JSON list shaped like ``sample_events.json``) and is written to fail soft:
any network or shape problem just means "no match", the same as
``StubEventSource`` finding nothing. Once the real contract is known, only
``_parse_response`` and the request URL/params should need to change.
"""
from __future__ import annotations

import logging
from datetime import datetime

import requests

from app.events.base import EventInfo, EventSource

logger = logging.getLogger(__name__)


class WebsiteApiEventSource(EventSource):
    def __init__(self, base_url: str, api_key: str = "", *, timeout_seconds: float = 5.0) -> None:
        self._base_url = base_url.rstrip("/")
        self._api_key = api_key
        self._timeout_seconds = timeout_seconds

    def find_event(self, start: datetime, end: datetime) -> EventInfo | None:
        if not self._base_url:
            return None

        headers = {"Authorization": f"Bearer {self._api_key}"} if self._api_key else {}
        params = {"start": start.isoformat(), "end": end.isoformat()}

        try:
            response = requests.get(
                f"{self._base_url}/api/events",
                params=params,
                headers=headers,
                timeout=self._timeout_seconds,
            )
            response.raise_for_status()
            return self._parse_response(response.json())
        except requests.RequestException:
            logger.warning("Events website lookup failed; continuing without a match", exc_info=True)
            return None

    def _parse_response(self, payload: list[dict]) -> EventInfo | None:
        if not payload:
            return None
        best = payload[0]
        return EventInfo(
            name=best.get("name", "Untitled Event"),
            description=best.get("description", ""),
            location=best.get("location", ""),
            start=datetime.fromisoformat(best["start"]) if best.get("start") else None,
            end=datetime.fromisoformat(best["end"]) if best.get("end") else None,
        )
