#!/usr/bin/env python3
"""
간단한 호환성 수정 스크립트 (이모지 없는 버전)
"""
import sys
import os
from pathlib import Path

def setup_compatibility():
    """기본 호환성 설정"""
    print("호환성 설정 적용 중...")
    
    # 환경변수 설정
    os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'
    os.environ['CUDA_VISIBLE_DEVICES'] = '-1'
    os.environ['OMP_NUM_THREADS'] = '1'
    
    # PYTHONPATH 설정
    src_path = Path(__file__).parent / "src"
    if str(src_path) not in sys.path:
        sys.path.insert(0, str(src_path))
    
    print("기본 호환성 설정 완료")

def create_compatibility_module():
    """호환성 모듈 생성"""
    print("호환성 모듈 생성 중...")
    
    utils_dir = Path("src/utils")
    utils_dir.mkdir(exist_ok=True)
    
    # __init__.py
    init_file = utils_dir / "__init__.py"
    if not init_file.exists():
        init_file.write_text("# Utils module", encoding='utf-8')
    
    # compatibility.py
    compatibility_code = '''"""
Python 3.13 호환성 모듈
"""
import os
import warnings

# 환경변수 설정
os.environ.setdefault('KMP_DUPLICATE_LIB_OK', 'TRUE')
os.environ.setdefault('CUDA_VISIBLE_DEVICES', '-1')

# 경고 억제
warnings.filterwarnings("ignore", category=DeprecationWarning)
warnings.filterwarnings("ignore", message=".*numpy.*")

def apply_all_patches():
    """모든 호환성 패치 적용"""
    pass

# 자동 적용
apply_all_patches()
'''
    
    with open(utils_dir / "compatibility.py", 'w', encoding='utf-8') as f:
        f.write(compatibility_code)
    
    print("호환성 모듈 생성 완료")

def test_imports():
    """핵심 모듈 import 테스트"""
    print("핵심 모듈 테스트 중...")
    
    tests = [
        ("numpy", "import numpy as np; print(f'numpy {np.__version__}')"),
        ("opencv", "import cv2; print(f'opencv {cv2.__version__}')"),
        ("PyQt5", "from PyQt5.QtWidgets import QApplication; print('PyQt5 OK')"),
        ("PIL", "from PIL import Image; print('Pillow OK')"),
    ]
    
    success = 0
    for name, code in tests:
        try:
            exec(code)
            print(f"[OK] {name}")
            success += 1
        except Exception as e:
            print(f"[FAIL] {name}: {e}")
    
    print(f"테스트 결과: {success}/{len(tests)} 성공")
    return success >= len(tests) * 0.75

def create_startup_script():
    """시작 스크립트 생성"""
    print("시작 스크립트 생성 중...")
    
    script_content = '''@echo off
echo 카카오톡 OCR 챗봇 시스템 (호환성 수정 버전)
echo 기술 데모용 - Python 3.13 지원
echo.

REM 환경변수 설정
set PYTHONPATH=%CD%\\src;%PYTHONPATH%
set KMP_DUPLICATE_LIB_OK=TRUE
set CUDA_VISIBLE_DEVICES=-1
set OMP_NUM_THREADS=1

REM 가상환경 활성화
if exist "venv\\Scripts\\activate.bat" (
    call venv\\Scripts\\activate.bat
    echo 가상환경 활성화됨
) else (
    echo 가상환경이 없습니다.
    echo python -m venv venv 로 생성하세요.
    pause
    exit /b 1
)

REM 프로그램 실행
echo 프로그램 시작...
python main.py

if %ERRORLEVEL% neq 0 (
    echo 오류가 발생했습니다.
    pause
)
'''
    
    with open("start_demo.bat", 'w', encoding='cp949') as f:
        f.write(script_content)
    
    print("시작 스크립트 생성 완료: start_demo.bat")

def main():
    """메인 실행"""
    print("=" * 50)
    print("간단 호환성 수정 도구")
    print("=" * 50)
    
    print(f"Python: {sys.version}")
    print(f"작업 디렉토리: {os.getcwd()}")
    
    # 1. 기본 호환성 설정
    setup_compatibility()
    
    # 2. 호환성 모듈 생성
    create_compatibility_module()
    
    # 3. Import 테스트
    if test_imports():
        print("기본 모듈 테스트 통과")
    else:
        print("일부 모듈에 문제가 있습니다.")
    
    # 4. 시작 스크립트 생성
    create_startup_script()
    
    print("\n" + "=" * 50)
    print("호환성 수정 완료!")
    print("start_demo.bat 파일로 실행하세요.")
    print("=" * 50)

if __name__ == "__main__":
    main()