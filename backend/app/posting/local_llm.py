"""Client for a locally-running LLM (an Ollama-compatible server) used to
draft captions in the user's own voice.

Staying local here (rather than calling a cloud API) matches the rest of
the pipeline: no photos or event details leave the machine, and it needs no
API key. If no local model is reachable, ``caption.generate_caption`` falls
back to the deterministic template caption — the same "degrade gracefully
when the optional integration isn't configured" pattern used for the
Instagram/Facebook dry-run clients and the events website stub.

To use this, install and run Ollama (https://ollama.com) locally and pull a
model, e.g. ``ollama pull llama3.2``.
"""
from __future__ import annotations

import logging

import requests

from app.posting.style import CaptionStyle

logger = logging.getLogger(__name__)


class LocalLLMUnavailableError(Exception):
    pass


class LocalLLMClient:
    def __init__(self, base_url: str, model: str, *, timeout_seconds: float = 30.0) -> None:
        self._base_url = base_url.rstrip("/")
        self._model = model
        self._timeout_seconds = timeout_seconds

    def generate(self, prompt: str) -> str:
        try:
            response = requests.post(
                f"{self._base_url}/api/generate",
                json={"model": self._model, "prompt": prompt, "stream": False},
                timeout=self._timeout_seconds,
            )
            response.raise_for_status()
        except requests.RequestException as exc:
            raise LocalLLMUnavailableError(f"Local model at {self._base_url} is unreachable") from exc

        text = response.json().get("response", "").strip()
        if not text:
            raise LocalLLMUnavailableError("Local model returned an empty response")
        return text


def build_caption_prompt(
    *,
    style: CaptionStyle,
    event_name: str,
    date_str: str,
    location: str,
    organizations: list[str],
    description: str,
    photo_count: int,
    hashtags: list[str],
) -> str:
    lines = [
        "You are drafting a single Instagram/Facebook caption for a batch of "
        "event photos, written in a specific person's voice.",
        "",
    ]

    if style.tone_notes:
        lines += ["STYLE NOTES (tone and voice only):", style.tone_notes, ""]

    if style.example_captions:
        lines.append(
            "Captions this person likes the STYLE of (reference the tone, "
            "rhythm, and structure only — never copy this text, write "
            "something entirely new):"
        )
        for example in style.example_captions:
            lines.append(f'- "{example}"')
        lines.append("")

    lines += [
        "EVENT DETAILS:",
        f"- Event: {event_name}",
        f"- Date: {date_str}",
    ]
    if location:
        lines.append(f"- Location: {location}")
    if organizations:
        lines.append(f"- Organizations involved: {', '.join(organizations)}")
    if description:
        lines.append(f"- Description: {description}")
    lines.append(f"- Number of photos in this post: {photo_count}")
    lines.append("")

    lines.append("REQUIREMENTS:")
    if location:
        lines.append(f"- Mention the location ({location}) by name.")
    for org in organizations:
        lines.append(f"- Mention {org} by name.")
    if hashtags:
        lines.append(f"- End the caption with exactly these hashtags: {' '.join(hashtags)}")
    lines += [
        "- Write ONE original caption, 2-4 short sentences.",
        "- Do not wrap the caption in quotation marks.",
        "- Do not explain what you're doing, output only the caption itself.",
        "",
        "Caption:",
    ]

    return "\n".join(lines)
