#!/usr/bin/env python3
"""
최적화된 카카오톡 챗봇 시스템 - 30개 오버레이 영역 실시간 감지
- 듀얼 모니터 지원 (각 15개씩 총 30개 셀)
- PaddleOCR 한글 인식 최적화
- 실시간 감지 및 자동 응답
- 병목현상 방지 멀티스레딩
Python 3.11+ compatible
"""
from __future__ import annotations

import sys
import json
import time
import queue
import threading
import logging
from typing import Any
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
                            QGroupBox, QGridLayout, QScrollArea, QDoubleSpinBox)
from PyQt5.QtCore import Qt, QTimer, QThread, pyqtSignal
from PyQt5.QtGui import QPainter, QPen, QBrush, QColor, QFont
from screeninfo import get_monitors

# 리팩토링된 서비스들
from core.service_container import ServiceContainer, MonitoringOrchestrator
from core.grid_manager import GridCell, CellStatus

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
    """고성능 OCR 엔진 - 병렬 처리 최적화"""
    
    def __init__(self, config):
        self.config = config
        self.paddle_ocr = None
        self.executor = ThreadPoolExecutor(max_workers=config.get('max_concurrent_ocr', 6))
        
        if PADDLEOCR_AVAILABLE:
            self._init_paddle_ocr()
    
    def _init_paddle_ocr(self):
        """PaddleOCR 초기화 - 최대 성능 설정"""
        try:
            self.paddle_ocr = PaddleOCR(
                use_angle_cls=False,  # 각도 분류 비활성화 (속도 향상)
                lang='korean',
                enable_mkldnn=True,   # Intel MKL-DNN 가속
                cpu_threads=4,        # CPU 스레드 증가
                det_limit_side_len=960,  # 해상도 최적화
                drop_score=0.2,       # 낮은 신뢰도도 감지
                show_log=False,
                use_gpu=False         # CPU 최적화
            )
            print("🚀 고성능 PaddleOCR 엔진 초기화 완료")
        except Exception as e:
            print(f"❌ PaddleOCR 초기화 실패: {e}")
            self.paddle_ocr = None
    
    def preprocess_image_fast(self, image: np.ndarray) -> np.ndarray:
        """빠른 이미지 전처리"""
        try:
            import cv2
            
            # 1. 크기 조정 (4배 확대)
            height, width = image.shape[:2]
            new_width = int(width * 4)
            new_height = int(height * 4)
            image = cv2.resize(image, (new_width, new_height), interpolation=cv2.INTER_CUBIC)
            
            # 2. 그레이스케일 변환
            if len(image.shape) == 3:
                gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            else:
                gray = image.copy()
            
            # 3. 가우시안 블러 제거 (속도 향상)
            
            # 4. 이진화 - 빠른 방법
            binary = cv2.adaptiveThreshold(
                gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                cv2.THRESH_BINARY, 11, 2  # 블록 크기 축소
            )
            
            # 5. 반전
            binary = cv2.bitwise_not(binary)
            
            # 6. 샤프닝 (간소화)
            kernel = np.array([[0, -1, 0], [-1, 5, -1], [0, -1, 0]])
            binary = cv2.filter2D(binary, -1, kernel)
            
            return binary
            
        except Exception as e:
            print(f"전처리 오류: {e}")
            return image
    
    def detect_text_batch(self, images_with_cells: List[Tuple[np.ndarray, GridCell]]) -> List[DetectionResult]:
        """배치 OCR 처리"""
        if not self.paddle_ocr:
            return []
        
        results = []
        futures = []
        
        # 병렬 OCR 실행
        for image, cell in images_with_cells:
            future = self.executor.submit(self._process_single_ocr, image, cell)
            futures.append(future)
        
        # 결과 수집
        for future in futures:
            try:
                result = future.result(timeout=2.0)  # 2초 타임아웃
                if result:
                    results.append(result)
            except Exception as e:
                print(f"OCR 처리 오류: {e}")
        
        return results
    
    def _process_single_ocr(self, image: np.ndarray, cell: GridCell) -> Optional[DetectionResult]:
        """단일 OCR 처리"""
        try:
            # 이미지 전처리
            processed = self.preprocess_image_fast(image)
            
            # OCR 실행
            ocr_results = self.paddle_ocr.ocr(processed, cls=False)
            
            if not ocr_results or not ocr_results[0]:
                return None
            
            # 첫 번째 결과 추출
            first_result = ocr_results[0][0]
            text = first_result[1][0] if first_result[1] else ""
            confidence = first_result[1][1] if first_result[1] else 0.0
            
            # 위치 계산
            position = (0, 0)
            if first_result[0]:
                position = (int(first_result[0][0][0]), int(first_result[0][0][1]))
            
            # 트리거 패턴 확인
            if self._check_trigger_pattern(text):
                return DetectionResult(
                    cell=cell,
                    text=text,
                    confidence=confidence,
                    position=position,
                    timestamp=time.time()
                )
            
            return None
            
        except Exception as e:
            if "primitive" in str(e).lower():
                print("⚠️ PaddleOCR primitive 오류 - OCR 엔진 재시작 필요")
                self.paddle_ocr = None
            return None
    
    def _check_trigger_pattern(self, text: str) -> bool:
        """강화된 트리거 패턴 확인"""
        if not text:
            return False
        
        # 강화된 OCR 보정기 사용
        from ocr.enhanced_ocr_corrector import EnhancedOCRCorrector
        if not hasattr(self, 'corrector'):
            self.corrector = EnhancedOCRCorrector()
        
        is_match, matched_pattern = self.corrector.check_trigger_pattern(text)
        if is_match:
            print(f"🎯 트리거 감지: '{text}' -> '{matched_pattern}'")
            return True
        
        return False

