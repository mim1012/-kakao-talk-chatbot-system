@echo off
echo ================================================
echo Win32 자동화 테스트
echo ================================================

cd /d "D:\Project\카카오톡 챗봇 시스템"

echo.
echo 1. Direct Win32 API 테스트...
python test_win32_click.py

echo.
echo 2. PyAutoGUI 테스트...
python test_direct_click.py

echo.
echo 3. 좌표 확인 테스트...
python test_coordinates.py

pause