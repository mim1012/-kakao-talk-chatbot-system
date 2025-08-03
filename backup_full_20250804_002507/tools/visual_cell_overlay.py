"""
Visual Cell Overlay Tool
Shows transparent overlay with all cell positions for coordinate verification
"""
from __future__ import annotations

import sys
import os
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton, QHBoxLayout, QLabel
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QPainter, QPen, QBrush, QColor, QFont
from screeninfo import get_monitors

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(project_root, 'src'))

from core.config_manager import ConfigManager
from core.grid_manager import GridManager, CellStatus


class CellOverlayWidget(QWidget):
    """Transparent overlay showing all cell positions."""
    
    def __init__(self, monitor_index: int = 0) -> None:
        super().__init__()
        self.monitor_index = monitor_index
        self.config = ConfigManager()
        self.grid_manager = GridManager(self.config)
        
        # Filter cells for this monitor
        self.monitor_cells = [
            cell for cell in self.grid_manager.cells 
            if cell.monitor_index == monitor_index
        ]
        
        self.show_full_bounds: bool = True
        self.show_ocr_areas: bool = True
        self.show_labels: bool = True
        self.highlight_target: bool = True
        
        self.initUI()
        
    def initUI(self) -> None:
        """Initialize the overlay UI."""
        # Get monitor info
        monitors = get_monitors()
        if self.monitor_index < len(monitors):
            monitor = monitors[self.monitor_index]
            self.setGeometry(monitor.x, monitor.y, monitor.width, monitor.height)
        
        # Window settings for overlay
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)
        
        # Make click-through
        self.setWindowOpacity(0.7)
        
    def paintEvent(self, event) -> None:
        """Paint the overlay."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Window position
        overlay_x = self.geometry().x()
        overlay_y = self.geometry().y()
        
        for cell in self.monitor_cells:
            # Cell full bounds
            if self.show_full_bounds:
                cell_x, cell_y, cell_w, cell_h = cell.bounds
                rel_x = cell_x - overlay_x
                rel_y = cell_y - overlay_y
                
                # Color based on cell ID
                if self.highlight_target and cell.id == "M0_R0_C1":
                    color = QColor(255, 0, 0, 100)  # Red for target
                    pen_color = QColor(255, 0, 0, 200)
                    pen_width = 3
                else:
                    color = QColor(0, 255, 0, 50)  # Green for others
                    pen_color = QColor(0, 255, 0, 150)
                    pen_width = 2
                
                painter.setPen(QPen(pen_color, pen_width))
                painter.fillRect(rel_x, rel_y, cell_w, cell_h, QBrush(color))
                painter.drawRect(rel_x, rel_y, cell_w, cell_h)
            
            # OCR area
            if self.show_ocr_areas:
                ocr_x, ocr_y, ocr_w, ocr_h = cell.ocr_area
                rel_ocr_x = ocr_x - overlay_x
                rel_ocr_y = ocr_y - overlay_y
                
                # OCR area color
                if self.highlight_target and cell.id == "M0_R0_C1":
                    ocr_color = QColor(255, 255, 0, 80)  # Yellow for target
                    ocr_pen = QPen(QColor(255, 255, 0, 200), 2)
                else:
                    ocr_color = QColor(0, 0, 255, 60)  # Blue for others
                    ocr_pen = QPen(QColor(0, 0, 255, 180), 2)
                
                painter.setPen(ocr_pen)
                painter.fillRect(rel_ocr_x, rel_ocr_y, ocr_w, ocr_h, QBrush(ocr_color))
                painter.drawRect(rel_ocr_x, rel_ocr_y, ocr_w, ocr_h)
            
            # Labels
            if self.show_labels:
                cell_x, cell_y, cell_w, cell_h = cell.bounds
                rel_x = cell_x - overlay_x
                rel_y = cell_y - overlay_y
                
                # Font settings
                font = QFont("Arial", 10, QFont.Weight.Bold)
                painter.setFont(font)
                
                # Background for text
                text = cell.id
                if self.highlight_target and cell.id == "M0_R0_C1":
                    text = f"⭐ {text} ⭐"
                
                painter.setPen(QPen(QColor(255, 255, 255), 1))
                painter.fillRect(rel_x, rel_y - 20, len(text) * 8, 20, 
                               QBrush(QColor(0, 0, 0, 180)))
                painter.drawText(rel_x + 2, rel_y - 5, text)


class OverlayControlWindow(QWidget):
    """Control window for the overlay."""
    
    def __init__(self) -> None:
        super().__init__()
        self.overlays: list[CellOverlayWidget] = []
        self.initUI()
        self.create_overlays()
        
    def initUI(self) -> None:
        """Initialize control window UI."""
        self.setWindowTitle("셀 위치 오버레이 컨트롤")
        self.setGeometry(100, 100, 400, 200)
        
        layout = QVBoxLayout()
        
        # Title
        title = QLabel("셀 위치 시각화 도구")
        title.setStyleSheet("font-size: 16px; font-weight: bold; padding: 10px;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
        # Info
        info = QLabel(
            "• 녹색 영역: 전체 셀 영역\n"
            "• 파란색 영역: OCR 스캔 영역\n"
            "• 빨강/노랑: 목표 셀 (M0_R0_C1)\n"
            "• ESC: 오버레이 숨기기/표시"
        )
        info.setStyleSheet("padding: 10px; background-color: #f0f0f0;")
        layout.addWidget(info)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.toggle_btn = QPushButton("오버레이 숨기기")
        self.toggle_btn.clicked.connect(self.toggle_overlays)
        button_layout.addWidget(self.toggle_btn)
        
        refresh_btn = QPushButton("새로고침")
        refresh_btn.clicked.connect(self.refresh_overlays)
        button_layout.addWidget(refresh_btn)
        
        close_btn = QPushButton("종료")
        close_btn.clicked.connect(self.close)
        close_btn.setStyleSheet("background-color: #f44336; color: white;")
        button_layout.addWidget(close_btn)
        
        layout.addLayout(button_layout)
        
        # Monitor info
        monitors = get_monitors()
        monitor_info = QLabel(f"감지된 모니터: {len(monitors)}개")
        monitor_info.setStyleSheet("padding: 5px; color: #666;")
        layout.addWidget(monitor_info)
        
        self.setLayout(layout)
        
        # Always on top
        self.setWindowFlags(self.windowFlags() | Qt.WindowType.WindowStaysOnTopHint)
        
    def create_overlays(self) -> None:
        """Create overlay for each monitor."""
        monitors = get_monitors()
        
        for i in range(len(monitors)):
            overlay = CellOverlayWidget(i)
            overlay.show()
            self.overlays.append(overlay)
            
    def toggle_overlays(self) -> None:
        """Toggle overlay visibility."""
        if self.overlays and self.overlays[0].isVisible():
            for overlay in self.overlays:
                overlay.hide()
            self.toggle_btn.setText("오버레이 표시")
        else:
            for overlay in self.overlays:
                overlay.show()
            self.toggle_btn.setText("오버레이 숨기기")
            
    def refresh_overlays(self) -> None:
        """Refresh overlays."""
        # Close existing
        for overlay in self.overlays:
            overlay.close()
        self.overlays.clear()
        
        # Create new
        self.create_overlays()
        
    def keyPressEvent(self, event) -> None:
        """Handle key press."""
        if event.key() == Qt.Key.Key_Escape:
            self.toggle_overlays()
            
    def closeEvent(self, event) -> None:
        """Handle close event."""
        for overlay in self.overlays:
            overlay.close()
        event.accept()


def main() -> None:
    """Main function."""
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    
    # Create control window
    control = OverlayControlWindow()
    control.show()
    
    print("=" * 60)
    print("셀 위치 오버레이 실행됨")
    print("=" * 60)
    print("화면에 표시된 영역을 확인하세요:")
    print("- 녹색: 전체 셀 영역")
    print("- 파란색: OCR 스캔 영역")
    print("- 빨강/노랑: 목표 셀 (M0_R0_C1)")
    print("\n카카오톡 창이 이 영역들과 일치하는지 확인하세요!")
    print("=" * 60)
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()