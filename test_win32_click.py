#!/usr/bin/env python3
"""Win32 API 클릭 테스트"""
import sys
sys.path.insert(0, '.')

from src.utils.direct_win32 import automation
import time

print("Direct Win32 API 클릭 테스트")
print("=" * 60)

# 현재 마우스 위치
x, y = automation.get_cursor_pos()
print(f"현재 마우스 위치: ({x}, {y})")

# 테스트 위치 (셀 하단 예상 위치)
test_x = 1344
test_y = 712

print(f"\n3초 후 ({test_x}, {test_y}) 위치로 이동 후 클릭합니다...")
print("카카오톡 창을 확인하세요!")

for i in range(3, 0, -1):
    print(f"{i}...")
    time.sleep(1)

# 마우스 이동
print(f"\n마우스 이동 중...")
automation.set_cursor_pos(test_x, test_y)
time.sleep(0.5)

# 현재 위치 확인
current_x, current_y = automation.get_cursor_pos()
print(f"이동 후 위치: ({current_x}, {current_y})")

if current_x == test_x and current_y == test_y:
    print("✅ 마우스가 정상적으로 이동했습니다!")
else:
    print("❌ 마우스가 이동하지 않았습니다!")

# 클릭
print("\n클릭 실행...")
automation.mouse_click()
print("클릭 완료!")

# 테스트 텍스트 입력
print("\n테스트 텍스트 입력...")
automation.send_keys("테스트 메시지 - Win32 API")
time.sleep(0.5)

print("\n엔터키 전송...")
automation.send_enter()

print("\n" + "=" * 60)
print("테스트 완료")
print("\n주의사항:")
print("1. 마우스가 실제로 움직였는지 확인하세요")
print("2. 텍스트가 입력되었는지 확인하세요")
print("3. 안 된다면 관리자 권한으로 실행해보세요")