# Development Guide

## Setting Up Development Environment

1. **Clone the repository** (if applicable)

2. **Create and activate virtual environment**:
   ```bash
   # Windows
   python -m venv venv
   venv\Scripts\activate
   
   # Linux/macOS
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Install dependencies**:
   ```bash
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

## Project Structure

```
reddit-analyzer/
├── reddit.py                 # Main entry point
├── config.py                 # Configuration constants
├── cache.py                  # Caching functionality
├── skip_list.py              # Skip list management
├── reddit_api.py             # Reddit API interactions
├── gui/
│   ├── main_app.py          # Main application window
│   └── tabs/
│       ├── unique_extractor_tab.py    # Subreddit Analysis
│       ├── user_analysis_tab.py        # User Analysis
│       ├── creation_year_tab.py        # Creation Year Distribution
│       ├── overlapping_users_tab.py    # Overlapping Users
│       └── settings_tab.py            # Settings
├── requirements.txt          # Python dependencies
├── README.md                 # User documentation
└── DEVELOPMENT.md           # This file
```

## Code Style

- Follow PEP 8 style guidelines
- Use type hints where appropriate
- Document functions and classes with docstrings
- Keep functions focused and modular

## Testing

Currently, manual testing is performed. Consider adding automated tests in the future.

## Adding New Features

1. Create new tab classes in `gui/tabs/`
2. Import and add to `gui/tabs/__init__.py`
3. Register in `gui/main_app.py`
4. Update `README.md` with feature documentation

## Dependencies

- **requests**: HTTP library for Reddit API
- **pytz**: Timezone support
- **tkinter**: GUI framework (standard library)

To add a new dependency:
1. Add to `requirements.txt` with version constraints
2. Update this documentation if needed
3. Test installation in a fresh virtual environment

## Building Executable

To create a standalone executable using PyInstaller:

```bash
pip install pyinstaller
pyinstaller --onefile --windowed reddit.py
```

The executable will be in the `dist/` directory.

