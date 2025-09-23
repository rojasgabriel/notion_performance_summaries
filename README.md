# notion_performance_summaries
code for generating performance summaries for chipmunk and directly uploading them into a database in notion

`extensive testing is still required!!!`

## Installation

Install the package using pip:
```bash
pip install -e .
```

## Configuration

⚠️ **IMPORTANT**: You must configure the application before first use!

When you first run the application, it will automatically create a `preferences.json` file with empty settings that you must fill out. The application will not run until you configure your specific paths and lab subjects.

### Preferences File Location

The preferences file is searched for in this order:
1. Current working directory: `./preferences.json`
2. User home directory: `~/.notion_performance_summaries/preferences.json`

### Required Configuration

You must configure these required fields in your `preferences.json`:

- **`paths.input_loc`**: Directory where your data are stored
- **`paths.output_loc`**: Directory where performance summary PNG files will be saved
- **`paths.remote`**: rclone remote path for Google Drive backup (format: `remote_name:folder_path`)
- **`subjects`**: List of lab subject IDs to process (e.g., `["GRB036", "GRB037"]`)

### Preferences Structure

A complete example with descriptions can be found in `preferences.example.json`. Your `preferences.json` should look like:

```json
{
  "paths": {
    "input_loc": "/path/to/your/lab/data",
    "output_loc": "/path/to/your/performance/summaries",
    "remote": "your_gdrive_remote:folder_name"
  },
  "subjects": [
    "YOUR_SUBJECT_001", "YOUR_SUBJECT_002"
  ],
  "notion": {
    "version": "2025-09-03",
    "version_legacy": "2022-06-28"
  }
}
```

You can edit this file to:
- Change input and output directory paths
- Modify the Google Drive remote path
- Update the list of lab subjects to process
- Adjust Notion API versions if needed

## Usage

After installation, you can use the `notion_summaries` command directly:

```bash
notion_summaries 20250820 9
```

Available options:
```bash
notion_summaries [-h] [--notion-only] [--overwrite] date_pattern sessions_back
```

### Examples

Generate summaries for all subjects starting from date 20250820, going back 9 sessions:
```bash
notion_summaries 20250820 9
```

Skip data processing and only upload existing PNG files to Notion:
```bash
notion_summaries 20250820 9 --notion-only
```

Overwrite existing database entries instead of skipping them:
```bash
notion_summaries 20250820 9 --overwrite
```

Combine flags to skip processing and overwrite existing entries:
```bash
notion_summaries 20250820 9 --notion-only --overwrite
```

### Arguments

- `date_pattern`: Date pattern in YYYYMMDD format (e.g., 20250820)
- `sessions_back`: Number of sessions to go back from the pattern date
- `--notion-only`: Skip data processing and MATLAB execution, only upload existing PNG files to Notion
- `--overwrite`: Overwrite existing entries in the database instead of skipping them

This will generate performance summaries, back them up to Google Drive using rclone, and insert them into Notion.
