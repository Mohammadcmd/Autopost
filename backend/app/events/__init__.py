"""Event lookup: matching a photo cluster's time window to a real-world event."""
from __future__ import annotations

from app.config import settings
from app.events.base import EventInfo, EventSource
from app.events.stub_source import StubEventSource
from app.events.website_source import WebsiteApiEventSource

__all__ = ["EventInfo", "EventSource", "StubEventSource", "WebsiteApiEventSource", "get_default_event_source"]


def get_default_event_source() -> EventSource:
    """Prefer the real website once it's configured; fall back to the stub."""
    if settings.events_website_base_url:
        return WebsiteApiEventSource(
            settings.events_website_base_url, settings.events_website_api_key
        )
    return StubEventSource(settings.stub_events_file)
