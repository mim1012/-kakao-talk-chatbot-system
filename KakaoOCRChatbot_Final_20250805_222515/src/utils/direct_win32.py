#!/usr/bin/env python3
"""ctypes만 사용하는 Windows 자동화 모듈"""
import ctypes
import ctypes.wintypes
import time

# Windows API 상수
MOUSEEVENTF_MOVE = 0x0001
MOUSEEVENTF_LEFTDOWN = 0x0002
MOUSEEVENTF_LEFTUP = 0x0004
MOUSEEVENTF_ABSOLUTE = 0x8000

VK_CONTROL = 0x11
VK_SHIFT = 0x10
VK_RETURN = 0x0D
VK_V = 0x56
KEYEVENTF_KEYUP = 0x0002

class DirectWin32Automation:
    """ctypes를 통한 직접 Windows API 호출"""
    
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
        return True
        
    def mouse_click(self, x=None, y=None):
        """지정된 위치에서 마우스 클릭"""
        if x is not None and y is not None:
            self.set_cursor_pos(x, y)
            time.sleep(0.1)
            
        # 마우스 클릭 이벤트
        self.user32.mouse_event(MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
        time.sleep(0.05)
        self.user32.mouse_event(MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)
        return True
        
    def key_down(self, vk_code):
        """키 누름"""
        self.user32.keybd_event(vk_code, 0, 0, 0)
        
    def key_up(self, vk_code):
        """키 뗌"""
        self.user32.keybd_event(vk_code, 0, KEYEVENTF_KEYUP, 0)
        
    def key_press(self, vk_code):
        """키 누르기"""
        self.key_down(vk_code)
        time.sleep(0.05)
        self.key_up(vk_code)
        
    def send_text_via_clipboard(self, text):
        """클립보드를 통한 텍스트 전송"""
        # 클립보드 열기
        if self.user32.OpenClipboard(0):
            self.user32.EmptyClipboard()
            
            # 텍스트를 유니코드로 변환
            text_data = text.encode('utf-16-le')
            size = len(text_data) + 2
            
            # 글로벌 메모리 할당
            h_mem = self.kernel32.GlobalAlloc(0x0042, size)
            if h_mem:
                # 메모리 잠금
                p_mem = self.kernel32.GlobalLock(h_mem)
                if p_mem:
                    # 데이터 복사
                    ctypes.memmove(p_mem, text_data, len(text_data))
                    self.kernel32.GlobalUnlock(h_mem)
                    
                    # 클립보드에 설정
                    CF_UNICODETEXT = 13
                    self.user32.SetClipboardData(CF_UNICODETEXT, h_mem)
                    
            self.user32.CloseClipboard()
            time.sleep(0.1)
            
            # Ctrl+V로 붙여넣기
            self.key_down(VK_CONTROL)
            self.key_press(VK_V)
            self.key_up(VK_CONTROL)
            return True
        return False
        
    def send_keys(self, text):
        """텍스트 전송"""
        return self.send_text_via_clipboard(text)
        
    def send_enter(self):
        """엔터키 전송"""
        self.key_press(VK_RETURN)
        return True

# 전역 인스턴스
automation = DirectWin32Automation()