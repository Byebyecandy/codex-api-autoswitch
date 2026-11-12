from __future__ import annotations

from typing import Any
from ccswitch_manager import EnvironmentState


def run_configured_probe(state: EnvironmentState, config: dict[str, Any]) -> dict[str, Any]:
    endpoint = config.get("health_check", {}).get("endpoint")
    if not endpoint:
        return {"ok": False, "mode": "configuration", "message": "No safe health endpoint is configured; no API request was sent."}
    if not state.routing_enabled:
        return {"ok": False, "mode": "configuration", "message": "Codex Routing is disabled; no API request was sent."}
    import urllib.error
    import urllib.request
    request = urllib.request.Request(endpoint, headers={"User-Agent": "CodexApiAutoSwitch/1.0"}, method="GET")
    try:
        with urllib.request.urlopen(request, timeout=int(config.get("request_timeout_seconds", 10))) as response:
            return {"ok": 200 <= response.status < 400, "status": response.status, "mode": "configured_endpoint"}
    except urllib.error.HTTPError as exc:
        return {"ok": False, "status": exc.code, "mode": "configured_endpoint"}
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        return {"ok": False, "mode": "configured_endpoint", "error_type": type(exc).__name__}
