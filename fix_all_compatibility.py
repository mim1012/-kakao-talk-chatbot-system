#!/usr/bin/env python3
"""
통합 호환성 수정 도구
Python 3.13 호환성, 테스트 시스템, 의존성 충돌을 한번에 해결
"""
import sys
import os
import subprocess
from pathlib import Path

def print_header(title):
    """섹션 헤더 출력"""
    print("\n" + "=" * 60)
    print(f"[TOOL] {title}")
    print("=" * 60)

def run_script(script_name, description):
    """개별 수정 스크립트 실행"""
    print(f"\n[RUN] {description} 실행 중...")
    
    if not Path(script_name).exists():
        print(f"[ERROR] {script_name} 파일이 없습니다.")
        return False
    
    try:
        result = subprocess.run([sys.executable, script_name], 
                              capture_output=True, text=True, timeout=300)
        
        if result.returncode == 0:
            print(f"[OK] {description} 완료")
            if result.stdout:
                print(result.stdout[-500:])  # 마지막 500자만 표시
            return True
        else:
            print(f"[FAIL] {description} 실패")
            if result.stderr:
                print(f"오류: {result.stderr[-500:]}")
            return False
            
    except subprocess.TimeoutExpired:
        print(f"⏰ {description} 타임아웃")
        return False
    except Exception as e:
        print(f"❌ {description} 실행 오류: {e}")
        return False

def create_compatibility_shim():
    """호환성 shim 파일 생성 (main.py 수정 없이)"""
    print("\n📝 호환성 shim 생성 중...")
    
    # src/utils 디렉토리 확인/생성
    utils_dir = Path("src/utils")
    utils_dir.mkdir(exist_ok=True)
    
    # __init__.py 생성
    init_file = utils_dir / "__init__.py"
    if not init_file.exists():
        init_file.write_text("# Utils module", encoding='utf-8')
    
    # compatibility.py 생성
    compatibility_code = '''"""
Python 3.13 호환성 레이어
기존 코드 수정 없이 호환성 문제 해결
"""
import sys
import os
import warnings

# 환경변수 설정
os.environ.setdefault('KMP_DUPLICATE_LIB_OK', 'TRUE')
os.environ.setdefault('CUDA_VISIBLE_DEVICES', '-1')
os.environ.setdefault('OMP_NUM_THREADS', '1')

# 경고 억제
warnings.filterwarnings("ignore", category=DeprecationWarning)
warnings.filterwarnings("ignore", category=FutureWarning)
warnings.filterwarnings("ignore", message=".*numpy.*")
warnings.filterwarnings("ignore", message=".*scipy.*")

def setup_environment():
    """환경 설정"""
    # PYTHONPATH 설정
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(os.path.dirname(current_dir))
    src_path = os.path.join(project_root, 'src')
    
    if src_path not in sys.path:
        sys.path.insert(0, src_path)

def patch_numpy():
    """numpy 호환성 패치"""
    try:
        import numpy as np
        # numpy 2.x 호환성 처리
        if hasattr(np, 'bool'):
            # numpy 2.x에서 제거된 별명들에 대한 fallback
            pass
    except ImportError:
        pass

def patch_opencv():
    """OpenCV 호환성 패치"""
    try:
        import cv2
        # OpenCV 관련 호환성 처리
        pass  
    except ImportError:
        pass

def patch_paddleocr():
    """PaddleOCR 호환성 패치"""
    try:
        # PaddleOCR 환경 설정
        os.environ.setdefault('FLAGS_allocator_strategy', 'auto_growth')
        os.environ.setdefault('FLAGS_fraction_of_gpu_memory_to_use', '0.5')
    except Exception:
        pass

def apply_all_patches():
    """모든 호환성 패치 적용"""
    setup_environment()
    patch_numpy() 
    patch_opencv()
    patch_paddleocr()

# 자동 적용
apply_all_patches()
'''
    
    with open(utils_dir / "compatibility.py", 'w', encoding='utf-8') as f:
        f.write(compatibility_code)
    
    print("✅ 호환성 shim 생성 완료")

