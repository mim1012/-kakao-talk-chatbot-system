#!/usr/bin/env python3
"""
새 가상환경 설치 테스트
"""
import sys
import os

# 로그 억제
os.environ['GLOG_minloglevel'] = '3'
os.environ['PADDLE_LOG_LEVEL'] = 'ERROR'

print("=" * 60)
print("새 가상환경 테스트")
print("=" * 60)
print()

# Python 버전
print(f"Python 버전: {sys.version}")
print(f"가상환경: {'venv' in sys.executable}")
print()

# 패키지 체크
packages = {
    'numpy': '1.26.0',
    'scipy': '1.11.4',
    'cv2': '4.8.1.78',
    'paddle': '2.5.2',
    'PyQt5.QtCore': '5.15',
    'mss': '9.0.1',
    'pyautogui': '0.9.54'
}

print("패키지 상태:")
print("-" * 40)

all_ok = True
for pkg, expected in packages.items():
    try:
        if pkg == 'cv2':
            import cv2
            version = cv2.__version__
        elif pkg == 'PyQt5.QtCore':
            import PyQt5.QtCore
            version = PyQt5.QtCore.QT_VERSION_STR
        else:
            module = __import__(pkg)
            version = module.__version__
        print(f"✅ {pkg:15} {version}")
    except ImportError:
        print(f"❌ {pkg:15} 설치 안됨")
        all_ok = False

# PaddleOCR 테스트
print("\nPaddleOCR 테스트:")
print("-" * 40)

try:
    from paddleocr import PaddleOCR
    print("✅ PaddleOCR import 성공")
    
    print("초기화 중...")
    ocr = PaddleOCR(lang='korean')
    print("✅ PaddleOCR 초기화 성공")
    
    # 간단한 테스트
    import numpy as np
    test_img = np.ones((100, 300, 3), dtype=np.uint8) * 255
    result = ocr.ocr(test_img)
    print("✅ OCR 실행 성공")
    
    print("\n" + "=" * 60)
    print("🎉 모든 설치가 완료되었습니다!")
    print("=" * 60)
    print("\n실행 명령:")
    print("  python main.py")
    print("\n또는:")
    print("  run_chatbot.bat")
    
except ImportError as e:
    print(f"❌ PaddleOCR import 실패: {e}")
    print("\n수동으로 다시 설치:")
    print("  pip install paddleocr==2.7.0.3 --no-deps")
    
except Exception as e:
    print(f"❌ 오류: {e}")

print()