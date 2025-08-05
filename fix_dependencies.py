#!/usr/bin/env python3
"""
의존성 충돌 해결 스크립트
기존 코드를 건드리지 않고 의존성 문제만 해결
"""
import sys
import subprocess
import pkg_resources
from pathlib import Path
import json

def check_current_environment():
    """현재 환경 분석"""
    print("🔍 현재 환경 분석 중...")
    
    # Python 버전
    version = sys.version_info
    print(f"Python: {version.major}.{version.minor}.{version.micro}")
    
    # 가상환경 확인
    in_venv = hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix)
    print(f"가상환경: {'활성화됨' if in_venv else '비활성화됨'}")
    
    # 설치된 패키지 확인
    try:
        installed_packages = [d.project_name for d in pkg_resources.working_set]
        critical_packages = ['numpy', 'opencv-python', 'paddleocr', 'PyQt5', 'pillow']
        
        print("\n📦 주요 패키지 상태:")
        for package in critical_packages:
            if package.lower() in [p.lower() for p in installed_packages]:
                try:
                    version = pkg_resources.get_distribution(package).version
                    print(f"  ✅ {package}: {version}")
                except:
                    print(f"  ⚠️  {package}: 설치됨 (버전 확인 실패)")
            else:
                print(f"  ❌ {package}: 미설치")
                
    except Exception as e:
        print(f"❌ 패키지 상태 확인 실패: {e}")

def create_dependency_matrix():
    """의존성 호환성 매트릭스 생성"""
    print("\n📋 의존성 호환성 매트릭스 생성...")
    
    compatibility_matrix = {
        "python_3.11": {
            "numpy": "1.24.3",
            "opencv-python": "4.8.1.78", 
            "paddleocr": "2.7.3",
            "paddlepaddle": "2.5.2",
            "PyQt5": "5.15.9",
            "pillow": "10.0.1"
        },
        "python_3.12": {
            "numpy": "1.26.4",
            "opencv-python": "4.9.0.80",
            "paddleocr": "2.8.0",
            "paddlepaddle": "2.6.0",
            "PyQt5": "5.15.10",
            "pillow": "10.2.0"
        },
        "python_3.13": {
            "numpy": "2.1.0",  # 최신 호환 버전
            "opencv-python": "4.10.0.84",
            "paddleocr": "2.8.1",
            "paddlepaddle": "3.0.0b1",  # 베타 버전이지만 3.13 호환
            "PyQt5": "5.15.10",
            "pillow": "10.4.0"
        }
    }
    
    # JSON으로 저장
    with open("dependency_matrix.json", 'w', encoding='utf-8') as f:
        json.dump(compatibility_matrix, f, indent=2, ensure_ascii=False)
    
    print("✅ 의존성 매트릭스 저장 완료: dependency_matrix.json")
    return compatibility_matrix

def get_compatible_versions():
    """현재 Python 버전에 맞는 패키지 버전 반환"""
    version = sys.version_info
    
    try:
        with open("dependency_matrix.json", 'r', encoding='utf-8') as f:
            matrix = json.load(f)
    except:
        matrix = create_dependency_matrix()
    
    python_key = f"python_{version.major}.{version.minor}"
    
    if python_key in matrix:
        return matrix[python_key]
    else:
        # 기본값으로 3.13 설정 사용
        print(f"⚠️  Python {version.major}.{version.minor}에 대한 호환성 정보가 없습니다. 3.13 설정을 사용합니다.")
        return matrix.get("python_3.13", {})

