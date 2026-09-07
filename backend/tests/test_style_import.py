import requests

from app.posting.style_import import StyleImportError, fetch_own_captions


class FakeResponse:
    def __init__(self, json_data, status_code=200):
        self._json_data = json_data
        self.status_code = status_code

    def raise_for_status(self):
        if self.status_code >= 400:
            raise requests.HTTPError(f"{self.status_code} error")

    def json(self):
        return self._json_data


def test_fetch_own_captions_requires_credentials():
    try:
        fetch_own_captions("", "", graph_api_base_url="https://graph.facebook.com/v19.0")
        assert False, "expected StyleImportError"
    except StyleImportError:
        pass


def test_fetch_own_captions_returns_captions_and_skips_empty_ones(monkeypatch):
    def fake_get(url, params, timeout):
        assert "media" in url
        return FakeResponse(
            {
                "data": [
                    {"caption": "First real caption"},
                    {},  # a post with no caption at all
                    {"caption": "Second real caption"},
                ]
            }
        )

    monkeypatch.setattr(requests, "get", fake_get)
    captions = fetch_own_captions(
        "token", "1234", graph_api_base_url="https://graph.facebook.com/v19.0"
    )
    assert captions == ["First real caption", "Second real caption"]


def test_fetch_own_captions_follows_pagination_up_to_limit(monkeypatch):
    calls = []

    def fake_get(url, params=None, timeout=15.0):
        calls.append(url)
        if len(calls) == 1:
            return FakeResponse(
                {
                    "data": [{"caption": "Caption 1"}, {"caption": "Caption 2"}],
                    "paging": {"next": "https://graph.facebook.com/v19.0/next-page"},
                }
            )
        return FakeResponse({"data": [{"caption": "Caption 3"}]})

    monkeypatch.setattr(requests, "get", fake_get)
    captions = fetch_own_captions(
        "token", "1234", graph_api_base_url="https://graph.facebook.com/v19.0", limit=3
    )
    assert captions == ["Caption 1", "Caption 2", "Caption 3"]
    assert len(calls) == 2


def test_fetch_own_captions_raises_on_request_failure(monkeypatch):
    def fake_get(*args, **kwargs):
        raise requests.ConnectionError("network down")

    monkeypatch.setattr(requests, "get", fake_get)
    try:
        fetch_own_captions("token", "1234", graph_api_base_url="https://graph.facebook.com/v19.0")
        assert False, "expected StyleImportError"
    except StyleImportError:
        pass
