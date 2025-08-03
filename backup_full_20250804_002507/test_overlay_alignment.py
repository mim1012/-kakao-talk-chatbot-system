#!/usr/bin/env python3
"""오버레이 정렬 테스트 스크립트"""
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from PyQt5.QtWidgets import QApplication
from gui.optimized_chatbot_system import OptimizedOverlayWidget
from core.service_container import ServiceContainer

def test_overlay():
    """오버레이 정렬 테스트"""
    print("오버레이 정렬 테스트 시작...")
    
    app = QApplication(sys.argv)
    
    # 서비스 컨테이너 생성
    services = ServiceContainer()
    
    # 첫 번째 셀 정보 출력
    if services.grid_manager.cells:
        cell = services.grid_manager.cells[0]
        print(f"\n첫 번째 셀 정보:")
        print(f"  - ID: {cell.id}")
        print(f"  - 셀 영역: x={cell.bounds[0]}, y={cell.bounds[1]}, w={cell.bounds[2]}, h={cell.bounds[3]}")
        print(f"  - OCR 영역: x={cell.ocr_area[0]}, y={cell.ocr_area[1]}, w={cell.ocr_area[2]}, h={cell.ocr_area[3]}")
        print(f"  - OCR Y 위치: 셀 하단({cell.bounds[1] + cell.bounds[3]}) - OCR 높이({cell.ocr_area[3]}) = {cell.ocr_area[1]}")
        print(f"  - 여백: {(cell.bounds[1] + cell.bounds[3]) - (cell.ocr_area[1] + cell.ocr_area[3])}픽셀")
    
    # 오버레이 표시
    overlay = OptimizedOverlayWidget(services)
    overlay.show()
    
    print("\n오버레이가 표시되었습니다.")
    print("OCR 영역(파란색)이 각 셀의 하단에 정확히 위치하는지 확인하세요.")
    print("종료하려면 Ctrl+C를 누르세요.")
    
    sys.exit(app.exec_())

if __name__ == "__main__":
    test_overlay()