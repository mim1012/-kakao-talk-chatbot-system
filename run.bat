@echo off
chcp 65001 >nul
echo ========================================
echo 카카오톡 챗봇 시스템 실행
echo ========================================

echo 가상환경 활성화 중...
call chatbot_env\Scripts\activate.bat
if errorlevel 1 (
    echo 가상환경을 찾을 수 없습니다.
    echo 먼저 install.bat을 실행해주세요.
    pause
    exit /b 1
)

echo.
echo 챗봇 시스템 실행 중...
python main.py

pause 