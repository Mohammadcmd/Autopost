"""Pulls this account's OWN past Instagram captions via the Graph API, to
use as real style examples for the local caption model.

This is not scraping: it reads captions from the same Instagram Business
account this app is authorized to post to, using the same access token —
exactly what the Graph API's media endpoint is for. It cannot, and does
not attempt to, read any other account's posts.
"""
from __future__ import annotations

import logging

import requests

logger = logging.getLogger(__name__)


class StyleImportError(Exception):
    pass


def fetch_own_captions(
    access_token: str,
    ig_business_account_id: str,
    *,
    graph_api_base_url: str,
    limit: int = 30,
    timeout_seconds: float = 15.0,
) -> list[str]:
    """Return up to ``limit`` captions from this account's own past media,
    most recent first."""
    if not access_token or not ig_business_account_id:
        raise StyleImportError(
            "Instagram isn't configured yet (META_ACCESS_TOKEN / IG_BUSINESS_ACCOUNT_ID) — "
            "nothing to import from."
        )

    captions: list[str] = []
    url: str | None = f"{graph_api_base_url}/{ig_business_account_id}/media"
    params: dict[str, str | int] | None = {
        "fields": "caption",
        "limit": min(limit, 100),
        "access_token": access_token,
    }

    try:
        while url and len(captions) < limit:
            response = requests.get(url, params=params, timeout=timeout_seconds)
            response.raise_for_status()
            payload = response.json()

            for item in payload.get("data", []):
                caption = item.get("caption")
                if caption:
                    captions.append(caption)
                if len(captions) >= limit:
                    break

            # The "next" paging URL already carries every query param it needs.
            url = payload.get("paging", {}).get("next")
            params = None
    except requests.RequestException as exc:
        raise StyleImportError(f"Failed to fetch captions from Instagram: {exc}") from exc

    return captions
