"""
Screen Coordinate Verification Tool
Helps verify if OCR areas are correctly positioned over text regions
"""
from __future__ import annotations

import sys
import os
import cv2
import numpy as np
import mss
import time
from datetime import datetime
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                           QHBoxLayout, QPushButton, QLabel, QTextEdit, 
                           QSpinBox, QGroupBox, QGridLayout, QCheckBox)
from PyQt5.QtCore import Qt, QTimer, QThread, pyqtSignal
from PyQt5.QtGui import QPixmap, QImage, QPainter, QPen, QColor

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(project_root, 'src'))

from core.config_manager import ConfigManager
from core.grid_manager import GridManager
from ocr.enhanced_ocr_service import EnhancedOCRService


class ScreenCaptureThread(QThread):
    """Thread for continuous screen capture."""
    
    image_signal: pyqtSignal = pyqtSignal(np.ndarray, str)  # image, cell_id
    
    def __init__(self, cell_bounds: tuple[int, int, int, int], cell_id: str) -> None:
        super().__init__()
        self.cell_bounds = cell_bounds
        self.cell_id = cell_id
        self.running = False
        
    def run(self) -> None:
        """Capture screen continuously."""
        self.running = True
        
        with mss.mss() as sct:
            while self.running:
                try:
                    # Capture the cell area
                    area = {
                        'left': self.cell_bounds[0],
                        'top': self.cell_bounds[1],
                        'width': self.cell_bounds[2],
                        'height': self.cell_bounds[3]
                    }
                    
                    screenshot = sct.grab(area)
                    image = np.array(screenshot)
                    
                    # Convert BGRA to BGR
                    if image.shape[2] == 4:
                        image = image[:, :, :3]
                    
                    # Emit the image
                    self.image_signal.emit(image, self.cell_id)
                    
                    # Small delay
                    time.sleep(0.1)
                    
                except Exception as e:
                    print(f"Capture error: {e}")
                    time.sleep(1)
    
    def stop(self) -> None:
        """Stop capturing."""
        self.running = False


