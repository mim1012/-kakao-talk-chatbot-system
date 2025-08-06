"""
OCR 전처리 캐시 시스템
전처리 단계별 결과를 캐싱하여 성능을 최적화합니다.
"""
from __future__ import annotations

import hashlib
import cv2
import numpy as np
import threading
import time
from typing import Dict, Optional, Tuple, Any
from collections import OrderedDict
import logging


class PreprocessingStep:
    """전처리 단계를 나타내는 클래스"""
    
    def __init__(self, name: str, func: callable, params: Dict[str, Any]):
        self.name = name
        self.func = func
        self.params = params
        self.cache_key = self._generate_cache_key()
    
    def _generate_cache_key(self) -> str:
        """파라미터 기반 캐시 키 생성"""
        params_str = str(sorted(self.params.items()))
        return hashlib.md5(f"{self.name}_{params_str}".encode()).hexdigest()[:8]
    
    def apply(self, image: np.ndarray) -> np.ndarray:
        """전처리 단계 적용"""
        return self.func(image, **self.params)


class PreprocessingCache:
    """전처리 단계별 캐시 시스템"""
    
    def __init__(self, max_cache_size: int = 100, ttl_seconds: int = 300):
        self.max_cache_size = max_cache_size
        self.ttl_seconds = ttl_seconds
        self.cache: OrderedDict[str, Tuple[np.ndarray, float]] = OrderedDict()
        self.lock = threading.RLock()
        self.logger = logging.getLogger(__name__)
        
        # 히트/미스 통계
        self.hits = 0
        self.misses = 0
    
    def _generate_image_hash(self, image: np.ndarray, step_key: str) -> str:
        """이미지와 단계 조합의 해시 생성"""
        image_bytes = image.tobytes()
        combined = f"{hashlib.md5(image_bytes).hexdigest()[:8]}_{step_key}"
        return hashlib.md5(combined.encode()).hexdigest()
    
    def get(self, image: np.ndarray, step: PreprocessingStep) -> Optional[np.ndarray]:
        """캐시에서 전처리 결과 가져오기"""
        cache_key = self._generate_image_hash(image, step.cache_key)
        
        with self.lock:
            if cache_key in self.cache:
                cached_result, timestamp = self.cache[cache_key]
                
                # TTL 확인
                if time.time() - timestamp <= self.ttl_seconds:
                    # LRU 업데이트
                    self.cache.move_to_end(cache_key)
                    self.hits += 1
                    return cached_result.copy()
                else:
                    # 만료된 항목 제거
                    del self.cache[cache_key]
            
            self.misses += 1
            return None
    
    def put(self, image: np.ndarray, step: PreprocessingStep, result: np.ndarray):
        """전처리 결과를 캐시에 저장"""
        cache_key = self._generate_image_hash(image, step.cache_key)
        
        with self.lock:
            # 크기 제한 확인
            if len(self.cache) >= self.max_cache_size:
                # 가장 오래된 항목 제거
                self.cache.popitem(last=False)
            
            # 새 결과 저장
            self.cache[cache_key] = (result.copy(), time.time())
    
    def get_stats(self) -> Dict[str, Any]:
        """캐시 통계 반환"""
        with self.lock:
            total = self.hits + self.misses
            hit_rate = (self.hits / total * 100) if total > 0 else 0
            
            return {
                'hits': self.hits,
                'misses': self.misses,
                'hit_rate': hit_rate,
                'cache_size': len(self.cache),
                'max_cache_size': self.max_cache_size
            }
    
    def clear(self):
        """캐시 초기화"""
        with self.lock:
            self.cache.clear()
            self.hits = 0
            self.misses = 0


