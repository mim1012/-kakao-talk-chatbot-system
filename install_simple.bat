@echo off
echo ============================================
echo    KakaoTalk OCR Chatbot Setup
echo ============================================
echo.

:: Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found!
    echo Please install Python 3.11 first.
    pause
    exit
)

echo [OK] Python found
echo.

:: Install directly without venv
echo Installing packages...
echo.

echo [1/6] Upgrading pip...
python -m pip install --upgrade pip

echo.
echo [2/6] Installing numpy...
pip install numpy==1.26.4

echo.
echo [3/6] Installing PaddlePaddle...
pip install paddlepaddle

echo.
echo [4/6] Installing PaddleOCR...
pip install paddleocr

echo.
echo [5/6] Installing PyQt5...
pip install PyQt5

echo.
echo [6/6] Installing other packages...
pip install pyautogui mss screeninfo pyperclip psutil

:: Create run script
echo.
echo Creating run script...
echo @echo off > run.bat
echo python main.py >> run.bat
echo pause >> run.bat

echo.
echo ============================================
echo    Installation Complete!
echo ============================================
echo.
echo To run: Double-click run.bat
echo.
pause