class CoordinateVerificationWindow(QMainWindow):
    """Main window for verifying screen coordinates."""
    
    def __init__(self) -> None:
        super().__init__()
        self.config = ConfigManager()
        self.grid_manager = GridManager(self.config)
        self.ocr_service = EnhancedOCRService(self.config)
        
        self.current_cell_index: int = 0
        self.capture_thread: ScreenCaptureThread | None = None
        self.current_image: np.ndarray | None = None
        
        self.initUI()
        
    def initUI(self) -> None:
        """Initialize the UI."""
        self.setWindowTitle("OCR 영역 좌표 검증 도구")
        self.setGeometry(100, 100, 1200, 800)
        
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        main_layout = QHBoxLayout(central_widget)
        
        # Left panel - Controls
        left_panel = self.create_left_panel()
        main_layout.addWidget(left_panel, 1)
        
        # Right panel - Image display
        right_panel = self.create_right_panel()
        main_layout.addWidget(right_panel, 2)
        
        # Start with first cell
        self.load_cell(0)
        
    def create_left_panel(self) -> QWidget:
        """Create the control panel."""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        
        # Cell selection
        cell_group = QGroupBox("셀 선택")
        cell_layout = QVBoxLayout(cell_group)
        
        # Cell navigation
        nav_layout = QHBoxLayout()
        self.prev_btn = QPushButton("◀ 이전")
        self.prev_btn.clicked.connect(self.prev_cell)
        self.next_btn = QPushButton("다음 ▶")
        self.next_btn.clicked.connect(self.next_cell)
        nav_layout.addWidget(self.prev_btn)
        nav_layout.addWidget(self.next_btn)
        cell_layout.addLayout(nav_layout)
        
        # Cell info
        self.cell_info_label = QLabel("Cell: -")
        self.cell_info_label.setStyleSheet("font-size: 14px; font-weight: bold;")
        cell_layout.addWidget(self.cell_info_label)
        
        # Target cell button
        self.target_cell_btn = QPushButton("목표 셀로 이동 (M0_R0_C1)")
        self.target_cell_btn.clicked.connect(self.go_to_target_cell)
        self.target_cell_btn.setStyleSheet("background-color: #4CAF50; color: white;")
        cell_layout.addWidget(self.target_cell_btn)
        
        layout.addWidget(cell_group)
        
        # Coordinates info
        coord_group = QGroupBox("좌표 정보")
        coord_layout = QGridLayout(coord_group)
        
        self.coord_labels: dict[str, QLabel] = {}
        labels = ["셀 영역:", "OCR 영역:", "크기:"]
        for i, label in enumerate(labels):
            coord_layout.addWidget(QLabel(label), i, 0)
            info_label = QLabel("-")
            info_label.setWordWrap(True)
            self.coord_labels[label] = info_label
            coord_layout.addWidget(info_label, i, 1)
        
        layout.addWidget(coord_group)
        
        # OCR Test
        ocr_group = QGroupBox("OCR 테스트")
        ocr_layout = QVBoxLayout(ocr_group)
        
        # Test buttons
        self.test_ocr_btn = QPushButton("OCR 실행")
        self.test_ocr_btn.clicked.connect(self.test_ocr)
        self.test_ocr_btn.setStyleSheet("background-color: #2196F3; color: white;")
        ocr_layout.addWidget(self.test_ocr_btn)
        
        self.save_btn = QPushButton("현재 이미지 저장")
        self.save_btn.clicked.connect(self.save_current_image)
        ocr_layout.addWidget(self.save_btn)
        
        # OCR results
        self.ocr_result_text = QTextEdit()
        self.ocr_result_text.setReadOnly(True)
        self.ocr_result_text.setMaximumHeight(200)
        ocr_layout.addWidget(QLabel("OCR 결과:"))
        ocr_layout.addWidget(self.ocr_result_text)
        
        layout.addWidget(ocr_group)
        
        # Detection test
        detect_group = QGroupBox("감지 테스트")
        detect_layout = QVBoxLayout(detect_group)
        
        self.continuous_test_cb = QCheckBox("연속 테스트 모드")
        self.continuous_test_cb.stateChanged.connect(self.toggle_continuous_test)
        detect_layout.addWidget(self.continuous_test_cb)
        
        self.detection_log = QTextEdit()
        self.detection_log.setReadOnly(True)
        self.detection_log.setMaximumHeight(150)
        detect_layout.addWidget(QLabel("감지 로그:"))
        detect_layout.addWidget(self.detection_log)
        
        layout.addWidget(detect_group)
        
        layout.addStretch()
        
        return panel
    
    def create_right_panel(self) -> QWidget:
        """Create the image display panel."""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        
        # Image display
        self.image_label = QLabel()
        self.image_label.setMinimumSize(800, 600)
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_label.setStyleSheet("border: 2px solid #ccc;")
        self.image_label.setScaledContents(False)
        
        layout.addWidget(QLabel("캡처된 이미지 (OCR 영역):"))
        layout.addWidget(self.image_label)
        
        # Info panel
        info_layout = QHBoxLayout()
        self.capture_info_label = QLabel("대기 중...")
        self.capture_info_label.setStyleSheet("color: #666;")
        info_layout.addWidget(self.capture_info_label)
        info_layout.addStretch()
        
        layout.addLayout(info_layout)
        
        return panel
    
    def load_cell(self, index: int) -> None:
        """Load a specific cell."""
        if 0 <= index < len(self.grid_manager.cells):
            self.current_cell_index = index
            cell = self.grid_manager.cells[index]
            
            # Update info
            self.cell_info_label.setText(f"Cell: {cell.id} ({index + 1}/{len(self.grid_manager.cells)})")
            
            # Update coordinates
            self.coord_labels["셀 영역:"].setText(
                f"X: {cell.bounds[0]}, Y: {cell.bounds[1]}, "
                f"W: {cell.bounds[2]}, H: {cell.bounds[3]}"
            )
            self.coord_labels["OCR 영역:"].setText(
                f"X: {cell.ocr_area[0]}, Y: {cell.ocr_area[1]}, "
                f"W: {cell.ocr_area[2]}, H: {cell.ocr_area[3]}"
            )
            self.coord_labels["크기:"].setText(
                f"셀: {cell.bounds[2]}x{cell.bounds[3]}, "
                f"OCR: {cell.ocr_area[2]}x{cell.ocr_area[3]}"
            )
            
            # Stop previous capture
            if self.capture_thread:
                self.capture_thread.stop()
                self.capture_thread.wait()
            
            # Start new capture
            self.capture_thread = ScreenCaptureThread(cell.ocr_area, cell.id)
            self.capture_thread.image_signal.connect(self.on_image_captured)
            self.capture_thread.start()
            
            # Clear previous results
            self.ocr_result_text.clear()
            
            # Highlight target cell
            if cell.id == "M0_R0_C1":
                self.cell_info_label.setStyleSheet("font-size: 14px; font-weight: bold; color: red;")
                self.log_detection("⭐ 목표 셀 로드됨!")
            else:
                self.cell_info_label.setStyleSheet("font-size: 14px; font-weight: bold; color: black;")
    
    def on_image_captured(self, image: np.ndarray, cell_id: str) -> None:
        """Handle captured image."""
        self.current_image = image
        self.display_image(image)
        
        # Update capture info
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        self.capture_info_label.setText(f"캡처 시간: {timestamp}")
        
        # Continuous test mode
        if self.continuous_test_cb.isChecked():
            self.test_ocr()
    
    def display_image(self, image: np.ndarray) -> None:
        """Display the captured image."""
        try:
            # Convert to QImage
            height, width, channel = image.shape
            bytes_per_line = 3 * width
            
            # Create QImage
            if channel == 3:
                q_image = QImage(image.data, width, height, bytes_per_line, QImage.Format.Format_BGR888)
            else:
                q_image = QImage(image.data, width, height, bytes_per_line, QImage.Format.Format_RGB888)
            
            # Scale to fit label while maintaining aspect ratio
            pixmap = QPixmap.fromImage(q_image)
            scaled_pixmap = pixmap.scaled(
                self.image_label.size(), 
                Qt.AspectRatioMode.KeepAspectRatio, 
                Qt.TransformationMode.SmoothTransformation
            )
            
            # Draw border and grid
            painter = QPainter(scaled_pixmap)
            painter.setPen(QPen(QColor(255, 0, 0), 2))
            painter.drawRect(0, 0, scaled_pixmap.width()-1, scaled_pixmap.height()-1)
            
            # Draw grid lines
            painter.setPen(QPen(QColor(0, 255, 0, 100), 1))
            for i in range(1, 4):
                x = scaled_pixmap.width() * i // 4
                y = scaled_pixmap.height() * i // 4
                painter.drawLine(x, 0, x, scaled_pixmap.height())
                painter.drawLine(0, y, scaled_pixmap.width(), y)
            
            painter.end()
            
            self.image_label.setPixmap(scaled_pixmap)
            
        except Exception as e:
            print(f"Display error: {e}")
    
    def test_ocr(self) -> None:
        """Test OCR on current image."""
        if self.current_image is None:
            self.ocr_result_text.append("❌ 이미지 없음")
            return
        
        try:
            # Get current cell
            cell = self.grid_manager.cells[self.current_cell_index]
            
            # Perform OCR
            self.ocr_result_text.append(f"\n--- OCR 테스트 ({datetime.now().strftime('%H:%M:%S')}) ---")
            
            result = self.ocr_service.perform_ocr_with_recovery(
                self.current_image.copy(), 
                cell.id
            )
            
            if result.is_valid():
                self.ocr_result_text.append(f"✅ 텍스트 감지: '{result.text}'")
                self.ocr_result_text.append(f"   신뢰도: {result.confidence:.2f}")
                self.ocr_result_text.append(f"   위치: {result.position}")
                
                # Check if trigger pattern
                is_trigger = self.ocr_service.check_trigger_patterns(result)
                if is_trigger:
                    self.ocr_result_text.append("   🎯 트리거 패턴 매칭!")
                    self.log_detection(f"🎯 {cell.id}: 트리거 감지 - '{result.text}'")
                else:
                    self.ocr_result_text.append("   ❌ 트리거 패턴 아님")
                
                # Show all results if available
                if 'all_results' in result.debug_info and result.debug_info['all_results']:
                    self.ocr_result_text.append("\n   모든 전처리 결과:")
                    for r in result.debug_info['all_results']:
                        self.ocr_result_text.append(
                            f"   - 전략 {r['strategy']}: '{r['text']}' (신뢰도: {r['confidence']:.2f})"
                        )
                        
            else:
                self.ocr_result_text.append("⚪ 텍스트 감지 안됨")
                
                if 'error' in result.debug_info:
                    self.ocr_result_text.append(f"   오류: {result.debug_info['error']}")
                    
                if 'all_results' in result.debug_info and result.debug_info['all_results']:
                    self.ocr_result_text.append("\n   부분 결과:")
                    for r in result.debug_info['all_results']:
                        self.ocr_result_text.append(
                            f"   - 전략 {r['strategy']}: '{r['text']}' (신뢰도: {r['confidence']:.2f})"
                        )
            
            # Scroll to bottom
            self.ocr_result_text.verticalScrollBar().setValue(
                self.ocr_result_text.verticalScrollBar().maximum()
            )
            
        except Exception as e:
            self.ocr_result_text.append(f"❌ OCR 오류: {e}")
    
    def save_current_image(self) -> None:
        """Save current image for analysis."""
        if self.current_image is None:
            return
        
        try:
            # Create directory
            os.makedirs("debug_screenshots/coordinate_verification", exist_ok=True)
            
            # Generate filename
            cell = self.grid_manager.cells[self.current_cell_index]
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"debug_screenshots/coordinate_verification/{cell.id}_{timestamp}.png"
            
            # Save image
            cv2.imwrite(filename, self.current_image)
            
            # Also save with annotations
            annotated = self.current_image.copy()
            cv2.putText(annotated, f"{cell.id}", (10, 30), 
                       cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
            cv2.putText(annotated, f"Size: {annotated.shape[1]}x{annotated.shape[0]}", 
                       (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 1)
            
            annotated_filename = f"debug_screenshots/coordinate_verification/{cell.id}_{timestamp}_annotated.png"
            cv2.imwrite(annotated_filename, annotated)
            
            self.log_detection(f"💾 이미지 저장됨: {filename}")
            
        except Exception as e:
            self.log_detection(f"❌ 저장 오류: {e}")
    
    def log_detection(self, message: str) -> None:
        """Log detection message."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.detection_log.append(f"[{timestamp}] {message}")
        self.detection_log.verticalScrollBar().setValue(
            self.detection_log.verticalScrollBar().maximum()
        )
    
    def prev_cell(self) -> None:
        """Go to previous cell."""
        if self.current_cell_index > 0:
            self.load_cell(self.current_cell_index - 1)
    
    def next_cell(self) -> None:
        """Go to next cell."""
        if self.current_cell_index < len(self.grid_manager.cells) - 1:
            self.load_cell(self.current_cell_index + 1)
    
    def go_to_target_cell(self) -> None:
        """Go to target cell M0_R0_C1."""
        for i, cell in enumerate(self.grid_manager.cells):
            if cell.id == "M0_R0_C1":
                self.load_cell(i)
                break
    
    def toggle_continuous_test(self, state: int) -> None:
        """Toggle continuous test mode."""
        if state:
            self.log_detection("🔄 연속 테스트 모드 시작")
        else:
            self.log_detection("⏸️ 연속 테스트 모드 중지")
    
    def closeEvent(self, event) -> None:
        """Handle window close."""
        if self.capture_thread:
            self.capture_thread.stop()
            self.capture_thread.wait()
        event.accept()


def main() -> None:
    """Main function."""
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    
    window = CoordinateVerificationWindow()
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()