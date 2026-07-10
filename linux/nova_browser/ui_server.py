"""Embedded HTTP server — same pages as scripts/dev-server.py plus browser.html."""

from __future__ import annotations

import socket
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Callable


class LocalUIServer:
    def __init__(
        self,
        home_builder: Callable[[], str],
        browser_builder: Callable[[], str],
    ) -> None:
        self._home_builder = home_builder
        self._browser_builder = browser_builder
        self._home_bytes = b""
        self._browser_bytes = b""
        self._httpd: ThreadingHTTPServer | None = None
        self._thread: threading.Thread | None = None
        self.port = 0
        self._handler_cls = None

    def refresh(self) -> None:
        self._home_bytes = self._home_builder().encode("utf-8")
        self._browser_bytes = self._browser_builder().encode("utf-8")
        if self._handler_cls is not None:
            self._handler_cls.home_bytes = self._home_bytes
            self._handler_cls.browser_bytes = self._browser_bytes

    def _build_handler(self):
        home_payload = self._home_bytes
        browser_payload = self._browser_bytes

        class Handler(BaseHTTPRequestHandler):
            home_bytes = home_payload
            browser_bytes = browser_payload

            def do_GET(self) -> None:
                if self.path in ("/", "/index.html"):
                    body = self.home_bytes
                elif self.path.startswith("/browser.html"):
                    body = self.browser_bytes
                else:
                    self.send_error(404)
                    return
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(body)))
                self.send_header("Cache-Control", "no-store")
                self.end_headers()
                self.wfile.write(body)

            def log_message(self, format, *args):
                return

        self._handler_cls = Handler
        return Handler

    def start(self) -> str:
        self.refresh()
        handler = self._build_handler()
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind(("127.0.0.1", 0))
        self.port = sock.getsockname()[1]
        sock.close()

        self._httpd = ThreadingHTTPServer(("127.0.0.1", self.port), handler)
        self._thread = threading.Thread(target=self._httpd.serve_forever, daemon=True)
        self._thread.start()
        return f"http://127.0.0.1:{self.port}/"

    def stop(self) -> None:
        if self._httpd:
            self._httpd.shutdown()
            self._httpd.server_close()
            self._httpd = None
