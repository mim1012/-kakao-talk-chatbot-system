"""
OCR service module for text detection and recognition.
Handles PaddleOCR initialization, image preprocessing, and trigger pattern matching.
"""
from __future__ import annotations

import cv2
import gc
import logging
import numpy as np
import re
import sys
import os
from typing import Any
from core.config_manager import ConfigManager
from ocr.enhanced_ocr_corrector import EnhancedOCRCorrector
from utils.suppress_output import suppress_stdout_stderr

# Try to import PaddleOCR with graceful fallback
try:
    from paddleocr import PaddleOCR
    PADDLEOCR_AVAILABLE = True
except ImportError:
    PADDLEOCR_AVAILABLE = False
    logging.warning("PaddleOCR not available. OCR functionality will be disabled.")


class OCRResult:
    """Result of OCR processing."""
    
    def __init__(self, text: str = "", confidence: float = 0.0, position: tuple[int, int] | None = None):
        self.text = text
        self.confidence = confidence
        self.position = position or (0, 0)
        self.normalized_text = self._normalize_text(text)
    
    def _normalize_text(self, text: str) -> str:
        """Normalize text by removing spaces and special characters."""
        return re.sub(r'[^\w가-힣]', '', text)
    
    def is_valid(self) -> bool:
        """Check if the OCR result is valid."""
        return bool(self.text and self.confidence > 0)


