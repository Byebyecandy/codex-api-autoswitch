from __future__ import annotations

import os
import signal
import time
from pathlib import Path
from ccswitch_manager import CCSwitchManager, EnvironmentState
from codex_manager import restart_policy
from health_check import run_configured_probe


class Monitor:
    def __init__(self, manager: CCSwitchManager, state: EnvironmentState, log) -> None:
        self.manager, self.state, self.log = manager, state, log
        self.pid_path = manager.runtime_dir / "watchdog.pid"
        self.stop_path = manager.runtime_dir / "stop"
        self._running = True

    def run_as_service(self) -> int:
        self.manager.runtime_dir.mkdir(parents=True, exist_ok=True)
        if self.pid_path.exists():
            try:
                old_pid = int(self.pid_path.read_text(encoding="ascii").strip())
                os.kill(old_pid, 0)
                self.log.error("Watchdog already appears to be running (PID %s)", old_pid)
                return 2
            except (ValueError, OSError):
                self.pid_path.unlink(missing_ok=True)
        self.stop_path.unlink(missing_ok=True)
        self.pid_path.write_text(str(os.getpid()), encoding="ascii")
        if os.name == "nt":
            signal.signal(signal.SIGTERM, lambda *_: setattr(self, "_running", False))
        self.log.info("Watchdog started; Codex process policy: %s", restart_policy(self.state))
        try:
            interval = max(10, int(self.manager.config.get("check_interval_seconds", 60)))
            while self._running and not self.stop_path.exists():
                try:
                    fresh = self.manager.inspect()
                    report = run_configured_probe(fresh, self.manager.config)
                    if not report["ok"]:
                        self.log.warning("Health probe not successful: %s", report.get("message", report.get("status", report.get("error_type", "unknown"))))
                except Exception as exc:
                    self.log.error("Monitor cycle failed: %s", type(exc).__name__)
                for _ in range(interval):
                    if not self._running or self.stop_path.exists():
                        break
                    time.sleep(1)
        finally:
            self.pid_path.unlink(missing_ok=True)
            self.log.info("Watchdog stopped")
        return 0

    @staticmethod
    def stop(runtime_dir: Path) -> int:
        if not (runtime_dir / "watchdog.pid").exists():
            print("Watchdog is not running")
            return 1
        runtime_dir.mkdir(parents=True, exist_ok=True)
        (runtime_dir / "stop").write_text("stop", encoding="ascii")
        print("Stop signal sent")
        return 0
