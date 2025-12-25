# Reddit Analyzer

A comprehensive Reddit analysis tool designed for OSINT (Open Source Intelligence) purposes. Analyze subreddit activity, user behavior, account creation patterns, and find overlapping users across multiple datasets.

## Features

### 1. Subreddit Analysis

Analyze activity and contributors within a specific subreddit using posts and comments JSONL files.

**Input Requirements:**
- **File A (Posts)**: JSONL file containing Reddit posts from a single subreddit
- **File B (Comments)**: JSONL file containing Reddit comments from the same subreddit
- Both files must be from the same subreddit (validated automatically)

**Features:**
- **Unique Usernames**: Extract and display all unique usernames with export to TXT functionality
- **Top 20 Contributors**: View the most active contributors ranked by post/comment count
- **Activity Tracker**: GitHub-style contribution calendar showing daily activity levels
  - Filter by year
  - Displays all 365/366 days of the selected year
  - Horizontal layout (weeks as columns, days as rows)
- **Day-by-Day Posting Hours Heatmap**: Visualize posting patterns by hour and day of week
  - Timezone adjustment support (UTC, US timezones, UK, Europe, Japan, Australia)
  - Color-coded intensity levels
- **Exploratory Statistics**:
  - Posts per Day (PPD)
  - Posts per Hour (PPH)
  - Total posts/comments count
  - Unique usernames count
  - Date range
  - Average posts per user

### 2. User Analysis

Analyze individual Reddit user activity patterns across multiple subreddits.

**Input Requirements:**
- **File A (Posts)**: JSONL file containing posts from a single Reddit user
- **File B (Comments)**: JSONL file containing comments from the same Reddit user
- Both files must be from the same user (validated automatically)
- User can have activity across multiple subreddits

**Features:**
- **Subreddit Frequency List**: View all subreddits the user participates in, sorted by activity frequency
- **Activity Tracker**: GitHub-style contribution calendar
  - Filter by year
  - Displays all 365/366 days of the selected year
  - Horizontal layout matching GitHub's style
- **Day-by-Day Posting Hours Heatmap**: Analyze posting time patterns
  - Timezone adjustment support
  - Interactive cells showing day, hour, and activity count

### 3. Creation Year Distribution

Analyze the distribution of account creation years for a list of Reddit usernames.

**Input Requirements:**
- TXT file with one username per line

**Features:**
- **Pagination**: Process and display results in pages of 1000 users
- **Persistent Caching**: API responses are cached to avoid redundant requests
- **Year Distribution**: Visualize how many accounts were created in each year
- **Filter by Year**: View detailed breakdown for specific years
- **Progress Tracking**: Real-time progress bar and status updates
- **Account Status**: Shows account status (active, suspended, deleted, etc.)
- **Clickable Results**: Click usernames to open their Reddit profile in browser

### 4. Overlapping Users

Find users that appear in all submitted files (set intersection).

**Input Requirements:**
- 2 to 5 TXT files, each containing Reddit usernames (one per line)

**Features:**
- **Multi-File Analysis**: Find users present in ALL submitted files
- **Account Information**: Fetches creation dates and account status via Reddit API
- **Year Filtering**: Filter results by account creation year
- **Progress Tracking**: Real-time progress updates during API calls
- **Export Results**: View and export overlapping users with their account details
- **Clickable Usernames**: Open user profiles directly from results

### 5. Settings

Configuration and application settings.

## File Format Requirements

### JSONL Files (Subreddit Analysis & User Analysis)

Each line must be a valid JSON object representing a Reddit post or comment.

**Post objects should contain:**
- `subreddit` or `subreddit_name_prefixed`
- `author`
- `created_utc` or `created`
- `title` or `is_self` (post-specific fields)

**Comment objects should contain:**
- `subreddit` or `subreddit_name_prefixed`
- `author`
- `created_utc` or `created`
- `body` and `link_id` (comment-specific fields)

### TXT Files (Creation Year & Overlapping Users)

Plain text files with one Reddit username per line:
```
username1
username2
username3
```

## Validation

The application includes comprehensive validation:

- **Subreddit Analysis**: Ensures both files are from the same subreddit
- **User Analysis**: Ensures both files are from the same Reddit user
- **File Type Validation**: Verifies posts vs comments structure
- **Required Fields**: Checks for necessary JSON fields
- **File Format**: Validates JSONL structure

## Requirements

- Python 3.8 or higher
- `tkinter` - GUI framework (usually included with Python)
  - On Linux: may need to install `python3-tk` package
  - On macOS with Homebrew Python: included by default
  - On Windows: included with Python

## Installation

### Using Virtual Environment (Recommended)

For reproducibility and to avoid conflicts with system packages, use a virtual environment:

#### Windows:
```bash
# Run the setup script
setup_env.bat

# Or manually:
python -m venv venv
venv\Scripts\activate
pip install --upgrade pip
pip install -r requirements.txt
```

#### Linux/macOS:
```bash
# Make the script executable (first time only)
chmod +x setup_env.sh

# Run the setup script
./setup_env.sh

# Or manually:
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

### Manual Installation (Without Virtual Environment)

If you prefer not to use a virtual environment:

```bash
pip install -r requirements.txt
```

**Note:** This is not recommended as it may conflict with other Python projects.

## Usage

1. **Activate the virtual environment** (if using one):
   - Windows: `venv\Scripts\activate`
   - Linux/macOS: `source venv/bin/activate`

2. **Run the application**:
   ```bash
   python reddit.py
   ```

3. Select the appropriate tab for your analysis type

4. Load your JSONL or TXT files using the file browser

5. Click "Analyze" to process the data

6. Explore the results using the interactive visualizations and filters


## Notes

- API requests are cached to improve performance and reduce rate limiting
- Large datasets are processed efficiently with pagination
- All timestamps are handled in UTC and can be converted to local timezones
- The application validates file structure before processing to prevent errors
