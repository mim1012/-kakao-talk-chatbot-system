@echo off
chcp 65001 > nul
echo ============================================================
echo PaddleOCR GitHub에서 직접 설치
echo ============================================================
echo.

REM 가상환경 활성화
call venv\Scripts\activate.bat

echo [1] 기존 PaddleOCR 제거...
pip uninstall paddleocr -y

echo.
echo [2] GitHub에서 PaddleOCR 다운로드 및 설치...
pip install git+https://github.com/PaddlePaddle/PaddleOCR.git@release/2.7

echo.
echo 대안: 안정 버전 설치
echo [3] 특정 버전 설치 시도...
pip install "paddleocr>=2.0.1" --no-deps
pip install shapely scikit-image imgaug pyclipper lmdb attrdict Pillow beautifulsoup4 rapidfuzz

echo.
echo [4] 테스트...
python -c "from paddleocr import PaddleOCR; print('PaddleOCR 설치 성공!')"

echo.
pause