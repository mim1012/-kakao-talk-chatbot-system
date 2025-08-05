#!/usr/bin/env python3
"""PyAutoGUI 클릭 테스트"""
import pyautogui
import time

print("PyAutoGUI 클릭 테스트")
print("=" * 60)

# 현재 마우스 위치
x, y = pyautogui.position()
print(f"현재 마우스 위치: ({x}, {y})")

# 5초 후 클릭 (마우스를 원하는 위치에 놓으세요)
print("\n5초 후 현재 마우스 위치를 클릭합니다...")
print("원하는 위치에 마우스를 놓으세요!")

for i in range(5, 0, -1):
    print(f"{i}...")
    time.sleep(1)

# 현재 위치 클릭
x, y = pyautogui.position()
print(f"\n클릭 위치: ({x}, {y})")
pyautogui.click(x, y)
print("클릭 완료!")

# 테스트 텍스트 입력
print("\n테스트 텍스트 입력...")
pyautogui.typewrite("Test message from PyAutoGUI", interval=0.1)
print("입력 완료!")

print("\n" + "=" * 60)
print("테스트 완료")