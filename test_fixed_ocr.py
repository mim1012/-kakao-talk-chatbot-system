#!/usr/bin/env python3
"""
PaddleOCR 수정된 파라미터로 테스트
"""
import os
import sys

# 환경변수 설정
os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'
os.environ['CUDA_VISIBLE_DEVICES'] = '-1'

def test_fixed_paddleocr():
    """수정된 PaddleOCR 파라미터로 테스트"""
    print("PaddleOCR 파라미터 수정 테스트...")
    
    try:
        import numpy as np
        print(f"numpy: {np.__version__}")
        
        import cv2
        print(f"OpenCV: {cv2.__version__}")
        
        import paddleocr
        print("PaddleOCR import: OK")
        
        # 수정된 파라미터로 초기화
        print("PaddleOCR 초기화 중...")
        ocr = paddleocr.PaddleOCR(use_textline_orientation=True, lang='korean')
        print("✅ PaddleOCR 초기화 성공!")
        
        # 테스트 이미지로 OCR 실행
        test_img = np.ones((100, 300, 3), dtype=np.uint8) * 255
        result = ocr.ocr(test_img, cls=True)
        print("✅ 실제 OCR 테스트 성공!")
        print(f"OCR 결과: {result}")
        
        return True
        
    except Exception as e:
        print(f"❌ 테스트 실패: {e}")
        return False

if __name__ == "__main__":
    success = test_fixed_paddleocr()
    sys.exit(0 if success else 1)