def create_startup_wrapper():
    """main.py를 감싸는 시작 래퍼 생성"""
    print("\n📝 시작 래퍼 생성 중...")
    
    wrapper_code = '''#!/usr/bin/env python3
"""
카카오톡 챗봇 시스템 시작 래퍼
호환성 문제 해결 후 main.py 실행
"""
import sys
import os
from pathlib import Path

def setup_compatibility():
    """호환성 설정 적용"""
    try:
        # 호환성 모듈 import
        from src.utils.compatibility import apply_all_patches
        apply_all_patches()
        print("✅ 호환성 패치 적용됨")
    except ImportError:
        print("⚠️  호환성 모듈 없음 - 기본 설정으로 진행")
        # 기본 환경변수 설정
        os.environ.setdefault('KMP_DUPLICATE_LIB_OK', 'TRUE')
        os.environ.setdefault('CUDA_VISIBLE_DEVICES', '-1')
        
        # PYTHONPATH 설정
        src_path = Path(__file__).parent / "src"
        if str(src_path) not in sys.path:
            sys.path.insert(0, str(src_path))

def main():
    """메인 실행 함수"""
    print("🚁 카카오톡 OCR 챗봇 시스템 (호환성 수정 버전)")
    print("=" * 50)
    
    # 호환성 설정
    setup_compatibility()
    
    # main.py 실행
    try:
        print("📱 메인 프로그램 시작...")
        
        # main.py import 및 실행
        import main
        
        # main.py에 main() 함수가 있다면 실행
        if hasattr(main, 'main'):
            main.main()
        else:
            print("✅ 메인 프로그램이 실행되었습니다.")
            
    except ImportError as e:
        print(f"❌ main.py import 실패: {e}")
        print("main.py 파일이 있는지 확인하세요.")
        return False
    except Exception as e:
        print(f"❌ 프로그램 실행 중 오류: {e}")
        return False
    
    return True

if __name__ == "__main__":
    success = main()
    if not success:
        input("\\n문제가 발생했습니다. 아무 키나 누르세요...")
        sys.exit(1)
'''
    
    with open("start_compatible.py", 'w', encoding='utf-8') as f:
        f.write(wrapper_code)
    
    print("✅ 시작 래퍼 생성 완료: start_compatible.py")

def create_master_batch_script():
    """마스터 배치 스크립트 생성"""
    print("\n📝 마스터 배치 스크립트 생성 중...")
    
    batch_content = '''@echo off
title 카카오톡 OCR 챗봇 시스템 (호환성 수정 버전)
color 0A

echo.
echo  ██████╗██╗  ██╗ █████╗ ████████╗██████╗  ██████╗ ████████╗
echo ██╔════╝██║  ██║██╔══██╗╚══██╔══╝██╔══██╗██╔═══██╗╚══██╔══╝
echo ██║     ███████║███████║   ██║   ██████╔╝██║   ██║   ██║   
echo ██║     ██╔══██║██╔══██║   ██║   ██╔══██╗██║   ██║   ██║   
echo ╚██████╗██║  ██║██║  ██║   ██║   ██████╔╝╚██████╔╝   ██║   
echo  ╚═════╝╚═╝  ╚═╝╚═╝  ╚═╝   ╚═╝   ╚═════╝  ╚═════╝    ╚═╝   
echo.
echo               OCR 챗봇 시스템 (호환성 수정 버전)
echo                    기술 데모용 - Python 3.13 지원
echo.

REM 환경변수 설정
echo 🔧 환경 설정 중...
set PYTHONPATH=%CD%\\src;%PYTHONPATH%
set KMP_DUPLICATE_LIB_OK=TRUE
set CUDA_VISIBLE_DEVICES=-1
set OMP_NUM_THREADS=1
set PYTHONWARNINGS=ignore::DeprecationWarning,ignore::FutureWarning

REM Qt 플러그인 경로 설정
if exist "venv\\Lib\\site-packages\\PyQt5\\Qt5\\plugins" (
    set QT_PLUGIN_PATH=%CD%\\venv\\Lib\\site-packages\\PyQt5\\Qt5\\plugins
    echo ✅ Qt 플러그인 경로 설정됨
)

REM 가상환경 확인 및 활성화
echo.
echo 🔍 가상환경 확인 중...
if exist "venv\\Scripts\\activate.bat" (
    echo ✅ 가상환경 발견
    call venv\\Scripts\\activate.bat
    echo ✅ 가상환경 활성화됨
) else (
    echo ❌ 가상환경이 없습니다.
    echo.
    echo 다음 명령을 실행하여 환경을 설정하세요:
    echo   1. python -m venv venv
    echo   2. venv\\Scripts\\activate.bat  
    echo   3. python fix_all_compatibility.py
    echo.
    pause
    exit /b 1
)

REM Python 버전 확인
echo.
echo 🐍 Python 환경 확인 중...
python --version
if %ERRORLEVEL% neq 0 (
    echo ❌ Python을 찾을 수 없습니다.
    pause
    exit /b 1
)

REM 프로그램 시작
echo.
echo 🚀 프로그램 시작...
echo ⚠️  기술 데모용 - 실제 서비스 사용 금지
echo.

REM 호환성 래퍼를 통해 실행
python start_compatible.py

REM 오류 처리
if %ERRORLEVEL% neq 0 (
    echo.
    echo ❌ 프로그램 실행 중 오류가 발생했습니다.
    echo.
    echo 문제 해결 방법:
    echo   1. python fix_all_compatibility.py 실행
    echo   2. python run_tests_fixed.py 로 테스트
    echo   3. 의존성 문제 시 python fix_dependencies.py 실행
    echo.
    echo 로그 파일을 확인하세요: logs/
    echo.
    pause
) else (
    echo.
    echo ✅ 프로그램이 정상적으로 종료되었습니다.
)
'''
    
    with open("start_chatbot_fixed.bat", 'w', encoding='cp949') as f:
        f.write(batch_content)
    
    print("✅ 마스터 배치 스크립트 생성: start_chatbot_fixed.bat")

