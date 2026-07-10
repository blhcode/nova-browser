"""Minimal startup logging for troubleshooting."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path


def log(message: str) -> None:
    try:
        path = Path.home() / ".cache" / "nova-browser" / "startup.log"
        path.parent.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        with path.open("a", encoding="utf-8") as handle:
            handle.write(f"{stamp} {message}\n")
    except OSError:
        pass
