#!/usr/bin/env python3
"""
KakaoTalk OCR Chatbot System - Main Entry Point
Reorganized project structure
Python 3.11+ compatible
"""
from __future__ import annotations

import sys
import os
import io
from pathlib import Path
from typing import NoReturn

# Set environment variables before any imports
os.environ['PPOCR_LOG_LEVEL'] = 'ERROR'
os.environ['PADDLEX_LOG_LEVEL'] = 'ERROR'
os.environ['PADDLE_LOG_LEVEL'] = 'ERROR'
os.environ['PADDLEOCR_SHOW_PROGRESS'] = '0'
os.environ['PADDLEX_SHOW_PROGRESS'] = '0'
os.environ['TQDM_DISABLE'] = '1'
os.environ['GLOG_v'] = '0'
os.environ['GLOG_logtostderr'] = '0'
os.environ['GLOG_minloglevel'] = '3'
os.environ['FLAGS_logtostderr'] = '0'

# Set UTF-8 encoding for stdout
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Disable PaddleOCR logging and warnings
import logging
import warnings

# Suppress all warnings (강화)
warnings.filterwarnings('ignore')
warnings.filterwarnings('ignore', category=UserWarning)
warnings.filterwarnings('ignore', category=FutureWarning)
warnings.filterwarnings('ignore', category=DeprecationWarning)

# Disable all paddle-related logging (강화)
logging.getLogger('ppocr').setLevel(logging.CRITICAL)
logging.getLogger('paddleocr').setLevel(logging.CRITICAL)
logging.getLogger('paddle').setLevel(logging.CRITICAL)
logging.getLogger('paddlex').setLevel(logging.CRITICAL)
logging.getLogger('ppocr.PaddleOCR').setLevel(logging.CRITICAL)

# Disable root logger for paddle
logging.getLogger().setLevel(logging.ERROR)

# 추가 로깅 차단

# Windows DPI 및 마우스 제어 설정
if sys.platform == 'win32':
    import ctypes
    try:
        # DPI Aware 설정 (고해상도 디스플레이 지원)
        try:
            ctypes.windll.shcore.SetProcessDpiAwareness(2)  # PROCESS_PER_MONITOR_DPI_AWARE
        except:
            ctypes.windll.user32.SetProcessDPIAware()
    except:
        pass
    
    # PyAutoGUI 마우스 제어 문제 해결
    try:
        import pyautogui
        pyautogui.FAILSAFE = False
        pyautogui.PAUSE = 0
        
        # Windows에서 ctypes 직접 사용하도록 패치
        import pyautogui._pyautogui_win as platformModule
        def fixed_moveTo(x, y):
            ctypes.windll.user32.SetCursorPos(int(x), int(y))
        platformModule._moveTo = fixed_moveTo
    except:
        pass
for logger_name in ['ppocr', 'paddleocr', 'paddle', 'paddlex']:
    logger = logging.getLogger(logger_name)
    logger.disabled = True
    logger.propagate = False

# Suppress Windows command output
if sys.platform == "win32":
    import subprocess
    # STARTUPINFO 클래스를 인스턴스로 덮어쓰지 않도록 수정
    # 이는 나중에 subprocess 모듈이 사용될 때 문제를 일으킴

def setup_environment():
    """Setup the Python environment and paths."""
    # Get the directory where this script is located
    script_dir = Path(__file__).parent.absolute()
    
    # Add src directory to Python path
    src_path = script_dir / "src"
    if src_path.exists() and str(src_path) not in sys.path:
        sys.path.insert(0, str(src_path))
        print(f"Python path: Added {src_path}")
    
    # Set Qt plugin path before importing PyQt5 (Windows only)
    if sys.platform == "win32":
        # Find virtual environment path
        venv_path = Path(sys.executable).parent.parent
        qt_plugin_path = venv_path / "Lib" / "site-packages" / "PyQt5" / "Qt5" / "plugins"
        
        if qt_plugin_path.exists():
            os.environ['QT_PLUGIN_PATH'] = str(qt_plugin_path)
            os.environ['QT_QPA_PLATFORM_PLUGIN_PATH'] = str(qt_plugin_path / "platforms")
            print(f"Qt plugin path set: {qt_plugin_path}")
        else:
            print("Warning: Qt plugin path not found, GUI may not work properly")
    
    # Add src to Python path
    src_path = script_dir / "src"
    if src_path.exists():
        sys.path.insert(0, str(src_path))
    else:
        print("Error: src/ directory not found!")
        print(f"Expected path: {src_path}")
        sys.exit(1)

def check_dependencies():
    """Check if required dependencies are available."""
    required_modules = [
        'numpy',
        'cv2',
        'PyQt5',
        'pyautogui',
        'mss'
    ]
    
    missing_modules = []
    for module in required_modules:
        try:
            __import__(module)
        except ImportError:
            missing_modules.append(module)
    
    if missing_modules:
        print("Error: 다음 모듈들이 설치되지 않았습니다:")
        for module in missing_modules:
            print(f"  - {module}")
        print("\n해결방법:")
        print("1. install.bat을 실행하거나")
        print("2. pip install -r requirements.txt를 실행하세요.")
        sys.exit(1)

def run_application() -> NoReturn:
    """Run the main application with proper initialization."""
    print("=" * 60)
    print("카카오톡 OCR 챗봇 시스템")
    print("=" * 60)
    print("프로젝트가 새로운 구조로 정리되었습니다.")
    print("src/ - 소스 코드")
    print("tools/ - 도구 및 유틸리티")
    print("tests/ - 테스트 파일")
    print("docs/ - 문서")
    print("=" * 60)
    
    try:
        # Import and run the GUI application
        from PyQt5.QtWidgets import QApplication
        from gui.chatbot_gui import UnifiedChatbotGUI
        
        print("✅ GUI 모듈 로드 완료")
        
        # QApplication 생성 및 실행
        app = QApplication(sys.argv)
        app.setApplicationName("카카오톡 OCR 챗봇")
        
        # 메인 윈도우 생성 및 표시
        window = UnifiedChatbotGUI()
        window.show()
        
        print("✅ GUI 시작됨 - 모니터링 시작 버튼을 클릭하세요")
        print("📌 오버레이 표시 버튼을 클릭하면 화면에 그리드가 표시됩니다")
        
        # 이벤트 루프 실행
        sys.exit(app.exec_())
            
    except ImportError as e:
        print(f"Error: 모듈을 불러올 수 없습니다: {e}")
        print("필요한 패키지가 설치되었는지 확인하세요.")
        sys.exit(1)
    except Exception as e:
        print(f"Error: 애플리케이션 실행 중 오류가 발생했습니다: {e}")
        sys.exit(1)


if __name__ == "__main__":
    setup_environment()
    check_dependencies()
    run_application()