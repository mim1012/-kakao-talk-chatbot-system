#!/usr/bin/env python3
"""
통합 카카오톡 챗봇 GUI 시스템
- 듀얼 모니터 30개 셀 지원
- PaddleOCR 한글 인식 최적화  
- 실시간 감지 및 자동 응답
- 향상된 오버레이 및 그리드 시스템
Python 3.11+ compatible
"""
from __future__ import annotations

import sys
import json
import time
from datetime import datetime
import queue
import threading
import logging
import os
from typing import Any, Tuple, List, Optional
import numpy as np
import mss
import pyautogui
import pyperclip

# PyAutoGUI 설정
pyautogui.FAILSAFE = True  # 안전 모드 활성화
pyautogui.PAUSE = 0.1      # 각 동작 사이 0.1초 대기

# 원격 데스크톱 감지
def is_remote_session():
    """원격 데스크톱 세션인지 확인"""
    try:
        import os
        # 환경 변수 확인
        if os.environ.get('SESSIONNAME', '').startswith('RDP-'):
            return True
        # AnyDesk, TeamViewer 등 확인
        import psutil
        for proc in psutil.process_iter(['name']):
            pname = proc.info['name'].lower()
            if any(remote in pname for remote in ['anydesk', 'teamviewer', 'rustdesk', 'rdpclip']):
                return True
    except:
        pass
    return False

# Win32 자동화 모듈 import
IS_REMOTE = is_remote_session()
if IS_REMOTE:
    print("원격 데스크톱 환경 감지됨!")
    
# 원격 환경이면 특별 처리
if IS_REMOTE:
    try:
        from src.utils.remote_automation import automation as win32_auto
        WIN32_AVAILABLE = True
        print("[OK] 원격 데스크톱 자동화 모듈 로드됨")
    except ImportError:
        win32_auto = None
        WIN32_AVAILABLE = False
        print("[WARN] 원격 자동화 모듈 로드 실패")
else:
    try:
        # 먼저 SendInput API 시도 (가장 신뢰할 수 있음)
        from src.utils.sendinput_automation import automation as win32_auto
        WIN32_AVAILABLE = True
        print("[OK] SendInput 자동화 모듈 로드됨")
    except ImportError:
        try:
            # 다음으로 direct_win32 시도 (ctypes만 사용)
            from src.utils.direct_win32 import automation as win32_auto
            WIN32_AVAILABLE = True
            print("[OK] Direct Win32 자동화 모듈 로드됨")
        except ImportError:
            try:
                # 마지막으로 pywin32 기반 모듈 시도
                from src.utils.win32_automation import automation as win32_auto
                WIN32_AVAILABLE = True
                print("[OK] PyWin32 자동화 모듈 로드됨")
            except ImportError:
                win32_auto = None
                WIN32_AVAILABLE = False
                print("[WARN] Win32 자동화 모듈을 불러올 수 없습니다")
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass

# 변화 감지 모듈 import
try:
    from src.monitoring.change_detection import ChangeDetectionMonitor
    CHANGE_DETECTION_AVAILABLE = True
except ImportError:
    CHANGE_DETECTION_AVAILABLE = False
    print("[WARN] 변화 감지 모듈을 사용할 수 없습니다")

# 최적화된 병렬 모니터 import
try:
    from src.monitoring.optimized_parallel_monitor import OptimizedParallelMonitor, MonitoringOrchestrator
    from src.monitoring.adaptive_monitor import AdaptivePriorityManager
    PARALLEL_MONITOR_AVAILABLE = True
except ImportError:
    PARALLEL_MONITOR_AVAILABLE = False
    print("[WARN] 병렬 모니터 모듈을 사용할 수 없습니다")

# Windows DPI 설정
if sys.platform == "win32":
    import ctypes
    ctypes.windll.shcore.SetProcessDpiAwareness(2)

# PyQt5 GUI
from PyQt5.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout, 
                            QLabel, QPushButton, QTextEdit, QSpinBox, QCheckBox, 
                            QGroupBox, QGridLayout, QScrollArea, QDoubleSpinBox,
                            QSlider, QComboBox, QTabWidget, QTableWidget, QTableWidgetItem,
                            QHeaderView)
from PyQt5.QtCore import Qt, QTimer, QThread, pyqtSignal, QRect, QMetaType
from PyQt5.QtGui import QColor
from PyQt5.QtGui import QPainter, QPen, QBrush, QColor, QFont, QTextCursor

# QTextCursor를 메타타입으로 등록 (스레드 간 통신을 위해)
try:
    # PyQt5에서는 대부분 자동으로 메타타입이 등록됨
    # 수동 등록이 필요한 경우를 위한 안전한 처리
    from PyQt5.QtCore import QMetaType
    # QTextCursor 타입이 이미 등록되어 있는지 확인
    cursor_type_id = QMetaType.type('QTextCursor')
    if cursor_type_id == 0:  # 등록되지 않은 경우
        # PyQt5는 대부분 자동으로 처리하므로 추가 작업 불필요
        pass
except Exception:
    # 메타타입 등록 관련 오류는 무시 (PyQt5가 자동 처리)
    pass

from screeninfo import get_monitors

# 서비스 임포트
from core.service_container import ServiceContainer
from core.grid_manager import GridCell, CellStatus
from core.cache_manager import CacheManager
from monitoring.performance_monitor import PerformanceMonitor, PerformanceOptimizer
# from ocr.enhanced_ocr_service import EnhancedOCRService  # ServiceContainer가 처리
from utils.suppress_output import suppress_stdout_stderr

# PaddleOCR
try:
    from paddleocr import PaddleOCR
    PADDLEOCR_AVAILABLE = True
except ImportError:
    PADDLEOCR_AVAILABLE = False
    print("[WARN] PaddleOCR not available")

@dataclass
class DetectionResult:
    """감지 결과 데이터"""
    cell: GridCell
    text: str
    confidence: float
    position: Tuple[int, int]
    timestamp: float

