#!/usr/bin/env python3
"""
영역별 전담 모니터링 - 각 영역을 독립적으로 감시
"""
import threading
import time
import mss
import numpy as np

class ZoneMonitor:
    """특정 영역만 전담하는 모니터"""
    
    def __init__(self, cells, ocr_service, action_queue):
        self.cells = cells  # 담당할 셀들 (예: 3~5개)
        self.ocr_service = ocr_service
        self.action_queue = action_queue
        self.running = False
        
    def start(self):
        """독립적으로 실행"""
        self.running = True
        threading.Thread(target=self._monitor_loop, daemon=True).start()
        
    def _monitor_loop(self):
        """담당 영역만 계속 감시"""
        with mss.mss() as sct:
            while self.running:
                for cell in self.cells:
                    if not cell.can_be_triggered():
                        continue
                        
                    # 캡처
                    x, y, w, h = cell.ocr_area
                    monitor = {"left": x, "top": y, "width": w, "height": h}
                    screenshot = sct.grab(monitor)
                    image = np.array(screenshot)
                    
                    # OCR
                    result = self.ocr_service.perform_ocr_with_recovery(image, cell.id)
                    
                    # 즉시 확인
                    if result.text and "들어왔습니다" in result.text:
                        self.action_queue.put((cell, result))
                        cell.set_cooldown(5.0)
                        
                time.sleep(0.1)  # 짧은 대기

class MultiZoneMonitor:
    """전체 화면을 여러 구역으로 나눠서 감시"""
    
    def __init__(self, grid_manager, ocr_service, zones=3):
        self.grid_manager = grid_manager
        self.ocr_service = ocr_service
        self.zones = zones
        self.action_queue = queue.Queue()
        self.monitors = []
        
    def start(self):
        """영역별로 모니터 시작"""
        cells_per_zone = len(self.grid_manager.cells) // self.zones
        
        for i in range(self.zones):
            start_idx = i * cells_per_zone
            end_idx = start_idx + cells_per_zone
            if i == self.zones - 1:  # 마지막 구역
                end_idx = len(self.grid_manager.cells)
                
            zone_cells = self.grid_manager.cells[start_idx:end_idx]
            monitor = ZoneMonitor(zone_cells, self.ocr_service, self.action_queue)
            monitor.start()
            self.monitors.append(monitor)
            
            print(f"Zone {i+1}: 셀 {start_idx}~{end_idx-1} 담당")

# 사용 예시
"""
# 15개 셀을 3개 구역으로 나눔
# Zone 1: 셀 0~4
# Zone 2: 셀 5~9  
# Zone 3: 셀 10~14
multi_monitor = MultiZoneMonitor(grid_manager, ocr_service, zones=3)
multi_monitor.start()
"""