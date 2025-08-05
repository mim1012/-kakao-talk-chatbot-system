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
import sys
import os
from typing import Any
from core.config_manager import ConfigManager
from ocr.enhanced_ocr_corrector import EnhancedOCRCorrector
from utils.suppress_output import suppress_stdout_stderr

# Try to import OCR engines with graceful fallback
try:
    from paddleocr import PaddleOCR
    from ocr.safe_paddleocr import create_safe_paddleocr
    PADDLEOCR_AVAILABLE = True
except ImportError:
    PADDLEOCR_AVAILABLE = False
    logging.warning("PaddleOCR not available.")

try:
    import easyocr
    EASYOCR_AVAILABLE = True
except ImportError:
    EASYOCR_AVAILABLE = False
    logging.warning("EasyOCR not available.")


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
        
        # Debug mode temporarily enabled to check OCR results
        self.debug_mode = True
        self.debug_save_count = 0
        self.max_debug_saves = 0  # 디버그 저장 비활성화
        self.save_preprocessed = False  # 전처리 이미지 저장 비활성화
        
        # Performance metrics
        self.ocr_stats = {
            'total_attempts': 0,
            'successful_detections': 0,
            'empty_results': 0,
            'errors': 0,
            'last_error_time': 0
        }
        
        # OCR 엔진 초기화 - config에 따라 선택
        self.use_easyocr = getattr(config_manager, 'use_easyocr', False)
        self.paddle_ocr = None
        self.easy_ocr = None
        
        # config에서 use_easyocr 값을 직접 확인
        config_use_easyocr = config_manager.get('use_easyocr', False)
        
        if config_use_easyocr and EASYOCR_AVAILABLE:
            self._initialize_easy_ocr()
        elif PADDLEOCR_AVAILABLE:
            self._initialize_paddle_ocr()
        else:
            self.logger.error("No OCR engine available!")
    
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
                # Suppress all output during PaddleOCR initialization
                with suppress_stdout_stderr():
                    # Use safe PaddleOCR initialization for Python 3.11 compatibility
                    EnhancedOCRService._shared_paddle_ocr = create_safe_paddleocr()
                
                if EnhancedOCRService._shared_paddle_ocr is None:
                    # Fallback to basic initialization
                    EnhancedOCRService._shared_paddle_ocr = PaddleOCR(
                        lang='korean',
                        use_angle_cls=False,
                        enable_mkldnn=False
                    )
                
                self.paddle_ocr = EnhancedOCRService._shared_paddle_ocr
                EnhancedOCRService._last_init_time = current_time
                self.logger.info("PaddleOCR initialized successfully with enhanced settings")
                
            except Exception as e:
                self.logger.error(f"Failed to initialize PaddleOCR: {e}")
                self.paddle_ocr = None
    
    def _initialize_easy_ocr(self) -> None:
        """Initialize EasyOCR with Korean language support."""
        try:
            # EasyOCR 초기화
            languages = getattr(self.config, 'easyocr_languages', ['ko'])
            self.easy_ocr = easyocr.Reader(languages, gpu=False)
            self.logger.info(f"EasyOCR initialized successfully with languages: {languages}")
        except Exception as e:
            self.logger.error(f"Failed to initialize EasyOCR: {e}")
            self.easy_ocr = None
    
    def _run_easyocr(self, image: np.ndarray) -> list:
        """Run EasyOCR and return results in a format compatible with PaddleOCR."""
        try:
            # EasyOCR 실행
            results = self.easy_ocr.readtext(image)
            
            # EasyOCR 결과를 PaddleOCR 호환 형식으로 변환
            formatted_results = []
            for (bbox, text, confidence) in results:
                formatted_results.append([bbox, (text, confidence)])
            
            return [formatted_results] if formatted_results else []
            
        except Exception as e:
            self.logger.error(f"EasyOCR execution failed: {e}")
            return []
    
    def _extract_text_confidence(self, results: list) -> list[tuple[str, float]]:
        """Extract text and confidence pairs from OCR results (EasyOCR or PaddleOCR)."""
        text_confidence_pairs = []
        
        try:
            if not results or len(results) == 0:
                if self.debug_mode:
                    self.logger.info("결과가 비어있음")
                return text_confidence_pairs
            
            if self.debug_mode:
                self.logger.info(f"결과 파싱 시작 - 결과 수: {len(results)}")
            
            # PaddleX 새로운 딕셔너리 형식 처리 (v3.1.0+)
            if isinstance(results[0], dict) and 'rec_texts' in results[0] and 'rec_scores' in results[0]:
                rec_texts = results[0]['rec_texts']
                rec_scores = results[0]['rec_scores']
                text_confidence_pairs = list(zip(rec_texts, rec_scores))
                if len(text_confidence_pairs) > 0:
                    self.logger.info(f"PaddleX 딕셔너리 형식으로 파싱됨: {len(text_confidence_pairs)}개 텍스트")
                    for text, score in text_confidence_pairs:
                        self.logger.info(f"감지된 텍스트: '{text}' (신뢰도: {score:.2f})")
            # PaddleX 객체 형식 처리 (이전 버전)
            elif hasattr(results[0], 'rec_texts') and hasattr(results[0], 'rec_scores'):
                rec_texts = results[0].rec_texts
                rec_scores = results[0].rec_scores
                text_confidence_pairs = list(zip(rec_texts, rec_scores))
                if self.debug_mode:
                    self.logger.info(f"PaddleX 객체 형식으로 파싱됨: {len(text_confidence_pairs)}개 텍스트")
            
            # 표준 PaddleOCR/EasyOCR 형식 처리
            elif isinstance(results[0], list):
                if self.debug_mode:
                    self.logger.info(f"표준 형식으로 파싱 중 - 첫 번째 결과 길이: {len(results[0])}")
                for line in results[0]:
                    if len(line) >= 2 and isinstance(line[1], tuple) and len(line[1]) >= 2:
                        text, confidence = line[1]
                        text_confidence_pairs.append((text, confidence))
                        if self.debug_mode:
                            self.logger.info(f"추출된 텍스트: '{text}' (신뢰도: {confidence:.2f})")
            else:
                if self.debug_mode:
                    self.logger.warning(f"알 수 없는 결과 형식: {type(results[0])}")
            
            if self.debug_mode:
                self.logger.info(f"최종 추출된 텍스트 수: {len(text_confidence_pairs)}")
            
            return text_confidence_pairs
            
        except Exception as e:
            self.logger.error(f"Failed to extract text/confidence: {e}")
            if self.debug_mode:
                self.logger.error(f"결과 구조: {results}")
            return []
    
    def preprocess_image_enhanced(self, image: np.ndarray, cell_id: str = "") -> list[np.ndarray]:
        """Enhanced preprocessing with multiple strategies."""
        # 빠른 모드 확인
        fast_mode = self.config.get('fast_ocr_mode', True)
        
        if fast_mode:
            return self._preprocess_fast(image, cell_id)
        
        # 기존의 복잡한 전처리 (비활성화)
        return self._preprocess_full(image, cell_id)
    
    def _preprocess_fast(self, image: np.ndarray, cell_id: str = "") -> list[np.ndarray]:
        """빠른 전처리 - 최소한의 처리만"""
        preprocessed_images = []
        
        try:
            # RGBA 처리
            if len(image.shape) == 3 and image.shape[2] == 4:
                image = cv2.cvtColor(image, cv2.COLOR_RGBA2RGB)
            
            # 그레이스케일 변환
            if len(image.shape) == 3:
                gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
            else:
                gray = image.copy()
            
            # 1. 원본 (이미 깨끗한 텍스트용)
            preprocessed_images.append(image.copy())
            
            # 2. 간단한 이진화 (OTSU)
            _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            preprocessed_images.append(binary)
            
            # 3. 크기가 작으면 2배 확대 후 이진화
            height, width = gray.shape
            if width < 400 or height < 150:
                upscaled = cv2.resize(gray, (width * 2, height * 2), interpolation=cv2.INTER_LINEAR)
                _, binary_upscaled = cv2.threshold(upscaled, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
                preprocessed_images.append(binary_upscaled)
            
            return preprocessed_images
            
        except Exception as e:
            self.logger.error(f"Fast preprocessing failed: {e}")
            return [image]
    
    def _preprocess_full(self, image: np.ndarray, cell_id: str = "") -> list[np.ndarray]:
        """기존의 전체 전처리 (현재 비활성화)"""
        # 기존 코드를 여기로 이동...
        preprocessed_images = []
        
        try:
            # Handle RGBA → RGB conversion first
            if len(image.shape) == 3 and image.shape[2] == 4:
                # RGBA to RGB conversion
                image = cv2.cvtColor(image, cv2.COLOR_RGBA2RGB)
                self.logger.debug(f"Converted RGBA to RGB for {cell_id}")
            
            # Strategy 1: Original image (for already clear text)
            preprocessed_images.append(image.copy())
            
            # Convert to grayscale if needed  
            if len(image.shape) == 3:
                gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
            else:
                gray = image.copy()
            
            # Strategy 2: Aggressive upscaling for Korean text
            height, width = gray.shape
            # 더 적극적인 확대 - 카카오톡 텍스트는 보통 작음
            min_width, min_height = 600, 200  # 최소 크기 증가
            if width < min_width or height < min_height:
                scale_factor = max(min_width / width, min_height / height, 3.0)  # 최소 3배 확대
                new_width = int(width * scale_factor)
                new_height = int(height * scale_factor)
                upscaled = cv2.resize(gray, (new_width, new_height), interpolation=cv2.INTER_CUBIC)
                
                # 대비 향상
                clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
                enhanced = clahe.apply(upscaled)
                
                # Sharpen
                kernel = np.array([[-1,-1,-1], [-1,9,-1], [-1,-1,-1]])
                sharpened = cv2.filter2D(enhanced, -1, kernel)
                preprocessed_images.append(sharpened)
                
                if self.debug_mode:
                    self.logger.info(f"이미지 확대: {width}x{height} → {new_width}x{new_height} (x{scale_factor:.1f})")
            
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
            
            # Debug image saving disabled to prevent clutter
            
            return preprocessed_images
            
        except Exception as e:
            self.logger.error(f"Image preprocessing failed for {cell_id}: {e}")
            return [image]  # Return original if preprocessing fails
    
    def _save_debug_images(self, images: list[np.ndarray], cell_id: str):
        """Debug image saving disabled."""
        pass  # 디버그 이미지 저장 비활성화
    
    def perform_ocr_with_recovery(self, image: np.ndarray, cell_id: str = "") -> OCRResult:
        """Perform OCR with automatic recovery and multiple strategies."""
        self.ocr_stats['total_attempts'] += 1
        
        # Check if OCR engine needs recovery
        if not self._check_ocr_health():
            self._recover_ocr_engine()
        
        if not self.paddle_ocr and not self.easy_ocr:
            self.logger.warning("No OCR engine available")
            self.ocr_stats['errors'] += 1
            return OCRResult(debug_info={'error': 'OCR not available'})
        
        try:
            # Garbage collection before OCR
            gc.collect()
            
            # 이미지 정보 로깅
            if self.debug_mode:
                self.logger.info(f"OCR 시작 - {cell_id}: 이미지 크기 {image.shape}, 평균값: {image.mean():.1f}")
            
            # Get multiple preprocessed versions
            preprocessed_images = self.preprocess_image_enhanced(image, cell_id)
            
            if self.debug_mode:
                self.logger.info(f"전처리 완료 - {cell_id}: {len(preprocessed_images)}개 이미지 생성")
            
            best_result = None
            best_confidence = -1  # -1로 초기화하여 모든 결과가 고려되도록 함
            all_results = []
            trigger_results = []  # 트리거 패턴이 포함된 결과들
            
            # Try OCR on each preprocessed image
            for i, processed_img in enumerate(preprocessed_images):
                try:
                    # Use PaddleOCR (EasyOCR disabled)
                    if self.debug_mode:
                        self.logger.info(f"PaddleOCR 실행 중 - {cell_id} Strategy {i}")
                    
                    results = self.paddle_ocr.ocr(processed_img)
                    
                    if self.debug_mode:
                        self.logger.info(f"PaddleOCR 결과 - {cell_id} Strategy {i}: {len(results) if results else 0}개 결과")
                        if results:
                            self.logger.info(f"결과 타입: {type(results)}, 첫 번째 결과: {type(results[0]) if results else 'None'}")
                    
                    if results and len(results) > 0:
                        # 통합된 결과 처리 (EasyOCR/PaddleOCR 모두 지원)
                        text_confidence_pairs = self._extract_text_confidence(results)
                        
                        # 모든 감지된 텍스트 로그 출력
                        if text_confidence_pairs:
                            print(f"\n🔍 [OCR 감지] Strategy {i} - {len(text_confidence_pairs)}개 텍스트 발견:")
                            for idx, (t, c) in enumerate(text_confidence_pairs):
                                print(f"   [{idx}] '{t}' (신뢰도: {c:.2f})")
                        
                        for j, (text, confidence) in enumerate(text_confidence_pairs):
                                # 로그 텍스트 필터링
                                if self._is_log_text(text):
                                    if self.debug_mode:
                                        self.logger.debug(f"{cell_id}: 로그 텍스트 건너뛰기 - '{text}'")
                                    continue
                                
                                # Log only high confidence detections in debug mode
                                if self.debug_mode and confidence > 0.7:
                                    self.logger.debug(f"{cell_id} Strategy {i}: '{text}' (conf: {confidence:.2f})")
                                
                                all_results.append({
                                    'text': text,
                                    'confidence': confidence,
                                    'strategy': i
                                })
                                
                                # Update best result
                                # 트리거 패턴이 포함된 텍스트를 우선적으로 선택
                                is_trigger_text = any(pattern in text for pattern in self.config.get('trigger_patterns', []))
                                
                                # 트리거 패턴이 있거나 신뢰도가 더 높은 경우 업데이트
                                should_update = False
                                if is_trigger_text and confidence > 0.3:
                                    # 트리거 패턴이 있으면 낮은 신뢰도(0.3)도 허용
                                    should_update = True
                                elif confidence > best_confidence and not any(pattern in best_result.text if best_result else '' for pattern in self.config.get('trigger_patterns', [])):
                                    # 현재 최고 결과가 트리거가 아니고, 새 결과가 더 높은 신뢰도면 선택
                                    should_update = True
                                
                                if should_update:
                                    best_confidence = confidence
                                    # PaddleX 형식에서는 position을 다르게 처리
                                    position = (0, 0)  # 기본값
                                    if hasattr(results[0], 'rec_polys') and len(results[0].rec_polys) > j:
                                        poly = results[0].rec_polys[j]
                                        if len(poly) > 0:
                                            position = (int(poly[0][0]), int(poly[0][1]))
                                    
                                    best_result = OCRResult(
                                        text, 
                                        confidence, 
                                        position,
                                        debug_info={
                                            'strategy': i,
                                            'all_results': all_results
                                        }
                                    )
                        else:
                            # 기존 형식 처리 (리스트 형식)
                            for detection in results[0]:
                                if detection[1]:  # Has text result
                                    text = detection[1][0]
                                    confidence = detection[1][1]
                                    
                                    # 로그 텍스트 필터링
                                    if self._is_log_text(text):
                                        if self.debug_mode:
                                            self.logger.debug(f"{cell_id}: 로그 텍스트 건너뛰기 - '{text}'")
                                        continue
                                    
                                    # Log only high confidence detections in debug mode
                                    if self.debug_mode and confidence > 0.7:
                                        self.logger.debug(f"{cell_id} Strategy {i}: '{text}' (conf: {confidence:.2f})")
                                    
                                    all_results.append({
                                        'text': text,
                                        'confidence': confidence,
                                        'strategy': i
                                    })
                                    
                                    # Update best result
                                    # 트리거 패턴이 포함된 텍스트를 우선적으로 선택
                                    is_trigger_text = any(pattern in text for pattern in self.config.get('trigger_patterns', []))
                                    
                                    # 트리거 패턴이 있거나 신뢰도가 더 높은 경우 업데이트
                                    should_update = False
                                    if is_trigger_text and confidence > 0.3:
                                        # 트리거 패턴이 있고 신뢰도가 충분하면 선택
                                        should_update = True
                                    elif confidence > best_confidence and not any(pattern in best_result.text if best_result else '' for pattern in self.config.get('trigger_patterns', [])):
                                        # 현재 최고 결과가 트리거가 아니고, 새 결과가 더 높은 신뢰도면 선택
                                        should_update = True
                                    
                                    if should_update:
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
            
            # 트리거 패턴이 있는 결과를 우선 확인
            best_trigger_result = None
            best_trigger_confidence = 0
            
            for res in all_results:
                text = res.get('text', '')
                conf = res.get('confidence', 0)
                
                # 로그 텍스트는 건너뛰기
                if self._is_log_text(text):
                    continue
                    
                for pattern in self.config.get('trigger_patterns', []):
                    if pattern in text and conf > best_trigger_confidence:
                        best_trigger_confidence = conf
                        best_trigger_result = OCRResult(
                            text,
                            conf,
                            debug_info={'all_results': all_results, 'trigger_found': True}
                        )
                        self.logger.info(f"🎯 트리거 패턴 발견: '{text}' (신뢰도: {conf:.2f})")
            
            # 트리거 패턴이 있으면 우선 반환
            if best_trigger_result:
                self.ocr_stats['successful_detections'] += 1
                return best_trigger_result
            
            # 트리거 패턴이 없으면 기존 best_result 반환
            if best_result:
                self.ocr_stats['successful_detections'] += 1
                self.logger.info(f"✅ OCR 최종 선택: '{best_result.text}' (신뢰도: {best_result.confidence:.2f})")
                return best_result
            else:
                # best_result가 없어도 all_results에서 트리거 패턴 찾기
                for res in all_results:
                    text = res.get('text', '')
                    if text and any(pattern in text for pattern in self.config.get('trigger_patterns', [])):
                        # 트리거 패턴이 있으면 해당 결과 반환
                        return OCRResult(
                            text,
                            res.get('confidence', 0.9),
                            debug_info={'all_results': all_results, 'fallback': True}
                        )
                
                self.ocr_stats['empty_results'] += 1
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
        
        # 로그 텍스트 필터링 - OCR이 로그 창을 읽는 것 방지
        if self._is_log_text(text):
            self.logger.debug(f"로그 텍스트 필터링: '{text}'")
            return False
        
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
    
    def _is_log_text(self, text: str) -> bool:
        """로그 창의 텍스트인지 확인"""
        # 로그 패턴들
        log_patterns = [
            r'\[\d{2}:\d{2}:\d{2}\]',  # [02:23:40] 같은 타임스탬프
            r'OCR \uac10\uc9c0:',  # 'OCR 감지:' 텍스트
            r'\uac10\uc9c0:',  # '감지:' 텍스트
            r'\uc790\ub3d9\ud654:',  # '자동화:' 텍스트
            r'\[TARGET\]',  # '[TARGET]' 텍스트
            r'\[OK\]',  # '[OK]' 텍스트
            r'\uc2e0\ub8b0\ub3c4:',  # '신뢰도:' 텍스트
            r'monitor_\d+_cell_\d+_\d+',  # 셀 ID 패턴
        ]
        
        for pattern in log_patterns:
            if re.search(pattern, text):
                return True
        
        # 로그에서 흔히 볼 수 있는 특수 문자 조합
        if "'(" in text and ")" in text:  # '(신뢰도:' 같은 패턴
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
    
    def get_statistics(self) -> dict[str, Any]:
        """Get OCR service statistics (alias for get_status)."""
        return self.get_status()