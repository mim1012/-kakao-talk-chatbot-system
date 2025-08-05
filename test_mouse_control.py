#!/usr/bin/env python3
"""다양한 마우스 제어 방법 테스트"""
import ctypes
import time
import os

print("마우스 제어 테스트")
print("=" * 60)

# 1. ctypes로 직접 SetCursorPos 호출
print("\n[방법 1] ctypes.windll.user32.SetCursorPos")
user32 = ctypes.windll.user32

# 현재 위치
class POINT(ctypes.Structure):
    _fields_ = [("x", ctypes.c_long), ("y", ctypes.c_long)]

pt = POINT()
user32.GetCursorPos(ctypes.byref(pt))
print(f"현재 위치: ({pt.x}, {pt.y})")

# 이동
new_x, new_y = 800, 600
print(f"이동 목표: ({new_x}, {new_y})")
result = user32.SetCursorPos(new_x, new_y)
print(f"SetCursorPos 결과: {result}")

time.sleep(0.5)
user32.GetCursorPos(ctypes.byref(pt))
print(f"이동 후 위치: ({pt.x}, {pt.y})")
print(f"성공 여부: {'✅' if pt.x == new_x and pt.y == new_y else '❌'}")

# 2. mouse_event 사용
print("\n[방법 2] mouse_event (상대 이동)")
MOUSEEVENTF_MOVE = 0x0001

# 상대적으로 100픽셀 이동
user32.mouse_event(MOUSEEVENTF_MOVE, 100, 100, 0, 0)
time.sleep(0.5)

user32.GetCursorPos(ctypes.byref(pt))
print(f"상대 이동 후 위치: ({pt.x}, {pt.y})")

# 3. SendInput 사용
print("\n[방법 3] SendInput (절대 위치)")

# INPUT 구조체들
class MOUSEINPUT(ctypes.Structure):
    _fields_ = [
        ("dx", ctypes.c_long),
        ("dy", ctypes.c_long),
        ("mouseData", ctypes.c_ulong),
        ("dwFlags", ctypes.c_ulong),
        ("time", ctypes.c_ulong),
        ("dwExtraInfo", ctypes.POINTER(ctypes.c_ulong))
    ]

class INPUT(ctypes.Structure):
    class _INPUT(ctypes.Union):
        _fields_ = [("mi", MOUSEINPUT)]
    _anonymous_ = ("_input",)
    _fields_ = [("type", ctypes.c_ulong), ("_input", _INPUT)]

MOUSEEVENTF_ABSOLUTE = 0x8000
INPUT_MOUSE = 0

# 화면 크기
screen_width = user32.GetSystemMetrics(0)
screen_height = user32.GetSystemMetrics(1)
print(f"화면 크기: {screen_width}x{screen_height}")

# 절대 좌표 계산 (1344, 712)
target_x, target_y = 1344, 712
abs_x = int(target_x * 65536 / screen_width)
abs_y = int(target_y * 65536 / screen_height)

print(f"목표 위치: ({target_x}, {target_y})")
print(f"절대 좌표: ({abs_x}, {abs_y})")

# INPUT 생성
extra = ctypes.c_ulong(0)
input_struct = INPUT()
input_struct.type = INPUT_MOUSE
input_struct.mi = MOUSEINPUT(
    abs_x, abs_y, 0,
    MOUSEEVENTF_MOVE | MOUSEEVENTF_ABSOLUTE,
    0, ctypes.pointer(extra)
)

# SendInput 호출
result = user32.SendInput(1, ctypes.pointer(input_struct), ctypes.sizeof(input_struct))
print(f"SendInput 결과: {result}")

time.sleep(0.5)
user32.GetCursorPos(ctypes.byref(pt))
print(f"SendInput 후 위치: ({pt.x}, {pt.y})")

# 4. 프로세스 권한 확인
print("\n[권한 정보]")
print(f"프로세스 ID: {os.getpid()}")
print(f"관리자 권한: {'예' if ctypes.windll.shell32.IsUserAnAdmin() else '아니오'}")

# 5. 시스템 정보
print("\n[시스템 정보]")
print(f"DPI Aware: {user32.IsProcessDPIAware()}")

print("\n" + "=" * 60)
print("테스트 완료")
print("\n권장사항:")
print("1. 관리자 권한으로 실행")
print("2. 백신/보안 프로그램 일시 중지")
print("3. 다른 자동화 도구와 충돌 확인")