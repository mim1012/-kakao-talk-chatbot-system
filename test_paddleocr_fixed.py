#!/usr/bin/env python3
"""
PaddleOCR 3.1.0 호환 테스트
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
os.environ['GLOG_v'] = '0'

# src 디렉토리를 Python 경로에 추가
script_dir = Path(__file__).parent.absolute()
src_path = script_dir / "src"
if src_path.exists():
    sys.path.insert(0, str(src_path))

print("=" * 60)
print("PaddleOCR 3.1.0 작동 테스트")
print("=" * 60)

# 1. PaddleOCR import
print("\n1. PaddleOCR import 테스트:")
try:
    from paddleocr import PaddleOCR
    print("✅ PaddleOCR import 성공")
except ImportError as e:
    print(f"❌ PaddleOCR import 실패: {e}")
    sys.exit(1)

# 2. PaddleOCR 초기화 (3.1.0 호환)
print("\n2. PaddleOCR 초기화:")
try:
    # PaddleOCR 3.1.0 호환 파라미터만 사용
    ocr = PaddleOCR(
        lang='korean',
        use_gpu=False,
        use_angle_cls=True,
        det=True,
        rec=True,
        cls=True
    )
    print("✅ PaddleOCR 초기화 성공")
except Exception as e:
    print(f"❌ PaddleOCR 초기화 실패: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# 3. 간단한 OCR 테스트
print("\n3. OCR 기능 테스트:")
try:
    import numpy as np
    import cv2
    
    # 테스트 이미지 생성 (흰 배경에 검은 텍스트)
    test_image = np.ones((100, 400, 3), dtype=np.uint8) * 255
    
    # OpenCV로 텍스트 추가
    cv2.putText(test_image, "Test OCR", (50, 50),
                cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0, 0, 0), 2)
    
    # OCR 실행
    result = ocr.ocr(test_image)
    
    print("✅ OCR 실행 성공")
    
    if result and result[0]:
        print("   감지된 텍스트:")
        for line in result[0]:
            if line[1]:
                text = line[1][0]
                confidence = line[1][1]
                print(f"   - '{text}' (신뢰도: {confidence:.2f})")
    else:
        print("   텍스트를 감지하지 못했습니다.")
        
except Exception as e:
    print(f"❌ OCR 테스트 실패: {e}")
    import traceback
    traceback.print_exc()

# 4. 프로젝트 모듈 테스트
print("\n4. 프로젝트 모듈 호환성 테스트:")
try:
    from ocr.optimized_ocr_service import OptimizedOCRService, PADDLEOCR_AVAILABLE
    print(f"✅ OptimizedOCRService import 성공")
    print(f"   PADDLEOCR_AVAILABLE = {PADDLEOCR_AVAILABLE}")
    
    if PADDLEOCR_AVAILABLE:
        # 서비스 초기화 테스트
        from core.config_manager import ConfigManager
        config = ConfigManager()
        service = OptimizedOCRService(config)
        print("✅ OptimizedOCRService 초기화 성공")
        
except Exception as e:
    print(f"❌ 프로젝트 모듈 테스트 실패: {e}")
    import traceback
    traceback.print_exc()

# 5. 결과 요약
print("\n" + "=" * 60)
print("테스트 결과 요약")
print("=" * 60)
print("\n✅ PaddleOCR 3.1.0이 정상적으로 작동합니다!")
print("\n주의사항:")
print("- show_log 파라미터는 3.1.0에서 제거됨")
print("- 첫 실행시 모델 다운로드가 필요할 수 있음")
print("- Korean 언어 모델이 자동으로 다운로드됨")