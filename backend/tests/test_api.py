"""End-to-end API test: scan -> review (keep/delete) -> caption -> post.

This exercises the whole pipeline through the same HTTP interface the
frontend uses, which is what caught two real bugs during manual testing
(an OpenCV shape mismatch in deskew_and_crop, and a str/datetime schema
mismatch in the photos response) that the narrower unit tests missed.
"""
import os
from datetime import datetime
from pathlib import Path

import numpy as np
from fastapi.testclient import TestClient
from PIL import Image

from app.main import app


def _make_photo(dir_path: Path, name: str, when: datetime) -> None:
    array = np.random.default_rng(0).integers(0, 255, size=(50, 50, 3), dtype=np.uint8)
    path = dir_path / name
    Image.fromarray(array).save(path)
    ts = when.timestamp()
    os.utime(path, (ts, ts))


def test_full_pipeline_scan_review_and_post(tmp_path):
    photos_dir = tmp_path / "camera"
    photos_dir.mkdir()
    # Falls inside the sample_events.json stub window (2024-07-04, 11:00-16:00)
    # so the website-matching + caption drafting path gets exercised too.
    _make_photo(photos_dir, "a.jpg", datetime(2024, 7, 4, 12, 0, 0))
    _make_photo(photos_dir, "b.jpg", datetime(2024, 7, 4, 12, 5, 0))
    _make_photo(photos_dir, "c.jpg", datetime(2024, 7, 4, 12, 9, 0))

    with TestClient(app) as client:
        scan_resp = client.post("/api/sessions/scan", json={"path": str(photos_dir)})
        assert scan_resp.status_code == 200, scan_resp.text
        event = scan_resp.json()["events"][0]
        assert event["photo_count"] == 3
        assert event["website_event_name"] == "Sample Community Picnic"

        event_id = event["id"]
        photos = client.get(f"/api/events/{event_id}/photos").json()
        assert len(photos) == 3

        client.post(f"/api/photos/{photos[0]['id']}/decision", json={"decision": "keep"})
        client.post(f"/api/photos/{photos[1]['id']}/decision", json={"decision": "keep"})
        client.post(f"/api/photos/{photos[2]['id']}/decision", json={"decision": "delete"})

        img_resp = client.get(f"/api/photos/{photos[0]['id']}/image")
        assert img_resp.status_code == 200
        assert img_resp.headers["content-type"] == "image/jpeg"

        caption_resp = client.get(f"/api/events/{event_id}/caption")
        assert caption_resp.status_code == 200
        assert "Sample Community Picnic" in caption_resp.json()["caption"]

        post_resp = client.post(f"/api/events/{event_id}/post")
        assert post_resp.status_code == 200, post_resp.text
        result = post_resp.json()
        assert result["dry_run"] is True
        assert result["instagram"]["dry_run"] is True
        assert result["facebook"]["album"]["dry_run"] is True
        assert len(result["facebook"]["photos"]) == 2  # only the 2 kept photos


def test_scan_missing_path_returns_404():
    with TestClient(app) as client:
        response = client.post("/api/sessions/scan", json={"path": "/no/such/path"})
        assert response.status_code == 404


def test_post_without_kept_photos_returns_400(tmp_path):
    photos_dir = tmp_path / "camera"
    photos_dir.mkdir()
    _make_photo(photos_dir, "a.jpg", datetime(2024, 7, 4, 12, 0, 0))

    with TestClient(app) as client:
        scan_resp = client.post("/api/sessions/scan", json={"path": str(photos_dir)})
        event_id = scan_resp.json()["events"][0]["id"]

        post_resp = client.post(f"/api/events/{event_id}/post")
        assert post_resp.status_code == 400
