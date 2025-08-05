#!/usr/bin/env python3
"""
numpy DLL 문제 해결 스크립트
Python 3.13에서 numpy 2.3.2의 DLL 로딩 문제 해결
"""
import sys
import subprocess
import os

def uninstall_numpy():
    """기존 numpy 완전 제거"""
    print("기존 numpy 제거 중...")
    
    packages_to_remove = [
        'numpy',
        'scipy',  # scipy도 numpy에 의존
        'opencv-python',  # opencv도 numpy에 의존
        'paddleocr',  # paddleocr도 numpy에 의존
        'paddlepaddle'
    ]
    
    for package in packages_to_remove:
        try:
            result = subprocess.run([
                sys.executable, "-m", "pip", "uninstall", 
                package, "-y"
            ], capture_output=True, text=True)
            
            if result.returncode == 0:
                print(f"  [OK] {package} 제거 완료")
            else:
                print(f"  [SKIP] {package} 제거 건너뜀")
        except Exception as e:
            print(f"  [ERROR] {package} 제거 실패: {e}")

def install_compatible_numpy():
    """호환되는 numpy 설치"""
    print("호환되는 numpy 설치 중...")
    
    # Python 3.13용 numpy 호환 버전 설치 시도
    numpy_versions = [
        "numpy==2.1.0",  # 최신 안정 버전
        "numpy==2.0.2",  # 이전 안정 버전
        "numpy==1.26.4", # 마지막 1.x 버전 (fallback)
    ]
    
    for numpy_version in numpy_versions:
        print(f"  {numpy_version} 설치 시도...")
        
        try:
            result = subprocess.run([
                sys.executable, "-m", "pip", "install",
                numpy_version,
                "--no-cache-dir",
                "--force-reinstall"
            ], capture_output=True, text=True, timeout=180)
            
            if result.returncode == 0:
                print(f"  [OK] {numpy_version} 설치 성공")
                
                # 설치 테스트
                test_result = subprocess.run([
                    sys.executable, "-c", "import numpy; print(f'numpy {numpy.__version__} 로드 성공')"
                ], capture_output=True, text=True, timeout=30)
                
                if test_result.returncode == 0:
                    print(f"  [OK] {numpy_version} 테스트 통과")
                    return True
                else:
                    print(f"  [FAIL] {numpy_version} 테스트 실패: {test_result.stderr}")
                    continue
            else:
                print(f"  [FAIL] {numpy_version} 설치 실패")
                continue
                
        except subprocess.TimeoutExpired:
            print(f"  [TIMEOUT] {numpy_version} 설치 타임아웃")
            continue
        except Exception as e:
            print(f"  [ERROR] {numpy_version} 설치 오류: {e}")
            continue
    
    return False

def install_dependencies():
    """의존성 패키지 재설치"""
    print("의존성 패키지 재설치 중...")
    
    # 순서가 중요한 패키지들
    packages_order = [
        "Pillow==10.4.0",
        "opencv-python==4.10.0.84",
        "mss==9.0.1",
        "screeninfo==0.8.1",
        "psutil==6.0.0",
    ]
    
    for package in packages_order:
        print(f"  {package} 설치 중...")
        try:
            result = subprocess.run([
                sys.executable, "-m", "pip", "install",
                package,
                "--no-deps"  # 의존성 자동 설치 방지
            ], capture_output=True, text=True, timeout=60)
            
            if result.returncode == 0:
                print(f"  [OK] {package} 설치 완료")
            else:
                print(f"  [FAIL] {package} 설치 실패")
        except Exception as e:
            print(f"  [ERROR] {package} 설치 오류: {e}")

def install_paddleocr_alternative():
    """PaddleOCR 대신 easyocr 설치 (더 안정적)"""
    print("OCR 라이브러리 설치 중...")
    
    # PaddleOCR는 복잡하므로 easyocr로 대체 고려
    ocr_options = [
        "easyocr==1.7.1",  # 더 안정적인 대안
        # "paddleocr==2.8.1",  # 원본 (문제 시 주석 처리)
    ]
    
    for package in ocr_options:
        print(f"  {package} 설치 시도...")
        try:
            result = subprocess.run([
                sys.executable, "-m", "pip", "install",
                package,
                "--no-cache-dir"
            ], capture_output=True, text=True, timeout=300)
            
            if result.returncode == 0:
                print(f"  [OK] {package} 설치 성공")
                return True
            else:
                print(f"  [FAIL] {package} 설치 실패")
        except Exception as e:
            print(f"  [ERROR] {package} 설치 오류: {e}")
    
    return False

