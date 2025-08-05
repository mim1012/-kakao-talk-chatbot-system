@echo off
echo ================================================
echo 카카오톡 OCR 챗봇 - Python 3.11 실행
echo ================================================
echo.

REM Python 3.11 경로 확인
set PYTHON311=C:\Users\PC_1M\AppData\Local\Programs\Python\Python311\python.exe

if not exist "%PYTHON311%" (
    echo ❌ Python 3.11이 설치되지 않았습니다!
    echo    설치 경로: %PYTHON311%
    pause
    exit /b 1
)

echo ✅ Python 3.11 발견: %PYTHON311%

REM 현재 디렉토리로 이동
cd /d "D:\Project\카카오톡 챗봇 시스템"

REM Python 버전 확인
echo.
echo Python 버전:
"%PYTHON311%" --version

REM 필요한 패키지 설치 확인
echo.
echo 패키지 확인 중...
"%PYTHON311%" -m pip list | findstr /i "paddlepaddle paddleocr numpy opencv"

REM 프로그램 실행
echo.
echo ================================================
echo 프로그램 시작...
echo ================================================
echo.

"%PYTHON311%" main.py

pause