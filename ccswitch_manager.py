from __future__ import annotations

import json
import os
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Any


class EnvironmentError(RuntimeError):
    pass


def _truthy(value: Any) -> bool:
    return str(value).strip().casefold() in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class Provider:
    id: str
    name: str
    sort_index: int
    is_current: bool
    in_failover_queue: bool
    provider_type: str | None


@dataclass(frozen=True)
class EnvironmentState:
    ccswitch_installed: bool
    ccswitch_version: str | None
    db_path: Path | None
    codex_config: Path
    current_provider_id: str | None
    providers: tuple[Provider, ...]
    proxy_enabled: bool
    routing_enabled: bool
    failover_enabled: bool
    failover_providers: tuple[str, ...]
    codex_processes: tuple[str, ...]

    @property
    def current_provider(self) -> Provider | None:
        return next((p for p in self.providers if p.id == self.current_provider_id), None)

    @property
    def second_provider(self) -> Provider | None:
        return self.providers[1] if len(self.providers) > 1 else None

    @property
    def failover_ready(self) -> bool:
        expected = [p.id for p in (self.current_provider, self.second_provider) if p is not None]
        return self.proxy_enabled and self.routing_enabled and self.failover_enabled and len(expected) == 2 and list(self.failover_providers[:2]) == expected

    def status_report(self) -> dict[str, Any]:
        return {"ccswitch_version": self.ccswitch_version, "routing_enabled": self.routing_enabled, "failover_enabled": self.failover_enabled, "current_provider": self.current_provider.name if self.current_provider else None, "providers_in_sort_order": [p.name for p in self.providers], "default_second_provider": self.second_provider.name if self.second_provider else None, "failover_queue": list(self.failover_providers), "codex_processes": list(self.codex_processes), "failover_ready": self.failover_ready}

    def doctor_report(self) -> dict[str, Any]:
        return {"os": os.name, "ccswitch_installed": self.ccswitch_installed, "ccswitch_version": self.ccswitch_version, "ccswitch_database_found": self.db_path is not None, "codex_config_found": self.codex_config.exists(), "codex_current_provider": self.current_provider.name if self.current_provider else None, "codex_provider_order": [p.name for p in self.providers], "default_backup_provider": self.second_provider.name if self.second_provider else None, "routing_enabled": self.routing_enabled, "failover_enabled": self.failover_enabled, "failover_queue": list(self.failover_providers), "codex_processes": list(self.codex_processes), "recommendation": "Enable Codex Routing and Failover in CC Switch UI, then add current provider as P1 and second sorted provider as P2." if not self.failover_ready else "Native failover is configured; watchdog can observe its state.", "secrets_read": False}


class CCSwitchManager:
    def __init__(self) -> None:
        self.config = self._load_config()
        self.home = Path(os.environ.get("USERPROFILE", str(Path.home())))
        self.codex_dir = Path(self.config.get("codex_dir") or self.home / ".codex")
        self.codex_config = self.codex_dir / "config.toml"
        self.cc_dir = Path(self.config.get("ccswitch_dir") or self.home / ".cc-switch")
        self.runtime_dir = Path(os.environ.get("LOCALAPPDATA", str(self.home))) / "CodexApiAutoSwitch"

    @staticmethod
    def _load_config() -> dict[str, Any]:
        config_path = Path(__file__).with_name("config.json")
        try:
            return json.loads(config_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise EnvironmentError(f"Could not load {config_path.name}: {exc}") from exc

    def inspect(self) -> EnvironmentState:
        db = self.cc_dir / "cc-switch.db"
        executable = Path(self.config.get("ccswitch_executable", r"D:\CC Switch\cc-switch.exe"))
        settings: dict[str, Any] = {}
        providers: list[Provider] = []
        current_id: str | None = None
        proxy_enabled = routing_enabled = failover_enabled = False
        queue: list[str] = []
        if db.exists():
            try:
                connection = sqlite3.connect(f"file:{db.as_posix()}?mode=ro", uri=True, timeout=2)
                try:
                    tables = {row[0] for row in connection.execute("SELECT name FROM sqlite_master WHERE type='table'")}
                    if "providers" not in tables:
                        raise EnvironmentError("CC Switch database schema is unsupported")
                    rows = connection.execute("SELECT CAST(id AS BLOB),CAST(name AS BLOB),sort_index,is_current,in_failover_queue,CAST(provider_type AS BLOB) FROM providers WHERE app_type='codex' ORDER BY sort_index,created_at").fetchall()
                    providers = [Provider(bytes(r[0]).decode("utf-8", errors="replace"), bytes(r[1]).decode("utf-8", errors="replace"), int(r[2] or 0), bool(r[3]), bool(r[4]), bytes(r[5]).decode("utf-8", errors="replace") if r[5] is not None else None) for r in rows]
                    current_id = next((p.id for p in providers if p.is_current), None)
                    if "settings" in tables:
                        settings = dict(connection.execute("SELECT key,value FROM settings"))
                    if "proxy_config" in tables:
                        row = connection.execute("SELECT proxy_enabled,enabled,auto_failover_enabled FROM proxy_config WHERE app_type='codex'").fetchone()
                        if row:
                            proxy_enabled, routing_enabled, failover_enabled = map(bool, row)
                    queue = [p.id for p in providers if p.in_failover_queue]
                finally:
                    connection.close()
            except sqlite3.Error as exc:
                raise EnvironmentError(f"Could not safely read CC Switch database: {exc}") from exc
        settings_path = self.cc_dir / "settings.json"
        if settings_path.exists():
            try:
                settings = {**json.loads(settings_path.read_text(encoding="utf-8")), **settings}
            except (OSError, json.JSONDecodeError):
                pass
        if "enableLocalProxy" in settings:
            proxy_enabled = _truthy(settings["enableLocalProxy"])
            routing_enabled = proxy_enabled
        if "enableFailoverToggle" in settings:
            failover_enabled = _truthy(settings["enableFailoverToggle"])
        version = settings.get("version") or settings.get("appVersion")
        if not version and executable.exists() and os.name == "nt":
            try:
                import subprocess
                result = subprocess.run(["powershell", "-NoProfile", "-Command", f"(Get-Item -LiteralPath '{str(executable).replace(chr(39), chr(39)*2)}').VersionInfo.ProductVersion"], capture_output=True, text=True, timeout=5, check=False)
                version = result.stdout.strip() or None
            except (OSError, subprocess.TimeoutExpired):
                version = None
        state = EnvironmentState(bool(executable.exists() or db.exists()), version, db if db.exists() else None, self.codex_config, current_id, tuple(providers), proxy_enabled, routing_enabled, failover_enabled, tuple(queue), self._codex_process_names())
        return state

    @staticmethod
    def _codex_process_names() -> tuple[str, ...]:
        if os.name != "nt":
            return ()
        import subprocess
        try:
            result = subprocess.run(["powershell", "-NoProfile", "-Command", "Get-Process -Name codex -ErrorAction SilentlyContinue | ForEach-Object { $_.ProcessName }"], capture_output=True, text=True, timeout=5, check=False)
            return tuple(x.strip() for x in result.stdout.splitlines() if x.strip())
        except (OSError, subprocess.TimeoutExpired):
            return ()