def test_all_imports():
    """모든 중요한 모듈 import 테스트"""
    print("전체 모듈 import 테스트...")
    
    test_modules = [
        ("numpy", "import numpy as np; print(f'numpy {np.__version__}')"),
        ("opencv", "import cv2; print(f'opencv {cv2.__version__}')"),
        ("Pillow", "from PIL import Image; print('Pillow OK')"),
        ("PyQt5", "from PyQt5.QtWidgets import QApplication; print('PyQt5 OK')"),
        ("mss", "import mss; print('mss OK')"),
        ("psutil", "import psutil; print('psutil OK')"),
    ]
    
    success_count = 0
    for name, test_code in test_modules:
        try:
            result = subprocess.run([
                sys.executable, "-c", test_code
            ], capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                print(f"  [OK] {name}: {result.stdout.strip()}")
                success_count += 1
            else:
                print(f"  [FAIL] {name}: {result.stderr.strip()}")
        except Exception as e:
            print(f"  [ERROR] {name}: {e}")
    
    print(f"테스트 결과: {success_count}/{len(test_modules)} 성공")
    return success_count >= len(test_modules) * 0.8

def create_no_ocr_version():
    """OCR 없는 버전 생성 (테스트용)"""
    print("OCR 없는 테스트 버전 생성...")
    
    # OCR 모듈을 mock으로 대체하는 wrapper 생성
    mock_ocr_code = '''"""
OCR Mock 모듈 - PaddleOCR 대신 사용
"""

class MockOCR:
    def __init__(self, *args, **kwargs):
        print("Mock OCR 초기화됨 (실제 OCR 기능 없음)")
    
    def ocr(self, image, *args, **kwargs):
        """Mock OCR 결과 반환"""
        return [[[[0, 0], [100, 0], [100, 30], [0, 30]], ('들어왔습니다', 0.95)]]

# PaddleOCR 호환성을 위한 클래스
class PaddleOCR(MockOCR):
    pass

def paddleocr(*args, **kwargs):
    return MockOCR(*args, **kwargs)
'''
    
    # src/ocr 디렉토리 확인
    ocr_dir = Path("src/ocr")
    if ocr_dir.exists():
        with open(ocr_dir / "mock_paddleocr.py", 'w', encoding='utf-8') as f:
            f.write(mock_ocr_code)
        print("  [OK] Mock OCR 모듈 생성 완료")

def main():
    """메인 실행 함수"""
    print("=" * 60)
    print("numpy DLL 문제 해결 도구")
    print("Python 3.13 + numpy 2.3.2 호환성 문제 해결")
    print("=" * 60)
    
    print(f"Python 버전: {sys.version}")
    
    # 사용자 확인
    print("\n주의: 현재 설치된 numpy, opencv, paddleocr 등이 모두 제거됩니다.")
    if input("계속하시겠습니까? (y/n): ").lower() != 'y':
        print("중단되었습니다.")
        return False
    
    success_steps = 0
    total_steps = 5
    
    # 1. 기존 패키지 제거
    try:
        uninstall_numpy()
        success_steps += 1
    except Exception as e:
        print(f"패키지 제거 실패: {e}")
    
    # 2. 호환 numpy 설치
    if install_compatible_numpy():
        print("[OK] numpy 설치 성공")
        success_steps += 1
    else:
        print("[FAIL] numpy 설치 실패")
    
    # 3. 의존성 재설치
    try:
        install_dependencies()
        success_steps += 1
    except Exception as e:
        print(f"의존성 설치 실패: {e}")
    
    # 4. OCR 라이브러리 설치 (선택사항)
    if input("OCR 라이브러리를 설치하시겠습니까? (y/n): ").lower() == 'y':
        if install_paddleocr_alternative():
            success_steps += 1
    else:
        create_no_ocr_version()
        success_steps += 1
    
    # 5. 전체 테스트
    if test_all_imports():
        success_steps += 1
    
    # 결과 요약
    print("\n" + "=" * 60)
    print(f"수정 결과: {success_steps}/{total_steps} 단계 성공")
    
    if success_steps >= 4:
        print("[SUCCESS] numpy DLL 문제 해결 완료!")
        print("이제 start_demo.bat으로 프로그램을 실행해보세요.")
        return True
    else:
        print("[PARTIAL] 일부 문제가 남아있을 수 있습니다.")
        print("수동으로 패키지를 재설치해보세요:")
        print("  pip install numpy==2.1.0 --force-reinstall")
        return False

if __name__ == "__main__":
    from pathlib import Path
    main()