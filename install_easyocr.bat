@echo off
chcp 65001 > nul
echo ============================================================
echo EasyOCR 설치 (PaddleOCR 대체)
echo ============================================================
echo.

REM 가상환경 활성화
call venv\Scripts\activate.bat

echo [1] PaddleOCR 관련 패키지 제거...
pip uninstall paddleocr paddlepaddle -y

echo.
echo [2] EasyOCR 설치...
pip install easyocr

echo.
echo [3] 추가 의존성...
pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu

echo.
echo [4] 테스트...
python test_easyocr.py

echo.
echo ============================================================
echo EasyOCR 설치 완료!
echo ============================================================
pause