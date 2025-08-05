#!/usr/bin/env python3
"""
안전한 배포 패키지 생성 (인코딩 문제 해결)
"""
import os
import shutil
import zipfile
import datetime

def create_safe_installer():
    """영어 기반 설치 패키지 생성"""
    
    dist_folder = "KakaoOCRChatbot_Setup"
    if os.path.exists(dist_folder):
        shutil.rmtree(dist_folder)
    os.makedirs(dist_folder)
    
    print("[Setup] Creating installation package...")
    
    # 1. Copy program files
    program_folder = os.path.join(dist_folder, "program")
    os.makedirs(program_folder)
    
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
    
    if os.path.exists("src"):
        shutil.copytree("src", os.path.join(program_folder, "src"))
    
    # 2. Copy installer
    if os.path.exists("simple_installer.bat"):
        shutil.copy2("simple_installer.bat", os.path.join(dist_folder, "INSTALL.bat"))
    
    # 3. Create Korean readme
    readme_kr = """=== KakaoTalk OCR Chatbot ===

[설치 방법]
1. INSTALL.bat 파일을 마우스 오른쪽 클릭
2. "관리자 권한으로 실행" 선택
3. 설치 완료 후 C:\KakaoOCRChatbot\run.bat 실행

[필수 사항]
- Windows 10 이상
- Python 3.11 (없으면 먼저 설치)
- 인터넷 연결

[문제 해결]
- Python 설치: https://www.python.org/downloads/
- 설치 오류 시 백신 프로그램 일시 중지
"""
    
    # Save as ANSI (cp949)
    with open(os.path.join(dist_folder, "README_KR.txt"), "w", encoding="cp949") as f:
        f.write(readme_kr)
    
    # 4. Create English readme
    readme_en = """=== KakaoTalk OCR Chatbot ===

[Installation]
1. Right-click INSTALL.bat
2. Select "Run as administrator"
3. After installation, run C:\KakaoOCRChatbot\run.bat

[Requirements]
- Windows 10 or higher
- Python 3.11
- Internet connection

[Troubleshooting]
- Install Python from: https://www.python.org/downloads/
- Disable antivirus temporarily if installation fails
"""
    
    with open(os.path.join(dist_folder, "README.txt"), "w", encoding="ascii") as f:
        f.write(readme_en)
    
    # 5. Create ZIP
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    zip_filename = f"KakaoOCRChatbot_Setup_{timestamp}.zip"
    
    with zipfile.ZipFile(zip_filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(dist_folder):
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, dist_folder)
                zipf.write(file_path, arcname)
    
    size_mb = os.path.getsize(zip_filename) / (1024 * 1024)
    
    print(f"\n[Complete] Installation package created!")
    print(f"File: {zip_filename}")
    print(f"Size: {size_mb:.2f} MB")
    print("\nDelivery methods:")
    print("1. USB drive")
    print("2. Cloud storage (Google Drive, Dropbox)")
    print("3. Email attachment")
    
    # Clean up old files
    old_files = [
        "KakaoOCRChatbot_Installer_20250805.zip",
        "kakao_chatbot_20250805_190712.zip"
    ]
    for old_file in old_files:
        if os.path.exists(old_file):
            os.remove(old_file)
            print(f"\nCleaned up: {old_file}")

if __name__ == "__main__":
    create_safe_installer()