class OCRService:
    """Service for OCR operations and trigger pattern matching."""
    
    def __init__(self, config_manager: ConfigManager):
        self.config = config_manager
        self.logger = logging.getLogger(__name__)
        self.paddle_ocr = None
        
        # 강화된 OCR 보정기 초기화
        self.ocr_corrector = EnhancedOCRCorrector()
        self.logger.info("강화된 OCR 보정기 초기화 완료")
        
        if PADDLEOCR_AVAILABLE:
            self._initialize_paddle_ocr()
    
    def _initialize_paddle_ocr(self) -> None:
        """Initialize PaddleOCR with optimized settings."""
        try:
            # Suppress all output during PaddleOCR initialization
            with suppress_stdout_stderr():
                self.paddle_ocr = PaddleOCR(
                    lang='korean'
                )
                
            self.logger.info("PaddleOCR initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize PaddleOCR: {e}")
            self.paddle_ocr = None
    
    def preprocess_image(self, image: np.ndarray) -> np.ndarray:
        """Preprocess image for better OCR results."""
        try:
            preprocess_config = self.config.ocr_preprocess_config
            
            # Scale image
            scale = preprocess_config.get('scale', 4.0)
            if scale != 1.0:
                height, width = image.shape[:2]
                new_width = int(width * scale)
                new_height = int(height * scale)
                image = cv2.resize(image, (new_width, new_height), interpolation=cv2.INTER_CUBIC)
            
            # Convert to grayscale if not already
            if len(image.shape) == 3:
                gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            else:
                gray = image.copy()
            
            # Apply Gaussian blur if enabled
            if preprocess_config.get('gaussian_blur', True):
                gray = cv2.GaussianBlur(gray, (3, 3), 0)
            
            # Adaptive thresholding
            block_size = preprocess_config.get('adaptive_thresh_blocksize', 15)
            c_value = preprocess_config.get('adaptive_thresh_C', 4)
            binary = cv2.adaptiveThreshold(
                gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                cv2.THRESH_BINARY, block_size, c_value
            )
            
            # Invert if specified
            if preprocess_config.get('invert', True):
                binary = cv2.bitwise_not(binary)
            
            # Apply morphological operations
            if preprocess_config.get('use_morph_close', True):
                kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2))
                binary = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)
            
            # Apply sharpening
            if preprocess_config.get('apply_sharpen', True):
                kernel = np.array([[-1, -1, -1], [-1, 9, -1], [-1, -1, -1]])
                binary = cv2.filter2D(binary, -1, kernel)
            
            # Enhance contrast
            if preprocess_config.get('contrast_enhance', True):
                binary = cv2.equalizeHist(binary)
            
            return binary
            
        except Exception as e:
            self.logger.error(f"Image preprocessing failed: {e}")
            return image
    
    def perform_ocr(self, image: np.ndarray) -> OCRResult:
        """Perform OCR on the given image."""
        if not self.paddle_ocr:
            self.logger.warning("PaddleOCR not available")
            return OCRResult()
        
        try:
            # Garbage collection before OCR to manage memory
            gc.collect()
            
            # Preprocess image
            processed_image = self.preprocess_image(image)
            
            # Perform OCR
            results = self.paddle_ocr.ocr(processed_image)
            
            if not results or not results[0]:
                return OCRResult()
            
            # Extract first result
            first_result = results[0][0]
            text = first_result[1][0] if first_result[1] else ""
            confidence = first_result[1][1] if first_result[1] else 0.0
            
            # Get position of first detected text
            position = (0, 0)
            if first_result[0]:
                # Get top-left corner of bounding box
                position = (int(first_result[0][0][0]), int(first_result[0][0][1]))
            
            return OCRResult(text, confidence, position)
            
        except Exception as e:
            error_msg = str(e).lower()
            
            # Handle specific errors using match-case
            match error_msg:
                case msg if "primitive" in msg:
                    self.logger.error("PaddleOCR primitive error detected, disabling OCR engine")
                    self.paddle_ocr = None
                    return OCRResult()
                case msg if "memory" in msg or "allocation" in msg:
                    self.logger.error("Memory error in OCR processing, attempting cleanup")
                    gc.collect()
                    return OCRResult()
                case _:
                    self.logger.error(f"OCR processing failed: {e}")
                    return OCRResult()
    
    def check_trigger_patterns(self, ocr_result: OCRResult) -> bool:
        """Check if OCR result matches any trigger patterns using enhanced corrector."""
        if not ocr_result.is_valid():
            return False
        
        text = ocr_result.text
        
        # 강화된 OCR 보정기 사용
        is_match, matched_pattern = self.ocr_corrector.check_trigger_pattern(text)
        
        if is_match:
            self.logger.info(f"🎯 트리거 패턴 감지: '{text}' -> '{matched_pattern}'")
            return True
        
        # 추가 노이즈 필터링
        if self._is_likely_noise(text):
            return False
        
        return False
    
    def _apply_ocr_corrections(self, text: str) -> str:
        """Apply common OCR error corrections."""
        corrected = text
        for error, correction in self._trigger_corrections.items():
            corrected = corrected.replace(error, correction)
        return corrected
    
    def _get_pattern_variations(self, pattern: str) -> list[str]:
        """Get common OCR variations of a pattern."""
        variations = [pattern]
        
        # Add common character substitutions
        char_subs = {
            '들': ['둘', '를'],
            '어': ['머', '여'],
            '왔': ['왔', '았', '웠'],
            '습': ['슴', '습'],
            '니': ['니', '느', '시'],
            '다': ['다', '타']
        }
        
        for original_char, substitutes in char_subs.items():
            if original_char in pattern:
                for substitute in substitutes:
                    variations.append(pattern.replace(original_char, substitute))
        
        return list(set(variations))
    
    def _is_likely_noise(self, text: str) -> bool:
        """Check if text is likely to be noise/false positive."""
        if not text:
            return True
        
        # Too long (likely paragraph text)
        if len(text) > 50:
            return True
        
        # Too many numbers (likely timestamps or IDs)
        num_digits = sum(1 for c in text if c.isdigit())
        if len(text) > 3 and num_digits / len(text) > 0.5:
            return True
        
        # Too many special characters
        num_special = sum(1 for c in text if not c.isalnum() and not c.isspace())
        if len(text) > 3 and num_special / len(text) > 0.3:
            return True
        
        return False
    
    def is_available(self) -> bool:
        """Check if OCR service is available."""
        return self.paddle_ocr is not None
    
    def get_status(self) -> dict[str, Any]:
        """Get OCR service status information."""
        return {
            'available': self.is_available(),
            'paddleocr_installed': PADDLEOCR_AVAILABLE,
            'engine_initialized': self.paddle_ocr is not None
        }