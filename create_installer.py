#!/usr/bin/env python3
"""
사용자 친화적인 설치 패키지 생성
"""
import os
import shutil
import zipfile
import datetime

def create_installer():
    """올인원 설치 패키지 생성"""
    
    dist_folder = "KakaoOCRChatbot_Installer"
    if os.path.exists(dist_folder):
        shutil.rmtree(dist_folder)
    os.makedirs(dist_folder)
    
    print("[설치 패키지] 생성 중...")
    
    # 1. 프로그램 파일 복사
    program_folder = os.path.join(dist_folder, "program")
    os.makedirs(program_folder)
    
    # 필수 파일들
    files_to_copy = [
        "main.py",
        "config.json",
        "requirements.txt",
        "CLAUDE.md",
        "README.md"
    ]
    
    for file in files_to_copy:
        if os.path.exists(file):
            shutil.copy2(file, program_folder)
    
    # src 폴더
    if os.path.exists("src"):
        shutil.copytree("src", os.path.join(program_folder, "src"))
    
    # 2. 설치 스크립트 생성
    install_script = '''@echo off
title 카카오톡 OCR 챗봇 설치 프로그램
color 0A

echo ============================================
echo    카카오톡 OCR 챗봇 자동 설치 프로그램
echo ============================================
echo.

:: 관리자 권한 확인
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo [경고] 관리자 권한이 필요합니다.
    echo 마우스 오른쪽 클릭 → "관리자 권한으로 실행"을 선택해주세요.
    pause
    exit /b 1
)

:: Python 설치 확인
echo [1/5] Python 설치 확인...
python --version >nul 2>&1
if errorlevel 1 (
    echo.
    echo [오류] Python이 설치되어 있지 않습니다!
    echo.
    echo Python 3.11을 설치하시겠습니까? (Y/N)
    set /p install_python=
    if /i "%install_python%"=="Y" (
        echo Python 다운로드 페이지를 엽니다...
        start https://www.python.org/downloads/release/python-3119/
        echo.
        echo Python 설치 후 다시 실행해주세요.
        pause
        exit /b 1
    ) else (
        echo 설치를 취소합니다.
        pause
        exit /b 1
    )
)

echo [OK] Python이 설치되어 있습니다.
python --version
echo.

:: 프로그램 폴더 생성
echo [2/5] 프로그램 설치 중...
set install_path=C:\KakaoOCRChatbot
if exist "%install_path%" (
    echo 기존 설치 폴더를 제거합니다...
    rmdir /s /q "%install_path%"
)
mkdir "%install_path%"

:: 파일 복사
echo 파일을 복사하는 중...
xcopy /E /I /Y "program\*" "%install_path%"
echo [OK] 파일 복사 완료
echo.

:: 가상환경 생성
echo [3/5] 가상환경 생성 중...
cd /d "%install_path%"
python -m venv venv
echo [OK] 가상환경 생성 완료
echo.

:: 패키지 설치
echo [4/5] 필수 패키지 설치 중... (5-10분 소요)
call venv\Scripts\activate.bat
python -m pip install --upgrade pip
pip install numpy==1.26.4
pip install paddlepaddle paddleocr
pip install -r requirements.txt
echo [OK] 패키지 설치 완료
echo.

:: 바로가기 생성
echo [5/5] 바로가기 생성 중...
powershell -Command "$WScriptShell = New-Object -ComObject WScript.Shell; $Shortcut = $WScriptShell.CreateShortcut('%USERPROFILE%\Desktop\카카오톡 OCR 챗봇.lnk'); $Shortcut.TargetPath = '%install_path%\run.bat'; $Shortcut.WorkingDirectory = '%install_path%'; $Shortcut.IconLocation = '%SystemRoot%\System32\SHELL32.dll,13'; $Shortcut.Save()"

:: 실행 파일 생성
echo @echo off > "%install_path%\run.bat"
echo cd /d "%install_path%" >> "%install_path%\run.bat"
echo call venv\Scripts\activate.bat >> "%install_path%\run.bat"
echo set QT_PLUGIN_PATH=%install_path%\venv\Lib\site-packages\PyQt5\Qt5\plugins >> "%install_path%\run.bat"
echo python main.py >> "%install_path%\run.bat"
echo pause >> "%install_path%\run.bat"

echo.
echo ============================================
echo    설치가 완료되었습니다!
echo ============================================
echo.
echo 설치 위치: %install_path%
echo 바탕화면에 바로가기가 생성되었습니다.
echo.
echo 지금 실행하시겠습니까? (Y/N)
set /p run_now=
if /i "%run_now%"=="Y" (
    start "" "%install_path%\run.bat"
)

pause
'''
    
    with open(os.path.join(dist_folder, "설치.bat"), "w", encoding="cp949") as f:
        f.write(install_script)
    
    # 3. 사용 설명서
    manual = """# 카카오톡 OCR 챗봇 설치 및 사용 안내

## 설치 방법

1. **설치.bat** 파일을 **관리자 권한**으로 실행
   - 마우스 오른쪽 클릭 → "관리자 권한으로 실행"

2. 설치 과정 (자동)
   - Python 설치 확인
   - 프로그램 파일 복사
   - 가상환경 생성
   - 필수 패키지 설치
   - 바탕화면 바로가기 생성

## 사용 방법

1. 바탕화면의 "카카오톡 OCR 챗봇" 바로가기 실행
2. GUI 창에서 "모니터링 시작" 클릭
3. 카카오톡 창을 적절한 위치에 배치

## 설정 변경

- C:\KakaoOCRChatbot\config.json 파일 수정
- 클릭 위치: `input_box_offset.from_bottom` 값 조정

## 문제 해결

### 프로그램이 실행되지 않을 때
1. C:\KakaoOCRChatbot\run.bat 직접 실행
2. 오류 메시지 확인

### OCR이 작동하지 않을 때
1. 카카오톡 창 위치 확인
2. 오버레이 표시로 감지 영역 확인

## 제거 방법

1. C:\KakaoOCRChatbot 폴더 삭제
2. 바탕화면 바로가기 삭제
"""
    
    with open(os.path.join(dist_folder, "사용설명서.txt"), "w", encoding="utf-8") as f:
        f.write(manual)
    
    # 4. ZIP 파일로 압축
    timestamp = datetime.datetime.now().strftime("%Y%m%d")
    zip_filename = f"KakaoOCRChatbot_Installer_{timestamp}.zip"
    
    with zipfile.ZipFile(zip_filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(dist_folder):
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, dist_folder)
                zipf.write(file_path, arcname)
    
    size_mb = os.path.getsize(zip_filename) / (1024 * 1024)
    
    print(f"\n[완료] 설치 패키지 생성 완료!")
    print(f"파일명: {zip_filename}")
    print(f"크기: {size_mb:.2f} MB")
    print("\n전달 방법:")
    print("1. USB 메모리")
    print("2. 구글 드라이브")
    print("3. 이메일 첨부")

if __name__ == "__main__":
    create_installer()