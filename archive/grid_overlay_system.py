#!/usr/bin/env python3
"""
카카오톡 그리드 오버레이 시스템
- 각 셀마다 공통 OCR 영역
- 투명 오버레이로 정확한 위치 표시
- 클립보드 자동 붙여넣기 및 엔터
"""

import sys
import json
import time
import pyperclip
import pyautogui
import warnings
import os
import mss
import concurrent.futures
from PIL import Image

# Windows DPI 인식 설정
if sys.platform == "win32":
    import ctypes
    from ctypes import wintypes
    # DPI 인식 설정
    ctypes.windll.shcore.SetProcessDpiAwareness(2)  # Per-monitor DPI aware v2

# 경고 메시지 숨기기 (선택사항)
warnings.filterwarnings("ignore", category=UserWarning, module="torch")
warnings.filterwarnings("ignore", message="Using CPU")

from PyQt5.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout, 
                            QLabel, QPushButton, QTextEdit, QSpinBox, QCheckBox, QGroupBox, QGridLayout, QScrollArea, QDoubleSpinBox)
from PyQt5.QtCore import Qt, QTimer, QThread, pyqtSignal
from PyQt5.QtGui import QPainter, QPen, QBrush, QColor, QFont
from screeninfo import get_monitors
from monitoring.monitor_manager import MonitorManager

