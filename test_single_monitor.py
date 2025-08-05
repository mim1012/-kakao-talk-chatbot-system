#!/usr/bin/env python3
"""
싱글 모니터 OCR 테스트
"들어왔습니다"를 화면에 띄우고 감지되는지 확인
"""
import sys
import os
import time

# 프로젝트 경로 추가
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from core.config_manager import ConfigManager
from core.grid_manager import GridManager
from ocr.optimized_ocr_service import OptimizedOCRService
from core.cache_manager import CacheManager
from monitoring.performance_monitor import PerformanceMonitor
import mss
import numpy as np
from PIL import Image

def test_single_monitor():
    """싱글 모니터에서 첫 3개 셀 테스트"""
    print("="*60)
    print("싱글 모니터 OCR 감지 테스트")
    print("="*60)
    
    # 서비스 초기화
    config = ConfigManager()
    grid_manager = GridManager(config)
    cache_manager = CacheManager(config._config)
    perf_monitor = PerformanceMonitor()
    ocr_service = OptimizedOCRService(config, cache_manager, perf_monitor)
    
    # 첫 번째 모니터의 활성 셀만 필터링
    monitor_0_cells = [cell for cell in grid_manager.cells if cell.monitor_index == 0]
    test_cells = monitor_0_cells[:3]  # 첫 3개 셀만 테스트
    
    print(f"모니터 0의 첫 3개 셀 테스트:")
    for cell in test_cells:
        print(f"  셀 {cell.id}: OCR 영역 {cell.ocr_area}")
    
    print("\n🔍 5초 후 OCR 스캔 시작...")
    print("💡 테스트하려면 화면 어딘가에 '들어왔습니다' 텍스트를 표시하세요")
    time.sleep(5)
    
    # 10번 반복 테스트
    for i in range(10):
        print(f"\n[스캔 {i+1}/10]")
        
        with mss.mss() as sct:
            for cell in test_cells:
                # OCR 영역 캡처
                x, y, w, h = cell.ocr_area
                monitor = {"left": x, "top": y, "width": w, "height": h}
                
                try:
                    # 스크린샷 캡처
                    screenshot = sct.grab(monitor)
                    img = Image.frombytes("RGB", screenshot.size, screenshot.bgra, "raw", "BGRX")
                    img_array = np.array(img)
                    
                    # OCR 수행
                    result = ocr_service.perform_ocr_cached(img_array, cell.ocr_area)
                    
                    if result.text:
                        print(f"  셀 {cell.id}: '{result.text[:50]}'")
                        
                        # 트리거 패턴 확인
                        if ocr_service.check_trigger_patterns(result.text):
                            print(f"  🎯🎯🎯 '들어왔습니다' 패턴 감지됨! 셀 {cell.id}")
                            print(f"       텍스트: '{result.text}'")
                            print(f"       신뢰도: {result.confidence:.2f}")
                    else:
                        print(f"  셀 {cell.id}: 텍스트 없음")
                        
                except Exception as e:
                    print(f"  셀 {cell.id}: 오류 - {e}")
        
        time.sleep(2)  # 2초 간격
    
    print("\n" + "="*60)
    print("테스트 완료")
    print("="*60)

if __name__ == "__main__":
    test_single_monitor()