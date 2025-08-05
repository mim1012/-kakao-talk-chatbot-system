#!/usr/bin/env python3
"""
가장 간단한 배포 패키지 생성
"""
import os
import shutil
import zipfile
import datetime

def create_simple_package():
    """단순 배포 패키지 생성"""
    
    # 필요한 파일들만 ZIP으로 압축
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    zip_filename = f"KakaoOCRChatbot_{timestamp}.zip"
    
    print("[Package] Creating simple distribution package...")
    
    # 포함할 파일 목록
    files_to_include = [
        "main.py",
        "config.json",
        "requirements.txt",
        "quick_setup.bat",
        "README.md",
        "CLAUDE.md"
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
        
        # docs 폴더 추가
        if os.path.exists("docs"):
            for root, dirs, files in os.walk("docs"):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path)
                    zipf.write(file_path, arcname)
            print("  Added: docs/ folder")
    
    # 사용 안내서 생성
    guide = """=== KakaoTalk OCR Chatbot 사용 안내 ===

[설치 방법]
1. ZIP 파일을 원하는 폴더에 압축 해제
2. quick_setup.bat 실행 (자동 설치)
3. 설치 완료 후 run_chatbot.bat 실행

[수동 설치 (quick_setup.bat이 안 될 때)]
1. 명령 프롬프트 열기
2. 압축 해제한 폴더로 이동
3. 다음 명령어 실행:
   python -m venv venv
   venv\Scripts\activate.bat
   pip install -r requirements.txt
4. 실행: python main.py

[필수 프로그램]
- Python 3.11 (https://www.python.org/downloads/)
- Windows 10 이상

[문제 해결]
- 백신 프로그램 일시 중지
- 관리자 권한으로 실행
- 인터넷 연결 확인
"""
    
    with open("사용안내.txt", "w", encoding="cp949") as f:
        f.write(guide)
    
    # 최종 안내
    size_mb = os.path.getsize(zip_filename) / (1024 * 1024)
    print(f"\n[Complete] Package created successfully!")
    print(f"File: {zip_filename}")
    print(f"Size: {size_mb:.2f} MB")
    print("\n[Usage]")
    print("1. Send this ZIP file to user")
    print("2. User extracts ZIP")
    print("3. User runs quick_setup.bat")
    print("4. Done!")
    
    # 기존 패키지들 정리
    clean_files = [
        "KakaoOCRChatbot_Setup_20250805_210624.zip",
        "kakao_chatbot_20250805_210106.zip"
    ]
    
    for f in clean_files:
        if os.path.exists(f):
            os.remove(f)
    
    # 임시 폴더 정리
    clean_dirs = ["KakaoOCRChatbot_Setup", "kakao_chatbot_dist", "KakaoOCRChatbot_Installer"]
    for d in clean_dirs:
        if os.path.exists(d):
            shutil.rmtree(d)

if __name__ == "__main__":
    create_simple_package()