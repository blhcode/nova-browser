"""Build HTML served to the embedded WebKit view."""

from __future__ import annotations

import sys
from pathlib import Path

from .app import ui_dir
from .datastore import DataStore


class HomeLoader:
    def __init__(self, datastore: DataStore) -> None:
        self.datastore = datastore

    def build_home_html(self) -> str:
        ui_path = ui_dir()
        ui_str = str(ui_path)
        if ui_str not in sys.path:
            sys.path.insert(0, ui_str)
        from bundle import bundle_ui_html

        # Identical to the working dev server bundle.
        return bundle_ui_html(ui_path)

    def build_browser_html(self) -> str:
        ui_path = ui_dir()
        ui_str = str(ui_path)
        if ui_str not in sys.path:
            sys.path.insert(0, ui_str)
        from bundle import bundle_browser_html

        return bundle_browser_html(ui_path)
