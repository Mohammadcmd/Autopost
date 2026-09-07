"""Interface for looking up "what event was this" from a time window."""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime


@dataclass(frozen=True)
class EventInfo:
    name: str
    description: str = ""
    location: str = ""
    organizations: list[str] = field(default_factory=list)
    start: datetime | None = None
    end: datetime | None = None


class EventSource(ABC):
    """Resolves a photo cluster's time window to a named real-world event."""

    @abstractmethod
    def find_event(self, start: datetime, end: datetime) -> EventInfo | None:
        """Return the event that overlaps ``[start, end]``, if any."""
        raise NotImplementedError
