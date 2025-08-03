"""
최적화된 OCR 서비스
캐싱, 성능 모니터링, GPU 가속 지원
"""
from __future__ import annotations

import cv2
import time
import logging
import numpy as np
from typing import Optional, List, Tuple, Dict, Any
from concurrent.futures import ThreadPoolExecutor, Future
import threading

from core.config_manager import ConfigManager
from core.cache_manager import CacheManager
from monitoring.performance_monitor import PerformanceMonitor
from ocr.enhanced_ocr_corrector import EnhancedOCRCorrector
from utils.suppress_output import suppress_stdout_stderr

# PaddleOCR 임포트
try:
    from paddleocr import PaddleOCR
    PADDLEOCR_AVAILABLE = True
except ImportError:
    PADDLEOCR_AVAILABLE = False
    logging.warning("PaddleOCR not available")

class OptimizedOCRResult:
    """최적화된 OCR 결과"""
    
    def __init__(self, text: str = "", confidence: float = 0.0, 
                 position: Optional[Tuple[int, int]] = None,
                 processing_time_ms: float = 0.0,
                 cache_hit: bool = False):
        self.text = text
        self.confidence = confidence
        self.position = position or (0, 0)
        self.processing_time_ms = processing_time_ms
        self.cache_hit = cache_hit
        self.timestamp = time.time()

