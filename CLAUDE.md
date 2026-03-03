# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is `dify-client-python`, a Python client library for the [Dify API](https://dify.ai). It provides both synchronous (`Client`) and asynchronous (`AsyncClient`) interfaces for interacting with Dify's completion, chat, workflow, and file upload APIs.

## Development Environment

The project uses `uv` for Python environment management. The virtual environment is at `.venv/` with Python 3.12.

### Installing Dependencies

The project uses `uv` for Python environment and dependency management.

```bash
# Install package in development mode (editable install)
uv pip install -e .

# Install with dev dependencies (ruff for linting)
uv pip install -e . --group dev

# Sync all dependencies from lock file (if exists)
uv sync
```

### Linting

The project uses **ruff** for linting (configured in `pyproject.toml` dependency groups):

```bash
# Install dev dependencies (includes ruff)
uv pip install --group dev

# Check for linting errors
ruff check .

# Auto-fix linting errors
ruff check . --fix

# Format code
ruff format .
```

### Testing

Tests are run with pytest:

```bash
# Install pytest if not already installed
uv pip install pytest

# Run tests
pytest
```

Note: The project currently has no test files. When adding tests, follow the pytest framework.

### Building and Publishing

**Local Build:**
```bash
# Build package (creates dist/ with wheel and sdist)
uv build
```

**Automated Release (Recommended):**

项目配置了 GitHub Actions 自动 release 工作流。当你推送版本标签时，会自动创建 GitHub Release：

```bash
# 1. 更新 pyproject.toml 中的 version
# 2. 提交并推送更改
git add pyproject.toml
git commit -m "Bump version to 1.0.2"
git push

# 3. 创建并推送版本标签 (触发 release 工作流)
git tag v1.0.2
git push origin v1.0.2
```

触发后会自动执行：
- 运行 ruff 代码检查
- 运行 pytest 测试
- 构建 wheel 和 sdist
- 创建 GitHub Release (包含构建产物)

**手动发布到 PyPI (如需):**
```bash
uv build
uv publish
# 或使用 twine
python -m twine upload dist/*
```

## Architecture

### Package Structure

```
dify_client/
├── __init__.py          # Exports Client and AsyncClient
├── _clientx.py          # Core implementation (~660 lines)
├── errors.py            # Exception classes and error handling
├── models/              # Pydantic models for all API operations
│   ├── base.py          # Shared base models (ResponseMode, File, Usage, etc.)
│   ├── chat.py          # Chat request/response models
│   ├── completion.py    # Completion (text generation) models
│   ├── workflow.py      # Workflow execution models
│   ├── feedback.py      # Message feedback models
│   ├── file.py          # File upload models
│   └── stream.py        # Streaming event types and response builders
└── utils/
    └── _common.py       # String-to-enum conversion utility
```

### Client Architecture

**`Client`** and **`AsyncClient`** (`_clientx.py`):
- Both extend `pydantic.BaseModel` for configuration (api_key, api_base)
- Share module-level httpx clients (`_httpx_client`, `_async_httpx_client`)
- Mirror methods: `chat_messages` → `achat_messages`, `run_workflows` → `arun_workflows`, etc.
- Support both blocking and streaming response modes via `ResponseMode` enum

**Streaming Support**:
- Streaming uses Server-Sent Events (SSE) via `httpx-sse`
- `request_stream()` returns `Iterator[ServerSentEvent]` (or `AsyncIterator`)
- Events are mapped to typed response models via `stream.py` builders
- PING events are filtered out automatically (`IGNORED_STREAM_EVENTS`)

**Error Handling** (`errors.py`):
- All errors extend `DifyAPIError` base class
- Specific error types mapped by API error code (e.g., `invalid_param` → `DifyInvalidParam`)
- `raise_for_status()` handles both regular responses and SSE error events
- HTTP 404 raises `DifyResourceNotFound`, 500 raises `DifyInternalServerError`

### API Endpoint Mapping

Endpoints are defined as string constants in `_clientx.py`:

```python
ENDPOINT_CHAT_MESSAGES = "/chat-messages"
ENDPOINT_COMPLETION_MESSAGES = "/completion-messages"
ENDPOINT_RUN_WORKFLOWS = "/workflows/run"
ENDPOINT_FILES_UPLOAD = "/files/upload"
# ... etc
```

### Response Model Factory

`stream.py` contains event-to-model mapping dictionaries:
- `_COMPLETION_EVENT_TO_STREAM_RESP_MAPPING` - for completion streaming
- `_CHAT_EVENT_TO_STREAM_RESP_MAPPING` - for chat streaming
- `_WORKFLOW_EVENT_TO_STREAM_RESP_MAPPING` - for workflow streaming

Unknown event types fall back to base `StreamResponse` class.

## Key Patterns

**Adding a New Stream Event Type**:
1. Add event name to `StreamEvent` enum in `stream.py`
2. If needed, create a new response model class extending `StreamResponse`
3. Add mapping to appropriate `_*_EVENT_TO_STREAM_RESP_MAPPING` dict
4. Events are automatically handled via `StreamEvent.new()` validator which tolerates unknown events

**Request/Response Flow**:
1. User creates request model (e.g., `ChatRequest`)
2. Client method checks `response_mode` and routes to blocking or streaming implementation
3. Request is serialized via `model_dump()` and sent via httpx
4. Response JSON is parsed into typed response model
5. For streaming, SSE events are yielded and transformed by event type

**Python Version Compatibility**:
- Supports Python 3.8+
- Uses `StrEnum` backport from `strenum` for older Python versions
- Uses `HTTPMethod` polyfill for Python < 3.11

## CI/CD

**`.github/workflows/python-package.yml`** - 持续集成
- 触发条件: push 到 master 分支, 或 pull_request 到 master
- 测试 Python 3.8, 3.9, 3.10, 3.11, 3.12
- 运行 ruff linting 和格式化检查
- 运行 pytest

**`.github/workflows/release.yml`** - 自动发布
- 触发条件: 推送 `v*` 标签 (如 `v1.0.2`)
- 运行测试和 lint 检查
- 构建 wheel 和 sdist
- 创建 GitHub Release (自动生成 release notes, 包含构建产物)

## Common Tasks

**Adding a new API endpoint**:
1. Define endpoint constant in `_clientx.py`
2. Add request/response models in appropriate `models/` file
3. Implement sync method in `Client` class
4. Implement async method in `AsyncClient` class
5. Export models in `models/__init__.py`

**Adding a model field**:
- Models use Pydantic v2 with `ConfigDict(extra='allow')` for forward compatibility
- Optional fields should have sensible defaults
- Unix timestamp fields are typed as `int`
