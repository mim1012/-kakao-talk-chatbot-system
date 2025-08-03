"""
Grid management module for handling screen grid cells and their states.
Manages cell creation, state updates, and cooldown mechanisms.
"""
from __future__ import annotations

import logging
import time
from typing import Any
from dataclasses import dataclass, field
from enum import StrEnum
import screeninfo
from core.config_manager import ConfigManager


class CellStatus(StrEnum):
    """Enumeration of possible cell states."""
    IDLE = "idle"
    TRIGGERED = "triggered"
    COOLDOWN = "cooldown"
    DISABLED = "disabled"


@dataclass
class GridCell:
    """Represents a single grid cell with its properties and state."""
    id: str
    bounds: tuple[int, int, int, int]  # (x, y, width, height)
    ocr_area: tuple[int, int, int, int]  # (x, y, width, height)
    status: CellStatus = CellStatus.IDLE
    enabled: bool = True
    last_triggered: float = 0.0
    cooldown_until: float = 0.0
    detected_text: str = ""
    detected_text_position: tuple[int, int] | None = None
    trigger_count: int = 0
    monitor_index: int = 0
    
    def set_triggered(self, text: str = "", position: tuple[int, int] | None = None) -> None:
        """Mark cell as triggered with detected text."""
        self.status = CellStatus.TRIGGERED
        self.detected_text = text
        self.detected_text_position = position
        self.last_triggered = time.time()
        self.trigger_count += 1
    
    def set_cooldown(self, duration_sec: float) -> None:
        """Set cell to cooldown state for specified duration."""
        self.status = CellStatus.COOLDOWN
        self.cooldown_until = time.time() + duration_sec
    
    def set_idle(self) -> None:
        """Reset cell to idle state."""
        self.status = CellStatus.IDLE
        self.detected_text = ""
        self.detected_text_position = None
    
    def is_in_cooldown(self) -> bool:
        """Check if cell is currently in cooldown."""
        if self.status != CellStatus.COOLDOWN:
            return False
        
        if time.time() >= self.cooldown_until:
            self.set_idle()
            return False
        
        return True
    
    def can_be_triggered(self) -> bool:
        """Check if cell can be triggered (enabled and not in cooldown)."""
        return self.enabled and not self.is_in_cooldown() and self.status == CellStatus.IDLE
    
    def get_center_point(self) -> tuple[int, int]:
        """Get the center point of the cell."""
        x, y, width, height = self.bounds
        return (x + width // 2, y + height // 2)
    
    def get_ocr_center_point(self) -> tuple[int, int]:
        """Get the center point of the OCR area."""
        x, y, width, height = self.ocr_area
        return (x + width // 2, y + height // 2)
    
    def to_dict(self) -> dict[str, Any]:
        """Convert cell to dictionary representation."""
        return {
            'id': self.id,
            'bounds': self.bounds,
            'ocr_area': self.ocr_area,
            'status': self.status.value,
            'enabled': self.enabled,
            'last_triggered': self.last_triggered,
            'cooldown_until': self.cooldown_until,
            'detected_text': self.detected_text,
            'detected_text_position': self.detected_text_position,
            'trigger_count': self.trigger_count,
            'monitor_index': self.monitor_index
        }


class GridManager:
    """Manages the screen grid and cell states."""
    
    def __init__(self, config_manager: ConfigManager):
        self.config = config_manager
        self.logger = logging.getLogger(__name__)
        self.cells: list[GridCell] = []
        self.monitors = []
        self._current_cycle_index = 0
        
        self._initialize_monitors()
        self._create_grid_cells()
    
    def _initialize_monitors(self) -> None:
        """Initialize monitor information."""
        try:
            self.monitors = screeninfo.get_monitors()
            self.logger.info(f"Detected {len(self.monitors)} monitor(s)")
            
            for i, monitor in enumerate(self.monitors):
                self.logger.info(f"Monitor {i}: {monitor.width}x{monitor.height} at ({monitor.x}, {monitor.y})")
        
        except Exception as e:
            self.logger.error(f"Failed to initialize monitors: {e}")
            # Fallback to single monitor
            self.monitors = [type('Monitor', (), {
                'x': 0, 'y': 0, 'width': 1920, 'height': 1080
            })()]
    
    def _create_grid_cells(self) -> None:
        """Create grid cells based on configuration."""
        try:
            rows = self.config.grid_rows
            cols = self.config.grid_cols
            ui_constants = self.config.ui_constants
            
            self.cells.clear()
            
            for monitor_idx, monitor in enumerate(self.monitors):
                cell_width = monitor.width // cols
                cell_height = monitor.height // rows
                
                for row in range(rows):
                    for col in range(cols):
                        # Calculate cell bounds
                        cell_x = monitor.x + col * cell_width
                        cell_y = monitor.y + row * cell_height
                        cell_bounds = (cell_x, cell_y, cell_width, cell_height)
                        
                        # Calculate OCR area at the bottom of the cell
                        ocr_x = cell_x
                        ocr_y = cell_y + cell_height - ui_constants.ocr_area_height  # OCR area at bottom
                        ocr_width = cell_width
                        ocr_height = ui_constants.ocr_area_height
                        ocr_area = (ocr_x, ocr_y, ocr_width, ocr_height)
                        
                        # Create cell
                        cell_id = f"monitor_{monitor_idx}_cell_{row}_{col}"
                        cell = GridCell(
                            id=cell_id,
                            bounds=cell_bounds,
                            ocr_area=ocr_area,
                            monitor_index=monitor_idx
                        )
                        
                        self.cells.append(cell)
            
            self.logger.info(f"Created {len(self.cells)} grid cells")
            
        except Exception as e:
            self.logger.error(f"Failed to create grid cells: {e}")
    
    def get_cells_for_cycle(self) -> list[GridCell]:
        """Get the next batch of cells for processing in round-robin fashion."""
        if not self.cells:
            return []
        
        # Get enabled cells that can be triggered
        active_cells = [cell for cell in self.cells if cell.can_be_triggered()]
        
        if not active_cells:
            return []
        
        cells_per_cycle = self.config.automation_config.cells_per_cycle
        
        # Round-robin selection
        start_index = self._current_cycle_index % len(active_cells)
        end_index = min(start_index + cells_per_cycle, len(active_cells))
        
        selected_cells = active_cells[start_index:end_index]
        
        # If we need more cells and there are more available, wrap around
        if len(selected_cells) < cells_per_cycle and len(active_cells) > cells_per_cycle:
            remaining_needed = cells_per_cycle - len(selected_cells)
            wrap_around_cells = active_cells[:remaining_needed]
            selected_cells.extend(wrap_around_cells)
        
        # Update cycle index
        self._current_cycle_index = (self._current_cycle_index + cells_per_cycle) % len(active_cells)
        
        return selected_cells
    
    def get_cell_by_id(self, cell_id: str) -> GridCell | None:
        """Get a cell by its ID."""
        for cell in self.cells:
            if cell.id == cell_id:
                return cell
        return None
    
    def get_cells_by_status(self, status: CellStatus) -> list[GridCell]:
        """Get all cells with the specified status."""
        return [cell for cell in self.cells if cell.status == status]
    
    def get_enabled_cells(self) -> list[GridCell]:
        """Get all enabled cells."""
        return [cell for cell in self.cells if cell.enabled]
    
    def update_cell_cooldowns(self) -> None:
        """Update all cells to check if cooldowns have expired."""
        current_time = time.time()
        
        for cell in self.cells:
            if cell.status == CellStatus.COOLDOWN and current_time >= cell.cooldown_until:
                cell.set_idle()
    
    def set_cell_enabled(self, cell_id: str, enabled: bool) -> bool:
        """Enable or disable a specific cell."""
        cell = self.get_cell_by_id(cell_id)
        if cell:
            cell.enabled = enabled
            if not enabled:
                cell.status = CellStatus.DISABLED
            elif cell.status == CellStatus.DISABLED:
                cell.set_idle()
            return True
        return False
    
    def reset_all_cells(self) -> None:
        """Reset all cells to idle state."""
        for cell in self.cells:
            if cell.enabled:
                cell.set_idle()
            else:
                cell.status = CellStatus.DISABLED
    
    def get_cell_at_position(self, x: int, y: int) -> GridCell | None:
        """Get the cell that contains the specified screen position."""
        for cell in self.cells:
            cell_x, cell_y, cell_width, cell_height = cell.bounds
            if (cell_x <= x < cell_x + cell_width and 
                cell_y <= y < cell_y + cell_height):
                return cell
        return None
    
    def get_statistics(self) -> dict[str, Any]:
        """Get grid statistics."""
        total_cells = len(self.cells)
        enabled_cells = len(self.get_enabled_cells())
        idle_cells = len(self.get_cells_by_status(CellStatus.IDLE))
        triggered_cells = len(self.get_cells_by_status(CellStatus.TRIGGERED))
        cooldown_cells = len(self.get_cells_by_status(CellStatus.COOLDOWN))
        disabled_cells = len(self.get_cells_by_status(CellStatus.DISABLED))
        
        # Calculate total triggers
        total_triggers = sum(cell.trigger_count for cell in self.cells)
        
        return {
            'total_cells': total_cells,
            'enabled_cells': enabled_cells,
            'idle_cells': idle_cells,
            'triggered_cells': triggered_cells,
            'cooldown_cells': cooldown_cells,
            'disabled_cells': disabled_cells,
            'total_triggers': total_triggers,
            'monitors': len(self.monitors),
            'current_cycle_index': self._current_cycle_index
        }
    
    def export_cell_states(self) -> list[dict[str, Any]]:
        """Export all cell states as a list of dictionaries."""
        return [cell.to_dict() for cell in self.cells]
    
    def refresh_grid(self) -> None:
        """Refresh the grid (recreate cells with current configuration)."""
        self.logger.info("Refreshing grid cells")
        self._initialize_monitors()
        self._create_grid_cells()
    
    def get_cells_in_monitor(self, monitor_index: int) -> list[GridCell]:
        """Get all cells in a specific monitor."""
        return [cell for cell in self.cells if cell.monitor_index == monitor_index]