#!/usr/bin/env python3
"""
실제 OCR을 위한 필수 패키지 설치
"""
import subprocess
import sys

def install_packages():
    """필수 패키지 설치"""
    packages = [
        "numpy>=1.24.0",
        "opencv-python>=4.8.0",
        "paddlepaddle>=2.5.0",
        "paddleocr>=2.7.0",
        "Pillow>=10.0.0"
    ]
    
    print("필수 패키지 설치 중...")
    
    for package in packages:
        print(f"설치 중: {package}")
        try:
            subprocess.check_call([
                sys.executable, "-m", "pip", "install", 
                package, "--upgrade", "--force-reinstall"
            ])
            print(f"OK {package} 설치 완료")
        except subprocess.CalledProcessError:
            print(f"FAIL {package} 설치 실패")
    
    print("\n패키지 설치 완료!")

if __name__ == "__main__":
    install_packages()
