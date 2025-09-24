import os
import re
import argparse

# Import from organized modules
from config import OUTPUT_LOC, SUBJECTS
from data_processing import ensure_sessions, run_matlab
from notion_api import find_subject_page, find_child_db, insert_summary
from file_operations import upload_to_drive
from preferences import get_preference


# === MAIN PIPELINE ===
def main(pattern, sessions_back, notion_only=False, overwrite=False):
    input_loc = get_preference("paths.input_loc")
    labdata_loc = input_loc

    for subject in SUBJECTS:
        print(f"\n⏳ Processing {subject}")
        sessions = []

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
            # In notion-only mode, determine which sessions should be processed
            # based on pattern and sessions_back to avoid processing all files
            sessions = _get_sessions_for_pattern(subject, pattern, sessions_back)

        # Extract date patterns from sessions for filtering PNG files
        # Sessions are in format YYYYMMDD_HHMMSS, we need YYYYMMDD for matching
        session_dates = (
            {session.split("_")[0] for session in sessions} if sessions else set()
        )

        # Find PNGs that match the current session pattern
        subject_output = f"{OUTPUT_LOC}/{subject}"
        if not os.path.exists(subject_output):
            continue

        for fname in os.listdir(subject_output):
            if fname.endswith(".png"):
                # Extract date from filename to check if it matches current sessions
                match = re.search(r"(\d{8})", fname)
                file_date = match.group(1) if match else None

                # Skip files that don't match the current session dates
                if session_dates and file_date and file_date not in session_dates:
                    print(f"⏭️ Skipping {fname} - not in current session scope")
                    continue

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


def _get_sessions_for_pattern(subject, pattern, sessions_back):
    """
    Get sessions that would be processed for a given pattern and sessions_back.
    This is used in notion-only mode to determine which PNG files should be processed.
    """
    try:
        # Use the same logic as ensure_sessions but without downloading
        from data_processing import run_cmd

        out = run_cmd(["labdata", "sessions", subject, "--files"])
        sessions = sorted(
            list(set(re.findall(r"[0-9]{8}_[0-9]{6}", out))), reverse=True
        )
        # Find pattern match
        match_index = next(
            (i for i, s in enumerate(sessions) if s.startswith(pattern)), -1
        )
        if match_index < 0:
            print(f"❌ No session found for {subject} with {pattern}")
            return []
        end_index = min(match_index + sessions_back + 1, len(sessions))
        return sessions[match_index:end_index]
    except Exception as e:
        print(f"⚠️ Could not determine sessions for {subject}: {e}")
        print("⚠️ Processing all PNG files in notion-only mode")
        return []


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

    return parser.parse_args()


def cli():
    """Entry point for the console script."""
    args = parse_arguments()
    main(
        args.date_pattern,
        args.sessions_back,
        notion_only=args.notion_only,
        overwrite=args.overwrite,
    )


if __name__ == "__main__":
    cli()
