# Contributing

## Development Setup

Use Python 3.10 or later on Windows 10/11. The runtime uses only the Python standard library.

```powershell
py -3 -m venv .venv
.venv\Scripts\Activate.ps1
py -3 -m unittest discover -s tests -v
```

## Changes

- Keep changes focused and preserve read-only access to CC Switch and Codex configuration.
- Add tests for error classification, provider ordering, schema compatibility, and process safety when behavior changes.
- Do not add credentials, machine-specific paths, database snapshots, or runtime logs to commits.
- Update README and `remind.md` when supported versions, safety boundaries, or runtime behavior change.

## Pull Requests

Explain the user-visible behavior, supported versions, tests run, and any integration limitations. Never include API keys or private request/response content in examples or logs.
