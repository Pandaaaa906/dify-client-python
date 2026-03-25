from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from dify_client.models.base import File, Metadata, Mode, ResponseMode


class CompletionRequest(BaseModel):
    inputs: Dict[str, Any] = Field(default_factory=dict)
    # Legacy field. Prefer passing query in `inputs`.
    query: Optional[str] = ""
    response_mode: ResponseMode
    user: str
    files: List[File] = Field(default_factory=list)


class CompletionResponse(BaseModel):
    event: Optional[str] = None
    task_id: Optional[str] = None
    id: Optional[str] = None
    message_id: str
    mode: Mode
    answer: str
    metadata: Metadata
    created_at: int  # unix timestamp seconds
