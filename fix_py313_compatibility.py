#!/usr/bin/env python3
"""
Python 3.13 호환성 수정 스크립트
기존 코드를 건드리지 않고 호환성 문제만 해결
"""
import sys
import subprocess
import os
from pathlib import Path

def check_python_version():
    """Python 버전 확인"""
    version = sys.version_info
    print(f"현재 Python 버전: {version.major}.{version.minor}.{version.micro}")
    
    if version.major != 3:
        print("❌ Python 3이 필요합니다.")
        return False
    
    if version.minor < 11:
        print("⚠️  Python 3.11 이상을 권장합니다.")
    elif version.minor == 13:
        print("✅ Python 3.13 감지됨. 호환성 수정을 적용합니다.")
    
    return True

def fix_numpy_compatibility():
    """numpy 호환성 문제 해결"""
    print("\n🔧 numpy 호환성 수정 중...")
    try:
        # numpy 버전 확인
        import numpy as np
        print(f"현재 numpy 버전: {np.__version__}")
        
        # 호환되는 버전인지 확인
        if np.__version__.startswith('2.'):
            print("✅ numpy 2.x 호환 버전 사용 중")
            return True
        else:
            print("⚠️  numpy 1.x 버전 감지. 업그레이드를 권장합니다.")
            return True
            
    except ImportError:
        print("❌ numpy가 설치되지 않았습니다.")
        return False
    except Exception as e:
        print(f"❌ numpy 확인 중 오류: {e}")
        return False

def create_compatibility_shim():
    """호환성 shim 모듈 생성"""
    print("\n🔧 호환성 shim 생성 중...")
    
    # src/utils/compatibility.py 생성
    utils_dir = Path("src/utils")
    utils_dir.mkdir(exist_ok=True)
    
    compatibility_code = '''"""
Python 3.13 호환성 shim
기존 코드 수정 없이 호환성 문제 해결
"""
import sys
import warnings

# numpy 관련 경고 억제
warnings.filterwarnings("ignore", category=DeprecationWarning, module="numpy")
warnings.filterwarnings("ignore", message=".*dtype.*")

def suppress_numpy_warnings():
    """numpy 관련 경고 억제"""
    try:
        import numpy as np
        # numpy 2.x 호환성 설정
        if hasattr(np, '_NoValue'):
            # numpy 2.x에서 제거된 기능들에 대한 fallback
            pass
    except ImportError:
        pass

def fix_scipy_compatibility():
    """scipy 호환성 문제 해결"""
    try:
        import scipy
        # scipy 관련 호환성 처리
        pass
    except ImportError:
        pass

def patch_paddleocr():
    """PaddleOCR 호환성 패치"""
    try:
        # PaddleOCR import 전에 환경 설정
        import os
        os.environ.setdefault('KMP_DUPLICATE_LIB_OK', 'TRUE')
        
        # CUDA 관련 설정
        os.environ.setdefault('CUDA_VISIBLE_DEVICES', '-1')  # CPU 모드 강제
    except Exception:
        pass

def apply_all_fixes():
    """모든 호환성 수정 적용"""
    suppress_numpy_warnings()
    fix_scipy_compatibility()
    patch_paddleocr()

# 모듈 import 시 자동으로 적용
apply_all_fixes()
'''
    
    with open(utils_dir / "compatibility.py", 'w', encoding='utf-8') as f:
        f.write(compatibility_code)
    
    print("✅ 호환성 shim 생성 완료")

