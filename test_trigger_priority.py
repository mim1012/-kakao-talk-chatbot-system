#!/usr/bin/env python3
"""트리거 우선순위 테스트"""
import sys
import os
import io

# UTF-8 설정
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# 환경 변수 설정
os.environ['PPOCR_LOG_LEVEL'] = 'ERROR'
os.environ['GLOG_minloglevel'] = '3'

sys.path.insert(0, 'src')

print("=" * 60)
print("트리거 우선순위 테스트")
print("=" * 60)

# 최근 테스트 이미지 사용
test_image_path = "screenshots/debug/TEST_monitor_0_cell_1_3_150957.png"

if os.path.exists(test_image_path):
    print(f"✅ 테스트 이미지 발견: {test_image_path}")
    
    import cv2
    from core.config_manager import ConfigManager
    from ocr.enhanced_ocr_service import EnhancedOCRService
    from utils.suppress_output import suppress_stdout_stderr
    
    # 이미지 로드
    image = cv2.imread(test_image_path)
    print(f"이미지 크기: {image.shape}")
    
    # OCR 서비스 초기화
    config = ConfigManager()
    ocr_service = EnhancedOCRService(config)
    
    # OCR 수행
    print("\nOCR 수행 중...")
    with suppress_stdout_stderr():
        result = ocr_service.perform_ocr_with_recovery(image, "test_cell")
    
    if result and result.text:
        print(f"\n✅ 최종 OCR 결과: '{result.text}' (신뢰도: {result.confidence:.2f})")
        
        # 트리거 패턴 확인
        is_trigger = ocr_service.check_trigger_patterns(result)
        print(f"트리거 패턴 매칭: {'✅ 성공' if is_trigger else '❌ 실패'}")
        
        # 디버그 정보
        if hasattr(result, 'debug_info') and 'all_results' in result.debug_info:
            print("\n전체 감지 결과:")
            for i, res in enumerate(result.debug_info['all_results'][:10]):
                text = res.get('text', '')
                conf = res.get('confidence', 0)
                is_trigger = any(pattern in text for pattern in config.get('trigger_patterns', []))
                print(f"  [{i}] '{text}' (신뢰도: {conf:.2f}) {' ⭐ 트리거' if is_trigger else ''}")
    else:
        print("❌ OCR 결과 없음")
else:
    print(f"❌ 테스트 이미지를 찾을 수 없습니다: {test_image_path}")

print("\n" + "=" * 60)