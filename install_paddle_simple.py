#!/usr/bin/env python3
"""
PaddleOCR 간단 설치 스크립트
"""
import subprocess
import sys

print("=" * 60)
print("PaddleOCR 설치 스크립트")
print("=" * 60)
print()

# Python 버전 확인
print(f"Python 버전: {sys.version}")
print(f"Python 경로: {sys.executable}")
print()

# Python 3.11 확인
if sys.version_info.major == 3 and sys.version_info.minor == 11:
    print("✅ Python 3.11 - 호환성 좋음")
    paddle_version = "2.5.2"
    ocr_version = "2.7.0.3"
elif sys.version_info.major == 3 and sys.version_info.minor == 13:
    print("⚠️ Python 3.13 - 최신 버전 사용")
    paddle_version = "2.6.1"  # 더 최신 버전 시도
    ocr_version = "2.7.3"
else:
    print(f"⚠️ Python {sys.version_info.major}.{sys.version_info.minor}")
    paddle_version = "2.5.2"
    ocr_version = "2.7.0.3"

print()
print("설치할 패키지:")
print(f"  - paddlepaddle=={paddle_version}")
print(f"  - paddleocr=={ocr_version}")
print()

# 설치 진행
answer = input("설치하시겠습니까? (y/n): ")
if answer.lower() == 'y':
    print()
    print("설치 중... (시간이 걸릴 수 있습니다)")
    
    # pip 업그레이드
    subprocess.run([sys.executable, "-m", "pip", "install", "--upgrade", "pip"])
    
    # PaddlePaddle 설치
    print(f"\nPaddlePaddle {paddle_version} 설치 중...")
    result = subprocess.run([sys.executable, "-m", "pip", "install", f"paddlepaddle=={paddle_version}"])
    
    if result.returncode != 0:
        print("⚠️ 특정 버전 설치 실패, 최신 버전 시도...")
        subprocess.run([sys.executable, "-m", "pip", "install", "paddlepaddle"])
    
    # PaddleOCR 설치
    print(f"\nPaddleOCR {ocr_version} 설치 중...")
    result = subprocess.run([sys.executable, "-m", "pip", "install", f"paddleocr=={ocr_version}"])
    
    if result.returncode != 0:
        print("⚠️ 특정 버전 설치 실패, 최신 버전 시도...")
        subprocess.run([sys.executable, "-m", "pip", "install", "paddleocr"])
    
    # 추가 패키지
    print("\n추가 의존성 설치 중...")
    subprocess.run([sys.executable, "-m", "pip", "install", "shapely", "pyclipper"])
    
    print()
    print("=" * 60)
    print("설치 완료!")
    print("=" * 60)
    
    # 테스트
    print("\n설치 확인 중...")
    try:
        import paddle
        print(f"✅ PaddlePaddle {paddle.__version__} 설치됨")
    except ImportError:
        print("❌ PaddlePaddle 설치 실패")
    
    try:
        from paddleocr import PaddleOCR
        print("✅ PaddleOCR import 성공")
    except ImportError:
        print("❌ PaddleOCR 설치 실패")
else:
    print("설치 취소됨")