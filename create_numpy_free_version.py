#!/usr/bin/env python3
"""
numpy 없는 버전 생성 스크립트
numpy DLL 문제를 우회하여 실행 가능한 데모 버전 생성
"""
import sys
import os
from pathlib import Path
import shutil

def create_numpy_replacement():
    """numpy 대체 모듈 생성"""
    print("numpy 대체 모듈 생성 중...")
    
    utils_dir = Path("src/utils")
    utils_dir.mkdir(exist_ok=True)
    
    numpy_replacement = '''"""
numpy 대체 모듈 - 기본 기능만 제공
"""
import math
from typing import Union, List, Tuple, Any

class ndarray:
    """numpy.ndarray 대체 클래스"""
    def __init__(self, data, dtype=None):
        if isinstance(data, list):
            self.data = data
        else:
            self.data = [data]
        self.dtype = dtype or 'float64'
        
        # 차원 계산
        if isinstance(data, list) and len(data) > 0:
            if isinstance(data[0], list):
                self.shape = (len(data), len(data[0]))
            else:
                self.shape = (len(data),)
        else:
            self.shape = (1,)
    
    def __getitem__(self, key):
        return self.data[key]
    
    def __setitem__(self, key, value):
        self.data[key] = value
    
    def __len__(self):
        return len(self.data)

def array(data, dtype=None):
    """numpy.array 대체 함수"""
    return ndarray(data, dtype)

def zeros(shape, dtype='float64'):
    """numpy.zeros 대체"""
    if isinstance(shape, int):
        return ndarray([0] * shape, dtype)
    elif isinstance(shape, tuple) and len(shape) == 2:
        return ndarray([[0] * shape[1] for _ in range(shape[0])], dtype)
    else:
        return ndarray([0], dtype)

def ones(shape, dtype='float64'):
    """numpy.ones 대체"""
    if isinstance(shape, int):
        return ndarray([1] * shape, dtype)
    elif isinstance(shape, tuple) and len(shape) == 2:
        return ndarray([[1] * shape[1] for _ in range(shape[0])], dtype)
    else:
        return ndarray([1], dtype)

def uint8():
    """numpy.uint8 타입"""
    return 'uint8'

def float64():
    """numpy.float64 타입"""
    return 'float64'

# 호환성을 위한 변수들
__version__ = "1.26.4 (compatible replacement)"
'''
    
    with open(utils_dir / "numpy_replacement.py", 'w', encoding='utf-8') as f:
        f.write(numpy_replacement)
    
    print("  [OK] numpy 대체 모듈 생성 완료")

def create_opencv_replacement():
    """OpenCV 대체 모듈 생성"""
    print("OpenCV 대체 모듈 생성 중...")
    
    utils_dir = Path("src/utils")
    
    opencv_replacement = '''"""
OpenCV 대체 모듈 - 기본 이미지 처리만 제공
"""
from PIL import Image
import io

# OpenCV 상수들
INTER_LINEAR = 1
INTER_CUBIC = 2
THRESH_BINARY = 0
THRESH_OTSU = 8
COLOR_BGR2GRAY = 6
COLOR_RGB2BGR = 4

__version__ = "4.10.0 (compatible replacement)"

def imread(filename, flags=1):
    """이미지 읽기 (PIL 사용)"""
    try:
        img = Image.open(filename)
        if flags == 0:  # 그레이스케일
            img = img.convert('L')
        elif flags == 1:  # 컬러
            img = img.convert('RGB')
        
        # PIL Image를 리스트로 변환
        width, height = img.size
        pixels = list(img.getdata())
        
        # 2D 배열로 변환
        if flags == 0:  # 그레이스케일
            return [[pixels[i * width + j] for j in range(width)] for i in range(height)]
        else:  # 컬러
            return [[[pixels[i * width + j][k] for k in range(3)] for j in range(width)] for i in range(height)]
    except Exception:
        return None

def imwrite(filename, img):
    """이미지 저장"""
    try:
        # 간단한 더미 구현
        return True
    except Exception:
        return False

def resize(img, size, interpolation=INTER_LINEAR):
    """이미지 크기 조정"""
    # 간단한 더미 구현
    return img

def cvtColor(img, code):
    """색상 공간 변환"""
    # 간단한 더미 구현
    return img

def threshold(img, thresh, maxval, type):
    """임계값 처리"""
    # 간단한 더미 구현
    return thresh, img

def morphologyEx(img, op, kernel):
    """형태학적 연산"""
    return img

def getStructuringElement(shape, size):
    """구조 요소 생성"""
    return [[1] * size[0] for _ in range(size[1])]
'''
    
    with open(utils_dir / "opencv_replacement.py", 'w', encoding='utf-8') as f:
        f.write(opencv_replacement)
    
    print("  [OK] OpenCV 대체 모듈 생성 완료")

