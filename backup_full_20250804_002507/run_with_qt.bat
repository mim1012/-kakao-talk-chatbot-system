@echo off
echo Starting KakaoTalk OCR Chatbot System...
echo.

REM Activate virtual environment
call new_venv\Scripts\activate

REM Set Qt plugin path
set QT_PLUGIN_PATH=%CD%\new_venv\Lib\site-packages\PyQt5\Qt5\plugins
set QT_QPA_PLATFORM_PLUGIN_PATH=%CD%\new_venv\Lib\site-packages\PyQt5\Qt5\plugins\platforms

echo Qt Plugin Path: %QT_PLUGIN_PATH%
echo.

REM Run the application
python main.py

pause