class OptimizedOverlayWidget(QWidget):
    """최적화된 30개 셀 오버레이 위젯"""
    
    def __init__(self, service_container: ServiceContainer):
        super().__init__()
        self.services = service_container
        self.grid_manager = service_container.grid_manager
        self.show_grid = True
        self.show_ocr_areas = True
        self.initUI()
    
    def initUI(self):
        """UI 초기화 - 듀얼 모니터 지원"""
        monitors = get_monitors()
        
        # 전체 화면 범위 계산
        min_x = min(m.x for m in monitors)
        min_y = min(m.y for m in monitors)
        max_x = max(m.x + m.width for m in monitors)
        max_y = max(m.y + m.height for m in monitors)
        
        total_width = max_x - min_x
        total_height = max_y - min_y
        
        # 오버레이 설정
        margin = 10
        self.setGeometry(min_x - margin, min_y - margin, 
                        total_width + 2*margin, total_height + 2*margin)
        
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool
        )
        
        print(f"🖥️ 듀얼 모니터 오버레이 초기화:")
        for i, monitor in enumerate(monitors):
            print(f"   모니터 {i+1}: {monitor.width}x{monitor.height} at ({monitor.x}, {monitor.y})")
        print(f"   총 30개 셀 생성됨 (각 모니터당 15개)")
    
    def paintEvent(self, event):
        """그리드 및 OCR 영역 그리기"""
        if not (self.show_grid or self.show_ocr_areas):
            return
        
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        overlay_x = self.geometry().x()
        overlay_y = self.geometry().y()
        
        for cell in self.grid_manager.cells:
            # 셀 경계 그리기
            if self.show_grid:
                cell_x, cell_y, cell_w, cell_h = cell.bounds
                rel_x = cell_x - overlay_x
                rel_y = cell_y - overlay_y
                
                # 상태별 색상
                if cell.status == CellStatus.TRIGGERED:
                    color = QColor(255, 0, 0, 100)  # 빨강 (트리거됨)
                elif cell.status == CellStatus.COOLDOWN:
                    color = QColor(255, 165, 0, 100)  # 주황 (쿨다운)
                else:
                    color = QColor(0, 255, 0, 50)   # 초록 (대기)
                
                painter.setPen(QPen(color, 2))
                painter.drawRect(rel_x, rel_y, cell_w, cell_h)
            
            # OCR 영역 그리기
            if self.show_ocr_areas:
                ocr_x, ocr_y, ocr_w, ocr_h = cell.ocr_area
                rel_ocr_x = ocr_x - overlay_x
                rel_ocr_y = ocr_y - overlay_y
                
                painter.setPen(QPen(QColor(0, 0, 255), 2))  # 파랑
                painter.fillRect(rel_ocr_x, rel_ocr_y, ocr_w, ocr_h, 
                               QBrush(QColor(0, 0, 255, 30)))
                
                # 셀 ID 표시
                painter.setPen(QPen(QColor(255, 255, 255), 1))
                painter.setFont(QFont("Arial", 8))
                painter.drawText(rel_ocr_x, rel_ocr_y - 5, cell.id)

