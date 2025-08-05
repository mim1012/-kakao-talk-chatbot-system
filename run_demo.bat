@echo off
title 카카오톡 OCR 챗봇 데모 (numpy 문제 우회 버전)
color 0B

echo.
echo ==========================================
echo 카카오톡 OCR 챗봇 시스템 - 데모 버전
echo numpy DLL 문제 우회 버전
echo ==========================================
echo.
echo 주의: 이것은 기술 데모 전용입니다.
echo 실제 OCR 기능은 제한적입니다.
echo 상업적 사용을 금지합니다.
echo.

REM 환경변수 설정
set PYTHONPATH=%CD%\src;%PYTHONPATH%
set KMP_DUPLICATE_LIB_OK=TRUE
set CUDA_VISIBLE_DEVICES=-1
set OMP_NUM_THREADS=1
set PYTHONIOENCODING=utf-8

REM 가상환경 확인
if exist "venv\Scripts\python.exe" (
    echo 가상환경에서 실행...
    venv\Scripts\python.exe main_demo.py
) else (
    echo 시스템 Python으로 실행...
    python main_demo.py
)

REM 결과 확인
if %ERRORLEVEL% equ 0 (
    echo.
    echo 데모 실행 완료
) else (
    echo.
    echo 데모 실행 중 오류 발생
    echo 다음을 시도해보세요:
    echo   1. python create_numpy_free_version.py
    echo   2. pip install PyQt5 Pillow mss psutil
    echo.
    pause
)
