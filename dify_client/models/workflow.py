try:
    from enum import StrEnum
except ImportError:
    from strenum import StrEnum
from typing import Dict, List, Optional

from pydantic import BaseModel, Field

from dify_client.models.base import ResponseMode, File


class WorkflowStatus(StrEnum):
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    STOPPED = "stopped"


class ExecutionMetadata(BaseModel):
    total_tokens: Optional[int] = None
    total_price: Optional[str] = None
    currency: Optional[str] = None


class WorkflowStartedData(BaseModel):
    id: str  # workflow run id
    workflow_id: str  # workflow id
    sequence_number: Optional[int] = None
    inputs: Optional[dict] = None
    created_at: int  # unix timestamp seconds


class NodeStartedData(BaseModel):
    id: str  # workflow run id
    node_id: str
    node_type: str
    title: str
    index: int
    predecessor_node_id: Optional[str] = None
    inputs: Optional[dict] = None
    created_at: int
    extras: dict = Field(default_factory=dict)


class NodeFinishedData(BaseModel):
    id: str  # workflow run id
    node_id: str
    node_type: str
    title: str
    index: int
    predecessor_node_id: Optional[str] = None
    inputs: Optional[dict] = None
    process_data: Optional[dict] = None
    outputs: Optional[dict] = Field(default_factory=dict)
    status: WorkflowStatus
    error: Optional[str] = None
    elapsed_time: Optional[float]  # seconds
    execution_metadata: Optional[ExecutionMetadata] = None
    created_at: int
    finished_at: int
    files: List = Field(default_factory=list)


class WorkflowFinishedData(BaseModel):
    id: str  # workflow run id
    workflow_id: str  # workflow id
    sequence_number: int
    status: WorkflowStatus
    outputs: Optional[dict] = None
    error: Optional[str] = None
    elapsed_time: Optional[float] = None
    total_tokens: Optional[int] = None
    total_steps: Optional[int] = 0
    created_at: int
    finished_at: int
    created_by: dict = Field(default_factory=dict)
    files: List = Field(default_factory=list)


class WorkflowsRunRequest(BaseModel):
    inputs: Dict = Field(default_factory=dict)
    response_mode: ResponseMode
    user: str
    conversation_id: Optional[str] = ""
    files: List[File] = Field(default_factory=list)


class WorkflowsRunResponse(BaseModel):
    log_id: str
    task_id: str
    data: WorkflowFinishedData
