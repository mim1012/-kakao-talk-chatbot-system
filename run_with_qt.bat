@echo off
chcp 65001 >nul
echo 카카오톡 OCR 챗봇 시스템 시작...
echo.

REM 가상환경 활성화
call new_venv\Scripts\activate

REM Python 경로 설정
set PYTHONPATH=%CD%\src;%PYTHONPATH%

REM Qt 플러그인 경로 설정
set QT_PLUGIN_PATH=%CD%\new_venv\Lib\site-packages\PyQt5\Qt5\plugins
set QT_QPA_PLATFORM_PLUGIN_PATH=%CD%\new_venv\Lib\site-packages\PyQt5\Qt5\plugins\platforms

echo Qt 플러그인 경로: %QT_PLUGIN_PATH%
echo Python 경로: %PYTHONPATH%
echo.

REM 애플리케이션 실행
python main.py

pause