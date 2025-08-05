@echo off
echo ============================================
echo    Manual Installation Guide
echo ============================================
echo.

echo If automatic installation fails, follow these steps:
echo.
echo 1. Open Command Prompt (cmd)
echo 2. Navigate to this folder
echo 3. Run these commands one by one:
echo.
echo    pip install numpy==1.26.4
echo    pip install paddlepaddle
echo    pip install paddleocr
echo    pip install PyQt5
echo    pip install pyautogui mss screeninfo pyperclip psutil
echo.
echo 4. Run: python main.py
echo.
echo Press any key to try automatic installation...
pause > nul

:: Try simple installation
pip install numpy==1.26.4
pip install paddlepaddle paddleocr
pip install PyQt5 pyautogui mss screeninfo pyperclip psutil

echo.
echo Installation complete! Run with: python main.py
pause