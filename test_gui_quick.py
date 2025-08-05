#!/usr/bin/env python3
"""
Quick GUI test script
"""
import sys
import os
import io
from pathlib import Path

# UTF-8 encoding
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# Add src to path
script_dir = Path(__file__).parent.absolute()
src_path = script_dir / "src"
if src_path.exists():
    sys.path.insert(0, str(src_path))

# Suppress PaddleOCR logs
os.environ['PPOCR_LOG_LEVEL'] = 'ERROR'
os.environ['PADDLEX_LOG_LEVEL'] = 'ERROR'
os.environ['PADDLE_LOG_LEVEL'] = 'ERROR'
os.environ['GLOG_minloglevel'] = '3'

import warnings
warnings.filterwarnings('ignore')

def test_gui():
    """Test GUI loading"""
    print("=" * 50)
    print("GUI 테스트")
    print("=" * 50)
    
    try:
        # Import GUI modules
        from PyQt5.QtWidgets import QApplication
        from gui.chatbot_gui import UnifiedChatbotGUI
        print("✅ GUI 모듈 임포트 성공")
        
        # Create QApplication
        app = QApplication(sys.argv)
        print("✅ QApplication 생성 성공")
        
        # Create GUI window
        window = UnifiedChatbotGUI()
        print("✅ GUI 윈도우 생성 성공")
        
        # Show window
        window.show()
        print("✅ GUI 표시 성공")
        print("\n📌 GUI가 열렸습니다!")
        print("📌 '모니터링 시작' 버튼을 클릭하여 모니터링을 시작하세요")
        print("📌 '오버레이 표시' 버튼을 클릭하여 감지 영역을 확인하세요")
        
        # Run event loop
        sys.exit(app.exec_())
        
    except Exception as e:
        print(f"❌ 오류: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_gui()