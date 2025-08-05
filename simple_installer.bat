@echo off
chcp 949 > nul
title KakaoTalk OCR Chatbot Installer
color 0A

echo ============================================
echo    KakaoTalk OCR Chatbot Auto Installer
echo ============================================
echo.

:: Check admin rights
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo [WARNING] Administrator rights required.
    echo Please right-click and select "Run as administrator"
    pause
    exit /b 1
)

:: Check Python
echo [1/5] Checking Python installation...
python --version >nul 2>&1
if errorlevel 1 (
    echo.
    echo [ERROR] Python is not installed!
    echo.
    echo Please install Python 3.11 first.
    echo Download from: https://www.python.org/downloads/release/python-3119/
    echo.
    pause
    exit /b 1
)

echo [OK] Python is installed.
python --version
echo.

:: Create program folder
echo [2/5] Installing program...
set install_path=C:\KakaoOCRChatbot
if exist "%install_path%" (
    echo Removing existing folder...
    rmdir /s /q "%install_path%"
)
mkdir "%install_path%"

:: Copy files
echo Copying files...
xcopy /E /I /Y "program\*" "%install_path%"
echo [OK] Files copied
echo.

:: Create virtual environment
echo [3/5] Creating virtual environment...
cd /d "%install_path%"
python -m venv venv
echo [OK] Virtual environment created
echo.

:: Install packages
echo [4/5] Installing packages... (5-10 minutes)
call venv\Scripts\activate.bat
python -m pip install --upgrade pip
pip install numpy==1.26.4
pip install paddlepaddle paddleocr
pip install -r requirements.txt
echo [OK] Packages installed
echo.

:: Create shortcut
echo [5/5] Creating desktop shortcut...
echo @echo off > "%install_path%\run.bat"
echo cd /d "%install_path%" >> "%install_path%\run.bat"
echo call venv\Scripts\activate.bat >> "%install_path%\run.bat"
echo set QT_PLUGIN_PATH=%%~dp0venv\Lib\site-packages\PyQt5\Qt5\plugins >> "%install_path%\run.bat"
echo python main.py >> "%install_path%\run.bat"
echo pause >> "%install_path%\run.bat"

echo.
echo ============================================
echo    Installation Complete!
echo ============================================
echo.
echo Install location: %install_path%
echo Run file: %install_path%\run.bat
echo.
pause