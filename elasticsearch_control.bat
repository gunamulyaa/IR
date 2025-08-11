@echo off
title Elasticsearch Control

echo ====================================
echo     Elasticsearch Control Panel
echo ====================================

echo Choose an action:
echo 1. Start Elasticsearch
echo 2. Stop Elasticsearch
echo 3. Check Elasticsearch status
echo 4. View Elasticsearch logs
echo 5. Reset Elasticsearch data
echo 6. Exit
echo.
set /p action="Enter choice (1-6): "

if "%action%"=="1" goto start_es
if "%action%"=="2" goto stop_es
if "%action%"=="3" goto check_es
if "%action%"=="4" goto view_logs
if "%action%"=="5" goto reset_data
if "%action%"=="6" goto end

:start_es
echo.
echo === STARTING ELASTICSEARCH ===
if exist "elasticsearch-8.11.1\bin\elasticsearch.bat" (
    echo Starting Elasticsearch server...
    cd elasticsearch-8.11.1
    start "Elasticsearch Server" bin\elasticsearch.bat
    cd ..
    echo.
    echo ✅ Elasticsearch started in new window
    echo ⏳ Waiting for server to be ready...
    timeout /t 15 /nobreak >nul
    goto check_es
) else (
    echo ❌ Elasticsearch not found!
    echo Please run setup_es.bat first
)
goto menu

:stop_es
echo.
echo === STOPPING ELASTICSEARCH ===
taskkill /f /im java.exe 2>nul
echo ✅ Elasticsearch stopped
goto menu

:check_es
echo.
echo === CHECKING ELASTICSEARCH STATUS ===
curl -s http://localhost:9200 2>nul >temp_status.txt
if %errorlevel%==0 (
    echo ✅ Elasticsearch is running
    echo.
    echo Server info:
    type temp_status.txt
    del temp_status.txt 2>nul
) else (
    echo ❌ Elasticsearch is not running
    echo.
    echo To start: choose option 1
)
goto menu

:view_logs
echo.
echo === ELASTICSEARCH LOGS ===
if exist "elasticsearch-8.11.1\logs" (
    echo Latest log entries:
    echo.
    dir elasticsearch-8.11.1\logs\*.log /o-d /b | head -1 > temp_log.txt
    set /p latest_log=<temp_log.txt
    tail -20 "elasticsearch-8.11.1\logs\%latest_log%" 2>nul || echo No logs found
    del temp_log.txt 2>nul
) else (
    echo ❌ Log directory not found
)
goto menu

:reset_data
echo.
echo === RESET ELASTICSEARCH DATA ===
echo ⚠️ This will delete all indexed data!
set /p confirm="Are you sure? (y/n): "
if /i "%confirm%"=="y" (
    echo Stopping Elasticsearch...
    taskkill /f /im java.exe 2>nul
    timeout /t 3 /nobreak >nul
    
    if exist "elasticsearch-8.11.1\data" (
        echo Deleting data directory...
        rmdir /s /q "elasticsearch-8.11.1\data"
        echo ✅ Data reset completed
    ) else (
        echo ℹ️ No data directory found
    )
)
goto menu

:menu
echo.
echo Press any key to return to menu...
pause >nul
cls
goto start

:end
echo Goodbye!
timeout /t 2 /nobreak >nul
