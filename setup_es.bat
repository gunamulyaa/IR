@echo off
echo ====================================
echo     Quick Elasticsearch Setup
echo ====================================

echo Choose installation method:
echo 1. Auto download and install (Recommended)
echo 2. I already have Elasticsearch downloaded
echo 3. Skip Elasticsearch, run app in simple mode
echo.
set /p choice="Enter choice (1-3): "

if "%choice%"=="1" goto auto_install
if "%choice%"=="2" goto manual_install
if "%choice%"=="3" goto simple_mode

:auto_install
echo.
echo === AUTO INSTALLATION ===
call install_elasticsearch_manual.bat
goto end

:manual_install
echo.
echo === MANUAL INSTALLATION ===
echo Please ensure you have downloaded:
echo elasticsearch-8.11.1-windows-x86_64.zip
echo.
echo Available files:
dir *.zip 2>nul
echo.
set /p continue="Continue with manual installation? (y/n): "
if /i "%continue%"=="y" call install_elasticsearch_manual.bat
goto end

:simple_mode
echo.
echo === SIMPLE MODE ===
echo Running application without Elasticsearch...
echo This will use basic search functionality.
echo.
python quick_start.py
goto end

:end
echo.
echo Installation process completed!
pause
