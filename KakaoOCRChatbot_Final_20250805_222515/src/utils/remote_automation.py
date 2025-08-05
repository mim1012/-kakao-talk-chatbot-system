#!/usr/bin/env python3
"""원격 데스크톱 환경을 위한 자동화 모듈"""
import time
import subprocess
import os

class RemoteAutomation:
    """원격 환경에서 작동하는 자동화 (AHK 스크립트 사용)"""
    
    def __init__(self):
        self.ahk_path = None
        self._check_ahk()
        
    def _check_ahk(self):
        """AutoHotkey 설치 확인"""
        # 일반적인 AHK 설치 경로들
        possible_paths = [
            r"C:\Program Files\AutoHotkey\AutoHotkey.exe",
            r"C:\Program Files (x86)\AutoHotkey\AutoHotkey.exe",
            r"C:\Program Files\AutoHotkey\v2\AutoHotkey64.exe",
            r"C:\Program Files\AutoHotkey\v1.1\AutoHotkeyU64.exe"
        ]
        
        for path in possible_paths:
            if os.path.exists(path):
                self.ahk_path = path
                print(f"✅ AutoHotkey 발견: {path}")
                return
                
    def get_cursor_pos(self):
        """마우스 위치는 PyAutoGUI로 읽기 (읽기는 가능)"""
        try:
            import pyautogui
            return pyautogui.position()
        except:
            return (0, 0)
            
    def set_cursor_pos(self, x, y):
        """AHK 스크립트로 마우스 이동"""
        if not self.ahk_path:
            print("❌ AutoHotkey가 설치되지 않았습니다")
            return False
            
        script = f"""
        CoordMode, Mouse, Screen
        MouseMove, {x}, {y}, 0
        ExitApp
        """
        
        # 임시 스크립트 파일 생성
        script_file = "temp_move.ahk"
        with open(script_file, 'w') as f:
            f.write(script)
            
        # AHK 실행
        try:
            subprocess.run([self.ahk_path, script_file], check=True)
            os.remove(script_file)
            return True
        except:
            return False
            
    def mouse_click(self, x=None, y=None):
        """AHK 스크립트로 클릭"""
        if not self.ahk_path:
            return False
            
        if x and y:
            script = f"""
            CoordMode, Mouse, Screen
            MouseMove, {x}, {y}, 0
            Sleep, 100
            Click
            ExitApp
            """
        else:
            script = """
            Click
            ExitApp
            """
            
        script_file = "temp_click.ahk"
        with open(script_file, 'w') as f:
            f.write(script)
            
        try:
            subprocess.run([self.ahk_path, script_file], check=True)
            os.remove(script_file)
            return True
        except:
            return False
            
    def send_keys(self, text):
        """AHK로 텍스트 전송"""
        if not self.ahk_path:
            # 대체 방법: pyperclip + pyautogui
            try:
                import pyperclip
                import pyautogui
                pyperclip.copy(text)
                time.sleep(0.1)
                # pyautogui는 원격에서도 키보드는 작동할 수 있음
                pyautogui.hotkey('ctrl', 'v')
                return True
            except:
                return False
                
        # AHK 스크립트
        # 텍스트 이스케이프
        text = text.replace('"', '""')
        script = f"""
        SendRaw, {text}
        ExitApp
        """
        
        script_file = "temp_send.ahk"
        with open(script_file, 'w', encoding='utf-8') as f:
            f.write(script)
            
        try:
            subprocess.run([self.ahk_path, script_file], check=True)
            os.remove(script_file)
            return True
        except:
            return False
            
    def send_enter(self):
        """엔터키 전송"""
        try:
            import pyautogui
            pyautogui.press('enter')
            return True
        except:
            if self.ahk_path:
                script = """
                Send, {Enter}
                ExitApp
                """
                script_file = "temp_enter.ahk"
                with open(script_file, 'w') as f:
                    f.write(script)
                    
                try:
                    subprocess.run([self.ahk_path, script_file], check=True)
                    os.remove(script_file)
                    return True
                except:
                    pass
            return False

# 전역 인스턴스
automation = RemoteAutomation()