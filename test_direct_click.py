#!/usr/bin/env python3
"""직접 클릭 테스트"""
import pyautogui
import time
import ctypes

print("직접 클릭 테스트")
print("=" * 60)

# 관리자 권한 확인
def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

print(f"관리자 권한: {'예' if is_admin() else '아니오'}")
print(f"PyAutoGUI 버전: {pyautogui.__version__}")

# 현재 설정
print(f"\nPyAutoGUI 설정:")
print(f"FAILSAFE: {pyautogui.FAILSAFE}")
print(f"PAUSE: {pyautogui.PAUSE}")

# 화면 크기
screen_width, screen_height = pyautogui.size()
print(f"화면 크기: {screen_width}x{screen_height}")

# 테스트 클릭 위치 (화면 중앙)
test_x = screen_width // 2
test_y = screen_height // 2

print(f"\n3초 후 화면 중앙({test_x}, {test_y})을 클릭합니다...")
print("마우스가 움직이는지 확인하세요!")

for i in range(3, 0, -1):
    print(f"{i}...")
    time.sleep(1)

# 마우스 이동
print("\n마우스 이동 중...")
pyautogui.moveTo(test_x, test_y, duration=1.0)
print("이동 완료")

# 클릭
print("\n클릭 실행...")
pyautogui.click(test_x, test_y)
print("클릭 완료")

# 현재 위치 확인
current_x, current_y = pyautogui.position()
print(f"\n현재 마우스 위치: ({current_x}, {current_y})")

if current_x == test_x and current_y == test_y:
    print("✅ 마우스가 정상적으로 이동했습니다")
else:
    print("❌ 마우스가 이동하지 않았습니다")
    print("\n가능한 해결책:")
    print("1. 관리자 권한으로 실행")
    print("2. Windows Defender 또는 백신 프로그램 확인")
    print("3. pyautogui 재설치: pip uninstall pyautogui && pip install pyautogui")

print("\n" + "=" * 60)