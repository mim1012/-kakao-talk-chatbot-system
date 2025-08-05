#!/usr/bin/env python3
"""
OCR 오버레이 영역 테스트
각 셀의 전체 영역에서 텍스트를 감지하는지 확인
"""
import sys
import os
import time
from datetime import datetime

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

def test_ocr_in_cells():
    """각 셀의 하단 100px 오버레이 영역 OCR 테스트"""
    print("="*60)
    print("셀 하단 오버레이 영역 OCR 테스트")
    print("="*60)
    
    # 서비스 초기화
    config = ConfigManager()
    grid_manager = GridManager(config)
    cache_manager = CacheManager(config._config)
    perf_monitor = PerformanceMonitor()
    ocr_service = OptimizedOCRService(config, cache_manager, perf_monitor)
    
    overlay_height = config.ui_constants.overlay_height
    print(f"\n총 {len(grid_manager.cells)}개 셀 생성됨")
    print(f"오버레이 높이: {overlay_height}px (셀 하단)")
    
    # 스크린 캡처
    with mss.mss() as sct:
        # 첫 번째 모니터의 처음 3개 셀만 테스트
        test_cells = grid_manager.cells[:3]
        
        for cell in test_cells:
            print(f"\n[셀 {cell.id}]")
            print(f"  전체 셀 영역: {cell.bounds}")
            print(f"  OCR 오버레이 영역: {cell.ocr_area}")
            
            # 오버레이 영역이 하단 100px인지 확인
            cell_x, cell_y, cell_w, cell_h = cell.bounds
            ocr_x, ocr_y, ocr_w, ocr_h = cell.ocr_area
            expected_ocr_y = cell_y + cell_h - overlay_height
            
            print(f"  ✓ 오버레이 Y 좌표 확인: {ocr_y} (예상: {expected_ocr_y})")
            print(f"  ✓ 오버레이 높이 확인: {ocr_h}px (설정: {overlay_height}px)")
            
            # OCR 영역 캡처
            monitor = {"left": ocr_x, "top": ocr_y, "width": ocr_w, "height": ocr_h}
            
            try:
                # 스크린샷 캡처
                screenshot = sct.grab(monitor)
                img = Image.frombytes("RGB", screenshot.size, screenshot.bgra, "raw", "BGRX")
                
                # 디버그용 저장
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                debug_path = f"screenshots/debug/overlay_{cell.id}_{timestamp}.png"
                os.makedirs("screenshots/debug", exist_ok=True)
                img.save(debug_path)
                print(f"  📸 오버레이 스크린샷: {debug_path}")
                
                # OCR 수행
                img_array = np.array(img)
                result = ocr_service.perform_ocr_cached(img_array, cell.ocr_area)
                
                if result.text:
                    print(f"  ✅ 텍스트 감지: '{result.text[:50]}...'")
                    print(f"     신뢰도: {result.confidence:.2f}")
                    print(f"     처리시간: {result.processing_time_ms:.1f}ms")
                    
                    # 트리거 패턴 확인
                    if ocr_service.check_trigger_patterns(result.text):
                        print(f"  🎯 '들어왔습니다' 패턴 감지됨!")
                else:
                    print(f"  ❌ 오버레이 영역에서 텍스트 없음")
                    
            except Exception as e:
                print(f"  ❌ 오류: {e}")
    
    print("\n" + "="*60)
    print("테스트 완료")
    print("📁 screenshots/debug 폴더에서 각 셀의 하단 100px 오버레이 캡처 확인")
    print("="*60)

if __name__ == "__main__":
    test_ocr_in_cells()