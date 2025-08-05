@echo off
chcp 949 > nul
title KakaoTalk OCR Chatbot Quick Setup
color 0A

echo ============================================
echo    KakaoTalk OCR Chatbot Quick Setup
echo ============================================
echo.

:: Python check
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not installed!
    echo Please install Python 3.11 from:
    echo https://www.python.org/downloads/
    pause
    exit /b 1
)

echo [OK] Python detected
python --version
echo.

:: Create venv
echo Creating virtual environment...
if exist venv rmdir /s /q venv
python -m venv venv
echo [OK] Virtual environment created
echo.

:: Activate and install
echo Installing packages... (This may take 5-10 minutes)
call venv\Scripts\activate.bat

:: Upgrade pip
python -m pip install --upgrade pip

:: Install packages one by one
echo.
echo [1/5] Installing numpy...
pip install numpy==1.26.4

echo.
echo [2/5] Installing PaddlePaddle...
pip install paddlepaddle

echo.
echo [3/5] Installing PaddleOCR...
pip install paddleocr

echo.
echo [4/5] Installing PyQt5...
pip install PyQt5

echo.
echo [5/5] Installing other requirements...
pip install -r requirements.txt

:: Create run script
echo.
echo Creating run script...
echo @echo off > run_chatbot.bat
echo call venv\Scripts\activate.bat >> run_chatbot.bat
echo set QT_PLUGIN_PATH=%%~dp0venv\Lib\site-packages\PyQt5\Qt5\plugins >> run_chatbot.bat
echo python main.py >> run_chatbot.bat
echo pause >> run_chatbot.bat

echo.
echo ============================================
echo    Setup Complete!
echo ============================================
echo.
echo To run the chatbot:
echo   1. Double-click run_chatbot.bat
echo   2. Or run: venv\Scripts\python.exe main.py
echo.
pause