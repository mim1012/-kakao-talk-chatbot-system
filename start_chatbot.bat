@echo off
chcp 65001 > nul
echo ============================================================
echo 카카오톡 OCR 챗봇 시스템 시작
echo ============================================================
echo.

REM Python 환경 설정
set PYTHONIOENCODING=utf-8
set PYTHONLEGACYWINDOWSSTDIO=utf-8

REM PaddleOCR 로그 차단
set PPOCR_LOG_LEVEL=ERROR
set PADDLEX_LOG_LEVEL=ERROR
set PADDLE_LOG_LEVEL=ERROR
set PADDLEOCR_SHOW_PROGRESS=0
set PADDLEX_SHOW_PROGRESS=0
set TQDM_DISABLE=1
set GLOG_v=0
set GLOG_logtostderr=0
set GLOG_minloglevel=3

echo [정보] GUI를 시작합니다...
echo.
echo 📌 사용 방법:
echo    1. "모니터링 시작" 버튼 클릭 - OCR 감지 시작
echo    2. "오버레이 표시" 버튼 클릭 - 화면에 감지 영역 표시
echo    3. 카카오톡 창이 감지 영역에 위치해야 함
echo.
echo [참고] 첫 실행시 PaddleOCR 모델을 다운로드할 수 있습니다.
echo        이는 정상적인 과정이며 한 번만 수행됩니다.
echo.

REM GUI 실행
python main.py

if errorlevel 1 (
    echo.
    echo [오류] 프로그램 실행 중 문제가 발생했습니다.
    echo.
    echo 해결 방법:
    echo 1. Python 3.11 이상이 설치되어 있는지 확인
    echo 2. pip install -r requirements.txt 실행
    echo 3. 관리자 권한으로 재실행
    pause
)