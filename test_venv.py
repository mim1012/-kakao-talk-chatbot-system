#!/usr/bin/env python3
"""
가상환경 테스트 스크립트
"""
import sys
import os

print("=" * 60)
print("가상환경 테스트")
print("=" * 60)
print()

# Python 정보
print(f"Python 버전: {sys.version}")
print(f"Python 경로: {sys.executable}")
print()

# 필수 패키지 확인
print("패키지 확인:")
print("-" * 40)

packages = [
    'numpy',
    'cv2',
    'PyQt5',
    'mss',
    'pyautogui',
    'paddleocr',
    'paddle'
]

for pkg in packages:
    try:
        module = __import__(pkg)
        version = getattr(module, '__version__', 'installed')
        print(f"✅ {pkg}: {version}")
    except ImportError as e:
        print(f"❌ {pkg}: 설치 안됨")

print()
print("테스트 완료!")