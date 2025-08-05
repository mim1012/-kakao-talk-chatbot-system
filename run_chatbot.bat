@echo off
chcp 65001 > nul
echo ============================================================
echo 카카오톡 OCR 챗봇 시스템 실행
echo ============================================================
echo.

REM 가상환경 확인 및 활성화
if exist venv\Scripts\activate.bat (
    echo [정보] 가상환경 활성화 중...
    call venv\Scripts\activate.bat
) else (
    echo [정보] 가상환경 없음, 시스템 Python 사용
)

REM Python 버전 확인
echo [정보] Python 버전:
python --version

REM 환경변수 설정
set PYTHONIOENCODING=utf-8
set PYTHONLEGACYWINDOWSSTDIO=utf-8

REM PaddleOCR 로그 차단
set PPOCR_LOG_LEVEL=ERROR
set PADDLEX_LOG_LEVEL=ERROR
set PADDLE_LOG_LEVEL=ERROR
set GLOG_minloglevel=3

echo.
echo [정보] 프로그램을 시작합니다...
echo.

REM 메인 프로그램 실행
python main.py

if errorlevel 1 (
    echo.
    echo [오류] 프로그램 실행 중 오류가 발생했습니다.
    pause
)