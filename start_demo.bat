@echo off
echo īī���� OCR ê�� �ý��� (ȣȯ�� ���� ����)
echo ��� ����� - Python 3.13 ����
echo.

REM ȯ�溯�� ����
set PYTHONPATH=%CD%\src;%PYTHONPATH%
set KMP_DUPLICATE_LIB_OK=TRUE
set CUDA_VISIBLE_DEVICES=-1
set OMP_NUM_THREADS=1

REM ����ȯ�� Ȱ��ȭ
if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
    echo ����ȯ�� Ȱ��ȭ��
) else (
    echo ����ȯ���� �����ϴ�.
    echo python -m venv venv �� �����ϼ���.
    pause
    exit /b 1
)

REM ���α׷� ����
echo ���α׷� ����...
python main.py

if %ERRORLEVEL% neq 0 (
    echo ������ �߻��߽��ϴ�.
    pause
)
