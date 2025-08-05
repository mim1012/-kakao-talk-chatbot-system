#!/usr/bin/env python3
"""키보드만 사용하는 자동화 (원격에서도 작동)"""
import pyautogui
import pyperclip
import time

class KeyboardOnlyAutomation:
    """마우스 없이 키보드로만 자동화"""
    
    def __init__(self):
        # 원격에서도 키보드는 대부분 작동
        pyautogui.FAILSAFE = False
        
    def get_cursor_pos(self):
        """현재 위치 반환 (읽기는 가능)"""
        try:
            return pyautogui.position()
        except:
            return (0, 0)
            
    def set_cursor_pos(self, x, y):
        """마우스 이동 불가 - 대신 탭 키 사용"""
        print(f"⚠️ 원격 환경: 마우스 이동 불가 ({x}, {y})")
        return False
        
    def mouse_click(self, x=None, y=None):
        """클릭 대신 스페이스바 사용"""
        print("⚠️ 원격 환경: 클릭 대신 스페이스바 사용")
        pyautogui.press('space')
        return True
        
    def focus_kakaotalk(self):
        """카카오톡 창으로 포커스 이동"""
        # Alt+Tab으로 창 전환
        pyautogui.hotkey('alt', 'tab')
        time.sleep(0.5)
        
    def send_keys(self, text):
        """텍스트 전송"""
        pyperclip.copy(text)
        time.sleep(0.1)
        pyautogui.hotkey('ctrl', 'v')
        return True
        
    def send_enter(self):
        """엔터키 전송"""
        pyautogui.press('enter')
        return True
        
    def tab_to_input(self):
        """탭 키로 입력창으로 이동"""
        # 여러 번 탭을 눌러 입력창 찾기
        for _ in range(10):
            pyautogui.press('tab')
            time.sleep(0.1)

# 전역 인스턴스
automation = KeyboardOnlyAutomation()