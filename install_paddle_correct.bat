@echo off
chcp 65001 > nul
echo ============================================================
echo PaddleOCR 올바른 설치
echo ============================================================
echo.

REM 가상환경 활성화
call venv\Scripts\activate.bat

echo [1] 모든 OCR 관련 패키지 제거...
pip uninstall paddleocr paddlepaddle scipy scikit-image -y

echo.
echo [2] NumPy 정리...
pip uninstall numpy -y
pip install numpy==1.26.0

echo.
echo [3] SciPy 설치...
pip install scipy==1.11.4

echo.
echo [4] PaddlePaddle CPU 버전 설치...
pip install paddlepaddle==2.5.2 -i https://pypi.tuna.tsinghua.edu.cn/simple

echo.
echo [5] scikit-image 설치...
pip install scikit-image==0.22.0

echo.
echo [6] PaddleOCR 의존성 수동 설치...
pip install shapely
pip install pyclipper
pip install opencv-python==4.8.1.78
pip install opencv-contrib-python==4.8.1.78
pip install imgaug
pip install lmdb
pip install attrdict
pip install beautifulsoup4
pip install rapidfuzz
pip install lxml
pip install tqdm
pip install Pillow
pip install matplotlib
pip install premailer
pip install openpyxl
pip install python-docx --no-deps

echo.
echo [7] PaddleOCR 설치 (의존성 무시)...
pip install paddleocr==2.7.0.3 --no-deps

echo.
echo [8] 테스트...
python test_paddle_install.py

echo.
pause