@echo off
echo ========================================
echo   📰 IR System with Elasticsearch  
echo ========================================

cd /d "C:\Users\SAMSUNG\Documents\GitHub\IR"

echo Activating virtual environment...
call .venv\Scripts\activate.bat

echo.
echo Checking system requirements...
python -c "import streamlit, json; print('✅ All requirements OK')" 2>nul
if errorlevel 1 (
    echo ❌ Requirements missing. Run install.bat first.
    pause
    exit /b 1
)

echo.
echo Starting Streamlit application...
echo Browser will open automatically at http://localhost:8501
echo Press Ctrl+C to stop the application
echo.

streamlit run app.py --server.port 8501 --server.headless false

pause
