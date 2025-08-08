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
:: Pin undetected-chromedriver to your installed Chrome major version on Windows
:: Adjust this if your Chrome updates (e.g., set to 139 when Chrome updates to 139)
set "UC_CHROME_VERSION_MAIN=138"
python main.py
if %errorlevel% neq 0 (
    echo Job scraper encountered an error.
    exit /b 1
)

echo Job scraper finished successfully.
exit /b 0
