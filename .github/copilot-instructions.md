# Notion Performance Summaries

This Python application generates performance summaries for chipmunk lab data, backs them up to Google Drive, and uploads them to Notion databases. The script processes lab animal data subjects, generates visualizations using MATLAB, and integrates with the Notion API.

**Always reference these instructions first and fallback to search or bash commands only when you encounter unexpected information that does not match the info here.**

## Working Effectively

### Environment Setup
- This is a Python 3 application with minimal dependencies
- Required Python packages: `requests` (for Notion API calls)
- External tool dependencies: `labdata`, `matlab`, `rclone` (see External Tools section)
- Set required environment variables:
  - `export NOTION_TOKEN=your_notion_integration_token`
  - `export LAB_ANIMALS_DB_ID=your_notion_lab_database_id`

### Basic Operation
- Main script: `notion_summaries.py`
- Usage: `python notion_summaries.py <YYYYMMDD> <sessionsBack> [--notion-only]`
- Example: `python notion_summaries.py 20250820 9`
- Example (skip data processing): `python notion_summaries.py 20250820 9 --notion-only`

### Testing and Validation
- **NEVER CANCEL: Script execution takes 2-10 minutes per subject depending on data size. Set timeout to 30+ minutes.**
- Basic functionality test: `NOTION_TOKEN=test_token LAB_ANIMALS_DB_ID=test_db python notion_summaries.py 20250820 9 --notion-only`
- Import test: `python -c "import requests; import json; print('Dependencies OK')"`
- **CRITICAL**: Always test with real environment variables and the `--notion-only` flag first to avoid external tool dependencies

## External Tools and Dependencies

### Required External Tools (NOT Available in Standard Environment)
- **labdata**: Command-line tool for lab data management
  - Used for session discovery and data downloading
  - Commands called: `labdata sessions <subject> --files`, `labdata get <subject> -s <session> -d chipmunk -i *.mat`
  - **LIMITATION**: This tool is NOT available in standard environments and will cause FileNotFoundError
- **matlab**: MATLAB command-line interface
  - Used for running `batchCopyPlot` function to generate performance visualizations
  - Command called: `matlab -batch "batchCopyPlot({'subject'}, 'input', 'labdata', 'output', sessions_back, 'pattern')"`
  - **LIMITATION**: MATLAB is NOT available in standard environments and will cause FileNotFoundError
- **rclone**: Cloud storage sync tool
  - Used for backing up generated PNG files to Google Drive
  - Command called: `rclone copy <local_file> my_gdrive:performance_summaries/<subject>`
  - **LIMITATION**: rclone is NOT available in standard environments and will cause FileNotFoundError

### Working Without External Tools
- Use the `--notion-only` flag to skip data processing and MATLAB execution
- This mode attempts to upload existing PNG files from the output directory to Notion
- **LIMITATION**: Even `--notion-only` mode requires `rclone` for file upload and will fail with FileNotFoundError
- Safe for testing argument parsing and basic script flow without external dependencies when no PNG files exist

## Validation Scenarios

### Primary Validation Workflow
1. **Environment Check**: Verify Python and requests are available
2. **Basic Script Test**: Run with `--notion-only` flag and mock environment variables
3. **API Integration Test**: Test Notion API calls (requires real tokens)
4. **Full Pipeline Test**: Run complete workflow (requires all external tools)

### Manual Testing Steps
```bash
# 1. Test imports and basic functionality
python -c "import requests; import json; print('Python dependencies OK')"

# 2. Test script usage without external tools (safe when no output directories exist)
NOTION_TOKEN=test_token LAB_ANIMALS_DB_ID=test_db python notion_summaries.py 20250820 9 --notion-only

# 3. Check for external tool availability (will fail in standard environments)
which labdata  # Expected: not found
which matlab   # Expected: not found  
which rclone   # Expected: not found

# 4. Test with real environment variables (if available)
# python notion_summaries.py 20250820 9 --notion-only

# Note: If PNG files exist in output directories, --notion-only will fail due to missing rclone
```

## Code Structure and Key Components

### Main Entry Point
- `if __name__ == "__main__":` block at line 280
- Parses command line arguments: pattern (YYYYMMDD), sessions_back (int), optional --notion-only flag
- Calls `main(pattern, sessions_back, notion_only=False)`

### Key Functions
- `main()`: Main processing loop for all subjects
- `ensure_sessions()`: Downloads lab data using labdata command
- `run_matlab()`: Executes MATLAB script for visualization generation
- `upload_to_drive()`: Backs up files to Google Drive and uploads to Notion
- `find_subject_page()`: Finds Notion page for a lab subject
- `insert_summary()`: Creates database entries in Notion

### Configuration
- Subjects: `["GRB036", "GRB037", "GRB038", "GRB039", "GRB045", "GRB046", "GRB047"]`
- Output directory: `/Users/gabriel/performance_summaries`
- Google Drive remote: `my_gdrive:performance_summaries`
- Notion API versions: Current (2025-09-03) and Legacy (2022-06-28)

## Common Issues and Limitations

### Expected Failures in Standard Environments
- `FileNotFoundError: 'labdata'` - labdata command not available
- `FileNotFoundError: 'matlab'` - MATLAB not available  
- `FileNotFoundError: 'rclone'` - rclone not available
- Missing output directories when using `--notion-only` flag

### Environment-Specific Paths
- Input data location: `/Users/gabriel/data` (hardcoded, may not exist)
- Output location: `/Users/gabriel/performance_summaries` (hardcoded, may not exist)

### API Requirements
- Valid Notion integration token with database access permissions
- Lab Animals database ID must exist in the Notion workspace
- Network access to api.notion.com

## Development Workflow

### Making Changes
1. **ALWAYS** test basic imports first: `python -c "import requests; print('OK')"`
2. Test with `--notion-only` flag before full workflow testing
3. Use mock environment variables for testing script argument parsing
4. When adding new Notion API calls, test with real tokens in a safe environment
5. Document any new external tool dependencies clearly

### Debugging
- Script prints detailed status messages with emoji indicators (⏳ ⚠️ ✔️ ⬇️ 📁)
- Check environment variables are set correctly
- Verify Notion tokens have proper permissions
- Use `--notion-only` to isolate API issues from external tool issues

## File Structure Reference
```
.
├── .git/
├── .gitignore          # Standard Python gitignore
├── README.md           # Basic usage documentation
└── notion_summaries.py # Main application script (10KB+)
```

**CRITICAL REMINDERS:**
- **NEVER CANCEL**: Allow sufficient time for data processing and MATLAB execution (30+ minute timeout)
- Always test the `--notion-only` mode first when making changes
- External tools (labdata, matlab, rclone) are NOT available in standard development environments
- Use real Notion credentials cautiously and only in secure environments