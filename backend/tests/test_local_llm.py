import requests

from app.posting.local_llm import LocalLLMClient, LocalLLMUnavailableError


class FakeResponse:
    def __init__(self, json_data, status_code=200):
        self._json_data = json_data
        self.status_code = status_code

    def raise_for_status(self):
        if self.status_code >= 400:
            raise requests.HTTPError(f"{self.status_code} error")

    def json(self):
        return self._json_data


def test_generate_returns_response_text(monkeypatch):
    def fake_post(url, json, timeout):
        assert url == "http://localhost:11434/api/generate"
        assert json["model"] == "llama3.2"
        assert json["stream"] is False
        return FakeResponse({"response": "  A lovely caption.  "})

    monkeypatch.setattr(requests, "post", fake_post)
    client = LocalLLMClient("http://localhost:11434", "llama3.2")
    assert client.generate("some prompt") == "A lovely caption."


def test_generate_raises_when_server_unreachable(monkeypatch):
    def fake_post(*args, **kwargs):
        raise requests.ConnectionError("connection refused")

    monkeypatch.setattr(requests, "post", fake_post)
    client = LocalLLMClient("http://localhost:11434", "llama3.2")
    try:
        client.generate("some prompt")
        assert False, "expected LocalLLMUnavailableError"
    except LocalLLMUnavailableError:
        pass


def test_generate_raises_on_empty_response(monkeypatch):
    monkeypatch.setattr(requests, "post", lambda *a, **k: FakeResponse({"response": "  "}))
    client = LocalLLMClient("http://localhost:11434", "llama3.2")
    try:
        client.generate("some prompt")
        assert False, "expected LocalLLMUnavailableError"
    except LocalLLMUnavailableError:
        pass


def test_generate_raises_on_http_error(monkeypatch):
    monkeypatch.setattr(requests, "post", lambda *a, **k: FakeResponse({}, status_code=500))
    client = LocalLLMClient("http://localhost:11434", "llama3.2")
    try:
        client.generate("some prompt")
        assert False, "expected LocalLLMUnavailableError"
    except LocalLLMUnavailableError:
        pass
