@echo off
chcp 65001 > nul
echo ============================================================
echo Python 3.11 가상환경 설정
echo ============================================================
echo.

REM Python 3.11 찾기
echo [1] Python 3.11 찾는 중...

REM 방법 1: py launcher 사용
py -3.11 --version >nul 2>&1
if %errorlevel% == 0 (
    echo ✅ Python 3.11을 찾았습니다 (py launcher)
    set PYTHON_CMD=py -3.11
    goto :found
)

REM 방법 2: 일반적인 설치 경로
if exist "C:\Python311\python.exe" (
    echo ✅ Python 3.11을 찾았습니다 (C:\Python311)
    set PYTHON_CMD=C:\Python311\python.exe
    goto :found
)

REM 방법 3: Program Files 경로
if exist "C:\Program Files\Python311\python.exe" (
    echo ✅ Python 3.11을 찾았습니다 (Program Files)
    set PYTHON_CMD="C:\Program Files\Python311\python.exe"
    goto :found
)

REM 방법 4: 사용자 경로
if exist "%LOCALAPPDATA%\Programs\Python\Python311\python.exe" (
    echo ✅ Python 3.11을 찾았습니다 (User)
    set PYTHON_CMD="%LOCALAPPDATA%\Programs\Python\Python311\python.exe"
    goto :found
)

REM Python 3.11을 찾지 못함
echo.
echo ❌ Python 3.11을 찾을 수 없습니다!
echo.
echo Python 3.11을 설치하세요:
echo 1. https://www.python.org/downloads/release/python-3119/ 접속
echo 2. Windows installer (64-bit) 다운로드
echo 3. 설치시 "Add Python to PATH" 체크
echo.
pause
exit /b 1

:found
echo.
echo [2] 기존 가상환경 제거 중...
if exist venv (
    rmdir /s /q venv
    echo ✅ 기존 가상환경 제거 완료
)

echo.
echo [3] Python 3.11로 새 가상환경 생성 중...
%PYTHON_CMD% -m venv venv
if %errorlevel% neq 0 (
    echo ❌ 가상환경 생성 실패
    pause
    exit /b 1
)
echo ✅ 가상환경 생성 완료

echo.
echo [4] 가상환경 활성화 중...
call venv\Scripts\activate.bat

echo.
echo [5] pip 업그레이드 중...
python -m pip install --upgrade pip --quiet

echo.
echo [6] Python 버전 확인...
python --version

echo.
echo ============================================================
echo ✅ Python 3.11 가상환경 설정 완료!
echo ============================================================
echo.
echo 다음 명령어로 패키지를 설치하세요:
echo   pip install -r requirements_py311.txt
echo.
echo 또는 자동 설치:
echo   install_py311.bat
echo.
pause