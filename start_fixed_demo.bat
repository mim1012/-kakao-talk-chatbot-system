@echo off
title 카카오톡 OCR 챗봇 (호환성 수정 버전)
echo.
echo ========================================
echo 카카오톡 OCR 챗봇 시스템
echo 호환성 수정 버전 - Python 3.13 지원
echo 기술 데모 전용
echo ========================================
echo.

REM 환경변수 설정
set PYTHONPATH=%CD%\src;%PYTHONPATH%
set KMP_DUPLICATE_LIB_OK=TRUE
set CUDA_VISIBLE_DEVICES=-1
set OMP_NUM_THREADS=1
set PYTHONIOENCODING=utf-8

echo 환경 설정 완료

REM 가상환경 확인
if exist "venv\Scripts\activate.bat" (
    echo 가상환경 활성화 중...
    call venv\Scripts\activate.bat
    echo 가상환경 활성화됨
) else (
    echo 경고: 가상환경이 없습니다.
    echo 다음 명령을 실행하세요:
    echo   python -m venv venv
    echo   venv\Scripts\activate.bat
    echo   python fix_numpy_auto.py
    echo.
    pause
    exit /b 1
)

echo.
echo 프로그램 시작 중...
echo 주의: 이것은 기술 데모용입니다.
echo.

python main.py

if %ERRORLEVEL% neq 0 (
    echo.
    echo 오류가 발생했습니다.
    echo 다음을 시도해보세요:
    echo   1. python fix_numpy_auto.py
    echo   2. python run_tests_fixed.py
    echo.
    pause
) else (
    echo.
    echo 프로그램이 정상 종료되었습니다.
)
