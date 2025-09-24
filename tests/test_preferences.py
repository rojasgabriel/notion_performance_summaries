import json
import pytest
from notion_performance_summaries.preferences import (
    get_preference,
    validate_preferences,
)


def test_get_preference(tmp_path):
    """Test that get_preference correctly retrieves nested values."""
    prefs_file = tmp_path / "preferences.json"
    prefs_data = {
        "paths": {"input_loc": "/test/input", "output_loc": "/test/output"},
        "subjects": ["SUB01", "SUB02"],
    }
    prefs_file.write_text(json.dumps(prefs_data))

    # Override the default path to our temporary file
    from notion_performance_summaries import preferences

    preferences.reload_preferences(path=prefs_file)

    assert get_preference("paths.input_loc") == "/test/input"
    assert get_preference("subjects") == ["SUB01", "SUB02"]


def test_load_preferences_missing_file(tmp_path):
    """Test that loading preferences raises an error for a missing file."""
    from notion_performance_summaries import preferences

    with pytest.raises(FileNotFoundError):
        preferences.reload_preferences(path=tmp_path / "nonexistent.json")


def test_validate_preferences_missing_key(tmp_path):
    """Test that validate_preferences raises an error for a missing key."""
    prefs_file = tmp_path / "preferences.json"
    prefs_data = {
        "paths": {
            "input_loc": "/test/input"
            # Missing output_loc
        },
        "subjects": ["SUB01", "SUB02"],
    }
    prefs_file.write_text(json.dumps(prefs_data))

    from notion_performance_summaries import preferences

    preferences.reload_preferences(path=prefs_file)

    with pytest.raises(
        KeyError, match="Missing required preference: 'paths.output_loc'"
    ):
        validate_preferences()
