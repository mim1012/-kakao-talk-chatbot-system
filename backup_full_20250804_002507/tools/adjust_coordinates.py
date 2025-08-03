"""
Coordinate Adjustment Tool
Helps adjust cell coordinates to match actual KakaoTalk window position
"""
from __future__ import annotations

import sys
import os
import json
import mss
import cv2
import numpy as np
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                           QHBoxLayout, QPushButton, QLabel, QSpinBox, 
                           QGroupBox, QGridLayout, QTextEdit, QMessageBox)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QPixmap, QImage

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(project_root, 'src'))

from core.config_manager import ConfigManager
from ocr.enhanced_ocr_service import EnhancedOCRService


class CoordinateAdjustmentTool(QMainWindow):
    """Tool for adjusting OCR coordinates."""
    
    def __init__(self) -> None:
        super().__init__()
        self.config = ConfigManager()
        self.ocr_service = EnhancedOCRService(self.config)
        
        # Test area coordinates
        self.test_x: int = 100
        self.test_y: int = 100
        self.test_width: int = 300
        self.test_height: int = 100
        
        self.current_image: np.ndarray | None = None
        self.initUI()
        
    def initUI(self) -> None:
        """Initialize UI."""
        self.setWindowTitle("OCR 좌표 조정 도구")
        self.setGeometry(100, 100, 1000, 700)
        
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        main_layout = QHBoxLayout(central_widget)
        
        # Left panel - Controls
        left_panel = self.create_control_panel()
        main_layout.addWidget(left_panel)
        
        # Right panel - Preview
        right_panel = self.create_preview_panel()
        main_layout.addWidget(right_panel)
        
        # Initial capture
        self.capture_test_area()
        
    def create_control_panel(self) -> QWidget:
        """Create control panel."""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        
        # Instructions
        instructions = QLabel(
            "사용 방법:\n"
            "1. 카카오톡을 실행하고 채팅방을 엽니다\n"
            "2. 좌표를 조정하여 메시지 영역을 맞춥니다\n"
            "3. '캡처 및 테스트' 버튼으로 확인합니다\n"
            "4. 한글 텍스트가 정상적으로 인식되면 '설정 저장'을 클릭합니다"
        )
        instructions.setStyleSheet("padding: 10px; background-color: #f0f0f0;")
        layout.addWidget(instructions)
        
        # Coordinate adjustment
        coord_group = QGroupBox("테스트 영역 좌표")
        coord_layout = QGridLayout(coord_group)
        
        # X coordinate
        coord_layout.addWidget(QLabel("X:"), 0, 0)
        self.x_spin = QSpinBox()
        self.x_spin.setRange(0, 3000)
        self.x_spin.setValue(self.test_x)
        self.x_spin.valueChanged.connect(self.update_coordinates)
        coord_layout.addWidget(self.x_spin, 0, 1)
        
        # Y coordinate
        coord_layout.addWidget(QLabel("Y:"), 1, 0)
        self.y_spin = QSpinBox()
        self.y_spin.setRange(0, 2000)
        self.y_spin.setValue(self.test_y)
        self.y_spin.valueChanged.connect(self.update_coordinates)
        coord_layout.addWidget(self.y_spin, 1, 1)
        
        # Width
        coord_layout.addWidget(QLabel("너비:"), 2, 0)
        self.width_spin = QSpinBox()
        self.width_spin.setRange(50, 1000)
        self.width_spin.setValue(self.test_width)
        self.width_spin.valueChanged.connect(self.update_coordinates)
        coord_layout.addWidget(self.width_spin, 2, 1)
        
        # Height
        coord_layout.addWidget(QLabel("높이:"), 3, 0)
        self.height_spin = QSpinBox()
        self.height_spin.setRange(20, 500)
        self.height_spin.setValue(self.test_height)
        self.height_spin.valueChanged.connect(self.update_coordinates)
        coord_layout.addWidget(self.height_spin, 3, 1)
        
        layout.addWidget(coord_group)
        
        # Quick adjust buttons
        quick_group = QGroupBox("빠른 조정")
        quick_layout = QGridLayout(quick_group)
        
        # Position buttons
        move_buttons = [
            ("↑", 0, 1, lambda: self.move_area(0, -10)),
            ("←", 1, 0, lambda: self.move_area(-10, 0)),
            ("→", 1, 2, lambda: self.move_area(10, 0)),
            ("↓", 2, 1, lambda: self.move_area(0, 10)),
        ]
        
        for text, row, col, func in move_buttons:
            btn = QPushButton(text)
            btn.clicked.connect(func)
            quick_layout.addWidget(btn, row, col)
        
        # Size buttons
        size_buttons = [
            ("크게", 3, 0, lambda: self.resize_area(10, 10)),
            ("작게", 3, 2, lambda: self.resize_area(-10, -10)),
        ]
        
        for text, row, col, func in size_buttons:
            btn = QPushButton(text)
            btn.clicked.connect(func)
            quick_layout.addWidget(btn, row, col)
        
        layout.addWidget(quick_group)
        
        # Test buttons
        test_group = QGroupBox("테스트")
        test_layout = QVBoxLayout(test_group)
        
        # Capture button
        self.capture_btn = QPushButton("캡처 및 테스트")
        self.capture_btn.clicked.connect(self.capture_and_test)
        self.capture_btn.setStyleSheet("background-color: #2196F3; color: white; padding: 10px;")
        test_layout.addWidget(self.capture_btn)
        
        # Auto scan button
        self.auto_scan_btn = QPushButton("자동 스캔 (전체 화면)")
        self.auto_scan_btn.clicked.connect(self.auto_scan_screen)
        self.auto_scan_btn.setStyleSheet("background-color: #4CAF50; color: white; padding: 10px;")
        test_layout.addWidget(self.auto_scan_btn)
        
        layout.addWidget(test_group)
        
        # Results
        result_group = QGroupBox("OCR 결과")
        result_layout = QVBoxLayout(result_group)
        
        self.result_text = QTextEdit()
        self.result_text.setReadOnly(True)
        self.result_text.setMaximumHeight(150)
        result_layout.addWidget(self.result_text)
        
        layout.addWidget(result_group)
        
        # Save button
        self.save_btn = QPushButton("설정 저장")
        self.save_btn.clicked.connect(self.save_coordinates)
        self.save_btn.setStyleSheet("background-color: #FF9800; color: white; padding: 10px;")
        layout.addWidget(self.save_btn)
        
        layout.addStretch()
        
        return panel
    
    def create_preview_panel(self) -> QWidget:
        """Create preview panel."""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        
        # Preview label
        layout.addWidget(QLabel("캡처 미리보기:"))
        
        self.preview_label = QLabel()
        self.preview_label.setMinimumSize(600, 400)
        self.preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview_label.setStyleSheet("border: 2px solid #ccc;")
        self.preview_label.setScaledContents(False)
        
        layout.addWidget(self.preview_label)
        
        # Info label
        self.info_label = QLabel("대기 중...")
        self.info_label.setStyleSheet("color: #666; padding: 5px;")
        layout.addWidget(self.info_label)
        
        return panel
    
    def update_coordinates(self) -> None:
        """Update test area coordinates."""
        self.test_x = self.x_spin.value()
        self.test_y = self.y_spin.value()
        self.test_width = self.width_spin.value()
        self.test_height = self.height_spin.value()
    
    def move_area(self, dx: int, dy: int) -> None:
        """Move test area."""
        self.x_spin.setValue(self.x_spin.value() + dx)
        self.y_spin.setValue(self.y_spin.value() + dy)
    
    def resize_area(self, dw: int, dh: int) -> None:
        """Resize test area."""
        self.width_spin.setValue(max(50, self.width_spin.value() + dw))
        self.height_spin.setValue(max(20, self.height_spin.value() + dh))
    
    def capture_test_area(self) -> np.ndarray | None:
        """Capture the test area."""
        try:
            with mss.mss() as sct:
                area = {
                    'left': self.test_x,
                    'top': self.test_y,
                    'width': self.test_width,
                    'height': self.test_height
                }
                
                screenshot = sct.grab(area)
                image = np.array(screenshot)
                
                # Convert BGRA to BGR
                if image.shape[2] == 4:
                    image = image[:, :, :3]
                
                self.current_image = image
                self.display_preview(image)
                
                return image
                
        except Exception as e:
            self.info_label.setText(f"캡처 오류: {e}")
            return None
    
    def display_preview(self, image: np.ndarray) -> None:
        """Display preview image."""
        try:
            # Add border to image
            bordered = cv2.copyMakeBorder(
                image, 2, 2, 2, 2, 
                cv2.BORDER_CONSTANT, 
                value=(0, 255, 0)
            )
            
            # Convert to QImage
            height, width, channel = bordered.shape
            bytes_per_line = 3 * width
            
            q_image = QImage(bordered.data, width, height, bytes_per_line, QImage.Format.Format_BGR888)
            
            # Scale to fit
            pixmap = QPixmap.fromImage(q_image)
            scaled_pixmap = pixmap.scaled(
                self.preview_label.size(),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            
            self.preview_label.setPixmap(scaled_pixmap)
            self.info_label.setText(f"크기: {image.shape[1]}x{image.shape[0]}")
            
        except Exception as e:
            self.info_label.setText(f"표시 오류: {e}")
    
    def capture_and_test(self) -> None:
        """Capture and test OCR."""
        self.result_text.clear()
        self.result_text.append("캡처 중...")
        
        image = self.capture_test_area()
        if image is None:
            return
        
        # Test OCR
        self.result_text.append("\nOCR 테스트 중...")
        
        try:
            result = self.ocr_service.perform_ocr_with_recovery(image, "coordinate_test")
            
            if result.is_valid():
                self.result_text.append(f"\n✅ 텍스트 감지됨:")
                self.result_text.append(f"텍스트: '{result.text}'")
                self.result_text.append(f"신뢰도: {result.confidence:.2f}")
                
                # Check if Korean
                if any(ord(c) >= 0xAC00 and ord(c) <= 0xD7A3 for c in result.text):
                    self.result_text.append("✅ 한글 텍스트 확인됨!")
                else:
                    self.result_text.append("⚠️ 한글이 아닌 텍스트")
                
                # Check trigger patterns
                is_trigger = self.ocr_service.check_trigger_patterns(result)
                if is_trigger:
                    self.result_text.append("🎯 트리거 패턴 매칭됨!")
                
            else:
                self.result_text.append("\n⚪ 텍스트를 찾을 수 없습니다.")
                self.result_text.append("카카오톡 채팅 메시지가 보이는 위치로 조정해주세요.")
                
                # Show debug info if available
                if 'all_results' in result.debug_info and result.debug_info['all_results']:
                    self.result_text.append("\n디버그 정보:")
                    for r in result.debug_info['all_results']:
                        self.result_text.append(f"- 전략 {r['strategy']}: '{r['text']}' ({r['confidence']:.2f})")
                        
        except Exception as e:
            self.result_text.append(f"\n❌ OCR 오류: {e}")
    
    def auto_scan_screen(self) -> None:
        """Auto scan screen for Korean text."""
        self.result_text.clear()
        self.result_text.append("🔍 전체 화면에서 한글 텍스트 검색 중...")
        self.result_text.append("(시간이 걸릴 수 있습니다...)\n")
        
        QApplication.processEvents()
        
        try:
            with mss.mss() as sct:
                # Get primary monitor
                monitor = sct.monitors[1]
                
                # Scan in grid pattern
                step_x = 200
                step_y = 100
                found_korean: list[dict[str, str | int | float]] = []
                
                for y in range(monitor['top'], monitor['height'] - 100, step_y):
                    for x in range(monitor['left'], monitor['width'] - 300, step_x):
                        # Test area
                        area = {
                            'left': x,
                            'top': y,
                            'width': 300,
                            'height': 100
                        }
                        
                        try:
                            screenshot = sct.grab(area)
                            image = np.array(screenshot)
                            
                            if image.shape[2] == 4:
                                image = image[:, :, :3]
                            
                            # Quick OCR test
                            result = self.ocr_service.perform_ocr_with_recovery(image, "auto_scan")
                            
                            if result.is_valid():
                                # Check for Korean
                                if any(ord(c) >= 0xAC00 and ord(c) <= 0xD7A3 for c in result.text):
                                    found_korean.append({
                                        'x': x,
                                        'y': y,
                                        'text': result.text,
                                        'confidence': result.confidence
                                    })
                                    
                                    self.result_text.append(
                                        f"✅ 한글 발견! 위치: ({x}, {y}) - '{result.text[:20]}...'"
                                    )
                                    
                                    # Update preview with first found
                                    if len(found_korean) == 1:
                                        self.x_spin.setValue(x)
                                        self.y_spin.setValue(y)
                                        self.capture_test_area()
                                    
                                    QApplication.processEvents()
                                    
                        except:
                            continue
                
                # Summary
                self.result_text.append(f"\n스캔 완료! 한글 텍스트 {len(found_korean)}곳 발견")
                
                if found_korean:
                    self.result_text.append("\n발견된 위치:")
                    for item in found_korean[:5]:  # Show first 5
                        self.result_text.append(
                            f"- ({item['x']}, {item['y']}): '{item['text'][:30]}...'"
                        )
                else:
                    self.result_text.append("\n⚠️ 한글 텍스트를 찾을 수 없습니다.")
                    self.result_text.append("카카오톡이 실행되어 있고 채팅방이 열려있는지 확인하세요.")
                    
        except Exception as e:
            self.result_text.append(f"\n❌ 스캔 오류: {e}")
    
    def save_coordinates(self) -> None:
        """Save adjusted coordinates."""
        # Create configuration
        adjusted_config = {
            'adjusted_coordinates': {
                'test_x': self.test_x,
                'test_y': self.test_y,
                'test_width': self.test_width,
                'test_height': self.test_height,
                'timestamp': str(np.datetime64('now'))
            },
            'notes': '좌표 조정 도구로 설정됨'
        }
        
        # Save to file
        try:
            with open('adjusted_coordinates.json', 'w', encoding='utf-8') as f:
                json.dump(adjusted_config, f, indent=2, ensure_ascii=False)
            
            QMessageBox.information(
                self, 
                "저장 완료", 
                f"조정된 좌표가 저장되었습니다.\n\n"
                f"X: {self.test_x}, Y: {self.test_y}\n"
                f"크기: {self.test_width}x{self.test_height}"
            )
            
            self.result_text.append("\n💾 좌표가 'adjusted_coordinates.json'에 저장되었습니다.")
            
        except Exception as e:
            QMessageBox.critical(self, "저장 오류", f"저장 중 오류 발생: {e}")


def main() -> None:
    """Main function."""
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    
    window = CoordinateAdjustmentTool()
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()