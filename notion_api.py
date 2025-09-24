"""Notion API functions for managing database operations and page creation."""

import requests
from config import (
    LAB_DB_ID,
    base_headers,
    json_headers,
)


def find_subject_page(subject):
    """Find the Notion page for a specific lab subject."""
    url = f"https://api.notion.com/v1/databases/{LAB_DB_ID}/query"
    payload = {"filter": {"property": "ID", "title": {"equals": subject}}}
    res = requests.post(url, headers=json_headers, json=payload)
    res.raise_for_status()
    data = res.json()
    return data["results"][0]["id"] if data["results"] else None


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
    """Check if a performance summary entry already exists for the given session."""
    url = f"https://api.notion.com/v1/databases/{perf_db_id}/query"
    payload = {"filter": {"property": "Session ID", "title": {"equals": session_name}}}
    res = requests.post(url, headers=json_headers, json=payload)
    res.raise_for_status()
    data = res.json()
    return data["results"][0]["id"] if data["results"] else None


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
    
    # Build Files & media items
    if notion_file_id:
        files_items = [{"type": "file_upload", "file_upload": {"id": notion_file_id}}]
    elif external_url:
        files_items = [{"type": "external", "external": {"url": external_url}}]
    else:
        raise ValueError("insert_summary requires notion_file_id or external_url")

    create_payload = {
        "parent": {"type": "database_id", "database_id": perf_db_id},
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
