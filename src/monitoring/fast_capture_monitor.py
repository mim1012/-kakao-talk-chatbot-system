"""
고속 캡처 모니터링 스레드
전체 화면을 한 번에 캡처한 후 필요한 영역만 자르는 방식으로 성능 개선
"""

import time
import numpy as np
import mss
from datetime import datetime
from typing import List, Tuple, Optional
from PyQt5.QtCore import QThread, pyqtSignal

class FastCaptureMonitor(QThread):
    """전체 화면 캡처 방식의 고속 모니터"""
    
    # 시그널 정의
    cell_captured_signal = pyqtSignal(str, np.ndarray, float)  # cell_id, image, timestamp
    status_signal = pyqtSignal(str)  # status message
    
    def __init__(self, cells, monitor_index=1):
        super().__init__()
        self.cells = cells
        self.monitor_index = monitor_index
        self.running = False
        self._last_capture = None
        self._last_capture_time = 0
        
    def run(self):
        """메인 캡처 루프"""
        self.running = True
        self.status_signal.emit("고속 캡처 모니터 시작")
        
        with mss.mss() as sct:
            monitor = sct.monitors[self.monitor_index]
            
            while self.running:
                try:
                    capture_start = time.perf_counter()
                    
                    # 전체 화면 캡처 (캐싱 활용)
                    current_time = time.time()
                    if self._last_capture is None or (current_time - self._last_capture_time) > 0.05:
                        # 50ms마다만 새로 캡처
                        screenshot = sct.grab(monitor)
                        self._last_capture = np.array(screenshot)
                        self._last_capture_time = current_time
                    
                    full_image = self._last_capture
                    
                    # 각 셀 영역 자르기 및 전달
                    for cell in self.cells:
                        if not cell.can_be_triggered():
                            continue
                        
                        x, y, w, h = cell.ocr_area
                        
                        # 화면 경계 체크
                        if x < 0 or y < 0:
                            continue
                        if x + w > full_image.shape[1] or y + h > full_image.shape[0]:
                            continue
                        
                        # 영역 자르기
                        cropped = full_image[y:y+h, x:x+w].copy()
                        
                        # 시그널 발생
                        self.cell_captured_signal.emit(
                            cell.id,
                            cropped,
                            time.perf_counter()
                        )
                    
                    # 처리 시간 계산
                    elapsed = (time.perf_counter() - capture_start) * 1000
                    
                    # 디버그 (10초마다)
                    if int(current_time) % 10 == 0 and int(current_time) != getattr(self, '_last_debug', 0):
                        self._last_debug = int(current_time)
                        self.status_signal.emit(f"캡처 성능: {elapsed:.1f}ms ({len(self.cells)}개 셀)")
                    
                    # 적응형 대기
                    if elapsed < 50:  # 50ms 미만이면 대기
                        time.sleep((50 - elapsed) / 1000)
                    
                except Exception as e:
                    self.status_signal.emit(f"캡처 오류: {e}")
                    time.sleep(0.1)
    
    def stop(self):
        """모니터 중지"""
        self.running = False

class OptimizedCaptureEngine:
    """최적화된 캡처 엔진"""
    
    def __init__(self, cells_per_monitor=15):
        self.cells_per_monitor = cells_per_monitor
        self.monitors = []
        self._cache = {}
        self._cache_time = {}
        self.cache_duration = 0.05  # 50ms 캐시
        
    def capture_batch(self, cells) -> List[Tuple[str, np.ndarray]]:
        """배치 캡처 수행"""
        results = []
        current_time = time.time()
        
        with mss.mss() as sct:
            # 모니터별로 그룹화
            monitor_groups = {}
            for cell in cells:
                # 모니터 인덱스 계산 (cell.id 기반)
                if 'monitor_0' in cell.id:
                    monitor_idx = 1
                elif 'monitor_1' in cell.id:
                    monitor_idx = 2 if len(sct.monitors) > 2 else 1
                else:
                    monitor_idx = 1
                
                if monitor_idx not in monitor_groups:
                    monitor_groups[monitor_idx] = []
                monitor_groups[monitor_idx].append(cell)
            
            # 각 모니터별로 전체 화면 캡처
            for monitor_idx, group_cells in monitor_groups.items():
                # 캐시 확인
                cache_key = f"monitor_{monitor_idx}"
                if (cache_key in self._cache and 
                    cache_key in self._cache_time and
                    (current_time - self._cache_time[cache_key]) < self.cache_duration):
                    # 캐시된 이미지 사용
                    full_image = self._cache[cache_key]
                else:
                    # 새로 캡처
                    monitor = sct.monitors[monitor_idx]
                    screenshot = sct.grab(monitor)
                    full_image = np.array(screenshot)
                    
                    # 캐시 저장
                    self._cache[cache_key] = full_image
                    self._cache_time[cache_key] = current_time
                
                # 각 셀 영역 자르기
                for cell in group_cells:
                    x, y, w, h = cell.ocr_area
                    
                    # 상대 좌표로 변환 (모니터 기준)
                    if monitor_idx == 2:
                        # 두 번째 모니터의 경우 x 좌표 조정
                        primary_width = sct.monitors[1]['width']
                        x = x - primary_width if x >= primary_width else x
                    
                    # 경계 체크
                    if x < 0 or y < 0:
                        continue
                    if x + w > full_image.shape[1] or y + h > full_image.shape[0]:
                        continue
                    
                    # 영역 자르기
                    cropped = full_image[y:y+h, x:x+w].copy()
                    results.append((cell.id, cropped))
        
        return results
    
    def clear_cache(self):
        """캐시 초기화"""
        self._cache.clear()
        self._cache_time.clear()