class GridOverlayWidget(QWidget):
    """공통 OCR 영역이 있는 그리드 오버레이"""
    
    def __init__(self, monitor_manager, overlay_height=120):
        super().__init__()
        self.monitor_manager = monitor_manager
        self.grid_cells = monitor_manager.grid_cells
        self.overlay_height = overlay_height
        self.overlay_margin = 5  # OCR 영역 가로 여백 (기본값 5px)
        self.overlay_offset = 0  # OCR 영역 Y 위치 오프셋
        self.show_grid = False
        self.show_overlay = False
        self.initUI()
    
    def initUI(self):
        """UI 초기화"""
        # 전체 모니터 범위 계산 (음수 좌표 고려)
        monitors = get_monitors()
        
        # 최소/최대 좌표 찾기
        min_x = min(monitor.x for monitor in monitors)
        min_y = min(monitor.y for monitor in monitors)
        max_x = max(monitor.x + monitor.width for monitor in monitors)
        max_y = max(monitor.y + monitor.height for monitor in monitors)
        
        # 실제 전체 화면 크기 계산
        total_width = max_x - min_x
        total_height = max_y - min_y
        
        # 오버레이 창 설정 - 좀 더 여유있게 설정
        margin = 10
        self.setGeometry(min_x - margin, min_y - margin, 
                        total_width + 2*margin, total_height + 2*margin)
        
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)  # 마우스 이벤트 통과
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool |
            Qt.WindowType.X11BypassWindowManagerHint
        )
        
        print(f"📺 모니터 정보:")
        for i, monitor in enumerate(monitors):
            print(f"   모니터 {i+1}: {monitor.width}x{monitor.height} at ({monitor.x}, {monitor.y})")
        print(f"📺 오버레이 창 설정: {total_width + 2*margin}x{total_height + 2*margin} at ({min_x - margin}, {min_y - margin})")
        print(f"📺 전체 좌표 범위: X({min_x} ~ {max_x}), Y({min_y} ~ {max_y})")
    
    def paintEvent(self, event):
        """그리드 및 오버레이 그리기"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # 오버레이 창의 시작 좌표 (절대 좌표)
        overlay_start_x = self.geometry().x()
        overlay_start_y = self.geometry().y()
        
        # 디버깅: 첫 번째와 마지막 셀 좌표 출력
        if self.show_grid and len(self.grid_cells) > 0:
            first_cell = self.grid_cells[0]
            last_cell = self.grid_cells[-1]
            print(f"🎨 오버레이 창 위치: ({overlay_start_x}, {overlay_start_y})")
            print(f"🎨 페인트 이벤트 - 첫 번째 셀: {first_cell.id} = {first_cell.bounds}")
            print(f"🎨 페인트 이벤트 - 마지막 셀: {last_cell.id} = {last_cell.bounds}")
        
        for i, cell in enumerate(self.grid_cells):
            # 절대 좌표에서 오버레이 창 기준 상대 좌표로 변환
            abs_x, abs_y, cell_w, cell_h = cell.bounds
            cell_x = abs_x - overlay_start_x
            cell_y = abs_y - overlay_start_y
            
            # 그리드 적용: 셀 경계선 표시
            if self.show_grid:
                painter.setPen(QPen(QColor(0, 255, 0), 3, Qt.PenStyle.SolidLine))  # 더 두껍게
                painter.setBrush(QBrush(QColor(0, 255, 0, 30)))  # 더 진하게
                painter.drawRect(cell_x, cell_y, cell_w, cell_h)
                
                # 처음 몇 개 셀만 좌표 디버깅
                if i < 3 or 'monitor2' in cell.id and i < 18:  # 모니터2 첫 3개도 포함
                    print(f"🎨 변환: {cell.id} abs({abs_x}, {abs_y}) -> rel({cell_x}, {cell_y}) size {cell_w}x{cell_h}")
                
                # 셀 ID 표시
                painter.setPen(QPen(QColor(255, 255, 255), 2))
                painter.setFont(QFont("Arial", 14, QFont.Weight.Bold))  # 더 크게
                painter.drawText(cell_x + 10, cell_y + 30, cell.id)
                
                # 셀 크기 정보 표시
                size_info = f"{cell_w}x{cell_h}"
                painter.setFont(QFont("Arial", 11))
                painter.drawText(cell_x + 10, cell_y + 50, size_info)
                
                # 좌표 정보 추가
                coord_info = f"({abs_x},{abs_y})"
                painter.setFont(QFont("Arial", 9))
                painter.drawText(cell_x + 10, cell_y + 70, coord_info)
                
                # 모서리 마커 추가 (정확한 경계 확인용)
                marker_size = 20
                painter.setPen(QPen(QColor(255, 0, 0), 4))
                # 좌상단
                painter.drawLine(cell_x, cell_y, cell_x + marker_size, cell_y)
                painter.drawLine(cell_x, cell_y, cell_x, cell_y + marker_size)
                # 우하단
                painter.drawLine(cell_x + cell_w - marker_size, cell_y + cell_h, 
                               cell_x + cell_w, cell_y + cell_h)
                painter.drawLine(cell_x + cell_w, cell_y + cell_h - marker_size, 
                               cell_x + cell_w, cell_y + cell_h)
            
            # 오버레이 적용: OCR 영역 표시
            if self.show_overlay:
                # 공통 오버레이 영역 계산 (절대 좌표) - 동적 여백 사용
                abs_ocr_x = abs_x + self.overlay_margin
                abs_ocr_y = abs_y + cell_h - self.overlay_offset - self.overlay_height
                ocr_w = cell_w - (self.overlay_margin * 2)  # 좌우 여백 적용
                ocr_h = self.overlay_height
                
                # 영역이 셀 밖으로 나가지 않도록 조정
                if abs_ocr_x < abs_x:
                    abs_ocr_x = abs_x + 2
                if abs_ocr_y < abs_y:
                    abs_ocr_y = abs_y + 2
                if abs_ocr_x + ocr_w > abs_x + cell_w:
                    ocr_w = abs_x + cell_w - abs_ocr_x - 2
                if abs_ocr_y + ocr_h > abs_y + cell_h:
                    ocr_h = abs_y + cell_h - abs_ocr_y - 2
                
                # OCR 영역이 유효한지 검증
                if ocr_w <= 0 or ocr_h <= 0:
                    # 최소 크기 보장 - 최소 여백으로 최대한 넓게
                    ocr_w = max(cell_w - 10, cell_w - (self.overlay_margin * 2))
                    ocr_h = max(30, min(cell_h - 10, self.overlay_height))
                    abs_ocr_x = abs_x + self.overlay_margin
                    abs_ocr_y = abs_y + (cell_h - ocr_h) // 2
                
                # 절대 좌표를 상대 좌표로 변환
                ocr_x = abs_ocr_x - overlay_start_x
                ocr_y = abs_ocr_y - overlay_start_y
                
                # 반투명 빨간색 OCR 영역 (기존)
                painter.setPen(QPen(QColor(255, 0, 0), 3, Qt.PenStyle.SolidLine))
                painter.setBrush(Qt.NoBrush)
                painter.drawRect(ocr_x, ocr_y, ocr_w, ocr_h)
                
                # OCR 영역 라벨 (배경 포함)
                painter.setBrush(QBrush(QColor(0, 0, 0, 200)))
                label_text = f"OCR: {cell.id}"
                label_rect = painter.boundingRect(ocr_x, ocr_y - 25, 200, 20, 
                                                Qt.AlignmentFlag.AlignLeft, label_text)
                painter.drawRect(label_rect)
                
                painter.setPen(QPen(QColor(255, 255, 255), 2))
                painter.setFont(QFont("Arial", 10, QFont.Weight.Bold))
                painter.drawText(ocr_x, ocr_y - 10, label_text)
                
                # 크기 정보
                size_info = f"{ocr_w}x{ocr_h}"
                painter.setBrush(QBrush(QColor(255, 100, 0, 180)))
                size_rect = painter.boundingRect(ocr_x, ocr_y + ocr_h + 5, 100, 15, 
                                               Qt.AlignmentFlag.AlignLeft, size_info)
                painter.drawRect(size_rect)
                
                painter.setPen(QPen(QColor(255, 255, 255), 1))
                painter.setFont(QFont("Arial", 8))
                painter.drawText(ocr_x, ocr_y + ocr_h + 15, size_info)
                
                # 💡 중요: 셀의 OCR 영역 업데이트 (절대 좌표로)
                cell.ocr_area = (abs_ocr_x, abs_ocr_y, ocr_w, ocr_h)
                print(f"📍 {cell.id}: OCR 영역 업데이트됨 - {cell.ocr_area}")
        
        painter.end()
    
    def set_grid_visible(self, visible):
        """그리드 표시/숨기기"""
        self.show_grid = visible
        self.update()
    
    def set_overlay_visible(self, visible):
        """오버레이 표시/숨기기"""
        self.show_overlay = visible
        if visible:
            self._update_all_ocr_areas()
        self.update()
    
    def _update_all_ocr_areas(self):
        """모든 셀의 OCR 영역 강제 업데이트"""
        print("📍 모든 셀의 OCR 영역을 업데이트합니다...")
        
        for cell in self.grid_cells:
            cell_x, cell_y, cell_w, cell_h = cell.bounds
            
            # 공통 오버레이 영역 계산 - 동적 여백 사용
            ocr_x = cell_x + self.overlay_margin
            ocr_y = cell_y + cell_h - self.overlay_offset - self.overlay_height
            ocr_w = cell_w - (self.overlay_margin * 2)  # 좌우 여백 적용
            ocr_h = self.overlay_height
            
            # 영역이 셀 밖으로 나가지 않도록 조정
            if ocr_x < cell_x:
                ocr_x = cell_x + 2
            if ocr_y < cell_y:
                ocr_y = cell_y + 2
            if ocr_x + ocr_w > cell_x + cell_w:
                ocr_w = cell_x + cell_w - ocr_x - 2
            if ocr_y + ocr_h > cell_y + cell_h:
                ocr_h = cell_y + cell_h - ocr_y - 2
            
            # OCR 영역이 유효한지 검증
            if ocr_w <= 0 or ocr_h <= 0:
                # 최소 크기 보장 - 최소 여백으로 최대한 넓게
                ocr_w = max(cell_w - 10, cell_w - (self.overlay_margin * 2))
                ocr_h = max(30, min(cell_h - 10, self.overlay_height))
                ocr_x = cell_x + self.overlay_margin
                ocr_y = cell_y + (cell_h - ocr_h) // 2
                print(f"⚠️ {cell.id}: OCR 영역 자동 조정됨 - {ocr_w}x{ocr_h}")
            
            # 셀의 OCR 영역 업데이트
            cell.ocr_area = (ocr_x, ocr_y, ocr_w, ocr_h)
            print(f"📍 {cell.id}: OCR 영역 설정됨 - {cell.ocr_area}")
    
    def set_overlay_height(self, height):
        """오버레이 높이 설정"""
        self.overlay_height = height
        if self.show_overlay:
            self._update_all_ocr_areas()
            self.update()
    
    def set_overlay_margin(self, margin):
        """OCR 영역 가로 여백 설정"""
        self.overlay_margin = margin
        if self.show_overlay:
            self._update_all_ocr_areas()
            self.update()
        print(f"📏 OCR 영역 가로 여백 설정: {margin}px")
    
    def set_overlay_offset(self, offset):
        """OCR 영역 Y 위치 오프셋 설정"""
        self.overlay_offset = abs(offset)  # 절댓값으로 변환 (항상 위쪽으로)
        if self.show_overlay:
            self._update_all_ocr_areas()
            self.update()
        print(f"📏 OCR 영역 Y 위치: {self.overlay_offset}px 위로")

class OCRMonitoringThread(QThread):
    """배치 처리 기반 고속 OCR 모니터링 스레드 (5개씩 배치)"""
    ocr_detected = pyqtSignal(str, str, int, int)  # cell_id, text, x, y
    message_sent = pyqtSignal(str, str)  # cell_id, message
    
    def __init__(self, monitor_manager):
        super().__init__()
        self.monitor_manager = monitor_manager
        self.running = False
        self.enabled_cells = set()
        self.cooldown_time = 3.0  # 3초 쿨다운
        self.cell_cooldowns = {}
        
        # ⚡ 실시간 모니터링 설정
        self.ocr_interval_sec = 0.1  # 실시간 간격 (0.1초)
        self.debug_mode = False
        self.realtime_mode = True  # 실시간 모드 활성화
        
        # 📊 강화된 캐싱
        self.ocr_cache = {}
        self.cache_timeout = 3.0  # 3초 캐시 유효시간
        
        # 📊 성능 통계
        self.loop_count = 0
        self.total_ocr_time = 0.0
        self.last_fps_update = time.time()
        
        # 🎯 OCR 영역 최적화
        self.optimal_ocr_height = 100  # 최적화된 높이
        
        print(f"⚡ 실시간 OCR 초기화 - 간격:{self.ocr_interval_sec}초, 즉시 감지 모드")

    def run(self):
        self.running = True
        print("⚡ 실시간 OCR 모니터링 시작! (즉시 감지 모드)")
        
        try:
            import mss
            import time
            import numpy as np
            import pyautogui, pyperclip
            import os
            from PIL import Image
            import hashlib

            if self.debug_mode:
                os.makedirs("debug_screenshots", exist_ok=True)

            # 🔍 초기 상태 디버깅
            print(f"🔍 [DEBUG] 활성 셀 개수: {len(self.enabled_cells)}")
            print(f"🔍 [DEBUG] 활성 셀 목록: {list(self.enabled_cells)}")
            print(f"🔍 [DEBUG] 전체 그리드 셀 개수: {len(self.monitor_manager.grid_cells)}")
            
            if not self.enabled_cells:
                print("❌ [DEBUG] 활성 셀이 없어서 스레드 종료")
                self.running = False
                return

            # 🖥️ 모니터 영역 계산
            from screeninfo import get_monitors
            try:
                monitors = get_monitors()
                monitor_rects = []
                for monitor in monitors:
                    monitor_rects.append({
                        "left": monitor.x,
                        "top": monitor.y,
                        "width": monitor.width,
                        "height": monitor.height
                    })
                print(f"🔍 [DEBUG] 모니터 {len(monitors)}개 감지됨")
            except Exception as monitor_error:
                print(f"⚠️ [DEBUG] 모니터 감지 오류: {monitor_error}")
                monitor_rects = [{"left":0,"top":0,"width":1920,"height":1080}]
            
            min_left = min(m["left"] for m in monitor_rects)
            min_top = min(m["top"] for m in monitor_rects)
            max_right = max(m["left"] + m["width"] for m in monitor_rects)
            max_bottom = max(m["top"] + m["height"] for m in monitor_rects)
            full_width = max_right - min_left
            full_height = max_bottom - min_top
            monitor_area = {"top": min_top, "left": min_left, "width": full_width, "height": full_height}
            
            print(f"🖥️ 전체 화면: {full_width}x{full_height}")
            print(f"⚡ 실시간 활성 셀: {len(self.enabled_cells)}개 (즉시 감지)")
            print(f"🔍 [DEBUG] 실시간 모니터링 루프 시작")
            
            # 🔍 PaddleOCR 상태 확인
            if hasattr(self.monitor_manager, 'paddle_ocr') and self.monitor_manager.paddle_ocr:
                print(f"✅ [DEBUG] PaddleOCR 엔진 정상 (활성화됨)")
            else:
                print(f"❌ [DEBUG] PaddleOCR 엔진 비활성화! 감지 불가능!")
                print(f"❌ [DEBUG] monitor_manager.paddle_ocr = {getattr(self.monitor_manager, 'paddle_ocr', 'NONE')}")
                if hasattr(self.monitor_manager, 'paddle_ocr'):
                    print(f"❌ [DEBUG] paddle_ocr 값: {self.monitor_manager.paddle_ocr}")
                else:
                    print(f"❌ [DEBUG] paddle_ocr 속성 자체가 없음!")

        except Exception as init_error:
            print(f"❌ [DEBUG] 초기화 오류: {init_error}")
            self.running = False
            return

        # 🚀 배치 처리 최적화 모니터링 루프
        loop_count = 0
        while self.running:
            loop_start = time.time()
            loop_count += 1
            
            # 🔍 첫 번째 루프에서만 상세 디버깅
            if loop_count == 1:
                print(f"🔍 [DEBUG] 첫 번째 루프 시작 (#{loop_count})")
            
            # 🖥️ 1. 전체 화면 캡처
            try:
                with mss.mss() as sct:
                    full_screenshot = sct.grab(monitor_area)
                    full_img = Image.frombytes("RGB", full_screenshot.size, full_screenshot.rgb)
                    capture_time = time.time() - loop_start
                    
                # 이미지 해시
                img_hash = hashlib.md5(full_img.tobytes()).hexdigest()[:8]
                
                if loop_count == 1:
                    print(f"🔍 [DEBUG] 화면 캡처 성공: {full_img.size}, 해시: {img_hash}")
                
            except Exception as e:
                print(f"💥 스크린샷 실패 (루프 #{loop_count}): {e}")
                time.sleep(self.ocr_interval_sec)
                continue

            # 🔒 2. 활성 셀 필터링 (강화된 디버그)
            all_enabled_cells = [cell for cell in self.monitor_manager.grid_cells if cell.id in self.enabled_cells]
            active_cells = [cell for cell in all_enabled_cells if hasattr(cell, 'ocr_area')]
            
            # 🔍 매 루프마다 상세 분석 (처음 5번)
            if loop_count <= 5:
                print(f"🔍 [DEBUG-{loop_count}] enabled_cells: {len(self.enabled_cells)}개")
                print(f"🔍 [DEBUG-{loop_count}] all_enabled_cells: {len(all_enabled_cells)}개")
                print(f"🔍 [DEBUG-{loop_count}] active_cells (ocr_area 있음): {len(active_cells)}개")
                
                if len(all_enabled_cells) != len(active_cells):
                    missing_ocr = [cell.id for cell in all_enabled_cells if not hasattr(cell, 'ocr_area')]
                    print(f"❌ [DEBUG-{loop_count}] OCR 영역 없는 셀들: {missing_ocr[:5]}...")
                    
                    # OCR 영역 강제 생성
                    for cell in all_enabled_cells:
                        if not hasattr(cell, 'ocr_area'):
                            x, y, w, h = cell.bounds
                            cell.ocr_area = (x + 5, y + h - 100, w - 10, 80)
                            print(f"🔧 [DEBUG-{loop_count}] {cell.id}: OCR 영역 강제 생성 - {cell.ocr_area}")
                    
                    # 다시 필터링
                    active_cells = [cell for cell in all_enabled_cells if hasattr(cell, 'ocr_area')]
                    print(f"🔧 [DEBUG-{loop_count}] 강제 생성 후 active_cells: {len(active_cells)}개")
                
                if active_cells:
                    print(f"✅ [DEBUG-{loop_count}] 첫 번째 활성 셀: {active_cells[0].id}")
                    print(f"✅ [DEBUG-{loop_count}] OCR 영역: {active_cells[0].ocr_area}")
            
            if not active_cells:
                print(f"❌ [DEBUG-{loop_count}] 활성 셀 없음! enabled_cells: {list(self.enabled_cells)[:3]}...")
                time.sleep(self.ocr_interval_sec)
                continue

            # ⚡ 실시간 모니터링 - 30개 셀 모두 지원
            if len(active_cells) > 15:
                print(f"⚡ 실시간 모니터링: {len(active_cells)}개 셀 (즉시 감지 모드)")
            elif len(active_cells) > 10:
                print(f"⚡ 고속 모니터링: {len(active_cells)}개 셀")

            processed_count = 0
            detected_count = 0
            
            # ⚡ 실시간 처리 - 모든 셀 즉시 처리 (배치 간 대기 없음)
            if loop_count <= 3:
                print(f"🚀 [DEBUG-{loop_count}] OCR 처리 시작: {len(active_cells)}개 셀")
            
            for cell_idx, cell in enumerate(active_cells):
                if not self.running:
                    break
                
                cell_start = time.time()
                
                # 🔍 monitor1-2-4 특별 디버그 + 처음 3개 셀
                is_target_cell = cell.id == "monitor1-2-4"
                is_debug_cell = cell_idx < 3 and loop_count <= 2
                
                if is_target_cell or is_debug_cell:
                    marker = "🎯 [TARGET]" if is_target_cell else f"🔍 [DEBUG-{loop_count}]"
                    print(f"{marker} 셀 {cell_idx}: {cell.id} 처리 시작")
                    print(f"{marker} OCR 영역: {cell.ocr_area}")
                    print(f"{marker} 셀 bounds: {cell.bounds}")
                
                try:
                    x, y, w, h = cell.ocr_area
                    
                    # 🎯 실시간 OCR 영역
                    optimized_h = min(h, self.optimal_ocr_height)
                    optimized_y = y + (h - optimized_h) // 2
                    
                    # 상대 좌표 변환
                    rel_x = x - min_left
                    rel_y = optimized_y - min_top
                    
                    # 범위 검증
                    if (rel_x < 0 or rel_y < 0 or 
                        rel_x + w > full_width or rel_y + optimized_h > full_height):
                        continue
                    
                    # ⚡ 실시간 캐시 확인
                    cache_key = f"{cell.id}_{img_hash}_{rel_x}_{rel_y}"
                    if cache_key in self.ocr_cache:
                        cache_time, cached_result = self.ocr_cache[cache_key]
                        if time.time() - cache_time < self.cache_timeout:
                            if cached_result and self._check_trigger_pattern_safe(cached_result):
                                if self._check_cooldown(cell):
                                    print(f"⚡ {cell.id}: 즉시 감지! - '{cached_result[:15]}...'")
                                    self._handle_trigger_safe(cell, cached_result)
                                    detected_count += 1
                            processed_count += 1
                            continue
                    
                    # 🖼️ 이미지 크롭 (강화된 디버그)
                    if cell_idx < 3 and loop_count <= 2:
                        print(f"🖼️ [DEBUG-{loop_count}] {cell.id}: 크롭 좌표 계산")
                        print(f"🖼️ [DEBUG-{loop_count}] 전체 이미지: {full_img.size}")
                        print(f"🖼️ [DEBUG-{loop_count}] 크롭 영역: ({rel_x}, {rel_y}, {rel_x + w}, {rel_y + optimized_h})")
                        print(f"🖼️ [DEBUG-{loop_count}] 크롭 크기: {w}x{optimized_h}")
                    
                    # 크롭 영역 유효성 재검증
                    if rel_x < 0 or rel_y < 0 or rel_x + w > full_width or rel_y + optimized_h > full_height:
                        if cell_idx < 3 and loop_count <= 2:
                            print(f"❌ [DEBUG-{loop_count}] {cell.id}: 크롭 영역 범위 벗어남!")
                            print(f"❌ [DEBUG-{loop_count}] rel_x={rel_x}, rel_y={rel_y}, w={w}, h={optimized_h}")
                            print(f"❌ [DEBUG-{loop_count}] 전체 범위: {full_width}x{full_height}")
                        continue
                    
                    crop_img = full_img.crop((rel_x, rel_y, rel_x + w, rel_y + optimized_h))
                    
                    # 🔍 크롭 이미지 강제 저장 (처음 5개 셀)
                    if cell_idx < 5:
                        debug_path = f"debug_screenshots/{cell.id}_crop_{int(time.time())}.png"
                        os.makedirs("debug_screenshots", exist_ok=True)
                        crop_img.save(debug_path)
                        print(f"💾 [DEBUG] {cell.id}: 크롭 이미지 저장 - {debug_path} (크기: {crop_img.size})")
                    
                    # ⚡ 강화된 디버그 OCR 수행
                    if cell_idx < 3 and loop_count <= 2:
                        print(f"🔍 [DEBUG-{loop_count}] {cell.id}: OCR 수행 시작...")
                    
                    ocr_text = self.monitor_manager._capture_and_ocr_from_img(crop_img)
                    processed_count += 1
                    
                    if cell_idx < 3 and loop_count <= 2:
                        print(f"🔍 [DEBUG-{loop_count}] {cell.id}: OCR 완료 - 결과 길이: {len(ocr_text) if ocr_text else 0}")
                        if ocr_text:
                            print(f"🔍 [DEBUG-{loop_count}] {cell.id}: OCR 텍스트: '{ocr_text[:50]}...'")
                        else:
                            print(f"❌ [DEBUG-{loop_count}] {cell.id}: OCR 결과 없음!")
                        
                        # 🔍 강화된 디버그 로그
                        if cell_idx < 5:  # 처음 5개 셀만 상세 로그
                            if ocr_text and ocr_text.strip():
                                print(f"📝 {cell.id}: OCR 성공 - '{ocr_text[:30]}...'")
                            else:
                                print(f"⚠️ {cell.id}: OCR 결과 없음 (빈 텍스트)")
                        
                        # 캐시 저장
                        self.ocr_cache[cache_key] = (time.time(), ocr_text)
                        
                        # 캐시 크기 관리 (간소화)
                        if len(self.ocr_cache) > 50:
                            # 오래된 캐시 일괄 삭제 (성능 향상)
                            current_time = time.time()
                            self.ocr_cache = {k: v for k, v in self.ocr_cache.items() 
                                            if current_time - v[0] < self.cache_timeout}
                        
                        cell_time = time.time() - cell_start
                        
                        # 🎯 강화된 감지 로직
                        if ocr_text and ocr_text.strip():
                            # 모든 OCR 결과 출력 (디버그용)
                            if len(ocr_text) > 2:  # 2글자 이상만
                                print(f"🔍 {cell.id}: 텍스트 분석 중 - '{ocr_text}'")
                            
                            if self._check_trigger_pattern_safe(ocr_text):
                                if self._check_cooldown(cell):
                                    print(f"🎯 {cell.id}: 트리거 감지! - '{ocr_text[:30]}...'")
                                    self._handle_trigger_safe(cell, ocr_text)
                                    detected_count += 1
                                else:
                                    print(f"🕐 {cell.id}: 쿨다운 중 - '{ocr_text[:15]}...'")
                            else:
                                # 트리거 패턴 매칭 실패 이유 출력
                                if len(ocr_text) > 2:
                                    print(f"❌ {cell.id}: 패턴 불일치 - '{ocr_text[:20]}...'")
                        else:
                            # OCR 실패 원인 분석
                            if cell_idx < 3:
                                print(f"⚠️ {cell.id}: OCR 실패 - 이미지 크기: {crop_img.size}")
                        
                        # 디버그 이미지 저장 (강제)
                        if cell_idx < 5:  # 처음 5개 셀은 항상 저장
                            debug_path = f"debug_screenshots/{cell.id}_debug_{int(time.time())}.png"
                            os.makedirs("debug_screenshots", exist_ok=True)
                            crop_img.save(debug_path)
                            print(f"🖼️ {cell.id}: 디버그 이미지 저장 - {debug_path}")
                    
                    # ⚡ 실시간 처리 - 대기 시간 최소화
                    if cell_idx % 10 == 9:  # 10개마다 짧은 휴식
                        time.sleep(0.02)  # 0.02초만 대기
                    
                except Exception as e:
                    print(f"🚫 {cell.id}: 처리 오류 - {str(e)[:30]}...")
                    continue

            # 📊 실시간 성능 통계
            loop_time = time.time() - loop_start
            self.loop_count += 1
            self.total_ocr_time += loop_time
            
            # 감지된 경우만 로그 출력
            if detected_count > 0:
                print(f"⚡ 즉시 감지 완료: {processed_count}개 처리, {detected_count}개 감지 ({loop_time:.3f}s)")
            elif loop_count <= 5:  # 처음 5번만 전체 로그
                print(f"⚡ 실시간 스캔: {processed_count}개 처리 ({loop_time:.3f}s)")
            
            # 성능 모니터링
            if loop_time > 2.0:  # 2초 이상이면 경고
                print(f"⚠️ 느린 처리: {loop_time:.3f}초 (실시간 최적화 필요)")
            elif loop_time < 0.5:
                if loop_count <= 3:  # 처음 3번만
                    print(f"⚡ 고속 처리: {loop_time:.3f}초 (실시간 최적화 성공!)")
            
            # 성능 보고 (15초마다 - 실시간이므로 더 자주)
            if time.time() - self.last_fps_update > 15.0:
                avg_time = self.total_ocr_time / max(self.loop_count, 1)
                real_fps = 1.0 / avg_time if avg_time > 0 else 0
                print(f"⚡ 실시간 성능: {avg_time:.3f}초/루프, FPS: {real_fps:.2f}, 활성셀: {len(active_cells)}개")
                self.loop_count = 0
                self.total_ocr_time = 0.0
                self.last_fps_update = time.time()
            
            # ⏱️ 루프 간격 대기
            remaining_time = self.ocr_interval_sec - (time.time() - loop_start)
            if remaining_time > 0:
                time.sleep(remaining_time)

    def _check_trigger_pattern_safe(self, text):
        """강화된 트리거 패턴 체크 (디버그 로그 포함)"""
        if not text or len(text) > 100:
            print(f"🚫 트리거 체크 실패: 텍스트 없음 또는 너무 길음 (길이: {len(text) if text else 0})")
            return False
        
        try:
            clean_text = text.replace(" ", "").replace("\n", "").lower()
            
            # 🎯 핵심 패턴 (더 많이 추가)
            patterns = [
                "들어왔습니다", "들어왔", "들머왔습니다", "들머왔",
                "입장했습니다", "참여했습니다", "joined", "entered",
                "들어오셨", "님이들어왔", "입장하셨", "참여하셨"
            ]
            
            # 각 패턴별로 체크
            for pattern in patterns:
                if pattern in clean_text:
                    print(f"🎯 트리거 매칭 성공! '{pattern}' 발견 in '{text[:30]}...'")
                    return True
            
            # 매칭 실패시 디버깅 정보
            print(f"❌ 트리거 매칭 실패: '{clean_text[:50]}...' (패턴: {len(patterns)}개 확인)")
            print(f"❌ 확인된 패턴들: {patterns[:3]}...")  # 처음 3개만
            return False
            
        except Exception as e:
            print(f"🚫 트리거 패턴 체크 오류: {e}")
            return False

    def _check_cooldown(self, cell):
        """쿨다운 체크"""
        current_time = time.time()
        if cell.id in self.cell_cooldowns:
            return (current_time - self.cell_cooldowns[cell.id]) >= self.cooldown_time
        return True

    def _handle_trigger_safe(self, cell, ocr_text):
        """안전한 트리거 처리"""
        current_time = time.time()
        self.cell_cooldowns[cell.id] = current_time
        
        print(f"🚀 {cell.id}: 안전 처리 시작!")
        self.ocr_detected.emit(cell.id, ocr_text, 0, 0)
        
        # 🚀 안전한 메시지 전송
        try:
            success = self._auto_input_message_safe(cell)
            if success:
                print(f"✅ {cell.id}: 안전 전송 성공!")
                self.message_sent.emit(cell.id, "직렬 전송")
            else:
                print(f"❌ {cell.id}: 전송 실패")
                self.cell_cooldowns[cell.id] = current_time + 7
        except Exception as e:
            print(f"💥 {cell.id}: 전송 오류 - {str(e)[:30]}...")

    def _auto_input_message_safe(self, cell):
        """안전한 메시지 입력"""
        import time
        import pyautogui
        import pyperclip
        import ctypes
        
        try:
            # OCR 영역 기준 입력 위치
            if hasattr(cell, 'ocr_area') and cell.ocr_area:
                ocr_x, ocr_y, ocr_w, ocr_h = cell.ocr_area
                input_x = ocr_x + ocr_w // 2
                input_y = ocr_y + ocr_h - 25  # 20 → 25px로 증가
                print(f"   🎯 안전 입력 위치: ({input_x}, {input_y})")
            else:
                return False
            
            # 1. 메시지 준비
            try:
                message = pyperclip.paste()
                if not message or not message.strip():
                    message = self.monitor_manager._get_response_message("")
                if not message:
                    print(f"   ❌ 전송할 메시지 없음")
                    return False
            except:
                return False
            
            # 2. 안전한 클릭
            try:
                ctypes.windll.user32.SetCursorPos(int(input_x), int(input_y))
                time.sleep(0.3)  # 0.2 → 0.3초로 증가
                
                # 단일 클릭
                ctypes.windll.user32.mouse_event(2, 0, 0, 0, 0)
                ctypes.windll.user32.mouse_event(4, 0, 0, 0, 0)
                
            except Exception as e:
                pyautogui.click(input_x, input_y)
                time.sleep(0.3)
            
            # 3. 안전한 메시지 입력
            try:
                time.sleep(0.5)  # 입력창 활성화 대기
                
                # 기존 텍스트 클리어
                pyautogui.hotkey('ctrl', 'a')
                time.sleep(0.2)
                pyautogui.press('delete')
                time.sleep(0.2)
                
                # 메시지 입력
                pyperclip.copy(message)
                time.sleep(0.2)
                pyautogui.hotkey('ctrl', 'v')
                time.sleep(0.3)
                
                # 전송
                pyautogui.press('enter')
                time.sleep(0.2)
                
                print(f"   🔒 직렬 전송 완료: '{message[:20]}...'")
                return True
                
            except Exception as e:
                print(f"   ❌ 입력 실패: {e}")
                return False
            
        except Exception as e:
            print(f"❌ {cell.id} 직렬 입력 실패: {e}")
            return False

    def stop(self):
        self.running = False
        print("🛑 실시간 OCR 모니터링 중지됨")

    def set_enabled_cells(self, cell_ids):
        self.enabled_cells = set(cell_ids)
        print(f"⚡ 실시간 활성 셀: {len(self.enabled_cells)}개 (즉시 감지 모드)")

    def set_performance_mode(self, interval_sec=0.1, max_workers=1, debug_mode=False):
        """실시간 모니터링 성능 모드 설정"""
        self.ocr_interval_sec = max(0.05, interval_sec)  # 최소 0.05초로 단축
        self.debug_mode = debug_mode
        print(f"⚡ 실시간 모드: {self.ocr_interval_sec}초 간격, 즉시 감지")

class GridOverlayController(QWidget):
    """그리드 오버레이 컨트롤러"""
    
    def __init__(self):
        super().__init__()
        
        # 모니터 매니저 초기화
        self.monitor_manager = MonitorManager("config.json")
        
        # 셀 체크박스 관련 변수 초기화
        self.cell_checkboxes = {}
        self.cell_checkbox_layout = QGridLayout()
        
        # 모니터링 스레드 초기화
        self.monitoring_thread = None
        
        # UI 초기화
        self.initUI()
        
        # 오버레이 위젯 초기화 및 표시
        self.overlay_widget = GridOverlayWidget(self.monitor_manager, self.height_spinbox.value())
        self.overlay_widget.set_overlay_margin(self.margin_spinbox.value())
        self.overlay_widget.set_overlay_offset(self.offset_spinbox.value())  # 오프셋 설정 추가
        self.overlay_widget.show()
        
        # 셀 체크박스 업데이트
        self._update_cell_checkboxes()
    
    def _update_cell_checkboxes(self):
        """UI의 셀 선택 체크박스를 생성하고 업데이트합니다."""
        # 기존 체크박스 레이아웃 초기화
        for i in reversed(range(self.cell_checkbox_layout.count())):
            widgetToRemove = self.cell_checkbox_layout.itemAt(i).widget()
            if widgetToRemove is not None:
                widgetToRemove.deleteLater()
        self.cell_checkboxes.clear()

        # MonitorManager로부터 셀 정보 가져오기
        grid_cells = self.monitor_manager.grid_cells
        if not grid_cells:
            print("WARNING: No grid cells found.")
            return

        # 셀 ID를 기반으로 체크박스 생성
        cols = self.monitor_manager.config.get("grid_cols", 5)
        def make_state_logger(cid):
            return lambda state: print(f"[DEBUG] {cid} 체크박스 상태: {state}")
        for i, cell in enumerate(grid_cells):
            row = i // cols
            col = i % cols
            checkbox = QCheckBox(cell.id)
            checkbox.setChecked(False)
            checkbox.stateChanged.connect(make_state_logger(cell.id))
            checkbox.stateChanged.connect(self._on_cell_checkbox_changed)
            self.cell_checkboxes[cell.id] = checkbox
            self.cell_checkbox_layout.addWidget(checkbox, row, col)
        
        self._sync_select_all_checkbox()
    
    def initUI(self):
        """UI 초기화"""
        self.setWindowTitle("⚡ 카카오톡 실시간 즉시 감지 시스템")
        self.setGeometry(100, 100, 600, 550)  # 높이 조금 늘림
        
        layout = QVBoxLayout()
        
        # 제목
        title = QLabel("⚡ 카카오톡 실시간 즉시 감지 시스템")
        title.setFont(QFont("Arial", 18, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("color: #ff6600; margin: 10px;")
        layout.addWidget(title)
        
        # 설명
        info_text = """
