"""
Base OCR Service - 통합된 OCR 서비스 기본 클래스
모든 OCR 구현의 공통 기능과 인터페이스를 제공합니다.
"""
from __future__ import annotations

import cv2
import gc
import logging
import numpy as np
import re
import threading
import time
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, List, Tuple
from src.core.config_manager import ConfigManager
from src.ocr.enhanced_ocr_corrector import EnhancedOCRCorrector


class OCRResult:
    """OCR 처리 결과를 담는 표준 클래스"""
    
    def __init__(self, text: str = "", confidence: float = 0.0, 
                 position: tuple[int, int] | None = None, 
                 debug_info: dict[str, Any] | None = None):
        self.text = text
        self.confidence = confidence
        self.position = position or (0, 0)
        self.normalized_text = self._normalize_text(text)
        self.debug_info = debug_info or {}
    
    def _normalize_text(self, text: str) -> str:
        """텍스트 정규화 - 공백과 특수문자 제거"""
        return re.sub(r'[^\w가-힣]', '', text)
    
    def is_valid(self) -> bool:
        """OCR 결과가 유효한지 확인"""
        return bool(self.text and self.confidence > 0)


class BaseOCRService(ABC):
    """OCR 서비스의 기본 추상 클래스"""
    
    def __init__(self, config_manager: ConfigManager):
        self.config = config_manager
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # 공통 구성 요소
        self.ocr_corrector = EnhancedOCRCorrector()
        
        # 성능 통계
        self.ocr_stats = {
            'total_attempts': 0,
            'successful_detections': 0,
            'empty_results': 0,
            'errors': 0,
            'last_error_time': 0,
            'avg_processing_time': 0.0
        }
        
        # 스레드 안전성을 위한 락
        self._stats_lock = threading.Lock()
        
        self.logger.info(f"{self.__class__.__name__} 초기화 완료")
    
    @abstractmethod
    def _initialize_ocr_engine(self) -> bool:
        """OCR 엔진 초기화 - 서브클래스에서 구현"""
        pass
    
    @abstractmethod
    def _perform_ocr_internal(self, image: np.ndarray) -> List[Tuple[str, float, Tuple[int, int]]]:
        """내부 OCR 처리 - 서브클래스에서 구현"""
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """OCR 엔진 사용 가능 여부 확인"""
        pass
    
    def preprocess_image(self, image: np.ndarray, simple_mode: bool = False) -> np.ndarray:
        """이미지 전처리 - 캐싱 최적화된 버전"""
        if image is None or image.size == 0:
            return image
        
        try:
            from ocr.preprocessing_cache import get_preprocessing_pipeline
            
            # 전역 전처리 파이프라인 사용
            pipeline = get_preprocessing_pipeline(use_cache=True, cache_size=100)
            
            scale = self.config.get('ocr_scale', 2.0)
            
            if simple_mode:
                # 간단 모드: 캐싱 없는 빠른 처리
                return pipeline.process_simple(image, scale)
            else:
                # 향상된 모드: 캐싱 적용
                return pipeline.process_enhanced(image, scale)
            
        except Exception as e:
            self.logger.error(f"이미지 전처리 오류: {e}")
            # 폴백: 기본 전처리
            return self._fallback_preprocessing(image)
    
    def _fallback_preprocessing(self, image: np.ndarray) -> np.ndarray:
        """폴백 전처리 (캐싱 실패 시)"""
        try:
            # 그레이스케일 변환
            if len(image.shape) == 3:
                gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            else:
                gray = image.copy()
            
            # 기본 스케일링
            scale = self.config.get('ocr_scale', 2.0)
            if scale > 1.0:
                height, width = gray.shape
                new_height, new_width = int(height * scale), int(width * scale)
                gray = cv2.resize(gray, (new_width, new_height), interpolation=cv2.INTER_CUBIC)
            
            # 기본 임계값
            return cv2.adaptiveThreshold(
                gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
            )
            
        except Exception as e:
            self.logger.error(f"폴백 전처리 오류: {e}")
            return image
    
    def process_image(self, image: np.ndarray, region: tuple[int, int, int, int] | None = None) -> OCRResult:
        """이미지 OCR 처리의 메인 인터페이스"""
        start_time = time.time()
        
        try:
            with self._stats_lock:
                self.ocr_stats['total_attempts'] += 1
            
            if not self.is_available():
                self.logger.error("OCR 엔진을 사용할 수 없습니다")
                return OCRResult()
            
            # 영역 추출
            if region:
                x, y, w, h = region
                if (x + w <= image.shape[1] and y + h <= image.shape[0] and 
                    x >= 0 and y >= 0 and w > 0 and h > 0):
                    image = image[y:y+h, x:x+w]
            
            # 이미지 전처리
            processed_image = self.preprocess_image(image)
            
            # OCR 실행
            ocr_results = self._perform_ocr_internal(processed_image)
            
            # 최상의 결과 선택
            best_result = self._select_best_result(ocr_results)
            
            # 텍스트 교정
            if best_result.text:
                corrected_text = self.ocr_corrector.correct_text(best_result.text)
                best_result.text = corrected_text
                best_result.normalized_text = best_result._normalize_text(corrected_text)
            
            # 통계 업데이트
            processing_time = time.time() - start_time
            self._update_stats(best_result, processing_time)
            
            return best_result
            
        except Exception as e:
            self.logger.error(f"OCR 처리 오류: {e}")
            with self._stats_lock:
                self.ocr_stats['errors'] += 1
                self.ocr_stats['last_error_time'] = time.time()
            return OCRResult()
    
    def _select_best_result(self, results: List[Tuple[str, float, Tuple[int, int]]]) -> OCRResult:
        """최상의 OCR 결과 선택"""
        if not results:
            return OCRResult()
        
        # 신뢰도가 가장 높은 결과 선택
        best = max(results, key=lambda x: x[1])
        text, confidence, position = best
        
        return OCRResult(text=text, confidence=confidence, position=position)
    
    def _update_stats(self, result: OCRResult, processing_time: float):
        """통계 업데이트"""
        with self._stats_lock:
            if result.is_valid():
                self.ocr_stats['successful_detections'] += 1
            else:
                self.ocr_stats['empty_results'] += 1
            
            # 평균 처리 시간 업데이트
            current_avg = self.ocr_stats['avg_processing_time']
            total_attempts = self.ocr_stats['total_attempts']
            
            if total_attempts > 1:
                self.ocr_stats['avg_processing_time'] = (
                    (current_avg * (total_attempts - 1) + processing_time) / total_attempts
                )
            else:
                self.ocr_stats['avg_processing_time'] = processing_time
    
    def get_stats(self) -> Dict[str, Any]:
        """OCR 통계 반환"""
        with self._stats_lock:
            stats = self.ocr_stats.copy()
            if stats['total_attempts'] > 0:
                stats['success_rate'] = (
                    stats['successful_detections'] / stats['total_attempts'] * 100
                )
            else:
                stats['success_rate'] = 0.0
            return stats
    
    def reset_stats(self):
        """통계 초기화"""
        with self._stats_lock:
            self.ocr_stats = {
                'total_attempts': 0,
                'successful_detections': 0,
                'empty_results': 0,
                'errors': 0,
                'last_error_time': 0,
                'avg_processing_time': 0.0
            }
            self.logger.info("OCR 통계가 초기화되었습니다")
    
    def cleanup(self):
        """리소스 정리"""
        gc.collect()
        self.logger.info(f"{self.__class__.__name__} 정리 완료")


class OCRServiceFactory:
    """OCR 서비스 팩토리 클래스"""
    
    @staticmethod
    def create_service(config_manager: ConfigManager) -> BaseOCRService:
        """OCR 서비스 생성 (최적화된 PaddleOCR)"""
        
        # 최적화된 PaddleOCR 서비스 우선 시도
        try:
            from ocr.optimized_paddle_service import OptimizedPaddleService
            service = OptimizedPaddleService(config_manager)
            if service.is_available():
                logging.info("최적화된 PaddleOCR 서비스 사용")
                return service
        except Exception as e:
            logging.warning(f"최적화된 PaddleOCR 서비스 생성 실패: {e}")
        
        # 기본 PaddleOCR 폴백
        try:
            from ocr.paddle_ocr_service import PaddleOCRService
            service = PaddleOCRService(config_manager)
            if service.is_available():
                logging.info("기본 PaddleOCR 서비스 사용")
                return service
        except Exception as e:
            logging.error(f"PaddleOCR 서비스 생성 실패: {e}")
        
        # 모든 OCR 엔진 실패 시 예외 발생
        raise RuntimeError("사용 가능한 OCR 엔진이 없습니다")