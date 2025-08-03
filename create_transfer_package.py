#!/usr/bin/env python3
"""필수 파일만 압축하는 스크립트"""
import os
import zipfile
from pathlib import Path

def create_transfer_package():
    """이전용 패키지 생성"""
    
    # 압축할 파일/폴더 목록
    files_to_include = [
        "main.py",
        "requirements.txt",
        "config.json",
        "setup_on_new_pc.py",
        "간단한_이전_가이드.txt"
    ]
    
    folders_to_include = [
        "src",
        "tools"
    ]
    
    # 제외할 패턴
    exclude_patterns = [
        "__pycache__",
        ".pyc",
        ".git",
        "venv",
        "new_venv",
        "backup"
    ]
    
    with zipfile.ZipFile("chatbot_transfer_package.zip", "w", zipfile.ZIP_DEFLATED) as zipf:
        # 개별 파일 추가
        for file in files_to_include:
            if os.path.exists(file):
                zipf.write(file, file)
                print(f"[OK] {file} 추가됨")
        
        # 폴더 추가
        for folder in folders_to_include:
            if os.path.exists(folder):
                for root, dirs, files in os.walk(folder):
                    # 제외할 디렉토리 필터링
                    dirs[:] = [d for d in dirs if not any(pattern in d for pattern in exclude_patterns)]
                    
                    for file in files:
                        # 제외할 파일 필터링
                        if not any(pattern in file for pattern in exclude_patterns):
                            file_path = os.path.join(root, file)
                            arcname = os.path.relpath(file_path)
                            zipf.write(file_path, arcname)
                
                print(f"[OK] {folder}/ 폴더 추가됨")
    
    print("\n[COMPLETE] chatbot_transfer_package.zip 생성 완료!")
    print("\n이전 방법:")
    print("1. 이 zip 파일을 새 컴퓨터로 복사")
    print("2. 압축 해제")
    print("3. python setup_on_new_pc.py 실행")
    print("4. run.bat 또는 python main.py 실행")

if __name__ == "__main__":
    create_transfer_package()