try:
    from enum import StrEnum
except ImportError:
    from strenum import StrEnum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from dify_client.models.base import ResponseMode, File


class WorkflowStatus(StrEnum):
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    STOPPED = "stopped"
    PARTIAL_SUCCEEDED = "partial-succeeded"
    PAUSED = "paused"
    EXCEPTION = "exception"


class ExecutionMetadata(BaseModel):
    total_tokens: Optional[int] = None
    total_price: Optional[float] = None
    currency: Optional[str] = None


class WorkflowStartedData(BaseModel):
    id: str  # workflow run id
    workflow_id: str  # workflow id
    sequence_number: Optional[int] = None
    inputs: Optional[Dict[str, Any]] = None
    created_at: int  # unix timestamp seconds
    reason: Optional[str] = None


class NodeStartedData(BaseModel):
    id: str  # workflow run id
    node_id: str
    node_type: str
    title: str
    index: int
    predecessor_node_id: Optional[str] = None
    inputs: Optional[Dict[str, Any]] = None
    inputs_truncated: Optional[bool] = None
    created_at: int
    extras: Dict[str, Any] = Field(default_factory=dict)
    iteration_id: Optional[str] = None
    loop_id: Optional[str] = None


class NodeFinishedData(BaseModel):
    id: str  # workflow run id
    node_id: str
    node_type: str
    title: str
    index: int
    predecessor_node_id: Optional[str] = None
    inputs: Optional[Dict[str, Any]] = None
    inputs_truncated: Optional[bool] = None
    process_data: Optional[Dict[str, Any]] = None
    process_data_truncated: Optional[bool] = None
    outputs: Optional[Dict[str, Any]] = Field(default_factory=dict)
    outputs_truncated: Optional[bool] = None
    status: WorkflowStatus
    error: Optional[str] = None
    elapsed_time: Optional[float]  # seconds
    execution_metadata: Optional[ExecutionMetadata] = None
    created_at: int
    finished_at: int
    files: List[Dict[str, Any]] = Field(default_factory=list)
    iteration_id: Optional[str] = None
    loop_id: Optional[str] = None
    retry_index: Optional[int] = None


class WorkflowFinishedData(BaseModel):
    id: str  # workflow run id
    workflow_id: str  # workflow id
    sequence_number: Optional[int] = None
    status: WorkflowStatus
    outputs: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    elapsed_time: Optional[float] = None
    total_tokens: Optional[int] = None
    total_steps: Optional[int] = 0
    created_at: int
    finished_at: Optional[int] = None
    created_by: Dict[str, Any] = Field(default_factory=dict)
    exceptions_count: Optional[int] = None
    files: List[Dict[str, Any]] = Field(default_factory=list)


class WorkflowsRunRequest(BaseModel):
    inputs: Dict[str, Any] = Field(default_factory=dict)
    response_mode: ResponseMode
    user: str
    files: List[File] = Field(default_factory=list)


class WorkflowsRunResponse(BaseModel):
    workflow_run_id: Optional[str] = None
    # Backward compatibility with older API responses.
    log_id: Optional[str] = None
    task_id: str
    data: WorkflowFinishedData
