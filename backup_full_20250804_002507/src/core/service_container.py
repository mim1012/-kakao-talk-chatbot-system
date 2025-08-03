"""
Service container for dependency injection and service management.
Centralizes the creation and lifecycle of all application services.
"""
from __future__ import annotations

import logging
import queue
import threading
import numpy as np
from typing import Any
from core.config_manager import ConfigManager
from ocr.ocr_service import OCRService
from automation.automation_service import AutomationService, DefaultInputManager, DefaultClipboardManager
from core.grid_manager import GridManager, GridCell, CellStatus


class ServiceContainer:
    """Container for managing application services and dependencies."""
    
    def __init__(self, config_path: str = "config.json"):
        self.logger = logging.getLogger(__name__)
        self._services = {}
        
        # Initialize services in dependency order
        self._config_manager = ConfigManager(config_path)
        self._ocr_service = OCRService(self._config_manager)
        self._input_manager = DefaultInputManager(self._config_manager)
        self._clipboard_manager = DefaultClipboardManager(self._config_manager)
        self._automation_service = AutomationService(
            self._config_manager,
            self._input_manager,
            self._clipboard_manager
        )
        self._grid_manager = GridManager(self._config_manager)
        
        # Task queue for communication between detection and execution
        self._task_queue = queue.Queue()
        
        # Control flags
        self._monitoring_active = False
        self._shutdown_requested = False
        
        self.logger.info("Service container initialized successfully")
    
    @property
    def config_manager(self) -> ConfigManager:
        """Get the configuration manager."""
        return self._config_manager
    
    @property
    def ocr_service(self) -> OCRService:
        """Get the OCR service."""
        return self._ocr_service
    
    @property
    def automation_service(self) -> AutomationService:
        """Get the automation service."""
        return self._automation_service
    
    @property
    def grid_manager(self) -> GridManager:
        """Get the grid manager."""
        return self._grid_manager
    
    @property
    def task_queue(self) -> queue.Queue:
        """Get the task queue."""
        return self._task_queue
    
    def is_monitoring_active(self) -> bool:
        """Check if monitoring is currently active."""
        return self._monitoring_active
    
    def is_shutdown_requested(self) -> bool:
        """Check if shutdown has been requested."""
        return self._shutdown_requested
    
    def start_monitoring(self) -> bool:
        """Start the monitoring process."""
        if self._monitoring_active:
            self.logger.warning("Monitoring is already active")
            return False
        
        if not self._ocr_service.is_available():
            self.logger.error("Cannot start monitoring: OCR service is not available")
            return False
        
        self._monitoring_active = True
        self._shutdown_requested = False
        self.logger.info("Monitoring started")
        return True
    
    def stop_monitoring(self) -> None:
        """Stop the monitoring process."""
        if not self._monitoring_active:
            return
        
        self._monitoring_active = False
        self.logger.info("Monitoring stopped")
    
    def request_shutdown(self) -> None:
        """Request shutdown of all services."""
        self._shutdown_requested = True
        self.stop_monitoring()
        self.logger.info("Shutdown requested")
    
    def process_detection_task(self, cell: GridCell) -> bool:
        """Process a single detection task."""
        try:
            if not cell.can_be_triggered():
                return False
            
            # Add to task queue for automation processing
            self._task_queue.put(cell)
            self.logger.info(f"Detection task queued for cell {cell.id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to process detection task for cell {cell.id}: {e}")
            return False
    
    def process_automation_task(self, timeout: float = 1.0) -> bool:
        """Process a single automation task from the queue."""
        try:
            cell = self._task_queue.get(timeout=timeout)
            
            try:
                # Execute automation
                result = self._automation_service.execute_full_automation(
                    cell.bounds,
                    cell.detected_text_position
                )
                
                if result.success:
                    self.logger.info(f"Automation successful for cell {cell.id}")
                    # Set normal cooldown
                    cell.set_cooldown(self._config_manager.cooldown_sec)
                else:
                    self.logger.warning(f"Automation failed for cell {cell.id}: {result.message}")
                    # Set longer cooldown after failure
                    cell.set_cooldown(self._config_manager.timing_config.cooldown_after_failure)
                
                return result.success
                
            finally:
                self._task_queue.task_done()
                
        except queue.Empty:
            return False
        except Exception as e:
            self.logger.error(f"Failed to process automation task: {e}")
            return False
    
    def get_system_status(self) -> dict[str, Any]:
        """Get comprehensive system status."""
        return {
            'monitoring_active': self._monitoring_active,
            'shutdown_requested': self._shutdown_requested,
            'task_queue_size': self._task_queue.qsize(),
            'config_manager': {
                'config_path': self._config_manager.config_path,
                'grid_size': f"{self._config_manager.grid_rows}x{self._config_manager.grid_cols}",
                'ocr_interval': self._config_manager.ocr_interval_sec,
                'cooldown_sec': self._config_manager.cooldown_sec
            },
            'ocr_service': self._ocr_service.get_status(),
            'automation_service': self._automation_service.get_status(),
            'grid_manager': self._grid_manager.get_statistics()
        }
    
    def refresh_configuration(self) -> bool:
        """Refresh configuration and dependent services."""
        try:
            self.logger.info("Refreshing configuration...")
            
            # Stop monitoring during refresh
            was_monitoring = self._monitoring_active
            self.stop_monitoring()
            
            # Reload configuration
            self._config_manager.load_config()
            
            # Refresh grid with new configuration
            self._grid_manager.refresh_grid()
            
            # Restart monitoring if it was active
            if was_monitoring:
                self.start_monitoring()
            
            self.logger.info("Configuration refreshed successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to refresh configuration: {e}")
            return False
    
    def cleanup(self) -> None:
        """Cleanup resources and prepare for shutdown."""
        try:
            self.logger.info("Cleaning up service container...")
            
            self.stop_monitoring()
            
            # Clear task queue
            while not self._task_queue.empty():
                try:
                    self._task_queue.get_nowait()
                    self._task_queue.task_done()
                except queue.Empty:
                    break
            
            # Reset grid state
            self._grid_manager.reset_all_cells()
            
            self.logger.info("Service container cleanup completed")
            
        except Exception as e:
            self.logger.error(f"Error during cleanup: {e}")


