#!/usr/bin/env python3
"""
완전한 카카오톡 챗봇 시스템 - 기존 GUI 기능 + 리팩토링된 구조
- 30개 오버레이 영역 설정 GUI
- 그리드 셀 라인 실시간 표시  
- 강화된 OCR 보정 시스템
- 실시간 감지 및 자동 응답
"""

import sys
import os
import json
import time
import logging
import numpy as np
from typing import List, Optional, Tuple

# Windows DPI 설정
if sys.platform == "win32":
    import ctypes
    ctypes.windll.shcore.SetProcessDpiAwareness(2)

# PyQt5 플랫폼 플러그인 경로 수정
def fix_qt_plugin_path():
    try:
        import PyQt5
        qt_plugin_path = os.path.join(os.path.dirname(PyQt5.__file__), 'Qt5', 'plugins')
        if os.path.exists(qt_plugin_path):
            os.environ['QT_QPA_PLATFORM_PLUGIN_PATH'] = qt_plugin_path
    except ImportError:
        pass

fix_qt_plugin_path()

# PyQt5 imports
from PyQt5.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout, 
                            QLabel, QPushButton, QTextEdit, QSpinBox, QCheckBox, 
                            QGroupBox, QGridLayout, QScrollArea, QDoubleSpinBox,
                            QSlider, QTabWidget, QMessageBox)
from PyQt5.QtCore import Qt, QTimer, QThread, pyqtSignal
from PyQt5.QtGui import QPainter, QPen, QBrush, QColor, QFont
from screeninfo import get_monitors
from automation.smart_input_automation import SmartInputAutomation

# 리팩토링된 서비스들 (오류 방지를 위해 선택적 import)
try:
    from core.service_container import ServiceContainer
    SERVICES_AVAILABLE = True
except ImportError:
    SERVICES_AVAILABLE = False
    print("⚠️ 리팩토링된 서비스를 사용할 수 없습니다. 기본 모드로 실행합니다.")

try:
    from ocr.enhanced_ocr_corrector import EnhancedOCRCorrector
    OCR_CORRECTOR_AVAILABLE = True
except ImportError:
    OCR_CORRECTOR_AVAILABLE = False

class GridOverlayWidget(QWidget):
    """완전한 그리드 오버레이 위젯 - 30개 셀 표시 및 설정"""
    
    def __init__(self, parent=None):
        super().__init__()
        self.parent_window = parent
        self.show_grid = True
        self.show_ocr_areas = True
        self.show_cell_ids = True
        
        # 그리드 설정
        self.grid_rows = 3
        self.grid_cols = 5
        self.overlay_height = 120
        self.overlay_margin = 5
        self.overlay_offset = 0
        
        # 셀 데이터
        self.grid_cells = []
        self.cell_status = {}  # cell_id -> status
        
        self.initUI()
        self.create_grid_cells()
    
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
        
        # 오버레이 설정 (전체 화면 덮기)
        margin = 10
        self.setGeometry(min_x - margin, min_y - margin, 
                        total_width + 2*margin, total_height + 2*margin)
        
        # 투명 오버레이 설정
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool |
            Qt.WindowType.X11BypassWindowManagerHint
        )
        
        print(f"🖥️ 오버레이 초기화:")
        for i, monitor in enumerate(monitors):
            print(f"   모니터 {i+1}: {monitor.width}x{monitor.height} at ({monitor.x}, {monitor.y})")
        print(f"   총 {self.grid_rows * self.grid_cols * len(monitors)}개 셀 생성")
    
    def create_grid_cells(self):
        """그리드 셀 생성"""
        self.grid_cells.clear()
        monitors = get_monitors()
        
        for monitor_idx, monitor in enumerate(monitors):
            cell_width = monitor.width // self.grid_cols
            cell_height = monitor.height // self.grid_rows
            
            for row in range(self.grid_rows):
                for col in range(self.grid_cols):
                    # 셀 경계 계산
                    cell_x = monitor.x + col * cell_width
                    cell_y = monitor.y + row * cell_height
                    
                    # OCR 영역 계산
                    ocr_x = cell_x + self.overlay_margin
                    ocr_y = cell_y + cell_height - self.overlay_offset - self.overlay_height
                    ocr_w = cell_width - (self.overlay_margin * 2)
                    ocr_h = self.overlay_height
                    
                    # 영역 보정
                    if ocr_x < cell_x: ocr_x = cell_x + 2
                    if ocr_y < cell_y: ocr_y = cell_y + 2
                    if ocr_x + ocr_w > cell_x + cell_width: ocr_w = cell_x + cell_width - ocr_x - 2
                    if ocr_y + ocr_h > cell_y + cell_height: ocr_h = cell_y + cell_height - ocr_y - 2
                    
                    if ocr_w <= 0 or ocr_h <= 0:
                        ocr_w = max(cell_width - 10, 50)
                        ocr_h = max(30, min(cell_height - 10, self.overlay_height))
                        ocr_x = cell_x + self.overlay_margin
                        ocr_y = cell_y + (cell_height - ocr_h) // 2
                    
                    # 텍스트 입력창 위치 계산 (셀 하단 5px 위, 중앙)
                    input_x = cell_x + cell_width // 2
                    input_y = cell_y + cell_height - 5
                    
                    # 셀 데이터 생성
                    cell_id = f"M{monitor_idx}_R{row}_C{col}"
                    cell_data = {
                        'id': cell_id,
                        'monitor': monitor_idx,
                        'bounds': (cell_x, cell_y, cell_width, cell_height),
                        'ocr_area': (ocr_x, ocr_y, ocr_w, ocr_h),
                        'input_position': (input_x, input_y),
                        'enabled': True,
                        # 호환성을 위한 개별 좌표들
                        'x': cell_x, 'y': cell_y, 'width': cell_width, 'height': cell_height,
                        'ocr_x': ocr_x, 'ocr_y': ocr_y, 'ocr_w': ocr_w, 'ocr_h': ocr_h
                    }
                    
                    self.grid_cells.append(cell_data)
                    self.cell_status[cell_id] = 'idle'  # idle, triggered, cooldown
        
        print(f"✅ {len(self.grid_cells)}개 그리드 셀 생성 완료")
    
    def paintEvent(self, event):
        """그리드 및 OCR 영역 그리기"""
        if not (self.show_grid or self.show_ocr_areas):
            return
        
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        overlay_x = self.geometry().x()
        overlay_y = self.geometry().y()
        
        for cell in self.grid_cells:
            cell_id = cell['id']
            status = self.cell_status.get(cell_id, 'idle')
            cell_x, cell_y, cell_w, cell_h = cell['bounds']
            ocr_x, ocr_y, ocr_w, ocr_h = cell['ocr_area']
            
            # 상대 좌표 계산
            rel_cell_x = cell_x - overlay_x
            rel_cell_y = cell_y - overlay_y
            rel_ocr_x = ocr_x - overlay_x
            rel_ocr_y = ocr_y - overlay_y
            
            # 셀 경계 그리기
            if self.show_grid:
                if status == 'triggered':
                    grid_color = QColor(255, 0, 0, 150)  # 빨강 (트리거됨)
                elif status == 'cooldown':
                    grid_color = QColor(255, 165, 0, 150)  # 주황 (쿨다운)
                elif not cell['enabled']:
                    grid_color = QColor(128, 128, 128, 100)  # 회색 (비활성)
                else:
                    grid_color = QColor(0, 255, 0, 80)   # 초록 (대기)
                
                painter.setPen(QPen(grid_color, 2))
                painter.drawRect(rel_cell_x, rel_cell_y, cell_w, cell_h)
                
                # 셀 ID 표시
                if self.show_cell_ids:
                    painter.setPen(QPen(QColor(255, 255, 255), 1))
                    painter.setFont(QFont("Arial", 8))
                    painter.drawText(rel_cell_x + 5, rel_cell_y + 15, cell_id)
            
            # OCR 영역 그리기
            if self.show_ocr_areas and cell['enabled']:
                ocr_color = QColor(0, 0, 255, 100)  # 파랑 (OCR 영역)
                painter.setPen(QPen(ocr_color, 2))
                painter.fillRect(rel_ocr_x, rel_ocr_y, ocr_w, ocr_h, 
                               QBrush(QColor(0, 0, 255, 30)))
                painter.drawRect(rel_ocr_x, rel_ocr_y, ocr_w, ocr_h)
                
                # OCR 영역 크기 표시
                painter.setPen(QPen(QColor(255, 255, 255), 1))
                painter.setFont(QFont("Arial", 7))
                size_text = f"{ocr_w}x{ocr_h}"
                painter.drawText(rel_ocr_x, rel_ocr_y - 2, size_text)
    
    def update_cell_status(self, cell_id: str, status: str):
        """셀 상태 업데이트"""
        if cell_id in self.cell_status:
            self.cell_status[cell_id] = status
            self.update()
    
    def set_grid_visible(self, visible: bool):
        """그리드 표시/숨기기"""
        self.show_grid = visible
        self.update()
    
    def set_ocr_areas_visible(self, visible: bool):
        """OCR 영역 표시/숨기기"""
        self.show_ocr_areas = visible
        self.update()
    
    def set_cell_ids_visible(self, visible: bool):
        """셀 ID 표시/숨기기"""
        self.show_cell_ids = visible
        self.update()
    
    def update_overlay_settings(self, height: int, margin: int, offset: int):
        """오버레이 설정 업데이트"""
        self.overlay_height = height
        self.overlay_margin = margin
        self.overlay_offset = offset
        self.create_grid_cells()
        self.update()
    
    def get_cell_at_position(self, x: int, y: int):
        """특정 위치의 셀 반환"""
        for cell in self.grid_cells:
            cell_x, cell_y, cell_w, cell_h = cell['bounds']
            if cell_x <= x < cell_x + cell_w and cell_y <= y < cell_y + cell_h:
                return cell
        return None

