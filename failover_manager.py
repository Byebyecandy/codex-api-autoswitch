from __future__ import annotations

import logging
from ccswitch_manager import CCSwitchManager, EnvironmentState


class FailoverManager:
    def __init__(self, manager: CCSwitchManager, state: EnvironmentState, log: logging.Logger) -> None:
        self.manager, self.state, self.log = manager, state, log

    def manual_switch(self) -> int:
        if not self.state.ccswitch_installed:
            self.log.error("CC Switch is not installed or its data directory was not found")
        elif not self.state.failover_ready:
            self.log.error("Native Codex routing/failover is disabled; no provider was changed")
        elif not self.state.second_provider:
            self.log.error("A second Codex provider is not configured")
        else:
            self.log.error("Provider changes must be made through CC Switch UI. The watchdog never writes its database or credentials.")
        return 2

    def observe_failure(self, classification) -> bool:
        if not classification.should_failover:
            self.log.info("No failover: %s (%s)", classification.label, classification.reason)
            return False
        if not self.state.failover_ready:
            self.log.error("Failover condition observed, but CC Switch native failover is not ready")
            return False
        self.log.warning("Failover condition observed; CC Switch native routing owns provider switching")
        return True
