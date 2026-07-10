"""Multi-tab browsing with grouped tab islands."""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import Callable

from gi.repository import Gdk, GLib, Gtk, WebKit2

ISLAND_COLORS = ("#6b8cff", "#51cf66", "#ff6b6b", "#ffd43b", "#cc5de8", "#20c997")


@dataclass
class BrowserTab:
    id: str
    island_id: str
    webview: WebKit2.WebView
    title: str = "Nova"
    url: str = ""
    is_home: bool = True
    button: Gtk.ToggleButton | None = None


@dataclass
class TabIsland:
    id: str
    name: str
    color: str
    collapsed: bool = False


class TabManager:
    def __init__(
        self,
        window: Gtk.Window,
        setup_webview: Callable[[WebKit2.WebView, str], None],
        on_active_changed: Callable[[], None],
        on_navigate: Callable[[BrowserTab, str], None],
    ) -> None:
        self.window = window
        self._setup_webview = setup_webview
        self._on_active_changed = on_active_changed
        self._on_navigate = on_navigate
        self.islands: list[TabIsland] = []
        self.tabs: list[BrowserTab] = []
        self.active_tab_id: str | None = None
        self._color_index = 0

        self.page_stack = Gtk.Stack()
        self.page_stack.set_transition_type(Gtk.StackTransitionType.NONE)
        self.page_stack.set_hexpand(True)
        self.page_stack.set_vexpand(True)

        self.tab_strip_scroll = Gtk.ScrolledWindow()
        self.tab_strip_scroll.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.NEVER)
        self.tab_strip_scroll.set_min_content_height(44)
        self.tab_strip_scroll.get_style_context().add_class("nova-tab-strip-scroll")

        self.tab_strip = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        self.tab_strip.set_border_width(6)
        self.tab_strip_scroll.add(self.tab_strip)

        self.btn_new_tab = Gtk.Button.new_with_label("+")
        self.btn_new_tab.get_style_context().add_class("nova-toolbar-btn")
        self.btn_new_tab.set_tooltip_text("New tab (Ctrl+T)")

        self.btn_new_island = Gtk.Button.new_with_label("⊞")
        self.btn_new_island.get_style_context().add_class("nova-toolbar-btn")
        self.btn_new_island.set_tooltip_text("New tab island")

        default_island = self.create_island("General")
        self._default_island_id = default_island.id

    def apply_toolbar_colors(self, is_light: bool) -> None:
        fg = Gdk.RGBA()
        fg.parse("#1a1a1a" if is_light else "#ffffff")
        bg = Gdk.RGBA()
        bg.parse("#ffffff" if is_light else "#2a2a38")
        bg_hover = Gdk.RGBA()
        bg_hover.parse("#e4e4ec" if is_light else "#3d3d52")
        tab_fg = Gdk.RGBA()
        tab_fg.parse("#333333" if is_light else "#e8e8f2")
        tab_active_bg = Gdk.RGBA()
        tab_active_bg.parse("#dbe4ff" if is_light else "#4a5a9f")
        tab_active_fg = Gdk.RGBA()
        tab_active_fg.parse("#1a1a1a" if is_light else "#ffffff")

        for btn in (self.btn_new_tab, self.btn_new_island):
            btn.override_color(Gtk.StateFlags.NORMAL, fg)
            btn.override_color(Gtk.StateFlags.PRELIGHT, fg)
            btn.override_background_color(Gtk.StateFlags.NORMAL, bg)
            btn.override_background_color(Gtk.StateFlags.PRELIGHT, bg_hover)
            for child in btn.get_children():
                if isinstance(child, Gtk.Label):
                    child.override_color(Gtk.StateFlags.NORMAL, fg)

        for tab in self.tabs:
            if tab.button:
                toggle = tab.button
                if toggle.get_active():
                    toggle.override_color(Gtk.StateFlags.NORMAL, tab_active_fg)
                    toggle.override_background_color(Gtk.StateFlags.NORMAL, tab_active_bg)
                else:
                    toggle.override_color(Gtk.StateFlags.NORMAL, tab_fg)
                    toggle.override_background_color(Gtk.StateFlags.NORMAL, bg)
                for child in toggle.get_children():
                    if isinstance(child, Gtk.Label):
                        child.override_color(
                            Gtk.StateFlags.NORMAL,
                            tab_active_fg if toggle.get_active() else tab_fg,
                        )

    def create_island(self, name: str | None = None) -> TabIsland:
        color = ISLAND_COLORS[self._color_index % len(ISLAND_COLORS)]
        self._color_index += 1
        island = TabIsland(
            id=str(uuid.uuid4()),
            name=name or f"Island {len(self.islands) + 1}",
            color=color,
        )
        self.islands.append(island)
        self._rebuild_tab_strip()
        return island

    def prompt_new_island(self) -> None:
        dialog = Gtk.Dialog(title="New tab island", transient_for=self.window, modal=True)
        dialog.add_button(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL)
        dialog.add_button(Gtk.STOCK_OK, Gtk.ResponseType.OK)
        box = dialog.get_content_area()
        box.set_border_width(12)
        box.set_spacing(8)
        label = Gtk.Label(label="Island name:", xalign=0)
        entry = Gtk.Entry()
        entry.set_text(f"Island {len(self.islands) + 1}")
        entry.set_activates_default(True)
        box.pack_start(label, False, False, 0)
        box.pack_start(entry, True, True, 0)
        dialog.set_default_response(Gtk.ResponseType.OK)
        dialog.show_all()
        response = dialog.run()
        name = entry.get_text().strip()
        dialog.destroy()
        if response == Gtk.ResponseType.OK:
            island = self.create_island(name or None)
            self.new_tab(island_id=island.id, load_home=True)

    def new_tab(self, load_home: bool = True, island_id: str | None = None) -> BrowserTab:
        target_island = island_id or self._active_island_id()
        tab = self._create_tab(target_island)
        self.activate_tab(tab.id)
        if load_home:
            self._on_navigate(tab, "")
        return tab

    def open_url(self, url: str, new_tab: bool = False) -> BrowserTab:
        if new_tab:
            tab = self.new_tab(load_home=False)
            self._on_navigate(tab, url)
            return tab
        if not self.tabs:
            tab = self.new_tab(load_home=False)
            self._on_navigate(tab, url)
            return tab
        tab = self.get_active_tab()
        if tab is None:
            tab = self.new_tab(load_home=False)
        self.activate_tab(tab.id)
        self._on_navigate(tab, url)
        return tab

    def go_home_in_active_tab(self) -> None:
        tab = self.get_active_tab()
        if tab is None:
            tab = self.new_tab(load_home=True)
        else:
            self.activate_tab(tab.id)
            self._on_navigate(tab, "")

    def _active_island_id(self) -> str:
        active = self.get_active_tab()
        if active:
            return active.island_id
        return self._default_island_id

    def _create_tab(self, island_id: str) -> BrowserTab:
        tab_id = str(uuid.uuid4())
        webview = WebKit2.WebView()
        webview.get_style_context().add_class("nova-shell")
        webview.set_hexpand(True)
        webview.set_vexpand(True)
        self._setup_webview(webview, tab_id)
        webview.connect("load-changed", self._on_load_changed, tab_id)
        webview.connect("load-failed", self._on_load_failed, tab_id)

        tab = BrowserTab(id=tab_id, island_id=island_id, webview=webview)
        self.tabs.append(tab)
        self.page_stack.add_named(webview, tab_id)
        webview.show_all()
        self.page_stack.show_all()
        self._rebuild_tab_strip()
        return tab

    def get_active_tab(self) -> BrowserTab | None:
        if not self.active_tab_id:
            return None
        return next((t for t in self.tabs if t.id == self.active_tab_id), None)

    def get_active_webview(self) -> WebKit2.WebView | None:
        tab = self.get_active_tab()
        return tab.webview if tab else None

    def activate_tab(self, tab_id: str) -> None:
        if tab_id not in {t.id for t in self.tabs}:
            return
        self.active_tab_id = tab_id
        self.page_stack.set_visible_child_name(tab_id)
        tab = self.get_active_tab()
        if tab and tab.webview:
            tab.webview.show()
            self.page_stack.show_all()
            tab.webview.queue_draw()
        self._on_active_changed()
        self._rebuild_tab_strip()
        if hasattr(self.window, "_is_light_toolbar"):
            self.apply_toolbar_colors(self.window._is_light_toolbar())

    def close_tab(self, tab_id: str) -> None:
        tab = next((t for t in self.tabs if t.id == tab_id), None)
        if not tab:
            return
        idx = self.tabs.index(tab)
        self.tabs.remove(tab)
        self.page_stack.remove(tab.webview)
        if not self.tabs:
            self.new_tab(load_home=True)
            return
        if self.active_tab_id == tab_id:
            next_idx = min(idx, len(self.tabs) - 1)
            self.activate_tab(self.tabs[next_idx].id)
        self._prune_empty_islands()
        self._rebuild_tab_strip()

    def _prune_empty_islands(self) -> None:
        used = {t.island_id for t in self.tabs}
        self.islands = [i for i in self.islands if i.id in used]
        if not self.islands:
            island = self.create_island("General")
            self._default_island_id = island.id

    def move_tab_to_island(self, tab_id: str, island_id: str) -> None:
        tab = next((t for t in self.tabs if t.id == tab_id), None)
        if not tab:
            return
        tab.island_id = island_id
        self._rebuild_tab_strip()

    def toggle_island_collapsed(self, island_id: str) -> None:
        for island in self.islands:
            if island.id == island_id:
                island.collapsed = not island.collapsed
                break
        self._rebuild_tab_strip()

    def next_tab(self) -> None:
        if not self.tabs or not self.active_tab_id:
            return
        ids = [t.id for t in self.tabs]
        idx = ids.index(self.active_tab_id)
        self.activate_tab(ids[(idx + 1) % len(ids)])

    def prev_tab(self) -> None:
        if not self.tabs or not self.active_tab_id:
            return
        ids = [t.id for t in self.tabs]
        idx = ids.index(self.active_tab_id)
        self.activate_tab(ids[(idx - 1) % len(ids)])

    def _on_load_changed(self, webview: WebKit2.WebView, load_event, tab_id: str) -> None:
        if load_event != WebKit2.LoadEvent.FINISHED:
            return
        tab = next((t for t in self.tabs if t.id == tab_id), None)
        if not tab:
            return
        uri = webview.get_uri() or tab.url
        tab.url = uri
        tab.is_home = uri.startswith("http://127.0.0.1:") or uri.startswith("nova://")
        tab.title = (
            "Nova"
            if tab.is_home
            else (webview.get_title() or self._title_from_url(uri))[:48]
        )
        if tab.button:
            tab.button.set_label(tab.title)
        if tab.id == self.active_tab_id:
            self._on_active_changed()

    def _on_load_failed(self, webview: WebKit2.WebView, failing_uri: str, error, tab_id: str) -> bool:
        from .debug_log import log as debug_log

        tab = next((t for t in self.tabs if t.id == tab_id), None)
        message = error.message if error else "unknown error"
        debug_log(f"tab load failed {failing_uri}: {message}")
        if tab and tab.button:
            tab.title = "Failed"
            tab.button.set_label(tab.title)
        return False

    @staticmethod
    def _title_from_url(url: str) -> str:
        try:
            from urllib.parse import urlparse

            host = urlparse(url).netloc
            return host or url[:32] or "Page"
        except Exception:
            return url[:32] or "Page"

    def _rebuild_tab_strip(self) -> None:
        for child in self.tab_strip.get_children():
            self.tab_strip.remove(child)

        island_map: dict[str, list[BrowserTab]] = {i.id: [] for i in self.islands}
        for tab in self.tabs:
            if tab.island_id not in island_map:
                tab.island_id = self._default_island_id
            island_map.setdefault(tab.island_id, []).append(tab)

        for island in self.islands:
            tabs = island_map.get(island.id, [])
            if not tabs:
                continue

            group = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=4)
            group.get_style_context().add_class("nova-tab-island")
            rgba = Gdk.RGBA()
            rgba.parse(island.color)
            rgba.alpha = 0.22
            group.override_background_color(Gtk.StateFlags.NORMAL, rgba)

            header = Gtk.Button()
            header.set_relief(Gtk.ReliefStyle.NONE)
            header.get_style_context().add_class("nova-toolbar-btn")
            arrow = "▾" if not island.collapsed else "▸"
            header.set_label(f"{arrow} {island.name}")
            header.connect(
                "clicked",
                lambda *_ , iid=island.id: self.toggle_island_collapsed(iid),
            )
            group.pack_start(header, False, False, 0)

            if not island.collapsed:
                tabs_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=2)
                for tab in tabs:
                    tabs_box.pack_start(self._build_tab_button(tab), False, False, 0)
                group.pack_start(tabs_box, False, False, 0)
            elif self.active_tab_id in {t.id for t in tabs}:
                active = next(t for t in tabs if t.id == self.active_tab_id)
                group.pack_start(self._build_tab_button(active), False, False, 0)

            self.tab_strip.pack_start(group, False, False, 0)

        self.tab_strip.pack_start(self.btn_new_tab, False, False, 0)
        self.tab_strip.pack_start(self.btn_new_island, False, False, 0)
        self.tab_strip.show_all()
        if hasattr(self.window, "_is_light_toolbar"):
            self.apply_toolbar_colors(self.window._is_light_toolbar())

    def _build_tab_button(self, tab: BrowserTab) -> Gtk.Box:
        row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        toggle = Gtk.ToggleButton(label=tab.title)
        toggle.set_relief(Gtk.ReliefStyle.NONE)
        toggle.get_style_context().add_class("nova-browser-tab")
        toggle.set_active(tab.id == self.active_tab_id)
        toggle.connect("toggled", self._on_tab_toggled, tab.id)
        toggle.connect("button-press-event", self._on_tab_button_press, tab.id)
        tab.button = toggle

        close = Gtk.Button(label="×")
        close.set_relief(Gtk.ReliefStyle.NONE)
        close.get_style_context().add_class("nova-tab-close-btn")
        close.set_can_focus(False)
        close.connect("clicked", lambda *_ , tid=tab.id: self.close_tab(tid))

        row.pack_start(toggle, True, True, 0)
        row.pack_start(close, False, False, 0)
        return row

    def _on_tab_toggled(self, button: Gtk.ToggleButton, tab_id: str) -> None:
        if button.get_active() and self.active_tab_id != tab_id:
            self.activate_tab(tab_id)
        elif not button.get_active() and self.active_tab_id == tab_id:
            button.set_active(True)

    def _on_tab_button_press(self, widget, event, tab_id: str) -> bool:
        if event.button == 2:
            self.close_tab(tab_id)
            return True
        if event.button == 3:
            self._show_tab_menu(tab_id, event)
            return True
        return False

    def _show_tab_menu(self, tab_id: str, event) -> None:
        menu = Gtk.Menu()
        close_item = Gtk.MenuItem(label="Close tab")
        close_item.connect("activate", lambda *_ , tid=tab_id: self.close_tab(tid))
        menu.append(close_item)

        move_menu = Gtk.MenuItem(label="Move to island")
        submenu = Gtk.Menu()
        for island in self.islands:
            item = Gtk.MenuItem(label=island.name)
            item.connect(
                "activate",
                lambda *_ , tid=tab_id, iid=island.id: self.move_tab_to_island(tid, iid),
            )
            submenu.append(item)
        new_item = Gtk.MenuItem(label="New island…")
        new_item.connect(
            "activate",
            lambda *_ , tid=tab_id: self._move_tab_to_new_island(tid),
        )
        submenu.append(new_item)
        move_menu.set_submenu(submenu)
        menu.append(move_menu)
        menu.show_all()
        menu.popup_at_pointer(event)

    def _move_tab_to_new_island(self, tab_id: str) -> None:
        island = self.create_island()
        self.move_tab_to_island(tab_id, island.id)

    def all_webviews(self) -> list[WebKit2.WebView]:
        return [tab.webview for tab in self.tabs]

    def tab_by_id(self, tab_id: str) -> BrowserTab | None:
        return next((t for t in self.tabs if t.id == tab_id), None)
