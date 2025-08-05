#!/usr/bin/env python3
"""
PaddleOCR 설치 확인 스크립트
"""
import sys

print("PaddleOCR 설치 확인...")
print("-" * 40)

# 1. PaddlePaddle 확인
try:
    import paddle
    print(f"✅ PaddlePaddle {paddle.__version__} 설치됨")
except ImportError as e:
    print(f"❌ PaddlePaddle 설치 안됨: {e}")
    print("\n설치 명령: pip install paddlepaddle==2.5.2")

# 2. PaddleOCR 확인
try:
    from paddleocr import PaddleOCR
    print("✅ PaddleOCR import 성공")
    
    # 초기화 테스트
    print("\nPaddleOCR 초기화 테스트...")
    ocr = PaddleOCR(lang='korean')
    print("✅ PaddleOCR 초기화 성공!")
    
except ImportError as e:
    print(f"❌ PaddleOCR import 실패: {e}")
    print("\n설치 명령: pip install paddleocr==2.7.0.3")
except Exception as e:
    print(f"❌ PaddleOCR 초기화 실패: {e}")

print("\n" + "=" * 40)
print("테스트 완료!")

# 프로그램 실행 가능 여부
try:
    from paddleocr import PaddleOCR
    import paddle
    print("\n✅ 프로그램 실행 가능!")
    print("실행: python main.py")
except:
    print("\n⚠️ PaddleOCR 설치가 필요합니다.")
    print("설치: pip install paddlepaddle==2.5.2 paddleocr==2.7.0.3")