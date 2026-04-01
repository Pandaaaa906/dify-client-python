try:
    from enum import StrEnum
except ImportError:
    from strenum import StrEnum
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, ConfigDict, Field, field_validator

from dify_client import utils
from dify_client.models.base import Metadata, ErrorResponse
from dify_client.models.workflow import (
    WorkflowStartedData,
    WorkflowFinishedData,
    NodeStartedData,
    NodeFinishedData,
)

STREAM_EVENT_KEY = "event"


class StreamEvent(StrEnum):
    MESSAGE = "message"
    AGENT_MESSAGE = "agent_message"
    AGENT_THOUGHT = "agent_thought"
    MESSAGE_FILE = "message_file"  # need to show file
    TTS_MESSAGE = "tts_message"
    TTS_MESSAGE_END = "tts_message_end"
    WORKFLOW_STARTED = "workflow_started"
    NODE_STARTED = "node_started"
    NODE_FINISHED = "node_finished"
    NODE_RETRY = "node_retry"
    ITERATION_STARTED = "iteration_started"
    ITERATION_NEXT = "iteration_next"
    ITERATION_COMPLETED = "iteration_completed"
    LOOP_STARTED = "loop_started"
    LOOP_NEXT = "loop_next"
    LOOP_COMPLETED = "loop_completed"
    TEXT_CHUNK = "text_chunk"
    TEXT_REPLACE = "text_replace"
    WORKFLOW_FINISHED = "workflow_finished"
    WORKFLOW_PAUSED = "workflow_paused"
    HUMAN_INPUT_REQUIRED = "human_input_required"
    HUMAN_INPUT_FORM_FILLED = "human_input_form_filled"
    HUMAN_INPUT_FORM_TIMEOUT = "human_input_form_timeout"
    MESSAGE_END = "message_end"
    MESSAGE_REPLACE = "message_replace"
    ERROR = "error"
    PING = "ping"
    # Legacy events from old chatflow runtime.
    PARALLEL_BRANCH_STARTED = "parallel_branch_started"
    PARALLEL_BRANCH_FINISHED = "parallel_branch_finished"
    AGENT_LOG = "agent_log"

    @classmethod
    def new(cls, event: Union["StreamEvent", str]) -> "StreamEvent":
        if isinstance(event, cls):
            return event
        return utils.str_to_enum(cls, event, ignore_not_found=True, enum_default=event)


class StreamResponse(BaseModel):
    model_config = ConfigDict(extra="allow")

    event: Union[StreamEvent, str]
    task_id: Optional[str] = ""

    @field_validator("event", mode="before")
    def transform_stream_event(cls, event: Union[StreamEvent, str]) -> StreamEvent:
        return StreamEvent.new(event)


class PingResponse(StreamResponse):
    pass


class ErrorStreamResponse(StreamResponse, ErrorResponse):
    message_id: Optional[str] = ""


class MessageStreamResponse(StreamResponse):
    message_id: str
    conversation_id: Optional[str] = ""
    answer: str
    created_at: int  # unix timestamp seconds


class MessageEndStreamResponse(StreamResponse):
    message_id: str
    conversation_id: Optional[str] = ""
    created_at: int  # unix timestamp seconds
    metadata: Optional[Metadata] = None


class MessageReplaceStreamResponse(MessageStreamResponse):
    pass


class AgentMessageStreamResponse(MessageStreamResponse):
    pass


class AgentThoughtStreamResponse(StreamResponse):
    id: str  # agent thought id
    message_id: str
    conversation_id: str
    position: int  # thought position, start from 1
    thought: str
    observation: str
    tool: str
    tool_input: str
    message_files: List[str] = Field(default_factory=list)
    created_at: int  # unix timestamp seconds


class MessageFileStreamResponse(StreamResponse):
    id: str  # file id
    conversation_id: Optional[str] = ""
    type: str  # only image
    belongs_to: str  # assistant
    url: str


