import os
import re
import argparse

# Import from organized modules
from .config import OUTPUT_LOC, SUBJECTS  # type: ignore
from .data_processing import ensure_sessions, run_matlab  # type: ignore
from .notion_api import find_subject_page, find_child_db, insert_summary  # type: ignore
from .file_operations import upload_to_drive, backup_subject  # type: ignore
from .preferences import get_preference  # type: ignore


# === MAIN PIPELINE ===
def main(pattern, sessions_back, notion_only=False, overwrite=False, dry_run=False):
    input_loc = get_preference("paths.input_loc")
    labdata_loc = input_loc

    for subject in SUBJECTS:
        print(f"\n⏳ Processing {subject}")

        if not notion_only:
            sessions = ensure_sessions(
                subject, pattern, sessions_back, input_loc, dry_run=dry_run
            )
            if not sessions:
                continue
            subject_output = f"{OUTPUT_LOC}/{subject}"
            run_matlab(
                subject,
                input_loc,
                labdata_loc,
                subject_output,
                sessions_back,
                pattern,
                dry_run=dry_run,
            )
        else:
            subject_output = f"{OUTPUT_LOC}/{subject}"
            if not os.path.exists(subject_output):
                print(f"⚠️ No output directory for {subject}, skipping Notion upload")
                continue

        # Find PNGs that match the EXACT pattern date only
        subject_output = f"{OUTPUT_LOC}/{subject}"
        if not os.path.exists(subject_output):
            continue

        # Perform a single backup per subject (copy vs sync) before per-file Notion uploads
        backup_subject(subject, overwrite=overwrite, dry_run=dry_run)

        processed = set()
        for fname in sorted(os.listdir(subject_output)):
            if fname.endswith(".png"):
                # Extract date from filename to check if it matches the exact pattern
                match = re.search(r"(\d{8})", fname)
                file_date = match.group(1) if match else None

                # Skip files that don't match the exact pattern date
                if file_date and file_date != pattern:
                    print(f"⏭️ Skipping {fname} - not matching pattern date {pattern}")
                    continue

                if fname in processed:
                    continue
                # Upload only to Notion; backup already done for the subject
                notion_file_id = upload_to_drive(
                    subject,
                    fname,
                    overwrite=overwrite,
                    backup_already_done=True,
                    dry_run=dry_run,
                )
                if dry_run:
                    print("DRY RUN: Skipping Notion API calls")
                    continue

                page_id = find_subject_page(subject)
                if not page_id:
                    print(f"⚠️ No Notion page for {subject}")
                    continue
                perf_db_id = find_child_db(page_id)
                if not perf_db_id:
                    print(f"⚠️ No child DB for {subject}")
                    continue

                # Extract a cleaner session name from the filename
                session_name = (
                    file_date if file_date else fname.replace("_summary.png", "")
                )

                insert_summary(
                    perf_db_id,
                    subject,
                    notion_file_id=notion_file_id,
                    session_name=session_name,
                    overwrite=overwrite,
                )
                processed.add(fname)


def parse_arguments():
    """Parse command line arguments using argparse."""
    parser = argparse.ArgumentParser(
        description="Generate performance summaries for chipmunk lab data and upload them to Notion.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
            Examples:
            notion_summaries 20250820 9
            notion_summaries 20250820 9 --notion-only
            notion_summaries 20250820 9 --overwrite
            notion_summaries 20250820 9 --notion-only --overwrite
                    """,
    )

    parser.add_argument(
        "date_pattern", help="Date pattern in YYYYMMDD format (e.g., 20250820)"
    )

    parser.add_argument(
        "sessions_back",
        type=int,
        help="Number of sessions to go back from the pattern date",
    )

    parser.add_argument(
        "--notion-only",
        action="store_true",
        help="Skip data processing and MATLAB execution, only upload existing PNG files to Notion",
    )

    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite existing entries in the database instead of skipping them",
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print commands that would be executed without running them",
    )

    return parser.parse_args()


def cli():
    """Entry point for the console script."""
    args = parse_arguments()
    main(
        args.date_pattern,
        args.sessions_back,
        notion_only=args.notion_only,
        overwrite=args.overwrite,
        dry_run=args.dry_run,
    )


if __name__ == "__main__":
    cli()