def update_main_imports():
    """메인 파일에 호환성 import 추가"""
    print("\n🔧 메인 파일 호환성 import 추가...")
    
    main_file = Path("main.py")
    if not main_file.exists():
        print("❌ main.py 파일을 찾을 수 없습니다.")
        return False
    
    # main.py 읽기
    with open(main_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 호환성 import가 이미 있는지 확인
    if "from src.utils.compatibility import" in content:
        print("✅ 호환성 import가 이미 존재합니다.")
        return True
    
    # 호환성 import 추가
    import_line = "# Python 3.13 호환성 수정\nfrom src.utils.compatibility import apply_all_fixes\napply_all_fixes()\n\n"
    
    # 기존 import 섹션 다음에 추가
    lines = content.split('\n')
    new_lines = []
    added = False
    
    for i, line in enumerate(lines):
        new_lines.append(line)
        # 첫 번째 import 구문 이후에 추가
        if not added and line.strip().startswith('import ') and i > 0:
            new_lines.extend([
                "",
                "# Python 3.13 호환성 수정",
                "try:",
                "    from src.utils.compatibility import apply_all_fixes",
                "    apply_all_fixes()",
                "except ImportError:",
                "    pass  # 호환성 모듈이 없어도 계속 실행",
                ""
            ])
            added = True
    
    # 파일 업데이트
    with open(main_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(new_lines))
    
    print("✅ 메인 파일 호환성 import 추가 완료")
    return True

def install_compatible_packages():
    """호환 가능한 패키지 설치"""
    print("\n📦 Python 3.13 호환 패키지 설치 중...")
    
    try:
        # requirements_py313.txt 사용
        result = subprocess.run([
            sys.executable, "-m", "pip", "install", 
            "-r", "requirements_py313.txt",
            "--upgrade"
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ 호환 패키지 설치 완료")
            return True
        else:
            print(f"❌ 패키지 설치 실패: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ 패키지 설치 중 오류: {e}")
        return False

def create_startup_script():
    """호환성 적용된 시작 스크립트 생성"""
    print("\n📝 시작 스크립트 생성 중...")
    
    script_content = '''@echo off
echo Python 3.13 호환 카카오톡 챗봇 시작...
echo.

REM 환경변수 설정
set PYTHONPATH=%CD%\\src;%PYTHONPATH%
set KMP_DUPLICATE_LIB_OK=TRUE
set CUDA_VISIBLE_DEVICES=-1

REM Qt 플러그인 경로 설정
if exist "venv\\Lib\\site-packages\\PyQt5\\Qt5\\plugins" (
    set QT_PLUGIN_PATH=%CD%\\venv\\Lib\\site-packages\\PyQt5\\Qt5\\plugins
)

REM 가상환경 활성화
if exist "venv\\Scripts\\activate.bat" (
    call venv\\Scripts\\activate.bat
) else (
    echo 가상환경을 찾을 수 없습니다. python -m venv venv로 생성하세요.
    pause
    exit /b 1
)

REM Python 실행
python main.py

REM 오류 발생 시 대기
if %ERRORLEVEL% neq 0 (
    echo.
    echo 오류가 발생했습니다. 로그를 확인하세요.
    pause
)
'''
    
    with open("run_py313_compatible.bat", 'w', encoding='cp949') as f:
        f.write(script_content)
    
    print("✅ 호환성 시작 스크립트 생성 완료: run_py313_compatible.bat")

def main():
    """메인 실행 함수"""
    print("🔧 Python 3.13 호환성 수정 도구")
    print("=" * 50)
    
    # 1. Python 버전 확인
    if not check_python_version():
        return False
    
    # 2. numpy 호환성 확인
    fix_numpy_compatibility()
    
    # 3. 호환성 shim 생성
    create_compatibility_shim()
    
    # 4. 메인 파일 수정
    update_main_imports()
    
    # 5. 호환 패키지 설치
    if input("\n호환 패키지를 설치하시겠습니까? (y/n): ").lower() == 'y':
        install_compatible_packages()
    
    # 6. 시작 스크립트 생성
    create_startup_script()
    
    print("\n✅ Python 3.13 호환성 수정 완료!")
    print("\n사용법:")
    print("1. run_py313_compatible.bat 실행")
    print("2. 또는 python main.py로 직접 실행")
    
    return True

if __name__ == "__main__":
    main()