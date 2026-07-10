import json
import os
import sys
from pathlib import Path

import gi

gi.require_version("Gtk", "3.0")
gi.require_version("WebKit2", "4.1")
from gi.repository import Gdk, GLib, Gtk, WebKit2

from .app import normalize_url, ui_dir
from .datastore import DESKTOP_UA, MOBILE_UA, DataStore
from .debug_log import log as debug_log
from .home_loader import HomeLoader
from .tab_manager import BrowserTab, TabManager
from .ui_server import LocalUIServer

SNAPSHOT_PATH = Path.home() / ".cache" / "nova-browser" / "startup-frame.png"

DARK_TOOLBAR_CSS = b"""
.nova-browser-bar, .nova-tab-strip-scroll {
  background-color: #14141c;
}
.nova-browser-bar entry {
  background-color: #2a2a38;
  color: #f5f5fa;
  border: 1px solid #44445a;
}
.nova-toolbar-btn, .nova-browser-bar button, .nova-tab-strip-scroll button {
  background-color: #2a2a38;
  color: #ffffff;
  border: 1px solid #55556a;
}
.nova-toolbar-btn label, .nova-browser-bar button label, .nova-tab-strip-scroll button label {
  color: #ffffff;
}
.nova-toolbar-btn:hover, .nova-browser-bar button:hover {
  background-color: #3d3d52;
  color: #ffffff;
}
.nova-browser-tab {
  background-color: #222230;
  color: #e8e8f2;
  border: 1px solid #44445a;
}
.nova-browser-tab:checked {
  background-color: #4a5a9f;
  color: #ffffff;
  border-color: #6b8cff;
}
.nova-browser-tab label { color: inherit; }
.nova-tab-close-btn { color: #ccccdd; background: transparent; border: none; }
.nova-tab-close-btn label { color: #ccccdd; }
"""

LIGHT_TOOLBAR_CSS = b"""
.nova-browser-bar, .nova-tab-strip-scroll {
  background-color: #f0f0f5;
}
.nova-browser-bar entry {
  background-color: #ffffff;
  color: #1a1a1a;
  border: 1px solid #ccccdd;
}
.nova-toolbar-btn, .nova-browser-bar button, .nova-tab-strip-scroll button {
  background-color: #ffffff;
  color: #1a1a1a;
  border: 1px solid #bbb;
}
.nova-toolbar-btn label, .nova-browser-bar button label, .nova-tab-strip-scroll button label {
  color: #1a1a1a;
}
.nova-toolbar-btn:hover, .nova-browser-bar button:hover {
  background-color: #e4e4ec;
  color: #000000;
}
.nova-browser-tab {
  background-color: #ffffff;
  color: #333333;
  border: 1px solid #ccccdd;
}
.nova-browser-tab:checked {
  background-color: #dbe4ff;
  color: #1a1a1a;
  border-color: #6b8cff;
}
.nova-browser-tab label { color: inherit; }
.nova-tab-close-btn { color: #666; background: transparent; border: none; }
.nova-tab-close-btn label { color: #666; }
"""


def _disable_webkit_sandbox() -> None:
    try:
        WebKit2.WebContext.get_default().set_sandbox_enabled(False)
    except Exception as exc:
        debug_log(f"sandbox disable skipped: {exc}")


