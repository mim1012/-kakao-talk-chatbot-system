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
import queue
import threading
import logging
import os
from typing import Any, Tuple, List, Optional
import numpy as np
import mss
import pyautogui
import pyperclip
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass

# Windows DPI 설정
if sys.platform == "win32":
    import ctypes
    ctypes.windll.shcore.SetProcessDpiAwareness(2)

# PyQt5 GUI
from PyQt5.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout, 
                            QLabel, QPushButton, QTextEdit, QSpinBox, QCheckBox, 
                            QGroupBox, QGridLayout, QScrollArea, QDoubleSpinBox,
                            QSlider, QComboBox, QTabWidget)
from PyQt5.QtCore import Qt, QTimer, QThread, pyqtSignal, QRect
from PyQt5.QtGui import QPainter, QPen, QBrush, QColor, QFont
from screeninfo import get_monitors

# 서비스 임포트
from core.service_container import ServiceContainer, MonitoringOrchestrator
from core.grid_manager import GridCell, CellStatus
from core.cache_manager import CacheManager
from monitoring.performance_monitor import PerformanceMonitor, PerformanceOptimizer
from ocr.optimized_ocr_service import OptimizedOCRService
from utils.suppress_output import suppress_stdout_stderr

# PaddleOCR
try:
    from paddleocr import PaddleOCR
    PADDLEOCR_AVAILABLE = True
except ImportError:
    PADDLEOCR_AVAILABLE = False
    print("⚠️ PaddleOCR not available")

@dataclass
class DetectionResult:
    """감지 결과 데이터"""
    cell: GridCell
    text: str
    confidence: float
    position: Tuple[int, int]
    timestamp: float

class HighPerformanceOCREngine:
    """고성능 OCR 엔진 - 병렬 처리 최적화 (Deprecated - OptimizedOCRService 사용)"""
    
    def __init__(self, config, cache_manager=None, perf_monitor=None):
        self.config = config
        self.cache = cache_manager
        self.perf_monitor = perf_monitor
        # OptimizedOCRService로 대체
        self.ocr_service = OptimizedOCRService(config, cache_manager, perf_monitor)
        self.executor = self.ocr_service.executor
    
    def _init_paddle_ocr(self):
        """PaddleOCR 초기화"""
        try:
            with suppress_stdout_stderr():
                self.paddle_ocr = PaddleOCR(lang='korean')
            print("🚀 고성능 PaddleOCR 엔진 초기화 완료")
        except Exception as e:
            print(f"❌ PaddleOCR 초기화 실패: {e}")
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
        """배치 OCR 처리 (OptimizedOCRService로 위임)"""
        # 새로운 형식으로 변환
        images_with_regions = []
        cells = []
        
        for image, cell in images_with_cells:
            region = (cell.ocr_area[0], cell.ocr_area[1], 
                     cell.ocr_area[2], cell.ocr_area[3])
            images_with_regions.append((image, region))
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
            
            # OCR 수행
            with suppress_stdout_stderr():
                result = self.paddle_ocr.ocr(processed, cls=True)
            
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
    
    def _check_trigger_patterns(self, text: str) -> bool:
        """트리거 패턴 확인"""
        trigger_patterns = ["들어왔습니다", "입장했습니다", "참여했습니다"]
        return any(pattern in text for pattern in trigger_patterns)