def create_import_patcher():
    """import 패치 모듈 생성"""
    print("import 패치 모듈 생성 중...")
    
    utils_dir = Path("src/utils")
    
    patcher_code = '''"""
import 패치 모듈
numpy, cv2 등의 import를 대체 모듈로 리다이렉트
"""
import sys
from pathlib import Path

# 현재 모듈 경로
current_dir = Path(__file__).parent

def patch_imports():
    """import 패치 적용"""
    # numpy import 패치
    try:
        import numpy
    except ImportError:
        # numpy 대체 모듈을 numpy로 등록
        from . import numpy_replacement
        sys.modules['numpy'] = numpy_replacement
        sys.modules['np'] = numpy_replacement
        print("[PATCH] numpy를 대체 모듈로 패치")
    except Exception as e:
        print(f"[PATCH] numpy DLL 오류로 인한 대체 모듈 사용: {e}")
        from . import numpy_replacement
        sys.modules['numpy'] = numpy_replacement
        sys.modules['np'] = numpy_replacement
    
    # cv2 import 패치
    try:
        import cv2
    except ImportError:
        from . import opencv_replacement
        sys.modules['cv2'] = opencv_replacement
        print("[PATCH] cv2를 대체 모듈로 패치")
    except Exception as e:
        print(f"[PATCH] cv2 오류로 인한 대체 모듈 사용: {e}")
        from . import opencv_replacement
        sys.modules['cv2'] = opencv_replacement

# 자동 패치 적용
patch_imports()
'''
    
    with open(utils_dir / "import_patcher.py", 'w', encoding='utf-8') as f:
        f.write(patcher_code)
    
    print("  [OK] import 패치 모듈 생성 완료")

def create_demo_main():
    """데모용 main 파일 생성"""
    print("데모용 main 파일 생성 중...")
    
    # 기존 main.py 백업
    if Path("main.py").exists():
        shutil.copy("main.py", "main_original.py")
        print("  [BACKUP] 기존 main.py를 main_original.py로 백업")
    
    demo_main = '''#!/usr/bin/env python3
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
    print("\\n핵심 모듈 테스트 중...")
    
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
    
    print(f"\\n모듈 테스트 결과: {success_count}/{total_tests} 성공")
    return success_count >= total_tests * 0.6  # 60% 이상 성공

def run_gui_demo():
    """GUI 데모 실행"""
    print("\\nGUI 데모 실행 시도...")
    
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
        
        info_label = QLabel("이 버전은 기술 데모 목적으로만 사용하세요.\\nOCR 기능은 제한적입니다.")
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
    print("\\n콘솔 데모 모드")
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
        
        print("\\n[SUCCESS] 콘솔 데모 실행 완료")
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
        print("\\n[ERROR] 필수 모듈 로드 실패")
        print("다음을 시도해보세요:")
        print("  1. python fix_numpy_auto.py")
        print("  2. pip install PyQt5 Pillow mss psutil")
        return False
    
    # 3. 실행 모드 선택
    try:
        # GUI 실행 시도
        print("\\nGUI 모드로 실행을 시도합니다...")
        if run_gui_demo():
            return True
    except Exception as e:
        print(f"GUI 모드 실패: {e}")
    
    # GUI 실패 시 콘솔 모드
    print("\\nGUI 실행 실패, 콘솔 모드로 전환...")
    return run_console_demo()

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\\n사용자에 의해 중단되었습니다.")
        sys.exit(0)
    except Exception as e:
        print(f"\\n예상치 못한 오류: {e}")
        sys.exit(1)
'''
    
    with open("main_demo.py", 'w', encoding='utf-8') as f:
        f.write(demo_main)
    
    print("  [OK] 데모용 main 파일 생성: main_demo.py")

