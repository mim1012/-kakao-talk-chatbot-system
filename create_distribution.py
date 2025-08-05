#!/usr/bin/env python3
"""
클라이언트 배포용 패키지 생성 스크립트
"""
import os
import shutil
import zipfile
import datetime

def create_distribution():
    """배포용 패키지 생성"""
    
    # 배포 폴더 생성
    dist_folder = "kakao_chatbot_dist"
    if os.path.exists(dist_folder):
        shutil.rmtree(dist_folder)
    os.makedirs(dist_folder)
    
    print("[패키지] 배포 패키지 생성 중...")
    
    # 1. 필수 파일들 복사
    essential_files = [
        "main.py",
        "config.json",
        "requirements.txt",
        "run_with_qt.bat",
        "CLAUDE.md",
        "README.md"
    ]
    
    for file in essential_files:
        if os.path.exists(file):
            shutil.copy2(file, dist_folder)
            print(f"  [OK] {file} 복사 완료")
    
    # 2. src 폴더 전체 복사
    if os.path.exists("src"):
        shutil.copytree("src", os.path.join(dist_folder, "src"))
        print("  [OK] src 폴더 복사 완료")
    
    # 3. 배치 파일 생성
    
    # 설치 배치 파일
    install_bat = """@echo off
echo ====================================
echo 카카오톡 OCR 챗봇 설치 프로그램
echo ====================================
echo.

echo Python 3.11이 설치되어 있는지 확인합니다...
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python이 설치되어 있지 않습니다!
    echo Python 3.11을 먼저 설치해주세요.
    echo https://www.python.org/downloads/
    pause
    exit /b 1
)

echo Python 버전:
python --version
echo.

echo 필수 패키지를 설치합니다...
echo.

echo 1. numpy 설치 중...
pip install numpy==1.26.4

echo 2. PaddleOCR 설치 중...
pip install paddlepaddle paddleocr

echo 3. 기타 패키지 설치 중...
pip install -r requirements.txt

echo.
echo [OK] 설치가 완료되었습니다!
echo.
echo 실행 방법:
echo   1. run.bat 파일을 더블클릭하세요
echo   2. 또는 python main.py 명령을 실행하세요
echo.
pause
"""
    
    with open(os.path.join(dist_folder, "install.bat"), "w", encoding="utf-8") as f:
        f.write(install_bat)
    
    # 실행 배치 파일
    run_bat = """@echo off
title 카카오톡 OCR 챗봇
echo 카카오톡 OCR 챗봇을 시작합니다...
python main.py
pause
"""
    
    with open(os.path.join(dist_folder, "run.bat"), "w", encoding="utf-8") as f:
        f.write(run_bat)
    
    # 4. 사용 설명서 생성
    manual = """# 카카오톡 OCR 챗봇 사용 설명서

## 1. 설치 방법

1. **Python 3.11 설치** (이미 설치되어 있다면 건너뛰세요)
   - https://www.python.org/downloads/ 에서 Python 3.11 다운로드
   - 설치 시 "Add Python to PATH" 체크 필수!

2. **챗봇 설치**
   - install.bat 파일을 더블클릭하여 실행
   - 자동으로 필요한 패키지들이 설치됩니다

## 2. 실행 방법

1. **run.bat** 파일을 더블클릭
2. GUI 창이 열리면 "모니터링 시작" 버튼 클릭
3. 카카오톡 창을 적절한 위치에 배치

## 3. 설정 방법

### config.json 파일 수정
- `trigger_patterns`: 감지할 텍스트 패턴 (예: "들어왔습니다")
- `chatroom_configs`: 카카오톡 창 위치 설정

### 카카오톡 창 위치 조정
1. "오버레이 표시" 버튼을 클릭하여 감지 영역 확인
2. 카카오톡 창을 파란색 오버레이 영역에 맞춰 배치
3. 또는 config.json의 좌표를 수정

## 4. 문제 해결

### "Python이 설치되어 있지 않습니다" 오류
- Python 3.11을 설치하고 PATH에 추가했는지 확인

### OCR이 텍스트를 감지하지 못할 때
- 카카오톡 창이 오버레이 영역에 제대로 위치했는지 확인
- 화면 해상도가 1920x1080인지 확인
- config.json의 좌표 설정 확인

### 프로그램이 실행되지 않을 때
- 명령 프롬프트에서 `python main.py` 실행하여 오류 메시지 확인
- requirements.txt의 모든 패키지가 설치되었는지 확인

## 5. 주의사항

- 카카오톡 창이 다른 창에 가려지지 않도록 주의
- 화면 보호기가 실행되지 않도록 설정
- 원격 데스크톱 환경에서는 연결이 끊어지지 않도록 주의

## 문의사항

문제가 발생하거나 도움이 필요하면 개발자에게 연락주세요.
"""
    
    with open(os.path.join(dist_folder, "사용설명서.md"), "w", encoding="utf-8") as f:
        f.write(manual)
    
    # 5. 간단한 설정 도구
    config_tool = """import tkinter as tk
from tkinter import messagebox
import json

def save_config():
    try:
        with open('config.json', 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        # 트리거 패턴 업데이트
        patterns = patterns_text.get("1.0", tk.END).strip().split('\\n')
        config['trigger_patterns'] = [p.strip() for p in patterns if p.strip()]
        
        with open('config.json', 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
        
        messagebox.showinfo("성공", "설정이 저장되었습니다!")
    except Exception as e:
        messagebox.showerror("오류", f"설정 저장 실패: {e}")

# GUI 생성
root = tk.Tk()
root.title("카카오톡 챗봇 설정")
root.geometry("400x300")

# 트리거 패턴 설정
tk.Label(root, text="감지할 텍스트 패턴 (한 줄에 하나씩):", font=("Arial", 10)).pack(pady=10)

patterns_text = tk.Text(root, height=10, width=40)
patterns_text.pack(pady=5)

# 기존 설정 로드
try:
    with open('config.json', 'r', encoding='utf-8') as f:
        config = json.load(f)
        patterns = config.get('trigger_patterns', [])
        patterns_text.insert("1.0", '\\n'.join(patterns))
except:
    patterns_text.insert("1.0", "들어왔습니다\\n님이\\n입장\\n들어왔\\n참여")

# 저장 버튼
tk.Button(root, text="설정 저장", command=save_config, bg="green", fg="white", 
          font=("Arial", 12), width=20).pack(pady=20)

root.mainloop()
"""
    
    with open(os.path.join(dist_folder, "config_tool.py"), "w", encoding="utf-8") as f:
        f.write(config_tool)
    
    # 6. ZIP 파일로 압축
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    zip_filename = f"kakao_chatbot_{timestamp}.zip"
    
    print(f"\n[ZIP] ZIP 파일 생성 중: {zip_filename}")
    
    with zipfile.ZipFile(zip_filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(dist_folder):
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, dist_folder)
                zipf.write(file_path, arcname)
    
    # 파일 크기 확인
    size_mb = os.path.getsize(zip_filename) / (1024 * 1024)
    
    print("\n[완료] 배포 패키지 생성 완료!")
    print(f"[파일명] {zip_filename}")
    print(f"[크기] {size_mb:.2f} MB")
    print(f"[폴더] {dist_folder}")
    
    # 7. 전송 방법 안내
    print("\n[전송 방법] 클라이언트에게 전송하는 방법:")
    print("1. 이메일 첨부파일로 전송")
    print("2. Google Drive, Dropbox 등 클라우드 스토리지 공유")
    print("3. USB 메모리에 복사")
    print("4. 카카오톡 파일 전송 (용량이 크면 분할 필요)")
    
    return zip_filename

if __name__ == "__main__":
    create_distribution()