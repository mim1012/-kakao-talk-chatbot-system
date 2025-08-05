#!/usr/bin/env python3
"""SendInput API 테스트"""
import sys
sys.path.insert(0, '.')

from src.utils.sendinput_automation import automation
import time
import ctypes

print("SendInput API 테스트")
print("=" * 60)

# 관리자 권한 확인
def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

print(f"관리자 권한: {'예' if is_admin() else '아니오'}")
if not is_admin():
    print("⚠️ 관리자 권한으로 실행을 권장합니다!")

# 화면 크기
print(f"화면 크기: {automation.screen_width}x{automation.screen_height}")

# 현재 마우스 위치
x, y = automation.get_cursor_pos()
print(f"현재 마우스 위치: ({x}, {y})")

# 테스트 1: 화면 중앙으로 이동
test_x = automation.screen_width // 2
test_y = automation.screen_height // 2

print(f"\n[테스트 1] 3초 후 화면 중앙({test_x}, {test_y})으로 이동...")
for i in range(3, 0, -1):
    print(f"{i}...")
    time.sleep(1)

automation.set_cursor_pos(test_x, test_y)
time.sleep(0.5)

new_x, new_y = automation.get_cursor_pos()
print(f"이동 후 위치: ({new_x}, {new_y})")
print(f"결과: {'✅ 성공' if new_x == test_x and new_y == test_y else '❌ 실패'}")

# 테스트 2: 카카오톡 예상 위치로 이동
test_x2 = 1344
test_y2 = 712

print(f"\n[테스트 2] 3초 후 카카오톡 위치({test_x2}, {test_y2})로 이동...")
for i in range(3, 0, -1):
    print(f"{i}...")
    time.sleep(1)

automation.set_cursor_pos(test_x2, test_y2)
time.sleep(0.5)

new_x2, new_y2 = automation.get_cursor_pos()
print(f"이동 후 위치: ({new_x2}, {new_y2})")
print(f"결과: {'✅ 성공' if new_x2 == test_x2 and new_y2 == test_y2 else '❌ 실패'}")

# 테스트 3: 클릭
print(f"\n[테스트 3] 현재 위치에서 클릭...")
automation.mouse_click()
print("클릭 완료!")

print("\n" + "=" * 60)
print("테스트 완료")
print("\n해결 방법:")
print("1. 관리자 권한으로 실행: 우클릭 > '관리자 권한으로 실행'")
print("2. Windows Defender 실시간 보호 일시 중지")
print("3. UAC 설정 낮추기 (권장하지 않음)")
print("4. 다른 자동화 프로그램이 실행 중인지 확인")