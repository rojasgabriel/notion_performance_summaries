"""Configuration constants and headers for Notion Performance Summaries."""

import os
from preferences import get_preference, validate_preferences

# Validate preferences before loading configuration
validate_preferences()

# === CONFIG ===
NOTION_TOKEN = os.environ.get("NOTION_TOKEN")
if not NOTION_TOKEN:
    raise RuntimeError(
        "NOTION_TOKEN environment variable is not set. Export your Notion integration token as NOTION_TOKEN."
    )
LAB_DB_ID = os.environ.get("LAB_ANIMALS_DB_ID")
if not LAB_DB_ID:
    raise RuntimeError(
        "LAB_DB_ID environment variable is not set. Export your Notion lab database ID as LAB_ANIMALS_DB_ID."
    )

# Load configuration from preferences.json (validation ensures these are not empty)
OUTPUT_LOC = get_preference("paths.output_loc")
REMOTE = get_preference("paths.remote")
SUBJECTS = get_preference("subjects")

# Notion API headers
NOTION_VERSION = get_preference("notion.version", "2025-09-03")
base_headers = {
    "Authorization": f"Bearer {NOTION_TOKEN}",
    "Notion-Version": NOTION_VERSION,
}
json_headers = {
    **base_headers,
    "Content-Type": "application/json",
}
