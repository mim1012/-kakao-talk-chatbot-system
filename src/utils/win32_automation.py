#!/usr/bin/env python3
"""Windows API를 직접 사용하는 자동화 모듈"""
import ctypes
import ctypes.wintypes
import time

try:
    import win32api
    import win32con
    import win32clipboard
    PYWIN32_AVAILABLE = True
except ImportError:
    PYWIN32_AVAILABLE = False
    print("⚠️ pywin32가 설치되지 않았습니다. pip install pywin32를 실행하세요.")

class Win32Automation:
    """Windows API를 사용한 마우스/키보드 자동화"""
    
    def __init__(self):
        self.user32 = ctypes.windll.user32
        self.kernel32 = ctypes.windll.kernel32
        
    def get_cursor_pos(self):
        """현재 마우스 커서 위치 반환"""
        point = ctypes.wintypes.POINT()
        self.user32.GetCursorPos(ctypes.byref(point))
        return point.x, point.y
        
    def set_cursor_pos(self, x, y):
        """마우스 커서 위치 설정"""
        self.user32.SetCursorPos(int(x), int(y))
        
    def mouse_click(self, x=None, y=None):
        """지정된 위치에서 마우스 클릭"""
        if x is not None and y is not None:
            self.set_cursor_pos(x, y)
            time.sleep(0.1)  # 이동 후 약간 대기
            
        # 현재 위치에서 클릭
        win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, 0, 0)
        time.sleep(0.05)
        win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, 0, 0)
        
    def send_keys(self, text):
        """텍스트 전송 (클립보드 사용)"""
        # 클립보드에 텍스트 복사
        win32clipboard.OpenClipboard()
        win32clipboard.EmptyClipboard()
        win32clipboard.SetClipboardText(text)
        win32clipboard.CloseClipboard()
        
        # Ctrl+V로 붙여넣기
        self.key_down(win32con.VK_CONTROL)
        self.key_press(ord('V'))
        self.key_up(win32con.VK_CONTROL)
        
    def key_press(self, vk_code):
        """키 누르기"""
        self.key_down(vk_code)
        time.sleep(0.05)
        self.key_up(vk_code)
        
    def key_down(self, vk_code):
        """키 누름"""
        win32api.keybd_event(vk_code, 0, 0, 0)
        
    def key_up(self, vk_code):
        """키 뗌"""
        win32api.keybd_event(vk_code, 0, win32con.KEYEVENTF_KEYUP, 0)
        
    def send_enter(self):
        """엔터키 전송"""
        self.key_press(win32con.VK_RETURN)

# 전역 인스턴스
automation = Win32Automation()