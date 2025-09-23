"""Notion API functions for managing database operations and page creation."""

import requests
from config import (
    LAB_DB_ID,
    base_headers,
    json_headers,
    legacy_base_headers,
    legacy_json_headers,
    _DATA_SOURCE_CACHE,
)


def get_data_source_id(database_id: str) -> str:
    """Get data source ID for a database, using cache if available."""
    if database_id in _DATA_SOURCE_CACHE:
        return _DATA_SOURCE_CACHE[database_id]
    url = f"https://api.notion.com/v1/databases/{database_id}"
    res = requests.get(url, headers=base_headers)
    res.raise_for_status()
    data = res.json()
    data_sources = data.get("data_sources") or []
    if not data_sources:
        raise RuntimeError(f"No data_sources found for database {database_id}")
    ds_id = data_sources[0]["id"]
    _DATA_SOURCE_CACHE[database_id] = ds_id
    return ds_id


def find_subject_page(subject):
    """Find the Notion page for a specific lab subject."""
    url = f"https://api.notion.com/v1/databases/{LAB_DB_ID}/query"
    payload = {"filter": {"property": "ID", "title": {"equals": subject}}}
    res = requests.post(url, headers=legacy_json_headers, json=payload)
    res.raise_for_status()
    data = res.json()
    return data["results"][0]["id"] if data["results"] else None


def find_child_db(page_id):
    """Find the performance summaries child database in a subject's page."""
    url = f"https://api.notion.com/v1/blocks/{page_id}/children"
    res = requests.get(url, headers=legacy_base_headers)
    res.raise_for_status()
    for b in res.json()["results"]:
        if b["type"] == "child_database":
            title = b["child_database"]["title"]
            print(f"Found child DB: '{title}'")
            if "performance summaries" in title.lower():
                return b["id"]
    return None


def insert_summary(
    perf_db_id, subject, notion_file_id=None, external_url=None, session_name=None
):
    """Insert a performance summary entry into the Notion database."""
    if session_name is None:
        session_name = subject

    create_url = "https://api.notion.com/v1/pages"
    perf_ds_id = get_data_source_id(perf_db_id)

    # Build Files & media items
    if notion_file_id:
        files_items = [{"type": "file_upload", "file_upload": {"id": notion_file_id}}]
    elif external_url:
        files_items = [{"type": "external", "external": {"url": external_url}}]
    else:
        raise ValueError("insert_summary requires notion_file_id or external_url")

    create_payload = {
        "parent": {"type": "data_source_id", "data_source_id": perf_ds_id},
        "properties": {
            "Session ID": {"title": [{"text": {"content": session_name}}]},
            "Files & media": {"files": files_items},
        },
    }

    try:
        res = requests.post(create_url, headers=json_headers, json=create_payload)
        res.raise_for_status()
        page_id = res.json().get("id")
        print(f"📄 Created Notion page for {session_name}")
        print(f"📎 Attached file to 'Files & media' for {session_name}")
        return page_id
    except requests.exceptions.HTTPError as e:
        print(f"⚠️ Error creating Notion entry: {e}")
        if hasattr(e.response, "text"):
            print(f"Response details: {e.response.text}")
        return None
    except Exception as e:
        print(f"⚠️ Unexpected error: {e}")
        return None
