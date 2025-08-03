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

# Set UTF-8 encoding for stdout
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Disable PaddleOCR logging and warnings
import logging
import warnings

# Suppress all warnings
warnings.filterwarnings('ignore')

# Disable all paddle-related logging
logging.getLogger('ppocr').setLevel(logging.ERROR)
logging.getLogger('paddleocr').setLevel(logging.ERROR)
logging.getLogger('paddle').setLevel(logging.ERROR)
logging.getLogger('paddlex').setLevel(logging.ERROR)

# Disable root logger for paddle
logging.getLogger().setLevel(logging.WARNING)

# Suppress Windows command output
if sys.platform == "win32":
    import subprocess
    subprocess.STARTUPINFO = subprocess.STARTUPINFO()
    subprocess.STARTUPINFO.dwFlags |= subprocess.STARTF_USESHOWWINDOW

def setup_environment():
    """Setup the Python environment and paths."""
    # Get the directory where this script is located
    script_dir = Path(__file__).parent.absolute()
    
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
        # Import the main application
        from gui.optimized_chatbot_system import main
        # Run the main application
        main()
    except ImportError as e:
        print(f"Error: 모듈을 불러올 수 없습니다: {e}")
        print("src/gui/optimized_chatbot_system.py 파일이 있는지 확인하세요.")
        sys.exit(1)
    except Exception as e:
        print(f"Error: 애플리케이션 실행 중 오류가 발생했습니다: {e}")
        sys.exit(1)


if __name__ == "__main__":
    setup_environment()
    check_dependencies()
    run_application()