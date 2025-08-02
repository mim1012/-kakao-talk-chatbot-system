"""
Automation service module for mouse and keyboard control.
Handles input simulation, clipboard operations, and message sending.
"""
from __future__ import annotations

import ctypes
import logging
import pyautogui
import pyperclip
import time
from typing import Protocol
from core.config_manager import ConfigManager


class InputManager(Protocol):
    """Protocol for input management abstraction."""
    
    def click(self, position: tuple[int, int]) -> bool:
        """Click at the specified position."""
        ...
    
    def move_to(self, position: tuple[int, int]) -> bool:
        """Move mouse to the specified position."""
        ...
    
    def press_key(self, key: str) -> bool:
        """Press a single key."""
        ...
    
    def hotkey(self, *keys: str) -> bool:
        """Press a combination of keys."""
        ...


class ClipboardManager(Protocol):
    """Protocol for clipboard management abstraction."""
    
    def copy(self, text: str) -> bool:
        """Copy text to clipboard."""
        ...
    
    def paste(self) -> str:
        """Get text from clipboard."""
        ...


class DefaultInputManager:
    """Default implementation using pyautogui and ctypes."""
    
    def __init__(self, config_manager: ConfigManager):
        self.config = config_manager
        self.logger = logging.getLogger(__name__)
        pyautogui.FAILSAFE = False
    
    def click(self, position: tuple[int, int]) -> bool:
        """Click at the specified position using Windows API or pyautogui."""
        try:
            x, y = position
            
            # Try Windows API first (more reliable)
            try:
                ctypes.windll.user32.SetCursorPos(x, y)
                time.sleep(self.config.timing_config.click_delay)
                
                # Perform click using Windows API
                ctypes.windll.user32.mouse_event(0x0002, x, y, 0, 0)  # Mouse down
                ctypes.windll.user32.mouse_event(0x0004, x, y, 0, 0)  # Mouse up
                
                return True
                
            except Exception as e:
                self.logger.warning(f"Windows API click failed, falling back to pyautogui: {e}")
                
                # Fallback to pyautogui
                pyautogui.click(x, y)
                return True
                
        except Exception as e:
            self.logger.error(f"Click operation failed: {e}")
            return False
    
    def move_to(self, position: tuple[int, int]) -> bool:
        """Move mouse to the specified position."""
        try:
            x, y = position
            
            # Try Windows API first
            try:
                ctypes.windll.user32.SetCursorPos(x, y)
                return True
            except Exception:
                # Fallback to pyautogui
                pyautogui.moveTo(x, y)
                return True
                
        except Exception as e:
            self.logger.error(f"Move operation failed: {e}")
            return False
    
    def press_key(self, key: str) -> bool:
        """Press a single key."""
        try:
            pyautogui.press(key)
            return True
        except Exception as e:
            self.logger.error(f"Key press failed: {e}")
            return False
    
    def hotkey(self, *keys: str) -> bool:
        """Press a combination of keys."""
        try:
            pyautogui.hotkey(*keys)
            return True
        except Exception as e:
            self.logger.error(f"Hotkey combination failed: {e}")
            return False


class DefaultClipboardManager:
    """Default implementation using pyperclip."""
    
    def __init__(self, config_manager: ConfigManager):
        self.config = config_manager
        self.logger = logging.getLogger(__name__)
    
    def copy(self, text: str) -> bool:
        """Copy text to clipboard with retry logic."""
        max_retries = self.config.automation_config.clipboard_retry_count
        
        for attempt in range(max_retries):
            try:
                pyperclip.copy(text)
                time.sleep(self.config.timing_config.clipboard_delay)
                
                # Verify copy operation
                if pyperclip.paste() == text:
                    return True
                    
            except Exception as e:
                self.logger.warning(f"Clipboard copy attempt {attempt + 1} failed: {e}")
                time.sleep(0.1)
        
        self.logger.error(f"Failed to copy text to clipboard after {max_retries} attempts")
        return False
    
    def paste(self) -> str:
        """Get text from clipboard."""
        try:
            return pyperclip.paste()
        except Exception as e:
            self.logger.error(f"Clipboard paste failed: {e}")
            return ""


class AutomationResult:
    """Result of an automation operation."""
    
    def __init__(self, success: bool, message: str = ""):
        self.success = success
        self.message = message


