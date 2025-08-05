#!/usr/bin/env python3
"""
카카오톡 OCR 챗봇 시스템 - 데모 버전
numpy DLL 문제 우회 버전
"""
import sys
import os
from pathlib import Path

def setup_demo_environment():
    """데모 환경 설정"""
    print("데모 환경 설정 중...")
    
    # 프로젝트 루트 설정
    project_root = Path(__file__).parent
    src_path = project_root / "src"
    
    # Python path 설정
    if str(src_path) not in sys.path:
        sys.path.insert(0, str(src_path))
    
    # 환경변수 설정
    os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'
    os.environ['CUDA_VISIBLE_DEVICES'] = '-1'
    os.environ['OMP_NUM_THREADS'] = '1'
    
    # import 패치 적용
    try:
        from src.utils.import_patcher import patch_imports
        patch_imports()
        print("  [OK] import 패치 적용됨")
    except ImportError:
        print("  [SKIP] import 패치 모듈 없음")
    
    print("  [OK] 데모 환경 설정 완료")

def test_core_modules():
    """핵심 모듈 테스트"""
    print("\n핵심 모듈 테스트 중...")
    
    success_count = 0
    total_tests = 0
    
    # numpy 테스트
    total_tests += 1
    try:
        import numpy as np
        print(f"  [OK] numpy: {np.__version__}")
        success_count += 1
    except Exception as e:
        print(f"  [FAIL] numpy: {e}")
    
    # PyQt5 테스트
    total_tests += 1
    try:
        from PyQt5.QtWidgets import QApplication
        print("  [OK] PyQt5: 사용 가능")
        success_count += 1
    except Exception as e:
        print(f"  [SKIP] PyQt5: {e}")
    
    # PIL 테스트
    total_tests += 1
    try:
        from PIL import Image
        print("  [OK] PIL: 사용 가능")
        success_count += 1
    except Exception as e:
        print(f"  [FAIL] PIL: {e}")
    
    # 프로젝트 모듈 테스트
    project_modules = [
        ("core.config_manager", "ConfigManager"),
        ("core.grid_manager", "GridCell"),
        ("core.simple_cache", "SimpleLRUCache"),
    ]
    
    for module_name, class_name in project_modules:
        total_tests += 1
        try:
            module = __import__(module_name, fromlist=[class_name])
            cls = getattr(module, class_name)
            print(f"  [OK] {module_name}.{class_name}")
            success_count += 1
        except Exception as e:
            print(f"  [FAIL] {module_name}.{class_name}: {e}")
    
    print(f"\n모듈 테스트 결과: {success_count}/{total_tests} 성공")
    return success_count >= total_tests * 0.6  # 60% 이상 성공

def run_gui_demo():
    """GUI 데모 실행"""
    print("\nGUI 데모 실행 시도...")
    
    try:
        # 간단한 GUI 데모
        from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel, QPushButton
        from PyQt5.QtCore import Qt
        
        app = QApplication(sys.argv)
        
        # 메인 윈도우
        window = QWidget()
        window.setWindowTitle("카카오톡 OCR 챗봇 - 데모 버전")
        window.setGeometry(100, 100, 400, 300)
        
        layout = QVBoxLayout()
        
        # 라벨들
        title_label = QLabel("카카오톡 OCR 챗봇 시스템")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("font-size: 16px; font-weight: bold; margin: 10px;")
        
        status_label = QLabel("데모 버전 - numpy DLL 문제 우회")
        status_label.setAlignment(Qt.AlignCenter)
        status_label.setStyleSheet("color: red; margin: 5px;")
        
        info_label = QLabel("이 버전은 기술 데모 목적으로만 사용하세요.\nOCR 기능은 제한적입니다.")
        info_label.setAlignment(Qt.AlignCenter)
        info_label.setStyleSheet("margin: 10px;")
        
        # 버튼
        close_button = QPushButton("데모 종료")
        close_button.clicked.connect(app.quit)
        close_button.setStyleSheet("margin: 10px; padding: 5px;")
        
        # 레이아웃에 추가
        layout.addWidget(title_label)
        layout.addWidget(status_label)
        layout.addWidget(info_label)
        layout.addWidget(close_button)
        
        window.setLayout(layout)
        window.show()
        
        print("  [OK] GUI 데모 실행됨")
        print("  [INFO] 창을 닫으면 프로그램이 종료됩니다.")
        
        return app.exec_()
        
    except Exception as e:
        print(f"  [FAIL] GUI 데모 실행 실패: {e}")
        return False

def run_console_demo():
    """콘솔 데모 실행"""
    print("\n콘솔 데모 모드")
    print("=" * 40)
    print("카카오톡 OCR 챗봇 시스템 (데모 버전)")
    print("numpy DLL 문제 우회 버전")
    print("=" * 40)
    
    try:
        # 설정 관리자 테스트
        from core.config_manager import ConfigManager
        config = ConfigManager()
        print(f"설정 로드됨: grid {config.grid_rows}x{config.grid_cols}")
        
        # 그리드 셀 테스트
        from core.grid_manager import GridCell, CellStatus
        cell = GridCell(
            id="demo_cell",
            bounds=(0, 0, 100, 100),
            ocr_area=(10, 10, 80, 80)
        )
        print(f"그리드 셀 생성됨: {cell.id}, 상태: {cell.status}")
        
        # 캐시 테스트
        from core.simple_cache import SimpleLRUCache
        cache = SimpleLRUCache(max_size=10)
        cache.put("test", "value")
        print(f"캐시 테스트: {cache.get('test')}")
        
        print("\n[SUCCESS] 콘솔 데모 실행 완료")
        print("핵심 모듈들이 정상적으로 작동합니다.")
        
        return True
        
    except Exception as e:
        print(f"[FAIL] 콘솔 데모 실행 실패: {e}")
        return False

def main():
    """메인 실행 함수"""
    print("카카오톡 OCR 챗봇 시스템 - 데모 버전")
    print("Python 3.13 호환성 문제 우회 버전")
    print("기술 데모 전용 - 실제 서비스 사용 금지")
    print()
    
    # 1. 환경 설정
    setup_demo_environment()
    
    # 2. 모듈 테스트
    if not test_core_modules():
        print("\n[ERROR] 필수 모듈 로드 실패")
        print("다음을 시도해보세요:")
        print("  1. python fix_numpy_auto.py")
        print("  2. pip install PyQt5 Pillow mss psutil")
        return False
    
    # 3. 실행 모드 선택
    try:
        # GUI 실행 시도
        print("\nGUI 모드로 실행을 시도합니다...")
        if run_gui_demo():
            return True
    except Exception as e:
        print(f"GUI 모드 실패: {e}")
    
    # GUI 실패 시 콘솔 모드
    print("\nGUI 실행 실패, 콘솔 모드로 전환...")
    return run_console_demo()

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n사용자에 의해 중단되었습니다.")
        sys.exit(0)
    except Exception as e:
        print(f"\n예상치 못한 오류: {e}")
        sys.exit(1)
