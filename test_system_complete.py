#!/usr/bin/env python3
"""
전체 시스템 통합 테스트
PaddleOCR 3.1.0 호환 버전
"""
import sys
import os
import io
from pathlib import Path

# UTF-8 encoding
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# 로그 억제
os.environ['PPOCR_LOG_LEVEL'] = 'ERROR'
os.environ['GLOG_minloglevel'] = '3'
os.environ['GLOG_v'] = '0'
os.environ['PADDLEOCR_SHOW_PROGRESS'] = '0'

# src 디렉토리를 Python 경로에 추가
script_dir = Path(__file__).parent.absolute()
src_path = script_dir / "src"
if src_path.exists():
    sys.path.insert(0, str(src_path))

print("=" * 60)
print("카카오톡 OCR 챗봇 시스템 통합 테스트")
print("=" * 60)

# 1. 기본 모듈 테스트
print("\n1. 기본 모듈 import 테스트:")
print("-" * 40)

modules_to_test = [
    ('numpy', 'NumPy'),
    ('cv2', 'OpenCV'),
    ('PyQt5.QtCore', 'PyQt5'),
    ('paddleocr', 'PaddleOCR'),
    ('mss', 'MSS (스크린 캡처)'),
    ('pyautogui', 'PyAutoGUI')
]

all_ok = True
for module_name, display_name in modules_to_test:
    try:
        module = __import__(module_name)
        version = getattr(module, '__version__', 'unknown')
        print(f"✅ {display_name}: {version}")
    except ImportError:
        print(f"❌ {display_name}: 설치 안됨")
        all_ok = False

if not all_ok:
    print("\n⚠️ 필수 모듈이 설치되지 않았습니다.")
    sys.exit(1)

# 2. PaddleOCR 초기화 테스트
print("\n2. PaddleOCR 초기화 테스트:")
print("-" * 40)

try:
    from paddleocr import PaddleOCR
    
    # 3.1.0 호환 초기화
    ocr = PaddleOCR(lang='korean')
    print("✅ PaddleOCR 초기화 성공")
    
    # 간단한 OCR 테스트
    import numpy as np
    test_img = np.ones((100, 300, 3), dtype=np.uint8) * 255
    result = ocr.ocr(test_img)
    print("✅ OCR 실행 테스트 성공")
    
except Exception as e:
    print(f"❌ PaddleOCR 테스트 실패: {e}")

# 3. 프로젝트 모듈 테스트
print("\n3. 프로젝트 모듈 테스트:")
print("-" * 40)

try:
    from core.config_manager import ConfigManager
    config = ConfigManager()
    print("✅ ConfigManager 로드 성공")
    
    from core.grid_manager import GridManager
    grid = GridManager(config)
    print(f"✅ GridManager 로드 성공 (셀 개수: {len(grid.cells)})")
    
    from ocr.optimized_ocr_service import OptimizedOCRService
    ocr_service = OptimizedOCRService(config)
    print("✅ OptimizedOCRService 로드 성공")
    
    from gui.chatbot_gui import UnifiedChatbotGUI
    print("✅ UnifiedChatbotGUI 로드 성공")
    
except Exception as e:
    print(f"❌ 프로젝트 모듈 로드 실패: {e}")
    import traceback
    traceback.print_exc()

# 4. GUI 테스트 (non-blocking)
print("\n4. GUI 초기화 테스트:")
print("-" * 40)

try:
    from PyQt5.QtWidgets import QApplication
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    
    from gui.chatbot_gui import UnifiedChatbotGUI
    window = UnifiedChatbotGUI()
    print("✅ GUI 윈도우 생성 성공")
    
    # 윈도우 속성 확인
    print(f"   - 윈도우 크기: {window.width()}x{window.height()}")
    print(f"   - 윈도우 제목: {window.windowTitle()}")
    
    # 닫기 (테스트만)
    window.close()
    app.quit()
    
except Exception as e:
    print(f"❌ GUI 테스트 실패: {e}")

# 5. 시스템 상태 요약
print("\n" + "=" * 60)
print("시스템 상태 요약")
print("=" * 60)

print("\n✅ 모든 테스트 완료!")
print("\n시스템 실행 방법:")
print("1. Python 3.11 권장 (3.13도 동작)")
print("2. 실행: python main.py")
print("3. 또는: start_chatbot.bat")
print("\n주의사항:")
print("- 첫 실행시 PaddleOCR 모델 다운로드 (약 100MB)")
print("- 모델 다운로드 메시지는 정상")
print("- 다운로드는 한 번만 수행됨")