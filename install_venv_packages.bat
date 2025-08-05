@echo off
chcp 65001 > nul
echo ============================================================
echo 가상환경 패키지 설치
echo ============================================================
echo.

REM 가상환경 활성화
if not exist venv (
    echo [오류] 가상환경이 없습니다!
    echo 먼저 Python 3.11로 가상환경을 생성하세요:
    echo   python -m venv venv
    pause
    exit /b 1
)

echo [1] 가상환경 활성화 중...
call venv\Scripts\activate.bat

echo.
echo [2] Python 버전 확인...
python --version

echo.
echo [3] pip 업그레이드...
python -m pip install --upgrade pip

echo.
echo [4] 필수 패키지 설치...
echo.

REM numpy와 OpenCV (PaddleOCR 의존성)
echo Installing numpy...
pip install numpy==1.24.3

echo Installing OpenCV...
pip install opencv-python==4.6.0.66

REM PyQt5
echo Installing PyQt5...
pip install PyQt5==5.15.10

REM 스크린 캡처 및 자동화
echo Installing screen capture tools...
pip install mss==9.0.1
pip install pyautogui==0.9.54
pip install pyperclip==1.8.2
pip install screeninfo==0.8.1

REM PaddleOCR (Python 3.11 호환 버전)
echo.
echo [5] PaddleOCR 설치 중...
pip install paddlepaddle==2.5.2
pip install paddleocr==2.7.0.3

REM 추가 유틸리티
echo.
echo [6] 추가 패키지 설치...
pip install Pillow==10.1.0
pip install pyyaml==6.0.1
pip install requests==2.31.0
pip install psutil==5.9.6
pip install colorlog==6.8.0

echo.
echo [7] 설치 확인...
python -c "import numpy; print(f'✅ NumPy {numpy.__version__}')"
python -c "import cv2; print(f'✅ OpenCV {cv2.__version__}')"
python -c "import PyQt5.QtCore; print(f'✅ PyQt5 installed')"
python -c "import paddle; print(f'✅ PaddlePaddle {paddle.__version__}')" 2>nul || echo ⚠️ PaddlePaddle 설치 확인 필요
python -c "import paddleocr; print(f'✅ PaddleOCR installed')" 2>nul || echo ⚠️ PaddleOCR 설치 확인 필요

echo.
echo ============================================================
echo ✅ 패키지 설치 완료!
echo ============================================================
echo.
echo 프로그램 실행:
echo   run_chatbot.bat
echo.
pause