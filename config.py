"""Configuration constants and headers for Notion Performance Summaries."""

import os
from typing import Dict

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

OUTPUT_LOC = "/Users/gabriel/performance_summaries"
REMOTE = "my_gdrive:performance_summaries"
SUBJECTS = ["GRB036", "GRB037", "GRB038", "GRB039", "GRB045", "GRB046", "GRB047"]

# Notion API headers
NOTION_VERSION = "2025-09-03"
base_headers = {
    "Authorization": f"Bearer {NOTION_TOKEN}",
    "Notion-Version": NOTION_VERSION,
}
json_headers = {
    **base_headers,
    "Content-Type": "application/json",
}

# Legacy headers for database operations (pre-2025 data sources)
NOTION_VERSION_LEGACY = "2022-06-28"
legacy_base_headers = {
    "Authorization": f"Bearer {NOTION_TOKEN}",
    "Notion-Version": NOTION_VERSION_LEGACY,
}
legacy_json_headers = {
    **legacy_base_headers,
    "Content-Type": "application/json",
}

# Simple cache for database_id -> data_source_id lookups
_DATA_SOURCE_CACHE: Dict[str, str] = {}
