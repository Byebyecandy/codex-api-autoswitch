from __future__ import annotations

import argparse
import json
from ccswitch_manager import CCSwitchManager, EnvironmentError
from failover_manager import FailoverManager
from health_check import run_configured_probe
from logger import get_logger
from monitor import Monitor


def main() -> int:
    parser = argparse.ArgumentParser(description="Codex and CC Switch API failover watchdog")
    parser.add_argument("command", choices=("start", "stop", "status", "switch", "test", "doctor"))
    parser.add_argument("--confirm-enable-routing", action="store_true", help="Confirmation flag; enablement must be performed in the CC Switch UI")
    args = parser.parse_args()
    log = get_logger()
    manager = CCSwitchManager()
    try:
        state = manager.inspect()
    except EnvironmentError as exc:
        log.error("CC Switch inspection failed: %s", exc)
        return 2
    if args.command == "doctor":
        print(json.dumps(state.doctor_report(), indent=2, ensure_ascii=False))
        return 0 if state.ccswitch_installed else 1
    if args.command == "status":
        print(json.dumps(state.status_report(), indent=2, ensure_ascii=False))
        return 0
    if args.command == "test":
        report = run_configured_probe(state, manager.config)
        print(json.dumps(report, indent=2, ensure_ascii=False))
        return 0 if report["ok"] else 1
    if args.command == "stop":
        return Monitor.stop(manager.runtime_dir)
    if args.command == "start":
        if not state.failover_ready:
            print("Native CC Switch Codex routing/failover is not ready. Review doctor output and configure it in CC Switch UI.")
            return 2
        return Monitor(manager, state, log).run_as_service()
    if args.command == "switch":
        return FailoverManager(manager, state, log).manual_switch()
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
