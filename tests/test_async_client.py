import httpx
import pytest
from httpx_sse import ServerSentEvent

from dify_client import errors, models
from dify_client._clientx import AsyncClient


def _usage_payload():
    return {
        "prompt_tokens": 1,
        "completion_tokens": 1,
        "total_tokens": 2,
        "prompt_unit_price": "0",
        "prompt_price_unit": "0",
        "prompt_price": "0",
        "completion_unit_price": "0",
        "completion_price_unit": "0",
        "completion_price": "0",
        "total_price": "0",
        "currency": "USD",
        "latency": 0.1,
    }


def _completion_payload(mode: str):
    return {
        "event": "message",
        "task_id": "task-1",
        "id": "evt-1",
        "message_id": "msg-1",
        "conversation_id": "conv-1",
        "mode": mode,
        "answer": "ok",
        "metadata": {"usage": _usage_payload(), "retriever_resources": []},
        "created_at": 1,
    }


def _workflow_payload():
    return {
        "task_id": "task-1",
        "workflow_run_id": "run-1",
        "data": {
            "id": "run-1",
            "workflow_id": "wf-1",
            "status": "succeeded",
            "outputs": {},
            "created_at": 1,
            "finished_at": 2,
        },
    }


@pytest.mark.anyio
async def test_arequest_injects_authorization(monkeypatch):
    captured = {}

    async def fake_request(method, endpoint, **kwargs):
        captured["endpoint"] = endpoint
        captured["headers"] = kwargs["headers"]
        return httpx.Response(
            status_code=200,
            json={"ok": True},
            request=httpx.Request(str(method), endpoint),
        )

    from dify_client import _clientx

    monkeypatch.setattr(_clientx._async_httpx_client, "request", fake_request)
    client = AsyncClient(api_key="token", api_base="https://api.example.com/v1")
    await client.arequest(client._prepare_url("/chat-messages"), "GET")
    assert captured["endpoint"] == "https://api.example.com/v1/chat-messages"
    assert captured["headers"]["Authorization"] == "Bearer token"


@pytest.mark.anyio
async def test_arequest_stream_filters_ping(monkeypatch):
    class FakeAsyncEventSource:
        def __init__(self, response, events):
            self.response = response
            self._events = events

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc_val, exc_tb):
            return False

        async def aiter_sse(self):
            for event in self._events:
                yield event

    response = httpx.Response(
        status_code=200,
        headers={"content-type": "text/event-stream"},
        request=httpx.Request("POST", "https://api.example.com/v1/chat-messages"),
    )
    events = [
        ServerSentEvent(event="ping", data=""),
        ServerSentEvent(event="message", data='{"event":"message","answer":"ok"}'),
    ]

    def fake_aconnect_sse(*args, **kwargs):
        return FakeAsyncEventSource(response=response, events=events)

    from dify_client import _clientx

    monkeypatch.setattr(_clientx, "aconnect_sse", fake_aconnect_sse)
    client = AsyncClient(api_key="token", api_base="https://api.example.com/v1")
    seen = []
    async for event in client.arequest_stream(client._prepare_url("/chat-messages"), "POST", json={"a": 1}):
        seen.append(event)
    assert len(seen) == 1
    assert seen[0].event == "message"


@pytest.mark.anyio
async def test_arequest_stream_non_sse_raises_api_error(monkeypatch):
    class FakeAsyncEventSource:
        def __init__(self, response):
            self.response = response

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc_val, exc_tb):
            return False

        async def aiter_sse(self):
            if False:
                yield None

    response = httpx.Response(
        status_code=400,
        headers={"content-type": "application/json"},
        json={"status": 400, "code": "invalid_param", "message": "bad request"},
        request=httpx.Request("POST", "https://api.example.com/v1/chat-messages"),
    )

    def fake_aconnect_sse(*args, **kwargs):
        return FakeAsyncEventSource(response=response)

    from dify_client import _clientx

    monkeypatch.setattr(_clientx, "aconnect_sse", fake_aconnect_sse)
    client = AsyncClient(api_key="token", api_base="https://api.example.com/v1")

    with pytest.raises(errors.DifyInvalidParam):
        async for _ in client.arequest_stream(client._prepare_url("/chat-messages"), "POST", json={"a": 1}):
            pass


