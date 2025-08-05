@echo off
chcp 65001 >nul
echo ============================================
echo 카카오톡 OCR 챗봇 시스템 진단
echo ============================================
echo.

cd /d "D:\Project\카카오톡 챗봇 시스템"
call new_venv\Scripts\activate

echo Python 경로 설정 중...
set PYTHONPATH=%CD%\src;%PYTHONPATH%

echo 진단 실행 중...
python test_ocr_system.py

pause