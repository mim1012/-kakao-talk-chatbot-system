"""
Enhanced OCR Service with improved detection capabilities
Fixes for empty OCR results and better preprocessing
"""
from __future__ import annotations

import cv2
import gc
import logging
import numpy as np
import re
import threading
import time
from typing import Any
from core.config_manager import ConfigManager
from ocr.enhanced_ocr_corrector import EnhancedOCRCorrector

# Try to import PaddleOCR with graceful fallback
try:
    from paddleocr import PaddleOCR
    PADDLEOCR_AVAILABLE = True
except ImportError:
    PADDLEOCR_AVAILABLE = False
    logging.warning("PaddleOCR not available. OCR functionality will be disabled.")


class OCRResult:
    """Result of OCR processing with enhanced debugging."""
    
    def __init__(self, text: str = "", confidence: float = 0.0, position: tuple[int, int] | None = None, 
                 debug_info: dict[str, Any] | None = None):
        self.text = text
        self.confidence = confidence
        self.position = position or (0, 0)
        self.normalized_text = self._normalize_text(text)
        self.debug_info = debug_info or {}
    
    def _normalize_text(self, text: str) -> str:
        """Normalize text by removing spaces and special characters."""
        return re.sub(r'[^\w가-힣]', '', text)
    
    def is_valid(self) -> bool:
        """Check if the OCR result is valid."""
        return bool(self.text and self.confidence > 0)


