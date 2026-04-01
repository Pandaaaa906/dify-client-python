from http import HTTPStatus
from typing import Any, Dict, Union

import httpx
import httpx_sse

from dify_client import models


class DifyAPIError(Exception):
    def __init__(self, status: int, code: str, message: str):
        super().__init__(f"status_code={status}, code={code}, {message}")
        self.status = status
        self.code = code
        self.message = message


class DifyInvalidParam(DifyAPIError):
    pass


class DifyNotChatApp(DifyAPIError):
    pass


class DifyResourceNotFound(DifyAPIError):
    pass


class DifyAppUnavailable(DifyAPIError):
    pass


class DifyProviderNotInitialize(DifyAPIError):
    pass


class DifyProviderQuotaExceeded(DifyAPIError):
    pass


class DifyModelCurrentlyNotSupport(DifyAPIError):
    pass


class DifyCompletionRequestError(DifyAPIError):
    pass


class DifyInternalServerError(DifyAPIError):
    pass


class DifyNoFileUploaded(DifyAPIError):
    pass


class DifyTooManyFiles(DifyAPIError):
    pass


class DifyUnsupportedPreview(DifyAPIError):
    pass


class DifyUnsupportedEstimate(DifyAPIError):
    pass


class DifyFileTooLarge(DifyAPIError):
    pass


class DifyUnsupportedFileType(DifyAPIError):
    pass


class DifyS3ConnectionFailed(DifyAPIError):
    pass


class DifyS3PermissionDenied(DifyAPIError):
    pass


class DifyS3FileTooLarge(DifyAPIError):
    pass


SPEC_CODE_ERRORS = {
    # completion & chat & workflow
    "invalid_param": DifyInvalidParam,
    "not_chat_app": DifyNotChatApp,
    "app_unavailable": DifyAppUnavailable,
    "provider_not_initialize": DifyProviderNotInitialize,
    "provider_quota_exceeded": DifyProviderQuotaExceeded,
    "model_currently_not_support": DifyModelCurrentlyNotSupport,
    "completion_request_error": DifyCompletionRequestError,
    # files upload
    "no_file_uploaded": DifyNoFileUploaded,
    "too_many_files": DifyTooManyFiles,
    "unsupported_preview": DifyUnsupportedPreview,
    "unsupported_estimate": DifyUnsupportedEstimate,
    "file_too_large": DifyFileTooLarge,
    "unsupported_file_type": DifyUnsupportedFileType,
    "s3_connection_failed": DifyS3ConnectionFailed,
    "s3_permission_denied": DifyS3PermissionDenied,
    "s3_file_too_large": DifyS3FileTooLarge,
}


def _build_error_response(response: httpx.Response) -> models.ErrorResponse:
    fallback_message = response.text or response.reason_phrase or "Request failed"
    try:
        payload = response.json()
    except ValueError:
        payload = {}

    if not isinstance(payload, dict):
        payload = {}
    if "status" not in payload:
        payload["status"] = response.status_code
    if not payload.get("code"):
        payload["code"] = ""
    if not payload.get("message"):
        payload["message"] = fallback_message
    return models.ErrorResponse(**payload)


def _build_error_stream_response(response: httpx_sse.ServerSentEvent) -> models.ErrorStreamResponse:
    try:
        payload: Dict[str, Any] = response.json()
    except ValueError:
        payload = {}

    if not isinstance(payload, dict):
        payload = {}
    payload.setdefault("event", response.event or models.StreamEvent.ERROR.value)
    if not payload.get("message"):
        payload["message"] = response.data or ""
    if not payload.get("code"):
        payload["code"] = ""
    return models.ErrorStreamResponse(**payload)


def raise_for_status(response: Union[httpx.Response, httpx_sse.ServerSentEvent]):
    if isinstance(response, httpx.Response):
        if response.is_success:
            return
        details = _build_error_response(response)
    elif isinstance(response, httpx_sse.ServerSentEvent):
        if response.event != models.StreamEvent.ERROR.value:
            return
        details = _build_error_stream_response(response)
    else:
        raise ValueError(f"Invalid dify response type: {type(response)}")

    if details.status == HTTPStatus.NOT_FOUND:
        raise DifyResourceNotFound(details.status, details.code, details.message)
    elif details.status == HTTPStatus.INTERNAL_SERVER_ERROR:
        raise DifyInternalServerError(details.status, details.code, details.message)
    else:
        raise SPEC_CODE_ERRORS.get(details.code, DifyAPIError)(
            details.status, details.code, details.message
        )
