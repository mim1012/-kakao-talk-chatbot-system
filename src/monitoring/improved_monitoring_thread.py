"""
Improved monitoring thread with better OCR detection and debugging
"""
from __future__ import annotations

import time
import queue
import threading
import logging
import numpy as np
import mss
from dataclasses import dataclass
from PyQt5.QtCore import QThread, pyqtSignal

from core.service_container import ServiceContainer
from core.grid_manager import GridCell, CellStatus
from ocr.enhanced_ocr_service import EnhancedOCRService, OCRResult


@dataclass
class MonitoringResult:
    """Enhanced monitoring result with debugging info."""
    cell: GridCell
    ocr_result: OCRResult
    screenshot_time: float
    processing_time: float
    

class ImprovedMonitoringThread(QThread):
    """Improved monitoring thread with better detection and debugging."""
    
    # Signals
    detection_signal = pyqtSignal(str, str, float, float)  # cell_id, text, x, y
    status_signal = pyqtSignal(str)  # status message
    debug_signal = pyqtSignal(dict)  # debug info
    
    def __init__(self, service_container: ServiceContainer):
        super().__init__()
        self.services = service_container
        self.logger = logging.getLogger(__name__)
        
        # Enhanced OCR service
        self.ocr_service = EnhancedOCRService(service_container.config_manager)
        
        # Monitoring state
        self.running = False
        self.monitoring_interval = 0.5  # seconds
        self.batch_size = 10  # Process 10 cells at a time
        
        # Performance tracking
        self.performance_stats = {
            'cycles': 0,
            'total_time': 0,
            'detections': 0,
            'last_detection_time': 0
        }
        
        # Debug mode
        self.debug_mode = True
        self.debug_interval = 15  # Log stats every 15 seconds
        self.last_debug_time = time.time()
        
    def run(self):
        """Main monitoring loop with improved detection."""
        self.logger.info("🚀 Starting improved monitoring thread")
        self.running = True
        
        # Send initial status
        self.status_signal.emit("🚀 모니터링 시작 - 향상된 OCR 감지")
        
        with mss.mss() as sct:
            while self.running:
                cycle_start = time.time()
                
                try:
                    # Update cell cooldowns
                    self.services.grid_manager.update_cell_cooldowns()
                    
                    # Get active cells
                    active_cells = self._get_active_cells()
                    
                    if not active_cells:
                        self._idle_wait()
                        continue
                    
                    # Log active cells periodically
                    self._log_active_cells(active_cells)
                    
                    # Process cells in batches
                    for batch_start in range(0, len(active_cells), self.batch_size):
                        batch_end = min(batch_start + self.batch_size, len(active_cells))
                        batch = active_cells[batch_start:batch_end]
                        
                        # Capture screenshots for batch
                        screenshots = self._capture_batch_screenshots(sct, batch)
                        
                        # Process OCR for batch
                        results = self._process_batch_ocr(screenshots)
                        
                        # Handle results
                        self._handle_results(results)
                    
                    # Update performance stats
                    self._update_performance_stats(cycle_start)
                    
                    # Debug logging
                    self._periodic_debug_log()
                    
                    # Cycle timing
                    self._manage_cycle_timing(cycle_start)
                    
                except Exception as e:
                    self.logger.error(f"Monitoring cycle error: {e}", exc_info=True)
                    self.status_signal.emit(f"❌ 모니터링 오류: {str(e)}")
                    time.sleep(1)  # Error recovery delay
    
    def _get_active_cells(self) -> List[GridCell]:
        """Get cells that are ready for monitoring."""
        active_cells = []
        
        for cell in self.services.grid_manager.cells:
            if cell.can_be_triggered():
                active_cells.append(cell)
        
        # Sort by priority (target cells first)
        active_cells.sort(key=lambda c: (
            0 if c.id == "M0_R0_C1" else 1,  # Target cell priority
            c.last_triggered_time  # Least recently triggered
        ))
        
        return active_cells
    
    def _log_active_cells(self, active_cells: List[GridCell]):
        """Log active cells periodically."""
        if time.time() - self.last_debug_time > 15:  # Every 15 seconds
            cell_ids = [c.id for c in active_cells[:5]]  # First 5
            self.logger.info(f"🔄 활성 셀 확인: {', '.join(cell_ids)}")
    
    def _capture_batch_screenshots(self, sct, cells: List[GridCell]) -> List[Tuple[np.ndarray, GridCell, float]]:
        """Capture screenshots for a batch of cells."""
        screenshots = []
        
        for cell in cells:
            try:
                # Log target cell specially
                if cell.id == "M0_R0_C1":
                    self.logger.debug(f"🔍 {cell.id}: 강제 OCR 실행 (캐시 비활성화) ⭐ 목표 셀!")
                else:
                    self.logger.debug(f"🔍 {cell.id}: 강제 OCR 실행 (캐시 비활성화)")
                
                # Define capture area
                ocr_area = {
                    'left': cell.ocr_area[0],
                    'top': cell.ocr_area[1],
                    'width': cell.ocr_area[2],
                    'height': cell.ocr_area[3]
                }
                
                # Capture screenshot
                capture_time = time.time()
                screenshot = sct.grab(ocr_area)
                image = np.array(screenshot)
                
                # Convert BGRA to BGR
                if image.shape[2] == 4:
                    image = image[:, :, :3]
                
                screenshots.append((image, cell, capture_time))
                
                # Save debug screenshot for target cell
                if self.debug_mode and cell.id == "M0_R0_C1":
                    self._save_target_cell_debug(image, cell.id)
                    
            except Exception as e:
                self.logger.error(f"Screenshot capture failed for {cell.id}: {e}")
                
        return screenshots
    
    def _save_target_cell_debug(self, image: np.ndarray, cell_id: str):
        """Save debug image for target cell."""
        import cv2
        import os
        
        debug_dir = "debug_screenshots/target_cell"
        os.makedirs(debug_dir, exist_ok=True)
        
        timestamp = int(time.time() * 1000)
        filename = f"{debug_dir}/{cell_id}_{timestamp}.png"
        cv2.imwrite(filename, image)
        self.logger.debug(f"💾 Target cell debug saved: {filename}")
    
    def _process_batch_ocr(self, screenshots: List[Tuple[np.ndarray, GridCell, float]]) -> List[MonitoringResult]:
        """Process OCR for a batch of screenshots."""
        results = []
        
        for image, cell, capture_time in screenshots:
            try:
                # Perform OCR with recovery
                ocr_start = time.time()
                ocr_result = self.ocr_service.perform_ocr_with_recovery(image, cell.id)
                ocr_time = time.time() - ocr_start
                
                # Create monitoring result
                result = MonitoringResult(
                    cell=cell,
                    ocr_result=ocr_result,
                    screenshot_time=capture_time,
                    processing_time=ocr_time
                )
                
                results.append(result)
                
                # Log OCR result
                if ocr_result.is_valid():
                    self.logger.info(f"📝 OCR 감지: '{ocr_result.text}' (평균 신뢰도: {ocr_result.confidence:.2f})")
                else:
                    self.logger.debug(f"⚪ {cell.id}: OCR 결과 없음")
                    
            except Exception as e:
                self.logger.error(f"OCR processing failed for {cell.id}: {e}")
                
        return results
    
    def _handle_results(self, results: List[MonitoringResult]):
        """Handle monitoring results."""
        for result in results:
            cell = result.cell
            ocr_result = result.ocr_result
            
            if not ocr_result.is_valid():
                continue
            
            # Check trigger patterns
            if self.ocr_service.check_trigger_patterns(ocr_result):
                # Trigger detected!
                self.logger.info(f"✅ {cell.id}: '{ocr_result.text}' (트리거 감지!)")
                
                # Update cell state
                cell.set_triggered(ocr_result.text, ocr_result.position)
                
                # Emit detection signal
                self.detection_signal.emit(
                    cell.id, 
                    ocr_result.text,
                    ocr_result.position[0],
                    ocr_result.position[1]
                )
                
                # Update stats
                self.performance_stats['detections'] += 1
                self.performance_stats['last_detection_time'] = time.time()
                
                # Status update
                self.status_signal.emit(f"🎯 {cell.id}: 트리거 감지 - {ocr_result.text}")
            else:
                # Not a trigger pattern
                self.logger.debug(f"❌ {cell.id}: '{ocr_result.text}' (매칭 실패)")
    
    def _update_performance_stats(self, cycle_start: float):
        """Update performance statistics."""
        cycle_time = time.time() - cycle_start
        self.performance_stats['cycles'] += 1
        self.performance_stats['total_time'] += cycle_time
    
    def _periodic_debug_log(self):
        """Log debug information periodically."""
        current_time = time.time()
        
        if current_time - self.last_debug_time >= self.debug_interval:
            # Get OCR status
            ocr_status = self.ocr_service.get_status()
            
            # Calculate averages
            avg_cycle_time = (self.performance_stats['total_time'] / 
                            self.performance_stats['cycles']) if self.performance_stats['cycles'] > 0 else 0
            
            # Emit debug info
            debug_info = {
                'monitoring_cycles': self.performance_stats['cycles'],
                'avg_cycle_time': f"{avg_cycle_time:.3f}s",
                'total_detections': self.performance_stats['detections'],
                'ocr_status': ocr_status['stats']
            }
            
            self.debug_signal.emit(debug_info)
            
            # Log summary
            self.logger.info(f"📊 모니터링 상태: {self.performance_stats['cycles']} 사이클, "
                           f"{self.performance_stats['detections']} 감지, "
                           f"OCR 성공률: {ocr_status['stats']['success_rate']}")
            
            self.last_debug_time = current_time
    
    def _idle_wait(self):
        """Wait when no active cells."""
        time.sleep(0.1)
    
    def _manage_cycle_timing(self, cycle_start: float):
        """Manage monitoring cycle timing."""
        elapsed = time.time() - cycle_start
        sleep_time = max(self.monitoring_interval - elapsed, 0.05)
        
        if sleep_time > 0:
            time.sleep(sleep_time)
    
    def stop(self):
        """Stop monitoring thread."""
        self.logger.info("Stopping monitoring thread...")
        self.running = False
        
        # Final status
        total_runtime = self.performance_stats['total_time']
        self.status_signal.emit(
            f"🛑 모니터링 종료 - 총 {self.performance_stats['cycles']} 사이클, "
            f"{self.performance_stats['detections']} 감지, "
            f"실행 시간: {total_runtime:.1f}초"
        )
    
    def set_debug_mode(self, enabled: bool):
        """Toggle debug mode."""
        self.debug_mode = enabled
        self.ocr_service.debug_mode = enabled
        self.logger.info(f"Debug mode: {'enabled' if enabled else 'disabled'}")