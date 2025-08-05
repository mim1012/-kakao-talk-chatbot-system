#!/usr/bin/env python3
"""디버그 모드로 테스트"""
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
from ocr.enhanced_ocr_service import EnhancedOCRService, OCRResult
from utils.suppress_output import suppress_stdout_stderr

print("=" * 60)
print("디버그 모드 테스트")
print("=" * 60)

# 설정 및 서비스 초기화
config = ConfigManager()
ocr_service = EnhancedOCRService(config)

# 테스트용 이미지 생성
print("\n1. 테스트 이미지 생성...")
test_image = np.ones((100, 400, 3), dtype=np.uint8) * 255  # 흰 배경

# 텍스트 추가 (OpenCV 사용)
font = cv2.FONT_HERSHEY_SIMPLEX
cv2.putText(test_image, "님이 들어왔습니다", (50, 50), font, 1.0, (0, 0, 0), 2)
cv2.imwrite("test_image.png", test_image)
print("✅ 테스트 이미지 생성 완료: test_image.png")

# OCR 수행
print("\n2. OCR 수행...")
with suppress_stdout_stderr():
    result = ocr_service.perform_ocr_with_recovery(test_image, "test_cell")

if result and result.text:
    print(f"✅ OCR 결과: '{result.text}' (신뢰도: {result.confidence:.2f})")
    
    # 트리거 패턴 확인
    is_trigger = ocr_service.check_trigger_patterns(result)
    print(f"트리거 패턴 매칭: {'✅ 성공' if is_trigger else '❌ 실패'}")
    
    # 디버그 정보
    if hasattr(result, 'debug_info'):
        print("\n디버그 정보:")
        debug = result.debug_info
        if 'all_results' in debug:
            print(f"  - 전체 결과 수: {len(debug['all_results'])}")
            for i, res in enumerate(debug['all_results'][:5]):
                print(f"    [{i}] '{res.get('text', '')}' (신뢰도: {res.get('confidence', 0):.2f})")
else:
    print("❌ OCR 결과 없음")

# 저장된 스크린샷 확인
print("\n3. 저장된 스크린샷 확인...")
debug_dir = Path("screenshots/debug")
if debug_dir.exists():
    test_screenshots = list(debug_dir.glob("TEST_*.png"))
    print(f"테스트 스크린샷: {len(test_screenshots)}개")
    
    # 최근 5개 표시
    for img_path in sorted(test_screenshots)[-5:]:
        print(f"  - {img_path.name}")

print("\n" + "=" * 60)
print("디버깅 팁:")
print("1. screenshots/debug/ 폴더에서 TEST_로 시작하는 파일 확인")
print("2. 콘솔 로그에서 '🧪 테스트 모드' 메시지 확인")
print("3. OCR 결과가 없다면 이미지 위치와 크기 확인")
print("=" * 60)