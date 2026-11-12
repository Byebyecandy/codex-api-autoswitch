from __future__ import annotations

import logging
import re
from logging.handlers import RotatingFileHandler
from pathlib import Path


SECRET_PATTERNS = (
    re.compile(r"(?i)(authorization\s*[:=]\s*(?:bearer\s+)?)[^\s,;]+"),
    re.compile(r"(?i)(api[_-]?key\s*[:=]\s*)[^\s,;]+"),
    re.compile(r"\bsk-[A-Za-z0-9_-]{12,}\b"),
)


class RedactingFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        message = super().format(record)
        for pattern in SECRET_PATTERNS:
            message = pattern.sub(lambda m: (m.group(1) + "<redacted>") if m.lastindex else "<redacted>", message)
        return message


def get_logger() -> logging.Logger:
    logger = logging.getLogger("codex_api_autoswitch")
    if logger.handlers:
        return logger
    logger.setLevel(logging.INFO)
    runtime_dir = Path.home() / "AppData" / "Local" / "CodexApiAutoSwitch"
    runtime_dir.mkdir(parents=True, exist_ok=True)
    formatter = RedactingFormatter("%(asctime)s %(levelname)s %(message)s", "%Y-%m-%d %H:%M:%S")
    file_handler = RotatingFileHandler(runtime_dir / "watchdog.log", maxBytes=2_000_000, backupCount=3, encoding="utf-8")
    file_handler.setFormatter(formatter)
    console = logging.StreamHandler()
    console.setFormatter(formatter)
    logger.addHandler(file_handler)
    logger.addHandler(console)
    return logger
