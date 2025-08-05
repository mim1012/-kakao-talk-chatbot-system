#!/usr/bin/env python3
"""자동화 실행 테스트"""
import sys
import os
import io
import time

# UTF-8 설정
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

sys.path.insert(0, 'src')

import pyautogui
import pyperclip

print("=" * 60)
print("자동화 기능 테스트")
print("=" * 60)

# pyautogui 설정 확인
print("\n1. PyAutoGUI 설정:")
print(f"   - FAILSAFE: {pyautogui.FAILSAFE}")
print(f"   - PAUSE: {pyautogui.PAUSE}")
print(f"   - 화면 크기: {pyautogui.size()}")

# 마우스 현재 위치
current_x, current_y = pyautogui.position()
print(f"\n2. 현재 마우스 위치: ({current_x}, {current_y})")

# 테스트 이동
print("\n3. 마우스 이동 테스트:")
test_x, test_y = 500, 500
print(f"   - 목표 위치: ({test_x}, {test_y})")
pyautogui.moveTo(test_x, test_y, duration=0.5)
new_x, new_y = pyautogui.position()
print(f"   - 이동 후 위치: ({new_x}, {new_y})")

if new_x == test_x and new_y == test_y:
    print("   ✅ 마우스 이동 성공")
else:
    print("   ❌ 마우스 이동 실패")

# 클립보드 테스트
print("\n4. 클립보드 테스트:")
test_text = "테스트 메시지"
pyperclip.copy(test_text)
copied = pyperclip.paste()
if copied == test_text:
    print("   ✅ 클립보드 복사/붙여넣기 성공")
else:
    print("   ❌ 클립보드 실패")

print("\n" + "=" * 60)

# config 로드 테스트
try:
    from core.config_manager import ConfigManager
    config = ConfigManager()
    input_offset = config.get('input_box_offset', {}).get('from_bottom', 8)
    print(f"5. 입력창 오프셋 설정: {input_offset}px")
except Exception as e:
    print(f"5. 설정 로드 오류: {e}")

print("=" * 60)