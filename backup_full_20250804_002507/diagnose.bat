@echo off
echo ============================================
echo Kakao OCR Chatbot System Diagnosis
echo ============================================
echo.

cd /d "D:\Project\카카오톡 챗봇 시스템"
call new_venv\Scripts\activate

echo Running diagnosis...
python test_ocr_system.py

pause