class RealTimeMonitoringThread(QThread):
    """실시간 모니터링 스레드 - 0.5초 간격"""
    
    detection_signal = pyqtSignal(str, str, float, float)  # cell_id, text, x, y
    automation_signal = pyqtSignal(str, str)  # cell_id, result
    
    def __init__(self, service_container: ServiceContainer):
        super().__init__()
        self.services = service_container
        self.running = False
        self.ocr_engine = HighPerformanceOCREngine(service_container.config_manager._config)
        self.automation_queue = queue.Queue()
        
        # 자동화 처리 스레드 시작
        self.automation_thread = threading.Thread(target=self._automation_worker, daemon=True)
        self.automation_thread.start()
    
    def run(self):
        """메인 감지 루프"""
        print("🚀 실시간 모니터링 시작 - 0.5초 간격")
        self.running = True
        
        with mss.mss() as sct:
            while self.running:
                try:
                    start_time = time.time()
                    
                    # 활성 셀 가져오기 (쿨다운 업데이트 포함)
                    self.services.grid_manager.update_cell_cooldowns()
                    active_cells = [cell for cell in self.services.grid_manager.cells 
                                  if cell.can_be_triggered()]
                    
                    if not active_cells:
                        time.sleep(0.1)
                        continue
                    
                    # 배치로 스크린샷 캡처
                    images_with_cells = []
                    for cell in active_cells[:15]:  # 한 번에 15개씩 처리
                        try:
                            ocr_area = {
                                'left': cell.ocr_area[0],
                                'top': cell.ocr_area[1], 
                                'width': cell.ocr_area[2],
                                'height': cell.ocr_area[3]
                            }
                            screenshot = sct.grab(ocr_area)
                            image = np.array(screenshot)
                            images_with_cells.append((image, cell))
                        except Exception as e:
                            print(f"스크린샷 캡처 오류 {cell.id}: {e}")
                    
                    # 배치 OCR 처리
                    if images_with_cells:
                        detection_results = self.ocr_engine.detect_text_batch(images_with_cells)
                        
                        for result in detection_results:
                            # 셀 상태 업데이트
                            result.cell.set_triggered(result.text, result.position)
                            
                            # GUI 신호 전송
                            self.detection_signal.emit(
                                result.cell.id, result.text, 
                                result.position[0], result.position[1]
                            )
                            
                            # 자동화 큐에 추가
                            self.automation_queue.put(result)
                    
                    # 주기 조절 (0.5초 목표)
                    elapsed = time.time() - start_time
                    sleep_time = max(0.5 - elapsed, 0.05)  # 최소 0.05초
                    if sleep_time > 0:
                        time.sleep(sleep_time)
                    
                except Exception as e:
                    print(f"모니터링 루프 오류: {e}")
                    time.sleep(0.5)
    
    def _automation_worker(self):
        """자동화 처리 워커"""
        while True:
            try:
                result = self.automation_queue.get()
                
                # 자동화 실행
                automation_result = self.services.automation_service.execute_full_automation(
                    result.cell.bounds,
                    result.position
                )
                
                if automation_result.success:
                    # 성공 시 일반 쿨다운
                    result.cell.set_cooldown(self.services.config_manager.cooldown_sec)
                    self.automation_signal.emit(result.cell.id, "SUCCESS")
                else:
                    # 실패 시 긴 쿨다운
                    result.cell.set_cooldown(
                        self.services.config_manager.timing_config.cooldown_after_failure
                    )
                    self.automation_signal.emit(result.cell.id, f"FAILED: {automation_result.message}")
                
                self.automation_queue.task_done()
                
            except Exception as e:
                print(f"자동화 처리 오류: {e}")
    
    def stop(self):
        """모니터링 중지"""
        self.running = False

