@echo off

:: Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Python is not installed. Please install Python 3.10 or higher.
    exit /b 1
)

:: Install dependencies from requirements.txt
echo Installing dependencies...
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo Failed to install dependencies. Please check your Python and pip setup.
    exit /b 1
)

:: Run the main.py script
echo Starting the job scraper...
python main.py
if %errorlevel% neq 0 (
    echo Job scraper encountered an error.
    exit /b 1
)

echo Job scraper finished successfully.
exit /b 0
