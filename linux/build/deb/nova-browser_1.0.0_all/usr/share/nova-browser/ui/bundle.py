"""Assemble the Nova Browser UI into a single self-contained HTML document."""

from __future__ import annotations

import re
from pathlib import Path


def ui_directory(explicit: Path | None = None) -> Path:
    if explicit and (explicit / "index.html").is_file():
        return explicit

    import os

    env = os.environ.get("NOVA_BROWSER_UI")
    if env:
        path = Path(env)
        if (path / "index.html").is_file():
            return path

    installed = Path("/usr/share/nova-browser/ui")
    if (installed / "index.html").is_file():
        return installed

    repo = Path(__file__).resolve().parent
    if (repo / "index.html").is_file():
        return repo

    return installed


def _bundle_page(html_name: str, ui_root: Path | None = None) -> str:
    root = ui_directory(ui_root)
    index_path = root / html_name
    if not index_path.is_file():
        raise FileNotFoundError(f"Nova Browser UI not found at {index_path}")

    html = index_path.read_text(encoding="utf-8")

    def inline_stylesheet(match: re.Match[str]) -> str:
        href = match.group(1)
        css_path = root / href
        if not css_path.is_file():
            return match.group(0)
        css = css_path.read_text(encoding="utf-8")
        return f"<style>{css}</style>"

    def inline_script(match: re.Match[str]) -> str:
        src = match.group(1)
        js_path = root / src
        if not js_path.is_file():
            return match.group(0)
        js = js_path.read_text(encoding="utf-8")
        return f"<script>{js}</script>"

    html = re.sub(
        r'<link rel="stylesheet" href="([^"]+)">',
        inline_stylesheet,
        html,
    )
    html = re.sub(
        r'<script src="([^"]+)"></script>',
        inline_script,
        html,
    )

    html = re.sub(
        r"<script>\s*window\.addEventListener\(\"load\"[\s\S]*?</script>\s*",
        "",
        html,
        count=1,
    )

    return html


def bundle_ui_html(ui_root: Path | None = None) -> str:
    return _bundle_page("index.html", ui_root)


def bundle_browser_html(ui_root: Path | None = None) -> str:
    return _bundle_page("browser.html", ui_root)


def native_bridge_script(preloaded_data: str) -> str:
    return f"<script>{native_bridge_js(preloaded_data)}</script>"


def native_bridge_js(preloaded_data: str) -> str:
    import json

    try:
        payload = json.dumps(json.loads(preloaded_data))
    except (json.JSONDecodeError, TypeError):
        payload = preloaded_data if preloaded_data.startswith("{") else "{}"

    return f"""
window.__NOVA_PRELOADED_DATA__ = {payload};
window.NovaBridge = {{
  getData: function() {{
    return typeof window.__NOVA_PRELOADED_DATA__ === "string"
      ? window.__NOVA_PRELOADED_DATA__
      : JSON.stringify(window.__NOVA_PRELOADED_DATA__);
  }},
  saveData: function(json) {{
    window.webkit.messageHandlers.nova.postMessage(JSON.stringify({{op:'saveData', json: json}}));
    try {{ window.__NOVA_PRELOADED_DATA__ = JSON.parse(json); }} catch (e) {{ window.__NOVA_PRELOADED_DATA__ = json; }}
  }},
  openUrl: function(url) {{
    window.webkit.messageHandlers.nova.postMessage(JSON.stringify({{op:'openUrl', url: url}}));
  }},
  goHome: function() {{
    window.webkit.messageHandlers.nova.postMessage(JSON.stringify({{op:'goHome'}}));
  }},
  navigateInBrowser: function(url) {{
    window.webkit.messageHandlers.nova.postMessage(JSON.stringify({{op:'openUrl', url: url}}));
  }},
  pickImageWithCallback: function() {{
    window.webkit.messageHandlers.nova.postMessage(JSON.stringify({{op:'pickImage'}}));
  }},
  clearBrowsingData: function() {{
    window.webkit.messageHandlers.nova.postMessage(JSON.stringify({{op:'clearData'}}));
  }},
  browserGoBack: function() {{
    window.webkit.messageHandlers.nova.postMessage(JSON.stringify({{op:'browserGoBack'}}));
  }},
  browserGoForward: function() {{
    window.webkit.messageHandlers.nova.postMessage(JSON.stringify({{op:'browserGoForward'}}));
  }}
}};
"""
