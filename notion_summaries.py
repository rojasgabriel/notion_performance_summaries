import os
import re
import sys

# Import from organized modules
from config import OUTPUT_LOC, SUBJECTS
from data_processing import ensure_sessions, run_matlab
from notion_api import find_subject_page, find_child_db, insert_summary
from file_operations import upload_to_drive


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
            run_matlab(
                subject, input_loc, labdata_loc, subject_output, sessions_back, pattern
            )
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
                session_name = (
                    match.group(1) if match else fname.replace("_summary.png", "")
                )

                insert_summary(
                    perf_db_id,
                    subject,
                    notion_file_id=notion_file_id,
                    session_name=session_name,
                )


if __name__ == "__main__":
    notion_only_flag = False
    args = sys.argv[1:]
    if "--notion-only" in args:
        notion_only_flag = True
        args.remove("--notion-only")

    if len(args) != 2:
        print(
            "Usage: python notion_summaries.py <YYYYMMDD> <sessionsBack> [--notion-only]"
        )
        sys.exit(1)

    main(args[0], int(args[1]), notion_only=notion_only_flag)
