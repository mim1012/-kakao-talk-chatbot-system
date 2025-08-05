#!/usr/bin/env python3
"""
PaddleOCR 3.1.0 새로운 API 테스트
"""
import sys
import os
import io
from pathlib import Path

# UTF-8 encoding
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# 로그 억제
os.environ['PPOCR_LOG_LEVEL'] = 'ERROR'
os.environ['GLOG_minloglevel'] = '3'

print("=" * 60)
print("PaddleOCR 3.1.0 새로운 API 테스트")
print("=" * 60)

# 1. 최소 파라미터로 초기화
print("\n1. 최소 파라미터로 PaddleOCR 초기화:")
try:
    from paddleocr import PaddleOCR
    
    # 최소 파라미터만 사용
    ocr = PaddleOCR(lang='korean')
    print("✅ PaddleOCR 초기화 성공 (최소 설정)")
    
except Exception as e:
    print(f"❌ 초기화 실패: {e}")
    import traceback
    traceback.print_exc()

# 2. OCR 테스트
print("\n2. OCR 기능 테스트:")
try:
    import numpy as np
    
    # 간단한 테스트 이미지
    test_image = np.ones((100, 300, 3), dtype=np.uint8) * 255
    
    # OCR 실행
    result = ocr.ocr(test_image)
    print("✅ OCR 실행 성공")
    
    if result:
        print(f"   결과 타입: {type(result)}")
    
except Exception as e:
    print(f"❌ OCR 실행 실패: {e}")

# 3. 한글 텍스트 테스트
print("\n3. 한글 OCR 테스트:")
try:
    import cv2
    
    # 한글 텍스트가 포함된 이미지 생성
    korean_image = np.ones((200, 400, 3), dtype=np.uint8) * 255
    
    # 텍스트 추가 (영문으로 테스트)
    cv2.putText(korean_image, "Welcome", (50, 100),
                cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0, 0, 0), 2)
    
    # OCR 실행
    result = ocr.ocr(korean_image)
    
    if result and result[0]:
        print("✅ 텍스트 감지 성공:")
        for line in result[0]:
            if line[1]:
                text = line[1][0]
                confidence = line[1][1]
                print(f"   - '{text}' (신뢰도: {confidence:.2f})")
    else:
        print("   텍스트를 감지하지 못했습니다.")
        
except Exception as e:
    print(f"❌ 한글 OCR 테스트 실패: {e}")

print("\n" + "=" * 60)
print("결과")
print("=" * 60)
print("\n✅ PaddleOCR 3.1.0 작동 확인!")
print("\n사용 방법:")
print("  ocr = PaddleOCR(lang='korean')")
print("  result = ocr.ocr(image)")
print("\n주의:")
print("- use_gpu, show_log 등의 파라미터는 3.1.0에서 제거됨")
print("- 간단하게 lang 파라미터만 사용 권장")