"""Preferences management for Notion Performance Summaries."""

import json
from pathlib import Path
from typing import Dict, Any


DEFAULT_PREFERENCES = {
    "paths": {
        "input_loc": "",
        "output_loc": "",
        "remote": "",
    },
    "subjects": [],
    "notion": {"version": "2025-09-03"},
}


def get_preferences_path() -> Path:
    """Return the path to the preferences.json file in your home directory."""
    return Path.home() / ".notion_performance_summaries" / "preferences.json"


def create_default_preferences(preferences_path: Path) -> Dict[str, Any]:
    """Create a default preferences.json file."""
    # Ensure parent directory exists
    preferences_path.parent.mkdir(parents=True, exist_ok=True)

    with open(preferences_path, "w", encoding="utf-8") as f:
        json.dump(DEFAULT_PREFERENCES, f, indent=2)

    print(f"✨ Created default preferences file at: {preferences_path}")
    print("⚠️  IMPORTANT: Edit this file before running the code again.")

    return DEFAULT_PREFERENCES


def load_preferences(preferences_path: Path | None = None) -> Dict[str, Any]:
    """Load preferences from preferences.json, creating defaults if needed."""
    if preferences_path is None:
        preferences_path = get_preferences_path()

    if not preferences_path.exists():
        raise FileNotFoundError(f"Preferences file not found at {preferences_path}")

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
_preferences: Dict[str, Any] | None = None


def get_preference(key_path: str, default=None):
    """Get a preference value using dot notation (e.g., 'paths.input_loc')."""
    global _preferences
    if _preferences is None:
        _preferences = load_preferences()

    keys = key_path.split(".")
    value = _preferences

    for key in keys:
        if isinstance(value, dict) and key in value:
            value = value[key]
        else:
            return default

    return value


def validate_preferences():
    """Validate that required preferences are configured."""
    errors = []

    # Ensure preferences are loaded
    global _preferences
    if _preferences is None:
        _preferences = load_preferences()

    # Check required paths
    required_paths = ["paths.input_loc", "paths.output_loc", "paths.remote"]
    for path_key in required_paths:
        value = get_preference(path_key, "")
        if not value or value.strip() == "":
            errors.append(f"Missing required preference: '{path_key}'")

    # Check subjects
    subjects = get_preference("subjects", [])
    if not subjects or len(subjects) == 0:
        errors.append("Missing required preference: 'subjects' list cannot be empty")

    if errors:
        # For now, let's raise a KeyError for the first missing key to satisfy tests
        # A more robust solution might involve a custom exception type.
        raise KeyError(errors[0])


def reload_preferences(path: Path | None = None):
    """Reload preferences from file, optionally from a specific path."""
    global _preferences
    _preferences = load_preferences(preferences_path=path)
    return _preferences
