import httpx
import pytest
from httpx_sse import ServerSentEvent

from dify_client import models
from dify_client._clientx import Client


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


def _response(method: str, endpoint: str, payload):
    return httpx.Response(
        status_code=200,
        json=payload,
        request=httpx.Request(method, endpoint),
    )


def test_sync_wrapper_methods(monkeypatch):
    calls = []

    def fake_request(self, endpoint, method, **kwargs):
        calls.append((endpoint, str(method)))
        if endpoint.endswith("/messages/msg-1/feedbacks"):
            return _response(str(method), endpoint, {"result": "success"})
        if endpoint.endswith("/messages/msg-1/suggested"):
            return _response(str(method), endpoint, {"result": "success", "data": ["q1"]})
        if endpoint.endswith("/files/upload"):
            return _response(
                str(method),
                endpoint,
                {
                    "id": "f1",
                    "name": "a.txt",
                    "size": 1,
                    "extension": ".txt",
                    "mime_type": "text/plain",
                    "created_by": "u1",
                    "created_at": 1,
                },
            )
        if endpoint.endswith("/completion-messages"):
            return _response(str(method), endpoint, _completion_payload("completion"))
        if endpoint.endswith("/completion-messages/task-1/stop"):
            return _response(str(method), endpoint, {"result": "success"})
        if endpoint.endswith("/chat-messages"):
            return _response(str(method), endpoint, _completion_payload("chat"))
        if endpoint.endswith("/chat-messages/task-1/stop"):
            return _response(str(method), endpoint, {"result": "success"})
        if endpoint.endswith("/workflows/run"):
            return _response(str(method), endpoint, _workflow_payload())
        if endpoint.endswith("/workflows/tasks/task-1/stop"):
            return _response(str(method), endpoint, {"result": "success"})
        raise AssertionError(endpoint)

    monkeypatch.setattr(Client, "request", fake_request)
    client = Client(api_key="token", api_base="https://api.example.com/v1")

    assert client.feedback_messages("msg-1", models.FeedbackRequest(user="u1")).result == "success"
    assert client.suggest_messages("msg-1", models.ChatSuggestRequest(user="u1")).data == ["q1"]
    assert client.upload_files(("a.txt", b"x", "text/plain"), models.UploadFileRequest(user="u1")).id == "f1"

    completion_req = models.CompletionRequest(
        inputs={"query": "hi"},
        response_mode=models.ResponseMode.BLOCKING,
        user="u1",
    )
    assert client.completion_messages(completion_req).mode == models.Mode.COMPLETION
    assert client.stop_completion_messages("task-1", models.StopRequest(user="u1")).result == "success"

    chat_req = models.ChatRequest(
        query="hi",
        inputs={},
        response_mode=models.ResponseMode.BLOCKING,
        user="u1",
    )
    assert client.chat_messages(chat_req).mode == models.Mode.CHAT
    assert client.stop_chat_messages("task-1", models.StopRequest(user="u1")).result == "success"

    workflow_req = models.WorkflowsRunRequest(
        inputs={"a": 1},
        response_mode=models.ResponseMode.BLOCKING,
        user="u1",
    )
    assert client.run_workflows(workflow_req).workflow_run_id == "run-1"
    assert client.stop_workflows("task-1", models.StopRequest(user="u1")).result == "success"
    assert len(calls) == 9


def test_sync_stream_wrapper_methods(monkeypatch):
    def fake_request_stream(self, endpoint, method, **kwargs):
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

    monkeypatch.setattr(Client, "request_stream", fake_request_stream)
    client = Client(api_key="token", api_base="https://api.example.com/v1")

    completion_req = models.CompletionRequest(
        inputs={"query": "hi"},
        response_mode=models.ResponseMode.STREAMING,
        user="u1",
    )
    completion_items = list(client.completion_messages(completion_req))
    assert completion_items[0].event == models.StreamEvent.MESSAGE

    chat_req = models.ChatRequest(
        query="hi",
        inputs={},
        response_mode=models.ResponseMode.STREAMING,
        user="u1",
    )
    chat_items = list(client.chat_messages(chat_req))
    assert chat_items[0].event == models.StreamEvent.MESSAGE

    workflow_req = models.WorkflowsRunRequest(
        inputs={"a": 1},
        response_mode=models.ResponseMode.STREAMING,
        user="u1",
    )
    workflow_items = list(client.run_workflows(workflow_req))
    assert workflow_items[0].event == models.StreamEvent.WORKFLOW_FINISHED


def test_sync_invalid_response_mode_raises_value_error():
    client = Client(api_key="token")

    completion_req = models.CompletionRequest(
        inputs={"query": "hi"},
        response_mode=models.ResponseMode.BLOCKING,
        user="u1",
    )
    completion_req.response_mode = "invalid"
    with pytest.raises(ValueError):
        client.completion_messages(completion_req)

    chat_req = models.ChatRequest(
        query="hi",
        inputs={},
        response_mode=models.ResponseMode.BLOCKING,
        user="u1",
    )
    chat_req.response_mode = "invalid"
    with pytest.raises(ValueError):
        client.chat_messages(chat_req)

    workflow_req = models.WorkflowsRunRequest(
        inputs={"a": 1},
        response_mode=models.ResponseMode.BLOCKING,
        user="u1",
    )
    workflow_req.response_mode = "invalid"
    with pytest.raises(ValueError):
        client.run_workflows(workflow_req)
