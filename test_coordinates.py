#!/usr/bin/env python3
"""좌표 확인 테스트"""
import pyautogui
import time

print("좌표 확인 테스트")
print("=" * 60)

# 테스트할 좌표
test_positions = [
    (1344, 712, "셀 하단 입력창 예상 위치"),
    (1152, 620, "셀 시작 위치"),
    (1536, 720, "셀 끝 위치")
]

print("각 위치에 마우스를 이동시킵니다.")
print("카카오톡 창을 확인하세요!\n")

for x, y, desc in test_positions:
    print(f"\n{desc}: ({x}, {y})")
    print("3초 후 이동...")
    time.sleep(3)
    
    pyautogui.moveTo(x, y, duration=0.5)
    print("이동 완료! 위치를 확인하세요.")
    
    # 시각적 표시를 위해 작은 원 그리기 (마우스 움직임)
    for i in range(4):
        pyautogui.moveRel(10, 0, duration=0.1)
        pyautogui.moveRel(0, 10, duration=0.1)
        pyautogui.moveRel(-10, 0, duration=0.1)
        pyautogui.moveRel(0, -10, duration=0.1)
    
    time.sleep(2)

print("\n" + "=" * 60)
print("테스트 완료")
print("\n확인 사항:")
print("1. 마우스가 카카오톡 입력창에 위치했나요?")
print("2. 좌표가 맞지 않다면 config.json의 input_box_offset 조정 필요")
print("3. 또는 셀 영역 설정이 잘못되었을 수 있음")