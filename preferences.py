"""Preferences management for Notion Performance Summaries."""

import json
from pathlib import Path
from typing import Dict, Any


DEFAULT_PREFERENCES = {
    "paths": {
        "input_loc": "/Users/gabriel/data",
        "output_loc": "/Users/gabriel/performance_summaries",
        "remote": "my_gdrive:performance_summaries",
    },
    "subjects": ["GRB036", "GRB037", "GRB038", "GRB039", "GRB045", "GRB046", "GRB047"],
    "notion": {"version": "2025-09-03", "version_legacy": "2022-06-28"},
}


def get_preferences_path() -> Path:
    """Get the path to the preferences.json file."""
    # Try to find preferences.json in current directory first, then home directory
    current_dir = Path.cwd() / "preferences.json"
    if current_dir.exists():
        return current_dir

    home_dir = Path.home() / ".notion_performance_summaries" / "preferences.json"
    return home_dir


def create_default_preferences(preferences_path: Path) -> Dict[str, Any]:
    """Create a default preferences.json file."""
    # Ensure parent directory exists
    preferences_path.parent.mkdir(parents=True, exist_ok=True)

    with open(preferences_path, "w", encoding="utf-8") as f:
        json.dump(DEFAULT_PREFERENCES, f, indent=2)

    print(f"✨ Created default preferences file at: {preferences_path}")
    print("🔧 You can edit this file to customize paths and subjects for your setup.")

    return DEFAULT_PREFERENCES


def load_preferences() -> Dict[str, Any]:
    """Load preferences from preferences.json, creating defaults if needed."""
    preferences_path = get_preferences_path()

    if not preferences_path.exists():
        return create_default_preferences(preferences_path)

    try:
        with open(preferences_path, "r", encoding="utf-8") as f:
            preferences = json.load(f)

        # Validate that all required keys exist, add missing ones with defaults
        updated = False
        for key, value in DEFAULT_PREFERENCES.items():
            if key not in preferences:
                preferences[key] = value
                updated = True
            elif isinstance(value, dict):
                # Check nested dictionaries
                for subkey, subvalue in value.items():
                    if subkey not in preferences[key]:
                        preferences[key][subkey] = subvalue
                        updated = True

        # Save updated preferences if we added missing keys
        if updated:
            with open(preferences_path, "w", encoding="utf-8") as f:
                json.dump(preferences, f, indent=2)
            print(
                f"🔄 Updated preferences file with missing defaults: {preferences_path}"
            )

        return preferences

    except (json.JSONDecodeError, KeyError) as e:
        print(f"⚠️ Error reading preferences file {preferences_path}: {e}")
        print("🔧 Creating new default preferences file...")
        return create_default_preferences(preferences_path)


# Load preferences on module import
_preferences = load_preferences()


def get_preference(key_path: str, default=None):
    """Get a preference value using dot notation (e.g., 'paths.input_loc')."""
    keys = key_path.split(".")
    value = _preferences

    for key in keys:
        if isinstance(value, dict) and key in value:
            value = value[key]
        else:
            return default

    return value


def reload_preferences():
    """Reload preferences from file."""
    global _preferences
    _preferences = load_preferences()