class RealTimeMonitoringThread(QThread):
    """실시간 모니터링 스레드"""
    
    detection_signal = pyqtSignal(str, str, float, float)  # cell_id, text, x, y
    automation_signal = pyqtSignal(str, str)  # cell_id, result
    status_signal = pyqtSignal(str)  # status message
    performance_signal = pyqtSignal(dict)  # performance metrics
    
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
        
        # 자동화 처리 스레드
        self.automation_thread = threading.Thread(target=self._automation_worker, daemon=True)
        self.automation_thread.start()
    
    def run(self):
        """메인 감지 루프"""
        print("🚀 실시간 모니터링 시작")
        self.running = True
        self.status_signal.emit("🚀 모니터링 시작")
        
        with mss.mss() as sct:
            while self.running:
                try:
                    start_time = time.time()
                    
                    # 활성 셀 가져오기
                    self.services.grid_manager.update_cell_cooldowns()
                    active_cells = [cell for cell in self.services.grid_manager.cells 
                                  if cell.can_be_triggered()]
                    
                    if not active_cells:
                        time.sleep(0.1)
                        continue
                    
                    # 동적 배치 크기 결정
                    if self.perf_monitor:
                        stats = self.perf_monitor.get_current_stats()
                        if stats.avg_cpu > 70:
                            batch_size = 8  # CPU 부하가 높으면 배치 크기 감소
                        else:
                            batch_size = 15
                    else:
                        batch_size = 15
                    
                    # 배치 스크린샷 (최적화된 크기)
                    images_with_regions = []
                    capture_start = time.time()
                    
                    for cell in active_cells[:batch_size]:
                        try:
                            ocr_area = {
                                'left': cell.ocr_area[0],
                                'top': cell.ocr_area[1], 
                                'width': cell.ocr_area[2],
                                'height': cell.ocr_area[3]
                            }
                            screenshot = sct.grab(ocr_area)
                            image = np.array(screenshot)
                            region = (cell.ocr_area[0], cell.ocr_area[1], 
                                    cell.ocr_area[2], cell.ocr_area[3])
                            images_with_regions.append((image, region))
                        except Exception as e:
                            print(f"스크린샷 오류 {cell.id}: {e}")
                    
                    # 스크린 캡처 시간 기록
                    if self.perf_monitor:
                        capture_time = (time.time() - capture_start) * 1000
                        self.perf_monitor.record_capture_latency(capture_time)
                    
                    # 배치 OCR 처리 (최적화된 서비스 사용)
                    results = self.ocr_engine.ocr_service.perform_batch_ocr(images_with_regions)
                    
                    # 결과와 셀 매핑
                    for i, result in enumerate(results):
                        if i < len(active_cells) and result.text:
                            cell = active_cells[i]
                            # 트리거 패턴 확인
                            if self.ocr_engine.ocr_service.check_trigger_patterns(result.text):
                                detection_result = DetectionResult(
                                    cell=cell,
                                    text=result.text,
                                    confidence=result.confidence,
                                    position=result.position,
                                    timestamp=result.timestamp
                                )
                                results.append(detection_result)
                    
                    # 결과 처리
                    for result in results:
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
                    
                    # 주기 조절
                    elapsed = time.time() - start_time
                    if elapsed < 0.5:
                        time.sleep(0.5 - elapsed)
                        
                except Exception as e:
                    print(f"모니터링 오류: {e}")
                    self.status_signal.emit(f"❌ 오류: {str(e)}")
                    time.sleep(1)
    
    def _automation_worker(self):
        """자동화 처리 워커"""
        while True:
            try:
                result = self.automation_queue.get(timeout=1)
                
                # 자동화 실행
                success = self._execute_automation(result)
                
                # 결과 신호
                status = "✅ 성공" if success else "❌ 실패"
                self.automation_signal.emit(result.cell.id, status)
                
            except queue.Empty:
                continue
            except Exception as e:
                print(f"자동화 오류: {e}")
    
    def _execute_automation(self, result: DetectionResult) -> bool:
        """자동화 실행"""
        try:
            cell = result.cell
            x, y = cell.detected_text_position
            
            # 입력창 클릭
            pyautogui.click(x, y + 100)
            time.sleep(0.2)
            
            # 텍스트 입력
            pyperclip.copy("어서오세요! 환영합니다 😊")
            pyautogui.hotkey('ctrl', 'v')
            time.sleep(0.1)
            
            # 전송
            pyautogui.press('enter')
            
            # 쿨다운 설정
            cell.set_cooldown(5.0)
            
            return True
            
        except Exception as e:
            print(f"자동화 실행 오류: {e}")
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
        """그리기 이벤트"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # 그리드 그리기
        grid_pen = QPen(self.grid_color, self.grid_line_width)
        painter.setPen(grid_pen)
        
        for cell in self.grid_manager.cells:
            x, y, w, h = cell.bounds
            
            # 셀 테두리
            painter.drawRect(x, y, w, h)
            
            # 셀 상태에 따른 색상
            if cell.status == CellStatus.TRIGGERED:
                painter.fillRect(x, y, w, h, QBrush(self.active_color))
            elif cell.status == CellStatus.COOLDOWN:
                painter.fillRect(x, y, w, h, QBrush(self.cooldown_color))
            
            # OCR 영역 표시
            ocr_x, ocr_y, ocr_w, ocr_h = cell.ocr_area
            ocr_pen = QPen(QColor(255, 255, 0, 150), 2, Qt.DashLine)
            painter.setPen(ocr_pen)
            painter.drawRect(ocr_x, ocr_y, ocr_w, ocr_h)
            
            # 셀 ID 표시
            painter.setPen(QPen(Qt.white))
            painter.setFont(QFont("Arial", 10))
            painter.drawText(x + 5, y + 15, cell.id)

class UnifiedChatbotGUI(QWidget):
    """통합 챗봇 GUI - 모든 기능 포함"""
    
    def __init__(self):
        super().__init__()
        self.services = ServiceContainer()
        
        # 성능 최적화 컴포넌트
        self.cache_manager = CacheManager(self.services.config_manager._config)
        self.perf_monitor = PerformanceMonitor()
        self.perf_optimizer = PerformanceOptimizer(self.perf_monitor)
        
        # 캐시와 모니터 시작
        self.cache_manager.start()
        self.perf_monitor.start()
        
        # 성능 콜백 등록
        self.perf_monitor.add_callback(self.on_performance_update)
        
        self.monitoring_thread = None
        self.overlay = None
        self.init_ui()
        self.log("🎉 통합 카카오톡 챗봇 시스템 시작!")
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
        self.status_label = QLabel("⏸️ 대기 중...")
        self.status_label.setStyleSheet("font-size: 14px; font-weight: bold; padding: 10px;")
        main_tab_layout.addWidget(self.status_label)
        
        # 컨트롤 버튼
        control_layout = QHBoxLayout()
        
        self.start_btn = QPushButton("🚀 모니터링 시작")
        self.start_btn.clicked.connect(self.start_monitoring)
        control_layout.addWidget(self.start_btn)
        
        self.stop_btn = QPushButton("⏹️ 모니터링 중지")
        self.stop_btn.clicked.connect(self.stop_monitoring)
        self.stop_btn.setEnabled(False)
        control_layout.addWidget(self.stop_btn)
        
        self.overlay_btn = QPushButton("📐 오버레이 표시")
        self.overlay_btn.clicked.connect(self.toggle_overlay)
        control_layout.addWidget(self.overlay_btn)
        
        main_tab_layout.addLayout(control_layout)
        
        # 로그 영역
        log_group = QGroupBox("📋 실시간 로그")
        log_layout = QVBoxLayout()
        
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMaximumHeight(400)
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
        optimize_btn = QPushButton("🚀 자동 최적화")
        optimize_btn.clicked.connect(self.auto_optimize)
        perf_layout.addWidget(optimize_btn)
        
        perf_group.setLayout(perf_layout)
        layout.addWidget(perf_group)
        
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
            self.log("❌ PaddleOCR이 설치되지 않았습니다.")
            return
        
        if self.monitoring_thread and self.monitoring_thread.running:
            self.log("⚠️ 이미 모니터링 중입니다.")
            return
        
        self.monitoring_thread = RealTimeMonitoringThread(
            self.services, 
            self.cache_manager,
            self.perf_monitor
        )
        self.monitoring_thread.detection_signal.connect(self.on_detection)
        self.monitoring_thread.automation_signal.connect(self.on_automation)
        self.monitoring_thread.status_signal.connect(self.on_status_update)
        self.monitoring_thread.start()
        
        self.status_label.setText("🚀 실시간 모니터링 중...")
        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.log("✅ 모니터링을 시작했습니다.")
    
    def stop_monitoring(self):
        """모니터링 중지"""
        if self.monitoring_thread:
            self.monitoring_thread.stop()
            self.monitoring_thread.wait()
            
        self.status_label.setText("⏸️ 대기 중...")
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.log("⏹️ 모니터링을 중지했습니다.")
    
    def toggle_overlay(self):
        """오버레이 토글"""
        if self.overlay:
            self.overlay.close()
            self.overlay = None
            self.overlay_btn.setText("📐 오버레이 표시")
            self.log("오버레이를 숨겼습니다.")
        else:
            self.overlay = GridOverlayWidget(self.services.grid_manager)
            self.overlay.show()
            self.overlay_btn.setText("📐 오버레이 숨기기")
            self.log("오버레이를 표시했습니다.")
    
    def on_detection(self, cell_id, text, x, y):
        """감지 이벤트 처리"""
        self.detection_count += 1
        self.detection_count_label.setText(f"감지: {self.detection_count}회")
        self.log(f"🔍 감지: [{cell_id}] {text}")
        
        if self.overlay:
            self.overlay.update()
    
    def on_automation(self, cell_id, result):
        """자동화 결과 처리"""
        if "성공" in result:
            self.automation_count += 1
            self.automation_count_label.setText(f"자동화: {self.automation_count}회")
        self.log(f"🤖 자동화: [{cell_id}] {result}")
    
    def on_status_update(self, message):
        """상태 업데이트"""
        self.log(f"📢 {message}")
    
    def apply_settings(self):
        """설정 적용"""
        # TODO: 설정 적용 로직
        self.log("✅ 설정을 적용했습니다.")
    
    def log(self, message):
        """로그 추가"""
        timestamp = time.strftime("%H:%M:%S")
        self.log_text.append(f"[{timestamp}] {message}")
        
        # 로그 크기 제한
        if self.log_text.document().lineCount() > 1000:
            cursor = self.log_text.textCursor()
            cursor.movePosition(cursor.Start)
            cursor.movePosition(cursor.Down, cursor.KeepAnchor, 100)
            cursor.removeSelectedText()
    
    def on_performance_update(self, metrics):
        """성능 메트릭 업데이트"""
        # UI 업데이트
        self.cpu_label.setText(f"CPU: {metrics.cpu_percent:.1f}%")
        self.memory_label.setText(f"메모리: {metrics.memory_mb:.0f}MB")
        
        if metrics.ocr_latency_ms:
            self.ocr_latency_label.setText(f"OCR 레이턴시: {metrics.ocr_latency_ms:.1f}ms")
        
        # 캐시 히트율 계산
        if hasattr(self.monitoring_thread, 'ocr_engine'):
            stats = self.monitoring_thread.ocr_engine.ocr_service.get_statistics()
            hit_rate = stats.get('cache_hit_rate', 0)
            self.cache_hit_label.setText(f"캐시 히트율: {hit_rate:.1f}%")
        
        # 최적화 분석
        recommendations = self.perf_optimizer.analyze_and_optimize(metrics)
        if recommendations:
            for rec in recommendations:
                self.log(f"💡 최적화 제안: {rec}")
    
    def auto_optimize(self):
        """자동 최적화"""
        self.log("🚀 자동 최적화 시작...")
        
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
        
        self.log(f"✅ 최적화 완료: OCR 워커 {optimized['max_concurrent_ocr']}개, 배치 {optimized['batch_size']}개")
    
    def closeEvent(self, event):
        """종료 이벤트"""
        self.stop_monitoring()
        if self.overlay:
            self.overlay.close()
        
        # 성능 모니터 및 캐시 정리
        self.perf_monitor.stop()
        self.cache_manager.stop()
        self.cache_manager.save_cache_to_disk()
        
        # 성능 통계 내보내기
        try:
            self.perf_monitor.export_metrics('performance_stats.json')
            self.log("📊 성능 통계 저장: performance_stats.json")
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
    
    print("🎉 통합 카카오톡 챗봇 시스템 v2.0")
    print("📊 듀얼 모니터 30개 셀 지원")
    print("⚡ 실시간 감지 및 자동 응답")
    print("🚀 최적화된 성능")
    
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()