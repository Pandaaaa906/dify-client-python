from dify_client import models


def test_completion_stream_supports_tts_message():
    item = models.build_completion_stream_response(
        {
            "event": "tts_message",
            "task_id": "task-1",
            "message_id": "msg-1",
            "audio": "BASE64_AUDIO",
        }
    )
    assert isinstance(item, models.TtsMessageStreamResponse)
    assert item.audio == "BASE64_AUDIO"


def test_chat_stream_supports_text_chunk_events():
    item = models.build_chat_stream_response(
        {
            "event": "text_chunk",
            "task_id": "task-1",
            "workflow_run_id": "run-1",
            "data": {
                "text": "partial answer",
                "from_variable_selector": ["body", "text"],
            },
        }
    )
    assert isinstance(item, models.TextChunkStreamResponse)
    assert item.data.text == "partial answer"
    assert item.data.from_variable_selector == ["body", "text"]


def test_workflow_stream_supports_workflow_paused():
    item = models.build_workflows_stream_response(
        {
            "event": "workflow_paused",
            "task_id": "task-1",
            "workflow_run_id": "run-1",
            "data": {
                "paused_nodes": ["node-1"],
                "status": "paused",
            },
        }
    )
    assert isinstance(item, models.WorkflowsStreamResponse)
    assert item.event == models.StreamEvent.WORKFLOW_PAUSED
