#!/usr/bin/env python3
"""
PyInstaller를 사용한 EXE 파일 생성 스크립트
"""
import os
import subprocess
import shutil

def create_exe():
    """EXE 파일 생성"""
    
    print("[EXE 생성] PyInstaller 설치 확인...")
    try:
        import PyInstaller
    except ImportError:
        print("[설치] PyInstaller 설치 중...")
        subprocess.run(["pip", "install", "pyinstaller"], check=True)
    
    print("\n[EXE 생성] 실행 파일 생성 중...")
    
    # PyInstaller 명령어
    cmd = [
        "pyinstaller",
        "--onedir",  # 하나의 폴더로 패키징
        "--windowed",  # 콘솔 창 숨기기 (GUI만 표시)
        "--icon=icon.ico" if os.path.exists("icon.ico") else "",  # 아이콘 있으면 사용
        "--name=KakaoOCRChatbot",  # 실행 파일 이름
        "--add-data=config.json;.",  # config.json 포함
        "--add-data=src;src",  # src 폴더 포함
        "--hidden-import=paddleocr",  # PaddleOCR 명시적 포함
        "--hidden-import=PyQt5",  # PyQt5 명시적 포함
        "--collect-all=paddleocr",  # PaddleOCR 전체 수집
        "main.py"
    ]
    
    # 빈 문자열 제거
    cmd = [arg for arg in cmd if arg]
    
    try:
        subprocess.run(cmd, check=True)
        print("\n[성공] EXE 파일 생성 완료!")
        print(f"[위치] dist/KakaoOCRChatbot/ 폴더")
        
        # 추가 파일 복사
        if os.path.exists("dist/KakaoOCRChatbot"):
            # 설정 파일 복사
            shutil.copy2("config.json", "dist/KakaoOCRChatbot/")
            
            # 실행 배치 파일 생성
            with open("dist/KakaoOCRChatbot/실행.bat", "w", encoding="utf-8") as f:
                f.write("@echo off\nKakaoOCRChatbot.exe\npause")
            
            print("[OK] 추가 파일 복사 완료")
            
    except subprocess.CalledProcessError as e:
        print(f"[오류] EXE 생성 실패: {e}")
        print("\n대안: 배포 패키지(ZIP)를 사용하세요.")

if __name__ == "__main__":
    create_exe()