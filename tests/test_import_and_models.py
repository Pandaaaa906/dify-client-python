from dify_client import AsyncClient, Client, models


def test_imports_and_type_annotations_work_on_python39_plus():
    client = Client(api_key="token")
    async_client = AsyncClient(api_key="token")
    assert client.api_base == "https://api.dify.ai/v1"
    assert async_client.api_base == "https://api.dify.ai/v1"
    assert models.Mode.ADVANCED_CHAT.value == "advanced-chat"
    assert models.Mode.ADAVANCED_CHAT == models.Mode.ADVANCED_CHAT


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
