@echo off
chcp 65001 > nul
title 원격 PC 카카오톡 챗봇 - 빠른 시작

echo ================================================================
echo              원격 PC 카카오톡 챗봇 - 빠른 시작
echo ================================================================
echo.

REM 현재 디렉토리를 프로젝트 루트로 설정
cd /d "%~dp0"

REM 원격 환경 감지
set REMOTE_DETECTED=0
if defined SESSIONNAME (
    if "%SESSIONNAME:~0,4%"=="RDP-" (
        set REMOTE_DETECTED=1
        echo [REMOTE] 원격 데스크톱 환경 감지됨
    )
)

if defined CLIENTNAME (
    set REMOTE_DETECTED=1
    echo [REMOTE] 원격 클라이언트: %CLIENTNAME%
)

if %REMOTE_DETECTED%==0 (
    echo [LOCAL] 로컬 환경에서 실행 중
)
echo.

REM 자동 설정
echo [AUTO] 원격 PC 최적화 설정 적용...
set PYTHONUNBUFFERED=1
set PYTHONIOENCODING=utf-8
set QT_AUTO_SCREEN_SCALE_FACTOR=1
set QT_SCALE_FACTOR=1

REM 가상환경 확인
if exist "venv\Scripts\python.exe" (
    echo [ENV] 가상환경 사용
    set PYTHON_CMD=venv\Scripts\python.exe
) else (
    echo [ENV] 전역 Python 사용
    set PYTHON_CMD=python
)

REM 빠른 헬스체크
echo [CHECK] 시스템 상태 확인...
%PYTHON_CMD% -c "import sys; print(f'Python {sys.version}')" 2>nul
if errorlevel 1 (
    echo [ERROR] Python을 찾을 수 없습니다.
    echo [HELP] 'install_and_run.bat'을 먼저 실행하세요.
    pause
    exit /b 1
)

REM 필수 모듈 빠른 체크
%PYTHON_CMD% -c "import paddleocr, PyQt5" 2>nul
if errorlevel 1 (
    echo [WARN] 일부 모듈이 누락되었을 수 있습니다.
    echo [AUTO] 빠른 설치를 시도합니다...
    pip install paddleocr PyQt5 numpy opencv-python pillow mss pyautogui
)

echo [OK] 시스템 준비 완료
echo.

REM 로그 설정
set TIMESTAMP=%date:~0,4%%date:~5,2%%date:~8,2%_%time:~0,2%%time:~3,2%%time:~6,2%
set TIMESTAMP=%TIMESTAMP: =0%
if not exist "logs" mkdir logs
set LOG_FILE=logs\remote_session_%TIMESTAMP%.log

echo [LOG] 세션 로그: %LOG_FILE%
echo.

REM 원격 최적화 메시지
if %REMOTE_DETECTED%==1 (
    echo [REMOTE] 원격 데스크톱 최적화 기능:
    echo - 자동 화면 해상도 감지
    echo - 원격 입력 최적화
    echo - 네트워크 지연 보상
    echo - 세션 연결 유지
    echo.
)

echo [INFO] 카카오톡을 열고 대상 채팅방을 준비하세요.
echo [INFO] 챗봇이 시작되면 GUI에서 모니터링 시작 버튼을 클릭하세요.
echo.

set /p READY="준비가 되셨습니까? (Enter를 누르면 시작): "

echo.
echo [START] 카카오톡 OCR 챗봇 시작...
echo ================================================================
echo.

REM 메인 애플리케이션 실행 (원격 최적화 플래그 포함)
if %REMOTE_DETECTED%==1 (
    %PYTHON_CMD% main.py --remote-mode 2>&1 | tee "%LOG_FILE%"
) else (
    %PYTHON_CMD% main.py 2>&1 | tee "%LOG_FILE%"
)

echo.
echo ================================================================
echo [END] 원격 세션 종료
echo [LOG] 로그 저장됨: %LOG_FILE%
echo.

if %REMOTE_DETECTED%==1 (
    echo [REMOTE] 원격 연결을 유지하려면 창을 열어두세요.
    echo [REMOTE] 연결을 끊으려면 아무 키나 누르세요...
) else (
    echo 종료하려면 아무 키나 누르세요...
)
pause