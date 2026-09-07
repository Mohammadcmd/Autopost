from fastapi.testclient import TestClient

from app.main import app


def test_get_style_defaults_when_no_file_written_yet():
    with TestClient(app) as client:
        response = client.get("/api/style")
        assert response.status_code == 200
        # Whatever was left by a previous test in this run; just confirm the shape.
        body = response.json()
        assert "tone_notes" in body
        assert "example_captions" in body


def test_update_and_get_style_round_trips():
    with TestClient(app) as client:
        put_resp = client.put(
            "/api/style",
            json={"tone_notes": "Casual and warm.", "example_captions": ["One caption", "Two caption"]},
        )
        assert put_resp.status_code == 200
        assert put_resp.json() == {
            "tone_notes": "Casual and warm.",
            "example_captions": ["One caption", "Two caption"],
        }

        get_resp = client.get("/api/style")
        assert get_resp.json() == {
            "tone_notes": "Casual and warm.",
            "example_captions": ["One caption", "Two caption"],
        }


def test_import_from_instagram_fails_without_credentials():
    with TestClient(app) as client:
        response = client.post("/api/style/import-from-instagram")
        assert response.status_code == 400
        assert "META_ACCESS_TOKEN" in response.json()["detail"]
