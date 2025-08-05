@echo off
chcp 65001 > nul
echo ============================================================
echo PaddleOCR 설치 (PyMuPDF 제외)
echo ============================================================
echo.

REM 가상환경 활성화
call venv\Scripts\activate.bat

echo [1] 기존 패키지 제거...
pip uninstall paddleocr paddlepaddle -y 2>nul

echo.
echo [2] PaddlePaddle 설치...
pip install paddlepaddle==2.5.2

echo.
echo [3] PaddleOCR 의존성 수동 설치 (PyMuPDF 제외)...
pip install opencv-python==4.6.0.66
pip install opencv-contrib-python==4.6.0.66
pip install shapely
pip install pyclipper  
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
pip install python-docx
pip install pdf2docx --no-deps
pip install openpyxl
pip install rarfile

echo.
echo [4] PaddleOCR 설치 (의존성 무시)...
pip install paddleocr==2.7.0.3 --no-deps

echo.
echo [5] 설치 확인...
python test_paddle.py

echo.
echo ============================================================
echo 설치 완료!
echo ============================================================
pause