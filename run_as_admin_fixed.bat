@echo off
chcp 65001 > nul
echo ================================================
echo 관리자 권한으로 카카오톡 챗봇 실행
echo ================================================

:: 현재 디렉토리로 이동
cd /d "%~dp0"
echo 현재 디렉토리: %CD%

:: 관리자 권한 확인
net session >nul 2>&1
if %errorLevel% == 0 (
    echo ✅ 관리자 권한으로 실행 중입니다.
    echo.
    goto :run
) else (
    echo ❌ 관리자 권한이 필요합니다!
    echo.
    echo 이 창을 닫고 다음 방법으로 실행하세요:
    echo 1. 이 파일을 우클릭
    echo 2. "관리자 권한으로 실행" 선택
    echo.
    pause
    exit
)

:run
echo Qt 플러그인 경로 설정...
set QT_PLUGIN_PATH=%CD%\venv\Lib\site-packages\PyQt5\Qt5\plugins

echo.
echo 메인 프로그램 실행...
echo 실행 명령: python "%CD%\main.py"
python "%CD%\main.py"

pause