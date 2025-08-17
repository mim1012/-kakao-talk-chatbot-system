@echo off
chcp 65001 > nul
title 카카오톡 OCR 챗봇 - 설치 및 실행

echo ================================================================
echo            카카오톡 OCR 챗봇 시스템 - 자동 설치
echo ================================================================
echo.
echo 원격 PC 첫 실행용 스크립트
echo.

REM 현재 디렉토리를 프로젝트 루트로 설정
cd /d "%~dp0"

REM 관리자 권한 확인
net session >nul 2>&1
if errorlevel 1 (
    echo [WARN] 관리자 권한으로 실행하는 것을 권장합니다.
    echo [INFO] 일부 기능이 제한될 수 있습니다.
    echo.
)

REM Python 설치 확인
echo [STEP 1] Python 설치 확인...
python --version > nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python이 설치되지 않았습니다.
    echo.
    echo [SOLUTION] 다음 단계를 수행하세요:
    echo 1. Python 3.11+ 다운로드: https://www.python.org/downloads/
    echo 2. 설치 시 "Add Python to PATH" 옵션 체크
    echo 3. 설치 완료 후 이 스크립트를 다시 실행
    echo.
    pause
    exit /b 1
)

python --version
echo [OK] Python이 설치되어 있습니다.
echo.

REM 가상환경 생성 (선택사항)
set /p CREATE_VENV="가상환경을 생성하시겠습니까? (권장) (Y/N, 기본값: Y): "
if "%CREATE_VENV%"=="" set CREATE_VENV=Y
if /i "%CREATE_VENV%"=="Y" (
    echo [STEP 2] 가상환경 생성 중...
    if not exist "venv" (
        python -m venv venv
        if errorlevel 1 (
            echo [ERROR] 가상환경 생성에 실패했습니다.
            echo [INFO] 전역 Python 환경을 사용합니다.
        ) else (
            echo [OK] 가상환경이 생성되었습니다.
            call venv\Scripts\activate.bat
            echo [OK] 가상환경이 활성화되었습니다.
        )
    ) else (
        echo [INFO] 기존 가상환경을 사용합니다.
        call venv\Scripts\activate.bat
    )
) else (
    echo [SKIP] 가상환경을 건너뜁니다.
)
echo.

REM 필수 패키지 설치
echo [STEP 3] 필수 패키지 설치...
if exist "requirements.txt" (
    echo [INFO] requirements.txt에서 패키지를 설치합니다...
    pip install --upgrade pip
    pip install -r requirements.txt
    if errorlevel 1 (
        echo [WARN] 일부 패키지 설치에 실패했을 수 있습니다.
        echo [INFO] 개별 설치를 시도합니다...
        pip install paddleocr PyQt5 numpy opencv-python pillow mss pyautogui
    )
) else (
    echo [INFO] 기본 패키지를 설치합니다...
    pip install --upgrade pip
    pip install paddleocr PyQt5 numpy opencv-python pillow mss pyautogui
)
echo.

REM 폰트 설치 확인 (한글 지원)
echo [STEP 4] 한글 폰트 확인...
if exist "C:\Windows\Fonts\malgun.ttf" (
    echo [OK] 맑은 고딕 폰트가 설치되어 있습니다.
) else (
    echo [WARN] 한글 폰트가 없을 수 있습니다.
    echo [INFO] OCR 한글 인식에 영향을 줄 수 있습니다.
)
echo.

REM 디렉토리 구조 확인
echo [STEP 5] 프로젝트 구조 확인...
set REQUIRED_DIRS=src config debug logs debug_screenshots cache
for %%d in (%REQUIRED_DIRS%) do (
    if not exist "%%d" (
        mkdir "%%d"
        echo [CREATE] %%d 폴더가 생성되었습니다.
    )
)
echo.

REM 설정 파일 확인
echo [STEP 6] 설정 파일 확인...
if not exist "config.json" (
    echo [WARN] config.json 파일이 없습니다.
    echo [INFO] 기본 설정 파일을 생성합니다...
    
    echo {> config.json
    echo   "grid_rows": 3,>> config.json
    echo   "grid_cols": 5,>> config.json
    echo   "ocr_interval_sec": 0.5,>> config.json
    echo   "fast_ocr_mode": true,>> config.json
    echo   "cooldown_sec": 5,>> config.json
    echo   "trigger_patterns": ["들어왔습니다"],>> config.json
    echo   "response_message": "어서와요👋 환영합니다!",>> config.json
    echo   "use_gpu": false,>> config.json
    echo   "monitor_mode": "all">> config.json
    echo }>> config.json
    
    echo [OK] 기본 config.json이 생성되었습니다.
) else (
    echo [OK] config.json 파일이 존재합니다.
)
echo.

REM 원격 데스크톱 설정 확인
if defined SESSIONNAME (
    if "%SESSIONNAME:~0,4%"=="RDP-" (
        echo [REMOTE] 원격 데스크톱 환경이 감지되었습니다.
        echo [INFO] 원격 데스크톱 최적화 설정이 적용됩니다.
        echo.
    )
)

REM 테스트 실행
echo [STEP 7] 시스템 테스트...
echo [INFO] 간단한 모듈 테스트를 실행합니다...
python -c "
try:
    import paddleocr
    import PyQt5
    import numpy
    import cv2
    import PIL
    import mss
    import pyautogui
    print('[OK] 모든 필수 모듈이 정상적으로 로드되었습니다.')
except ImportError as e:
    print(f'[ERROR] 모듈 로드 실패: {e}')
    exit(1)
"

if errorlevel 1 (
    echo [ERROR] 모듈 테스트에 실패했습니다.
    echo [SOLUTION] 패키지 설치를 다시 확인하세요.
    pause
    exit /b 1
)
echo.

echo ================================================================
echo                        설치 완료!
echo ================================================================
echo.
echo [SUCCESS] 카카오톡 OCR 챗봇 시스템이 준비되었습니다.
echo.
echo [NEXT] 다음 단계:
echo 1. 카카오톡을 실행하고 대상 채팅방을 엽니다
echo 2. 'run_chatbot.bat'을 실행하여 챗봇을 시작합니다
echo.

set /p RUN_NOW="지금 바로 챗봇을 실행하시겠습니까? (Y/N, 기본값: Y): "
if "%RUN_NOW%"=="" set RUN_NOW=Y
if /i "%RUN_NOW%"=="Y" (
    echo.
    echo [START] 챗봇을 시작합니다...
    call run_chatbot.bat
) else (
    echo.
    echo [INFO] 준비가 되면 'run_chatbot.bat'을 실행하세요.
    pause
)