#!/usr/bin/env python3
"""
NumPy/SciPy 호환성 문제 해결 스크립트
"""
import subprocess
import sys

print("=" * 60)
print("NumPy/SciPy 호환성 수정")
print("=" * 60)
print()

print("Python 버전:", sys.version)
print()

# 호환 버전 조합
if sys.version_info.minor == 11:  # Python 3.11
    numpy_version = "1.26.0"
    scipy_version = "1.11.4"
    scikit_version = "0.22.0"
    opencv_version = "4.8.1.78"
else:
    numpy_version = "1.24.3"
    scipy_version = "1.10.1"
    scikit_version = "0.22.0"
    opencv_version = "4.6.0.66"

packages_to_remove = ["numpy", "scipy", "scikit-image"]
packages_to_install = [
    f"numpy=={numpy_version}",
    f"scipy=={scipy_version}",
    f"scikit-image=={scikit_version}",
    f"opencv-python=={opencv_version}",
    f"opencv-contrib-python=={opencv_version}"
]

print("제거할 패키지:")
for pkg in packages_to_remove:
    print(f"  - {pkg}")
print()

print("설치할 패키지:")
for pkg in packages_to_install:
    print(f"  - {pkg}")
print()

# 제거
print("기존 패키지 제거 중...")
for pkg in packages_to_remove:
    subprocess.run([sys.executable, "-m", "pip", "uninstall", pkg, "-y"], 
                  capture_output=True)
print("제거 완료")
print()

# 설치
print("호환 버전 설치 중...")
for pkg in packages_to_install:
    print(f"설치 중: {pkg}")
    result = subprocess.run([sys.executable, "-m", "pip", "install", pkg], 
                          capture_output=True, text=True)
    if result.returncode == 0:
        print(f"  ✅ {pkg} 설치 완료")
    else:
        print(f"  ❌ {pkg} 설치 실패")
        print(result.stderr)

print()
print("=" * 60)
print("테스트 중...")
print("=" * 60)
print()

# 테스트
try:
    import numpy
    print(f"✅ NumPy {numpy.__version__} 로드 성공")
except Exception as e:
    print(f"❌ NumPy 로드 실패: {e}")

try:
    import scipy
    print(f"✅ SciPy {scipy.__version__} 로드 성공")
except Exception as e:
    print(f"❌ SciPy 로드 실패: {e}")

try:
    import cv2
    print(f"✅ OpenCV {cv2.__version__} 로드 성공")
except Exception as e:
    print(f"❌ OpenCV 로드 실패: {e}")

try:
    from paddleocr import PaddleOCR
    print("✅ PaddleOCR import 성공!")
    
    print("\n초기화 테스트 중...")
    ocr = PaddleOCR(lang='korean')
    print("✅ PaddleOCR 초기화 성공!")
    
    print("\n🎉 모든 호환성 문제가 해결되었습니다!")
    print("실행: python main.py")
    
except Exception as e:
    print(f"❌ PaddleOCR 테스트 실패: {e}")
    print("\n추가 디버깅이 필요합니다.")