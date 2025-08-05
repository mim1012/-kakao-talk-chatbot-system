@echo off
echo 카카오톡 OCR 챗봇 시스템 (호환성 수정 버전)
echo 기술 데모용 - Python 3.13 지원
echo.

REM 환경변수 설정
set PYTHONPATH=%CD%\src;%PYTHONPATH%
set KMP_DUPLICATE_LIB_OK=TRUE
set CUDA_VISIBLE_DEVICES=-1
set OMP_NUM_THREADS=1

REM 가상환경 활성화
if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
    echo 가상환경 활성화됨
) else (
    echo 가상환경이 없습니다.
    echo python -m venv venv 로 생성하세요.
    pause
    exit /b 1
)

REM 프로그램 실행
echo 프로그램 시작...
python main.py

if %ERRORLEVEL% neq 0 (
    echo 오류가 발생했습니다.
    pause
)
