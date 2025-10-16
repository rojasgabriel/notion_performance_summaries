# notion_performance_summaries
Code for generating performance summaries for chipmunk and directly uploading them into a database in Notion. This works with labdata-tools, not labdata (yet).

`extensive testing is still required!!!`

## Installation

In the folder you cloned the repo, run:
```bash
pip install -e .
```

## Configuration

When you first run the code, it will automatically create a `preferences.json` file with empty settings that you must fill out. The code will not run until you configure your specific paths and lab subjects. These paths are the ones that the MATLAB batch copy script needs to generate the summaries.

### Preferences file location

The preferences file is stored in:
`~/.notion_performance_summaries/preferences.json`

### Required fields

You must edit these fields in your `preferences.json`:

- **`paths.input_loc`**: Directory where your data are stored
- **`paths.output_loc`**: Directory where performance summary PNG files will be saved
- **`paths.remote`**: rclone remote path for Google Drive backup (format: `remote_name:folder_path`)
- **`subjects`**: List of lab subject IDs to process (e.g., `["GRB036", "GRB037"]`)

## Usage

```bash
notion_summaries [-h] [--notion-only] [--overwrite] date_pattern sessions_back
```

### Examples

Generate summaries for all subjects starting from date 20250820, going back 9 sessions:
```bash
notion_summaries 20250820 9
```

Skip data processing and only upload (and backup) existing PNG files to Notion:
```bash
notion_summaries 20250820 9 --notion-only
```

Overwrite existing database entries and Google Drive backups instead of skipping them:
```bash
notion_summaries 20250820 9 --overwrite
```