class MonitoringOrchestrator:
    """Orchestrates the monitoring process using the service container."""
    
    def __init__(self, service_container: ServiceContainer):
        self.services = service_container
        self.logger = logging.getLogger(__name__)
        self._detection_thread = None
        self._automation_thread = None
    
    def start_monitoring_threads(self) -> bool:
        """Start the monitoring threads."""
        if not self.services.start_monitoring():
            return False
        
        try:
            # Start detection thread
            self._detection_thread = threading.Thread(
                target=self._detection_loop,
                name="OCRDetectionThread",
                daemon=True
            )
            self._detection_thread.start()
            
            # Start automation thread
            self._automation_thread = threading.Thread(
                target=self._automation_loop,
                name="AutomationExecutionThread",
                daemon=True
            )
            self._automation_thread.start()
            
            self.logger.info("Monitoring threads started successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to start monitoring threads: {e}")
            self.services.stop_monitoring()
            return False
    
    def stop_monitoring_threads(self) -> None:
        """Stop the monitoring threads."""
        self.services.stop_monitoring()
        
        # Wait for threads to finish
        if self._detection_thread and self._detection_thread.is_alive():
            self._detection_thread.join(timeout=5.0)
        
        if self._automation_thread and self._automation_thread.is_alive():
            self._automation_thread.join(timeout=5.0)
        
        self.logger.info("Monitoring threads stopped")
    
    def _detection_loop(self) -> None:
        """Main detection loop running in a separate thread."""
        import mss
        import time
        
        self.logger.info("Detection loop started")
        
        try:
            with mss.mss() as sct:
                while self.services.is_monitoring_active() and not self.services.is_shutdown_requested():
                    try:
                        # Update cell cooldowns
                        self.services.grid_manager.update_cell_cooldowns()
                        
                        # Get cells for this cycle
                        cells_to_process = self.services.grid_manager.get_cells_for_cycle()
                        
                        for cell in cells_to_process:
                            if not self.services.is_monitoring_active():
                                break
                            
                            # Capture OCR area
                            ocr_area = {
                                'left': cell.ocr_area[0],
                                'top': cell.ocr_area[1],
                                'width': cell.ocr_area[2],
                                'height': cell.ocr_area[3]
                            }
                            
                            screenshot = sct.grab(ocr_area)
                            image = np.array(screenshot)
                            
                            # Perform OCR
                            ocr_result = self.services.ocr_service.perform_ocr(image)
                            
                            # Check for trigger patterns
                            if self.services.ocr_service.check_trigger_patterns(ocr_result):
                                cell.set_triggered(ocr_result.text, ocr_result.position)
                                self.services.process_detection_task(cell)
                        
                        # Sleep between cycles
                        time.sleep(self.services.config_manager.ocr_interval_sec)
                        
                    except Exception as e:
                        self.logger.error(f"Error in detection loop: {e}")
                        time.sleep(1.0)  # Brief pause before continuing
        
        except Exception as e:
            self.logger.error(f"Fatal error in detection loop: {e}")
        
        finally:
            self.logger.info("Detection loop ended")
    
    def _automation_loop(self) -> None:
        """Main automation loop running in a separate thread."""
        self.logger.info("Automation loop started")
        
        try:
            while self.services.is_monitoring_active() and not self.services.is_shutdown_requested():
                try:
                    # Process automation tasks from queue
                    self.services.process_automation_task(timeout=1.0)
                    
                except Exception as e:
                    self.logger.error(f"Error in automation loop: {e}")
        
        except Exception as e:
            self.logger.error(f"Fatal error in automation loop: {e}")
        
        finally:
            self.logger.info("Automation loop ended")