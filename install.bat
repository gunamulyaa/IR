@echo off
echo ====================================
echo Installing IR System Requirements
echo ====================================

cd /d "C:\Users\SAMSUNG\Documents\GitHub\IR"

echo Activating virtual environment...
call .venv\Scripts\activate.bat

echo Installing packages...
pip install streamlit
pip install elasticsearch==8.11.1
pip install python-dotenv
pip install pandas

echo.
echo Testing installation...
python -c "import streamlit; print('✅ Streamlit installed successfully')"
python -c "import elasticsearch; print('✅ Elasticsearch installed successfully')"
python -c "import dotenv; print('✅ Python-dotenv installed successfully')"
python -c "import pandas; print('✅ Pandas installed successfully')"

echo.
echo ====================================
echo Installation completed!
echo ====================================
echo.
echo To run the app:
echo   streamlit run app.py
echo.
pause
