#!/usr/bin/env python3
"""SendInput API를 사용하는 Windows 자동화 모듈"""
import ctypes
import ctypes.wintypes
import time

# 구조체 정의
class MOUSEINPUT(ctypes.Structure):
    _fields_ = [("dx", ctypes.c_long),
                ("dy", ctypes.c_long),
                ("mouseData", ctypes.c_ulong),
                ("dwFlags", ctypes.c_ulong),
                ("time", ctypes.c_ulong),
                ("dwExtraInfo", ctypes.POINTER(ctypes.c_ulong))]

class KEYBDINPUT(ctypes.Structure):
    _fields_ = [("wVk", ctypes.c_ushort),
                ("wScan", ctypes.c_ushort),
                ("dwFlags", ctypes.c_ulong),
                ("time", ctypes.c_ulong),
                ("dwExtraInfo", ctypes.POINTER(ctypes.c_ulong))]

class HARDWAREINPUT(ctypes.Structure):
    _fields_ = [("uMsg", ctypes.c_ulong),
                ("wParamL", ctypes.c_ushort),
                ("wParamH", ctypes.c_ushort)]

class INPUT_UNION(ctypes.Union):
    _fields_ = [("mi", MOUSEINPUT),
                ("ki", KEYBDINPUT),
                ("hi", HARDWAREINPUT)]

class INPUT(ctypes.Structure):
    _fields_ = [("type", ctypes.c_ulong),
                ("ii", INPUT_UNION)]

# 상수
INPUT_MOUSE = 0
INPUT_KEYBOARD = 1

MOUSEEVENTF_MOVE = 0x0001
MOUSEEVENTF_LEFTDOWN = 0x0002
MOUSEEVENTF_LEFTUP = 0x0004
MOUSEEVENTF_ABSOLUTE = 0x8000

VK_CONTROL = 0x11
VK_RETURN = 0x0D
VK_V = 0x56
KEYEVENTF_KEYUP = 0x0002

