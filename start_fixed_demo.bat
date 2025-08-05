@echo off
title īī���� OCR ê�� (ȣȯ�� ���� ����)
echo.
echo ========================================
echo īī���� OCR ê�� �ý���
echo ȣȯ�� ���� ���� - Python 3.13 ����
echo ��� ���� ����
echo ========================================
echo.

REM ȯ�溯�� ����
set PYTHONPATH=%CD%\src;%PYTHONPATH%
set KMP_DUPLICATE_LIB_OK=TRUE
set CUDA_VISIBLE_DEVICES=-1
set OMP_NUM_THREADS=1
set PYTHONIOENCODING=utf-8

echo ȯ�� ���� �Ϸ�

REM ����ȯ�� Ȯ��
if exist "venv\Scripts\activate.bat" (
    echo ����ȯ�� Ȱ��ȭ ��...
    call venv\Scripts\activate.bat
    echo ����ȯ�� Ȱ��ȭ��
) else (
    echo ���: ����ȯ���� �����ϴ�.
    echo ���� ����� �����ϼ���:
    echo   python -m venv venv
    echo   venv\Scripts\activate.bat
    echo   python fix_numpy_auto.py
    echo.
    pause
    exit /b 1
)

echo.
echo ���α׷� ���� ��...
echo ����: �̰��� ��� ������Դϴ�.
echo.

python main.py

if %ERRORLEVEL% neq 0 (
    echo.
    echo ������ �߻��߽��ϴ�.
    echo ������ �õ��غ�����:
    echo   1. python fix_numpy_auto.py
    echo   2. python run_tests_fixed.py
    echo.
    pause
) else (
    echo.
    echo ���α׷��� ���� ����Ǿ����ϴ�.
)
