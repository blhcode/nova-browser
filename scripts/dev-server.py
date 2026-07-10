#!/usr/bin/env python3
"""Serve the Nova Browser UI (bundled) from the correct directory."""

from __future__ import annotations

import os
import signal
import socket
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "shared" / "ui"))

from bundle import bundle_ui_html, ui_directory  # noqa: E402

PORT = 8765
UI_DIR = ui_directory()


class Handler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        if self.path not in ("/", "/index.html"):
            self.send_error(404, "Use / for Nova Browser UI")
            return

        try:
            body = bundle_ui_html(UI_DIR).encode("utf-8")
        except FileNotFoundError as exc:
            self.send_error(500, str(exc))
            return

        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format, *args):
        print(format % args)


def port_in_use(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            sock.bind(("", port))
        except OSError:
            return True
    return False


def stop_stale_servers() -> None:
    for port in (8080, 8765):
        if not port_in_use(port):
            continue
        os.system(f"fuser -k {port}/tcp >/dev/null 2>&1")


def main() -> None:
    if not (UI_DIR / "index.html").is_file():
        raise SystemExit(f"UI not found at {UI_DIR}")

    stop_stale_servers()

    if port_in_use(PORT):
        raise SystemExit(
            f"Port {PORT} is still in use. Stop the other process and retry."
        )

    with ThreadingHTTPServer(("", PORT), Handler) as server:
        url = f"http://localhost:{PORT}/"
        print(f"Serving bundled Nova Browser UI from:\n  {UI_DIR}")
        print(f"\nOpen: {url}")
        print("Press Ctrl+C to stop.\n")

        if os.environ.get("NOVA_OPEN_BROWSER", "1") == "1":
            os.system(f"xdg-open '{url}' >/dev/null 2>&1 &")

        try:
            server.serve_forever()
        except KeyboardInterrupt:
            print("\nStopped.")


if __name__ == "__main__":
    main()
