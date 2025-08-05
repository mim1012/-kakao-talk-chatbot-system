@echo off
chcp 65001 > nul
echo ============================================================
echo NumPy 버전 충돌 해결
echo ============================================================
echo.

REM 가상환경 활성화
call venv\Scripts\activate.bat

echo [1] 현재 NumPy 제거...
pip uninstall numpy -y

echo.
echo [2] NumPy 1.24.3 재설치 (Python 3.11 호환)...
pip install numpy==1.24.3

echo.
echo [3] OpenCV 재설치...
pip uninstall opencv-python opencv-contrib-python -y
pip install opencv-python==4.6.0.66
pip install opencv-contrib-python==4.6.0.66

echo.
echo [4] 테스트...
python -c "import numpy; print(f'NumPy {numpy.__version__} OK')"
python -c "import cv2; print(f'OpenCV {cv2.__version__} OK')"
python -c "from paddleocr import PaddleOCR; print('PaddleOCR import OK')"

echo.
echo ============================================================
echo 완료!
echo ============================================================
pause