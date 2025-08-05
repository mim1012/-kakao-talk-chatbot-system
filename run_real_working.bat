@echo off
title 카카오톡 OCR 챗봇 - 실제 텍스트 인식 가능
color 0A

echo.
echo ==========================================
echo 카카오톡 OCR 챗봇 시스템
echo 실제 OCR 작동 버전 (PaddleOCR 파라미터 수정)
echo ==========================================
echo.
echo 주의: 실제 텍스트 인식이 가능합니다.
echo 기술 데모 전용으로 사용하세요.
echo.

REM 환경변수 설정
set PYTHONPATH=%CD%\src;%PYTHONPATH%
set KMP_DUPLICATE_LIB_OK=TRUE
set CUDA_VISIBLE_DEVICES=-1
set OMP_NUM_THREADS=1
set PYTHONIOENCODING=utf-8

REM 실제 OCR 시스템 실행
echo 실제 OCR 시스템 시작...
echo.

REM 가상환경에서 실행 시도
if exist "venv\Scripts\python.exe" (
    echo 가상환경에서 실행...
    venv\Scripts\python.exe main_real_working.py
) else (
    echo 시스템 Python으로 실행...
    python main_real_working.py
)

REM 결과 확인
if %ERRORLEVEL% equ 0 (
    echo.
    echo ==========================================
    echo 실제 OCR 시스템 정상 종료
    echo ==========================================
) else (
    echo.
    echo ==========================================
    echo ERROR 실행 중 오류 발생
    echo ==========================================
    echo.
    echo 해결 방법:
    echo   1. setup_real_ocr.bat 실행
    echo   2. python fix_real_ocr.py 실행
    echo   3. 가상환경 재생성
    echo.
    pause
)
