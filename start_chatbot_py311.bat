@echo off
echo 카카오톡 챗봇 시스템 시작 (Python 3.11)
echo.

REM 가상환경 활성화
call venv\Scripts\activate.bat

REM Python 버전 확인
python --version

REM 메인 프로그램 실행
python main.py

pause