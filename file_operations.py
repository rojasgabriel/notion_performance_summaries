"""File operations including Notion uploads and Google Drive backup."""

import os
import json
import requests
from config import OUTPUT_LOC, REMOTE, base_headers, json_headers
from data_processing import run_cmd


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
        print(
            f"📤 Starting direct Notion upload for {file_name} ({file_size} bytes)..."
        )

        # Step 1: Create a file upload (JSON)
        create_payload = {
            "filename": file_name,
            "content_type": mime_type,
            "mode": "single_part",
        }
        r_create = requests.post(
            "https://api.notion.com/v1/file_uploads",
            headers=json_headers,
            json=create_payload,
        )
        try:
            r_create.raise_for_status()
        except requests.exceptions.HTTPError as e:
            body = None
            try:
                body = r_create.text
            except Exception:
                pass
            print(
                f"❌ HTTP Error during Notion create file upload: {e}\nResponse Body: {body}"
            )
            raise

        meta = r_create.json()
        file_id = meta.get("id") or (
            meta.get("file_upload", {})
            if isinstance(meta.get("file_upload"), dict)
            else {}
        ).get("id")
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
            print(
                f"❌ HTTP Error during Notion send file upload: {e}\nResponse Body: {body}"
            )
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