class TtsMessageStreamResponse(StreamResponse):
    audio: str
    created_at: Optional[int] = None


class TextStreamData(BaseModel):
    text: str
    from_variable_selector: Optional[List[str]] = None


class TextChunkStreamResponse(StreamResponse):
    data: TextStreamData
    workflow_run_id: Optional[str] = ""


class TextReplaceStreamResponse(StreamResponse):
    data: TextStreamData
    workflow_run_id: Optional[str] = ""


class WorkflowsStreamResponse(StreamResponse):
    workflow_run_id: Optional[str] = ""
    data: Optional[Union[
        WorkflowStartedData,
        WorkflowFinishedData,
        NodeStartedData,
        NodeFinishedData,
        Dict[str, Any]]
    ] = None


class ChatWorkflowsStreamResponse(WorkflowsStreamResponse):
    message_id: Optional[str] = ""
    conversation_id: Optional[str] = ""
    created_at: Optional[int] = None


_COMPLETION_EVENT_TO_STREAM_RESP_MAPPING = {
    StreamEvent.PING: PingResponse,
    StreamEvent.MESSAGE: MessageStreamResponse,
    StreamEvent.MESSAGE_FILE: MessageFileStreamResponse,
    StreamEvent.TTS_MESSAGE: TtsMessageStreamResponse,
    StreamEvent.TTS_MESSAGE_END: TtsMessageStreamResponse,
    StreamEvent.MESSAGE_END: MessageEndStreamResponse,
    StreamEvent.MESSAGE_REPLACE: MessageReplaceStreamResponse,
}

CompletionStreamResponse = Union[
    PingResponse,
    MessageStreamResponse,
    MessageFileStreamResponse,
    TtsMessageStreamResponse,
    MessageEndStreamResponse,
    MessageReplaceStreamResponse,
]


def build_completion_stream_response(data: dict) -> CompletionStreamResponse:
    event = StreamEvent.new(data.get(STREAM_EVENT_KEY))
    return _COMPLETION_EVENT_TO_STREAM_RESP_MAPPING.get(event, StreamResponse)(**data)


_CHAT_EVENT_TO_STREAM_RESP_MAPPING = {
    StreamEvent.PING: PingResponse,
    # chat
    StreamEvent.MESSAGE: MessageStreamResponse,
    StreamEvent.TTS_MESSAGE: TtsMessageStreamResponse,
    StreamEvent.TTS_MESSAGE_END: TtsMessageStreamResponse,
    StreamEvent.MESSAGE_END: MessageEndStreamResponse,
    StreamEvent.MESSAGE_REPLACE: MessageReplaceStreamResponse,
    StreamEvent.MESSAGE_FILE: MessageFileStreamResponse,
    # agent
    StreamEvent.AGENT_MESSAGE: AgentMessageStreamResponse,
    StreamEvent.AGENT_THOUGHT: AgentThoughtStreamResponse,
    # workflow
    StreamEvent.WORKFLOW_STARTED: WorkflowsStreamResponse,
    StreamEvent.NODE_STARTED: WorkflowsStreamResponse,
    StreamEvent.NODE_FINISHED: WorkflowsStreamResponse,
    StreamEvent.NODE_RETRY: WorkflowsStreamResponse,
    StreamEvent.ITERATION_STARTED: WorkflowsStreamResponse,
    StreamEvent.ITERATION_NEXT: WorkflowsStreamResponse,
    StreamEvent.ITERATION_COMPLETED: WorkflowsStreamResponse,
    StreamEvent.LOOP_STARTED: WorkflowsStreamResponse,
    StreamEvent.LOOP_NEXT: WorkflowsStreamResponse,
    StreamEvent.LOOP_COMPLETED: WorkflowsStreamResponse,
    StreamEvent.TEXT_CHUNK: TextChunkStreamResponse,
    StreamEvent.TEXT_REPLACE: TextReplaceStreamResponse,
    StreamEvent.WORKFLOW_FINISHED: WorkflowsStreamResponse,
    StreamEvent.WORKFLOW_PAUSED: WorkflowsStreamResponse,
    StreamEvent.HUMAN_INPUT_REQUIRED: WorkflowsStreamResponse,
    StreamEvent.HUMAN_INPUT_FORM_FILLED: WorkflowsStreamResponse,
    StreamEvent.HUMAN_INPUT_FORM_TIMEOUT: WorkflowsStreamResponse,
    StreamEvent.PARALLEL_BRANCH_STARTED: WorkflowsStreamResponse,
    StreamEvent.PARALLEL_BRANCH_FINISHED: WorkflowsStreamResponse,
    StreamEvent.AGENT_LOG: WorkflowsStreamResponse,
}

