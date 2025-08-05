#!/usr/bin/env python3
"""PyAutoGUI 설정 수정 테스트"""
import pyautogui
import time
import ctypes
import sys

print("PyAutoGUI 수정 테스트")
print("=" * 60)

# 1. PyAutoGUI 설정 변경
print("\n[PyAutoGUI 설정 변경]")
pyautogui.FAILSAFE = False  # 안전 모드 끄기
pyautogui.PAUSE = 0  # 일시 정지 없애기
print(f"FAILSAFE: {pyautogui.FAILSAFE}")
print(f"PAUSE: {pyautogui.PAUSE}")

# 2. 플랫폼별 백엔드 확인
print(f"\n[PyAutoGUI 백엔드]")
print(f"플랫폼: {sys.platform}")

# Windows에서 다른 방법 시도
if sys.platform == 'win32':
    # ctypes 직접 사용
    print("\n[방법 1: ctypes 직접 사용]")
    user32 = ctypes.windll.user32
    
    current_x, current_y = pyautogui.position()
    print(f"현재 위치: ({current_x}, {current_y})")
    
    target_x = current_x + 200
    target_y = current_y + 200
    print(f"목표 위치: ({target_x}, {target_y})")
    
    # ctypes로 이동
    user32.SetCursorPos(target_x, target_y)
    time.sleep(0.5)
    
    new_x, new_y = pyautogui.position()
    print(f"이동 후: ({new_x}, {new_y})")
    print(f"결과: {'✅ 성공' if new_x == target_x else '❌ 실패'}")

# 3. PyAutoGUI 다시 시도
print("\n[방법 2: PyAutoGUI moveTo]")
current_x, current_y = pyautogui.position()
print(f"현재 위치: ({current_x}, {current_y})")

target_x = 1344
target_y = 712
print(f"목표 위치: ({target_x}, {target_y})")

# duration 없이
pyautogui.moveTo(target_x, target_y)
time.sleep(0.5)

new_x, new_y = pyautogui.position()
print(f"이동 후: ({new_x}, {new_y})")
print(f"결과: {'✅ 성공' if new_x == target_x else '❌ 실패'}")

# 4. PyAutoGUI moveRel 시도
print("\n[방법 3: PyAutoGUI moveRel]")
print("상대적으로 100, 100 이동")
pyautogui.moveRel(100, 100)
time.sleep(0.5)

final_x, final_y = pyautogui.position()
print(f"최종 위치: ({final_x}, {final_y})")

# 5. 직접 _moveTo 호출
print("\n[방법 4: 내부 함수 직접 호출]")
try:
    # Windows 플랫폼 함수 직접 호출
    if hasattr(pyautogui, '_pyautogui_win'):
        pyautogui._pyautogui_win._moveTo(800, 600)
        print("내부 함수 호출 성공")
    else:
        print("내부 함수 없음")
except Exception as e:
    print(f"오류: {e}")

# 6. 마우스 이벤트 직접 발생
print("\n[방법 5: mouse_event 사용]")
MOUSEEVENTF_ABSOLUTE = 0x8000
MOUSEEVENTF_MOVE = 0x0001

screen_width = user32.GetSystemMetrics(0)
screen_height = user32.GetSystemMetrics(1)

# 절대 좌표 계산
abs_x = int(1344 * 65535 / screen_width)
abs_y = int(712 * 65535 / screen_height)

user32.mouse_event(MOUSEEVENTF_ABSOLUTE | MOUSEEVENTF_MOVE, abs_x, abs_y, 0, 0)

print("\n" + "=" * 60)
print("테스트 완료")
print("\n추가 확인사항:")
print("1. 게임이나 전체화면 앱이 실행 중인가?")
print("2. 원격 데스크톱 설정에서 '로컬 리소스' > '로컬 장치 및 리소스' 확인")
print("3. 디스플레이 배율이 100%가 아닌가?")