class OptimizedOCRService:
    """최적화된 OCR 서비스"""
    
    def __init__(self, config_manager: ConfigManager, 
                 cache_manager: Optional[CacheManager] = None,
                 performance_monitor: Optional[PerformanceMonitor] = None):
        self.config = config_manager
        self.cache = cache_manager or CacheManager(config_manager._config)
        self.perf_monitor = performance_monitor
        self.logger = logging.getLogger(__name__)
        
        # OCR 엔진
        self.paddle_ocr = None
        self.ocr_corrector = EnhancedOCRCorrector()
        
        # 스레드 풀
        self.executor = ThreadPoolExecutor(
            max_workers=config_manager._config.get('max_concurrent_ocr', 6)
        )
        
        # GPU 설정
        self.use_gpu = config_manager._config.get('use_gpu', False)
        self.gpu_id = config_manager._config.get('gpu_id', 0)
        
        # 초기화
        if PADDLEOCR_AVAILABLE:
            self._init_paddle_ocr()
        
        # 통계
        self.total_ocr_count = 0
        self.cache_hit_count = 0
        
    def _init_paddle_ocr(self):
        """PaddleOCR 초기화 (GPU 지원 포함)"""
        try:
            with suppress_stdout_stderr():
                self.paddle_ocr = PaddleOCR(
                    lang='korean',
                    use_gpu=self.use_gpu,
                    gpu_id=self.gpu_id,
                    use_angle_cls=True,
                    det=True,
                    rec=True,
                    cls=True,
                    show_log=False
                )
            
            gpu_status = "GPU" if self.use_gpu else "CPU"
            self.logger.info(f"PaddleOCR 초기화 완료 ({gpu_status} 모드)")
            
        except Exception as e:
            self.logger.error(f"PaddleOCR 초기화 실패: {e}")
            self.paddle_ocr = None
    
    def preprocess_image_optimized(self, image: np.ndarray) -> np.ndarray:
        """최적화된 이미지 전처리"""
        start_time = time.time()
        
        # 캐시 확인
        cached = self.cache.get_preprocessed_image(image)
        if cached is not None:
            return cached
        
        try:
            # 크기 조정 (동적 스케일)
            height, width = image.shape[:2]
            scale = self._calculate_optimal_scale(width, height)
            
            if scale != 1.0:
                new_width = int(width * scale)
                new_height = int(height * scale)
                image = cv2.resize(image, (new_width, new_height), 
                                 interpolation=cv2.INTER_CUBIC)
            
            # 그레이스케일 변환
            if len(image.shape) == 3:
                gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            else:
                gray = image
            
            # 노이즈 제거
            denoised = cv2.fastNlMeansDenoising(gray, None, 10, 7, 21)
            
            # 대비 향상 (CLAHE)
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
            enhanced = clahe.apply(denoised)
            
            # 이진화
            _, binary = cv2.threshold(enhanced, 0, 255, 
                                    cv2.THRESH_BINARY | cv2.THRESH_OTSU)
            
            # 모폴로지 연산
            kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2))
            processed = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)
            
            # 캐시 저장
            self.cache.cache_preprocessed_image(image, processed)
            
            # 성능 기록
            if self.perf_monitor:
                processing_time = (time.time() - start_time) * 1000
                self.perf_monitor.record_capture_latency(processing_time)
            
            return processed
            
        except Exception as e:
            self.logger.error(f"이미지 전처리 오류: {e}")
            return image
    
    def _calculate_optimal_scale(self, width: int, height: int) -> float:
        """최적 스케일 계산"""
        # 작은 이미지는 확대, 큰 이미지는 축소
        min_dimension = min(width, height)
        
        if min_dimension < 50:
            return 4.0
        elif min_dimension < 100:
            return 2.0
        elif min_dimension > 500:
            return 0.5
        else:
            return 1.0
    
    def perform_ocr_cached(self, image: np.ndarray, 
                          region: Optional[Tuple[int, int, int, int]] = None) -> OptimizedOCRResult:
        """캐싱이 적용된 OCR 수행"""
        start_time = time.time()
        self.total_ocr_count += 1
        
        # 캐시 키 생성을 위한 영역 정보
        if region:
            x, y, w, h = region
            
            # 캐시 확인
            cached_result = self.cache.get_ocr_result(x, y, w, h, image)
            if cached_result:
                self.cache_hit_count += 1
                return OptimizedOCRResult(
                    text=cached_result.get('text', ''),
                    confidence=cached_result.get('confidence', 0.0),
                    position=cached_result.get('position', (0, 0)),
                    processing_time_ms=0.1,
                    cache_hit=True
                )
        
        # 실제 OCR 수행
        result = self._perform_ocr_internal(image)
        
        # 캐시 저장
        if region and result.text:
            self.cache.cache_ocr_result(
                x, y, w, h,
                {
                    'text': result.text,
                    'confidence': result.confidence,
                    'position': result.position
                },
                image
            )
        
        # 성능 기록
        processing_time = (time.time() - start_time) * 1000
        result.processing_time_ms = processing_time
        
        if self.perf_monitor:
            self.perf_monitor.record_ocr_latency(processing_time)
        
        return result
    
    def _perform_ocr_internal(self, image: np.ndarray) -> OptimizedOCRResult:
        """실제 OCR 수행"""
        if not self.paddle_ocr:
            return OptimizedOCRResult()
        
        try:
            # 전처리
            processed = self.preprocess_image_optimized(image)
            
            # OCR 실행
            with suppress_stdout_stderr():
                result = self.paddle_ocr.ocr(processed, cls=True)
            
            if not result or not result[0]:
                return OptimizedOCRResult()
            
            # 텍스트 추출 및 보정
            all_text = []
            total_confidence = 0
            count = 0
            
            for line in result[0]:
                if line[1]:
                    text = line[1][0]
                    confidence = line[1][1]
                    
                    if confidence > 0.5:
                        # OCR 보정 적용
                        is_trigger, corrected = self.ocr_corrector.check_trigger_pattern(text)
                        if is_trigger:
                            text = corrected
                        
                        all_text.append(text)
                        total_confidence += confidence
                        count += 1
            
            if not all_text:
                return OptimizedOCRResult()
            
            combined_text = ' '.join(all_text)
            avg_confidence = total_confidence / count if count > 0 else 0
            
            return OptimizedOCRResult(
                text=combined_text,
                confidence=avg_confidence,
                position=(0, 0)
            )
            
        except Exception as e:
            self.logger.error(f"OCR 처리 오류: {e}")
            return OptimizedOCRResult()
    
    def perform_batch_ocr(self, images_with_regions: List[Tuple[np.ndarray, Tuple[int, int, int, int]]]) -> List[OptimizedOCRResult]:
        """배치 OCR 처리"""
        futures = []
        
        for image, region in images_with_regions:
            future = self.executor.submit(self.perform_ocr_cached, image, region)
            futures.append(future)
        
        results = []
        for future in futures:
            try:
                result = future.result(timeout=2.0)
                results.append(result)
            except Exception as e:
                self.logger.error(f"배치 OCR 오류: {e}")
                results.append(OptimizedOCRResult())
        
        return results
    
    def check_trigger_patterns(self, text: str) -> bool:
        """트리거 패턴 확인 (보정 포함)"""
        if not text:
            return False
        
        # OCR 보정기로 확인
        is_trigger, _ = self.ocr_corrector.check_trigger_pattern(text)
        
        if is_trigger and self.perf_monitor:
            self.perf_monitor.increment_detection_count()
        
        return is_trigger
    
    def get_statistics(self) -> Dict[str, Any]:
        """서비스 통계"""
        cache_stats = self.cache.get_stats() if self.cache else {}
        
        return {
            'total_ocr_count': self.total_ocr_count,
            'cache_hit_count': self.cache_hit_count,
            'cache_hit_rate': (self.cache_hit_count / self.total_ocr_count * 100) 
                            if self.total_ocr_count > 0 else 0,
            'cache_stats': cache_stats,
            'use_gpu': self.use_gpu,
            'worker_count': self.executor._max_workers
        }
    
    def optimize_settings(self, performance_data: Dict[str, float]):
        """성능 데이터 기반 설정 최적화"""
        # CPU 사용률이 높으면 워커 수 감소
        if performance_data.get('cpu_percent', 0) > 80:
            new_workers = max(2, self.executor._max_workers - 1)
            self.executor._max_workers = new_workers
            self.logger.info(f"OCR 워커 수 감소: {new_workers}")
        
        # 레이턴시가 높으면 전처리 간소화
        if performance_data.get('avg_ocr_latency', 0) > 100:
            # 간소화된 전처리 모드 활성화
            self.config._config['ocr_preprocess']['simple_mode'] = True
            self.logger.info("간소화된 전처리 모드 활성화")
    
    def cleanup(self):
        """리소스 정리"""
        self.executor.shutdown(wait=True)
        if self.cache:
            self.cache.save_cache_to_disk()
        self.logger.info("OCR 서비스 정리 완료")