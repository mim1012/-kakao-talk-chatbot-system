#!/usr/bin/env python3
"""
PaddleOCR 모든 의존성 설치 스크립트
"""
import subprocess
import sys

print("=" * 60)
print("PaddleOCR 의존성 설치")
print("=" * 60)
print()

# 필수 패키지 목록
packages = [
    "opencv-contrib-python==4.6.0.66",
    "Pillow",
    "attrdict",
    "beautifulsoup4",
    "cython",
    "fire>=0.3.0",
    "fonttools>=4.24.0",
    "imgaug",
    "lmdb",
    "lxml",
    "openpyxl",
    "premailer",
    "python-docx",
    "rapidfuzz",
    "scikit-image",
    "tqdm",
    "visualdl",
    "scipy",
    "matplotlib",
    "cssselect",
    "cssutils",
    # PyMuPDF 대체
    "pdf2docx --no-deps"
]

print("설치할 패키지:")
for pkg in packages:
    print(f"  - {pkg}")
print()

# 설치 진행
for i, package in enumerate(packages, 1):
    print(f"\n[{i}/{len(packages)}] {package} 설치 중...")
    if "pdf2docx" in package:
        # pdf2docx는 의존성 없이 설치
        result = subprocess.run([sys.executable, "-m", "pip", "install", "pdf2docx", "--no-deps"], 
                              capture_output=True, text=True)
    else:
        result = subprocess.run([sys.executable, "-m", "pip", "install", package], 
                              capture_output=True, text=True)
    
    if result.returncode == 0:
        print(f"  ✅ {package} 설치 완료")
    else:
        print(f"  ⚠️ {package} 설치 실패 (계속 진행)")

print("\n" + "=" * 60)
print("설치 완료! 테스트 중...")
print("=" * 60)
print()

# 테스트
try:
    from paddleocr import PaddleOCR
    print("✅ PaddleOCR import 성공!")
    
    print("\n초기화 테스트...")
    ocr = PaddleOCR(lang='korean')
    print("✅ PaddleOCR 초기화 성공!")
    
    print("\n🎉 모든 설치가 완료되었습니다!")
    print("실행: python main.py")
    
except ImportError as e:
    print(f"❌ 아직 일부 패키지가 누락됨: {e}")
    print("\n수동 설치가 필요한 패키지를 확인하세요.")
except Exception as e:
    print(f"❌ 오류: {e}")