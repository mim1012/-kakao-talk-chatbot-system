#!/usr/bin/env python3
"""
병렬 처리 모니터링 - 더 빠른 캡처와 OCR
"""
import threading
import queue
import time
from concurrent.futures import ThreadPoolExecutor
import numpy as np
import mss

class ParallelMonitor:
    """병렬 처리로 성능 개선"""
    
    def __init__(self, grid_manager, ocr_service, max_workers=4):
        self.grid_manager = grid_manager
        self.ocr_service = ocr_service
        self.max_workers = max_workers
        
        # 3개의 큐로 작업 분리
        self.capture_queue = queue.Queue()
        self.ocr_queue = queue.Queue()
        self.action_queue = queue.Queue()
        
        # 스레드 풀
        self.capture_pool = ThreadPoolExecutor(max_workers=max_workers)
        self.ocr_pool = ThreadPoolExecutor(max_workers=2)
        
        self.running = False
        
    def start(self):
        """병렬 처리 시작"""
        self.running = True
        
        # 1. 캡처 스레드 (여러 개)
        for i in range(self.max_workers):
            threading.Thread(target=self._capture_worker, daemon=True).start()
            
        # 2. OCR 스레드 (2개)
        for i in range(2):
            threading.Thread(target=self._ocr_worker, daemon=True).start()
            
        # 3. 스케줄러 스레드 (셀 분배)
        threading.Thread(target=self._scheduler, daemon=True).start()
        
    def _scheduler(self):
        """셀을 캡처 큐에 분배"""
        while self.running:
            active_cells = [c for c in self.grid_manager.cells if c.can_be_triggered()]
            
            # 활성 셀들을 캡처 큐에 추가
            for cell in active_cells:
                self.capture_queue.put(cell)
                
            time.sleep(0.3)  # 스캔 주기
            
    def _capture_worker(self):
        """캡처 전담 워커"""
        with mss.mss() as sct:
            while self.running:
                try:
                    cell = self.capture_queue.get(timeout=0.1)
                    
                    # 빠른 캡처
                    x, y, w, h = cell.ocr_area
                    monitor = {"left": x, "top": y, "width": w, "height": h}
                    screenshot = sct.grab(monitor)
                    image = np.array(screenshot)
                    
                    # OCR 큐로 전달
                    self.ocr_queue.put((cell, image))
                    
                except queue.Empty:
                    continue
                    
    def _ocr_worker(self):
        """OCR 전담 워커"""
        while self.running:
            try:
                cell, image = self.ocr_queue.get(timeout=0.1)
                
                # OCR 실행
                result = self.ocr_service.perform_ocr_with_recovery(image, cell.id)
                
                # 트리거 확인
                if result.text and "들어왔습니다" in result.text:
                    self.action_queue.put((cell, result))
                    
            except queue.Empty:
                continue

# 사용 예시
"""
monitor = ParallelMonitor(grid_manager, ocr_service, max_workers=4)
monitor.start()

# 액션 큐에서 결과 가져오기
while True:
    cell, result = monitor.action_queue.get()
    # 자동화 실행
"""