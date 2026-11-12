import logging
import unittest
from pathlib import Path
from ccswitch_manager import CCSwitchManager, EnvironmentState, Provider
from failover_manager import FailoverManager


class FailoverBoundaryTests(unittest.TestCase):
    def setUp(self):
        self.providers = (Provider("p1", "Primary", 0, True, True, "codex"), Provider("p2", "Backup", 1, False, True, "codex"))

    def state(self, ready=True, running=()):
        return EnvironmentState(True, "3.x", Path("cc-switch.db"), Path("config.toml"), "p1", self.providers, ready, ready, ready, ("p1", "p2") if ready else (), running)

    def test_primary_and_second_sorted_provider_are_explicit(self):
        self.assertEqual(self.state().current_provider.id, "p1")
        self.assertEqual(self.state().second_provider.id, "p2")

    def test_ready_requires_queue_p1_then_second_sorted_provider(self):
        valid = self.state()
        wrong_order = EnvironmentState(True, "3.x", Path("cc-switch.db"), Path("config.toml"), "p1", self.providers, True, True, True, ("p2", "p1"), ())
        wrong_target = EnvironmentState(True, "3.x", Path("cc-switch.db"), Path("config.toml"), "p1", self.providers, True, True, True, ("p1", "p3"), ())
        self.assertTrue(valid.failover_ready)
        self.assertFalse(wrong_order.failover_ready)
        self.assertFalse(wrong_target.failover_ready)

    def test_not_ready_manual_switch_never_modifies_provider(self):
        manager = CCSwitchManager.__new__(CCSwitchManager)
        self.assertEqual(FailoverManager(manager, self.state(ready=False), logging.getLogger("null")).manual_switch(), 2)

    def test_active_codex_is_never_stopped(self):
        from codex_manager import restart_policy
        self.assertIn("manual_restart_required", restart_policy(self.state(ready=False, running=("codex",))))


if __name__ == "__main__":
    unittest.main()
