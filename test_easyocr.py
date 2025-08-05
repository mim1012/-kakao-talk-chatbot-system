#!/usr/bin/env python3
"""
EasyOCR 테스트
"""
import sys
import numpy as np

print("=" * 60)
print("EasyOCR 테스트")
print("=" * 60)
print()

try:
    import easyocr
    print("✅ EasyOCR import 성공")
    
    print("\n한글 OCR Reader 초기화 중...")
    reader = easyocr.Reader(['ko', 'en'])
    print("✅ EasyOCR Reader 초기화 성공")
    
    # 간단한 테스트
    print("\n간단한 테스트 이미지 생성...")
    test_image = np.ones((100, 300, 3), dtype=np.uint8) * 255
    
    # OCR 실행
    result = reader.readtext(test_image)
    print("✅ OCR 실행 성공")
    
    print("\n" + "=" * 60)
    print("🎉 EasyOCR 설치 및 테스트 성공!")
    print("=" * 60)
    
except ImportError as e:
    print(f"❌ EasyOCR import 실패: {e}")
    print("\n설치 명령:")
    print("  pip install easyocr")
    
except Exception as e:
    print(f"❌ 오류: {e}")
    print("\nPyTorch 설치가 필요할 수 있습니다:")
    print("  pip install torch torchvision")