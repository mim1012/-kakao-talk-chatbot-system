@echo off
echo 카카오톡 챗봇 시스템 이전용 스크립트
echo =====================================

REM 필수 파일만 압축
powershell -Command "Compress-Archive -Path @('src', 'tools', 'tests', '*.py', '*.txt', '*.json', '*.md') -DestinationPath 'chatbot_transfer.zip' -Force"

echo.
echo 압축 완료! chatbot_transfer.zip 파일이 생성되었습니다.
echo.
echo 다른 컴퓨터에서 설치 방법:
echo 1. zip 파일 압축 해제
echo 2. cmd 또는 PowerShell 열기
echo 3. 프로젝트 폴더로 이동
echo 4. 다음 명령어 실행:
echo    python -m venv venv
echo    venv\Scripts\activate
echo    pip install -r requirements.txt
echo    python main.py
echo.
pause