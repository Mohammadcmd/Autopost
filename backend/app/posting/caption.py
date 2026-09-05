"""Draft a caption for the post from the matched event + photo info.

Tries the local AI model first (see ``local_llm.py``) so captions read in
the user's own voice; falls back to a deterministic template if no local
model is reachable. Either way, the hard requirements (hashtags, location,
organizations) are enforced afterward rather than trusted to the model,
since a small local model won't always follow instructions exactly.
"""
from __future__ import annotations

import logging
from datetime import date

from app.events.base import EventInfo
from app.posting.local_llm import LocalLLMClient, LocalLLMUnavailableError, build_caption_prompt
from app.posting.style import CaptionStyle

logger = logging.getLogger(__name__)


def generate_caption(
    event: EventInfo | None,
    event_date: date,
    photo_count: int,
    *,
    organizations: list[str] | None = None,
    hashtags: list[str] | None = None,
    style: CaptionStyle | None = None,
    llm: LocalLLMClient | None = None,
) -> str:
    organizations = organizations if organizations is not None else (event.organizations if event else [])
    hashtags = hashtags or []
    date_str = _format_date(event_date)
    location = event.location if event else ""

    caption = None
    if llm is not None:
        prompt = build_caption_prompt(
            style=style or CaptionStyle(),
            event_name=event.name if event else f"Photos from {date_str}",
            date_str=date_str,
            location=location,
            organizations=organizations,
            description=event.description if event else "",
            photo_count=photo_count,
            hashtags=hashtags,
        )
        try:
            caption = llm.generate(prompt)
        except LocalLLMUnavailableError:
            logger.info("Local caption model unavailable; falling back to the template caption")

    if caption is None:
        caption = generate_template_caption(event, event_date, photo_count, organizations=organizations)

    return _enforce_requirements(caption, location=location, organizations=organizations, hashtags=hashtags)


def generate_template_caption(
    event: EventInfo | None, event_date: date, photo_count: int, *, organizations: list[str] | None = None
) -> str:
    organizations = organizations if organizations is not None else (event.organizations if event else [])
    date_str = _format_date(event_date)

    if event is None:
        lines = [f"Photos from {date_str}. \N{CAMERA}", "", f"{photo_count} moments from the day \N{BLACK HEART}"]
        return "\n".join(lines)

    lines = [f"{event.name} \N{SPARKLES}"]
    if event.location:
        lines.append(f"\N{ROUND PUSHPIN} {event.location}")
    lines.append(date_str)
    if event.description:
        lines.append("")
        lines.append(event.description)
    if organizations:
        lines.append("")
        lines.append(f"With thanks to {_join_names(organizations)} \N{PERSON WITH FOLDED HANDS}")
    lines.append("")
    lines.append(f"{photo_count} favorite moments from the day \N{BLACK HEART}")

    return "\n".join(lines)


def _enforce_requirements(caption: str, *, location: str, organizations: list[str], hashtags: list[str]) -> str:
    caption = caption.strip().strip('"')
    lower_caption = caption.lower()
    added_lines = []

    if location and location.lower() not in lower_caption:
        added_lines.append(f"\N{ROUND PUSHPIN} {location}")

    missing_orgs = [org for org in organizations if org.lower() not in lower_caption]
    if missing_orgs:
        added_lines.append(f"With thanks to {_join_names(missing_orgs)} \N{PERSON WITH FOLDED HANDS}")

    if added_lines:
        caption = caption + "\n\n" + "\n".join(added_lines)

    missing_hashtags = [tag for tag in hashtags if tag.lower() not in caption.lower()]
    if missing_hashtags:
        caption = caption + "\n\n" + " ".join(missing_hashtags)

    return caption


def _join_names(names: list[str]) -> str:
    if len(names) == 1:
        return names[0]
    return ", ".join(names[:-1]) + f" and {names[-1]}"


def _format_date(event_date: date) -> str:
    return event_date.strftime("%B %-d, %Y") if hasattr(event_date, "strftime") else str(event_date)
