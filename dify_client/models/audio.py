from typing import Optional

from pydantic import BaseModel


class AudioToTextRequest(BaseModel):
    user: Optional[str] = None


class AudioToTextResponse(BaseModel):
    text: str


class TextToAudioRequest(BaseModel):
    message_id: Optional[str] = None
    text: Optional[str] = None
    user: Optional[str] = None
    voice: Optional[str] = None
    streaming: Optional[bool] = None
