import httpx
from httpx_sse import ServerSentEvent

from dify_client import errors


def test_raise_for_status_maps_known_error_code():
    response = httpx.Response(
        status_code=400,
        json={
            "status": 400,
            "code": "invalid_param",
            "message": "bad request",
        },
        request=httpx.Request("POST", "https://api.example.com/v1/chat-messages"),
    )

    try:
        errors.raise_for_status(response)
    except errors.DifyInvalidParam as exc:
        assert exc.status == 400
        assert exc.code == "invalid_param"
        assert "bad request" in exc.message
    else:
        raise AssertionError("Expected DifyInvalidParam")


def test_raise_for_status_uses_fallback_for_non_json_response():
    response = httpx.Response(
        status_code=502,
        text="Bad gateway",
        request=httpx.Request("GET", "https://api.example.com/v1/workflows/run"),
    )

    try:
        errors.raise_for_status(response)
    except errors.DifyAPIError as exc:
        assert exc.status == 502
        assert exc.code == ""
        assert "Bad gateway" in exc.message
    else:
        raise AssertionError("Expected DifyAPIError")


def test_raise_for_status_handles_non_json_stream_error():
    sse = ServerSentEvent(event="error", data="stream failed")
    try:
        errors.raise_for_status(sse)
    except errors.DifyInternalServerError as exc:
        assert exc.status == 500
        assert exc.code == ""
        assert "stream failed" in exc.message
    else:
        raise AssertionError("Expected DifyInternalServerError")


def test_raise_for_status_ignores_non_error_stream_event():
    sse = ServerSentEvent(event="message", data="ok")
    errors.raise_for_status(sse)
