"""Facebook Graph API client (Page albums).

Unlike Instagram's Content Publishing API, Facebook's Page photo endpoint
accepts a direct multipart file upload, so this client can work with local
edited photos without needing a public URL.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import requests

logger = logging.getLogger(__name__)


@dataclass
class FacebookClient:
    access_token: str
    page_id: str
    graph_api_base_url: str = "https://graph.facebook.com/v19.0"
    dry_run: bool = field(init=False)

    def __post_init__(self) -> None:
        self.dry_run = not (self.access_token and self.page_id)

    def create_album(self, name: str, message: str = "") -> dict[str, Any]:
        request = {
            "url": f"{self.graph_api_base_url}/{self.page_id}/albums",
            "data": {"name": name, "message": message, "access_token": "***"},
        }

        if self.dry_run:
            logger.info("Facebook dry-run (create_album): %s", request)
            return {"dry_run": True, "platform": "facebook", "action": "create_album", "request": request}

        response = requests.post(
            request["url"],
            data={"name": name, "message": message, "access_token": self.access_token},
            timeout=30,
        )
        response.raise_for_status()
        return response.json()

    def upload_photo(self, album_id: str, file_path: str | Path, caption: str = "") -> dict[str, Any]:
        file_path = Path(file_path)
        request = {
            "url": f"{self.graph_api_base_url}/{album_id}/photos",
            "data": {"caption": caption, "access_token": "***"},
            "file": str(file_path),
        }

        if self.dry_run:
            logger.info("Facebook dry-run (upload_photo): %s", request)
            return {"dry_run": True, "platform": "facebook", "action": "upload_photo", "request": request}

        with file_path.open("rb") as f:
            response = requests.post(
                request["url"],
                data={"caption": caption, "access_token": self.access_token},
                files={"source": f},
                timeout=60,
            )
        response.raise_for_status()
        return response.json()

    def post_album(self, name: str, photo_paths: list[str | Path], caption: str = "") -> dict[str, Any]:
        """Convenience helper: create an album and upload every kept photo."""
        album_result = self.create_album(name, caption)
        album_id = album_result.get("id", "<album_id>")
        photo_results = [self.upload_photo(album_id, p, caption) for p in photo_paths]
        return {"album": album_result, "photos": photo_results}