@pytest.mark.anyio
async def test_async_wrapper_methods(monkeypatch):
    async def fake_arequest(self, endpoint, method, **kwargs):
        request = httpx.Request(str(method), endpoint)
        if endpoint.endswith("/messages/msg-1/feedbacks"):
            return httpx.Response(status_code=200, json={"result": "success"}, request=request)
        if endpoint.endswith("/messages/msg-1/suggested"):
            return httpx.Response(
                status_code=200,
                json={"result": "success", "data": ["q1"]},
                request=request,
            )
        if endpoint.endswith("/files/upload"):
            return httpx.Response(
                status_code=200,
                json={
                    "id": "f1",
                    "name": "a.txt",
                    "size": 1,
                    "extension": ".txt",
                    "mime_type": "text/plain",
                    "created_by": "u1",
                    "created_at": 1,
                },
                request=request,
            )
        if endpoint.endswith("/audio-to-text"):
            return httpx.Response(status_code=200, json={"text": "hello"}, request=request)
        if endpoint.endswith("/text-to-audio"):
            return httpx.Response(
                status_code=200,
                content=b"mp3-bytes",
                headers={"content-type": "audio/mpeg"},
                request=request,
            )
        if endpoint.endswith("/completion-messages"):
            return httpx.Response(status_code=200, json=_completion_payload("completion"), request=request)
        if endpoint.endswith("/completion-messages/task-1/stop"):
            return httpx.Response(status_code=200, json={"result": "success"}, request=request)
        if endpoint.endswith("/chat-messages"):
            return httpx.Response(status_code=200, json=_completion_payload("chat"), request=request)
        if endpoint.endswith("/chat-messages/task-1/stop"):
            return httpx.Response(status_code=200, json={"result": "success"}, request=request)
        if endpoint.endswith("/workflows/run"):
            return httpx.Response(status_code=200, json=_workflow_payload(), request=request)
        if endpoint.endswith("/workflows/tasks/task-1/stop"):
            return httpx.Response(status_code=200, json={"result": "success"}, request=request)
        raise AssertionError(endpoint)

    async def fake_arequest_stream(self, endpoint, method, **kwargs):
        if endpoint.endswith("/completion-messages"):
            yield ServerSentEvent(
                event="message",
                data='{"event":"message","message_id":"m1","answer":"ok","created_at":1}',
            )
            return
        if endpoint.endswith("/chat-messages"):
            yield ServerSentEvent(
                event="message",
                data='{"event":"message","message_id":"m1","conversation_id":"c1","answer":"ok","created_at":1}',
            )
            return
        if endpoint.endswith("/workflows/run"):
            yield ServerSentEvent(
                event="workflow_finished",
                data='{"event":"workflow_finished","workflow_run_id":"r1","data":{"id":"r1","workflow_id":"wf1","status":"succeeded","created_at":1,"finished_at":2}}',
            )
            return
        raise AssertionError(endpoint)

    monkeypatch.setattr(AsyncClient, "arequest", fake_arequest)
    monkeypatch.setattr(AsyncClient, "arequest_stream", fake_arequest_stream)

    client = AsyncClient(api_key="token", api_base="https://api.example.com/v1")

    assert (await client.afeedback_messages("msg-1", models.FeedbackRequest(user="u1"))).result == "success"
    assert (await client.asuggest_messages("msg-1", models.ChatSuggestRequest(user="u1"))).data == ["q1"]
    assert (await client.aupload_files(("a.txt", b"x", "text/plain"), models.UploadFileRequest(user="u1"))).id == "f1"
    assert (await client.aaudio_to_text(("a.wav", b"x", "audio/wav"), models.AudioToTextRequest(user="u1"))).text == "hello"
    assert await client.atext_to_audio(models.TextToAudioRequest(text="hello", user="u1")) == b"mp3-bytes"

    completion_blocking = models.CompletionRequest(
        inputs={"query": "hi"},
        response_mode=models.ResponseMode.BLOCKING,
        user="u1",
    )
    assert (await client.acompletion_messages(completion_blocking)).mode == models.Mode.COMPLETION
    assert (await client.astop_completion_messages("task-1", models.StopRequest(user="u1"))).result == "success"

    completion_stream = models.CompletionRequest(
        inputs={"query": "hi"},
        response_mode=models.ResponseMode.STREAMING,
        user="u1",
    )
    c_stream = await client.acompletion_messages(completion_stream)
    c_items = [item async for item in c_stream]
    assert c_items[0].event == models.StreamEvent.MESSAGE

    chat_blocking = models.ChatRequest(
        query="hi",
        inputs={},
        response_mode=models.ResponseMode.BLOCKING,
        user="u1",
    )
    assert (await client.achat_messages(chat_blocking)).mode == models.Mode.CHAT
    assert (await client.astop_chat_messages("task-1", models.StopRequest(user="u1"))).result == "success"

    chat_stream = models.ChatRequest(
        query="hi",
        inputs={},
        response_mode=models.ResponseMode.STREAMING,
        user="u1",
    )
    ch_stream = await client.achat_messages(chat_stream)
    ch_items = [item async for item in ch_stream]
    assert ch_items[0].event == models.StreamEvent.MESSAGE

    workflow_blocking = models.WorkflowsRunRequest(
        inputs={"a": 1},
        response_mode=models.ResponseMode.BLOCKING,
        user="u1",
    )
    assert (await client.arun_workflows(workflow_blocking)).workflow_run_id == "run-1"
    assert (await client.astop_workflows("task-1", models.StopRequest(user="u1"))).result == "success"

    workflow_stream = models.WorkflowsRunRequest(
        inputs={"a": 1},
        response_mode=models.ResponseMode.STREAMING,
        user="u1",
    )
    wf_stream = await client.arun_workflows(workflow_stream)
    wf_items = [item async for item in wf_stream]
    assert wf_items[0].event == models.StreamEvent.WORKFLOW_FINISHED


