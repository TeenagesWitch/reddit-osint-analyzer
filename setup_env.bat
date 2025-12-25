@echo off
REM Setup script for Windows
echo Creating virtual environment...
python -m venv venv

echo Activating virtual environment...
call venv\Scripts\activate.bat

echo Installing dependencies...
pip install --upgrade pip
pip install -r requirements.txt

echo.
echo Setup complete! To activate the virtual environment, run:
echo   venv\Scripts\activate.bat
echo.
echo Then run the application with:
echo   python reddit.py
echo.

