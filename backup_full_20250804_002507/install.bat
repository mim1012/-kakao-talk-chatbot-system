@echo off
chcp 65001 >nul
echo ========================================
echo 카카오톡 챗봇 시스템 설치 스크립트
echo ========================================

echo Python 버전 확인 중...
python --version
if errorlevel 1 (
    echo Python이 설치되어 있지 않습니다.
    echo Python 3.11 이상을 설치해주세요.
    pause
    exit /b 1
)

echo.
echo 가상환경 생성 중...
python -m venv chatbot_env
if errorlevel 1 (
    echo 가상환경 생성에 실패했습니다.
    pause
    exit /b 1
)

echo.
echo 가상환경 활성화 중...
call chatbot_env\Scripts\activate.bat
if errorlevel 1 (
    echo 가상환경 활성화에 실패했습니다.
    pause
    exit /b 1
)

echo.
echo pip 업그레이드 중...
python -m pip install --upgrade pip

echo.
echo 필수 패키지 설치 중...
pip install -r requirements.txt
if errorlevel 1 (
    echo 패키지 설치에 실패했습니다.
    echo requirements_safe.txt를 사용해보세요.
    pip install -r requirements_safe.txt
)

echo.
echo 설치 완료!
echo 실행하려면: python main.py
echo.
pause 