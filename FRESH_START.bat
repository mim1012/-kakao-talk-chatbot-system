@echo off
chcp 65001 > nul
echo ============================================================
echo 가상환경 완전 재설정 및 PaddleOCR 설치
echo ============================================================
echo.

echo [1] 기존 가상환경 삭제 중...
if exist venv (
    rmdir /s /q venv
    echo    기존 가상환경 삭제 완료
)

echo.
echo [2] Python 3.11로 새 가상환경 생성...
echo.

REM Python 3.11 찾기
set PYTHON_CMD=

REM py launcher로 3.11 찾기
py -3.11 --version >nul 2>&1
if %errorlevel% == 0 (
    set PYTHON_CMD=py -3.11
    goto :create_venv
)

REM 일반 경로에서 찾기
if exist "C:\Python311\python.exe" (
    set PYTHON_CMD=C:\Python311\python.exe
    goto :create_venv
)

if exist "%LOCALAPPDATA%\Programs\Python\Python311\python.exe" (
    set PYTHON_CMD="%LOCALAPPDATA%\Programs\Python\Python311\python.exe"
    goto :create_venv
)

REM Python 3.11을 찾지 못함
echo ❌ Python 3.11을 찾을 수 없습니다!
echo    https://www.python.org/downloads/release/python-3119/ 에서 설치하세요.
pause
exit /b 1

:create_venv
echo Python 3.11 찾음!
%PYTHON_CMD% -m venv venv
echo ✅ 가상환경 생성 완료

echo.
echo [3] 가상환경 활성화...
call venv\Scripts\activate.bat

echo.
echo [4] pip 업그레이드...
python -m pip install --upgrade pip

echo.
echo [5] 필수 패키지 설치 시작...
echo.

echo    기본 패키지 설치 중...
pip install numpy==1.26.0
pip install scipy==1.11.4
pip install scikit-image==0.22.0

echo.
echo    OpenCV 설치 중...
pip install opencv-python==4.8.1.78
pip install opencv-contrib-python==4.8.1.78

echo.
echo    PyQt5 설치 중...
pip install PyQt5==5.15.10

echo.
echo    스크린 캡처 도구 설치 중...
pip install mss==9.0.1
pip install pyautogui==0.9.54
pip install pyperclip==1.8.2
pip install screeninfo==0.8.1

echo.
echo [6] PaddlePaddle 설치 중...
pip install paddlepaddle==2.5.2

echo.
echo [7] PaddleOCR 의존성 설치 중...
pip install shapely pyclipper imgaug lmdb attrdict
pip install beautifulsoup4 rapidfuzz lxml tqdm Pillow
pip install matplotlib premailer openpyxl fonttools fire
pip install python-docx --no-deps
pip install pdf2docx --no-deps

echo.
echo [8] PaddleOCR 설치 중...
pip install paddleocr==2.7.0.3 --no-deps

echo.
echo [9] 추가 유틸리티...
pip install psutil colorlog pyyaml requests

echo.
echo ============================================================
echo 설치 완료! 테스트 중...
echo ============================================================
echo.

python test_fresh_install.py

echo.
pause