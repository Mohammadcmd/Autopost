"""Instagram Graph API client (Content Publishing API).

Important constraint: the Graph API's media container endpoint takes an
``image_url`` that Instagram's servers fetch themselves — it does not accept
a raw file upload. That means each kept photo must be reachable at a public
URL before a real (non-dry-run) post can be created; ``image_urls`` is
expected to already be built from ``settings.public_base_url`` by the
caller. Until that's configured, or until ``META_ACCESS_TOKEN`` /
``IG_BUSINESS_ACCOUNT_ID`` are set, this client runs in dry-run mode: it
builds and returns the exact requests it would have made instead of sending
them.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

import requests

logger = logging.getLogger(__name__)


@dataclass
class InstagramClient:
    access_token: str
    ig_business_account_id: str
    graph_api_base_url: str = "https://graph.facebook.com/v19.0"
    dry_run: bool = field(init=False)

    def __post_init__(self) -> None:
        self.dry_run = not (self.access_token and self.ig_business_account_id)

    def create_post(self, image_urls: list[str], caption: str) -> dict[str, Any]:
        """Publish a single photo, or a carousel for multiple photos."""
        if not image_urls:
            raise ValueError("At least one image_url is required")

        if len(image_urls) == 1:
            return self._create_single_photo_post(image_urls[0], caption)
        return self._create_carousel_post(image_urls, caption)

    # -- single photo -----------------------------------------------------

    def _create_single_photo_post(self, image_url: str, caption: str) -> dict[str, Any]:
        container_request = {
            "url": f"{self.graph_api_base_url}/{self.ig_business_account_id}/media",
            "data": {"image_url": image_url, "caption": caption, "access_token": "***"},
        }

        if self.dry_run:
            return self._dry_run_result([container_request, self._publish_request("<container_id>")])

        container = self._post(
            f"{self.graph_api_base_url}/{self.ig_business_account_id}/media",
            {"image_url": image_url, "caption": caption, "access_token": self.access_token},
        )
        return self._publish(container["id"])

    # -- carousel -----------------------------------------------------------

    def _create_carousel_post(self, image_urls: list[str], caption: str) -> dict[str, Any]:
        item_requests = [
            {
                "url": f"{self.graph_api_base_url}/{self.ig_business_account_id}/media",
                "data": {"image_url": url, "is_carousel_item": True, "access_token": "***"},
            }
            for url in image_urls
        ]
        carousel_request = {
            "url": f"{self.graph_api_base_url}/{self.ig_business_account_id}/media",
            "data": {
                "media_type": "CAROUSEL",
                "children": ["<item_container_id>"] * len(image_urls),
                "caption": caption,
                "access_token": "***",
            },
        }

        if self.dry_run:
            return self._dry_run_result(
                [*item_requests, carousel_request, self._publish_request("<carousel_container_id>")]
            )

        item_ids = [
            self._post(
                f"{self.graph_api_base_url}/{self.ig_business_account_id}/media",
                {"image_url": url, "is_carousel_item": "true", "access_token": self.access_token},
            )["id"]
            for url in image_urls
        ]
        carousel = self._post(
            f"{self.graph_api_base_url}/{self.ig_business_account_id}/media",
            {
                "media_type": "CAROUSEL",
                "children": ",".join(item_ids),
                "caption": caption,
                "access_token": self.access_token,
            },
        )
        return self._publish(carousel["id"])

    # -- shared helpers -----------------------------------------------------

    def _publish_request(self, container_id: str) -> dict[str, Any]:
        return {
            "url": f"{self.graph_api_base_url}/{self.ig_business_account_id}/media_publish",
            "data": {"creation_id": container_id, "access_token": "***"},
        }

    def _publish(self, container_id: str) -> dict[str, Any]:
        return self._post(
            f"{self.graph_api_base_url}/{self.ig_business_account_id}/media_publish",
            {"creation_id": container_id, "access_token": self.access_token},
        )

    def _post(self, url: str, data: dict[str, Any]) -> dict[str, Any]:
        response = requests.post(url, data=data, timeout=30)
        response.raise_for_status()
        return response.json()

    def _dry_run_result(self, requests_planned: list[dict[str, Any]]) -> dict[str, Any]:
        logger.info("Instagram dry-run: %s", requests_planned)
        return {"dry_run": True, "platform": "instagram", "requests": requests_planned}
