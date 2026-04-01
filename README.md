# dify-client-python

`dify-client-python` is a typed Python SDK for Dify Runtime APIs, covering chat, completion, workflow, file upload, feedback, and audio conversion endpoints.

## Requirements

- Python `>=3.8`
- Dify Runtime API (cloud or self-hosted) compatible with `/v1` endpoints

## Installation

```bash
pip install dify-client-python
```

## What Is Supported

- Sync and async clients: `Client`, `AsyncClient`
- Blocking and streaming response modes
- Chat and completion message APIs
- Workflow run/stream/stop APIs
- File upload APIs
- Message feedback and suggestion APIs
- Audio APIs:
  - `audio-to-text`
  - `text-to-audio`
- Updated stream event support for newer workflow/chatflow runtimes:
  - `workflow_paused`, `iteration_*`, `loop_*`, `text_chunk`, `text_replace`
  - `human_input_*`, `node_retry`, `agent_log`, `tts_message`

## Quick Start (Sync)

```python
import uuid
from dify_client import Client, models

client = Client(
    api_key="your-api-key",
    api_base="https://api.dify.ai/v1",
)
user = str(uuid.uuid4())

req = models.ChatRequest(
    query="Hello from dify-client-python",
    inputs={},
    user=user,
    response_mode=models.ResponseMode.BLOCKING,
)

res = client.chat_messages(req, timeout=60.0)
print(res.answer)
```

### Streaming Chat

```python
stream_req = models.ChatRequest(
    query="Stream this answer",
    inputs={},
    user=user,
    response_mode=models.ResponseMode.STREAMING,
)

for event in client.chat_messages(stream_req, timeout=60.0):
    print(event.event, getattr(event, "answer", None))
```

### Audio APIs

```python
audio_text = client.audio_to_text(
    ("sample.wav", open("sample.wav", "rb"), "audio/wav"),
    models.AudioToTextRequest(user=user),
)
print(audio_text.text)

audio_bytes = client.text_to_audio(
    models.TextToAudioRequest(text="Hello world", user=user)
)
with open("speech.mp3", "wb") as f:
    f.write(audio_bytes)
```

## Quick Start (Async)

```python
import asyncio
from dify_client import AsyncClient, models

async_client = AsyncClient(api_key="your-api-key", api_base="https://api.dify.ai/v1")

async def main():
    req = models.ChatRequest(
        query="hello",
        inputs={},
        user="user-1",
        response_mode=models.ResponseMode.STREAMING,
    )
    async for chunk in await async_client.achat_messages(req, timeout=60.0):
        print(chunk.event)

asyncio.run(main())
```

## Security Notes

- Do not hardcode production API keys in source code.
- Prefer environment variables or secret managers for `api_key`.
- The SDK injects `Authorization: Bearer ...` headers, but does not log keys by default.
- If you add your own logging middleware around requests, redact `Authorization` headers.

## Development

```bash
python -m pip install -e . pytest pytest-cov flake8 build twine setuptools wheel
python -m flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics
python -m pytest -q --cov=dify_client --cov-report=term-missing
python -m build --no-isolation
python -m twine check --strict dist/*
```

## Release

Use [RELEASE.md](./RELEASE.md) for the release checklist and commands.
