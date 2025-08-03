"""
Configuration management module for the chatbot system.
Handles loading, validation, and access to configuration settings.
"""
from __future__ import annotations

import json
import logging
from typing import Any
from dataclasses import dataclass


@dataclass
class UIConstants:
    """UI-related constants."""
    ocr_area_y_offset: int = 100
    ocr_area_height: int = 80
    overlay_height: int = 120
    grid_line_width: int = 3
    trigger_box_color: list[int] | None = None
    normal_box_color: list[int] | None = None
    cooldown_box_color: list[int] | None = None
    
    def __post_init__(self):
        if self.trigger_box_color is None:
            self.trigger_box_color = [0, 255, 0]
        if self.normal_box_color is None:
            self.normal_box_color = [255, 255, 255]
        if self.cooldown_box_color is None:
            self.cooldown_box_color = [255, 0, 0]


@dataclass
class TimingConfig:
    """Timing-related configuration."""
    click_delay: float = 0.2
    clipboard_delay: float = 0.1
    paste_delay: float = 0.3
    send_delay: float = 0.5
    verification_delay: float = 0.5
    cooldown_after_failure: float = 5.0


@dataclass
class AutomationConfig:
    """Automation-related configuration."""
    max_retries: int = 3
    clipboard_retry_count: int = 5
    input_position_fallback_offset: int = 50
    cells_per_cycle: int = 10
    enable_batch_processing: bool = True
    max_concurrent_ocr: int = 6


@dataclass
class ChatroomConfig:
    """Configuration for a single chatroom."""
    x: int
    y: int
    width: int
    height: int
    input_x: int
    input_y: int
    ocr_x: int
    ocr_y: int
    ocr_w: int
    ocr_h: int


class ConfigManager:
    """Manages application configuration loading and access."""
    
    def __init__(self, config_path: str = "config.json"):
        self.config_path = config_path
        self.logger = logging.getLogger(__name__)
        self._config = {}
        self._ui_constants = None
        self._timing_config = None
        self._automation_config = None
        self._chatroom_configs: list[ChatroomConfig] = []
        
        self.load_config()
    
    def load_config(self) -> None:
        """Load configuration from JSON file."""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                self._config = json.load(f)
            
            self._parse_config()
            self.logger.info(f"Configuration loaded from {self.config_path}")
            
        except FileNotFoundError:
            self.logger.warning(f"Config file {self.config_path} not found, using defaults")
            self._use_defaults()
        except json.JSONDecodeError as e:
            self.logger.error(f"Invalid JSON in config file: {e}")
            self._use_defaults()
    
    def _parse_config(self) -> None:
        """Parse loaded configuration into structured objects."""
        # Parse UI constants
        ui_data = self._config.get('ui_constants', {})
        self._ui_constants = UIConstants(**ui_data)
        
        # Parse timing config
        timing_data = self._config.get('timing_config', {})
        self._timing_config = TimingConfig(**timing_data)
        
        # Parse automation config
        automation_data = self._config.get('automation_config', {})
        self._automation_config = AutomationConfig(**automation_data)
        
        # Parse chatroom configs
        chatroom_data = self._config.get('chatroom_configs', [])
        self._chatroom_configs = [ChatroomConfig(**room) for room in chatroom_data]
    
    def _use_defaults(self) -> None:
        """Use default configuration values."""
        self._ui_constants = UIConstants()
        self._timing_config = TimingConfig()
        self._automation_config = AutomationConfig()
        self._chatroom_configs: list[ChatroomConfig] = []
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get a configuration value by key."""
        return self._config.get(key, default)
    
    @property
    def ui_constants(self) -> UIConstants:
        """Get UI constants."""
        return self._ui_constants
    
    @property
    def timing_config(self) -> TimingConfig:
        """Get timing configuration."""
        return self._timing_config
    
    @property
    def automation_config(self) -> AutomationConfig:
        """Get automation configuration."""
        return self._automation_config
    
    @property
    def chatroom_configs(self) -> list[ChatroomConfig]:
        """Get chatroom configurations."""
        return self._chatroom_configs
    
    @property
    def grid_rows(self) -> int:
        """Get number of grid rows."""
        return self.get('grid_rows', 3)
    
    @property
    def grid_cols(self) -> int:
        """Get number of grid columns."""
        return self.get('grid_cols', 5)
    
    @property
    def ocr_interval_sec(self) -> float:
        """Get OCR monitoring interval in seconds."""
        return self.get('ocr_interval_sec', 3.0)
    
    @property
    def cooldown_sec(self) -> float:
        """Get cooldown period in seconds."""
        return self.get('cooldown_sec', 10.0)
    
    @property
    def trigger_patterns(self) -> list[str]:
        """Get trigger patterns."""
        return self.get('trigger_patterns', ['들어왔습니다'])
    
    @property
    def ocr_preprocess_config(self) -> dict[str, Any]:
        """Get OCR preprocessing configuration."""
        return self.get('ocr_preprocess', {})
    
    def validate_config(self) -> bool:
        """Validate the loaded configuration."""
        try:
            # Basic validation
            if self.grid_rows <= 0 or self.grid_cols <= 0:
                self.logger.error("Grid dimensions must be positive")
                return False
            
            if self.ocr_interval_sec <= 0:
                self.logger.error("OCR interval must be positive")
                return False
            
            if not self.trigger_patterns:
                self.logger.warning("No trigger patterns defined")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Configuration validation failed: {e}")
            return False