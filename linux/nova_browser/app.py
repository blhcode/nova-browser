import json
import os
import sys
from pathlib import Path
from urllib.parse import quote

import gi

gi.require_version("Gtk", "3.0")
gi.require_version("WebKit2", "4.1")
from gi.repository import GLib, Gtk, WebKit2


SEARCH_ENGINES = {
    "google": "https://www.google.com/search?q=",
    "duckduckgo": "https://duckduckgo.com/?q=",
    "bing": "https://www.bing.com/search?q=",
    "brave": "https://search.brave.com/search?q=",
}


def normalize_url(raw: str, search_engine: str = "google") -> str:
    trimmed = (raw or "").strip()
    if not trimmed:
        return trimmed
    lower = trimmed.lower()
    if lower.startswith("http://") or lower.startswith("https://"):
        return trimmed
    if "." in trimmed and " " not in trimmed:
        return f"https://{trimmed}"
    base = SEARCH_ENGINES.get(search_engine, SEARCH_ENGINES["google"])
    return f"{base}{quote(trimmed)}"


def ui_dir() -> Path:
    env = os.environ.get("NOVA_BROWSER_UI")
    if env:
        return Path(env)

    installed = Path("/usr/share/nova-browser/ui")
    if (installed / "index.html").is_file():
        return installed

    # Development fallback when running from the repo without installing.
    repo_ui = Path(__file__).resolve().parents[2] / "shared" / "ui"
    if (repo_ui / "index.html").is_file():
        return repo_ui

    return installed


class NovaBrowserApp(Gtk.Application):
    def __init__(self) -> None:
        super().__init__(application_id="com.nova.browser")
        self.window = None

    def do_activate(self) -> None:
        if not self.window:
            try:
                from .window import NovaBrowserWindow

                self.window = NovaBrowserWindow(application=self)
            except RuntimeError as exc:
                dialog = Gtk.MessageDialog(
                    transient_for=None,
                    flags=0,
                    message_type=Gtk.MessageType.ERROR,
                    buttons=Gtk.ButtonsType.OK,
                    text="Nova Browser failed to start",
                )
                dialog.format_secondary_text(str(exc))
                dialog.run()
                dialog.destroy()
                return
        self.window.show_all()
        self.window.present()
        if not self.window.tabs.tabs:
            self.window._open_new_tab()


def main() -> int:
    app = NovaBrowserApp()
    return app.run(sys.argv)


if __name__ == "__main__":
    raise SystemExit(main())
