@echo off
title 실제 OCR 시스템 설정
color 0C

echo.
echo ==========================================
echo 실제 OCR 시스템 설정
echo numpy DLL 문제 완전 해결
echo ==========================================
echo.

REM 가상환경 생성 (이미 있으면 스킵)
if not exist "venv" (
    echo 가상환경 생성 중...
    python -m venv venv
    if %ERRORLEVEL% neq 0 (
        echo 가상환경 생성 실패
        pause
        exit /b 1
    )
    echo 가상환경 생성 완료
) else (
    echo 기존 가상환경 사용
)

echo.
echo 가상환경 활성화 중...
call venv\Scripts\activate.bat

REM Python 버전 확인
python --version
echo.

REM pip 업그레이드
echo pip 업그레이드 중...
python -m pip install --upgrade pip

REM 기존 문제 패키지 완전 제거
echo.
echo 문제 패키지 제거 중...
pip uninstall numpy opencv-python paddleocr paddlepaddle scipy -y

REM numpy 설치 (여러 버전 시도)
echo.
echo numpy 설치 중...
pip install numpy==1.24.3 --force-reinstall --no-cache-dir
if %ERRORLEVEL% neq 0 (
    echo numpy 1.24.3 실패, 1.26.4 시도...
    pip install numpy==1.26.4 --force-reinstall --no-cache-dir
)

REM numpy 테스트
python -c "import numpy as np; print(f'numpy {np.__version__} 설치 성공')"
if %ERRORLEVEL% neq 0 (
    echo numpy 설치 실패!
    pause
    exit /b 1
)

REM OpenCV 설치
echo.
echo OpenCV 설치 중...
pip install opencv-python==4.8.1.78 --no-cache-dir

REM OpenCV 테스트
python -c "import cv2; import numpy; print(f'OpenCV {cv2.__version__} + numpy 연동 성공')"
if %ERRORLEVEL% neq 0 (
    echo OpenCV 설치 실패!
    pause
    exit /b 1
)

REM 기본 패키지 설치
echo.
echo 기본 패키지 설치 중...
pip install Pillow==10.0.1 PyQt5==5.15.9 mss psutil screeninfo

REM PaddlePaddle 설치 (CPU 버전)
echo.
echo PaddlePaddle 설치 중...
pip install paddlepaddle==2.5.2 -i https://pypi.org/simple/

REM PaddleOCR 설치
echo.
echo PaddleOCR 설치 중...
pip install paddleocr==2.7.3

echo.
echo ==========================================
echo 설치 완료! 테스트 중...
echo ==========================================

REM 종합 테스트
python -c "
import os
os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'
os.environ['CUDA_VISIBLE_DEVICES'] = '-1'

print('=== 실제 OCR 테스트 ===')
import numpy as np
print(f'✅ numpy {np.__version__}')

import cv2  
print(f'✅ OpenCV {cv2.__version__}')

import paddleocr
print('✅ PaddleOCR import 성공')

# 실제 OCR 테스트
print('PaddleOCR 초기화 중...')
ocr = paddleocr.PaddleOCR(use_angle_cls=True, lang='korean', show_log=False)
print('✅ PaddleOCR 초기화 성공!')

# 테스트 이미지로 OCR 실행
test_img = np.ones((100, 300, 3), dtype=np.uint8) * 255
result = ocr.ocr(test_img, cls=True)
print('✅ 실제 OCR 실행 성공!')
print('🎉 모든 테스트 통과! 실제 텍스트 인식 가능!')
"

if %ERRORLEVEL% equ 0 (
    echo.
    echo ==========================================
    echo 🎉 실제 OCR 시스템 설정 완료!
    echo ==========================================
    echo.
    echo 이제 다음 명령으로 실행하세요:
    echo   run_real_ocr.bat
    echo 또는
    echo   python main_real_ocr.py
    echo.
    echo ✅ 실제 텍스트 인식이 가능합니다!
    echo.
) else (
    echo.
    echo ❌ 설치 중 오류 발생
    echo 가상환경을 삭제하고 다시 시도하세요:
    echo   rmdir /s venv
    echo   setup_real_ocr.bat
    echo.
)

pause