class AutomationService:
    """Service for handling automation tasks."""
    
    def __init__(self, 
                 config_manager: ConfigManager,
                 input_manager: InputManager = None,
                 clipboard_manager: ClipboardManager = None):
        self.config = config_manager
        self.logger = logging.getLogger(__name__)
        
        # Use dependency injection or create default implementations
        self.input_manager = input_manager or DefaultInputManager(config_manager)
        self.clipboard_manager = clipboard_manager or DefaultClipboardManager(config_manager)
    
    def find_input_position(self, cell_bounds: tuple[int, int, int, int], 
                          detected_text_position: tuple[int, int] | None = None) -> tuple[int, int]:
        """Find the input position for a given cell."""
        if detected_text_position:
            # Use dynamic positioning based on detected text
            x, y = detected_text_position
            # Position input field below the detected text
            ocr_y_offset = self.config.ui_constants.ocr_area_y_offset
            return (x, y + ocr_y_offset + 5)
        
        # Fallback to static positioning
        cell_x, cell_y, cell_width, cell_height = cell_bounds
        fallback_offset = self.config.automation_config.input_position_fallback_offset
        return (
            cell_x + cell_width // 2,  # Center horizontally
            cell_y + cell_height - fallback_offset  # Near bottom
        )
    
    def execute_message_input(self, 
                            position: tuple[int, int], 
                            message: str) -> AutomationResult:
        """Execute the complete message input sequence."""
        try:
            # Step 1: Move to position and click
            if not self.input_manager.move_to(position):
                return AutomationResult(False, "Failed to move mouse to position")
            
            time.sleep(self.config.timing_config.click_delay)
            
            if not self.input_manager.click(position):
                return AutomationResult(False, "Failed to click at position")
            
            # Step 2: Copy message to clipboard
            if not self.clipboard_manager.copy(message):
                return AutomationResult(False, "Failed to copy message to clipboard")
            
            # Step 3: Clear existing text and paste new message
            time.sleep(self.config.timing_config.clipboard_delay)
            
            # Select all and delete
            if not self.input_manager.hotkey('ctrl', 'a'):
                return AutomationResult(False, "Failed to select all text")
            
            time.sleep(0.05)
            
            if not self.input_manager.press_key('delete'):
                return AutomationResult(False, "Failed to delete existing text")
            
            time.sleep(self.config.timing_config.clipboard_delay)
            
            # Paste new message
            if not self.input_manager.hotkey('ctrl', 'v'):
                return AutomationResult(False, "Failed to paste message")
            
            time.sleep(self.config.timing_config.paste_delay)
            
            # Step 4: Send message
            if not self.input_manager.press_key('enter'):
                return AutomationResult(False, "Failed to send message")
            
            time.sleep(self.config.timing_config.send_delay)
            
            return AutomationResult(True, "Message sent successfully")
            
        except Exception as e:
            self.logger.error(f"Message input execution failed: {e}")
            return AutomationResult(False, f"Execution failed: {str(e)}")
    
    def verify_message_sent(self, position: tuple[int, int]) -> bool:
        """Verify that a message was sent by checking if input field is empty."""
        try:
            # Click on the input field
            if not self.input_manager.click(position):
                return False
            
            time.sleep(self.config.timing_config.verification_delay)
            
            # Select all text
            if not self.input_manager.hotkey('ctrl', 'a'):
                return False
            
            time.sleep(0.05)
            
            # Copy selected text
            if not self.input_manager.hotkey('ctrl', 'c'):
                return False
            
            time.sleep(self.config.timing_config.clipboard_delay)
            
            # Check if clipboard is empty (message was sent)
            current_text = self.clipboard_manager.paste().strip()
            return len(current_text) == 0
            
        except Exception as e:
            self.logger.error(f"Message verification failed: {e}")
            return False
    
    def get_response_message(self) -> str:
        """Get response message - 이제 smart_input_automation.py에서 관리됨"""
        # 이 메소드는 deprecated됨. smart_input_automation.py의 메시지를 사용하세요.
        # 호환성을 위해 기본 메시지 제공
        return "어서와요👋\n\n▪ 보이스룸이 켜져있을 경우 오른쪽 상단 ❌ 또는 ☰ 메뉴에서 '공지사항' 먼저 확인해 주세요!\n\n▪ 채팅방 하트 꾹 눌러주세요❤\n\n▪입장하시면 같이 인사해주세요❤"
    
    def execute_full_automation(self, 
                              cell_bounds: tuple[int, int, int, int],
                              detected_text_position: tuple[int, int] | None = None) -> AutomationResult:
        """Execute the complete automation sequence."""
        try:
            # Find input position
            input_position = self.find_input_position(cell_bounds, detected_text_position)
            
            # Get response message
            message = self.get_response_message()
            
            # Execute message input
            result = self.execute_message_input(input_position, message)
            
            if result.success:
                # Verify message was sent
                if self.verify_message_sent(input_position):
                    self.logger.info("Automation completed successfully and verified")
                    return AutomationResult(True, "Automation completed and verified")
                else:
                    self.logger.warning("Automation completed but verification failed")
                    return AutomationResult(True, "Automation completed but verification failed")
            
            return result
            
        except Exception as e:
            self.logger.error(f"Full automation failed: {e}")
            return AutomationResult(False, f"Full automation failed: {str(e)}")
    
    def get_status(self) -> dict:
        """Get automation service status."""
        return {
            'input_manager': type(self.input_manager).__name__,
            'clipboard_manager': type(self.clipboard_manager).__name__,
            'pyautogui_available': True,  # We know it's available since we imported it
            'failsafe_disabled': not pyautogui.FAILSAFE
        }