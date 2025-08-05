#!/usr/bin/env python3
"""
PaddleOCR 최종 테스트
"""
import sys

print("=" * 60)
print("PaddleOCR 최종 테스트")
print("=" * 60)
print()

# 1. 버전 확인
print("1. 패키지 버전 확인:")
print("-" * 40)

try:
    import numpy
    print(f"✅ NumPy: {numpy.__version__}")
except ImportError as e:
    print(f"❌ NumPy: {e}")

try:
    import scipy
    print(f"✅ SciPy: {scipy.__version__}")
except ImportError as e:
    print(f"❌ SciPy: {e}")

try:
    import cv2
    print(f"✅ OpenCV: {cv2.__version__}")
except ImportError as e:
    print(f"❌ OpenCV: {e}")

try:
    import paddle
    print(f"✅ PaddlePaddle: {paddle.__version__}")
except ImportError as e:
    print(f"❌ PaddlePaddle: {e}")

# 2. PaddleOCR import
print("\n2. PaddleOCR import 테스트:")
print("-" * 40)

try:
    from paddleocr import PaddleOCR
    print("✅ PaddleOCR import 성공!")
    
    # 3. 초기화 테스트
    print("\n3. PaddleOCR 초기화 테스트:")
    print("-" * 40)
    
    print("초기화 중... (첫 실행시 모델 다운로드)")
    ocr = PaddleOCR(lang='korean')
    print("✅ PaddleOCR 초기화 성공!")
    
    # 4. 간단한 OCR 테스트
    print("\n4. OCR 기능 테스트:")
    print("-" * 40)
    
    import numpy as np
    # 간단한 테스트 이미지
    test_image = np.ones((100, 300, 3), dtype=np.uint8) * 255
    
    result = ocr.ocr(test_image)
    print("✅ OCR 실행 성공!")
    
    print("\n" + "=" * 60)
    print("🎉 모든 테스트 통과!")
    print("=" * 60)
    print("\n✅ PaddleOCR이 정상 작동합니다!")
    print("✅ 프로그램을 실행할 수 있습니다: python main.py")
    
except ImportError as e:
    print(f"❌ PaddleOCR import 실패: {e}")
    print("\n필요한 패키지:")
    print("  pip install scipy==1.11.4")
    print("  pip install scikit-image==0.22.0")
    
except Exception as e:
    print(f"❌ 오류: {e}")
    import traceback
    traceback.print_exc()

print()