class EnhancedOCRService:
    """Enhanced OCR service with better detection and recovery."""
    
    # Class-level lock for thread-safe PaddleOCR initialization
    _ocr_lock = threading.Lock()
    _shared_paddle_ocr = None
    _last_init_time = 0
    
    def __init__(self, config_manager: ConfigManager):
        self.config = config_manager
        self.logger = logging.getLogger(__name__)
        
        # Enhanced OCR corrector
        self.ocr_corrector = EnhancedOCRCorrector()
        self.logger.info("Enhanced OCR corrector initialized")
        
        # Debug mode flag
        self.debug_mode = True
        self.debug_save_count = 0
        self.max_debug_saves = 100
        
        # Performance metrics
        self.ocr_stats = {
            'total_attempts': 0,
            'successful_detections': 0,
            'empty_results': 0,
            'errors': 0,
            'last_error_time': 0
        }
        
        if PADDLEOCR_AVAILABLE:
            self._initialize_paddle_ocr()
    
    def _initialize_paddle_ocr(self) -> None:
        """Thread-safe PaddleOCR initialization with shared instance."""
        with EnhancedOCRService._ocr_lock:
            current_time = time.time()
            
            # Reuse existing instance if initialized recently (within 5 minutes)
            if (EnhancedOCRService._shared_paddle_ocr is not None and 
                current_time - EnhancedOCRService._last_init_time < 300):
                self.paddle_ocr = EnhancedOCRService._shared_paddle_ocr
                self.logger.info("Reusing existing PaddleOCR instance")
                return
            
            try:
                # Initialize with optimized settings for Korean text
                EnhancedOCRService._shared_paddle_ocr = PaddleOCR(
                    use_angle_cls=True,  # Enable angle classification for better detection
                    lang='korean',
                    enable_mkldnn=True,
                    cpu_threads=4,
                    det_limit_side_len=960,
                    rec_batch_num=6,
                    max_text_length=25,
                    drop_score=0.5,  # Higher threshold to reduce false positives
                    det_db_thresh=0.3,
                    det_db_box_thresh=0.5,
                    det_db_unclip_ratio=1.5,
                    show_log=False
                )
                
                self.paddle_ocr = EnhancedOCRService._shared_paddle_ocr
                EnhancedOCRService._last_init_time = current_time
                self.logger.info("PaddleOCR initialized successfully with enhanced settings")
                
            except Exception as e:
                self.logger.error(f"Failed to initialize PaddleOCR: {e}")
                self.paddle_ocr = None
    
    def preprocess_image_enhanced(self, image: np.ndarray, cell_id: str = "") -> list[np.ndarray]:
        """Enhanced preprocessing with multiple strategies."""
        preprocessed_images = []
        
        try:
            # Strategy 1: Original image (for already clear text)
            preprocessed_images.append(image.copy())
            
            # Convert to grayscale if needed
            if len(image.shape) == 3:
                gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            else:
                gray = image.copy()
            
            # Strategy 2: Simple upscaling with sharpening
            height, width = gray.shape
            if width < 200 or height < 50:  # Small image, needs upscaling
                scale_factor = max(200 / width, 50 / height, 2.0)
                new_width = int(width * scale_factor)
                new_height = int(height * scale_factor)
                upscaled = cv2.resize(gray, (new_width, new_height), interpolation=cv2.INTER_CUBIC)
                
                # Sharpen
                kernel = np.array([[-1,-1,-1], [-1,9,-1], [-1,-1,-1]])
                sharpened = cv2.filter2D(upscaled, -1, kernel)
                preprocessed_images.append(sharpened)
            
            # Strategy 3: Adaptive threshold with different parameters
            for block_size in [11, 15]:
                for C in [2, 5]:
                    try:
                        binary = cv2.adaptiveThreshold(
                            gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                            cv2.THRESH_BINARY, block_size, C
                        )
                        preprocessed_images.append(binary)
                        
                        # Also try inverted
                        inverted = cv2.bitwise_not(binary)
                        preprocessed_images.append(inverted)
                    except:
                        continue
            
            # Strategy 4: OTSU thresholding
            _, otsu = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            preprocessed_images.append(otsu)
            
            # Strategy 5: Contrast enhancement
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
            enhanced = clahe.apply(gray)
            preprocessed_images.append(enhanced)
            
            # Save debug images if enabled
            if self.debug_mode and cell_id and self.debug_save_count < self.max_debug_saves:
                self._save_debug_images(preprocessed_images, cell_id)
            
            return preprocessed_images
            
        except Exception as e:
            self.logger.error(f"Image preprocessing failed for {cell_id}: {e}")
            return [image]  # Return original if preprocessing fails
    
    def _save_debug_images(self, images: list[np.ndarray], cell_id: str):
        """Save debug images for analysis."""
        import os
        debug_dir = "debug_screenshots/preprocessing"
        os.makedirs(debug_dir, exist_ok=True)
        
        timestamp = int(time.time() * 1000)
        for i, img in enumerate(images[:5]):  # Save first 5 strategies only
            if self.debug_save_count >= self.max_debug_saves:
                break
                
            filename = f"{debug_dir}/{cell_id}_strategy{i}_{timestamp}.png"
            cv2.imwrite(filename, img)
            self.debug_save_count += 1
    
    def perform_ocr_with_recovery(self, image: np.ndarray, cell_id: str = "") -> OCRResult:
        """Perform OCR with automatic recovery and multiple strategies."""
        self.ocr_stats['total_attempts'] += 1
        
        # Check if OCR engine needs recovery
        if not self._check_ocr_health():
            self._recover_ocr_engine()
        
        if not self.paddle_ocr:
            self.logger.warning("PaddleOCR not available")
            self.ocr_stats['errors'] += 1
            return OCRResult(debug_info={'error': 'OCR not available'})
        
        try:
            # Garbage collection before OCR
            gc.collect()
            
            # Get multiple preprocessed versions
            preprocessed_images = self.preprocess_image_enhanced(image, cell_id)
            
            best_result = None
            best_confidence = 0
            all_results = []
            
            # Try OCR on each preprocessed image
            for i, processed_img in enumerate(preprocessed_images):
                try:
                    results = self.paddle_ocr.ocr(processed_img, cls=True)
                    
                    if results and results[0]:
                        for detection in results[0]:
                            if detection[1]:  # Has text result
                                text = detection[1][0]
                                confidence = detection[1][1]
                                
                                # Log all detections in debug mode
                                if self.debug_mode:
                                    self.logger.debug(f"{cell_id} Strategy {i}: '{text}' (conf: {confidence:.2f})")
                                
                                all_results.append({
                                    'text': text,
                                    'confidence': confidence,
                                    'strategy': i
                                })
                                
                                # Update best result
                                if confidence > best_confidence:
                                    best_confidence = confidence
                                    position = (int(detection[0][0][0]), int(detection[0][0][1]))
                                    best_result = OCRResult(
                                        text, 
                                        confidence, 
                                        position,
                                        debug_info={
                                            'strategy': i,
                                            'all_results': all_results
                                        }
                                    )
                                    
                except Exception as e:
                    self.logger.debug(f"OCR failed on strategy {i}: {e}")
                    continue
            
            if best_result:
                self.ocr_stats['successful_detections'] += 1
                self.logger.info(f"✅ {cell_id}: Best OCR result: '{best_result.text}' (conf: {best_result.confidence:.2f})")
                return best_result
            else:
                self.ocr_stats['empty_results'] += 1
                self.logger.debug(f"⚪ {cell_id}: No OCR results from any strategy")
                return OCRResult(debug_info={'all_results': all_results})
                
        except Exception as e:
            self.ocr_stats['errors'] += 1
            self.ocr_stats['last_error_time'] = time.time()
            
            error_msg = str(e).lower()
            
            # Enhanced error handling with match-case
            match error_msg:
                case msg if "primitive" in msg:
                    self.logger.error(f"PaddleOCR primitive error for {cell_id}, marking for recovery")
                    self.paddle_ocr = None
                    EnhancedOCRService._shared_paddle_ocr = None
                case msg if "memory" in msg or "allocation" in msg:
                    self.logger.error(f"Memory error for {cell_id}, forcing cleanup")
                    gc.collect()
                case msg if "timeout" in msg:
                    self.logger.warning(f"OCR timeout for {cell_id}, may need optimization")
                case _:
                    self.logger.error(f"OCR processing failed for {cell_id}: {e}")
                
            return OCRResult(debug_info={'error': str(e)})
    
    def _check_ocr_health(self) -> bool:
        """Check if OCR engine is healthy."""
        if not self.paddle_ocr:
            return False
            
        # Check error rate
        if self.ocr_stats['total_attempts'] > 10:
            error_rate = self.ocr_stats['errors'] / self.ocr_stats['total_attempts']
            if error_rate > 0.5:  # More than 50% errors
                self.logger.warning(f"High OCR error rate: {error_rate:.2%}")
                return False
        
        # Check if too many empty results
        if self.ocr_stats['total_attempts'] > 10:
            empty_rate = self.ocr_stats['empty_results'] / self.ocr_stats['total_attempts']
            if empty_rate > 0.8:  # More than 80% empty
                self.logger.warning(f"High empty result rate: {empty_rate:.2%}")
                # Don't mark as unhealthy, but log for debugging
        
        return True
    
    def _recover_ocr_engine(self):
        """Attempt to recover OCR engine."""
        self.logger.info("Attempting OCR engine recovery...")
        
        # Reset shared instance
        with EnhancedOCRService._ocr_lock:
            EnhancedOCRService._shared_paddle_ocr = None
            EnhancedOCRService._last_init_time = 0
        
        # Reinitialize
        self._initialize_paddle_ocr()
        
        # Reset error stats
        self.ocr_stats['errors'] = 0
        self.ocr_stats['empty_results'] = 0
        
    def check_trigger_patterns(self, ocr_result: OCRResult) -> bool:
        """Check if OCR result matches any trigger patterns."""
        if not ocr_result.is_valid():
            return False
        
        text = ocr_result.text
        
        # Filter out obvious non-Korean text
        if self._is_non_korean_text(text):
            self.logger.debug(f"Filtered non-Korean text: '{text}'")
            return False
        
        # Use enhanced OCR corrector
        is_match, matched_pattern = self.ocr_corrector.check_trigger_pattern(text)
        
        if is_match:
            self.logger.info(f"🎯 Trigger pattern detected: '{text}' -> '{matched_pattern}'")
            return True
        
        return False
    
    def _is_non_korean_text(self, text: str) -> bool:
        """Check if text is likely non-Korean (like timestamps, IDs, etc)."""
        if not text:
            return True
        
        # Check for patterns like "-1 1A 11" (timestamps, IDs)
        if re.match(r'^[-\d\s\w]+$', text) and not any(ord(c) >= 0xAC00 and ord(c) <= 0xD7A3 for c in text):
            return True
        
        # Count Korean characters
        korean_chars = sum(1 for c in text if ord(c) >= 0xAC00 and ord(c) <= 0xD7A3)
        total_chars = len(text.replace(' ', ''))
        
        # If less than 30% Korean characters, likely not Korean text
        if total_chars > 0 and korean_chars / total_chars < 0.3:
            return True
        
        return False
    
    def is_available(self) -> bool:
        """Check if OCR service is available."""
        return self.paddle_ocr is not None
    
    def get_status(self) -> dict[str, Any]:
        """Get detailed OCR service status."""
        total = self.ocr_stats['total_attempts']
        success_rate = (self.ocr_stats['successful_detections'] / total * 100) if total > 0 else 0
        empty_rate = (self.ocr_stats['empty_results'] / total * 100) if total > 0 else 0
        error_rate = (self.ocr_stats['errors'] / total * 100) if total > 0 else 0
        
        return {
            'available': self.is_available(),
            'paddleocr_installed': PADDLEOCR_AVAILABLE,
            'engine_initialized': self.paddle_ocr is not None,
            'stats': {
                'total_attempts': total,
                'success_rate': f"{success_rate:.1f}%",
                'empty_rate': f"{empty_rate:.1f}%",
                'error_rate': f"{error_rate:.1f}%",
                'debug_saves': f"{self.debug_save_count}/{self.max_debug_saves}"
            }
        }
    
    def reset_debug_saves(self):
        """Reset debug save counter."""
        self.debug_save_count = 0
        self.logger.info("Debug save counter reset")