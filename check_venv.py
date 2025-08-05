#!/usr/bin/env python3
"""
가상환경 패키지 상태 확인
"""
import sys
import os

print("=" * 60)
print("가상환경 상태 확인")
print("=" * 60)
print()

# Python 정보
print(f"Python 버전: {sys.version}")
print(f"Python 경로: {sys.executable}")
print()

# 가상환경 확인
if 'venv' in sys.executable:
    print("✅ 가상환경에서 실행 중")
else:
    print("⚠️ 시스템 Python에서 실행 중")
print()

# 필수 패키지 확인
print("패키지 설치 상태:")
print("-" * 40)

required_packages = {
    'numpy': '1.24.3',
    'cv2': '4.6.0.66',
    'PyQt5': '5.15.10',
    'mss': '9.0.1',
    'pyautogui': '0.9.54',
    'paddle': '2.5.2',
    'paddleocr': '2.7.0.3'
}

missing = []
for pkg_name, expected_version in required_packages.items():
    try:
        if pkg_name == 'cv2':
            import cv2
            module = cv2
        elif pkg_name == 'PyQt5':
            import PyQt5.QtCore
            module = PyQt5.QtCore
        else:
            module = __import__(pkg_name)
        
        version = getattr(module, '__version__', 'unknown')
        if pkg_name == 'PyQt5':
            version = PyQt5.QtCore.QT_VERSION_STR
        
        print(f"✅ {pkg_name}: {version}")
    except ImportError:
        print(f"❌ {pkg_name}: 설치 안됨 (필요: {expected_version})")
        missing.append(pkg_name)

if missing:
    print()
    print("=" * 60)
    print("⚠️ 설치가 필요한 패키지:")
    print("=" * 60)
    for pkg in missing:
        print(f"  - {pkg}")
    print()
    print("설치 방법:")
    print("  install_paddleocr_venv.bat 실행")
    print("또는:")
    print("  pip install paddlepaddle==2.5.2")
    print("  pip install paddleocr==2.7.0.3")
else:
    print()
    print("=" * 60)
    print("✅ 모든 패키지가 설치되어 있습니다!")
    print("=" * 60)
    print()
    print("PaddleOCR 테스트:")
    try:
        from paddleocr import PaddleOCR
        ocr = PaddleOCR(lang='korean')
        print("✅ PaddleOCR 초기화 성공")
    except Exception as e:
        print(f"❌ PaddleOCR 초기화 실패: {e}")