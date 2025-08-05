@echo off
chcp 65001 > nul
echo ============================================================
echo NumPy 강제 업데이트
echo ============================================================
echo.

REM 가상환경 활성화
call venv\Scripts\activate.bat

echo [1] NumPy 완전 제거...
pip uninstall numpy -y
pip uninstall numpy -y

echo.
echo [2] 캐시 삭제...
pip cache purge

echo.
echo [3] NumPy 1.26.0 설치 (Python 3.11 호환)...
pip install numpy==1.26.0 --force-reinstall --no-cache-dir

echo.
echo [4] 확인...
python -c "import numpy; print(f'NumPy 버전: {numpy.__version__}')"

echo.
echo [5] SciPy 재설치...
pip uninstall scipy -y
pip install scipy==1.11.4

echo.
echo [6] scikit-image 재설치...
pip uninstall scikit-image -y
pip install scikit-image==0.22.0

echo.
echo [7] 최종 테스트...
python -c "import numpy; print(f'NumPy: {numpy.__version__}')"
python -c "import scipy; print(f'SciPy: {scipy.__version__}')"
python -c "from paddleocr import PaddleOCR; print('PaddleOCR OK!')"

echo.
pause