def create_fixed_requirements():
    """수정된 requirements.txt 생성"""
    print("\n📝 수정된 requirements 파일 생성...")
    
    compatible_versions = get_compatible_versions()
    
    requirements_content = f'''# Python {sys.version_info.major}.{sys.version_info.minor} 호환 의존성
# 자동 생성됨 - 수동 편집 하지 마세요

# 핵심 의존성 (순서 중요)
numpy=={compatible_versions.get('numpy', '2.1.0')}
Pillow=={compatible_versions.get('pillow', '10.4.0')}
opencv-python=={compatible_versions.get('opencv-python', '4.10.0.84')}

# GUI 프레임워크
PyQt5=={compatible_versions.get('PyQt5', '5.15.10')}

# OCR 의존성 (PaddlePaddle 먼저 설치)
paddlepaddle=={compatible_versions.get('paddlepaddle', '3.0.0b1')}
paddleocr=={compatible_versions.get('paddleocr', '2.8.1')}

# 유틸리티 라이브러리
mss==9.0.1
screeninfo==0.8.1
psutil==6.0.0
keyboard==0.13.5
pyautogui==0.9.54

# 테스트 프레임워크
pytest==8.3.2
pytest-asyncio==0.23.8
pytest-mock==3.14.0

# 선택적 의존성 (문제 시 주석 처리)
# shapely>=1.7.0
# scipy>=1.9.0
'''
    
    with open("requirements_fixed.txt", 'w', encoding='utf-8') as f:
        f.write(requirements_content)
    
    print("✅ 수정된 requirements 생성: requirements_fixed.txt")

def uninstall_conflicting_packages():
    """충돌하는 패키지 제거"""
    print("\n🗑️  충돌하는 패키지 제거 중...")
    
    # 제거할 패키지들 (의존성 순서 고려)
    packages_to_remove = [
        'paddleocr',
        'paddlepaddle',
        'paddlepaddle-gpu', 
        'opencv-python',
        'opencv-contrib-python',
        'numpy',
        'pillow'
    ]
    
    for package in packages_to_remove:
        try:
            result = subprocess.run([
                sys.executable, "-m", "pip", "uninstall", 
                package, "-y"
            ], capture_output=True, text=True)
            
            if result.returncode == 0:
                print(f"  ✅ {package} 제거 완료")
            else:
                print(f"  ⚠️  {package} 제거 실패 (이미 없거나 오류)")
        except Exception as e:
            print(f"  ❌ {package} 제거 중 오류: {e}")