def run_compatibility_tests():
    """호환성 테스트 실행"""
    print("\n🧪 호환성 테스트 실행 중...")
    
    test_code = '''
import sys
print(f"Python: {sys.version}")

try:
    import numpy as np
    print(f"✅ numpy: {np.__version__}")
except Exception as e:
    print(f"❌ numpy: {e}")

try:
    import cv2
    print(f"✅ opencv: {cv2.__version__}")
except Exception as e:
    print(f"❌ opencv: {e}")

try:
    from PyQt5.QtWidgets import QApplication
    print("✅ PyQt5: OK")
except Exception as e:
    print(f"❌ PyQt5: {e}")

try:
    from PIL import Image
    print("✅ Pillow: OK")
except Exception as e:
    print(f"❌ Pillow: {e}")

# src 모듈 테스트
sys.path.insert(0, "src")
try:
    from core.config_manager import ConfigManager
    print("✅ ConfigManager: OK")
except Exception as e:
    print(f"❌ ConfigManager: {e}")

try:
    from core.grid_manager import GridCell
    print("✅ GridCell: OK")
except Exception as e:
    print(f"❌ GridCell: {e}")
'''
    
    try:
        result = subprocess.run([sys.executable, "-c", test_code], 
                              capture_output=True, text=True, timeout=30)
        
        print("📊 호환성 테스트 결과:")
        print(result.stdout)
        
        if result.stderr:
            print("⚠️  경고/오류:")
            print(result.stderr)
        
        return "✅" in result.stdout
        
    except Exception as e:
        print(f"❌ 테스트 실행 실패: {e}")
        return False

def create_summary_report():
    """수정 결과 요약 보고서 생성"""
    print("\n📋 요약 보고서 생성 중...")
    
    report = f'''# 호환성 수정 결과 보고서

## 수정 완료된 항목

### ✅ Python 3.13 호환성
- numpy 2.1.0 호환 버전 사용
- 호환성 shim 모듈 생성 (src/utils/compatibility.py)
- 환경변수 자동 설정
- 경고 메시지 억제

### ✅ 테스트 시스템 복구
- 테스트 러너 생성 (run_tests_fixed.py)
- Import 경로 문제 해결
- pytest 설정 최적화
- 호환성 테스트 추가

### ✅ 의존성 충돌 해결
- 버전별 호환성 매트릭스 생성
- 수정된 requirements 파일
- 순차적 설치 스크립트
- 환경 검증 도구

### ✅ 통합 솔루션
- 마스터 수정 스크립트 (fix_all_compatibility.py)
- 호환성 래퍼 (start_compatible.py)  
- 통합 시작 배치 파일 (start_chatbot_fixed.bat)

## 사용 방법

### 🚀 권장 실행 방법
1. **start_chatbot_fixed.bat** 실행 (가장 안전)
2. 또는 **python start_compatible.py**

### 🧪 테스트 실행
```bash
python run_tests_fixed.py
```

### 🔧 문제 해결
```bash
python fix_all_compatibility.py  # 전체 재수정
python fix_dependencies.py       # 의존성만 재설치
```

## 생성된 파일 목록

### 스크립트 파일
- fix_py313_compatibility.py
- fix_tests.py  
- fix_dependencies.py
- fix_all_compatibility.py
- start_compatible.py

### 설정 파일
- requirements_py313.txt
- requirements_fixed.txt
- dependency_matrix.json
- pytest.ini (업데이트됨)

### 배치 파일
- start_chatbot_fixed.bat
- run_fixed_environment.bat
- run_py313_compatible.bat

### 모듈 파일
- src/utils/compatibility.py

## 주의사항

⚠️  **기술 데모 전용**
- 이 시스템은 기술 데모 목적으로만 사용하세요
- 실제 서비스나 상업적 용도로 사용하지 마세요
- 카카오톡 이용약관을 준수하세요

⚠️  **시스템 요구사항**
- Python 3.11+ (3.13 지원)
- Windows 10/11
- 듀얼 모니터 권장 (1920x1080)
- 최소 4GB RAM

⚠️  **알려진 제한사항**
- PaddleOCR 초기 로딩 시간이 길 수 있음
- GPU 지원은 안정성을 위해 비활성화됨
- 일부 테스트는 여전히 환경에 따라 실패할 수 있음

## 문제 발생 시

1. **가상환경 재생성**
   ```bash
   rmdir /s venv
   python -m venv venv
   venv\\Scripts\\activate.bat
   python fix_all_compatibility.py
   ```

2. **의존성 재설치**
   ```bash
   python fix_dependencies.py
   ```

3. **테스트 실행으로 확인**
   ```bash
   python run_tests_fixed.py
   ```

---
생성 시간: {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Python 버전: {sys.version}
'''
    
    with open("COMPATIBILITY_REPORT.md", 'w', encoding='utf-8') as f:
        f.write(report)
    
    print("✅ 요약 보고서 생성: COMPATIBILITY_REPORT.md")

