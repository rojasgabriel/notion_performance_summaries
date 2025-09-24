"""File operations including Notion uploads and Google Drive backup."""

import os
import json
import requests
from .config import OUTPUT_LOC, REMOTE, base_headers, json_headers  # type: ignore
from .data_processing import run_cmd  # type: ignore


def upload_to_notion_and_get_file_id(filepath):
    """Upload a file using ONLY the 2025-09-03 Notion file upload flow.

    Flow:
      1) POST /v1/file_uploads  { filename, content_type, mode=single_part }
      2) POST /v1/file_uploads/{id}/send (multipart form field "file")
      3) Reference returned id in Files & media property as type file_upload.
    """
    try:
        file_name = os.path.basename(filepath)
        mime_type = "image/png"
        file_size = os.path.getsize(filepath)
        print(
            f"📤 Starting direct Notion upload for {file_name} ({file_size} bytes)..."
        )

        # Step 1: Create file upload descriptor
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
        r_create.raise_for_status()
        meta = r_create.json()
        file_id = meta.get("id") or (
            meta.get("file_upload", {})
            if isinstance(meta.get("file_upload"), dict)
            else {}
        ).get("id")
        if not file_id:
            print("⚠️ Unexpected create response:", json.dumps(meta, indent=2))
            raise RuntimeError("Notion did not return file upload id")

        # Step 2: Send file bytes
        send_url = f"https://api.notion.com/v1/file_uploads/{file_id}/send"
        with open(filepath, "rb") as f:
            files = {"file": (file_name, f, mime_type)}
            r_send = requests.post(send_url, headers=base_headers, files=files)
        r_send.raise_for_status()

        print(f"✅ Uploaded to Notion (file id: {file_id})")
        return file_id
    except requests.exceptions.HTTPError as e:
        body = None
        try:
            body = e.response.text  # type: ignore[attr-defined]
        except Exception:
            pass
        print(f"❌ HTTP error during Notion upload: {e}\nBody: {body}")
        raise
    except Exception as e:
        print(f"❌ Notion upload failed: {e}")
        raise


def backup_subject(subject: str, overwrite: bool = False):
    """Perform a single backup operation for a subject directory."""
    subject_dir = f"{OUTPUT_LOC}/{subject}"
    if not os.path.isdir(subject_dir):
        print(f"⚠️ Subject directory missing, skipping backup: {subject_dir}")
        return
    remote_path = f"{REMOTE}/{subject}"
    cmd = ["rclone", "copy", "--progress", subject_dir, remote_path]
    if not overwrite:
        cmd.append("--ignore-existing")
    run_cmd(cmd)
    print(f"✅ Backup complete: {remote_path}")


def upload_to_drive(subject, fname, overwrite=False, backup_already_done=True):
    """Upload PNG to Notion (assumes backup already handled unless specified)."""
    subject_dir = f"{OUTPUT_LOC}/{subject}"
    file_path = f"{subject_dir}/{fname}"
    if not os.path.exists(file_path):
        raise FileNotFoundError(file_path)
    if not backup_already_done:
        # Fallback single file backup if explicitly requested (not expected in main flow)
        remote_path = f"{REMOTE}/{subject}"
        cmd = ["rclone", "copy", "--progress", subject_dir, remote_path]
        if not overwrite:
            cmd.append("--ignore-existing")
        run_cmd(cmd)
        print(f"📁 On-demand backup performed for {fname}")
    return upload_to_notion_and_get_file_id(file_path)
