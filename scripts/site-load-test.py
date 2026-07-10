#!/usr/bin/env python3
"""Verify external sites load in an active tab WebView."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "linux"))
os.environ["NOVA_BROWSER_UI"] = str(ROOT / "shared" / "ui")

import gi

gi.require_version("Gtk", "3.0")
gi.require_version("WebKit2", "4.1")
from gi.repository import GLib, Gtk  # noqa: E402

RESULT: dict = {"ok": False, "steps": []}


def main() -> int:
    from nova_browser.window import NovaBrowserWindow

    win_holder: dict = {}
    app = Gtk.Application(application_id="com.nova.browser.site-test")

    def on_activate(application):
        win = NovaBrowserWindow(application=application)
        win.show_all()
        win_holder["win"] = win

    app.connect("activate", on_activate)
    app.register()
    app.activate()

    def step(name: str, ok: bool, detail: str = "") -> None:
        RESULT["steps"].append({"name": name, "ok": ok, "detail": detail})

    def finish(ok: bool, reason: str) -> bool:
        RESULT["ok"] = ok
        RESULT["reason"] = reason
        Gtk.main_quit()
        return False

    def after_home(_u=None):
        win = win_holder.get("win")
        if not win or not win.tabs.get_active_tab():
            return finish(False, "no window/tab after startup")

        step("home_tab", True, win.tabs.get_active_tab().id[:8])
        win.show_site("https://example.com")

        def check_site(_u=None):
            tab = win.tabs.get_active_tab()
            wv = tab.webview if tab else None
            if not wv:
                return finish(False, "no webview")

            uri = wv.get_uri() or ""
            if "example.com" not in uri:
                return True  # keep polling

            def on_js(_wv, res, _u2):
                try:
                    val = _wv.evaluate_javascript_finish(res)
                    data = json.loads(val.to_string())
                    ok = "Example Domain" in data.get("title", "") or "example" in data.get("text", "").lower()
                    step("example_com", ok, json.dumps(data)[:120])
                    if not ok:
                        finish(False, "example.com content missing")
                        return
                    win._go_home_in_tab()

                    def check_home(_u3=None):
                        tab2 = win.tabs.get_active_tab()
                        if not tab2 or not tab2.is_home:
                            uri2 = tab2.webview.get_uri() if tab2 else ""
                            if uri2.startswith("http://127.0.0.1:"):
                                tab2.is_home = True
                            else:
                                return True
                        step("home_in_same_tab", len(win.tabs.tabs) == 1, f"tabs={len(win.tabs.tabs)}")
                        win._open_new_tab()

                        def check_new_tab(_u4=None):
                            tabs = win.tabs.tabs
                            if len(tabs) < 2:
                                return True
                            new_tab = tabs[-1]
                            uri3 = new_tab.webview.get_uri() or ""
                            ok = uri3.startswith("http://127.0.0.1:") or new_tab.is_home
                            step("new_tab_home", ok, uri3[:60])
                            finish(ok and len(tabs) == 2, "new tab home flow")

                        GLib.timeout_add(1500, check_new_tab)
                        return False

                    GLib.timeout_add(1500, check_home)
                    return False
                except Exception as exc:
                    finish(False, f"js eval: {exc}")
                return False

            wv.evaluate_javascript(
                "JSON.stringify({title:document.title,text:(document.body.innerText||'').slice(0,80),href:location.href})",
                -1,
                None,
                None,
                None,
                on_js,
                None,
            )
            return False

        GLib.timeout_add(500, check_site)
        return False

    GLib.timeout_add(2500, after_home)
    GLib.timeout_add_seconds(25, lambda: finish(False, "timeout"))
    Gtk.main()
    print(json.dumps(RESULT, indent=2))
    return 0 if RESULT.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
