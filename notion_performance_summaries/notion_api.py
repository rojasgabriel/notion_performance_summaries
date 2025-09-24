"""Notion API functions for managing database operations and page creation.

This module uses ONLY the 2025-09-03 Notion API style:
    * All database-like queries go through data source endpoints: /v1/data_sources/{id}/query
    * Page parent references use {"type": "data_source_id", "data_source_id": <id>}
    * File attachments use the file_upload object (created elsewhere) inside a Files & media property
"""

import requests
from .config import LAB_DB_ID, base_headers, json_headers, _DATA_SOURCE_CACHE


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


def _query_data_source(data_source_id: str, filter_payload: dict):
    """Low-level wrapper to query a data source (new API). Returns JSON dict."""
    url = f"https://api.notion.com/v1/data_sources/{data_source_id}/query"
    res = requests.post(url, headers=json_headers, json=filter_payload)
    try:
        res.raise_for_status()
    except requests.exceptions.HTTPError as e:
        snippet = res.text[:300] if hasattr(res, "text") else "(no body)"
        raise RuntimeError(
            f"Data source query failed ({data_source_id}): {e} :: {snippet}"
        ) from e
    return res.json()


def find_subject_page(subject):
    """Find the Notion page for a specific lab subject via data source query only."""
    ds_id = get_data_source_id(LAB_DB_ID)
    payload = {"filter": {"property": "ID", "title": {"equals": subject}}}
    data = _query_data_source(ds_id, payload)
    return data["results"][0]["id"] if data.get("results") else None


def find_child_db(page_id):
    """Find the performance summaries child database in a subject's page."""
    url = f"https://api.notion.com/v1/blocks/{page_id}/children"
    res = requests.get(url, headers=base_headers)
    res.raise_for_status()
    for b in res.json()["results"]:
        if b["type"] == "child_database":
            title = b["child_database"]["title"]
            print(f"Found child DB: '{title}'")
            if "performance summaries" in title.lower():
                return b["id"]
    return None


def find_existing_summary(perf_db_id, session_name):
    """Check if a performance summary entry already exists (data source query)."""
    perf_ds_id = get_data_source_id(perf_db_id)
    payload = {"filter": {"property": "Session ID", "title": {"equals": session_name}}}
    data = _query_data_source(perf_ds_id, payload)
    return data["results"][0]["id"] if data.get("results") else None


def insert_summary(
    perf_db_id,
    subject,
    notion_file_id=None,
    external_url=None,
    session_name=None,
    overwrite=False,
):
    """Insert a performance summary entry into the Notion database."""
    if session_name is None:
        session_name = subject

    # Check if entry already exists
    existing_page_id = find_existing_summary(perf_db_id, session_name)
    if existing_page_id:
        if not overwrite:
            print(
                f"⚠️ Entry for {session_name} already exists. Use --overwrite to replace it."
            )
            return existing_page_id
        else:
            print(f"🔄 Overwriting existing entry for {session_name}")
            # Delete the existing entry
            delete_url = f"https://api.notion.com/v1/pages/{existing_page_id}"
            delete_payload = {"archived": True}
            res = requests.patch(delete_url, headers=json_headers, json=delete_payload)
            try:
                res.raise_for_status()
                print(f"🗑️ Archived existing entry for {session_name}")
            except requests.exceptions.HTTPError as e:
                print(f"⚠️ Warning: Could not archive existing entry: {e}")

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