⚡ 실시간 즉시 감지 시스템 (사람 눈과 같은 속도!):
1. '그리드 적용' - 모든 셀의 경계선을 녹색으로 표시 (3x5 = 15셀)
2. '오버레이 적용' - 각 셀마다 최적화된 OCR 영역을 빨간색으로 표시
3. 모니터링할 셀을 선택하고 '⚡ 실시간 모니터링' 시작 (30개 셀 모두 지원!)
4. "들어왔습니다" 메시지가 나타나는 순간 즉시 감지하여 0.1초 내 전송!
        """
        
        info_label = QLabel(info_text)
        info_label.setWordWrap(True)
        layout.addWidget(info_label)
        
        # 오버레이 설정 그룹
        settings_group = QGroupBox("공통 오버레이 설정")
        settings_layout = QVBoxLayout()
        
        # 오버레이 높이 설정
        height_layout = QHBoxLayout()
        height_layout.addWidget(QLabel("OCR 영역 높이:"))
        self.height_spinbox = QSpinBox()
        self.height_spinbox.setRange(20, 200)
        self.height_spinbox.setValue(120)
        self.height_spinbox.setSuffix("px")
        self.height_spinbox.valueChanged.connect(self.update_overlay_height)
        height_layout.addWidget(self.height_spinbox)
        height_layout.addStretch()
        settings_layout.addLayout(height_layout)
        
        # OCR 영역 가로 여백 설정
        margin_layout = QHBoxLayout()
        margin_layout.addWidget(QLabel("OCR 영역 가로 여백:"))
        self.margin_spinbox = QSpinBox()
        self.margin_spinbox.setRange(2, 50)
        self.margin_spinbox.setValue(5)
        self.margin_spinbox.setSuffix("px")
        self.margin_spinbox.setToolTip("좌우 여백 (작을수록 넓어짐)")
        self.margin_spinbox.valueChanged.connect(self.update_overlay_margin)
        margin_layout.addWidget(self.margin_spinbox)
        margin_layout.addStretch()
        settings_layout.addLayout(margin_layout)
        
        # OCR 영역 Y 위치 오프셋 설정
        offset_layout = QHBoxLayout()
        offset_layout.addWidget(QLabel("OCR 영역 위치:"))
        self.offset_spinbox = QSpinBox()
        self.offset_spinbox.setRange(-200, 200)
        self.offset_spinbox.setValue(0)
        self.offset_spinbox.setSuffix("px")
        self.offset_spinbox.setToolTip("음수: 위로 이동, 양수: 아래로 이동")
        self.offset_spinbox.valueChanged.connect(self.update_overlay_offset)
        offset_layout.addWidget(self.offset_spinbox)
        offset_layout.addStretch()
        settings_layout.addLayout(offset_layout)
        
        settings_group.setLayout(settings_layout)
        layout.addWidget(settings_group)
        
        # ⚡ 실시간 OCR 설정 그룹
        ocr_param_group = QGroupBox("⚡ 실시간 즉시 감지 OCR 설정")
        ocr_param_layout = QGridLayout()
        ocr_param_group.setLayout(ocr_param_layout)

        # OCR 간격 설정
        ocr_param_layout.addWidget(QLabel("OCR 간격:"), 0, 0)
        self.ocr_interval_spinbox = QDoubleSpinBox()
        self.ocr_interval_spinbox.setRange(0.02, 1.0)  # 0.02초까지 (50 FPS)
        self.ocr_interval_spinbox.setSingleStep(0.01)  # 0.01초 단위
        self.ocr_interval_spinbox.setValue(0.05)  # 기본값을 0.05초로 (20 FPS)
        self.ocr_interval_spinbox.setSuffix("초")
        self.ocr_interval_spinbox.setToolTip("초고속 감지 간격 (0.02-1.0초)")
        self.ocr_interval_spinbox.valueChanged.connect(self.update_ocr_interval)
        ocr_param_layout.addWidget(self.ocr_interval_spinbox, 0, 1)

        # 처리 방식 표시
        ocr_param_layout.addWidget(QLabel("처리 방식:"), 0, 2)
        mode_label = QLabel("⚡ 실시간 감지")
        mode_label.setStyleSheet("QLabel { background-color: #ff6600; color: white; padding: 5px; border-radius: 3px; font-weight: bold; }")
        mode_label.setToolTip("사람 눈과 같은 속도로 즉시 감지")
        ocr_param_layout.addWidget(mode_label, 0, 3)

        # 디버그 모드 설정
        self.debug_mode_checkbox = QCheckBox("디버그 모드")
        self.debug_mode_checkbox.setToolTip("이미지 저장 (성능 저하)")
        self.debug_mode_checkbox.stateChanged.connect(self.update_debug_mode)
        ocr_param_layout.addWidget(self.debug_mode_checkbox, 1, 0)

        # ⚡ 실시간 성능 프리셋 버튼들
        preset_layout = QHBoxLayout()
        
        speed_btn = QPushButton("⚡ 번개 감지")
        speed_btn.setToolTip("0.05초 간격 (초고속 실시간)")
        speed_btn.clicked.connect(lambda: self.set_performance_preset("lightning"))
        speed_btn.setStyleSheet("QPushButton { background-color: #ff6600; color: white; font-weight: bold; }")
        preset_layout.addWidget(speed_btn)
        
        stable_btn = QPushButton("🚀 고속 감지")
        stable_btn.setToolTip("0.1초 간격 (권장)")
        stable_btn.clicked.connect(lambda: self.set_performance_preset("fast"))
        stable_btn.setStyleSheet("QPushButton { background-color: #44aa44; color: white; font-weight: bold; }")
        preset_layout.addWidget(stable_btn)
        
        save_btn = QPushButton("⚖️ 균형 감지")
        save_btn.setToolTip("0.2초 간격 (안정성 우선)")
        save_btn.clicked.connect(lambda: self.set_performance_preset("balanced"))
        save_btn.setStyleSheet("QPushButton { background-color: #4444aa; color: white; font-weight: bold; }")
        preset_layout.addWidget(save_btn)
        
        ocr_param_layout.addLayout(preset_layout, 1, 1, 1, 3)

        layout.addWidget(ocr_param_group)
        
        # 🚀 주요 기능 버튼들
        button_layout = QGridLayout()
        
        self.grid_btn = QPushButton("📐 그리드 적용")
        self.grid_btn.setCheckable(True)
        self.grid_btn.clicked.connect(self.toggle_grid)
        self.grid_btn.setStyleSheet("QPushButton { padding: 8px; font-weight: bold; }")
        button_layout.addWidget(self.grid_btn, 0, 0)
        
        self.overlay_btn = QPushButton("🎯 오버레이 적용")
        self.overlay_btn.setCheckable(True)
        self.overlay_btn.clicked.connect(self.toggle_overlay)
        self.overlay_btn.setStyleSheet("QPushButton { padding: 8px; font-weight: bold; }")
        button_layout.addWidget(self.overlay_btn, 0, 1)
        
        self.monitor_btn = QPushButton("⚡ 실시간 모니터링 시작")
        self.monitor_btn.setCheckable(True)
        self.monitor_btn.clicked.connect(self.toggle_monitoring)
        self.monitor_btn.setStyleSheet("QPushButton { padding: 12px; font-weight: bold; background-color: #ff6600; color: white; }")
        button_layout.addWidget(self.monitor_btn, 1, 0, 1, 2)  # 2열 차지
        
        # 🧪 빠른 테스트 버튼
        test_btn = QPushButton("🧪 실시간 테스트 (2초 즉시감지)")
        test_btn.setToolTip("2초 동안 실시간 즉시 감지 테스트")
        test_btn.clicked.connect(self.quick_test)
        test_btn.setStyleSheet("QPushButton { padding: 8px; background-color: #aa4444; color: white; font-weight: bold; }")
        button_layout.addWidget(test_btn, 2, 0, 1, 2)
        
        layout.addLayout(button_layout)
        
        # 셀 체크박스 그룹 생성 전
        self.select_all_checkbox = QCheckBox("전체 선택")
        self.select_all_checkbox.stateChanged.connect(self._on_select_all_checkbox_changed)
        layout.addWidget(self.select_all_checkbox)
        
        # 셀 선택 (간단한 체크박스만)
        cell_group = QGroupBox("모니터링할 셀 선택")
        cell_layout = QVBoxLayout()
        cell_layout.addLayout(self.cell_checkbox_layout)
        cell_group.setLayout(cell_layout)
        layout.addWidget(cell_group)
        
        # 🚀 성능 모니터링 대시보드
        perf_group = QGroupBox("📊 실시간 성능 모니터")
        perf_layout = QGridLayout()
        perf_group.setLayout(perf_layout)
        
        # 성능 지표 라벨들
        self.fps_label = QLabel("FPS: 대기중")
        self.cache_label = QLabel("캐시: 0개")
        self.workers_label = QLabel("워커: 대기중")
        self.active_cells_label = QLabel("활성 셀: 0개")
        
        perf_layout.addWidget(self.fps_label, 0, 0)
        perf_layout.addWidget(self.cache_label, 0, 1)
        perf_layout.addWidget(self.workers_label, 0, 2)
        perf_layout.addWidget(self.active_cells_label, 0, 3)
        
        layout.addWidget(perf_group)
        
        # 성능 업데이트 타이머
        self.perf_timer = QTimer()
        self.perf_timer.timeout.connect(self.update_performance_display)
        self.perf_timer.start(1000)  # 1초마다 업데이트
        
        # 결과 표시
        self.result_text = QTextEdit()
        self.result_text.setMaximumHeight(120)
        self.result_text.setPlaceholderText("OCR 결과 및 자동 입력 로그가 여기에 표시됩니다...")
        layout.addWidget(QLabel("📊 실행 결과:"))
        layout.addWidget(self.result_text)
        
        self.setLayout(layout)
        
        # 그리드 정보 출력
        self.print_grid_info()
    
    def print_grid_info(self):
        """그리드 정보 출력"""
        print("="*70)
        print("⚡ 카카오톡 실시간 즉시 감지 시스템 초기화")
        print("="*70)
        print(f"📊 총 {len(self.monitor_manager.grid_cells)}개 셀 생성 (3x5 구조)")
        print(f"⚡ 실시간 OCR 영역 (100px 높이)")
        print(f"🚀 기본 성능: 0.1초 간격, 즉시 감지 (사람 눈보다 빠름!)")
        print(f"💾 강화된 캐싱: 2초 유효시간")
        print(f"🎯 30개 셀 모두 처리: 모든 채팅방 실시간 감지")
        print(f"🛡️ PaddleOCR 안정성 + 실시간 처리")
        print("="*70)
    
    def toggle_grid(self):
        """그리드 표시/숨기기"""
        if self.overlay_widget is None:
            self.overlay_widget = GridOverlayWidget(self.monitor_manager, self.height_spinbox.value())
            self.overlay_widget.set_overlay_margin(self.margin_spinbox.value())  # 여백 설정 추가
            self.overlay_widget.show()
        
        is_checked = self.grid_btn.isChecked()
        self.overlay_widget.set_grid_visible(is_checked)
        
        if is_checked:
            self.grid_btn.setText("그리드 숨기기")
            print("✅ 그리드가 표시되었습니다 (녹색 경계선)")
        else:
            self.grid_btn.setText("그리드 적용")
            print("❌ 그리드가 숨겨졌습니다")
    
    def toggle_overlay(self):
        """OCR 오버레이 표시/숨기기 토글"""
        is_checked = self.overlay_btn.isChecked()
        self.overlay_widget.set_overlay_visible(is_checked)
        
        if is_checked:
            self.overlay_btn.setText("OCR 오버레이 숨김")
            self.log_message("🟢 OCR 오버레이가 표시되었습니다.")
        else:
            self.overlay_btn.setText("OCR 오버레이 표시")
            self.log_message("🔴 OCR 오버레이가 숨겨졌습니다.")
    
    def get_smart_cell_selection(self, selected_cells):
        """⚡ 실시간 모니터링: 선택된 모든 셀 처리 (30개까지)"""
        # 실시간 모드에서는 모든 셀 처리!
        self.log_message(f"⚡ 실시간 모드: {len(selected_cells)}개 셀 모두 처리!")
        return selected_cells

    def toggle_monitoring(self):
        """모니터링 시작/중지"""
        is_checked = self.monitor_btn.isChecked()
        print(f"[DEBUG] 모든 체크박스 상태:")
        for cell_id, checkbox in self.cell_checkboxes.items():
            print(f"  {cell_id}: {checkbox.isChecked()}")
        if is_checked:
            selected_cells = [cell_id for cell_id, checkbox in self.cell_checkboxes.items() if checkbox.isChecked()]
            print(f"[DEBUG] 선택된 셀: {selected_cells}")
            if not selected_cells:
                self.log_message("❌ 모니터링할 셀을 선택해주세요")
                self.monitor_btn.setChecked(False)
                return
            
            # ⚡ 실시간 모니터링: 선택된 모든 셀 처리
            original_count = len(selected_cells)
            selected_cells = self.get_smart_cell_selection(selected_cells)
            
            # ⚡ 실시간 처리 안내
            if len(selected_cells) >= 30:
                self.log_message(f"⚡ 최대 30개 셀 실시간 감지! 모든 채팅방 즉시 처리!")
            elif len(selected_cells) >= 20:
                self.log_message(f"⚡ {len(selected_cells)}개 셀 실시간 감지! 고성능 처리!")
            elif len(selected_cells) >= 10:
                self.log_message(f"⚡ {len(selected_cells)}개 셀 실시간 감지! 빠른 처리!")
            else:
                self.log_message(f"⚡ {len(selected_cells)}개 셀 실시간 감지 시작!")
                
            try:
                self.monitor_manager.set_specific_cells_only(selected_cells)
                self.monitoring_thread = OCRMonitoringThread(self.monitor_manager)
                self.monitoring_thread.set_enabled_cells(selected_cells)
                self.monitoring_thread.ocr_detected.connect(self.on_ocr_detected)
                self.monitoring_thread.message_sent.connect(self.on_message_sent)
                
                # 스레드 시작 전 상태 확인
                print(f"🚀 [DEBUG] 스레드 시작 준비: {len(selected_cells)}개 셀")
                self.monitoring_thread.start()
                
                # 스레드가 제대로 시작되었는지 확인
                import time
                time.sleep(0.1)  # 0.1초 대기
                
                if self.monitoring_thread.isRunning():
                    self.monitor_btn.setText("🛑 실시간 모니터링 중지")
                    self.log_message(f"⚡ 실시간 모니터링 시작: {len(selected_cells)}개 셀 (즉시 감지)")
                    print(f"⚡ [DEBUG] 실시간 스레드 정상 시작됨")
                else:
                    self.log_message("❌ 모니터링 스레드 시작 실패")
                    self.monitor_btn.setChecked(False)
                    print(f"❌ [DEBUG] 스레드 시작 실패")
                    
            except Exception as e:
                self.log_message(f"❌ 모니터링 시작 오류: {e}")
                self.monitor_btn.setChecked(False)
                print(f"❌ [DEBUG] 모니터링 시작 예외: {e}")
        else:
            print(f"🛑 [DEBUG] 모니터링 중지 요청")
            if self.monitoring_thread:
                self.monitoring_thread.stop()
                self.monitoring_thread.wait()
                self.monitoring_thread = None
                print(f"🛑 [DEBUG] 스레드 정상 중지됨")
            self.monitor_btn.setText("⚡ 실시간 모니터링 시작")
            self.log_message("⏹️ 실시간 모니터링이 중지되었습니다")

    def quick_test(self):
        """🧪 빠른 테스트 (2초 실시간 감지)"""
        selected_cells = [cell_id for cell_id, checkbox in self.cell_checkboxes.items() if checkbox.isChecked()]
        
        if not selected_cells:
            self.log_message("❌ 테스트할 셀을 먼저 선택해주세요!")
            return
        
        if self.monitoring_thread and self.monitoring_thread.running:
            self.log_message("⚠️ 이미 모니터링이 실행 중입니다!")
            return
        
        # ⚡ 번개 모드 적용
        self.set_performance_preset("lightning")  # 번개 모드 (0.05초)
        
        # 2초 테스트 시작
        self.log_message(f"🧪 2초 실시간 테스트 시작! (셀: {len(selected_cells)}개, 즉시 감지)")
        
        # 모니터링 시작
        self.monitor_manager.set_specific_cells_only(selected_cells)
        self.monitoring_thread = OCRMonitoringThread(self.monitor_manager)
        self.monitoring_thread.set_enabled_cells(selected_cells)
        self.monitoring_thread.ocr_detected.connect(self.on_ocr_detected)
        self.monitoring_thread.message_sent.connect(self.on_message_sent)
        self.monitoring_thread.start()
        
        # 2초 후 자동 중지 타이머
        QTimer.singleShot(2000, self.stop_quick_test)
        
        self.log_message(f"⚡ 실시간 감지 중... (2초 후 자동 중지)")

    def stop_quick_test(self):
        """🧪 빠른 테스트 중지"""
        if self.monitoring_thread:
            self.monitoring_thread.stop()
            self.monitoring_thread.wait()
            self.monitoring_thread = None
            self.log_message("🧪 실시간 테스트 완료!")
    
    def update_overlay_height(self, height):
        """오버레이 높이 업데이트"""
        if self.overlay_widget:
            self.overlay_widget.set_overlay_height(height)
        print(f"📏 OCR 영역 높이: {height}px")
    
    def update_overlay_margin(self, margin):
        """OCR 영역 가로 여백 업데이트"""
        if self.overlay_widget:
            self.overlay_widget.set_overlay_margin(margin)
        print(f"📏 OCR 영역 가로 여백: {margin}px")
    
    def update_overlay_offset(self, offset):
        """OCR 영역 Y 위치 오프셋 업데이트"""
        if self.overlay_widget:
            self.overlay_widget.set_overlay_offset(offset)
        print(f"📏 OCR 영역 Y 위치: {self.overlay_offset}px")
    
    def on_ocr_detected(self, cell_id, text, x, y):
        """OCR 감지 이벤트"""
        timestamp = time.strftime("%H:%M:%S")
        log_text = f"[{timestamp}] 🎯 {cell_id}: '{text}' 감지됨\n"
        self.result_text.append(log_text)
        self.scroll_to_bottom()
    
    def on_message_sent(self, cell_id, message):
        """메시지 전송 이벤트"""
        timestamp = time.strftime("%H:%M:%S")
        log_text = f"[{timestamp}] 📤 {cell_id}: '{message[:30]}...' 전송완료\n"
        self.result_text.append(log_text)
        self.scroll_to_bottom()
    
    def scroll_to_bottom(self):
        """텍스트 영역 하단으로 스크롤"""
        scrollbar = self.result_text.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
    
    def closeEvent(self, event):
        """윈도우 종료 이벤트 (리소스 정리)"""
        # 성능 타이머 정지
        if hasattr(self, 'perf_timer'):
            self.perf_timer.stop()
        
        # 모니터링 스레드 정지
        if self.monitoring_thread:
            self.monitoring_thread.stop()
            self.monitoring_thread.wait()
        
        # 오버레이 위젯 정리
        if self.overlay_widget:
            self.overlay_widget.close()
        
        print("🛑 실시간 OCR 모니터링 시스템 종료됨")
        event.accept()

    def log_message(self, message: str):
        """로그 메시지를 UI에 표시합니다."""
        self.result_text.append(message)
        self.scroll_to_bottom()

    def _on_select_all_checkbox_changed(self, state):
        checked = (state == Qt.Checked)
        for checkbox in self.cell_checkboxes.values():
            checkbox.blockSignals(True)
            checkbox.setChecked(checked)
            checkbox.blockSignals(False)
        # 필요시 모니터링 매니저에도 반영
        # self.monitor_manager.set_all_cells_enabled(checked)

    def _on_cell_checkbox_changed(self, state):
        self._sync_select_all_checkbox()

    def _sync_select_all_checkbox(self):
        if not self.cell_checkboxes:
            self.select_all_checkbox.setCheckState(Qt.Unchecked)
            return
        checked_count = sum(1 for cb in self.cell_checkboxes.values() if cb.isChecked())
        if checked_count == len(self.cell_checkboxes):
            self.select_all_checkbox.setCheckState(Qt.Checked)
        elif checked_count == 0:
            self.select_all_checkbox.setCheckState(Qt.Unchecked)
        else:
            self.select_all_checkbox.setCheckState(Qt.PartiallyChecked)

    def update_ocr_interval(self, value):
        """OCR 간격 실시간 업데이트"""
        if self.monitoring_thread:
            self.monitoring_thread.ocr_interval_sec = value
            print(f"⚡ OCR 간격 업데이트: {value}초")

    def update_ocr_workers(self, value):
        """워커 수 업데이트 (실시간 처리에서는 무시)"""
        # 실시간 모드에서는 항상 1개만 사용 (즉시 처리)
        print(f"⚡ 실시간 모드: 워커 수 고정 (1개, 즉시 처리)")

    def update_debug_mode(self, state):
        """디버그 모드 실시간 업데이트"""
        debug_mode = state == 2  # Qt.Checked
        if self.monitoring_thread:
            self.monitoring_thread.debug_mode = debug_mode
            print(f"🐛 디버그 모드: {'활성화' if debug_mode else '비활성화'}")

    def set_performance_preset(self, preset_name):
        """⚡ 실시간 모니터링 성능 프리셋 적용"""
        presets = {
            "lightning": {
                "interval": 0.05,
                "workers": 1,
                "debug": False,
                "name": "⚡ 번개 감지"
            },
            "fast": {
                "interval": 0.1,
                "workers": 1,
                "debug": False,
                "name": "🚀 고속 감지"
            },
            "balanced": {
                "interval": 0.2,
                "workers": 1,
                "debug": False,
                "name": "⚖️ 균형 감지"
            },
            "speed": {
                "interval": 0.1,
                "workers": 1,
                "debug": False,
                "name": "🚀 고속 감지"
            }
        }
        
        if preset_name in presets:
            preset = presets[preset_name]
            
            # UI 업데이트
            self.ocr_interval_spinbox.setValue(preset["interval"])
            self.debug_mode_checkbox.setChecked(preset["debug"])
            
            # 모니터링 스레드 업데이트
            if self.monitoring_thread:
                self.monitoring_thread.set_performance_mode(
                    interval_sec=preset["interval"],
                    max_workers=preset["workers"],
                    debug_mode=preset["debug"]
                )
            
            print(f"🎯 {preset['name']} 적용됨!")
            self.log_message(f"⚡ 실시간 프리셋 적용: {preset['name']} ({preset['interval']}초 간격, 즉시 감지)")

    def get_current_performance_info(self):
        """현재 성능 설정 정보 반환"""
        if self.monitoring_thread:
            return {
                "interval": getattr(self.monitoring_thread, 'ocr_interval_sec', 0.8),
                "workers": 1,  # 배치 모드 고정 (5개씩 배치)
                "debug": getattr(self.monitoring_thread, 'debug_mode', False),
                "enabled_cells": len(getattr(self.monitoring_thread, 'enabled_cells', []))
            }
        return None

    def update_performance_display(self):
        """실시간 성능 통계 업데이트"""
        if self.monitoring_thread and self.monitoring_thread.running:
            # FPS 계산 (대략적)
            fps = 1.0 / self.monitoring_thread.ocr_interval_sec
            self.fps_label.setText(f"⚡ FPS: {fps:.1f}")
            
            # 캐시 상태
            cache_count = len(getattr(self.monitoring_thread, 'ocr_cache', {}))
            self.cache_label.setText(f"💾 캐시: {cache_count}개")
            
            # 워커 상태 (실시간 모드)
            workers = 1  # 실시간 모드
            self.workers_label.setText(f"👥 워커: {workers}개 (실시간)")
            
            # 활성 셀 수
            active_count = len(getattr(self.monitoring_thread, 'enabled_cells', []))
            self.active_cells_label.setText(f"🎯 활성 셀: {active_count}개")
            
            # 성능 상태에 따른 색상 변경
            if fps >= 2.0:
                self.fps_label.setStyleSheet("color: green; font-weight: bold;")
            elif fps >= 1.0:
                self.fps_label.setStyleSheet("color: orange; font-weight: bold;")
            else:
                self.fps_label.setStyleSheet("color: red; font-weight: bold;")
        else:
            # 모니터링 중지 상태
            self.fps_label.setText("FPS: 대기중")
            self.cache_label.setText("캐시: 0개")
            self.workers_label.setText("워커: 대기중")
            self.active_cells_label.setText("활성 셀: 0개")
            
            # 기본 색상으로 복원
            for label in [self.fps_label, self.cache_label, self.workers_label, self.active_cells_label]:
                label.setStyleSheet("")

def main():
    # High DPI 지원 활성화
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
    
    app = QApplication(sys.argv)
    
    # DPI 스케일링 정보 출력
    screen = app.primaryScreen()
    dpi = screen.logicalDotsPerInch()
    scale_factor = screen.devicePixelRatio()
    print(f"🖥️ DPI 정보: {dpi}, 스케일 팩터: {scale_factor}")
    
    controller = GridOverlayController()
    controller.show()
    
    sys.exit(app.exec_())

if __name__ == "__main__":
    main() 