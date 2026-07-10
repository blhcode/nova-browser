#!/usr/bin/env python3
"""Verify Nova Browser paints real UI pixels (not a blank white WebView)."""

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
from gi.repository import GLib, Gtk, WebKit2  # noqa: E402

RESULT: dict = {"ok": False}


def sample_webview_colors(webview) -> dict:
    region = WebKit2.SnapshotRegion.FULL_DOCUMENT

    def on_snapshot(wv, res, _u):
        try:
            surf = wv.get_snapshot_finish(res)
            w, h = surf.get_width(), surf.get_height()
            data = surf.get_data()
            stride = surf.get_stride()
            dark = light = 0
            samples = 0
            for y in range(0, h, max(1, h // 15)):
                for x in range(0, w, max(1, w // 15)):
                    i = y * stride + x * 4
                    if i + 2 >= len(data):
                        continue
                    lum = (
                        0.299 * data[i]
                        + 0.587 * data[i + 1]
                        + 0.114 * data[i + 2]
                    )
                    if lum < 50:
                        dark += 1
                    elif lum > 230:
                        light += 1
                    samples += 1
            RESULT["snapshot"] = {
                "w": w,
                "h": h,
                "dark": dark,
                "light": light,
                "samples": samples,
            }
            RESULT["ok"] = dark > samples * 0.08 and light < samples * 0.9
            if not RESULT["ok"]:
                RESULT["reason"] = f"bad pixels dark={dark} light={light} samples={samples}"
            else:
                RESULT["reason"] = "dark themed UI pixels detected"
        except Exception as exc:
            RESULT["reason"] = f"snapshot: {exc}"
        Gtk.main_quit()

    try:
        webview.get_snapshot(
            region,
            WebKit2.SnapshotOptions.NONE,
            None,
            on_snapshot,
            None,
        )
    except Exception as exc:
        RESULT["reason"] = f"get_snapshot: {exc}"
        Gtk.main_quit()


def main() -> int:
    from nova_browser.window import NovaBrowserWindow

    win_holder: dict = {}

    app = Gtk.Application(application_id="com.nova.browser.test")

    def on_activate(application):
        win = NovaBrowserWindow(application=application)
        win.show_all()
        win_holder["win"] = win

    app.connect("activate", on_activate)
    app.register()
    app.activate()

    def verify():
        win = win_holder.get("win")
        if not win:
            RESULT["reason"] = "window not created"
            Gtk.main_quit()
            return False
        wv = win.webview or win.tabs.get_active_webview()
        if not wv:
            RESULT["reason"] = "no active webview"
            Gtk.main_quit()
            return False

        def on_js(wv, res, _u):
            try:
                val = wv.evaluate_javascript_finish(res)
                RESULT["js"] = json.loads(val.to_string())
            except Exception as exc:
                RESULT["js_error"] = str(exc)
            sample_webview_colors(wv)

        wv.evaluate_javascript(
            "JSON.stringify({text:(document.body.innerText||'').slice(0,60),"
            "href:location.href,bg:getComputedStyle(document.body).backgroundColor})",
            -1,
            None,
            None,
            None,
            on_js,
            None,
        )
        return False

    GLib.timeout_add(5000, verify)
    GLib.timeout_add_seconds(12, Gtk.main_quit)
    Gtk.main()
    print(json.dumps(RESULT, indent=2))
    return 0 if RESULT.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
