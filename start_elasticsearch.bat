@echo off
echo ====================================
echo  Starting Elasticsearch with Docker
echo ====================================

echo Checking if Docker is running...
docker --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Docker is not running or not installed
    echo.
    echo Please:
    echo 1. Install Docker Desktop from: https://www.docker.com/products/docker-desktop
    echo 2. Start Docker Desktop
    echo 3. Wait for Docker to fully start
    echo 4. Run this script again
    echo.
    pause
    exit /b 1
)

echo ✅ Docker is available
echo.

echo Stopping any existing Elasticsearch container...
docker stop elasticsearch 2>nul
docker rm elasticsearch 2>nul

echo Starting Elasticsearch container...
docker run -d ^
    --name elasticsearch ^
    -p 9200:9200 ^
    -e "discovery.type=single-node" ^
    -e "ES_JAVA_OPTS=-Xms512m -Xmx512m" ^
    -e "xpack.security.enabled=false" ^
    elasticsearch:8.11.1

if errorlevel 1 (
    echo ❌ Failed to start Elasticsearch container
    pause
    exit /b 1
)

echo ✅ Elasticsearch container started successfully!
echo.
echo Waiting for Elasticsearch to be ready...
timeout /t 10 /nobreak >nul

echo Testing Elasticsearch connection...
curl -s http://localhost:9200 >nul 2>&1
if errorlevel 1 (
    echo ⚠️ Elasticsearch is starting... please wait a moment
    echo Check status: docker logs elasticsearch
) else (
    echo ✅ Elasticsearch is ready!
    echo 🌐 Access: http://localhost:9200
)

echo.
echo Next steps:
echo 1. Run: python setup_elasticsearch.py --setup
echo 2. Run: streamlit run app_elasticsearch.py
echo.
pause