ChatStreamResponse = Union[
    PingResponse,
    MessageStreamResponse,
    TtsMessageStreamResponse,
    MessageEndStreamResponse,
    MessageReplaceStreamResponse,
    MessageFileStreamResponse,
    AgentMessageStreamResponse,
    AgentThoughtStreamResponse,
    TextChunkStreamResponse,
    TextReplaceStreamResponse,
    WorkflowsStreamResponse,
]


def build_chat_stream_response(data: dict) -> ChatStreamResponse:
    event = StreamEvent.new(data.get(STREAM_EVENT_KEY))
    return _CHAT_EVENT_TO_STREAM_RESP_MAPPING.get(event, StreamResponse)(**data)


_WORKFLOW_EVENT_TO_STREAM_RESP_MAPPING = {
    StreamEvent.PING: PingResponse,
    # workflow
    StreamEvent.WORKFLOW_STARTED: WorkflowsStreamResponse,
    StreamEvent.NODE_STARTED: WorkflowsStreamResponse,
    StreamEvent.NODE_FINISHED: WorkflowsStreamResponse,
    StreamEvent.NODE_RETRY: WorkflowsStreamResponse,
    StreamEvent.ITERATION_STARTED: WorkflowsStreamResponse,
    StreamEvent.ITERATION_NEXT: WorkflowsStreamResponse,
    StreamEvent.ITERATION_COMPLETED: WorkflowsStreamResponse,
    StreamEvent.LOOP_STARTED: WorkflowsStreamResponse,
    StreamEvent.LOOP_NEXT: WorkflowsStreamResponse,
    StreamEvent.LOOP_COMPLETED: WorkflowsStreamResponse,
    StreamEvent.TEXT_CHUNK: TextChunkStreamResponse,
    StreamEvent.TEXT_REPLACE: TextReplaceStreamResponse,
    StreamEvent.WORKFLOW_FINISHED: WorkflowsStreamResponse,
    StreamEvent.WORKFLOW_PAUSED: WorkflowsStreamResponse,
    StreamEvent.TTS_MESSAGE: TtsMessageStreamResponse,
    StreamEvent.TTS_MESSAGE_END: TtsMessageStreamResponse,
    StreamEvent.HUMAN_INPUT_REQUIRED: WorkflowsStreamResponse,
    StreamEvent.HUMAN_INPUT_FORM_FILLED: WorkflowsStreamResponse,
    StreamEvent.HUMAN_INPUT_FORM_TIMEOUT: WorkflowsStreamResponse,
    StreamEvent.AGENT_LOG: WorkflowsStreamResponse,
}

WorkflowsRunStreamResponse = Union[
    PingResponse,
    TtsMessageStreamResponse,
    TextChunkStreamResponse,
    TextReplaceStreamResponse,
    WorkflowsStreamResponse,
]


def build_workflows_stream_response(data: dict) -> WorkflowsRunStreamResponse:
    event = StreamEvent.new(data.get(STREAM_EVENT_KEY))
    return _WORKFLOW_EVENT_TO_STREAM_RESP_MAPPING.get(event, StreamResponse)(**data)