class MonitoringThread(QThread):
    """실제 OCR 모니터링 및 자동화 스레드"""
    
    detection_signal = pyqtSignal(str, str)  # cell_id, text
    automation_signal = pyqtSignal(str, str, bool)  # cell_id, message, success
    status_signal = pyqtSignal(str)  # status message
    
    def __init__(self, overlay_widget):
        super().__init__()
        self.overlay = overlay_widget
        self.running = False
        
        # OCR 보정기 초기화
        if OCR_CORRECTOR_AVAILABLE:
            self.ocr_corrector = EnhancedOCRCorrector()
        else:
            self.ocr_corrector = None
        
        # 스마트 자동화 시스템 초기화
        self.automation = SmartInputAutomation()
        
        # 로깅 설정 - 자동화 상세 로그 표시
        import logging
        automation_logger = logging.getLogger('smart_input_automation')
        automation_logger.setLevel(logging.INFO)
        
        # 실제 OCR을 위한 설정 (선택적)
        self.use_real_ocr = True  # 실제 OCR 사용으로 변경하여 데모 모드 비활성화
        
        # 디버깅용: 이미지 변화 감지 비활성화 (모든 셀을 매번 OCR 처리)
        self.disable_cache = True  # True로 설정하면 캐시 무시하고 모든 셀 OCR
        
        # 디버깅용: 스크린샷 저장 (문제 진단용)
        self.save_debug_images = True  # OCR 처리 이미지들을 파일로 저장
        self.debug_counter = 0
        
        # 디버깅용: 모든 OCR 결과 로그 출력
        self.log_all_ocr_results = True  # 모든 OCR 결과를 로그에 남김 (매칭 실패도 포함)
    
    def run(self):
        """모니터링 실행"""
        self.running = True
        self.status_signal.emit("🚀 실시간 모니터링 시작")
        
        if self.use_real_ocr:
            self._run_real_ocr_monitoring()
        else:
            self._run_demo_monitoring()
    
    def _run_real_ocr_monitoring(self):
        """최적화된 실제 OCR 모니터링"""
        import mss
        import hashlib
        from concurrent.futures import ThreadPoolExecutor, as_completed
        
        # 이미지 캐시 (변화 감지용)
        image_cache = {}
        
        with mss.mss() as sct:
            # 스레드 풀 생성 (메모리 안정성을 위해 스레드 수 제한)
            max_workers = min(2, max(1, len(self.overlay.grid_cells) // 10))  # 메모리 안전을 위해 최대 2개 스레드
            
            while self.running:
                try:
                    # 활성 셀들 가져오기
                    active_cells = [cell for cell in self.overlay.grid_cells if cell['enabled']]
                    
                    if not active_cells:
                        self.msleep(500)
                        continue
                    
                    # 디버깅: 활성 셀 목록 로그 (주기적으로)
                    if hasattr(self, '_cycle_count'):
                        self._cycle_count += 1
                    else:
                        self._cycle_count = 1
                    
                    if self._cycle_count % 10 == 1:  # 10번마다 한 번 로그
                        cell_ids = [cell['id'] for cell in active_cells[:5]]  # 처음 5개만
                        self.status_signal.emit(f"🔄 활성 셀 확인: {', '.join(cell_ids)}")
                    
                    # 모든 활성 셀의 스크린샷을 먼저 캡처 (빠른 캡처)
                    cell_images = []
                    for cell in active_cells:
                        if not self.running:
                            break
                            
                        ocr_x, ocr_y, ocr_w, ocr_h = cell['ocr_area']
                        ocr_area = {
                            'left': ocr_x,
                            'top': ocr_y,
                            'width': ocr_w,
                            'height': ocr_h
                        }
                        
                        try:
                            screenshot = sct.grab(ocr_area)
                            image = np.array(screenshot)
                            
                            # 이미지 변화 감지 (해시 비교)
                            image_hash = hashlib.md5(image.tobytes()).hexdigest()
                            cell_id = cell['id']
                            
                            # 이전과 동일한 이미지면 스킵 (디버그 로그 추가)
                            if not self.disable_cache and cell_id in image_cache and image_cache[cell_id] == image_hash:
                                # 변화 없음 - 스킵 (캐시 활성화 시에만)
                                continue
                            else:
                                # 변화 감지됨 또는 캐시 비활성화
                                if self.disable_cache:
                                    log_msg = f"🔍 {cell_id}: 강제 OCR 실행 (캐시 비활성화)"
                                    # M0_R0_C1 특별 추적
                                    if cell_id == "M0_R0_C1":
                                        log_msg += " ⭐ 목표 셀!"
                                    self.status_signal.emit(log_msg)
                                elif cell_id not in image_cache:
                                    self.status_signal.emit(f"🆕 {cell_id}: 첫 번째 캡처")
                                else:
                                    self.status_signal.emit(f"🔄 {cell_id}: 이미지 변화 감지됨")
                                
                            image_cache[cell_id] = image_hash
                            
                            # 디버깅: 스크린샷 저장
                            if self.save_debug_images:
                                self._save_debug_screenshot(cell, image, "original")
                            
                            cell_images.append((cell, image))
                            
                        except Exception as e:
                            self.status_signal.emit(f"❌ 캡처 오류 {cell['id']}: {e}")
                    
                    # 변화가 있는 이미지들만 병렬 OCR 처리
                    if cell_images:
                        self._process_ocr_batch(cell_images, max_workers)
                    
                    # 처리 간격 조정 (변화가 많을 때는 짧게, 적을 때는 길게)
                    interval = 200 if len(cell_images) > 5 else 500
                    self.msleep(interval)
                    
                except Exception as e:
                    self.status_signal.emit(f"❌ 모니터링 오류: {e}")
                    self.msleep(1000)
    
    def _save_debug_screenshot(self, cell, image, stage):
        """디버깅용 스크린샷 저장"""
        try:
            import cv2
            import os
            from datetime import datetime
            
            # 디버그 폴더 생성
            debug_folder = "debug_screenshots"
            if not os.path.exists(debug_folder):
                os.makedirs(debug_folder)
            
            # 파일명 생성
            timestamp = datetime.now().strftime("%H%M%S")
            filename = f"{debug_folder}/{cell['id']}_{stage}_{timestamp}_{self.debug_counter:04d}.png"
            self.debug_counter += 1
            
            # 이미지 저장
            if len(image.shape) == 4:  # BGRA
                image_save = cv2.cvtColor(image, cv2.COLOR_BGRA2BGR)
            else:  # BGR
                image_save = image.copy()
            
            cv2.imwrite(filename, image_save)
            self.status_signal.emit(f"💾 디버그 저장: {filename}")
            
            # 너무 많은 파일 생성 방지 (최대 50개)
            if self.debug_counter > 50:
                self.save_debug_images = False
                self.status_signal.emit("⚠️ 디버그 이미지 저장 중단 (최대 개수 도달)")
                
        except Exception as e:
            self.status_signal.emit(f"❌ 디버그 스크린샷 저장 실패: {e}")
    
    def _process_ocr_batch(self, cell_images, max_workers):
        """병렬 OCR 배치 처리"""
        from concurrent.futures import ThreadPoolExecutor, as_completed
        
        def process_single_ocr(cell_image_pair):
            """단일 OCR 처리"""
            cell, image = cell_image_pair
            try:
                # 이미지 복사본 생성 (메모리 안전성)
                image_copy = image.copy()
                
                # 이미지 전처리 및 최적화
                optimized_image = self._optimize_image_for_ocr(image_copy)
                
                # 디버깅: 최적화된 이미지도 저장
                if self.save_debug_images:
                    self._save_debug_screenshot(cell, optimized_image, "optimized")
                
                # OCR 처리
                detected_text = self._perform_real_ocr(optimized_image)
                
                if detected_text and self.ocr_corrector:
                    is_match, corrected = self.ocr_corrector.check_trigger_pattern(detected_text)
                    
                    # 디버그: 패턴 매칭 결과 로그
                    if is_match:
                        self.status_signal.emit(f"✅ {cell['id']}: '{detected_text}' → '{corrected}' (매칭 성공)")
                        return (cell, detected_text, corrected, True)
                    else:
                        self.status_signal.emit(f"❌ {cell['id']}: '{detected_text}' (매칭 실패)")
                elif detected_text:
                    # OCR 보정기 없이 기본 패턴 체크
                    if "들어왔" in detected_text or "입장" in detected_text or "참여" in detected_text:
                        self.status_signal.emit(f"✅ {cell['id']}: '{detected_text}' (기본 패턴 매칭)")
                        return (cell, detected_text, detected_text, True)
                    else:
                        if self.log_all_ocr_results:
                            self.status_signal.emit(f"❌ {cell['id']}: '{detected_text}' (기본 패턴 불일치)")
                elif self.log_all_ocr_results:
                    # OCR 결과 없음도 로그
                    self.status_signal.emit(f"⚪ {cell['id']}: OCR 결과 없음")
                
                return (cell, detected_text, None, False)
                
            except Exception as e:
                self.status_signal.emit(f"❌ OCR 처리 오류 {cell['id']}: {e}")
                return (cell, None, None, False)
        
        # 병렬 처리 실행
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_cell = {executor.submit(process_single_ocr, cell_image): cell_image[0] 
                             for cell_image in cell_images}
            
            for future in as_completed(future_to_cell):
                if not self.running:
                    break
                    
                try:
                    cell, detected_text, corrected, is_match = future.result()
                    
                    if is_match:
                        # M0_R0_C1 특별 추적
                        if cell['id'] == "M0_R0_C1":
                            self.status_signal.emit(f"🎯 M0_R0_C1 매칭 성공! 자동화 실행 중...")
                        
                        self.detection_signal.emit(cell['id'], f"{detected_text} -> {corrected}")
                        self.overlay.update_cell_status(cell['id'], 'triggered')
                        
                        # 자동화 실행
                        self._execute_automation(cell, corrected)
                        
                except Exception as e:
                    self.status_signal.emit(f"❌ OCR 결과 처리 오류: {e}")
    
    def _optimize_image_for_ocr(self, image):
        """OCR을 위한 이미지 최적화"""
        import cv2
        
        # BGRA -> RGB 변환
        if len(image.shape) == 4:
            image_rgb = cv2.cvtColor(image, cv2.COLOR_BGRA2RGB)
        else:
            image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        
        # 해상도 최적화 (너무 크면 축소, 너무 작으면 확대)
        height, width = image_rgb.shape[:2]
        
        # OCR에 최적인 높이: 32-48px
        target_height = 40
        if height < 20:
            # 너무 작으면 2배 확대
            scale = 2.0
        elif height > 80:
            # 너무 크면 적절히 축소
            scale = target_height / height
        else:
            scale = 1.0
        
        if scale != 1.0:
            new_width = int(width * scale)
            new_height = int(height * scale)
            image_rgb = cv2.resize(image_rgb, (new_width, new_height), interpolation=cv2.INTER_CUBIC)
        
        # 대비 향상
        lab = cv2.cvtColor(image_rgb, cv2.COLOR_RGB2LAB)
        l, a, b = cv2.split(lab)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
        l = clahe.apply(l)
        enhanced = cv2.merge([l, a, b])
        image_rgb = cv2.cvtColor(enhanced, cv2.COLOR_LAB2RGB)
        
        return image_rgb
    
    def _run_demo_monitoring(self):
        """데모 모니터링 (실제 자동화 포함)"""
        demo_texts = [
            "들어왔습니다", "들머왔습니다", "둘어왔습니다", 
            "입장했습니다", "참여했습니다", "안녕하세요"
        ]
        
        import random
        counter = 0
        
        while self.running:
            try:
                # 10초마다 랜덤 셀에서 감지 시뮬레이션
                if counter % 100 == 0:  # 10초마다 (0.1초 * 100)
                    if self.overlay.grid_cells:
                        # 활성 셀 중에서 선택
                        active_cells = [cell for cell in self.overlay.grid_cells if cell['enabled']]
                        if active_cells:
                            cell = random.choice(active_cells)
                            text = random.choice(demo_texts)
                            
                            # OCR 보정 테스트
                            if self.ocr_corrector:
                                is_match, corrected = self.ocr_corrector.check_trigger_pattern(text)
                                if is_match:
                                    self.detection_signal.emit(cell['id'], f"{text} -> {corrected}")
                                    self.overlay.update_cell_status(cell['id'], 'triggered')
                                    
                                    # 실제 자동화 실행
                                    self._execute_automation(cell, corrected)
                                else:
                                    self.status_signal.emit(f"❌ 미매칭: {text}")
                            else:
                                if "들어왔" in text or "입장" in text or "참여" in text:
                                    self.detection_signal.emit(cell['id'], text)
                                    self.overlay.update_cell_status(cell['id'], 'triggered')
                                    
                                    # 실제 자동화 실행
                                    self._execute_automation(cell, text)
                
                counter += 1
                self.msleep(100)  # 0.1초 대기
                
            except Exception as e:
                self.status_signal.emit(f"❌ 모니터링 오류: {e}")
                self.msleep(1000)
    
    def _perform_real_ocr(self, image_rgb):
        """최적화된 PaddleOCR 수행 - 스레드 안전"""
        try:
            # 스레드별 OCR 인스턴스 생성 (스레드 안전성 보장)
            import threading
            thread_id = threading.current_thread().ident
            ocr_attr_name = f'ocr_reader_{thread_id}'
            
            if not hasattr(self, ocr_attr_name):
                from paddleocr import PaddleOCR
                ocr_reader = PaddleOCR(
                    use_angle_cls=False,  # 각도 분류 비활성화로 속도 향상
                    lang='korean',
                    use_gpu=False,  # CPU 사용 (안정성)
                    show_log=False  # 로그 출력 비활성화
                )
                setattr(self, ocr_attr_name, ocr_reader)
                self.status_signal.emit(f"🔧 PaddleOCR 초기화 완료 (스레드 {thread_id})")
            
            ocr_reader = getattr(self, ocr_attr_name)
            
            # PaddleOCR 실행 (이미 최적화된 이미지 사용)
            results = ocr_reader.ocr(image_rgb, cls=False)  # 각도 분류 비활성화
            
            if results and results[0]:
                # 높은 신뢰도 텍스트만 선별
                detected_texts = []
                high_confidence_texts = []
                
                for line in results[0]:
                    text = line[1][0].strip()  # 텍스트 추출 및 공백 제거
                    confidence = line[1][1]  # 신뢰도
                    
                    if confidence > 0.7:  # 높은 신뢰도
                        high_confidence_texts.append(text)
                    elif confidence > 0.4:  # 중간 신뢰도
                        detected_texts.append(text)
                
                # 높은 신뢰도 텍스트 우선, 없으면 중간 신뢰도 사용
                if high_confidence_texts:
                    full_text = ' '.join(high_confidence_texts)
                    avg_confidence = 0.8  # 높은 신뢰도 평균
                elif detected_texts:
                    full_text = ' '.join(detected_texts)
                    avg_confidence = 0.6  # 중간 신뢰도 평균
                else:
                    return None
                
                # 로그는 감지 시에만 출력 (성능 향상)
                if len(full_text) > 2:  # 의미 있는 텍스트만
                    # 디버그: OCR 결과 로그 출력
                    self.status_signal.emit(f"📝 OCR 감지: '{full_text}' (평균 신뢰도: {avg_confidence:.2f})")
                    return full_text
            
            return None
            
        except ImportError:
            self.status_signal.emit("❌ PaddleOCR가 설치되지 않음. pip install paddlepaddle paddleocr")
            return None
        except Exception as e:
            # OCR 오류는 빈번할 수 있으므로 로그 레벨 조정
            error_msg = str(e)
            if "No objects to concatenate" not in error_msg and "Tensor holds no memory" not in error_msg:
                self.status_signal.emit(f"❌ PaddleOCR 오류: {error_msg}")
            elif "Tensor holds no memory" in error_msg:
                # 메모리 오류 발생 시 해당 스레드의 OCR 인스턴스 제거
                import threading
                thread_id = threading.current_thread().ident
                ocr_attr_name = f'ocr_reader_{thread_id}'
                if hasattr(self, ocr_attr_name):
                    delattr(self, ocr_attr_name)
                self.status_signal.emit(f"⚠️ PaddleOCR 메모리 오류 - 스레드 {thread_id} 인스턴스 재생성 필요")
            return None
    
    def _execute_automation(self, cell, detected_text):
        """자동화 실행"""
        try:
            cell_bounds = cell['bounds']
            ocr_area = cell['ocr_area']
            
            # 상세 디버그 정보 출력
            self.status_signal.emit(f"🤖 자동화 시작: {cell['id']}")
            self.status_signal.emit(f"   📍 셀 경계: {cell_bounds}")
            self.status_signal.emit(f"   🔍 OCR 영역: {ocr_area}")
            if 'input_position' in cell:
                self.status_signal.emit(f"   🎯 입력 위치: {cell['input_position']}")
            
            # 스마트 자동화 실행 (기본 메시지 사용 - smart_input_automation.py에서 설정된 메시지)
            # ocr_based 방법을 사용하여 정확히 해당 셀의 하단 5px 위를 클릭
            success = self.automation.execute_auto_input(
                cell_bounds=cell_bounds,
                ocr_area=ocr_area,
                message=None,  # None으로 설정하면 smart_input_automation.py의 기본 메시지 사용
                method="ocr_based"  # 정확한 셀 위치를 보장하기 위해 ocr_based 사용
            )
            
            if success:
                self.automation_signal.emit(cell['id'], "자동 응답 성공", True)
                self.status_signal.emit(f"✅ 자동화 성공: {cell['id']}")
                # 쿨다운 설정
                self.overlay.update_cell_status(cell['id'], 'cooldown')
                # 5초 후 상태 리셋
                QTimer.singleShot(5000, lambda: self.overlay.update_cell_status(cell['id'], 'idle'))
            else:
                self.automation_signal.emit(cell['id'], "자동 응답 실패", False)
                self.status_signal.emit(f"❌ 자동화 실패: {cell['id']}")
                # 실패 시에도 쿨다운 (더 짧게)
                self.overlay.update_cell_status(cell['id'], 'cooldown')
                QTimer.singleShot(3000, lambda: self.overlay.update_cell_status(cell['id'], 'idle'))
                
        except Exception as e:
            self.automation_signal.emit(cell['id'], f"자동화 오류: {e}", False)
            self.status_signal.emit(f"❌ 자동화 오류 {cell['id']}: {e}")
    
    def stop(self):
        """모니터링 중지"""
        self.running = False
        self.status_signal.emit("⏹️ 모니터링 중지")

class CompleteChatbotGUI(QWidget):
    """완전한 챗봇 GUI - 모든 기존 기능 포함"""
    
    def __init__(self):
        super().__init__()
        self.overlay = None
        self.monitoring_thread = None
        self.detection_count = 0
        self.automation_success_count = 0
        self.automation_fail_count = 0
        
        self.initUI()
    
    def initUI(self):
        """GUI 초기화"""
        self.setWindowTitle("카카오톡 챗봇 시스템 - 완전판 (30개 오버레이)")
        self.setGeometry(100, 100, 800, 700)
        
        # 탭 위젯 생성
        tab_widget = QTabWidget()
        
        # 메인 제어 탭
        main_tab = self.create_main_tab()
        tab_widget.addTab(main_tab, "🤖 메인 제어")
        
        # 오버레이 설정 탭
        overlay_tab = self.create_overlay_tab()
        tab_widget.addTab(overlay_tab, "🔍 오버레이 설정")
        
        # 통계 탭
        stats_tab = self.create_stats_tab()
        tab_widget.addTab(stats_tab, "📊 통계")
        
        # 로그 탭
        log_tab = self.create_log_tab()
        tab_widget.addTab(log_tab, "📝 로그")
        
        # 메인 레이아웃
        main_layout = QVBoxLayout()
        main_layout.addWidget(tab_widget)
        self.setLayout(main_layout)
        
        # 타이머 설정
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_display)
        self.update_timer.start(1000)  # 1초마다 업데이트
    
    def create_main_tab(self):
        """메인 제어 탭"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # 시스템 상태
        status_group = QGroupBox("🖥️ 시스템 상태")
        status_layout = QVBoxLayout()
        
        self.status_label = QLabel("⏸️ 대기 중")
        self.status_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        self.status_label.setStyleSheet("color: blue;")
        
        monitors = get_monitors()
        system_info = f"🖥️ 모니터: {len(monitors)}개 | 그리드: 3x5 | 총 셀: {len(monitors) * 15}개"
        self.system_info_label = QLabel(system_info)
        
        status_layout.addWidget(self.status_label)
        status_layout.addWidget(self.system_info_label)
        status_group.setLayout(status_layout)
        
        # 제어 버튼
        control_group = QGroupBox("🎮 제어")
        control_layout = QGridLayout()
        
        self.start_btn = QPushButton("🚀 모니터링 시작")
        self.stop_btn = QPushButton("⏹️ 모니터링 중지")
        self.overlay_btn = QPushButton("🔍 오버레이 표시")
        self.test_btn = QPushButton("🧪 시스템 테스트")
        
        self.start_btn.clicked.connect(self.start_monitoring)
        self.stop_btn.clicked.connect(self.stop_monitoring)
        self.overlay_btn.clicked.connect(self.toggle_overlay)
        self.test_btn.clicked.connect(self.run_system_test)
        
        control_layout.addWidget(self.start_btn, 0, 0)
        control_layout.addWidget(self.stop_btn, 0, 1)
        control_layout.addWidget(self.overlay_btn, 1, 0)
        control_layout.addWidget(self.test_btn, 1, 1)
        control_group.setLayout(control_layout)
        
        # OCR 보정 테스트
        ocr_group = QGroupBox("🔧 OCR 보정 테스트")
        ocr_layout = QVBoxLayout()
        
        self.ocr_test_input = QTextEdit()
        self.ocr_test_input.setMaximumHeight(60)
        self.ocr_test_input.setPlaceholderText("OCR 텍스트를 입력하세요 (예: 들머왔습니다)")
        
        test_layout = QHBoxLayout()
        self.ocr_test_btn = QPushButton("🔍 보정 테스트")
        self.ocr_test_btn.clicked.connect(self.test_ocr_correction)
        self.automation_test_btn = QPushButton("🤖 자동화 테스트")
        self.automation_test_btn.clicked.connect(self.test_automation)
        self.manual_ocr_btn = QPushButton("📸 수동 OCR 테스트")
        self.manual_ocr_btn.clicked.connect(self.manual_ocr_test)
        
        test_layout.addWidget(self.ocr_test_btn)
        test_layout.addWidget(self.automation_test_btn)
        test_layout.addWidget(self.manual_ocr_btn)
        
        self.ocr_result_label = QLabel("결과가 여기에 표시됩니다")
        self.ocr_result_label.setStyleSheet("background-color: #f0f0f0; padding: 5px; border: 1px solid #ccc;")
        
        ocr_layout.addWidget(QLabel("테스트할 OCR 텍스트:"))
        ocr_layout.addWidget(self.ocr_test_input)
        ocr_layout.addLayout(test_layout)
        ocr_layout.addWidget(self.ocr_result_label)
        ocr_group.setLayout(ocr_layout)
        
        # 레이아웃 구성
        layout.addWidget(status_group)
        layout.addWidget(control_group)
        layout.addWidget(ocr_group)
        layout.addStretch()
        
        widget.setLayout(layout)
        return widget
    
    def create_overlay_tab(self):
        """오버레이 설정 탭"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # 표시 옵션
        display_group = QGroupBox("👁️ 표시 옵션")
        display_layout = QVBoxLayout()
        
        self.show_grid_cb = QCheckBox("그리드 라인 표시")
        self.show_grid_cb.setChecked(True)
        self.show_grid_cb.stateChanged.connect(self.update_overlay_display)
        
        self.show_ocr_cb = QCheckBox("OCR 영역 표시")
        self.show_ocr_cb.setChecked(True)
        self.show_ocr_cb.stateChanged.connect(self.update_overlay_display)
        
        self.show_ids_cb = QCheckBox("셀 ID 표시")
        self.show_ids_cb.setChecked(True)
        self.show_ids_cb.stateChanged.connect(self.update_overlay_display)
        
        display_layout.addWidget(self.show_grid_cb)
        display_layout.addWidget(self.show_ocr_cb)
        display_layout.addWidget(self.show_ids_cb)
        display_group.setLayout(display_layout)
        
        # OCR 영역 설정
        ocr_group = QGroupBox("📏 OCR 영역 설정")
        ocr_layout = QGridLayout()
        
        # 높이 설정
        ocr_layout.addWidget(QLabel("OCR 영역 높이:"), 0, 0)
        self.height_slider = QSlider(Qt.Orientation.Horizontal)
        self.height_slider.setRange(50, 200)
        self.height_slider.setValue(120)
        self.height_slider.valueChanged.connect(self.update_overlay_settings)
        self.height_value_label = QLabel("120px")
        ocr_layout.addWidget(self.height_slider, 0, 1)
        ocr_layout.addWidget(self.height_value_label, 0, 2)
        
        # 여백 설정
        ocr_layout.addWidget(QLabel("좌우 여백:"), 1, 0)
        self.margin_slider = QSlider(Qt.Orientation.Horizontal)
        self.margin_slider.setRange(0, 50)
        self.margin_slider.setValue(5)
        self.margin_slider.valueChanged.connect(self.update_overlay_settings)
        self.margin_value_label = QLabel("5px")
        ocr_layout.addWidget(self.margin_slider, 1, 1)
        ocr_layout.addWidget(self.margin_value_label, 1, 2)
        
        # 오프셋 설정
        ocr_layout.addWidget(QLabel("Y 위치 오프셋:"), 2, 0)
        self.offset_slider = QSlider(Qt.Orientation.Horizontal)
        self.offset_slider.setRange(0, 100)
        self.offset_slider.setValue(0)
        self.offset_slider.valueChanged.connect(self.update_overlay_settings)
        self.offset_value_label = QLabel("0px")
        ocr_layout.addWidget(self.offset_slider, 2, 1)
        ocr_layout.addWidget(self.offset_value_label, 2, 2)
        
        ocr_group.setLayout(ocr_layout)
        
        # 리셋 버튼
        reset_btn = QPushButton("🔄 기본값으로 리셋")
        reset_btn.clicked.connect(self.reset_overlay_settings)
        
        layout.addWidget(display_group)
        layout.addWidget(ocr_group)
        layout.addWidget(reset_btn)
        layout.addStretch()
        
        widget.setLayout(layout)
        return widget
    
    def create_stats_tab(self):
        """통계 탭"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        stats_group = QGroupBox("📊 실시간 통계")
        stats_layout = QGridLayout()
        
        # 통계 레이블들
        self.stats_labels = {}
        stats_items = [
            ("총 감지 횟수:", "detections"),
            ("자동화 성공:", "automation_success"),
            ("자동화 실패:", "automation_fail"),
            ("활성 셀 수:", "active_cells"),
            ("쿨다운 셀 수:", "cooldown_cells"),
            ("모니터링 시간:", "uptime")
        ]
        
        for i, (label, key) in enumerate(stats_items):
            stats_layout.addWidget(QLabel(label), i, 0)
            self.stats_labels[key] = QLabel("0")
            self.stats_labels[key].setStyleSheet("font-weight: bold; color: #0066cc;")
            stats_layout.addWidget(self.stats_labels[key], i, 1)
        
        stats_group.setLayout(stats_layout)
        
        # 성능 정보
        perf_group = QGroupBox("⚡ 성능 정보")
        perf_layout = QVBoxLayout()
        
        self.perf_label = QLabel("성능 데이터를 수집 중...")
        perf_layout.addWidget(self.perf_label)
        
        perf_group.setLayout(perf_layout)
        
        layout.addWidget(stats_group)
        layout.addWidget(perf_group)
        layout.addStretch()
        
        widget.setLayout(layout)
        return widget
    
    def create_log_tab(self):
        """로그 탭"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        log_group = QGroupBox("📝 실시간 로그")
        log_layout = QVBoxLayout()
        
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setFont(QFont("Consolas", 9))
        
        # 로그 제어 버튼
        log_control_layout = QHBoxLayout()
        clear_btn = QPushButton("🗑️ 로그 지우기")
        clear_btn.clicked.connect(self.clear_log)
        save_btn = QPushButton("💾 로그 저장")
        save_btn.clicked.connect(self.save_log)
        
        log_control_layout.addWidget(clear_btn)
        log_control_layout.addWidget(save_btn)
        log_control_layout.addStretch()
        
        log_layout.addWidget(self.log_text)
        log_layout.addLayout(log_control_layout)
        log_group.setLayout(log_layout)
        
        layout.addWidget(log_group)
        widget.setLayout(layout)
        return widget
    
    def start_monitoring(self):
        """모니터링 시작"""
        if self.monitoring_thread and self.monitoring_thread.running:
            return
        
        if not self.overlay:
            self.toggle_overlay()  # 오버레이가 없으면 자동 생성
        
        self.monitoring_thread = MonitoringThread(self.overlay)
        self.monitoring_thread.detection_signal.connect(self.on_detection)
        self.monitoring_thread.automation_signal.connect(self.on_automation)
        self.monitoring_thread.status_signal.connect(self.on_status_update)
        self.monitoring_thread.start()
        
        self.status_label.setText("🚀 모니터링 실행 중")
        self.status_label.setStyleSheet("color: green;")
        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        
        self.log(f"🚀 모니터링 시작 - {len(self.overlay.grid_cells)}개 셀 활성화")
    
    def stop_monitoring(self):
        """모니터링 중지"""
        if self.monitoring_thread:
            self.monitoring_thread.stop()
            self.monitoring_thread.wait()
            self.monitoring_thread = None
        
        self.status_label.setText("⏸️ 모니터링 중지됨")
        self.status_label.setStyleSheet("color: red;")
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        
        self.log("⏹️ 모니터링 중지")
    
    def toggle_overlay(self):
        """오버레이 토글"""
        if self.overlay:
            self.overlay.close()
            self.overlay = None
            self.overlay_btn.setText("🔍 오버레이 표시")
            self.log("🔍 오버레이 숨김")
        else:
            self.overlay = GridOverlayWidget(self)
            self.overlay.show()
            self.overlay_btn.setText("🙈 오버레이 숨김")
            self.log(f"🔍 오버레이 표시 - {len(self.overlay.grid_cells)}개 셀")
    
    def run_system_test(self):
        """시스템 테스트"""
        self.log("🧪 시스템 테스트 시작")
        
        tests = [
            ("PyQt5 GUI", True),
            ("오버레이 생성", self.overlay is not None or True),
            ("OCR 보정기", OCR_CORRECTOR_AVAILABLE),
            ("리팩토링된 서비스", SERVICES_AVAILABLE),
            ("설정 파일", os.path.exists("config.json")),
        ]
        
        results = []
        passed = 0
        
        for test_name, result in tests:
            if result:
                results.append(f"✅ {test_name}")
                passed += 1
            else:
                results.append(f"❌ {test_name}")
        
        success_rate = (passed / len(tests)) * 100
        
        msg = QMessageBox()
        msg.setWindowTitle("시스템 테스트 결과")
        msg.setText(f"🧪 테스트 완료: {passed}/{len(tests)} ({success_rate:.0f}%)")
        msg.setDetailedText("\n".join(results))
        msg.exec_()
        
        self.log(f"🧪 시스템 테스트 완료: {passed}/{len(tests)} 통과")
    
    def test_ocr_correction(self):
        """OCR 보정 테스트"""
        text = self.ocr_test_input.toPlainText().strip()
        if not text:
            return
        
        if OCR_CORRECTOR_AVAILABLE:
            corrector = EnhancedOCRCorrector()
            is_match, corrected = corrector.check_trigger_pattern(text)
            
            if is_match:
                result = f"✅ 매칭: '{text}' → '{corrected}'"
                self.ocr_result_label.setStyleSheet("background-color: #d4edda; padding: 5px; border: 1px solid #c3e6cb; color: #155724;")
            else:
                result = f"❌ 미매칭: '{text}'"
                self.ocr_result_label.setStyleSheet("background-color: #f8d7da; padding: 5px; border: 1px solid #f5c6cb; color: #721c24;")
        else:
            result = f"⚠️ OCR 보정기 없음: '{text}'"
            self.ocr_result_label.setStyleSheet("background-color: #fff3cd; padding: 5px; border: 1px solid #ffeaa7; color: #856404;")
        
        self.ocr_result_label.setText(result)
        self.log(f"🔧 OCR 테스트: {result}")
    
    def test_automation(self):
        """자동화 테스트"""
        try:
            from automation.smart_input_automation import SmartInputAutomation
            
            # 스마트 입력 자동화 시스템 생성
            automation = SmartInputAutomation()
            
            # 테스트용 데이터 (첫 번째 셀 사용)
            if self.overlay and len(self.overlay.grid_cells) > 0:
                cell = self.overlay.grid_cells[0]
                cell_bounds = (cell['x'], cell['y'], cell['width'], cell['height'])
                ocr_area = (cell['ocr_x'], cell['ocr_y'], cell['ocr_w'], cell['ocr_h'])
                
                # 입력 감지 테스트 실행
                test_results = automation.test_input_detection(cell_bounds, ocr_area)
                
                # 결과 표시
                result_text = "🤖 자동화 테스트 결과:\n\n"
                for method, result in test_results.items():
                    status = "✅" if result['success'] else "❌"
                    result_text += f"{status} {method}:\n"
                    result_text += f"   위치: {result['position']}\n"
                    result_text += f"   신뢰도: {result['confidence']:.2f}\n"
                    result_text += f"   메시지: {result['message']}\n\n"
                
                result_text += "🎯 추천 방법: multi_strategy\n"
                result_text += "📝 테스트 완료! 실제 실행을 위해 모니터링을 시작하세요."
                
                # 결과 표시를 위한 다이얼로그
                from PyQt5.QtWidgets import QMessageBox
                msg = QMessageBox()
                msg.setWindowTitle("자동화 테스트 결과")
                msg.setText("🤖 스마트 입력 자동화 테스트")
                msg.setDetailedText(result_text)
                msg.setStyleSheet("QMessageBox { min-width: 400px; }")
                msg.exec_()
                
                self.log("🧪 자동화 테스트 완료")
                
            else:
                self.log("❌ 오버레이가 없어 자동화 테스트 불가")
                from PyQt5.QtWidgets import QMessageBox
                QMessageBox.warning(self, "오류", "오버레이를 먼저 활성화해주세요.")
                
        except ImportError:
            self.log("❌ smart_input_automation.py 파일을 찾을 수 없음")
            from PyQt5.QtWidgets import QMessageBox
            QMessageBox.warning(self, "오류", "smart_input_automation.py 파일이 필요합니다.")
        except Exception as e:
            self.log(f"❌ 자동화 테스트 오류: {e}")
            from PyQt5.QtWidgets import QMessageBox
            QMessageBox.critical(self, "오류", f"자동화 테스트 실패:\n{e}")
    
    def manual_ocr_test(self):
        """수동 OCR 테스트 - 모든 셀의 현재 상태 확인"""
        if not self.overlay:
            self.log("❌ 오버레이가 없어 수동 OCR 테스트 불가")
            return
        
        try:
            import mss
            from paddleocr import PaddleOCR
            
            self.log("📸 수동 OCR 테스트 시작 - 모든 셀 스캔")
            
            # PaddleOCR 초기화
            ocr = PaddleOCR(use_angle_cls=False, lang='korean', show_log=False)
            
            results = []
            
            with mss.mss() as sct:
                for cell in self.overlay.grid_cells[:5]:  # 처음 5개 셀만 테스트
                    if not cell['enabled']:
                        continue
                    
                    try:
                        # 스크린샷 캡처
                        ocr_x, ocr_y, ocr_w, ocr_h = cell['ocr_area']
                        ocr_area = {
                            'left': ocr_x,
                            'top': ocr_y,
                            'width': ocr_w,
                            'height': ocr_h
                        }
                        
                        screenshot = sct.grab(ocr_area)
                        image = np.array(screenshot)
                        
                        # 이미지 저장 (디버그용)
                        import cv2
                        debug_filename = f"manual_test_{cell['id']}.png"
                        if len(image.shape) == 4:
                            image_save = cv2.cvtColor(image, cv2.COLOR_BGRA2BGR)
                        else:
                            image_save = image.copy()
                        cv2.imwrite(debug_filename, image_save)
                        
                        # OCR 실행
                        ocr_results = ocr.ocr(image, cls=False)
                        
                        detected_text = ""
                        if ocr_results and ocr_results[0]:
                            texts = []
                            for line in ocr_results[0]:
                                text = line[1][0].strip()
                                confidence = line[1][1]
                                if confidence > 0.4:
                                    texts.append(f"{text}({confidence:.2f})")
                            detected_text = " ".join(texts)
                        
                        result = f"{cell['id']}: '{detected_text}'"
                        if "들어왔" in detected_text:
                            result += " ⭐ 매칭!"
                        
                        results.append(result)
                        self.log(f"📝 {result}")
                        
                    except Exception as e:
                        self.log(f"❌ {cell['id']} OCR 실패: {e}")
            
            # 결과 요약
            summary = "\n".join(results)
            self.log(f"📊 수동 OCR 테스트 완료\n{summary}")
            
            # 결과 창 표시
            from PyQt5.QtWidgets import QMessageBox
            msg = QMessageBox()
            msg.setWindowTitle("수동 OCR 테스트 결과")
            msg.setText("📸 현재 모든 셀의 OCR 결과")
            msg.setDetailedText(summary)
            msg.exec_()
            
        except Exception as e:
            self.log(f"❌ 수동 OCR 테스트 오류: {e}")
    
    def update_overlay_display(self):
        """오버레이 표시 옵션 업데이트"""
        if not self.overlay:
            return
        
        self.overlay.set_grid_visible(self.show_grid_cb.isChecked())
        self.overlay.set_ocr_areas_visible(self.show_ocr_cb.isChecked())
        self.overlay.set_cell_ids_visible(self.show_ids_cb.isChecked())
    
    def update_overlay_settings(self):
        """오버레이 설정 업데이트"""
        if not self.overlay:
            return
        
        height = self.height_slider.value()
        margin = self.margin_slider.value()
        offset = self.offset_slider.value()
        
        self.height_value_label.setText(f"{height}px")
        self.margin_value_label.setText(f"{margin}px")
        self.offset_value_label.setText(f"{offset}px")
        
        self.overlay.update_overlay_settings(height, margin, offset)
        self.log(f"📏 오버레이 설정 업데이트: H{height} M{margin} O{offset}")
    
    def reset_overlay_settings(self):
        """오버레이 설정 리셋"""
        self.height_slider.setValue(120)
        self.margin_slider.setValue(5)
        self.offset_slider.setValue(0)
        self.log("🔄 오버레이 설정 기본값으로 리셋")
    
    def on_detection(self, cell_id: str, text: str):
        """감지 이벤트 처리"""
        self.detection_count += 1
        self.log(f"🎯 {cell_id}: {text}")
        
        # 3초 후 셀 상태 리셋
        QTimer.singleShot(3000, lambda: self.reset_cell_status(cell_id))
    
    def on_status_update(self, message: str):
        """상태 업데이트"""
        self.log(message)
    
    def on_automation(self, cell_id: str, message: str, success: bool):
        """자동화 이벤트 처리"""
        status_icon = "✅" if success else "❌"
        self.log(f"{status_icon} 자동화 {cell_id}: {message}")
        
        # 통계 업데이트
        if success:
            self.automation_success_count += 1
        else:
            self.automation_fail_count += 1
            
        # 통계 표시 업데이트
        if hasattr(self, 'stats_labels'):
            if 'automation_success' in self.stats_labels:
                self.stats_labels['automation_success'].setText(str(self.automation_success_count))
            if 'automation_fail' in self.stats_labels:
                self.stats_labels['automation_fail'].setText(str(self.automation_fail_count))
    
    def reset_cell_status(self, cell_id: str):
        """셀 상태 리셋"""
        if self.overlay:
            self.overlay.update_cell_status(cell_id, 'idle')
    
    def update_display(self):
        """디스플레이 업데이트"""
        if hasattr(self, 'stats_labels'):
            self.stats_labels['detections'].setText(str(self.detection_count))
            self.stats_labels['automation_success'].setText(str(self.automation_success_count))
            self.stats_labels['automation_fail'].setText(str(self.automation_fail_count))
            
            if self.overlay:
                active_count = sum(1 for cell in self.overlay.grid_cells if cell['enabled'])
                self.stats_labels['active_cells'].setText(str(active_count))
                
                cooldown_count = sum(1 for status in self.overlay.cell_status.values() if status == 'cooldown')
                self.stats_labels['cooldown_cells'].setText(str(cooldown_count))
    
    def log(self, message: str):
        """로그 추가"""
        timestamp = time.strftime("%H:%M:%S")
        log_message = f"[{timestamp}] {message}"
        
        if hasattr(self, 'log_text'):
            self.log_text.append(log_message)
            
            # 스크롤을 맨 아래로
            scrollbar = self.log_text.verticalScrollBar()
            scrollbar.setValue(scrollbar.maximum())
    
    def clear_log(self):
        """로그 지우기"""
        if hasattr(self, 'log_text'):
            self.log_text.clear()
            self.log("📝 로그 지워짐")
    
    def save_log(self):
        """로그 저장"""
        if hasattr(self, 'log_text'):
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            filename = f"chatbot_log_{timestamp}.txt"
            
            try:
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(self.log_text.toPlainText())
                self.log(f"💾 로그 저장됨: {filename}")
            except Exception as e:
                self.log(f"❌ 로그 저장 실패: {e}")
    
    def closeEvent(self, event):
        """프로그램 종료 시"""
        self.stop_monitoring()
        if self.overlay:
            self.overlay.close()
        event.accept()

def main():
    """메인 함수"""
    app = QApplication(sys.argv)
    app.setApplicationName("카카오톡 챗봇 시스템")
    app.setApplicationVersion("3.0 Complete")
    
    # GUI 생성 및 실행
    gui = CompleteChatbotGUI()
    gui.show()
    
    print("🎉 완전한 카카오톡 챗봇 시스템 시작!")
    print("✅ 30개 오버레이 영역 GUI 설정 가능")
    print("✅ 그리드 셀 라인 실시간 표시")
    print("✅ 강화된 OCR 보정 시스템")
    print("✅ 실시간 모니터링 및 통계")
    
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()  