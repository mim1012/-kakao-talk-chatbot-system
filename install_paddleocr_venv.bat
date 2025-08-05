@echo off
chcp 65001 > nul
echo ============================================================
echo 가상환경에 PaddleOCR 설치
echo ============================================================
echo.

REM 가상환경 활성화
if not exist venv (
    echo [오류] 가상환경이 없습니다!
    echo Python 3.11로 가상환경을 생성하세요:
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
echo [4] 기존 PaddleOCR 제거 (있다면)...
pip uninstall paddleocr paddlepaddle -y 2>nul

echo.
echo [5] PaddleOCR 설치 (Python 3.11 호환 버전)...
echo.

REM Python 3.11용 PaddleOCR 설치
echo Installing PaddlePaddle...
pip install paddlepaddle==2.5.2

echo.
echo Installing PaddleOCR...
pip install paddleocr==2.7.0.3

echo.
echo [6] 추가 의존성 설치...
pip install shapely
pip install pyclipper
pip install imgaug
pip install scikit-image
pip install lmdb
pip install tqdm
pip install visualdl

echo.
echo [7] 설치 확인...
echo.
python -c "import paddle; print(f'✅ PaddlePaddle {paddle.__version__} 설치됨')" 2>nul || echo ❌ PaddlePaddle 설치 실패
python -c "from paddleocr import PaddleOCR; print('✅ PaddleOCR 설치 및 import 성공')" 2>nul || echo ❌ PaddleOCR 설치 실패

echo.
echo [8] 간단한 테스트...
python -c "from paddleocr import PaddleOCR; ocr = PaddleOCR(lang='korean'); print('✅ PaddleOCR 초기화 성공')" 2>nul || echo ❌ PaddleOCR 초기화 실패

echo.
echo ============================================================
echo 설치 완료!
echo ============================================================
echo.
echo 프로그램 실행:
echo   python main.py
echo.
pause