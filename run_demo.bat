@echo off
title īī���� OCR ê�� ���� (numpy ���� ��ȸ ����)
color 0B

echo.
echo ==========================================
echo īī���� OCR ê�� �ý��� - ���� ����
echo numpy DLL ���� ��ȸ ����
echo ==========================================
echo.
echo ����: �̰��� ��� ���� �����Դϴ�.
echo ���� OCR ����� �������Դϴ�.
echo ����� ����� �����մϴ�.
echo.

REM ȯ�溯�� ����
set PYTHONPATH=%CD%\src;%PYTHONPATH%
set KMP_DUPLICATE_LIB_OK=TRUE
set CUDA_VISIBLE_DEVICES=-1
set OMP_NUM_THREADS=1
set PYTHONIOENCODING=utf-8

REM ����ȯ�� Ȯ��
if exist "venv\Scripts\python.exe" (
    echo ����ȯ�濡�� ����...
    venv\Scripts\python.exe main_demo.py
) else (
    echo �ý��� Python���� ����...
    python main_demo.py
)

REM ��� Ȯ��
if %ERRORLEVEL% equ 0 (
    echo.
    echo ���� ���� �Ϸ�
) else (
    echo.
    echo ���� ���� �� ���� �߻�
    echo ������ �õ��غ�����:
    echo   1. python create_numpy_free_version.py
    echo   2. pip install PyQt5 Pillow mss psutil
    echo.
    pause
)
