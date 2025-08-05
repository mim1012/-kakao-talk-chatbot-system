@echo off
chcp 65001 > nul
echo ============================================================
echo Python 3.11 패키지 설치
echo ============================================================
echo.

REM 가상환경 확인
if not exist venv (
    echo ❌ 가상환경이 없습니다!
    echo.
    echo 먼저 setup_venv_py311.bat를 실행하세요.
    pause
    exit /b 1
)

echo [1] 가상환경 활성화 중...
call venv\Scripts\activate.bat

echo.
echo [2] Python 버전 확인...
python --version | findstr "3.11"
if %errorlevel% neq 0 (
    echo ❌ Python 3.11이 아닙니다!
    echo.
    echo setup_venv_py311.bat를 먼저 실행하세요.
    pause
    exit /b 1
)

echo.
echo [3] pip 업그레이드...
python -m pip install --upgrade pip

echo.
echo [4] 기본 패키지 설치 중...
echo.

REM numpy 설치 (OpenCV 의존성)
echo - numpy 설치 중...
pip install numpy==1.24.3

REM OpenCV 설치
echo - OpenCV 설치 중...
pip install opencv-python==4.8.1.78

REM PyQt5 설치
echo - PyQt5 설치 중...
pip install PyQt5==5.15.10

REM 스크린 캡처 도구
echo - 스크린 캡처 도구 설치 중...
pip install mss==9.0.1 pyautogui==0.9.54 pyperclip==1.8.2 screeninfo==0.8.1

REM PaddleOCR 설치
echo.
echo [5] PaddleOCR 설치 중 (시간이 걸릴 수 있습니다)...
pip install paddlepaddle==2.5.2
pip install paddleocr==2.7.0.3

REM 추가 유틸리티
echo.
echo [6] 추가 유틸리티 설치 중...
pip install pyyaml==6.0.1 requests==2.31.0 python-dotenv==1.0.0
pip install psutil==5.9.6 cachetools==5.3.2 colorlog==6.8.0

REM 개발 도구 (선택사항)
echo.
echo [7] 개발 도구 설치 중 (선택사항)...
pip install pytest==7.4.3 pytest-cov==4.1.0 pytest-mock==3.12.0

echo.
echo [8] 설치된 패키지 확인...
echo.
python -c "import numpy; print(f'✅ NumPy {numpy.__version__}')"
python -c "import cv2; print(f'✅ OpenCV {cv2.__version__}')"
python -c "import PyQt5.QtCore; print(f'✅ PyQt5 {PyQt5.QtCore.QT_VERSION_STR}')"
python -c "import paddle; print(f'✅ PaddlePaddle {paddle.__version__}')" 2>nul
python -c "import paddleocr; print('✅ PaddleOCR 설치됨')" 2>nul

echo.
echo ============================================================
echo ✅ Python 3.11 환경 설정 완료!
echo ============================================================
echo.
echo 프로그램 실행:
echo   python main.py
echo.
echo 또는 배치 파일 사용:
echo   start_chatbot_py311.bat
echo.
pause