"""
EasyOCR 서비스 (PaddleOCR 대체)
"""
from __future__ import annotations

import time
import logging
import numpy as np
from typing import Optional, List, Tuple, Dict, Any
from concurrent.futures import ThreadPoolExecutor
import cv2

try:
    import easyocr
    EASYOCR_AVAILABLE = True
except ImportError:
    EASYOCR_AVAILABLE = False
    logging.warning("EasyOCR not available")

class EasyOCRResult:
    """EasyOCR 결과"""
    
    def __init__(self, text: str = "", confidence: float = 0.0, 
                 position: Optional[Tuple[int, int]] = None,
                 processing_time_ms: float = 0.0):
        self.text = text
        self.confidence = confidence
        self.position = position or (0, 0)
        self.processing_time_ms = processing_time_ms
        self.timestamp = time.time()

class EasyOCRService:
    """EasyOCR 서비스"""
    
    def __init__(self, config=None):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # EasyOCR Reader
        self.reader = None
        if EASYOCR_AVAILABLE:
            self._init_easyocr()
        
        # 스레드 풀
        self.executor = ThreadPoolExecutor(max_workers=4)
        
        # 트리거 패턴
        self.trigger_patterns = ["들어왔습니다", "입장했습니다", "참여했습니다"]
        
    def _init_easyocr(self):
        """EasyOCR 초기화"""
        try:
            # GPU 사용 가능하면 GPU, 아니면 CPU
            self.reader = easyocr.Reader(['ko', 'en'], gpu=False)
            self.logger.info("EasyOCR 초기화 완료")
        except Exception as e:
            self.logger.error(f"EasyOCR 초기화 실패: {e}")
            self.reader = None
    
    def preprocess_image(self, image: np.ndarray) -> np.ndarray:
        """이미지 전처리"""
        try:
            # 크기 조정
            height, width = image.shape[:2]
            if width < 100 or height < 50:
                scale = 3
                new_width = int(width * scale)
                new_height = int(height * scale)
                image = cv2.resize(image, (new_width, new_height), 
                                 interpolation=cv2.INTER_CUBIC)
            
            # 그레이스케일 변환
            if len(image.shape) == 3:
                gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            else:
                gray = image
            
            # 대비 향상
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
            enhanced = clahe.apply(gray)
            
            # 3채널로 변환 (EasyOCR은 3채널 필요)
            if len(enhanced.shape) == 2:
                enhanced = cv2.cvtColor(enhanced, cv2.COLOR_GRAY2BGR)
            
            return enhanced
            
        except Exception as e:
            self.logger.error(f"이미지 전처리 오류: {e}")
            return image
    
    def perform_ocr(self, image: np.ndarray) -> EasyOCRResult:
        """OCR 수행"""
        start_time = time.time()
        
        if not self.reader:
            return EasyOCRResult()
        
        try:
            # 전처리
            processed = self.preprocess_image(image)
            
            # OCR 실행
            results = self.reader.readtext(processed)
            
            if not results:
                return EasyOCRResult()
            
            # 텍스트 추출
            all_text = []
            total_confidence = 0
            count = 0
            
            for bbox, text, confidence in results:
                if confidence > 0.3:  # 신뢰도 임계값
                    all_text.append(text)
                    total_confidence += confidence
                    count += 1
            
            if not all_text:
                return EasyOCRResult()
            
            combined_text = ' '.join(all_text)
            avg_confidence = total_confidence / count if count > 0 else 0
            
            processing_time = (time.time() - start_time) * 1000
            
            return EasyOCRResult(
                text=combined_text,
                confidence=avg_confidence,
                processing_time_ms=processing_time
            )
            
        except Exception as e:
            self.logger.error(f"OCR 처리 오류: {e}")
            return EasyOCRResult()
    
    def perform_batch_ocr(self, images_with_regions: List[Tuple[np.ndarray, Tuple[int, int, int, int]]]) -> List[EasyOCRResult]:
        """배치 OCR 처리"""
        futures = []
        
        for image, region in images_with_regions:
            future = self.executor.submit(self.perform_ocr, image)
            futures.append(future)
        
        results = []
        for future in futures:
            try:
                result = future.result(timeout=2.0)
                results.append(result)
            except Exception as e:
                self.logger.error(f"배치 OCR 오류: {e}")
                results.append(EasyOCRResult())
        
        return results
    
    def check_trigger_patterns(self, text: str) -> bool:
        """트리거 패턴 확인"""
        if not text:
            return False
        
        # 기본 패턴 확인
        for pattern in self.trigger_patterns:
            if pattern in text:
                return True
        
        # OCR 오류 보정
        error_patterns = [
            "들어왔습니다", "들머왔습니다", "들어았습니다",
            "입장했습니다", "입장했습니다", "입장했슴니다",
            "참여했습니다", "참여했습니다", "참여했슴니다"
        ]
        
        for pattern in error_patterns:
            if pattern in text:
                return True
        
        return False
    
    def cleanup(self):
        """리소스 정리"""
        self.executor.shutdown(wait=True)
        self.logger.info("EasyOCR 서비스 정리 완료")