class OptimizedChatbotGUI(QWidget):
    """최적화된 챗봇 GUI - 30개 셀 관리"""
    
    def __init__(self):
        super().__init__()
        self.services = ServiceContainer()
        self.overlay = None
        self.monitoring_thread = None
        self.initUI()
    
    def initUI(self):
        """GUI 초기화"""
        self.setWindowTitle("카카오톡 챗봇 시스템 - 30개 오버레이 실시간 감지")
        self.setGeometry(100, 100, 600, 800)
        
        layout = QVBoxLayout()
        
        # 상태 정보
        status_group = QGroupBox("시스템 상태")
        status_layout = QVBoxLayout()
        
        self.status_label = QLabel("대기 중...")
        self.cell_count_label = QLabel(f"총 셀 개수: {len(self.services.grid_manager.cells)}개")
        self.ocr_status_label = QLabel("OCR: 준비됨" if PADDLEOCR_AVAILABLE else "OCR: 비활성화")
        
        status_layout.addWidget(self.status_label)
        status_layout.addWidget(self.cell_count_label)
        status_layout.addWidget(self.ocr_status_label)
        status_group.setLayout(status_layout)
        
        # 제어 버튼
        control_group = QGroupBox("제어")
        control_layout = QHBoxLayout()
        
        self.start_btn = QPushButton("모니터링 시작")
        self.stop_btn = QPushButton("모니터링 중지")
        self.overlay_btn = QPushButton("오버레이 표시")
        
        self.start_btn.clicked.connect(self.start_monitoring)
        self.stop_btn.clicked.connect(self.stop_monitoring)
        self.overlay_btn.clicked.connect(self.toggle_overlay)
        
        control_layout.addWidget(self.start_btn)
        control_layout.addWidget(self.stop_btn)
        control_layout.addWidget(self.overlay_btn)
        control_group.setLayout(control_layout)
        
        # 로그
        log_group = QGroupBox("실시간 로그")
        log_layout = QVBoxLayout()
        
        self.log_text = QTextEdit()
        self.log_text.setMaximumHeight(300)
        log_layout.addWidget(self.log_text)
        log_group.setLayout(log_layout)
        
        # 통계
        stats_group = QGroupBox("실시간 통계")
        stats_layout = QGridLayout()
        
        self.stats_labels = {}
        stats_items = [
            ("감지 횟수:", "detections"), ("자동화 성공:", "success"),
            ("자동화 실패:", "failed"), ("활성 셀:", "active_cells")
        ]
        
        for i, (label, key) in enumerate(stats_items):
            stats_layout.addWidget(QLabel(label), i, 0)
            self.stats_labels[key] = QLabel("0")
            stats_layout.addWidget(self.stats_labels[key], i, 1)
        
        stats_group.setLayout(stats_layout)
        
        # 레이아웃 구성
        layout.addWidget(status_group)
        layout.addWidget(control_group)
        layout.addWidget(log_group)
        layout.addWidget(stats_group)
        
        self.setLayout(layout)
        
        # 통계 업데이트 타이머
        self.stats_timer = QTimer()
        self.stats_timer.timeout.connect(self.update_stats)
        self.stats_timer.start(1000)  # 1초마다 업데이트
        
        # 통계 변수
        self.detection_count = 0
        self.success_count = 0
        self.failed_count = 0
    
    def start_monitoring(self):
        """모니터링 시작"""
        if not PADDLEOCR_AVAILABLE:
            self.log("❌ PaddleOCR이 설치되지 않아 모니터링을 시작할 수 없습니다.")
            return
        
        if self.monitoring_thread and self.monitoring_thread.running:
            self.log("⚠️ 이미 모니터링이 실행 중입니다.")
            return
        
        self.monitoring_thread = RealTimeMonitoringThread(self.services)
        self.monitoring_thread.detection_signal.connect(self.on_detection)
        self.monitoring_thread.automation_signal.connect(self.on_automation)
        self.monitoring_thread.start()
        
        self.status_label.setText("🚀 실시간 모니터링 중...")
        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.log("🚀 30개 셀 실시간 모니터링 시작!")
    
    def stop_monitoring(self):
        """모니터링 중지"""
        if self.monitoring_thread:
            self.monitoring_thread.stop()
            self.monitoring_thread.wait()
            self.monitoring_thread = None
        
        self.status_label.setText("⏹️ 모니터링 중지됨")
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.log("⏹️ 모니터링 중지")
    
    def toggle_overlay(self):
        """오버레이 토글"""
        if self.overlay:
            self.overlay.close()
            self.overlay = None
            self.overlay_btn.setText("오버레이 표시")
            self.log("🔍 오버레이 숨김")
        else:
            self.overlay = OptimizedOverlayWidget(self.services)
            self.overlay.show()
            self.overlay_btn.setText("오버레이 숨김")
            self.log("🔍 30개 셀 오버레이 표시")
    
    def on_detection(self, cell_id: str, text: str, x: float, y: float):
        """감지 이벤트 처리"""
        self.detection_count += 1
        self.log(f"🎯 {cell_id}: '{text}' 감지 at ({x:.0f}, {y:.0f})")
    
    def on_automation(self, cell_id: str, result: str):
        """자동화 이벤트 처리"""
        if result == "SUCCESS":
            self.success_count += 1
            self.log(f"✅ {cell_id}: 자동 응답 성공")
        else:
            self.failed_count += 1
            self.log(f"❌ {cell_id}: {result}")
    
    def update_stats(self):
        """통계 업데이트"""
        self.stats_labels["detections"].setText(str(self.detection_count))
        self.stats_labels["success"].setText(str(self.success_count))
        self.stats_labels["failed"].setText(str(self.failed_count))
        
        active_cells = len([c for c in self.services.grid_manager.cells if c.can_be_triggered()])
        self.stats_labels["active_cells"].setText(str(active_cells))
    
    def log(self, message: str):
        """로그 추가"""
        timestamp = time.strftime("%H:%M:%S")
        self.log_text.append(f"[{timestamp}] {message}")
        
        # 스크롤을 맨 아래로
        scrollbar = self.log_text.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
    
    def closeEvent(self, event):
        """프로그램 종료 시 정리"""
        self.stop_monitoring()
        if self.overlay:
            self.overlay.close()
        self.services.cleanup()
        event.accept()

def main():
    """메인 함수"""
    app = QApplication(sys.argv)
    
    # GUI 실행
    gui = OptimizedChatbotGUI()
    gui.show()
    
    print("🎉 최적화된 카카오톡 챗봇 시스템 시작!")
    print("📊 듀얼 모니터 30개 셀 지원")
    print("⚡ 실시간 감지 (0.5초 간격)")
    print("🚀 PaddleOCR 한글 최적화")
    print("🔄 멀티스레딩 병목현상 방지")
    
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()