class PreprocessingPipeline:
    """최적화된 전처리 파이프라인"""
    
    def __init__(self, use_cache: bool = True, cache_size: int = 100):
        self.use_cache = use_cache
        self.cache = PreprocessingCache(cache_size) if use_cache else None
        self.logger = logging.getLogger(__name__)
        
        # 미리 컴파일된 OpenCV 커널들
        self._kernels = self._precompile_kernels()
        
        # CLAHE 인스턴스 재사용
        self._clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    
    def _precompile_kernels(self) -> Dict[str, np.ndarray]:
        """OpenCV 커널 미리 컴파일"""
        return {
            'morph_rect_2x2': cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2)),
            'morph_rect_3x3': cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3)),
            'morph_ellipse_3x3': cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3)),
            'sharpen_kernel': np.array([[-1, -1, -1], [-1, 9, -1], [-1, -1, -1]])
        }
    
    def _scale_image(self, image: np.ndarray, scale: float = 2.0) -> np.ndarray:
        """이미지 스케일링"""
        if scale <= 1.0:
            return image
        
        height, width = image.shape[:2]
        new_height, new_width = int(height * scale), int(width * scale)
        return cv2.resize(image, (new_width, new_height), interpolation=cv2.INTER_CUBIC)
    
    def _denoise_image(self, image: np.ndarray) -> np.ndarray:
        """노이즈 제거"""
        return cv2.bilateralFilter(image, 9, 75, 75)
    
    def _enhance_contrast(self, image: np.ndarray) -> np.ndarray:
        """대비 향상 (CLAHE 재사용)"""
        return self._clahe.apply(image)
    
    def _apply_threshold(self, image: np.ndarray, block_size: int = 11, C: int = 2) -> np.ndarray:
        """적응형 임계값"""
        return cv2.adaptiveThreshold(
            image, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, block_size, C
        )
    
    def _morphology_close(self, image: np.ndarray, kernel_size: str = 'morph_rect_2x2') -> np.ndarray:
        """모폴로지 닫힘 연산"""
        kernel = self._kernels[kernel_size]
        return cv2.morphologyEx(image, cv2.MORPH_CLOSE, kernel)
    
    def _sharpen_image(self, image: np.ndarray) -> np.ndarray:
        """샤프닝 (미리 컴파일된 커널 사용)"""
        kernel = self._kernels['sharpen_kernel']
        return cv2.filter2D(image, -1, kernel)
    
    def process_simple(self, image: np.ndarray, scale: float = 2.0) -> np.ndarray:
        """간단 모드 전처리 (캐싱 없음)"""
        try:
            # 그레이스케일 변환
            if len(image.shape) == 3:
                gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            else:
                gray = image.copy()
            
            # 스케일링
            if scale > 1.0:
                gray = self._scale_image(gray, scale)
            
            # 적응형 임계값만 적용
            return self._apply_threshold(gray)
            
        except Exception as e:
            self.logger.error(f"간단 전처리 오류: {e}")
            return image
    
    def process_enhanced(self, image: np.ndarray, scale: float = 2.0) -> np.ndarray:
        """향상된 전처리 (캐싱 적용)"""
        try:
            # 그레이스케일 변환
            if len(image.shape) == 3:
                gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            else:
                gray = image.copy()
            
            # 전처리 단계 정의 (캐싱할 단계들)
            steps = [
                PreprocessingStep('scale', self._scale_image, {'scale': scale}),
                PreprocessingStep('denoise', self._denoise_image, {}),
                PreprocessingStep('contrast', self._enhance_contrast, {}),
                PreprocessingStep('threshold', self._apply_threshold, {'block_size': 11, 'C': 2}),
                PreprocessingStep('morphology', self._morphology_close, {'kernel_size': 'morph_rect_2x2'})
            ]
            
            # 파이프라인 실행
            result = gray
            for step in steps:
                if self.use_cache and self.cache:
                    # 캐시에서 시도
                    cached_result = self.cache.get(result, step)
                    if cached_result is not None:
                        result = cached_result
                        continue
                
                # 캐시 미스 - 실제 처리
                processed = step.apply(result)
                
                # 결과 캐싱
                if self.use_cache and self.cache:
                    self.cache.put(result, step, processed)
                
                result = processed
            
            return result
            
        except Exception as e:
            self.logger.error(f"향상된 전처리 오류: {e}")
            # 간단 모드로 폴백
            return self.process_simple(image, scale)
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """캐시 통계 반환"""
        if self.cache:
            return self.cache.get_stats()
        return {'cache_enabled': False}
    
    def clear_cache(self):
        """캐시 초기화"""
        if self.cache:
            self.cache.clear()


# 전역 파이프라인 인스턴스 (싱글톤 패턴)
_global_pipeline = None
_pipeline_lock = threading.Lock()


def get_preprocessing_pipeline(use_cache: bool = True, cache_size: int = 100) -> PreprocessingPipeline:
    """전역 전처리 파이프라인 인스턴스 반환"""
    global _global_pipeline
    
    with _pipeline_lock:
        if _global_pipeline is None:
            _global_pipeline = PreprocessingPipeline(use_cache, cache_size)
        return _global_pipeline