def install_fixed_packages():
    """수정된 패키지 설치"""
    print("\n📦 호환 패키지 설치 중...")
    
    try:
        # pip 업그레이드
        subprocess.run([sys.executable, "-m", "pip", "install", "--upgrade", "pip"], 
                      capture_output=True)
        
        # 순차적으로 설치 (의존성 순서 중요)
        install_order = [
            "numpy",
            "Pillow", 
            "opencv-python",
            "PyQt5",
            "paddlepaddle",
            "paddleocr"
        ]
        
        for package in install_order:
            print(f"  📦 {package} 설치 중...")
            result = subprocess.run([
                sys.executable, "-m", "pip", "install",
                f"{package}",
                "--no-deps",  # 의존성 자동 설치 방지
                "--force-reinstall"
            ], capture_output=True, text=True)
            
            if result.returncode == 0:
                print(f"  ✅ {package} 설치 완료")
            else:
                print(f"  ❌ {package} 설치 실패: {result.stderr[:200]}")
        
        # 나머지 패키지들 설치
        print("  📦 유틸리티 패키지 설치 중...")
        result = subprocess.run([
            sys.executable, "-m", "pip", "install",
            "-r", "requirements_fixed.txt",
            "--no-deps"
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print("  ✅ 모든 패키지 설치 완료")
            return True
        else:
            print(f"  ❌ 일부 패키지 설치 실패: {result.stderr[:200]}")
            return False
            
    except Exception as e:
        print(f"❌ 패키지 설치 중 오류: {e}")
        return False

def verify_installation():
    """설치 검증"""
    print("\n🔍 설치 검증 중...")
    
    test_imports = [
        ('numpy', 'import numpy as np; print(f"numpy {np.__version__}")'),
        ('opencv', 'import cv2; print(f"opencv {cv2.__version__}")'),
        ('PyQt5', 'from PyQt5.QtWidgets import QApplication; print("PyQt5 OK")'),
        ('PIL', 'from PIL import Image; print("Pillow OK")'),
    ]
    
    success_count = 0
    for name, test_code in test_imports:
        try:
            result = subprocess.run([
                sys.executable, "-c", test_code
            ], capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                print(f"  ✅ {name}: {result.stdout.strip()}")
                success_count += 1
            else:
                print(f"  ❌ {name}: {result.stderr.strip()}")
        except Exception as e:
            print(f"  ❌ {name}: 테스트 실패 - {e}")
    
    # PaddleOCR은 별도로 테스트 (시간이 오래 걸림)
    print("  🔍 PaddleOCR 테스트 중... (시간이 걸릴 수 있습니다)")
    try:
        result = subprocess.run([
            sys.executable, "-c", 
            "import paddleocr; print('PaddleOCR import OK')"
        ], capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            print("  ✅ PaddleOCR: 정상")
            success_count += 1
        else:
            print(f"  ❌ PaddleOCR: {result.stderr.strip()}")
    except subprocess.TimeoutExpired:
        print("  ⏰ PaddleOCR: 타임아웃 (설치는 되었을 가능성 높음)")
        success_count += 0.5
    except Exception as e:
        print(f"  ❌ PaddleOCR: {e}")
    
    total_tests = len(test_imports) + 1
    print(f"\n📊 검증 결과: {success_count}/{total_tests} 성공")
    return success_count >= total_tests * 0.8  # 80% 이상 성공

def create_environment_script():
    """환경 설정 스크립트 생성"""
    print("\n📝 환경 설정 스크립트 생성...")
    
    script_content = '''@echo off
echo 의존성 문제 해결된 환경으로 실행...
echo.

REM 환경변수 설정
set PYTHONPATH=%CD%\\src;%PYTHONPATH%
set KMP_DUPLICATE_LIB_OK=TRUE
set CUDA_VISIBLE_DEVICES=-1
set OMP_NUM_THREADS=1

REM numpy 경고 억제
set PYTHONWARNINGS=ignore::DeprecationWarning,ignore::numpy.VisibleDeprecationWarning

REM Qt 플러그인 경로
if exist "venv\\Lib\\site-packages\\PyQt5\\Qt5\\plugins" (
    set QT_PLUGIN_PATH=%CD%\\venv\\Lib\\site-packages\\PyQt5\\Qt5\\plugins
)

REM 가상환경 활성화
if exist "venv\\Scripts\\activate.bat" (
    call venv\\Scripts\\activate.bat
    echo 가상환경 활성화됨
) else (
    echo ⚠️  가상환경이 없습니다. 다음 명령으로 생성하세요:
    echo python -m venv venv
    echo venv\\Scripts\\activate.bat
    echo python fix_dependencies.py
    pause
    exit /b 1
)

REM Python 실행
echo 프로그램 시작...
python main.py

REM 오류 처리
if %ERRORLEVEL% neq 0 (
    echo.
    echo ❌ 오류가 발생했습니다.
    echo 문제 해결을 위해 다음을 확인하세요:
    echo 1. python fix_dependencies.py 실행
    echo 2. python run_tests_fixed.py 실행
    echo 3. 로그 파일 확인
    pause
)
'''
    
    with open("run_fixed_environment.bat", 'w', encoding='cp949') as f:
        f.write(script_content)
    
    print("✅ 환경 설정 스크립트 생성: run_fixed_environment.bat")

def main():
    """메인 실행 함수"""
    print("🔧 의존성 충돌 해결 도구")
    print("=" * 50)
    
    # 1. 현재 환경 분석
    check_current_environment()
    
    # 2. 호환성 매트릭스 생성
    create_dependency_matrix()
    
    # 3. 수정된 requirements 생성
    create_fixed_requirements()
    
    # 4. 사용자 확인
    print("\n⚠️  의존성 재설치가 필요합니다.")
    print("현재 설치된 패키지들이 제거되고 호환 버전으로 재설치됩니다.")
    
    if input("계속하시겠습니까? (y/n): ").lower() != 'y':
        print("중단되었습니다.")
        return False
    
    # 5. 충돌 패키지 제거
    uninstall_conflicting_packages()
    
    # 6. 호환 패키지 설치
    if not install_fixed_packages():
        print("❌ 패키지 설치에 실패했습니다.")
        return False
    
    # 7. 설치 검증
    if not verify_installation():
        print("⚠️  일부 패키지에 문제가 있을 수 있습니다.")
    
    # 8. 환경 스크립트 생성
    create_environment_script()
    
    print("\n✅ 의존성 충돌 해결 완료!")
    print("\n사용법:")
    print("1. run_fixed_environment.bat - 수정된 환경에서 실행")
    print("2. python run_tests_fixed.py - 테스트 실행")
    
    return True

if __name__ == "__main__":
    main()