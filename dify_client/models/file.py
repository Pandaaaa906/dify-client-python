from typing import Optional

from pydantic import BaseModel


class UploadFileRequest(BaseModel):
    user: Optional[str] = None


class UploadFileResponse(BaseModel):
    id: str
    name: str
    size: int
    extension: str
    mime_type: str
    created_by: str  # created by user
    created_at: int  # unix timestamp seconds
    preview_url: Optional[str] = None
    source_url: Optional[str] = None
    original_url: Optional[str] = None
    user_id: Optional[str] = None
    tenant_id: Optional[str] = None
    conversation_id: Optional[str] = None
    file_key: Optional[str] = None
