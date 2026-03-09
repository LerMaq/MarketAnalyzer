@echo off
REM Create virtual environment
if not exist .venv (
    echo "Creating virtual environment..."
    python -m venv .venv
)

REM Activate virtual environment
echo "Activating virtual environment..."
call .venv\Scripts\activate.bat

REM Install requirements
echo "Installing requirements..."
pip install -r requirements.txt

REM Run main.py
echo "Starting scraper..."
python main.py

REM Deactivate virtual environment
echo "Deactivating virtual environment..."
deactivate
pause