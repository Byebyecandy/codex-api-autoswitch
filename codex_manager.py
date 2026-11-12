from ccswitch_manager import EnvironmentState


def restart_policy(state: EnvironmentState) -> str:
    if not state.codex_processes:
        return "not_running"
    if state.routing_enabled:
        return "no_restart_needed_for_upstream_switch"
    return "manual_restart_required; active Codex work will not be terminated"
