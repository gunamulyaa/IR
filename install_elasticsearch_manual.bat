@echo off
echo ====================================
echo  Elasticsearch Manual Installation
echo ====================================

set ES_VERSION=8.11.1
set ES_DIR=elasticsearch-%ES_VERSION%
set ES_ZIP=%ES_DIR%-windows-x86_64.zip
set ES_URL=https://artifacts.elastic.co/downloads/elasticsearch/%ES_ZIP%

echo This script will:
echo 1. Download Elasticsearch %ES_VERSION% for Windows
echo 2. Extract it to current directory
echo 3. Configure it for development use
echo 4. Start Elasticsearch server
echo.
echo Size: ~500MB download
echo.
set /p choice="Continue? (y/n): "
if /i not "%choice%"=="y" exit /b 0

echo.
echo Downloading Elasticsearch...
if not exist "%ES_ZIP%" (
    echo Downloading from: %ES_URL%
    echo Please wait, this may take a few minutes...
    echo.
    
    REM Try using PowerShell to download
    powershell -Command "& {[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; Invoke-WebRequest -Uri '%ES_URL%' -OutFile '%ES_ZIP%' -UseBasicParsing}"
    
    if not exist "%ES_ZIP%" (
        echo ❌ Download failed. Please download manually from:
        echo %ES_URL%
        echo Save it as: %CD%\%ES_ZIP%
        echo Then run this script again
        pause
        exit /b 1
    )
    
    echo ✅ Download completed!
)

echo Extracting Elasticsearch...
if not exist "%ES_DIR%" (
    echo Extracting %ES_ZIP%...
    
    REM Try using PowerShell to extract
    powershell -Command "& {Expand-Archive -Path '%ES_ZIP%' -DestinationPath '.' -Force}"
    
    if not exist "%ES_DIR%" (
        echo ❌ Extraction failed. Please extract manually:
        echo 1. Right-click on %ES_ZIP%
        echo 2. Select "Extract All..."
        echo 3. Extract to current directory: %CD%
        echo Then run this script again
        pause
        exit /b 1
    )
    
    echo ✅ Extraction completed!
)

cd "%ES_DIR%"

echo Configuring Elasticsearch for development...
echo # Development Configuration > config\elasticsearch.yml
echo network.host: localhost >> config\elasticsearch.yml
echo http.port: 9200 >> config\elasticsearch.yml
echo discovery.type: single-node >> config\elasticsearch.yml
echo xpack.security.enabled: false >> config\elasticsearch.yml
echo cluster.name: ir-cluster >> config\elasticsearch.yml
echo node.name: ir-node >> config\elasticsearch.yml

echo.
echo Starting Elasticsearch...
echo ⚠️ Keep this window open while using the application
echo.
call bin\elasticsearch.bat

pause