class HighPerformanceOCREngine:
    """고성능 OCR 엔진 - 병렬 처리 최적화"""
    
    def __init__(self, config, cache_manager=None, perf_monitor=None):
        self.config = config
        self.cache = cache_manager
        self.perf_monitor = perf_monitor
        
        # ConfigManager 객체 생성 (dict를 ConfigManager로 변환)
        from src.core.config_manager import ConfigManager
        if isinstance(config, dict):
            config_manager = ConfigManager()
            config_manager._config = config
        else:
            config_manager = config
            
        # 고속 OCR 어댑터 사용 (기존 ServiceContainer 대신)
        try:
            from src.ocr.fast_ocr_adapter import FastOCRAdapter
            self.ocr_service = FastOCRAdapter(config_manager)
            print("[고속 OCR] Fast OCR Adapter 사용")
        except Exception as e:
            print(f"[경고] Fast OCR Adapter 로드 실패: {e}")
            # 폴백: 기존 ServiceContainer 사용
            from src.core.service_container import ServiceContainer
            temp_container = ServiceContainer()
            self.ocr_service = temp_container._ocr_service
        
        # ThreadPoolExecutor 생성 (기본값 사용)
        from concurrent.futures import ThreadPoolExecutor
        self.max_workers = getattr(config_manager, 'ocr_max_workers', 6)
        self.executor = ThreadPoolExecutor(max_workers=self.max_workers)
    
    def _init_paddle_ocr(self):
        """PaddleOCR 초기화"""
        try:
            with suppress_stdout_stderr():
                # PaddleOCR 3.1.0 호환 - 최소 파라미터만 사용
                self.paddle_ocr = PaddleOCR(lang='korean')
            print("고성능 PaddleOCR 엔진 초기화 완료")
        except Exception as e:
            print(f"[FAIL] PaddleOCR 초기화 실패: {e}")
            self.paddle_ocr = None
    
    def preprocess_image_fast(self, image: np.ndarray) -> np.ndarray:
        """빠른 이미지 전처리"""
        try:
            import cv2
            
            # 크기 조정
            height, width = image.shape[:2]
            new_width = int(width * 4)
            new_height = int(height * 4)
            image = cv2.resize(image, (new_width, new_height), interpolation=cv2.INTER_CUBIC)
            
            # 그레이스케일 변환
            if len(image.shape) == 3:
                gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            else:
                gray = image
            
            # 이진화
            _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)
            
            return binary
        except Exception as e:
            print(f"이미지 전처리 오류: {e}")
            return image
    
    def perform_ocr_batch(self, images_with_cells: list) -> list:
        """배치 OCR 처리"""
        # 새로운 형식으로 변환
        images_with_regions = []
        cells = []
        
        for image, cell in images_with_cells:
            region = (cell.ocr_area[0], cell.ocr_area[1], 
                     cell.ocr_area[2], cell.ocr_area[3])
            images_with_regions.append((image, region, cell.id))
            cells.append(cell)
        
        # 최적화된 서비스 사용
        ocr_results = self.ocr_service.perform_batch_ocr(images_with_regions)
        
        # DetectionResult로 변환
        results = []
        for i, ocr_result in enumerate(ocr_results):
            if i < len(cells) and ocr_result.text:
                cell = cells[i]
                if self.ocr_service.check_trigger_patterns(ocr_result.text):
                    results.append(DetectionResult(
                        cell=cell,
                        text=ocr_result.text,
                        confidence=ocr_result.confidence,
                        position=ocr_result.position,
                        timestamp=ocr_result.timestamp
                    ))
        
        return results
    
    def _process_single_ocr(self, image: np.ndarray, cell: GridCell) -> Optional[DetectionResult]:
        """단일 이미지 OCR 처리"""
        try:
            # 전처리
            processed = self.preprocess_image_fast(image)
            
            # OCR 수행 (3.1.0 호환)
            with suppress_stdout_stderr():
                result = self.paddle_ocr.ocr(processed)
            
            if not result or not result[0]:
                return None
            
            # 텍스트 추출
            all_text = []
            for line in result[0]:
                if line[1]:
                    text = line[1][0]
                    confidence = line[1][1]
                    if confidence > 0.5:
                        all_text.append(text)
            
            combined_text = ' '.join(all_text)
            
            # 트리거 패턴 확인
            if self._check_trigger_patterns(combined_text):
                return DetectionResult(
                    cell=cell,
                    text=combined_text,
                    confidence=0.9,
                    position=(cell.bounds[0] + 50, cell.bounds[1] + 50),
                    timestamp=time.time()
                )
            
            return None
            
        except Exception as e:
            print(f"OCR 처리 중 오류: {e}")
            return None
    
    def perform_batch_ocr(self, images_with_regions: List[Tuple[np.ndarray, Tuple[int, int, int, int], str]]) -> List[Any]:
        """배치 OCR 처리"""
        results = []
        
        # 개별 처리로 변경 (EnhancedOCRService 사용)
        for image, region, cell_id in images_with_regions:
            try:
                result = self.ocr_service.perform_ocr_with_recovery(image, cell_id)
                results.append(result)
            except Exception as e:
                print(f"OCR 처리 오류 ({cell_id}): {e}")
                results.append(None)
        
        return results
    
    def _check_trigger_patterns(self, text: str) -> bool:
        """트리거 패턴 확인"""
        trigger_patterns = ["들어왔습니다", "입장했습니다", "참여했습니다"]
        return any(pattern in text for pattern in trigger_patterns)
    
    def cleanup(self):
        """리소스 정리"""
        if hasattr(self, 'executor'):
            self.executor.shutdown(wait=True)

