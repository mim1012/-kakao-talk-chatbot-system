#!/usr/bin/env python3
"""
PaddleOCR 설치 확인
"""
import sys
import os

# 로그 억제
os.environ['GLOG_minloglevel'] = '3'

print("=" * 60)
print("PaddleOCR 설치 테스트")
print("=" * 60)
print()

# 1. 패키지 버전 확인
print("1. 패키지 버전:")
try:
    import numpy
    print(f"  NumPy: {numpy.__version__}")
except:
    print("  NumPy: 설치 안됨")

try:
    import scipy
    print(f"  SciPy: {scipy.__version__}")
except:
    print("  SciPy: 설치 안됨")

try:
    import paddle
    print(f"  PaddlePaddle: {paddle.__version__}")
except:
    print("  PaddlePaddle: 설치 안됨")

# 2. PaddleOCR import
print("\n2. PaddleOCR import 테스트:")
try:
    from paddleocr import PaddleOCR
    print("  ✅ import 성공")
    
    # 3. 초기화
    print("\n3. 초기화 테스트:")
    ocr = PaddleOCR(lang='korean')
    print("  ✅ 초기화 성공")
    
    print("\n" + "=" * 60)
    print("🎉 PaddleOCR 설치 성공!")
    print("프로그램 실행: python main.py")
    print("=" * 60)
    
except ImportError as e:
    print(f"  ❌ import 실패: {e}")
    print("\n누락된 패키지 설치 필요")
except Exception as e:
    print(f"  ❌ 오류: {e}")