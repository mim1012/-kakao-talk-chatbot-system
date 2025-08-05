#!/usr/bin/env python3
"""
최종 배포 패키지 생성 (가상환경 문제 해결)
"""
import os
import shutil
import zipfile
import datetime

def create_final_package():
    """최종 배포 패키지 생성"""
    
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    zip_filename = f"KakaoOCRChatbot_Final_{timestamp}.zip"
    
    print("[Final Package] Creating distribution package...")
    
    # 포함할 파일 목록
    files_to_include = [
        "main.py",
        "config.json",
        "install_simple.bat",
        "install_manual.bat",
        "README.md"
    ]
    
    with zipfile.ZipFile(zip_filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
        # 개별 파일 추가
        for file in files_to_include:
            if os.path.exists(file):
                zipf.write(file)
                print(f"  Added: {file}")
        
        # src 폴더 전체 추가
        if os.path.exists("src"):
            for root, dirs, files in os.walk("src"):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path)
                    zipf.write(file_path, arcname)
            print("  Added: src/ folder")
        
        # 간단한 실행 배치 파일도 추가
        run_bat_content = """@echo off
title KakaoTalk OCR Chatbot
python main.py
pause
"""
        # 임시 파일 생성
        with open("run.bat", "w") as f:
            f.write(run_bat_content)
        zipf.write("run.bat")
        os.remove("run.bat")  # 임시 파일 제거
        print("  Added: run.bat")
    
    # 사용 안내서 생성
    guide = """=== KakaoTalk OCR Chatbot 사용 안내 ===

[설치 방법 - 옵션 1: 자동 설치]
1. install_simple.bat 더블클릭
2. 완료 후 run.bat 실행

[설치 방법 - 옵션 2: 수동 설치]
1. install_manual.bat 더블클릭
2. 안내에 따라 진행

[설치 방법 - 옵션 3: 명령 프롬프트]
1. 명령 프롬프트(cmd) 열기
2. 이 폴더로 이동
3. 다음 명령어 실행:
   pip install numpy==1.26.4
   pip install paddlepaddle paddleocr
   pip install PyQt5 pyautogui mss screeninfo pyperclip psutil
4. 실행: python main.py

[실행 방법]
- run.bat 더블클릭
- 또는 명령 프롬프트에서: python main.py

[필수 프로그램]
- Python 3.11 (https://www.python.org/downloads/)
- Windows 10 이상

[문제 해결]
1. 백신 프로그램 일시 중지
2. 명령 프롬프트를 관리자 권한으로 실행
3. 인터넷 연결 확인
4. Python PATH 설정 확인

[지원]
- 설치 문제가 계속되면 수동으로 각 패키지를 하나씩 설치해보세요.
"""
    
    with open("설치안내.txt", "w", encoding="cp949") as f:
        f.write(guide)
    
    # 최종 안내
    size_mb = os.path.getsize(zip_filename) / (1024 * 1024)
    print(f"\n[Complete] Final package created!")
    print(f"File: {zip_filename}")
    print(f"Size: {size_mb:.2f} MB")
    print("\n[Installation Options]")
    print("1. install_simple.bat (automatic)")
    print("2. install_manual.bat (guided)")
    print("3. Manual pip commands")
    
    # 이전 파일들 정리
    old_files = [f for f in os.listdir('.') if f.startswith('KakaoOCRChatbot_') and f.endswith('.zip') and f != zip_filename]
    for old_file in old_files:
        try:
            os.remove(old_file)
            print(f"Cleaned: {old_file}")
        except:
            pass

if __name__ == "__main__":
    create_final_package()