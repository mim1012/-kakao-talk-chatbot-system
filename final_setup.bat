@echo off
chcp 65001 > nul
echo ============================================================
echo 최종 설정 및 테스트
echo ============================================================
echo.

REM 가상환경 활성화
call venv\Scripts\activate.bat

echo [1] NumPy 버전 확인...
python -c "import numpy; print(f'NumPy: {numpy.__version__}')"

echo.
echo [2] SciPy 설치/업데이트...
pip install scipy==1.11.4 --force-reinstall

echo.
echo [3] scikit-image 설치/업데이트...
pip install scikit-image==0.22.0 --force-reinstall

echo.
echo [4] OpenCV headless 설치 (pdf2docx용)...
pip install opencv-python-headless==4.8.1.78

echo.
echo [5] PaddleOCR 테스트...
python test_paddle_final.py

echo.
echo ============================================================
echo 설정 완료!
echo ============================================================
pause