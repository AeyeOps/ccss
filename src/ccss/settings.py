"""Settings persistence for ccss."""

from __future__ import annotations

import json
from pathlib import Path
from typing import TypedDict

CACHE_DIR = Path.home() / ".cache" / "ccss"
SETTINGS_PATH = CACHE_DIR / "settings.json"

DEFAULT_THEME = "textual-dark"

AVAILABLE_THEMES = [
    "cc-tribute",
    "textual-dark",
    "textual-light",
    "nord",
    "gruvbox",
    "tokyo-night",
    "dracula",
    "monokai",
    "solarized-light",
]


class SettingsDict(TypedDict):
    """Settings schema."""

    theme: str


def load_settings() -> SettingsDict:
    """Load settings from cache file. Returns defaults if missing or corrupted."""
    if not SETTINGS_PATH.exists():
        return {"theme": DEFAULT_THEME}

    try:
        with open(SETTINGS_PATH, encoding="utf-8") as f:
            data = json.load(f)
            theme = data.get("theme", DEFAULT_THEME)
            # Validate theme exists
            if theme not in AVAILABLE_THEMES:
                theme = DEFAULT_THEME
            return {"theme": theme}
    except (json.JSONDecodeError, OSError):
        # Corrupted or unreadable - return defaults
        return {"theme": DEFAULT_THEME}


def save_settings(settings: SettingsDict) -> None:
    """Save settings to cache file."""
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    with open(SETTINGS_PATH, "w", encoding="utf-8") as f:
        json.dump(settings, f, indent=2)
