import json
import os
from pathlib import Path

DEFAULT_DATA = {
    "bookmarks": [],
    "theme": {
        "mode": "space",
        "customBgColor": "#0a0a12",
        "customAccentColor": "#6b8cff",
        "customBgImage": None,
    },
    "settings": {
        "searchEngine": "google",
        "homepage": "",
        "javascriptEnabled": True,
        "desktopMode": False,
        "blockThirdPartyCookies": True,
        "zoomLevel": 100,
    },
}


SEARCH_ENGINES = {
    "google": "https://www.google.com/search?q=",
    "duckduckgo": "https://duckduckgo.com/?q=",
    "bing": "https://www.bing.com/search?q=",
    "brave": "https://search.brave.com/search?q=",
}

DESKTOP_UA = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)
MOBILE_UA = (
    "Mozilla/5.0 (Linux; Android 13; Mobile) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36"
)


class DataStore:
    def __init__(self) -> None:
        config_dir = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config"))
        self.config_path = config_dir / "nova-browser" / "data.json"
        self.themes_dir = Path(
            os.environ.get("XDG_DATA_HOME", Path.home() / ".local" / "share")
        ) / "nova-browser" / "themes"
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        self.themes_dir.mkdir(parents=True, exist_ok=True)

    def get_data(self) -> str:
        if not self.config_path.exists():
            self.save_data(json.dumps(DEFAULT_DATA))
        return self.config_path.read_text(encoding="utf-8")

    def save_data(self, raw: str) -> None:
        parsed = json.loads(raw)
        data = {**DEFAULT_DATA, **parsed}
        if "theme" in parsed:
            data["theme"] = {**DEFAULT_DATA["theme"], **parsed["theme"]}
        if "settings" in parsed:
            data["settings"] = {**DEFAULT_DATA["settings"], **parsed["settings"]}
        self.config_path.write_text(json.dumps(data, indent=2), encoding="utf-8")

    def as_dict(self) -> dict:
        return json.loads(self.get_data())
