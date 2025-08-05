#!/usr/bin/env python3
"""OCR 감지 테스트"""
import sys
import os
import io
import cv2
import numpy as np
from pathlib import Path

# UTF-8 설정
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# 환경 변수 설정
os.environ['PPOCR_LOG_LEVEL'] = 'ERROR'
os.environ['GLOG_minloglevel'] = '3'

sys.path.insert(0, 'src')

from core.config_manager import ConfigManager
from ocr.enhanced_ocr_service import EnhancedOCRService
from utils.suppress_output import suppress_stdout_stderr

print("=" * 60)
print("OCR 감지 테스트")
print("=" * 60)

# 설정 및 서비스 초기화
config = ConfigManager()
ocr_service = EnhancedOCRService(config)

# 저장된 스크린샷 확인
debug_dir = Path("screenshots/debug")
if debug_dir.exists():
    screenshots = list(debug_dir.glob("*.png"))
    print(f"\n찾은 스크린샷: {len(screenshots)}개")
    
    # 최근 5개 이미지만 테스트
    for img_path in screenshots[-5:]:
        print(f"\n테스트 이미지: {img_path.name}")
        
        # 이미지 로드
        image = cv2.imread(str(img_path))
        if image is None:
            print("   ❌ 이미지 로드 실패")
            continue
            
        print(f"   이미지 크기: {image.shape}")
        
        # OCR 수행
        with suppress_stdout_stderr():
            result = ocr_service.perform_ocr_with_recovery(image, img_path.stem)
        
        if result and result.text:
            print(f"   📝 OCR 결과: '{result.text}' (신뢰도: {result.confidence:.2f})")
            
            # 트리거 패턴 확인
            is_trigger = ocr_service.check_trigger_patterns(result)
            if is_trigger:
                print(f"   🎯 트리거 패턴 감지됨!")
            else:
                print(f"   ❌ 트리거 패턴 매칭 안됨")
        else:
            print(f"   ⭕ 텍스트 없음")

# 직접 테스트 텍스트
print("\n\n=== 트리거 패턴 직접 테스트 ===")
test_texts = [
    "님이 들어왔습니다",
    "들어왔습니다",
    "입장하셨습니다",
    "참여하셨습니다",
    "들머왔습니다",  # OCR 오류 시뮬레이션
]

from ocr.enhanced_ocr_service import OCRResult

for text in test_texts:
    # OCRResult 객체 생성
    test_result = OCRResult(text, 0.95)
    
    is_match = ocr_service.check_trigger_patterns(test_result)
    if is_match:
        print(f"✅ '{text}' → 트리거 감지됨")
    else:
        print(f"❌ '{text}' → 트리거 감지 안됨")

print("\n" + "=" * 60)