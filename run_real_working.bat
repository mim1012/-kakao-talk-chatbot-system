@echo off
title īī���� OCR ê�� - ���� �ؽ�Ʈ �ν� ����
color 0A

echo.
echo ==========================================
echo īī���� OCR ê�� �ý���
echo ���� OCR �۵� ���� (PaddleOCR �Ķ���� ����)
echo ==========================================
echo.
echo ����: ���� �ؽ�Ʈ �ν��� �����մϴ�.
echo ��� ���� �������� ����ϼ���.
echo.

REM ȯ�溯�� ����
set PYTHONPATH=%CD%\src;%PYTHONPATH%
set KMP_DUPLICATE_LIB_OK=TRUE
set CUDA_VISIBLE_DEVICES=-1
set OMP_NUM_THREADS=1
set PYTHONIOENCODING=utf-8

REM ���� OCR �ý��� ����
echo ���� OCR �ý��� ����...
echo.

REM ����ȯ�濡�� ���� �õ�
if exist "venv\Scripts\python.exe" (
    echo ����ȯ�濡�� ����...
    venv\Scripts\python.exe main_real_working.py
) else (
    echo �ý��� Python���� ����...
    python main_real_working.py
)

REM ��� Ȯ��
if %ERRORLEVEL% equ 0 (
    echo.
    echo ==========================================
    echo ���� OCR �ý��� ���� ����
    echo ==========================================
) else (
    echo.
    echo ==========================================
    echo ERROR ���� �� ���� �߻�
    echo ==========================================
    echo.
    echo �ذ� ���:
    echo   1. setup_real_ocr.bat ����
    echo   2. python fix_real_ocr.py ����
    echo   3. ����ȯ�� �����
    echo.
    pause
)