class NovaBrowserWindow(Gtk.ApplicationWindow):
    def __init__(self, application) -> None:
        _disable_webkit_sandbox()
        super().__init__(application=application, title="Nova Browser")
        self.set_default_size(480, 820)
        self.set_position(Gtk.WindowPosition.CENTER)
        self.datastore = DataStore()
        self.home_loader = HomeLoader(self.datastore)
        self.home_url = ""
        self._bridged_tabs: set[str] = set()
        self._toolbar_css_provider: Gtk.CssProvider | None = None

        ui_root = ui_dir()
        if not (ui_root / "index.html").is_file():
            raise RuntimeError(
                f"Nova Browser UI not found at {ui_root}.\n"
                f"Run: {Path(__file__).resolve().parents[2] / 'Nova-Browser'}"
            )

        self.ui_server = LocalUIServer(
            self.home_loader.build_home_html,
            self.home_loader.build_browser_html,
        )
        self.home_url = self.ui_server.start()

        self._apply_base_theme()

        self.browser_toolbar = self._build_browser_toolbar()

        self.tabs = TabManager(
            self,
            self._setup_tab_webview,
            self._on_active_tab_changed,
            self._navigate_tab,
        )
        self.tabs.btn_new_tab.connect("clicked", lambda *_: self._open_new_tab())
        self.tabs.btn_new_island.connect("clicked", lambda *_: self.tabs.prompt_new_island())

        self.root_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.root_box.pack_start(self.browser_toolbar, False, False, 0)
        self.root_box.pack_start(self.tabs.tab_strip_scroll, False, False, 0)
        self.root_box.pack_start(self.tabs.page_stack, True, True, 0)
        self.add(self.root_box)

        self._apply_toolbar_theme()

        self.webview = None  # set after first tab for tests

        self.connect("map-event", self._on_window_mapped)
        self.connect("key-press-event", self._on_key_press)
        self.connect("destroy", lambda *_: self.ui_server.stop())

        debug_log(f"ready url={self.home_url} ui={ui_root}")

    def _on_window_mapped(self, widget, event) -> bool:
        if not self.tabs.tabs:
            self._open_new_tab()
        return False

    def _apply_base_theme(self) -> None:
        css = b"""
        window, .nova-shell { background-color: #0a0a12; }
        .nova-browser-bar {
          border-bottom: 1px solid rgba(128, 128, 128, 0.25);
          padding: 8px;
        }
        .nova-tab-strip-scroll {
          border-bottom: 1px solid rgba(128, 128, 128, 0.2);
        }
        .nova-toolbar-btn, .nova-browser-bar button, .nova-tab-strip-scroll button {
          min-width: 36px;
          min-height: 36px;
          padding: 4px 8px;
          border-radius: 8px;
          font-weight: 600;
          background-image: none;
          -gtk-icon-shadow: none;
        }
        .nova-browser-bar entry {
          min-height: 36px;
          padding: 0 12px;
          border-radius: 18px;
        }
        .nova-tab-island { border-radius: 10px; padding: 2px 6px; }
        .nova-browser-tab {
          min-height: 28px;
          padding: 2px 10px;
          border-radius: 8px;
        }
        .nova-tab-close-btn { min-width: 24px; min-height: 24px; padding: 0; }
        """
        provider = Gtk.CssProvider()
        provider.load_from_data(css)
        Gtk.StyleContext.add_provider_for_screen(
            Gdk.Screen.get_default(),
            provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION,
        )

    def _apply_toolbar_theme(self) -> None:
        is_light = self._is_light_toolbar()
        css_data = LIGHT_TOOLBAR_CSS if is_light else DARK_TOOLBAR_CSS
        if self._toolbar_css_provider is None:
            self._toolbar_css_provider = Gtk.CssProvider()
            Gtk.StyleContext.add_provider_for_screen(
                Gdk.Screen.get_default(),
                self._toolbar_css_provider,
                Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION + 1,
            )
        self._toolbar_css_provider.load_from_data(css_data)
        self._apply_toolbar_button_colors(is_light)
        self.tabs.apply_toolbar_colors(is_light)

    @staticmethod
    def _is_light_color(hex_color: str) -> bool:
        match = str(hex_color or "").strip().lower()
        if match.startswith("#") and len(match) == 7:
            r = int(match[1:3], 16) / 255
            g = int(match[3:5], 16) / 255
            b = int(match[5:7], 16) / 255
            luminance = 0.2126 * r + 0.7152 * g + 0.0722 * b
            return luminance > 0.62
        return False

    def _is_light_toolbar(self) -> bool:
        theme = self.datastore.as_dict().get("theme", {})
        mode = theme.get("mode", "space")
        if mode == "white":
            return True
        if mode == "custom":
            return self._is_light_color(theme.get("customBgColor", "#0a0a12"))
        return False

    def _apply_toolbar_button_colors(self, is_light: bool) -> None:
        fg = Gdk.RGBA()
        fg.parse("#1a1a1a" if is_light else "#ffffff")
        bg = Gdk.RGBA()
        bg.parse("#ffffff" if is_light else "#2a2a38")
        bg_hover = Gdk.RGBA()
        bg_hover.parse("#e4e4ec" if is_light else "#3d3d52")

        buttons = (
            self.btn_back,
            self.btn_forward,
            self.btn_reload,
            self.btn_new_tab,
            self.btn_home,
        )
        for btn in buttons:
            if not btn:
                continue
            btn.override_color(Gtk.StateFlags.NORMAL, fg)
            btn.override_color(Gtk.StateFlags.PRELIGHT, fg)
            btn.override_color(Gtk.StateFlags.ACTIVE, fg)
            btn.override_background_color(Gtk.StateFlags.NORMAL, bg)
            btn.override_background_color(Gtk.StateFlags.PRELIGHT, bg_hover)
            for child in btn.get_children():
                if isinstance(child, Gtk.Label):
                    child.override_color(Gtk.StateFlags.NORMAL, fg)
                    child.override_color(Gtk.StateFlags.PRELIGHT, fg)
                    child.override_color(Gtk.StateFlags.ACTIVE, fg)

    def _build_browser_toolbar(self) -> Gtk.Box:
        bar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        bar.get_style_context().add_class("nova-browser-bar")

        def mkbtn(label: str, tip: str, handler):
            btn = Gtk.Button.new_with_label(label)
            btn.get_style_context().add_class("nova-toolbar-btn")
            btn.set_tooltip_text(tip)
            btn.connect("clicked", handler)
            return btn

        self.btn_back = mkbtn("←", "Back", lambda *_: self._browser_go_back())
        self.btn_forward = mkbtn("→", "Forward", lambda *_: self._browser_go_forward())
        self.url_entry = Gtk.Entry()
        self.url_entry.set_placeholder_text("Search or enter URL")
        self.url_entry.connect("activate", self._on_url_entry_activate)
        self.btn_reload = mkbtn("↻", "Reload", lambda *_: self._reload_active_tab())
        self.btn_new_tab = mkbtn("+", "New tab (Ctrl+T)", lambda *_: self._open_new_tab())
        self.btn_home = mkbtn("⌂", "Nova home in this tab", lambda *_: self._go_home_in_tab())

        for w in (
            self.btn_back,
            self.btn_forward,
            self.url_entry,
            self.btn_reload,
            self.btn_new_tab,
            self.btn_home,
        ):
            expand = w is self.url_entry
            bar.pack_start(w, expand, expand, 0)

        return bar

    def _setup_tab_webview(self, webview: WebKit2.WebView, tab_id: str) -> None:
        settings = webview.get_settings()
        settings.set_enable_javascript(True)
        settings.set_enable_developer_extras(True)
        rgba = Gdk.RGBA()
        rgba.parse("#0a0a12")
        webview.set_background_color(rgba)

        manager = webview.get_user_content_manager()
        try:
            manager.register_script_message_handler("nova")
            manager.connect(
                "script-message-received::nova",
                self._on_script_message,
                tab_id,
            )
        except Exception as exc:
            debug_log(f"message handler register failed: {exc}")

        webview.connect("load-changed", self._on_tab_load_changed, tab_id)

    def _on_tab_load_changed(self, webview: WebKit2.WebView, load_event, tab_id: str) -> None:
        if load_event != WebKit2.LoadEvent.FINISHED:
            return
        uri = webview.get_uri() or ""
        if uri.startswith("http://127.0.0.1:"):
            GLib.idle_add(self._inject_bridge, tab_id)

    def _navigate_tab(self, tab: BrowserTab, target: str) -> None:
        if self.tabs.active_tab_id != tab.id:
            self.tabs.activate_tab(tab.id)

        def do_load() -> bool:
            if tab.id not in {t.id for t in self.tabs.tabs}:
                return False
            tab.webview.show_all()
            self.tabs.page_stack.show_all()
            if target == "":
                self._load_tab_home(tab)
            else:
                self._load_tab_site(tab, target)
            return False

        GLib.idle_add(do_load)

    def _load_tab_home(self, tab: BrowserTab) -> None:
        self.ui_server.refresh()
        html = self.home_loader.build_home_html()
        debug_log(f"tab home load html bytes={len(html)} tab={tab.id[:8]}")
        if tab.webview.is_loading():
            tab.webview.stop_loading()
        tab.webview.load_html(html, self.home_url)
        tab.url = self.home_url
        tab.is_home = True
        tab.title = "Nova"
        self._bridged_tabs.discard(tab.id)

    def _load_tab_site(self, tab: BrowserTab, url: str) -> None:
        normalized = self._normalize(url)
        if not normalized:
            return
        self._apply_browser_settings(tab.webview)
        debug_log(f"tab site load {normalized} tab={tab.id[:8]}")
        tab.url = normalized
        tab.is_home = False
        if tab.webview.is_loading():
            tab.webview.stop_loading()
        tab.webview.load_uri(normalized)

    def _inject_bridge(self, tab_id: str) -> bool:
        tab = self.tabs.tab_by_id(tab_id)
        if not tab or tab_id in self._bridged_tabs:
            return False
        uri = tab.webview.get_uri() or ""
        if not uri.startswith("http://127.0.0.1:"):
            return False
        ui_str = str(ui_dir())
        if ui_str not in sys.path:
            sys.path.insert(0, ui_str)
        from bundle import native_bridge_js

        script = native_bridge_js(self.datastore.get_data())
        script += "\nif (typeof refreshUI === 'function') { refreshUI(); }\n"

        def on_done(webview, result, _u):
            try:
                webview.evaluate_javascript_finish(result)
                self._bridged_tabs.add(tab_id)
                debug_log(f"bridge injected tab={tab_id[:8]}")
            except Exception as exc:
                debug_log(f"bridge inject failed: {exc}")

        tab.webview.evaluate_javascript(script, -1, None, None, None, on_done, None)
        return False

    def _go_home_in_tab(self) -> None:
        self.tabs.go_home_in_active_tab()

    def show_site(self, url: str, new_tab: bool = False) -> None:
        tab = self.tabs.open_url(url, new_tab=new_tab)
        if not tab.is_home:
            self.url_entry.set_text(self._normalize(url))
        self._on_active_tab_changed()

    def _open_new_tab(self) -> bool:
        tab = self.tabs.new_tab(load_home=True)
        self.webview = tab.webview
        self.url_entry.set_text("")
        self.set_title("Nova Browser")
        return False

    def _reload_active_tab(self) -> None:
        tab = self.tabs.get_active_tab()
        if not tab:
            return
        if tab.is_home:
            self._navigate_tab(tab, "")
        else:
            tab.webview.reload()

    def _on_active_tab_changed(self) -> None:
        tab = self.tabs.get_active_tab()
        if not tab:
            return
        self.webview = tab.webview
        if tab.is_home:
            self.url_entry.set_text("")
            self.set_title("Nova Browser")
        else:
            uri = tab.webview.get_uri() or tab.url
            if uri:
                self.url_entry.set_text(uri)
            self.set_title(f"{tab.title} — Nova Browser")
        self._apply_browser_settings(tab.webview)
        self._update_nav_buttons()

    def _browser_go_back(self) -> None:
        webview = self.tabs.get_active_webview()
        if webview and webview.can_go_back():
            webview.go_back()
            return
        if len(self.tabs.tabs) > 1:
            self.tabs.prev_tab()

    def _browser_go_forward(self) -> None:
        webview = self.tabs.get_active_webview()
        if webview and webview.can_go_forward():
            webview.go_forward()

    def _on_url_entry_activate(self, entry) -> None:
        self.show_site(entry.get_text())

    def _update_nav_buttons(self) -> None:
        webview = self.tabs.get_active_webview()
        self.btn_back.set_sensitive(bool(webview and (webview.can_go_back() or len(self.tabs.tabs) > 1)))
        self.btn_forward.set_sensitive(bool(webview and webview.can_go_forward()))

    def _on_script_message(self, manager, message, tab_id: str) -> None:
        try:
            body = message.get_js_value().to_string()
        except Exception:
            try:
                body = message.get_body().get_data().decode("utf-8")
            except Exception:
                return
        try:
            payload = json.loads(body)
        except Exception:
            return

        tab = self.tabs.tab_by_id(tab_id)
        if not tab:
            return

        op = payload.get("op")
        if op == "saveData":
            self.datastore.save_data(payload.get("json", "{}"))
            self.ui_server.refresh()
            self._apply_toolbar_theme()
        elif op == "openUrl":
            self.show_site(payload.get("url", ""), new_tab=bool(payload.get("newTab")))
        elif op == "goHome":
            self._navigate_tab(tab, "")
        elif op == "pickImage":
            self._pick_image(tab)
        elif op == "clearData":
            self._clear_browsing_data()
        elif op == "browserGoBack":
            self._browser_go_back()
        elif op == "browserGoForward":
            self._browser_go_forward()

    def _on_key_press(self, widget, event) -> bool:
        ctrl = event.state & Gdk.ModifierType.CONTROL_MASK
        if ctrl and event.keyval in (Gdk.KEY_t, Gdk.KEY_T):
            self._open_new_tab()
            return True
        if ctrl and event.keyval in (Gdk.KEY_w, Gdk.KEY_W):
            if self.tabs.active_tab_id:
                self.tabs.close_tab(self.tabs.active_tab_id)
            return True
        if ctrl and event.keyval == Gdk.KEY_Tab:
            if event.state & Gdk.ModifierType.SHIFT_MASK:
                self.tabs.prev_tab()
            else:
                self.tabs.next_tab()
            return True
        if event.keyval in (Gdk.KEY_Escape, Gdk.KEY_Home):
            self._go_home_in_tab()
            return True
        if event.keyval in (Gdk.KEY_Back, Gdk.KEY_Left) and event.state & Gdk.ModifierType.ALT_MASK:
            self._browser_go_back()
            return True
        if event.keyval in (Gdk.KEY_Forward, Gdk.KEY_Right) and event.state & Gdk.ModifierType.ALT_MASK:
            self._browser_go_forward()
            return True
        return False

    def _settings(self) -> dict:
        return self.datastore.as_dict().get("settings", {})

    def _normalize(self, raw: str) -> str:
        return normalize_url(raw, self._settings().get("searchEngine", "google"))

    def _apply_browser_settings(self, webview: WebKit2.WebView) -> None:
        settings = self._settings()
        web_settings = webview.get_settings()
        web_settings.set_enable_javascript(settings.get("javascriptEnabled", True))
        web_settings.set_user_agent(
            DESKTOP_UA if settings.get("desktopMode", False) else MOBILE_UA
        )
        zoom = max(75, min(150, int(settings.get("zoomLevel", 100))))
        try:
            webview.set_zoom_level((zoom - 100) / 25.0)
        except Exception:
            pass

    def _clear_browsing_data(self) -> None:
        for webview in self.tabs.all_webviews():
            manager = webview.get_context().get_website_data_manager()
            types = (
                WebKit2.WebsiteDataTypes.COOKIES
                | WebKit2.WebsiteDataTypes.DISK_CACHE
                | WebKit2.WebsiteDataTypes.MEMORY_CACHE
                | WebKit2.WebsiteDataTypes.SESSION_STORAGE
                | WebKit2.WebsiteDataTypes.LOCAL_STORAGE
            )
            manager.clear(types, 0, None, None, None)

    def _pick_image(self, tab: BrowserTab) -> None:
        dialog = Gtk.FileChooserDialog(
            title="Choose background image",
            parent=self,
            action=Gtk.FileChooserAction.OPEN,
        )
        dialog.add_buttons(
            Gtk.STOCK_CANCEL,
            Gtk.ResponseType.CANCEL,
            Gtk.STOCK_OPEN,
            Gtk.ResponseType.OK,
        )
        filt = Gtk.FileFilter()
        filt.set_name("Images")
        filt.add_mime_type("image/*")
        dialog.add_filter(filt)

        def on_response(dialog, response) -> None:
            data_url = ""
            if response == Gtk.ResponseType.OK:
                path = dialog.get_filename()
                if path:
                    import base64
                    import mimetypes

                    mime = mimetypes.guess_type(path)[0] or "image/jpeg"
                    encoded = base64.b64encode(Path(path).read_bytes()).decode("ascii")
                    data_url = f"data:{mime};base64,{encoded}"
            dialog.destroy()
            escaped = data_url.replace("\\", "\\\\").replace("'", "\\'")
            tab.webview.run_javascript(
                f"window.__novaImageCallback && window.__novaImageCallback('{escaped}');"
            )

        dialog.connect("response", on_response)
        dialog.show()

    # Legacy name used by tests / scripts
    def show_home(self) -> bool:
        self._go_home_in_tab()
        return False