class SendInputAutomation:
    """SendInput API를 사용한 자동화"""
    
    def __init__(self):
        self.user32 = ctypes.windll.user32
        self.kernel32 = ctypes.windll.kernel32
        
        # 화면 크기 가져오기
        self.screen_width = self.user32.GetSystemMetrics(0)
        self.screen_height = self.user32.GetSystemMetrics(1)
        
    def get_cursor_pos(self):
        """현재 마우스 커서 위치 반환"""
        point = ctypes.wintypes.POINT()
        self.user32.GetCursorPos(ctypes.byref(point))
        return point.x, point.y
        
    def set_cursor_pos(self, x, y):
        """SendInput으로 마우스 이동"""
        # 절대 좌표로 변환 (0-65535 범위)
        absolute_x = int(x * 65536 / self.screen_width)
        absolute_y = int(y * 65536 / self.screen_height)
        
        # INPUT 구조체 생성
        extra = ctypes.c_ulong(0)
        ii = INPUT_UNION()
        ii.mi = MOUSEINPUT(
            dx=absolute_x,
            dy=absolute_y,
            mouseData=0,
            dwFlags=MOUSEEVENTF_MOVE | MOUSEEVENTF_ABSOLUTE,
            time=0,
            dwExtraInfo=ctypes.pointer(extra)
        )
        
        x_input = INPUT(type=INPUT_MOUSE, ii=ii)
        
        # SendInput 호출
        self.user32.SendInput(1, ctypes.pointer(x_input), ctypes.sizeof(x_input))
        return True
        
    def mouse_click(self, x=None, y=None):
        """마우스 클릭"""
        if x is not None and y is not None:
            self.set_cursor_pos(x, y)
            time.sleep(0.1)
            
        # 클릭 이벤트
        extra = ctypes.c_ulong(0)
        
        # 마우스 다운
        ii_down = INPUT_UNION()
        ii_down.mi = MOUSEINPUT(0, 0, 0, MOUSEEVENTF_LEFTDOWN, 0, ctypes.pointer(extra))
        down_input = INPUT(type=INPUT_MOUSE, ii=ii_down)
        
        # 마우스 업
        ii_up = INPUT_UNION()
        ii_up.mi = MOUSEINPUT(0, 0, 0, MOUSEEVENTF_LEFTUP, 0, ctypes.pointer(extra))
        up_input = INPUT(type=INPUT_MOUSE, ii=ii_up)
        
        # SendInput 호출
        self.user32.SendInput(1, ctypes.pointer(down_input), ctypes.sizeof(down_input))
        time.sleep(0.05)
        self.user32.SendInput(1, ctypes.pointer(up_input), ctypes.sizeof(up_input))
        return True
        
    def key_press(self, vk_code):
        """키 누르기"""
        extra = ctypes.c_ulong(0)
        
        # 키 다운
        ii_down = INPUT_UNION()
        ii_down.ki = KEYBDINPUT(vk_code, 0, 0, 0, ctypes.pointer(extra))
        down_input = INPUT(type=INPUT_KEYBOARD, ii=ii_down)
        
        # 키 업
        ii_up = INPUT_UNION()
        ii_up.ki = KEYBDINPUT(vk_code, 0, KEYEVENTF_KEYUP, 0, ctypes.pointer(extra))
        up_input = INPUT(type=INPUT_KEYBOARD, ii=ii_up)
        
        # SendInput 호출
        self.user32.SendInput(1, ctypes.pointer(down_input), ctypes.sizeof(down_input))
        time.sleep(0.05)
        self.user32.SendInput(1, ctypes.pointer(up_input), ctypes.sizeof(up_input))
        
    def send_keys(self, text):
        """클립보드를 통한 텍스트 전송"""
        # pyperclip 사용 가능한 경우
        try:
            import pyperclip
            pyperclip.copy(text)
        except:
            # 직접 클립보드 조작
            if self.user32.OpenClipboard(0):
                self.user32.EmptyClipboard()
                
                text_data = text.encode('utf-16-le')
                size = len(text_data) + 2
                
                h_mem = self.kernel32.GlobalAlloc(0x0042, size)
                if h_mem:
                    p_mem = self.kernel32.GlobalLock(h_mem)
                    if p_mem:
                        ctypes.memmove(p_mem, text_data, len(text_data))
                        self.kernel32.GlobalUnlock(h_mem)
                        
                        CF_UNICODETEXT = 13
                        self.user32.SetClipboardData(CF_UNICODETEXT, h_mem)
                        
                self.user32.CloseClipboard()
        
        time.sleep(0.1)
        
        # Ctrl+V
        extra = ctypes.c_ulong(0)
        
        # Ctrl 다운
        ctrl_down = INPUT_UNION()
        ctrl_down.ki = KEYBDINPUT(VK_CONTROL, 0, 0, 0, ctypes.pointer(extra))
        ctrl_down_input = INPUT(type=INPUT_KEYBOARD, ii=ctrl_down)
        
        # V 다운
        v_down = INPUT_UNION()
        v_down.ki = KEYBDINPUT(VK_V, 0, 0, 0, ctypes.pointer(extra))
        v_down_input = INPUT(type=INPUT_KEYBOARD, ii=v_down)
        
        # V 업
        v_up = INPUT_UNION()
        v_up.ki = KEYBDINPUT(VK_V, 0, KEYEVENTF_KEYUP, 0, ctypes.pointer(extra))
        v_up_input = INPUT(type=INPUT_KEYBOARD, ii=v_up)
        
        # Ctrl 업
        ctrl_up = INPUT_UNION()
        ctrl_up.ki = KEYBDINPUT(VK_CONTROL, 0, KEYEVENTF_KEYUP, 0, ctypes.pointer(extra))
        ctrl_up_input = INPUT(type=INPUT_KEYBOARD, ii=ctrl_up)
        
        # SendInput 호출
        self.user32.SendInput(1, ctypes.pointer(ctrl_down_input), ctypes.sizeof(ctrl_down_input))
        self.user32.SendInput(1, ctypes.pointer(v_down_input), ctypes.sizeof(v_down_input))
        time.sleep(0.05)
        self.user32.SendInput(1, ctypes.pointer(v_up_input), ctypes.sizeof(v_up_input))
        self.user32.SendInput(1, ctypes.pointer(ctrl_up_input), ctypes.sizeof(ctrl_up_input))
        
        return True
        
    def send_enter(self):
        """엔터키 전송"""
        self.key_press(VK_RETURN)
        return True

# 전역 인스턴스
automation = SendInputAutomation()