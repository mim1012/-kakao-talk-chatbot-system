@echo off
chcp 65001 > nul
title 카카오톡 OCR 챗봇 시스템

echo ================================================================
echo                   카카오톡 OCR 챗봇 시스템
echo ================================================================
echo.
echo 원격 PC 자동 실행 모드
echo.

REM 현재 디렉토리를 프로젝트 루트로 설정
cd /d "%~dp0"

REM 가상환경 확인 및 활성화
if exist "venv\Scripts\activate.bat" (
    echo [INFO] 가상환경 활성화 중...
    call venv\Scripts\activate.bat
) else if exist ".venv\Scripts\activate.bat" (
    echo [INFO] 가상환경 활성화 중...
    call .venv\Scripts\activate.bat
) else (
    echo [WARN] 가상환경을 찾을 수 없습니다. 전역 Python을 사용합니다.
)

REM Python 및 필수 모듈 확인
python --version > nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python이 설치되지 않았거나 PATH에 없습니다.
    echo [SOLUTION] Python 3.11+ 설치 후 다시 시도하세요.
    pause
    exit /b 1
)

echo [INFO] Python 버전 확인:
python --version

REM 필수 패키지 설치 확인
echo [INFO] 필수 패키지 확인 중...
python -c "import paddleocr, PyQt5, numpy, cv2, PIL, mss, pyautogui" 2>nul
if errorlevel 1 (
    echo [WARN] 일부 필수 패키지가 누락되었습니다.
    echo [INFO] 자동 설치를 시도합니다...
    pip install -r requirements.txt
    if errorlevel 1 (
        echo [ERROR] 패키지 설치에 실패했습니다.
        pause
        exit /b 1
    )
)

REM 원격 데스크톱 환경 확인
echo [INFO] 실행 환경 확인 중...
if defined SESSIONNAME (
    if "%SESSIONNAME:~0,4%"=="RDP-" (
        echo [REMOTE] 원격 데스크톱 환경이 감지되었습니다.
        echo [REMOTE] 원격 데스크톱에 최적화된 설정을 사용합니다.
        set REMOTE_MODE=1
    )
)

REM 디버그 폴더 생성
if not exist "debug" mkdir debug
if not exist "debug_screenshots" mkdir debug_screenshots
if not exist "logs" mkdir logs

REM 로그 파일 설정
set LOG_FILE=logs\chatbot_%date:~0,4%%date:~5,2%%date:~8,2%_%time:~0,2%%time:~3,2%%time:~6,2%.log
set LOG_FILE=%LOG_FILE: =0%

echo [INFO] 로그 파일: %LOG_FILE%
echo.

REM 시스템 요구사항 확인
echo [CHECK] 시스템 요구사항 확인:
echo - OS: Windows %OS%
echo - 아키텍처: %PROCESSOR_ARCHITECTURE%
if defined REMOTE_MODE (
    echo - 실행 모드: 원격 데스크톱
) else (
    echo - 실행 모드: 로컬
)
echo.

REM 자동 실행 옵션
set /p AUTO_START="자동으로 모니터링을 시작하시겠습니까? (Y/N, 기본값: Y): "
if "%AUTO_START%"=="" set AUTO_START=Y
if /i "%AUTO_START%"=="Y" (
    set AUTO_START_FLAG=--auto-start
) else (
    set AUTO_START_FLAG=
)

echo.
echo [START] 카카오톡 OCR 챗봇 시작 중...
echo ================================================================
echo.

REM 메인 애플리케이션 실행 (로그 파일에 출력 기록)
python main.py %AUTO_START_FLAG% 2>&1 | tee "%LOG_FILE%"

REM 종료 처리
echo.
echo ================================================================
echo [END] 프로그램이 종료되었습니다.
echo [LOG] 로그가 저장되었습니다: %LOG_FILE%
echo.

REM 원격 환경에서는 자동으로 종료하지 않음
if defined REMOTE_MODE (
    echo [REMOTE] 원격 세션에서 실행 중입니다.
    echo [REMOTE] 연결을 유지하려면 아무 키나 누르세요...
    pause
) else (
    echo 종료하려면 아무 키나 누르세요...
    pause
)