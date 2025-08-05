#!/usr/bin/env python3
"""
PaddleOCR 클린 설치 스크립트
"""
import subprocess
import sys
import os

print("=" * 60)
print("PaddleOCR 클린 설치")
print("=" * 60)
print()

# 1. 기존 제거
print("[1] 기존 PaddleOCR 제거...")
subprocess.run([sys.executable, "-m", "pip", "uninstall", "paddleocr", "-y"], capture_output=True)
subprocess.run([sys.executable, "-m", "pip", "uninstall", "paddleocr", "-y"], capture_output=True)
print("제거 완료")

# 2. 필수 패키지 확인
print("\n[2] 필수 패키지 설치...")
essential_packages = [
    "numpy==1.26.0",
    "scipy==1.11.4",
    "opencv-python==4.8.1.78",
    "Pillow",
    "shapely",
    "pyclipper",
]

for pkg in essential_packages:
    print(f"설치 중: {pkg}")
    subprocess.run([sys.executable, "-m", "pip", "install", pkg], capture_output=True)

# 3. PaddleOCR 다운로드 방법 선택
print("\n[3] PaddleOCR 설치 방법:")
print("1. GitHub에서 최신 버전 (권장)")
print("2. pip에서 안정 버전")
print("3. 로컬 소스에서 설치")

choice = input("\n선택 (1/2/3) [기본값: 1]: ").strip() or "1"

if choice == "1":
    print("\nGitHub에서 설치 중...")
    # GitHub에서 직접 설치
    result = subprocess.run([
        sys.executable, "-m", "pip", "install",
        "git+https://github.com/PaddlePaddle/PaddleOCR.git@release/2.7"
    ])
    
    if result.returncode != 0:
        print("GitHub 설치 실패, pip 버전 시도...")
        subprocess.run([sys.executable, "-m", "pip", "install", "paddleocr>=2.0.1", "--no-deps"])
        
elif choice == "2":
    print("\npip에서 설치 중...")
    subprocess.run([sys.executable, "-m", "pip", "install", "paddleocr>=2.0.1", "--no-deps"])
    
elif choice == "3":
    print("\n로컬 소스 설치 방법:")
    print("1. https://github.com/PaddlePaddle/PaddleOCR 에서 ZIP 다운로드")
    print("2. 압축 해제")
    print("3. 해당 폴더에서: pip install -e .")
    print("\n수동으로 진행하세요.")
    sys.exit(0)

# 4. 추가 의존성
print("\n[4] 추가 의존성 설치...")
additional = [
    "scikit-image",
    "imgaug", 
    "lmdb",
    "attrdict",
    "beautifulsoup4",
    "rapidfuzz",
    "tqdm",
    "lxml",
    "premailer",
    "openpyxl"
]

for pkg in additional:
    subprocess.run([sys.executable, "-m", "pip", "install", pkg], capture_output=True)
    print(f"✓ {pkg}")

# 5. 테스트
print("\n[5] 테스트...")
print("-" * 40)

try:
    from paddleocr import PaddleOCR
    print("✅ PaddleOCR import 성공!")
    
    print("\n초기화 테스트...")
    ocr = PaddleOCR(lang='korean')
    print("✅ PaddleOCR 초기화 성공!")
    
    print("\n🎉 설치 완료!")
    print("실행: python main.py")
    
except Exception as e:
    print(f"❌ 오류: {e}")
    print("\n해결 방법:")
    print("1. GitHub에서 ZIP 다운로드: https://github.com/PaddlePaddle/PaddleOCR")
    print("2. 압축 해제 후 해당 폴더에서: pip install -e .")
    print("3. 또는 다른 OCR 라이브러리 사용 (EasyOCR, Tesseract 등)")