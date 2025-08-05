@echo off
chcp 65001 > nul
echo ============================================================
echo PaddleOCR 필수 의존성 설치
echo ============================================================
echo.

REM 가상환경 활성화
call venv\Scripts\activate.bat

echo [1] 필수 의존성 설치 중...
echo.

REM 핵심 의존성
pip install shapely
pip install pyclipper
pip install opencv-python==4.6.0.66
pip install opencv-contrib-python==4.6.0.66
pip install Pillow
pip install numpy==1.24.3
pip install scipy
pip install scikit-image
pip install imgaug
pip install lmdb
pip install rapidfuzz
pip install attrdict
pip install beautifulsoup4
pip install lxml
pip install matplotlib
pip install tqdm
pip install premailer
pip install openpyxl
pip install python-docx --no-deps
pip install cssselect
pip install cssutils

echo.
echo [2] 설치 확인...
python test_paddle.py

echo.
echo ============================================================
echo 완료!
echo ============================================================
pause