@pytest.mark.anyio
async def test_async_stop_workflows_fallback_and_invalid_mode(monkeypatch):
    calls = []

    async def fake_astop_stream(self, endpoint, req, **kwargs):
        calls.append(endpoint)
        if endpoint.endswith("/workflows/tasks/task-1/stop"):
            raise errors.DifyResourceNotFound(404, "not_found", "not found")
        return models.StopResponse(result="success")

    monkeypatch.setattr(AsyncClient, "_astop_stream", fake_astop_stream)
    client = AsyncClient(api_key="token", api_base="https://api.example.com/v1")
    stop = await client.astop_workflows("task-1", models.StopRequest(user="u1"))
    assert stop.result == "success"
    assert calls == [
        "https://api.example.com/v1/workflows/tasks/task-1/stop",
        "https://api.example.com/v1/workflows/task-1/stop",
    ]

    completion_req = models.CompletionRequest(
        inputs={"query": "hi"},
        response_mode=models.ResponseMode.BLOCKING,
        user="u1",
    )
    completion_req.response_mode = "invalid"
    with pytest.raises(ValueError):
        await client.acompletion_messages(completion_req)

    chat_req = models.ChatRequest(
        query="hi",
        inputs={},
        response_mode=models.ResponseMode.BLOCKING,
        user="u1",
    )
    chat_req.response_mode = "invalid"
    with pytest.raises(ValueError):
        await client.achat_messages(chat_req)

    workflow_req = models.WorkflowsRunRequest(
        inputs={"a": 1},
        response_mode=models.ResponseMode.BLOCKING,
        user="u1",
    )
    workflow_req.response_mode = "invalid"
    with pytest.raises(ValueError):
        await client.arun_workflows(workflow_req)