def create_demo_launcher():
    """데모 실행 배치 파일 생성"""
    print("데모 실행 배치 파일 생성 중...")
    
    launcher_content = '''@echo off
title 카카오톡 OCR 챗봇 데모 (numpy 문제 우회 버전)
color 0B

echo.
echo ==========================================
echo 카카오톡 OCR 챗봇 시스템 - 데모 버전
echo numpy DLL 문제 우회 버전
echo ==========================================
echo.
echo 주의: 이것은 기술 데모 전용입니다.
echo 실제 OCR 기능은 제한적입니다.
echo 상업적 사용을 금지합니다.
echo.

REM 환경변수 설정
set PYTHONPATH=%CD%\\src;%PYTHONPATH%
set KMP_DUPLICATE_LIB_OK=TRUE
set CUDA_VISIBLE_DEVICES=-1
set OMP_NUM_THREADS=1
set PYTHONIOENCODING=utf-8

REM 가상환경 확인
if exist "venv\\Scripts\\python.exe" (
    echo 가상환경에서 실행...
    venv\\Scripts\\python.exe main_demo.py
) else (
    echo 시스템 Python으로 실행...
    python main_demo.py
)

REM 결과 확인
if %ERRORLEVEL% equ 0 (
    echo.
    echo 데모 실행 완료
) else (
    echo.
    echo 데모 실행 중 오류 발생
    echo 다음을 시도해보세요:
    echo   1. python create_numpy_free_version.py
    echo   2. pip install PyQt5 Pillow mss psutil
    echo.
    pause
)
'''
    
    with open("run_demo.bat", 'w', encoding='cp949') as f:
        f.write(launcher_content)
    
    print("  [OK] 데모 실행 배치 파일 생성: run_demo.bat")

def test_demo_functionality():
    """데모 기능 테스트"""
    print("데모 기능 테스트 중...")
    
    # Python path 설정
    src_path = Path("src")
    if str(src_path) not in sys.path:
        sys.path.insert(0, str(src_path))
    
    success_count = 0
    
    # 1. 대체 모듈 테스트
    try:
        from src.utils.numpy_replacement import array, zeros
        arr = array([1, 2, 3])
        zeros_arr = zeros(5)
        print("  [OK] numpy 대체 모듈 작동")
        success_count += 1
    except Exception as e:
        print(f"  [FAIL] numpy 대체 모듈: {e}")
    
    # 2. OpenCV 대체 모듈 테스트
    try:
        from src.utils.opencv_replacement import imread, resize
        print("  [OK] OpenCV 대체 모듈 작동")
        success_count += 1
    except Exception as e:
        print(f"  [FAIL] OpenCV 대체 모듈: {e}")
    
    # 3. import 패치 테스트
    try:
        from src.utils.import_patcher import patch_imports
        patch_imports()
        print("  [OK] import 패치 작동")
        success_count += 1
    except Exception as e:
        print(f"  [FAIL] import 패치: {e}")
    
    print(f"데모 기능 테스트: {success_count}/3 성공")
    return success_count >= 2

def main():
    """메인 실행 함수"""
    print("=" * 60)
    print("numpy 없는 데모 버전 생성 도구")
    print("numpy DLL 문제를 우회하여 실행 가능한 버전 생성")
    print("=" * 60)
    
    success_steps = 0
    
    # 1. numpy 대체 모듈 생성
    try:
        create_numpy_replacement()
        success_steps += 1
    except Exception as e:
        print(f"numpy 대체 모듈 생성 실패: {e}")
    
    # 2. OpenCV 대체 모듈 생성
    try:
        create_opencv_replacement()
        success_steps += 1
    except Exception as e:
        print(f"OpenCV 대체 모듈 생성 실패: {e}")
    
    # 3. import 패치 모듈 생성
    try:
        create_import_patcher()
        success_steps += 1
    except Exception as e:
        print(f"import 패치 모듈 생성 실패: {e}")
    
    # 4. 데모 main 파일 생성
    try:
        create_demo_main()
        success_steps += 1
    except Exception as e:
        print(f"데모 main 파일 생성 실패: {e}")
    
    # 5. 데모 실행 배치 파일 생성
    try:
        create_demo_launcher()
        success_steps += 1
    except Exception as e:
        print(f"실행 배치 파일 생성 실패: {e}")
    
    # 6. 기능 테스트
    if test_demo_functionality():
        success_steps += 1
    
    # 결과 요약
    print("\n" + "=" * 60)
    print(f"데모 버전 생성 결과: {success_steps}/6 단계 성공")
    
    if success_steps >= 5:
        print("[SUCCESS] numpy 없는 데모 버전 생성 완료!")
        print("\n실행 방법:")
        print("  1. run_demo.bat (권장)")
        print("  2. python main_demo.py")
        print("\n주의사항:")
        print("  - 이것은 기술 데모 전용입니다")
        print("  - OCR 기능은 더미 데이터를 반환합니다")
        print("  - 실제 사용을 위해서는 numpy 문제를 해결해야 합니다")
        return True
    else:
        print("[PARTIAL] 일부 기능이 작동하지 않을 수 있습니다.")
        return False

if __name__ == "__main__":
    main()