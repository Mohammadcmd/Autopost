"""Draft a caption for the post from the matched event + photo info."""
from __future__ import annotations

from datetime import date

from app.events.base import EventInfo


def generate_caption(event: EventInfo | None, event_date: date, photo_count: int) -> str:
    date_str = event_date.strftime("%B %-d, %Y") if hasattr(event_date, "strftime") else str(event_date)

    if event is None:
        return (
            f"Photos from {date_str}. \N{CAMERA}\n\n"
            f"{photo_count} moments from the day \N{BLACK HEART}"
        )

    lines = [f"{event.name} \N{SPARKLES}"]
    if event.location:
        lines.append(f"\N{ROUND PUSHPIN} {event.location}")
    lines.append(date_str)
    if event.description:
        lines.append("")
        lines.append(event.description)
    lines.append("")
    lines.append(f"{photo_count} favorite moments from the day \N{BLACK HEART}")

    return "\n".join(lines)
