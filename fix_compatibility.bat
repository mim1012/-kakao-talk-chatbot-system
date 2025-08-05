@echo off
chcp 65001 > nul
echo ============================================================
echo NumPy/SciPy 호환성 문제 해결
echo ============================================================
echo.

REM 가상환경 활성화
call venv\Scripts\activate.bat

echo [1] 기존 패키지 제거...
pip uninstall numpy scipy scikit-image -y

echo.
echo [2] 호환되는 버전 설치...
echo.

REM NumPy 1.26.0과 SciPy 1.11.4는 Python 3.11과 호환
pip install numpy==1.26.0
pip install scipy==1.11.4
pip install scikit-image==0.22.0

echo.
echo [3] OpenCV 재설치...
pip uninstall opencv-python opencv-contrib-python -y
pip install opencv-python==4.8.1.78
pip install opencv-contrib-python==4.8.1.78

echo.
echo [4] 테스트...
python -c "import numpy; print(f'NumPy {numpy.__version__}')"
python -c "import scipy; print(f'SciPy {scipy.__version__}')"
python -c "import cv2; print(f'OpenCV {cv2.__version__}')"

echo.
echo [5] PaddleOCR 테스트...
python -c "from paddleocr import PaddleOCR; print('PaddleOCR import 성공!')"

echo.
echo ============================================================
echo 완료!
echo ============================================================
pause