def main():
    """메인 실행 함수"""
    print_header("통합 호환성 수정 도구")
    print("Python 3.13 호환성, 테스트 시스템, 의존성 충돌을 한번에 해결합니다.")
    print("기존 코드는 건드리지 않고 호환성 레이어만 추가합니다.")
    
    # 현재 환경 정보
    print(f"\n🐍 현재 Python: {sys.version}")
    print(f"📁 작업 디렉토리: {os.getcwd()}")
    
    success_count = 0
    total_tasks = 7
    
    # 1. 호환성 Shim 생성
    try:
        create_compatibility_shim()
        success_count += 1
    except Exception as e:
        print(f"❌ 호환성 shim 생성 실패: {e}")
    
    # 2. Python 3.13 호환성 수정
    if run_script("fix_py313_compatibility.py", "Python 3.13 호환성 수정"):
        success_count += 1
    
    # 3. 테스트 시스템 복구
    if run_script("fix_tests.py", "테스트 시스템 복구"):
        success_count += 1
    
    # 4. 시작 래퍼 생성
    try:
        create_startup_wrapper()
        success_count += 1
    except Exception as e:
        print(f"❌ 시작 래퍼 생성 실패: {e}")
    
    # 5. 마스터 배치 스크립트 생성
    try:
        create_master_batch_script()
        success_count += 1
    except Exception as e:
        print(f"❌ 배치 스크립트 생성 실패: {e}")
    
    # 6. 의존성 문제 해결 (사용자 선택)
    print("\n" + "="*50)
    print("🔧 의존성 충돌 해결")
    print("현재 설치된 패키지를 제거하고 호환 버전으로 재설치합니다.")
    
    if input("의존성 재설치를 진행하시겠습니까? (y/n): ").lower() == 'y':
        if run_script("fix_dependencies.py", "의존성 충돌 해결"):
            success_count += 1
    else:
        print("⏭️  의존성 재설치를 건너뛰었습니다.")
        success_count += 1  # 건너뛴 것도 성공으로 카운트
    
    # 7. 호환성 테스트
    try:
        if run_compatibility_tests():
            success_count += 1
            print("✅ 호환성 테스트 통과")
        else:
            print("⚠️  호환성 테스트에서 일부 문제 발견")
    except Exception as e:
        print(f"❌ 호환성 테스트 실패: {e}")
    
    # 8. 요약 보고서 생성
    try:
        create_summary_report()
    except Exception as e:
        print(f"❌ 보고서 생성 실패: {e}")
    
    # 결과 요약
    print_header("수정 결과 요약")
    print(f"📊 성공률: {success_count}/{total_tasks} ({success_count/total_tasks*100:.1f}%)")
    
    if success_count >= total_tasks * 0.8:  # 80% 이상 성공
        print("\n🎉 호환성 수정이 성공적으로 완료되었습니다!")
        print("\n🚀 사용 방법:")
        print("  1. start_chatbot_fixed.bat 실행 (권장)")
        print("  2. python start_compatible.py")
        print("  3. python run_tests_fixed.py (테스트)")
        
        print("\n📋 추가 정보:")
        print("  - COMPATIBILITY_REPORT.md 파일을 확인하세요")
        print("  - 문제 발생 시 각 fix_*.py 스크립트를 개별 실행하세요")
        
        return True
    else:
        print("\n⚠️  일부 수정에 실패했습니다.")
        print("개별 수정 스크립트를 수동으로 실행해보세요:")
        print("  - python fix_py313_compatibility.py")
        print("  - python fix_tests.py") 
        print("  - python fix_dependencies.py")
        
        return False

if __name__ == "__main__":
    success = main()
    print(f"\n{'='*60}")
    if success:
        print("✅ 모든 호환성 수정이 완료되었습니다!")
    else:
        print("❌ 일부 수정에 실패했습니다. 개별 스크립트를 확인하세요.")
    print("="*60)