class RealTimeMonitoringThread(QThread):
    """실시간 모니터링 스레드"""
    
    detection_signal = pyqtSignal(str, str, float, float)  # cell_id, text, x, y
    automation_signal = pyqtSignal(str, str)  # cell_id, result
    status_signal = pyqtSignal(str)  # status message
    performance_signal = pyqtSignal(dict)  # performance metrics
    cell_status_signal = pyqtSignal(str, str, str)  # cell_id, status, timestamp
    
    def __init__(self, service_container: ServiceContainer, cache_manager=None, perf_monitor=None):
        super().__init__()
        self.services = service_container
        self.running = False
        self.cache_manager = cache_manager
        self.perf_monitor = perf_monitor
        self.ocr_engine = HighPerformanceOCREngine(
            service_container.config_manager._config,
            cache_manager,
            perf_monitor
        )
        self.automation_queue = queue.Queue()
        self._debug_samples_saved = False
        self.test_mode = False
        self.test_cell_id = None
        self.use_chatroom_coords = True  # 채팅방 좌표 직접 사용
        
        # 초고속 캡처 엔진 초기화
        self.ultra_fast_capture = None
        try:
            from src.monitoring.ultra_fast_capture import UltraFastCaptureManager, CaptureRegion
            self.ultra_fast_capture = UltraFastCaptureManager()
            self.CaptureRegion = CaptureRegion
            print("[초고속] Ultra Fast Capture 엔진 활성화")
        except Exception as e:
            print(f"[경고] Ultra Fast Capture 로드 실패: {e}")
        
        # 변화 감지 모니터 초기화
        self.change_detector = None
        if CHANGE_DETECTION_AVAILABLE:
            self.change_detector = ChangeDetectionMonitor(change_threshold=0.05)
            print("[OK] 변화 감지 모니터 활성화 (임계값: 5%)")
        
        # 자동화 처리 스레드
        self.automation_thread = threading.Thread(target=self._automation_worker, daemon=True)
        self.automation_thread.start()
        print("자동화 스레드 생성 및 시작")
    
    def run(self):
        """메인 감지 루프"""
        print("실시간 모니터링 시작")
        self.running = True
        self.status_signal.emit("모니터링 시작")
        
        with mss.mss() as sct:
            loop_count = 0
            while self.running:
                try:
                    loop_count += 1
                    start_time = time.time()
                    
                    # 10번마다 상태 출력
                    if loop_count % 10 == 0:
                        print(f"[LOOP {loop_count}] 모니터링 루프 실행 중... (시간: {datetime.now().strftime('%H:%M:%S')})")
                    
                    # 활성 셀 가져오기
                    self.services.grid_manager.update_cell_cooldowns()
                    
                    # 테스트 모드에서는 선택한 셀만 활성화
                    if self.test_mode and self.test_cell_id:
                        active_cells = [cell for cell in self.services.grid_manager.cells 
                                      if cell.can_be_triggered() and cell.id == self.test_cell_id]
                        if active_cells:
                            print(f"테스트 모드: {self.test_cell_id}만 감지 중...")
                    else:
                        active_cells = [cell for cell in self.services.grid_manager.cells 
                                      if cell.can_be_triggered()]
                        
                        # 카카오톡 채팅방 위치를 우선 처리 (monitor_0의 cell들)
                        priority_cells = [c for c in active_cells if 'monitor_0' in c.id]
                        other_cells = [c for c in active_cells if 'monitor_0' not in c.id]
                        active_cells = priority_cells + other_cells
                    
                    if not active_cells:
                        time.sleep(0.05)  # 더 짧은 대기 시간
                        continue
                    
                    # 배치 크기 제한 (최대 10개씩 처리 - 고속 OCR로 더 많이 가능)
                    batch_size = min(10, len(active_cells))  # 최대 10개씩 처리
                    
                    # 초고속 배치 캡처
                    images_with_regions = []
                    capture_start = time.time()
                    
                    # 디버그: 첫 루프에서만 출력
                    if loop_count == 1:
                        print(f"{len(active_cells)}개 셀 초고속 캡처 시작...")
                    
                    if self.ultra_fast_capture:
                        # 초고속 캡처 엔진 사용
                        capture_regions = []
                        for cell in active_cells[:batch_size]:
                            x, y, w, h = cell.ocr_area
                            region = self.CaptureRegion(x, y, w, h, cell.id)
                            capture_regions.append(region)
                            
                            # 셀 상태 업데이트 - 캡처 중
                            timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
                            self.cell_status_signal.emit(cell.id, "캡처 중", timestamp)
                        
                        # 배치 캡처 실행 (Win32 API 사용)
                        captured_images = self.ultra_fast_capture.capture_batch(capture_regions)
                        
                        # 결과 매핑
                        for i, (image, region) in enumerate(zip(captured_images, capture_regions)):
                            if image is not None:
                                images_with_regions.append((image, (region.x, region.y, region.width, region.height), region.cell_id))
                    else:
                        # 폴백: 기존 방식
                        monitor = sct.monitors[1]  # 주 모니터
                        full_screenshot = sct.grab(monitor)
                        full_image = np.array(full_screenshot)
                        
                        # 각 셀 영역 자르기
                        for cell in active_cells[:batch_size]:
                            try:
                                x, y, w, h = cell.ocr_area
                                
                                # 화면 경계 체크
                                if x < 0 or y < 0 or x + w > full_image.shape[1] or y + h > full_image.shape[0]:
                                    continue
                                
                                # 디버그: 첫 루프에서만 출력
                                if loop_count == 1:
                                    print(f"   셀 {cell.id}: 영역 ({x}, {y}, {w}, {h})")
                                
                                # 셀 상태 업데이트 - 캡처 중
                                timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
                                self.cell_status_signal.emit(cell.id, "캡처 중", timestamp)
                                
                                # 영역 자르기
                                image = full_image[y:y+h, x:x+w].copy()
                                
                                region = (x, y, w, h)
                                images_with_regions.append((image, region, cell.id))
                                
                                # 디버그: 첫 루프에서만 출력
                                if loop_count == 1:
                                    print(f"   [OK] 셀 {cell.id}: 캡처 완료 ({image.shape})")
                            
                            except Exception as e:
                                print(f"   [FAIL] 스크린샷 오류 {cell.id}: {e}")
                    
                    # 디버그: 첫 루프 또는 이미지가 있을 때만 출력
                    if loop_count == 1 or len(images_with_regions) > 0:
                        print(f"[LOOP {loop_count}] 캡처 완료: {len(images_with_regions)}개 이미지")
                    
                    # 스크린 캡처 시간 기록
                    if self.perf_monitor:
                        capture_time = (time.time() - capture_start) * 1000
                        self.perf_monitor.record_capture_latency(capture_time)
                    
                    # OCR 처리가 필요한 경우에만
                    if len(images_with_regions) > 0:
                        ocr_start_time = time.time()
                        print(f"[LOOP {loop_count}] OCR 처리 시작! ({len(images_with_regions)}개 이미지)")
                    
                    # 병렬 OCR 처리
                    ocr_results = []
                    
                    # 배치 OCR 사용 (병렬 처리)
                    if hasattr(self.ocr_engine.ocr_service, 'perform_batch_ocr'):
                        batch_images = [(img, cell_id) for img, _, cell_id in images_with_regions]
                        batch_results = self.ocr_engine.ocr_service.perform_batch_ocr(batch_images)
                        ocr_results = batch_results  # 이미 OCRResult 객체들
                    else:
                        # 폴백: 개별 처리
                        for image, region, cell_id in images_with_regions:
                            try:
                                # 셀 상태 업데이트 - OCR 처리 중
                                timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
                                self.cell_status_signal.emit(cell_id, "OCR 처리 중", timestamp)
                                
                                result = self.ocr_engine.ocr_service.perform_ocr_with_recovery(image, cell_id)
                                ocr_results.append(result)
                            except Exception as e:
                                print(f"OCR 처리 오류 ({cell_id}): {e}")
                                ocr_results.append(None)
                    
                    # OCR 처리 시간 측정
                    if len(images_with_regions) > 0:
                        ocr_time = time.time() - ocr_start_time
                        print(f"[LOOP {loop_count}] OCR 완료! 소요시간: {ocr_time:.2f}초")
                    
                    # 감지된 결과 리스트
                    detection_results = []
                    
                    # 변화 감지 통계 업데이트
                    if self.change_detector and time.time() % 10 < self.services.config_manager.get('ocr_interval_sec'):
                        stats = self.change_detector.get_statistics()
                        self.performance_signal.emit({
                            'change_detection': stats,
                            'timestamp': time.time()
                        })
                        print(f"[STATS] 변화 감지 - OCR 스킵율: {stats['skip_ratio']:.1%}, 효율성: {stats['efficiency_gain']:.1f}%")
                    
                    # 결과와 셀 매핑 (강화된 콘솔 디버깅)
                    try:
                        print(f"\n=== OCR 스캔 결과 ===")
                        print(f"OCR 결과: {len(ocr_results)}, 활성 셀: {len(active_cells)}")
                        
                        # 테스트 모드 상태 출력
                        if self.test_mode:
                            print(f"테스트 모드 활성 - 대상 셀: {self.test_cell_id}")
                        
                        # 안전한 인덱스 처리 - images_with_regions와 매핑
                        for i, (ocr_result, (image, region, cell_id)) in enumerate(zip(ocr_results, images_with_regions)):
                            # cell_id로 실제 cell 찾기
                            cell = next((c for c in active_cells if c.id == cell_id), None)
                            if not cell:
                                continue
                            
                            # 모든 OCR 결과를 콘솔에 출력
                            if ocr_result:
                                if ocr_result.text:
                                    print(f"셀 {cell.id}: '{ocr_result.text}' (신뢰도: {ocr_result.confidence:.2f})")
                                    
                                    # 셀 상태 업데이트 - 텍스트 감지
                                    timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
                                    self.cell_status_signal.emit(cell.id, f"텍스트: {ocr_result.text[:30]}", timestamp)
                                    
                                    # 디버그 정보 출력 - 테스트 모드가 아니어도 항상 출력
                                    if hasattr(ocr_result, 'debug_info'):
                                        debug_info = ocr_result.debug_info
                                        if 'all_results' in debug_info:
                                            print(f"   전체 감지 결과 ({len(debug_info['all_results'])}개):")
                                            for j, res in enumerate(debug_info['all_results']):  # 모든 결과 출력
                                                print(f"      [{j}] '{res.get('text', '')}' (신뢰도: {res.get('confidence', 0):.2f})")
                                                # 트리거 패턴 포함 여부 표시
                                                if any(pattern in res.get('text', '') for pattern in self.services.config_manager.get('trigger_patterns', [])):
                                                    print(f"         ^^^ 트리거 패턴 포함! ^^^")
                                    
                                    # 트리거 패턴 확인 (강화된 체크)
                                    text = ocr_result.text
                                    print(f"\n[TARGET] [트리거 체크] 텍스트: '{text}' (신뢰도: {ocr_result.confidence:.2f})")
                                    print(f"   찾는 패턴: {self.services.config_manager.get('trigger_patterns', [])}")
                                    
                                    # GUI 로그에도 표시
                                    self.status_signal.emit(f"OCR 감지: '{text}' (신뢰도: {ocr_result.confidence:.2f})")
                                    
                                    # 직접 패턴 매칭 ("들어왔습니다"만)
                                    trigger_found = False
                                    trigger_patterns = ["들어왔습니다"]
                                    
                                    for pattern in trigger_patterns:
                                        if pattern in text:
                                            trigger_found = True
                                            print(f"[OK] 직접 패턴 매치: '{pattern}' in '{text}'")
                                            break
                                    
                                    # 원래 체크도 병행
                                    ocr_check = self.ocr_engine.ocr_service.check_trigger_patterns(ocr_result)
                                    print(f"[SEARCH] OCR 서비스 체크 결과: {ocr_check}")
                                    
                                    if trigger_found or ocr_check:
                                        # 셀 상태 업데이트 - 트리거 감지
                                        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
                                        self.cell_status_signal.emit(cell.id, f"트리거 감지! → 자동화", timestamp)
                                        
                                        detection_result = DetectionResult(
                                            cell=cell,
                                            text=ocr_result.text,
                                            confidence=ocr_result.confidence,
                                            position=ocr_result.position,
                                            timestamp=time.time()
                                        )
                                        detection_results.append(detection_result)
                                        print(f"[TARGET][TARGET][TARGET] 감지! 셀 {cell.id}: '{ocr_result.text}' [TARGET][TARGET][TARGET]")
                                        self.status_signal.emit(f"[TARGET] 트리거 감지!!! '{ocr_result.text}' (신뢰도: {ocr_result.confidence:.2f})")
                                        
                                        # 테스트 모드에서는 GUI 로그에도 표시
                                        if self.test_mode:
                                            self.status_signal.emit(f"테스트 모드 감지: {cell.id} - '{ocr_result.text}'")
                                    else:
                                        print(f"[FAIL] 트리거 매칭 실패: '{ocr_result.text}'")
                                        
                                        # 테스트 모드에서는 왜 매칭 실패했는지 상세 정보 표시
                                        if self.test_mode:
                                            print(f"   원본 텍스트: '{ocr_result.text}'")
                                            print(f"   정규화 텍스트: '{ocr_result.normalized_text}'")
                                else:
                                    print(f"⭕ 셀 {cell.id}: 텍스트 없음")
                                    # 셀 상태 업데이트 - 텍스트 없음
                                    timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
                                    self.cell_status_signal.emit(cell.id, "대기 중", timestamp)
                                    if self.test_mode and hasattr(ocr_result, 'debug_info'):
                                        print(f"   ℹ️ 디버그: {ocr_result.debug_info}")
                            else:
                                print(f"[FAIL] 셀 {cell.id}: OCR 결과 없음 (None)")
                                # 셀 상태 업데이트 - OCR 실패
                                timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
                                self.cell_status_signal.emit(cell.id, "대기 중", timestamp)
                        
                        print(f"=== 스캔 완료 ===\n")
                                
                    except Exception as debug_e:
                        print(f"디버깅 오류: {debug_e}")
                        self.status_signal.emit(f"디버깅 오류: {debug_e}")
                    
                    # 결과 처리
                    for result in detection_results:
                        cell = result.cell
                        cell.set_triggered(result.text, result.position)
                        
                        # 신호 발송
                        self.detection_signal.emit(
                            cell.id,
                            result.text,
                            result.position[0],
                            result.position[1]
                        )
                        
                        # 자동화 큐에 추가
                        self.automation_queue.put(result)
                        print(f"\n[LAUNCH][LAUNCH][LAUNCH] [자동화 큐 추가] [LAUNCH][LAUNCH][LAUNCH]")
                        print(f"   셀: {result.cell.id}")
                        print(f"   텍스트: '{result.text}'")
                        print(f"   신뢰도: {result.confidence:.2f}")
                        print(f"[LAUNCH][LAUNCH][LAUNCH] 액션 실행 예정! [LAUNCH][LAUNCH][LAUNCH]")
                    
                    # 주기 조절 (config에서 설정값 사용)
                    elapsed = time.time() - start_time
                    if loop_count % 10 == 0:
                        print(f"[LOOP {loop_count}] 전체 루프 시간: {elapsed:.2f}초")
                    
                    ocr_interval = self.services.config_manager.get('ocr_interval_sec', 0.2)
                    if elapsed < ocr_interval:
                        time.sleep(ocr_interval - elapsed)
                        
                except Exception as e:
                    error_msg = f"모니터링 오류: {str(e)[:100]}"
                    self.status_signal.emit(f"[FAIL] {error_msg}")
                    time.sleep(2)  # 오류 시 더 긴 대기
    
    def _automation_worker(self):
        """자동화 처리 워커"""
        print("자동화 워커 시작됨")
        queue_check_count = 0
        while True:
            try:
                # 큐 상태 확인 (10번마다 한 번씩)
                queue_check_count += 1
                if queue_check_count % 10 == 0:
                    print(f"   큐 체크 중... (큐 크기: {self.automation_queue.qsize()})")
                
                result = self.automation_queue.get(timeout=1)
                print(f"\n💥💥💥 [자동화 실행 시작] 💥💥💥")
                print(f"자동화 대상: {result.cell.id} - '{result.text}'")
                print(f"   DetectionResult 정보:")
                print(f"      - cell: {result.cell.id}")
                print(f"      - text: '{result.text}'")
                print(f"      - position: {result.position}")
                print(f"      - confidence: {result.confidence}")
                
                # 자동화 실행
                success = self._execute_automation(result)
                
                # 결과 신호
                status = "[OK] 성공" if success else "[FAIL] 실패"
                self.automation_signal.emit(result.cell.id, status)
                print(f"자동화 완료: {status}")
                
            except queue.Empty:
                continue
            except Exception as e:
                print(f"자동화 오류: {e}")
                import traceback
                traceback.print_exc()
    
    def _execute_automation(self, result: DetectionResult) -> bool:
        """자동화 실행"""
        # 디버그 로그 파일에 기록
        with open("automation_debug.log", "a", encoding="utf-8") as f:
            f.write(f"\n{'='*60}\n")
            f.write(f"자동화 실행 시작: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Cell: {result.cell.id}, Text: '{result.text}'\n")
            
        try:
            cell = result.cell
            
            # 메시지 입력창 위치 계산
            # 셀의 하단에서 위로 8px 위치를 클릭
            ocr_x, ocr_y, ocr_width, ocr_height = cell.ocr_area
            
            # x 좌표는 셀의 중앙
            click_x = ocr_x + ocr_width // 2
            
            # y 좌표는 셀의 하단에서 위로 설정된 픽셀만큼
            input_offset = self.services.config_manager.get('input_box_offset', {}).get('from_bottom', 8)
            click_y = ocr_y + ocr_height - input_offset
            
            # 로그 파일에 기록
            with open("automation_debug.log", "a", encoding="utf-8") as f:
                f.write(f"셀 영역: ({ocr_x}, {ocr_y}, {ocr_width}, {ocr_height})\n")
                f.write(f"클릭 위치: ({click_x}, {click_y}) - 셀 하단에서 {input_offset}px 위\n")
                f.write(f"PyAutoGUI FAILSAFE: {pyautogui.FAILSAFE}\n")
                
            print(f"   셀 영역: ({ocr_x}, {ocr_y}, {ocr_width}, {ocr_height})")
            print(f"   클릭 위치: ({click_x}, {click_y}) - 셀 하단에서 {input_offset}px 위")
            
            # pyautogui 안전 모드 확인
            print(f"   PyAutoGUI FAILSAFE: {pyautogui.FAILSAFE}")
            print(f"   Win32 API 사용 가능: {WIN32_AVAILABLE}")
            
            # 입력창 클릭
            print(f"   클릭 실행 전...")
            with open("automation_debug.log", "a", encoding="utf-8") as f:
                f.write(f"클릭 실행 전... 시간: {time.strftime('%H:%M:%S')}\n")
                if WIN32_AVAILABLE:
                    before_x, before_y = win32_auto.get_cursor_pos()
                    f.write(f"현재 마우스 위치 (Win32): ({before_x}, {before_y})\n")
                else:
                    f.write(f"현재 마우스 위치 (PyAutoGUI): {pyautogui.position()}\n")
            
            # 스크린샷 저장을 주석 처리 (화면 깜빡임 방지)
            # screenshot = pyautogui.screenshot()
            # screenshot.save(f"automation_before_click_{time.strftime('%H%M%S')}.png")
            
            # 마우스 이동 후 클릭 - PyAutoGUI 우선 사용
            print(f"   ➡️ 마우스 이동: ({click_x}, {click_y})")
            
            # 이동 전 위치 확인
            before_pos = pyautogui.position()
            print(f"      이동 전 위치: {before_pos}")
            
            # PyAutoGUI로 마우스 이동 (빠르게)
            pyautogui.moveTo(click_x, click_y, duration=0.1)
            
            # 이동 후 위치 확인
            after_pos = pyautogui.position()
            print(f"      이동 후 위치: {after_pos}")
            
            # 즉시 클릭하여 창 활성화
            print(f"      입력창 클릭...")
            pyautogui.click(click_x, click_y)
            time.sleep(0.1)
            
            # 더블클릭으로 입력창 확실히 선택
            pyautogui.doubleClick(click_x, click_y)
            time.sleep(0.1)
            
            with open("automation_debug.log", "a", encoding="utf-8") as f:
                f.write(f"클릭 완료! 시간: {time.strftime('%H:%M:%S')}\n")
                f.write(f"클릭 후 마우스 위치 (PyAutoGUI): {pyautogui.position()}\n")
            
            print(f"      클릭 완료")
            
            # 텍스트 입력
            response = "어서오세요! 환영합니다"
            print(f"   응답 입력: '{response}'")
            pyperclip.copy(response)
            
            # 텍스트 전송 - PyAutoGUI 사용
            print(f"   텍스트 전송 중...")
            # 붙여넣기
            pyautogui.hotkey('ctrl', 'v')
            time.sleep(0.2)
            # 전송
            pyautogui.press('enter')
            print(f"   메시지 전송 완료")
            
            # 쿨다운 설정
            cell.set_cooldown(5.0)
            print(f"   ⏱️ 쿨다운 설정: 5초")
            
            with open("automation_debug.log", "a", encoding="utf-8") as f:
                f.write(f"자동화 성공! 시간: {time.strftime('%H:%M:%S')}\n")
                f.write(f"{'='*60}\n")
            
            return True
            
        except Exception as e:
            print(f"자동화 실행 오류: {e}")
            import traceback
            traceback.print_exc()
            
            with open("automation_debug.log", "a", encoding="utf-8") as f:
                f.write(f"자동화 실패! 오류: {e}\n")
                f.write(f"{'='*60}\n")
            
            return False
    
    def stop(self):
        """스레드 중지"""
        self.running = False

