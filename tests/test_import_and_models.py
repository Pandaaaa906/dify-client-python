from dify_client import AsyncClient, Client, models


def test_imports_and_type_annotations_work_on_python38_plus():
    client = Client(api_key="token")
    async_client = AsyncClient(api_key="token")
    assert client.api_base == "https://api.dify.ai/v1"
    assert async_client.api_base == "https://api.dify.ai/v1"
    assert models.Mode.ADVANCED_CHAT.value == "advanced-chat"
    assert models.Mode.ADAVANCED_CHAT == models.Mode.ADVANCED_CHAT
    assert models.FileType.DOCUMENT.value == "document"
    assert models.FileType.AUDIO.value == "audio"
    assert models.FileType.VIDEO.value == "video"
    assert models.FileType.CUSTOM.value == "custom"


def test_completion_request_supports_inputs_and_legacy_query():
    req = models.CompletionRequest(
        response_mode=models.ResponseMode.BLOCKING,
        user="u1",
    )
    assert req.inputs == {}
    assert req.query == ""


def test_workflows_run_response_accepts_workflow_run_id():
    res = models.WorkflowsRunResponse(
        task_id="task-1",
        workflow_run_id="run-1",
        data=models.WorkflowFinishedData(
            id="run-1",
            workflow_id="wf-1",
            status=models.WorkflowStatus.SUCCEEDED,
            created_at=1,
            finished_at=2,
        ),
    )
    assert res.workflow_run_id == "run-1"


def test_mutable_defaults_are_not_shared_between_instances():
    chat_req_a = models.ChatRequest(
        query="hello",
        response_mode=models.ResponseMode.BLOCKING,
        user="u1",
    )
    chat_req_b = models.ChatRequest(
        query="world",
        response_mode=models.ResponseMode.BLOCKING,
        user="u2",
    )

    chat_req_a.files.append(
        models.File(
            type=models.FileType.IMAGE,
            transfer_method=models.TransferMethod.REMOTE_URL,
            url="https://example.com/a.png",
        )
    )

    assert chat_req_b.files == []

    workflow_req_a = models.WorkflowsRunRequest(
        response_mode=models.ResponseMode.BLOCKING,
        user="u1",
    )
    workflow_req_b = models.WorkflowsRunRequest(
        response_mode=models.ResponseMode.BLOCKING,
        user="u2",
    )

    workflow_req_a.inputs["city"] = "beijing"
    assert workflow_req_b.inputs == {}
