import os
import re
import subprocess
import requests
import json
from datetime import datetime

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
_DATA_SOURCE_CACHE = {}

def get_data_source_id(database_id: str) -> str:
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


# === HELPERS ===
def run_cmd(cmd):
    print("▶", " ".join(cmd))
    return subprocess.run(cmd, capture_output=True, text=True, check=True).stdout.strip()


def ensure_sessions(subject, pattern, sessions_back, input_loc):
    """Mimics labdata session checking/downloading logic."""
    # Get list of sessions
    out = run_cmd(["labdata", "sessions", subject, "--files"])
    sessions = sorted(
        re.findall(r"[0-9]{8}_[0-9]{6}", out), reverse=True
    )
    # Find pattern match
    match_index = next((i for i, s in enumerate(sessions) if s.startswith(pattern)), -1)
    if match_index < 0:
        print(f"❌ No session found for {subject} with {pattern}")
        return []
    end_index = min(match_index + sessions_back + 1, len(sessions))
    to_download = sessions[match_index:end_index]

    for sess in to_download:
        session_dir = f"{input_loc}/{subject}/{sess}/chipmunk"
        if os.path.exists(session_dir) and any(f.endswith(".mat") for f in os.listdir(session_dir)):
            print(f"✅ Already downloaded: {subject} {sess}")
        else:
            print(f"⬇️ Downloading: {subject} {sess}")
            run_cmd(["labdata", "get", subject, "-s", sess, "-d", "chipmunk", "-i", "*.mat"])
    return to_download


def run_matlab(subject, input_loc, labdata_loc, subject_output, sessions_back, pattern):
    os.makedirs(subject_output, exist_ok=True)
    matlab_cmd = (
        f"batchCopyPlot({{'{subject}'}}, '{input_loc}', '{labdata_loc}', "
        f"'{subject_output}', {sessions_back}, '{pattern}')"
    )
    print("⚙️ Running MATLAB for", subject)
    run_cmd(["matlab", "-batch", matlab_cmd])
    print("✔️ Finished MATLAB for", subject)


def upload_to_notion_and_get_file_id(filepath):
    """
    Uploads a file directly to Notion using the official small file upload flow.
    Steps:
      1) POST /v1/files with name + mime to get an upload_url and file id.
      2) PUT the bytes to the upload_url.
    Returns: the Notion file id (to be referenced in blocks as a file upload).
    """
    try:
        file_name = os.path.basename(filepath)
        mime_type = "image/png"  # our summaries are PNGs
        file_size = os.path.getsize(filepath)
        print(f"📤 Starting direct Notion upload for {file_name} ({file_size} bytes)...")

        # Step 1: Create a file upload (JSON)
        create_payload = {
            "filename": file_name,
            "content_type": mime_type,
            "mode": "single_part",
        }
        r_create = requests.post("https://api.notion.com/v1/file_uploads", headers=json_headers, json=create_payload)
        try:
            r_create.raise_for_status()
        except requests.exceptions.HTTPError as e:
            body = None
            try:
                body = r_create.text
            except Exception:
                pass
            print(f"❌ HTTP Error during Notion create file upload: {e}\nResponse Body: {body}")
            raise

        meta = r_create.json()
        file_id = meta.get("id") or (meta.get("file_upload", {}) if isinstance(meta.get("file_upload"), dict) else {}).get("id")
        if not file_id:
            print("⚠️ Unexpected create response:", json.dumps(meta, indent=2))
            raise RuntimeError("Notion did not return file upload id")

        # Step 2: Send file contents (multipart)
        send_url = f"https://api.notion.com/v1/file_uploads/{file_id}/send"
        with open(filepath, "rb") as f:
            files = {"file": (file_name, f, mime_type)}
            r_send = requests.post(send_url, headers=base_headers, files=files)
        try:
            r_send.raise_for_status()
        except requests.exceptions.HTTPError as e:
            body = None
            try:
                body = r_send.text
            except Exception:
                pass
            print(f"❌ HTTP Error during Notion send file upload: {e}\nResponse Body: {body}")
            raise

        print(f"✅ Uploaded to Notion (file id: {file_id})")
        return file_id

    except Exception as e:
        print(f"❌ Notion upload failed: {e}")
        raise


def upload_to_drive(subject, fname):
    """Upload PNG to Drive as backup, then upload to Notion and return Notion file id."""
    local_file_path = f"{OUTPUT_LOC}/{subject}/{fname}"
    
    # Backup to Google Drive
    remote_path = f"{REMOTE}/{subject}"
    run_cmd(["rclone", "copy", local_file_path, remote_path])
    print(f"📁 Backed up to Google Drive: {remote_path}")
    
    # Upload to Notion and get the Notion file id
    return upload_to_notion_and_get_file_id(local_file_path)


def find_subject_page(subject):
    url = f"https://api.notion.com/v1/databases/{LAB_DB_ID}/query"
    payload = {"filter": {"property": "ID", "title": {"equals": subject}}}
    res = requests.post(url, headers=legacy_json_headers, json=payload)
    res.raise_for_status()
    data = res.json()
    return data["results"][0]["id"] if data["results"] else None


def find_child_db(page_id):
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


def insert_summary(perf_db_id, subject, notion_file_id=None, external_url=None, session_name=None):
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


# === MAIN PIPELINE ===
def main(pattern, sessions_back, notion_only=False):
    input_loc = "/Users/gabriel/data"
    labdata_loc = input_loc

    for subject in SUBJECTS:
        print(f"\n⏳ Processing {subject}")
        if not notion_only:
            sessions = ensure_sessions(subject, pattern, sessions_back, input_loc)
            if not sessions:
                continue
            subject_output = f"{OUTPUT_LOC}/{subject}"
            run_matlab(subject, input_loc, labdata_loc, subject_output, sessions_back, pattern)
        else:
            subject_output = f"{OUTPUT_LOC}/{subject}"
            if not os.path.exists(subject_output):
                print(f"⚠️ No output directory for {subject}, skipping Notion upload")
                continue

        # Find PNGs
        for fname in os.listdir(subject_output):
            if fname.endswith(".png"):
                notion_file_id = upload_to_drive(subject, fname)
                page_id = find_subject_page(subject)
                if not page_id:
                    print(f"⚠️ No Notion page for {subject}")
                    continue
                perf_db_id = find_child_db(page_id)
                if not perf_db_id:
                    print(f"⚠️ No child DB for {subject}")
                    continue
                
                # Extract a cleaner session name from the filename
                match = re.search(r"(\d{8})", fname)
                session_name = match.group(1) if match else fname.replace("_summary.png", "")

                insert_summary(perf_db_id, subject, notion_file_id=notion_file_id, session_name=session_name)


if __name__ == "__main__":
    import sys
    notion_only_flag = False
    args = sys.argv[1:]
    if "--notion-only" in args:
        notion_only_flag = True
        args.remove("--notion-only")

    if len(args) != 2:
        print("Usage: python notion_summaries.py <YYYYMMDD> <sessionsBack> [--notion-only]")
        sys.exit(1)

    main(args[0], int(args[1]), notion_only=notion_only_flag)