class GridOverlayWidget(QWidget):
    """향상된 그리드 오버레이 위젯"""
    
    def __init__(self, grid_manager):
        super().__init__()
        self.grid_manager = grid_manager
        self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_TransparentForMouseEvents)
        
        # 전체 화면 크기 설정
        monitors = get_monitors()
        total_width = sum(m.width for m in monitors)
        max_height = max(m.height for m in monitors)
        self.setGeometry(0, 0, total_width, max_height)
        
        # 그리기 설정
        self.grid_color = QColor(0, 255, 255, 100)
        self.active_color = QColor(0, 255, 0, 150)
        self.cooldown_color = QColor(255, 0, 0, 150)
        self.grid_line_width = 2
        
        # 애니메이션 타이머
        self.animation_timer = QTimer()
        self.animation_timer.timeout.connect(self.update)
        self.animation_timer.start(100)
    
    def paintEvent(self, event):
        """그리기 이벤트 (안전한 처리)"""
        try:
            painter = QPainter(self)
            if not painter.isActive():
                return
            
            painter.setRenderHint(QPainter.Antialiasing)
            
            # 그리드 그리기
            grid_pen = QPen(self.grid_color, self.grid_line_width)
            painter.setPen(grid_pen)
            
            for cell in self.grid_manager.cells:
                x, y, w, h = cell.bounds
                
                # 셀 테두리
                painter.drawRect(x, y, w, h)
                
                # 셀 상태에 따른 색상 (비활성화 - 깜빡임 방지)
                # if cell.status == CellStatus.TRIGGERED:
                #     painter.fillRect(x, y, w, h, QBrush(self.active_color))
                # elif cell.status == CellStatus.COOLDOWN:
                #     painter.fillRect(x, y, w, h, QBrush(self.cooldown_color))
                
                # OCR 영역 표시
                ocr_x, ocr_y, ocr_w, ocr_h = cell.ocr_area
                ocr_pen = QPen(QColor(255, 255, 0, 150), 2, Qt.DashLine)
                painter.setPen(ocr_pen)
                painter.drawRect(ocr_x, ocr_y, ocr_w, ocr_h)
                
                # 셀 ID 표시
                painter.setPen(QPen(Qt.white))
                painter.setFont(QFont("Arial", 10))
                painter.drawText(x + 5, y + 15, cell.id)
                
        except Exception as e:
            # QPainter 오류 무시 (로그만 남김)
            pass

