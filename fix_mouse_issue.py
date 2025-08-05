#!/usr/bin/env python3
"""마우스 문제 해결 스크립트"""
import ctypes
import sys
import os

print("마우스 제어 문제 해결")
print("=" * 60)

# 1. DPI Aware 설정
print("\n[1] DPI Aware 설정 중...")
try:
    # Windows 8.1 이상
    ctypes.windll.shcore.SetProcessDpiAwareness(2)  # PROCESS_PER_MONITOR_DPI_AWARE
    print("✅ DPI Aware 설정 완료 (Per-Monitor)")
except:
    try:
        # Windows Vista 이상
        ctypes.windll.user32.SetProcessDPIAware()
        print("✅ DPI Aware 설정 완료 (System)")
    except:
        print("❌ DPI Aware 설정 실패")

# 2. 문제 프로세스 확인
print("\n[2] 문제가 될 수 있는 프로세스:")
try:
    import psutil
    problematic = ['ICanRecorder.exe', 'obs64.exe', 'obs32.exe', 'bandicam.exe', 'fraps.exe']
    found = []
    for proc in psutil.process_iter(['name', 'pid']):
        if proc.info['name'] in problematic:
            found.append(f"- {proc.info['name']} (PID: {proc.info['pid']})")
    
    if found:
        print("다음 프로그램이 마우스 제어를 방해할 수 있습니다:")
        for p in found:
            print(p)
        print("\n💡 해결: 이 프로그램들을 종료하고 다시 시도하세요")
    else:
        print("✅ 문제 프로세스 없음")
except:
    pass

# 3. PyAutoGUI 재초기화
print("\n[3] PyAutoGUI 재초기화...")
import pyautogui

# 설정 변경
pyautogui.FAILSAFE = False
pyautogui.PAUSE = 0
pyautogui.DARWIN_CATCH_UP_TIME = 0  # Mac용이지만 설정

# Windows 특별 설정
if sys.platform == 'win32':
    # 직접 ctypes 사용하도록 강제
    import pyautogui._pyautogui_win as platformModule
    
    # 원래 moveTo 백업
    original_moveTo = platformModule._moveTo
    
    # ctypes 버전으로 교체
    def fixed_moveTo(x, y):
        ctypes.windll.user32.SetCursorPos(int(x), int(y))
    
    # 함수 교체
    platformModule._moveTo = fixed_moveTo
    print("✅ PyAutoGUI 함수 패치 완료")

# 4. 테스트
print("\n[4] 수정된 PyAutoGUI 테스트...")
current = pyautogui.position()
print(f"현재 위치: {current}")

test_x, test_y = 1344, 712
print(f"이동 목표: ({test_x}, {test_y})")

pyautogui.moveTo(test_x, test_y)
new_pos = pyautogui.position()
print(f"이동 후: {new_pos}")

if new_pos[0] == test_x and new_pos[1] == test_y:
    print("✅ PyAutoGUI 마우스 이동 성공!")
else:
    print("❌ 여전히 문제가 있습니다")

print("\n" + "=" * 60)
print("권장 조치:")
print("1. ICanRecorder.exe 종료")
print("2. 이 스크립트를 main.py 시작 부분에 추가")
print("3. 관리자 권한으로 실행 권장")