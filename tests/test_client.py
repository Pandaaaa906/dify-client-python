import httpx
from httpx_sse import ServerSentEvent

from dify_client import models
from dify_client._clientx import AsyncClient, Client


def _ok_response(method: str, url: str) -> httpx.Response:
    request = httpx.Request(method, url)
    return httpx.Response(status_code=200, json={"ok": True}, request=request)


def test_prepare_url_normalizes_slashes():
    client = Client(api_key="token", api_base="https://api.example.com/v1/")
    assert client._prepare_url("/chat-messages") == "https://api.example.com/v1/chat-messages"

    async_client = AsyncClient(api_key="token", api_base="https://api.example.com/v1")
    assert async_client._prepare_url("chat-messages") == "https://api.example.com/v1/chat-messages"


def test_prepare_auth_headers_keeps_existing_authorization():
    headers = {"authorization": "Bearer custom-token"}
    Client(api_key="token")._prepare_auth_headers(headers)
    assert headers["authorization"] == "Bearer custom-token"
    assert "Authorization" not in headers


def test_request_injects_bearer_token(monkeypatch):
    captured = {}

    def fake_request(method, endpoint, **kwargs):
        captured["method"] = method
        captured["endpoint"] = endpoint
        captured["headers"] = kwargs["headers"]
        return _ok_response(str(method), endpoint)

    from dify_client import _clientx

    monkeypatch.setattr(_clientx._httpx_client, "request", fake_request)
    client = Client(api_key="token", api_base="https://api.example.com/v1")
    client.request(client._prepare_url("/chat-messages"), "GET")

    assert captured["method"] == "GET"
    assert captured["endpoint"] == "https://api.example.com/v1/chat-messages"
    assert captured["headers"]["Authorization"] == "Bearer token"


def test_request_stream_ignores_ping_events(monkeypatch):
    class FakeEventSource:
        def __init__(self, response, events):
            self.response = response
            self._events = events

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc_val, exc_tb):
            return False

        def iter_sse(self):
            yield from self._events

    response = httpx.Response(
        status_code=200,
        headers={"content-type": "text/event-stream"},
        request=httpx.Request("POST", "https://api.example.com/v1/chat-messages"),
    )
    events = [
        ServerSentEvent(event="ping", data=""),
        ServerSentEvent(event="message", data='{"event":"message","answer":"ok"}'),
    ]

    def fake_connect_sse(*args, **kwargs):
        return FakeEventSource(response=response, events=events)

    from dify_client import _clientx

    monkeypatch.setattr(_clientx, "connect_sse", fake_connect_sse)
    client = Client(api_key="token", api_base="https://api.example.com/v1")
    chunks = list(client.request_stream(client._prepare_url("/chat-messages"), "POST", json={"a": 1}))
    assert len(chunks) == 1
    assert chunks[0].event == "message"


def test_stop_workflows_uses_latest_tasks_endpoint(monkeypatch):
    captured = {}

    def fake_request(method, endpoint, **kwargs):
        captured["endpoint"] = endpoint
        return httpx.Response(
            status_code=200,
            json={"result": "success"},
            request=httpx.Request(str(method), endpoint),
        )

    from dify_client import _clientx

    monkeypatch.setattr(_clientx._httpx_client, "request", fake_request)
    client = Client(api_key="token", api_base="https://api.example.com/v1")
    response = client.stop_workflows("task-1", models.StopRequest(user="u1"))
    assert captured["endpoint"] == "https://api.example.com/v1/workflows/tasks/task-1/stop"
    assert response.result == "success"


def test_audio_to_text_and_text_to_audio(monkeypatch):
    calls = []

    def fake_request(method, endpoint, **kwargs):
        calls.append((str(method), endpoint, kwargs))
        if endpoint.endswith("/audio-to-text"):
            return httpx.Response(
                status_code=200,
                json={"text": "hello"},
                request=httpx.Request(str(method), endpoint),
            )
        return httpx.Response(
            status_code=200,
            content=b"mp3-bytes",
            request=httpx.Request(str(method), endpoint),
            headers={"content-type": "audio/mpeg"},
        )

    from dify_client import _clientx

    monkeypatch.setattr(_clientx._httpx_client, "request", fake_request)
    client = Client(api_key="token", api_base="https://api.example.com/v1")

    audio_to_text = client.audio_to_text(("a.wav", b"abc", "audio/wav"), models.AudioToTextRequest(user="u1"))
    assert audio_to_text.text == "hello"

    audio = client.text_to_audio(models.TextToAudioRequest(text="hello", user="u1"))
    assert audio == b"mp3-bytes"
    assert calls[0][1].endswith("/audio-to-text")
    assert calls[1][1].endswith("/text-to-audio")
