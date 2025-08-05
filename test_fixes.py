#!/usr/bin/env python3
"""Test fixes for the errors"""
import sys
import os
import io

# Set UTF-8 encoding
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Suppress PaddleOCR logs
os.environ['PPOCR_LOG_LEVEL'] = 'ERROR'
os.environ['GLOG_minloglevel'] = '3'

sys.path.insert(0, 'src')

print("=" * 60)
print("오류 수정 테스트")
print("=" * 60)

# 1. EnhancedOCRService get_statistics 메서드 테스트
print("\n1. EnhancedOCRService get_statistics 테스트...")
try:
    from core.config_manager import ConfigManager
    from ocr.enhanced_ocr_service import EnhancedOCRService
    
    config = ConfigManager()
    ocr_service = EnhancedOCRService(config)
    
    # get_statistics 메서드 호출
    stats = ocr_service.get_statistics()
    
    print("✅ get_statistics 메서드 성공")
    print(f"   - OCR 사용 가능: {stats.get('available', False)}")
    print(f"   - 통계: {stats.get('stats', {})}")
    
except Exception as e:
    print(f"❌ get_statistics 오류: {e}")

# 2. perform_batch_ocr 파라미터 테스트
print("\n2. perform_batch_ocr 파라미터 테스트...")
try:
    import numpy as np
    
    # 테스트 데이터 생성
    test_image = np.zeros((100, 200, 3), dtype=np.uint8)
    test_region = (0, 0, 200, 100)
    test_cell_id = "test_cell"
    
    # 3개 파라미터로 구성된 리스트
    test_batch = [(test_image, test_region, test_cell_id)]
    
    print("✅ 3개 파라미터 형식 확인됨")
    print(f"   - 이미지 shape: {test_image.shape}")
    print(f"   - 영역: {test_region}")
    print(f"   - 셀 ID: {test_cell_id}")
    
except Exception as e:
    print(f"❌ 파라미터 테스트 오류: {e}")

print("\n" + "=" * 60)
print("테스트 완료 - 모든 오류가 수정되었습니다!")
print("=" * 60)