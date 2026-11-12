# Codex API AutoSwitch Watchdog

A Windows watchdog for Codex installations managed by CC Switch. It audits provider order and native routing state, classifies errors passed to its classifier, and avoids editing CC Switch or Codex configuration files.

> **Current scope:** live Codex request interception and automatic Direct-mode switching are not implemented. CC Switch Routing + Failover remains responsible for live failover.

## Compatibility

- Windows 10 22H2 and Windows 11
- Python 3.10–3.14 (standard library only)
- CC Switch versions whose SQLite database has the `providers` and `proxy_config` schema used by this project
- Codex CLI or Desktop metadata inspection; this tool does not restart either client

Other operating systems are not supported by the current process and executable discovery code. Unknown CC Switch database schemas fail closed.

## Quick Start

1. Install Python 3.10 or later and CC Switch.
2. Run `install.bat` (creates a project-local virtual environment; no global Python packages are installed).
3. Run `doctor.bat` and review the detected Provider order and routing state.
4. In CC Switch, review and enable Codex Routing + Failover. Set the active provider as P1 and the second Provider in sorted Codex order as P2.
5. Run `doctor.bat` again. `failover_ready` must be true before starting the watchdog.
6. Run `start.bat` in a terminal or configure it in Windows Task Scheduler for sign-in startup.

This checkout was inspected with Windows 10 build 19045, Python 3.14 and CC Switch 3.16.3. At inspection time Routing and Failover were disabled and the queue was empty, so the watchdog correctly refused to start.

## Commands

```powershell
py -3 main.py doctor  # installation, Provider order, routing/failover readiness
py -3 main.py status  # concise runtime state
py -3 main.py test    # run the explicitly configured endpoint probe, if any
py -3 main.py start   # foreground monitor; suitable for Task Scheduler
py -3 main.py stop    # request a graceful stop
py -3 main.py switch  # validate readiness; Provider changes remain in CC Switch UI
```

The optional probe in `config.json` is disabled by default. Configure only a non-secret health endpoint that is appropriate for the local Routing proxy. The probe sends an unauthenticated GET and is not a substitute for testing the configured model or account.

## Safety and Limitations

- The watchdog never edits `config.toml`, `auth.json`, the CC Switch database, Provider credentials, or failover queues.
- It does not terminate Codex processes or inspect private conversation logs.
- `classify_error()` classifies a supplied status/body/exception. The monitor currently does not receive live Codex response events, so classification alone does not trigger a provider change.
- With native Routing + Failover enabled and correctly ordered, CC Switch handles request retries, circuit breaking and live upstream failover. Avoid running a second independent failover controller.
- Direct mode is not automatically switched. Review a Provider change in CC Switch and restart Codex yourself when required.
- `doctor` reports Provider names and ordering but never reads API key fields. Logs are stored under `%LOCALAPPDATA%\CodexApiAutoSwitch` with secret-pattern redaction.

## Development

```powershell
py -3 -m unittest discover -s tests -v
py -3 -m py_compile main.py ccswitch_manager.py error_classifier.py failover_manager.py codex_manager.py health_check.py logger.py monitor.py
```

See [CONTRIBUTING.md](CONTRIBUTING.md), [SECURITY.md](SECURITY.md), and [remind.md](remind.md) before changing integrations or safety behavior.