class UnifiedChatbotGUI(QWidget):
    """통합 챗봇 GUI - 모든 기능 포함"""
    
    def __init__(self):
        super().__init__()
        self.services = ServiceContainer()
        
        # 성능 최적화 컴포넌트
        self.cache_manager = CacheManager(self.services.config_manager._config)
        self.perf_monitor = PerformanceMonitor()
        self.perf_optimizer = PerformanceOptimizer(self.perf_monitor)
        
        # UI 요소 초기화 (콜백 전에 초기화)
        self.cpu_label = None
        self.memory_label = None
        self.ocr_latency_label = None
        self.cache_hit_label = None
        
        self.monitoring_thread = None
        self.overlay = None
        
        # UI 초기화 먼저
        self.init_ui()
        
        # 캐시와 모니터 시작 (UI 초기화 후)
        self.cache_manager.start()
        self.perf_monitor.start()
        
        # 성능 콜백 등록 (UI 요소 생성 후)
        self.perf_monitor.add_callback(self.on_performance_update)
        
        self.log("통합 카카오톡 챗봇 시스템 시작!")
        self.log("⚡ 성능 최적화 활성화됨")
    
    def init_ui(self):
        """UI 초기화"""
        self.setWindowTitle("카카오톡 챗봇 시스템 v2.0")
        self.setGeometry(100, 100, 900, 700)
        
        # 메인 레이아웃
        main_layout = QVBoxLayout()
        
        # 탭 위젯
        tabs = QTabWidget()
        
        # 메인 탭
        main_tab = QWidget()
        main_tab_layout = QVBoxLayout()
        
        # 상태 표시
        self.status_label = QLabel("[PAUSE] 대기 중...")
        self.status_label.setStyleSheet("font-size: 14px; font-weight: bold; padding: 10px;")
        main_tab_layout.addWidget(self.status_label)
        
        # 컨트롤 버튼
        control_layout = QHBoxLayout()
        
        self.start_btn = QPushButton("모니터링 시작")
        self.start_btn.clicked.connect(self.start_monitoring)
        control_layout.addWidget(self.start_btn)
        
        self.stop_btn = QPushButton("[STOP] 모니터링 중지")
        self.stop_btn.clicked.connect(self.stop_monitoring)
        self.stop_btn.setEnabled(False)
        control_layout.addWidget(self.stop_btn)
        
        self.overlay_btn = QPushButton("오버레이 표시")
        self.overlay_btn.clicked.connect(self.toggle_overlay)
        control_layout.addWidget(self.overlay_btn)
        
        main_tab_layout.addLayout(control_layout)
        
        # 테스트 모드 섹션
        test_group = QGroupBox("테스트 모드")
        test_layout = QVBoxLayout()
        
        # 테스트 모드 체크박스
        self.test_mode_checkbox = QCheckBox("테스트 모드 활성화 (특정 셀만 감지)")
        self.test_mode_checkbox.stateChanged.connect(self.toggle_test_mode)
        test_layout.addWidget(self.test_mode_checkbox)
        
        # 셀 선택 콤보박스
        cell_select_layout = QHBoxLayout()
        cell_select_layout.addWidget(QLabel("테스트할 셀:"))
        
        self.test_cell_combo = QComboBox()
        self.test_cell_combo.setEnabled(False)
        # 셀 목록 추가 (3x5 그리드)
        for row in range(3):
            for col in range(5):
                self.test_cell_combo.addItem(f"셀 [{row},{col}] - monitor_0_cell_{row}_{col}")
        
        cell_select_layout.addWidget(self.test_cell_combo)
        test_layout.addLayout(cell_select_layout)
        
        test_group.setLayout(test_layout)
        main_tab_layout.addWidget(test_group)
        
        # 오버레이 설정 섹션
        overlay_group = QGroupBox("오버레이 설정")
        overlay_layout = QVBoxLayout()
        
        # 오버레이 높이 조절
        height_layout = QHBoxLayout()
        height_layout.addWidget(QLabel("오버레이 높이:"))
        
        self.overlay_height_slider = QSlider(Qt.Horizontal)
        self.overlay_height_slider.setMinimum(30)
        self.overlay_height_slider.setMaximum(200)
        self.overlay_height_slider.setSingleStep(10)
        self.overlay_height_slider.setPageStep(10)
        self.overlay_height_slider.setValue(100)  # 기본값 100px
        self.overlay_height_slider.setTickPosition(QSlider.TicksBelow)
        self.overlay_height_slider.setTickInterval(10)
        self.overlay_height_slider.valueChanged.connect(self.on_overlay_height_changed)
        height_layout.addWidget(self.overlay_height_slider)
        
        self.overlay_height_label = QLabel("100px")
        self.overlay_height_label.setMinimumWidth(50)
        height_layout.addWidget(self.overlay_height_label)
        
        overlay_layout.addLayout(height_layout)
        
        # 높이 조절 설명
        info_label = QLabel("※ 각 셀 하단의 OCR 감지 영역 높이를 조절합니다 (30~200px)")
        info_label.setStyleSheet("color: gray; font-size: 11px;")
        overlay_layout.addWidget(info_label)
        
        overlay_group.setLayout(overlay_layout)
        main_tab_layout.addWidget(overlay_group)
        
        # 로그 영역 (개선된 버전)
        log_group = QGroupBox("실시간 로그")
        log_layout = QVBoxLayout()
        
        # 셀 상태 테이블 추가
        cell_status_label = QLabel("📡 셀별 실시간 상태:")
        cell_status_label.setStyleSheet("font-weight: bold; margin-top: 5px;")
        log_layout.addWidget(cell_status_label)
        
        self.cell_status_table = QTableWidget()
        self.cell_status_table.setColumnCount(4)
        self.cell_status_table.setHorizontalHeaderLabels(["셀 ID", "시간", "상태", "감지 텍스트"])
        self.cell_status_table.horizontalHeader().setStretchLastSection(True)
        self.cell_status_table.setMaximumHeight(200)
        self.cell_status_table.setAlternatingRowColors(True)
        log_layout.addWidget(self.cell_status_table)
        
        # 셀 상태 딕셔너리 초기화
        self.cell_status_dict = {}
        
        # 일반 로그
        general_log_label = QLabel("📋 시스템 로그:")
        general_log_label.setStyleSheet("font-weight: bold; margin-top: 10px;")
        log_layout.addWidget(general_log_label)
        
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMaximumHeight(200)
        log_layout.addWidget(self.log_text)
        
        log_group.setLayout(log_layout)
        main_tab_layout.addWidget(log_group)
        
        # 통계 표시
        stats_layout = QHBoxLayout()
        
        self.cell_count_label = QLabel(f"총 셀: {len(self.services.grid_manager.cells)}개")
        stats_layout.addWidget(self.cell_count_label)
        
        self.detection_count_label = QLabel("감지: 0회")
        stats_layout.addWidget(self.detection_count_label)
        
        self.automation_count_label = QLabel("자동화: 0회")
        stats_layout.addWidget(self.automation_count_label)
        
        # 변화 감지 통계
        self.change_detection_label = QLabel("변화 감지: -")
        stats_layout.addWidget(self.change_detection_label)
        
        main_tab_layout.addLayout(stats_layout)
        
        main_tab.setLayout(main_tab_layout)
        tabs.addTab(main_tab, "메인")
        
        # 설정 탭
        settings_tab = self.create_settings_tab()
        tabs.addTab(settings_tab, "설정")
        
        # 고급 탭
        advanced_tab = self.create_advanced_tab()
        tabs.addTab(advanced_tab, "고급")
        
        main_layout.addWidget(tabs)
        self.setLayout(main_layout)
        
        # 카운터 초기화
        self.detection_count = 0
        self.automation_count = 0
    
    def create_settings_tab(self):
        """설정 탭 생성"""
        tab = QWidget()
        layout = QVBoxLayout()
        
        # OCR 설정
        ocr_group = QGroupBox("OCR 설정")
        ocr_layout = QGridLayout()
        
        ocr_layout.addWidget(QLabel("OCR 간격(초):"), 0, 0)
        self.ocr_interval_spin = QDoubleSpinBox()
        self.ocr_interval_spin.setRange(0.1, 5.0)
        self.ocr_interval_spin.setValue(0.5)
        self.ocr_interval_spin.setSingleStep(0.1)
        ocr_layout.addWidget(self.ocr_interval_spin, 0, 1)
        
        ocr_layout.addWidget(QLabel("쿨다운(초):"), 1, 0)
        self.cooldown_spin = QSpinBox()
        self.cooldown_spin.setRange(1, 60)
        self.cooldown_spin.setValue(5)
        ocr_layout.addWidget(self.cooldown_spin, 1, 1)
        
        ocr_layout.addWidget(QLabel("OCR 영역 폭:"), 2, 0)
        self.ocr_width_spin = QSpinBox()
        self.ocr_width_spin.setRange(100, 500)
        self.ocr_width_spin.setValue(200)
        self.ocr_width_spin.setSuffix(" px")
        ocr_layout.addWidget(self.ocr_width_spin, 2, 1)
        
        ocr_group.setLayout(ocr_layout)
        layout.addWidget(ocr_group)
        
        # 자동화 설정
        auto_group = QGroupBox("자동화 설정")
        auto_layout = QVBoxLayout()
        
        self.auto_response_check = QCheckBox("자동 응답 활성화")
        self.auto_response_check.setChecked(True)
        auto_layout.addWidget(self.auto_response_check)
        
        self.sound_alert_check = QCheckBox("소리 알림")
        self.sound_alert_check.setChecked(False)
        auto_layout.addWidget(self.sound_alert_check)
        
        auto_group.setLayout(auto_layout)
        layout.addWidget(auto_group)
        
        # 적용 버튼
        apply_btn = QPushButton("설정 적용")
        apply_btn.clicked.connect(self.apply_settings)
        layout.addWidget(apply_btn)
        
        layout.addStretch()
        tab.setLayout(layout)
        return tab
    
    def create_advanced_tab(self):
        """고급 탭 생성"""
        tab = QWidget()
        layout = QVBoxLayout()
        
        # 성능 모니터
        perf_group = QGroupBox("성능 모니터")
        perf_layout = QVBoxLayout()
        
        # 실시간 메트릭
        metrics_layout = QGridLayout()
        
        self.cpu_label = QLabel("CPU: 0%")
        self.memory_label = QLabel("메모리: 0MB")
        self.ocr_latency_label = QLabel("OCR 레이턴시: 0ms")
        self.cache_hit_label = QLabel("캐시 히트율: 0%")
        
        metrics_layout.addWidget(self.cpu_label, 0, 0)
        metrics_layout.addWidget(self.memory_label, 0, 1)
        metrics_layout.addWidget(self.ocr_latency_label, 1, 0)
        metrics_layout.addWidget(self.cache_hit_label, 1, 1)
        
        perf_layout.addLayout(metrics_layout)
        
        # 상세 로그
        self.perf_text = QTextEdit()
        self.perf_text.setReadOnly(True)
        self.perf_text.setMaximumHeight(200)
        perf_layout.addWidget(self.perf_text)
        
        # 최적화 버튼
        optimize_btn = QPushButton("자동 최적화")
        optimize_btn.clicked.connect(self.auto_optimize)
        perf_layout.addWidget(optimize_btn)
        
        perf_group.setLayout(perf_layout)
        layout.addWidget(perf_group)
        
        # 병렬 처리 옵션
        parallel_group = QGroupBox("병렬 처리 설정")
        parallel_layout = QVBoxLayout()
        
        # 병렬 처리 활성화
        self.use_parallel_check = QCheckBox("병렬 처리 사용 (실험적)")
        self.use_parallel_check.setChecked(False)
        if PARALLEL_MONITOR_AVAILABLE:
            self.use_parallel_check.setToolTip("변화 감지 + 우선순위 + 병렬 처리를 모두 사용")
        else:
            self.use_parallel_check.setEnabled(False)
            self.use_parallel_check.setToolTip("병렬 모니터 모듈이 없습니다")
        parallel_layout.addWidget(self.use_parallel_check)
        
        # 워커 수 설정
        worker_layout = QGridLayout()
        
        worker_layout.addWidget(QLabel("캡처 워커:"), 0, 0)
        self.capture_workers_spin = QSpinBox()
        self.capture_workers_spin.setRange(1, 8)
        self.capture_workers_spin.setValue(4)
        worker_layout.addWidget(self.capture_workers_spin, 0, 1)
        
        worker_layout.addWidget(QLabel("OCR 워커:"), 1, 0)
        self.ocr_workers_spin = QSpinBox()
        self.ocr_workers_spin.setRange(1, 4)
        self.ocr_workers_spin.setValue(2)
        worker_layout.addWidget(self.ocr_workers_spin, 1, 1)
        
        parallel_layout.addLayout(worker_layout)
        
        # 적응형 스캔 활성화
        self.adaptive_scan_check = QCheckBox("적응형 스캔 주기")
        self.adaptive_scan_check.setChecked(True)
        self.adaptive_scan_check.setToolTip("활발한 채팅방은 자주, 조용한 채팅방은 느리게 스캔")
        parallel_layout.addWidget(self.adaptive_scan_check)
        
        parallel_group.setLayout(parallel_layout)
        layout.addWidget(parallel_group)
        
        # 디버그 옵션
        debug_group = QGroupBox("디버그")
        debug_layout = QVBoxLayout()
        
        self.debug_mode_check = QCheckBox("디버그 모드")
        debug_layout.addWidget(self.debug_mode_check)
        
        self.save_screenshots_check = QCheckBox("스크린샷 저장")
        debug_layout.addWidget(self.save_screenshots_check)
        
        debug_group.setLayout(debug_layout)
        layout.addWidget(debug_group)
        
        layout.addStretch()
        tab.setLayout(layout)
        return tab
    
    def start_monitoring(self):
        """모니터링 시작"""
        if not PADDLEOCR_AVAILABLE:
            self.log("[FAIL] PaddleOCR이 설치되지 않았습니다.")
            return
        
        if hasattr(self, 'monitoring_thread') and self.monitoring_thread and self.monitoring_thread.running:
            self.log("[WARN] 이미 모니터링 중입니다.")
            return
        
        # 병렬 모니터 사용 여부 확인
        if PARALLEL_MONITOR_AVAILABLE and self.use_parallel_check.isChecked():
            self.log("[INFO] 최적화된 병렬 모니터를 사용합니다.")
            self.start_parallel_monitoring()
            return
        
        # 기존 모니터링 방식
        self.monitoring_thread = RealTimeMonitoringThread(
            self.services, 
            self.cache_manager,
            self.perf_monitor
        )
        
        # 테스트 모드 설정 전달
        if self.test_mode_checkbox.isChecked():
            selected_idx = self.test_cell_combo.currentIndex()
            row = selected_idx // 5
            col = selected_idx % 5
            test_cell_id = f"monitor_0_cell_{row}_{col}"
            self.monitoring_thread.test_mode = True
            self.monitoring_thread.test_cell_id = test_cell_id
            self.log(f"테스트 모드로 시작: {test_cell_id}만 감지")
        
        self.monitoring_thread.detection_signal.connect(self.on_detection)
        self.monitoring_thread.automation_signal.connect(self.on_automation)
        self.monitoring_thread.status_signal.connect(self.on_status_update)
        self.monitoring_thread.performance_signal.connect(self.on_performance_update)
        
        # 셀 상태 시그널 연결 (존재하는 경우만)
        if hasattr(self.monitoring_thread, 'cell_status_signal'):
            self.monitoring_thread.cell_status_signal.connect(lambda cell_id, status, timestamp: 
                self.update_cell_status(cell_id, status, timestamp))
        self.monitoring_thread.start()
        
        self.status_label.setText("실시간 모니터링 중...")
        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.log("[OK] 모니터링을 시작했습니다.")
    
    def start_parallel_monitoring(self):
        """병렬 모니터링 시작"""
        # 설정 업데이트
        self.services.config_manager._config['parallel_processing'] = {
            'enabled': True,
            'capture_workers': self.capture_workers_spin.value(),
            'ocr_workers': self.ocr_workers_spin.value()
        }
        
        # 병렬 모니터 생성
        self.parallel_orchestrator = MonitoringOrchestrator(
            self.services.grid_manager,
            self.services.ocr_service,
            self.services.config_manager._config
        )
        
        self.parallel_orchestrator.start()
        
        # 병렬 모니터 결과 처리 스레드
        self.parallel_result_thread = threading.Thread(
            target=self._process_parallel_results, 
            daemon=True
        )
        self.parallel_result_thread.start()
        
        # 통계 업데이트 타이머
        self.parallel_stats_timer = QTimer()
        self.parallel_stats_timer.timeout.connect(self._update_parallel_stats)
        self.parallel_stats_timer.start(1000)  # 1초마다 업데이트
        
        self.status_label.setText("병렬 모니터링 중...")
        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.log(f"[OK] 병렬 모니터링 시작 (캡처워커: {self.capture_workers_spin.value()}, OCR워커: {self.ocr_workers_spin.value()})")
    
    def _process_parallel_results(self):
        """병렬 모니터 결과 처리"""
        while hasattr(self, 'parallel_orchestrator') and self.parallel_orchestrator.running:
            task = self.parallel_orchestrator.get_automation_task(timeout=0.1)
            if task:
                # GUI 업데이트를 위해 시그널 emit
                self.detection_count += 1
                self.detection_count_label.setText(f"감지: {self.detection_count}회")
                
                # 자동화 실행
                cell_id = task['cell_id']
                text = task['text']
                cell = self._get_cell_by_id(cell_id)
                if cell:
                    x, y = self._get_click_position(cell)
                    self.services.automation_service.execute_automation(x, y, cell_id)
                    self.automation_count += 1
                    self.automation_count_label.setText(f"자동화: {self.automation_count}회")
                    self.log(f"[AUTO] {cell_id}: '{text}' → 자동화 실행")
    
    def _update_parallel_stats(self):
        """병렬 모니터 통계 업데이트"""
        if hasattr(self, 'parallel_orchestrator'):
            stats = self.parallel_orchestrator.get_statistics()
            
            # 변화 감지 통계
            change_stats = stats.get('change_detection', {})
            skip_percent = change_stats.get('skip_ratio', 0) * 100
            efficiency = change_stats.get('efficiency_gain', 0)
            self.change_detection_label.setText(f"변화 감지: 스킵 {skip_percent:.0f}% (효율 +{efficiency:.0f}%)")
            
            # 우선순위 통계
            priority_stats = stats.get('priority_management', {})
            active_cells = priority_stats.get('active_cells', 0)
            avg_interval = priority_stats.get('average_interval', 0)
            
            # 성능 텍스트에 상세 정보 표시
            perf_text = f"병렬 모니터 통계:\n"
            perf_text += f"- 평균 스캔 시간: {stats.get('avg_scan_time', 0)*1000:.1f}ms\n"
            perf_text += f"- 활발한 채팅방: {active_cells}개\n"
            perf_text += f"- 평균 스캔 주기: {avg_interval:.1f}초\n"
            perf_text += f"- 변화 감지 스킵: {stats.get('skipped_by_change', 0)}회\n"
            perf_text += f"- 우선순위 스킵: {stats.get('skipped_by_priority', 0)}회"
            
            if hasattr(self, 'perf_text'):
                self.perf_text.setPlainText(perf_text)
    
    def _get_cell_by_id(self, cell_id: str):
        """ID로 셀 찾기"""
        for cell in self.services.grid_manager.cells:
            if cell.id == cell_id:
                return cell
        return None
    
    def _get_click_position(self, cell) -> Tuple[int, int]:
        """클릭 위치 계산"""
        x, y, w, h = cell.bounds
        click_x = x + w // 2
        click_y = y + h - self.services.config_manager.get('input_box_offset', {}).get('from_bottom', 20)
        return click_x, click_y
    
    def stop_monitoring(self):
        """모니터링 중지"""
        # 병렬 모니터 중지
        if hasattr(self, 'parallel_orchestrator'):
            self.parallel_orchestrator.stop()
            del self.parallel_orchestrator
            
        if hasattr(self, 'parallel_stats_timer'):
            self.parallel_stats_timer.stop()
            
        # 기존 모니터 중지
        if hasattr(self, 'monitoring_thread') and self.monitoring_thread:
            self.monitoring_thread.stop()
            self.monitoring_thread.wait()
            
        self.status_label.setText("[PAUSE] 대기 중...")
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.log("[STOP] 모니터링을 중지했습니다.")
    
    def on_overlay_height_changed(self, value):
        """오버레이 높이 변경 처리"""
        # 10px 단위로 맞춤
        value = (value // 10) * 10
        self.overlay_height_slider.setValue(value)
        self.overlay_height_label.setText(f"{value}px")
        
        # config의 ui_constants 업데이트
        if hasattr(self.services.config_manager, 'ui_constants'):
            self.services.config_manager.ui_constants.overlay_height = value
        else:
            # ui_constants가 없으면 생성
            self.services.config_manager.ui_constants = type('UIConstants', (), {'overlay_height': value})()
        
        # GridManager의 셀들 업데이트
        self.services.grid_manager._create_grid_cells()
        
        # 오버레이가 표시 중이면 업데이트
        if self.overlay:
            self.overlay.update()
        
        self.log(f"오버레이 높이 변경: {value}px")
    
    def toggle_test_mode(self, state):
        """테스트 모드 토글"""
        is_enabled = state == Qt.Checked
        self.test_cell_combo.setEnabled(is_enabled)
        
        if is_enabled:
            self.log("테스트 모드 활성화 - 선택한 셀만 감지합니다")
        else:
            self.log("테스트 모드 비활성화 - 모든 셀을 감지합니다")
    
    def toggle_overlay(self):
        """오버레이 토글"""
        if self.overlay:
            self.overlay.close()
            self.overlay = None
            self.overlay_btn.setText("오버레이 표시")
            self.log("오버레이를 숨겼습니다.")
        else:
            self.overlay = GridOverlayWidget(self.services.grid_manager)
            self.overlay.show()
            self.overlay_btn.setText("오버레이 숨기기")
            self.log("오버레이를 표시했습니다.")
    
    def on_detection(self, cell_id, text, x, y):
        """감지 이벤트 처리"""
        self.detection_count += 1
        self.detection_count_label.setText(f"감지: {self.detection_count}회")
        self.log(f"감지: [{cell_id}] {text}")
        
        if self.overlay:
            self.overlay.update()
    
    def on_automation(self, cell_id, result):
        """자동화 결과 처리"""
        if "성공" in result:
            self.automation_count += 1
            self.automation_count_label.setText(f"자동화: {self.automation_count}회")
        self.log(f"자동화: [{cell_id}] {result}")
    
    def on_status_update(self, message):
        """상태 업데이트"""
        self.log(f"{message}")
    
    def apply_settings(self):
        """설정 적용"""
        # TODO: 설정 적용 로직
        self.log("[OK] 설정을 적용했습니다.")
    
    def log(self, message):
        """로그 추가 (밀리초 포함)"""
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]  # 밀리초까지만
        self.log_text.append(f"[{timestamp}] {message}")
        
        # 로그 크기 제한 (QTextCursor 사용 최소화)
        if self.log_text.document().lineCount() > 500:
            # 간단한 방법으로 텍스트 제한
            text = self.log_text.toPlainText()
            lines = text.split('\n')
            if len(lines) > 400:
                self.log_text.setPlainText('\n'.join(lines[-400:]))
    
    def update_cell_status(self, cell_id: str, status: str, timestamp: str = None):
        """셀 상태 테이블 업데이트"""
        if not self.cell_status_table:
            return
            
        if timestamp is None:
            timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        
        # 텍스트 추출 (상태에서)
        text = ""
        if ":" in status:
            parts = status.split(":", 1)
            if len(parts) > 1:
                text = parts[1].strip()[:50]  # 50자까지만
                status = parts[0].strip()
        
        # 딕셔너리에 상태 저장
        self.cell_status_dict[cell_id] = {
            'timestamp': timestamp,
            'status': status,
            'text': text
        }
        
        # 테이블 업데이트
        self.refresh_cell_status_table()
    
    def refresh_cell_status_table(self):
        """셀 상태 테이블 새로고침"""
        if not self.cell_status_table:
            return
            
        # 테이블 초기화
        self.cell_status_table.setRowCount(len(self.cell_status_dict))
        
        # 셀 ID로 정렬
        sorted_cells = sorted(self.cell_status_dict.items(), 
                            key=lambda x: (x[0].split('_')[0], int(x[0].split('_')[1]) if '_' in x[0] else 0))
        
        for row, (cell_id, data) in enumerate(sorted_cells):
            self.cell_status_table.setItem(row, 0, QTableWidgetItem(cell_id))
            self.cell_status_table.setItem(row, 1, QTableWidgetItem(data['timestamp']))
            self.cell_status_table.setItem(row, 2, QTableWidgetItem(data['status']))
            self.cell_status_table.setItem(row, 3, QTableWidgetItem(data['text']))
            
            # 상태에 따라 색상 설정
            if '트리거' in data['status']:
                for col in range(4):
                    item = self.cell_status_table.item(row, col)
                    if item:
                        item.setBackground(QColor(255, 200, 200))  # 연한 빨간색
            elif 'OCR' in data['status']:
                for col in range(4):
                    item = self.cell_status_table.item(row, col)
                    if item:
                        item.setBackground(QColor(200, 255, 200))  # 연한 초록색
            elif '자동화' in data['status']:
                for col in range(4):
                    item = self.cell_status_table.item(row, col)
                    if item:
                        item.setBackground(QColor(200, 200, 255))  # 연한 파란색
    
    def on_performance_update(self, metrics):
        """성능 메트릭 업데이트"""
        # 변화 감지 통계 업데이트
        if isinstance(metrics, dict) and 'change_detection' in metrics:
            stats = metrics['change_detection']
            skip_percent = stats.get('skip_ratio', 0) * 100
            efficiency = stats.get('efficiency_gain', 0)
            self.change_detection_label.setText(f"변화 감지: 스킵 {skip_percent:.0f}% (효율 +{efficiency:.0f}%)")
            return
        
        # UI 요소가 있는지 확인 후 업데이트
        if hasattr(metrics, 'cpu_percent') and hasattr(self, 'cpu_label') and self.cpu_label:
            self.cpu_label.setText(f"CPU: {metrics.cpu_percent:.1f}%")
        
        if hasattr(metrics, 'memory_mb') and hasattr(self, 'memory_label') and self.memory_label:
            self.memory_label.setText(f"메모리: {metrics.memory_mb:.0f}MB")
        
        if self.ocr_latency_label and metrics.ocr_latency_ms:
            self.ocr_latency_label.setText(f"OCR 레이턴시: {metrics.ocr_latency_ms:.1f}ms")
        
        # 캐시 히트율 계산
        if self.cache_hit_label and hasattr(self, 'monitoring_thread') and self.monitoring_thread:
            if hasattr(self.monitoring_thread, 'ocr_engine'):
                stats = self.monitoring_thread.ocr_engine.ocr_service.get_statistics()
                hit_rate = stats.get('cache_hit_rate', 0)
                self.cache_hit_label.setText(f"캐시 히트율: {hit_rate:.1f}%")
        
        # 최적화 분석 (로그 출력 제거)
        recommendations = self.perf_optimizer.analyze_and_optimize(metrics)
        # 로그 출력하지 않음
    
    def auto_optimize(self):
        """자동 최적화"""
        self.log("자동 최적화 시작...")
        
        # 최적화된 설정 가져오기
        optimized = self.perf_optimizer.get_optimized_settings()
        
        # 설정 적용
        if self.monitoring_thread and hasattr(self.monitoring_thread, 'ocr_engine'):
            # OCR 서비스에 최적화 설정 적용
            stats = self.perf_monitor.get_current_stats()
            self.monitoring_thread.ocr_engine.ocr_service.optimize_settings({
                'cpu_percent': stats.avg_cpu,
                'avg_ocr_latency': stats.avg_ocr_latency
            })
        
        self.log(f"[OK] 최적화 완료: OCR 워커 {optimized['max_concurrent_ocr']}개, 배치 {optimized['batch_size']}개")
    
    def closeEvent(self, event):
        """종료 이벤트"""
        self.stop_monitoring()
        if self.overlay:
            self.overlay.close()
        
        # 초고속 캡처 엔진 종료
        if self.monitoring_thread and hasattr(self.monitoring_thread, 'ultra_fast_capture'):
            if self.monitoring_thread.ultra_fast_capture:
                self.monitoring_thread.ultra_fast_capture.shutdown()
        
        # 성능 모니터 및 캐시 정리
        self.perf_monitor.stop()
        self.cache_manager.stop()
        self.cache_manager.save_cache_to_disk()
        
        # 성능 통계 내보내기
        try:
            self.perf_monitor.export_metrics('performance_stats.json')
            self.log("성능 통계 저장: performance_stats.json")
        except:
            pass
        
        self.services.cleanup()
        event.accept()

def main():
    """메인 함수"""
    app = QApplication(sys.argv)
    
    # GUI 실행
    gui = UnifiedChatbotGUI()
    gui.show()
    
    print("통합 카카오톡 챗봇 시스템 v2.0")
    print("듀얼 모니터 30개 셀 지원")
    print("⚡ 실시간 감지 및 자동 응답")
    print("최적화된 성능")
    
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()