# Changelog

## 1.0.3 - 2026-03-25

### Added

- Added audio models and client methods:
  - `audio_to_text` / `aaudio_to_text`
  - `text_to_audio` / `atext_to_audio`
- Added stream event support for newer Dify runtime events:
  - `tts_message`, `workflow_paused`, `iteration_*`, `loop_*`
  - `text_chunk`, `text_replace`
  - `human_input_required`, `human_input_form_filled`, `human_input_form_timeout`
- Added compatibility fallback for workflow stop endpoint:
  - tries `/workflows/tasks/{task_id}/stop`
  - falls back to `/workflows/{task_id}/stop` on not found
- Added tests for stream parsing, audio APIs, and endpoint compatibility fallback.

### Changed

- Updated package metadata:
  - `python_requires` is `>=3.8`
  - `pydantic>=2,<3`
- Updated file models to include new file types:
  - `image`, `document`, `audio`, `video`, `custom`
- Updated response/request models to align with latest runtime schema:
  - completion, workflow, and file upload models now include newer fields.
- Updated CI and build scripts to ensure `setuptools` and `wheel` are installed for `python -m build --no-isolation`.

### Fixed

- Fixed Python 3.8/3.12 CI build failures caused by missing build backend dependencies.
- Fixed packaging scope to include subpackages.
- Hardened error parsing for non-JSON HTTP/SSE error bodies.
