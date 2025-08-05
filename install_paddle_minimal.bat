@echo off
chcp 65001 > nul
echo ============================================================
echo PaddleOCR 최소 설치 (PyMuPDF 제외)
echo ============================================================
echo.

REM 가상환경 활성화
call venv\Scripts\activate.bat

echo [1] Python 버전 확인...
python --version

echo.
echo [2] PaddleOCR 핵심 패키지만 설치...
echo.

REM PyMuPDF를 제외하고 설치
pip install paddlepaddle==2.5.2 --no-deps
pip install paddleocr==2.7.0.3 --no-deps

echo.
echo [3] 필수 의존성만 설치...
pip install opencv-python==4.6.0.66
pip install opencv-contrib-python==4.6.0.66
pip install shapely
pip install pyclipper
pip install Pillow
pip install tqdm
pip install numpy==1.24.3
pip install scipy
pip install scikit-image
pip install imgaug
pip install lmdb
pip install rapidfuzz
pip install premailer
pip install attrdict
pip install beautifulsoup4
pip install lxml
pip install matplotlib

echo.
echo [4] 설치 확인...
python -c "import paddle; print(f'✅ PaddlePaddle {paddle.__version__}')" 2>nul || echo ⚠️ PaddlePaddle 확인 필요
python -c "from paddleocr import PaddleOCR; print('✅ PaddleOCR import 성공')" 2>nul || echo ⚠️ PaddleOCR 확인 필요

echo.
echo ============================================================
echo 설치 완료! (PyMuPDF 제외)
echo ============================================================
echo.
pause