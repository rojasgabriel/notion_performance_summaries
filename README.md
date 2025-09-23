# notion_performance_summaries
code for generating performance summaries for chipmunk and directly uploading them into a database in notion

`extensive testing is still required!!!`

features still pending:
- create a performance summaries db in a subject's page if it doesn't exist before attempting to insert a record

## Usage

Basic usage:
```bash
python notion_summaries.py 20250820 9
```

Available options:
```bash
python notion_summaries.py [-h] [--notion-only] [--overwrite] pattern sessions_back
```

### Examples

Generate summaries for all subjects starting from date 20250820, going back 9 sessions:
```bash
python notion_summaries.py 20250820 9
```

Skip data processing and only upload existing PNG files to Notion:
```bash
python notion_summaries.py 20250820 9 --notion-only
```

Overwrite existing database entries instead of skipping them:
```bash
python notion_summaries.py 20250820 9 --overwrite
```

Combine flags to skip processing and overwrite existing entries:
```bash
python notion_summaries.py 20250820 9 --notion-only --overwrite
```

### Arguments

- `pattern`: Date pattern in YYYYMMDD format (e.g., 20250820)
- `sessions_back`: Number of sessions to go back from the pattern date
- `--notion-only`: Skip data processing and MATLAB execution, only upload existing PNG files to Notion
- `--overwrite`: Overwrite existing entries in the database instead of skipping them

This will generate performance summaries, back them up to Google Drive using rclone, and insert them into Notion.
