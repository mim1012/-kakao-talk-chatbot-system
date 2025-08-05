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
        """PaddleOCR 초기화 (완전 로깅 차단)"""
        try:
            # 로깅 완전 차단
            import logging
            import os
            
            # 환경변수 설정
            os.environ['PPOCR_LOG_LEVEL'] = 'CRITICAL'
            os.environ['PADDLE_LOG_LEVEL'] = 'CRITICAL'
            os.environ['FLAGS_logtostderr'] = '0'
            os.environ['GLOG_minloglevel'] = '3'
            os.environ['GLOG_v'] = '0'
            
            # 로깅 비활성화
            for name in ['ppocr', 'paddleocr', 'paddle', 'paddlex']:
                logger = logging.getLogger(name)
                logger.setLevel(logging.CRITICAL)
                logger.disabled = True
                logger.propagate = False
            
            with suppress_stdout_stderr():
                # 최소한의 설정으로 초기화
                self.paddle_ocr = PaddleOCR(
                    lang='korean',
                    use_angle_cls=False,
                    show_log=False,
                    det_db_thresh=0.3,
                    det_db_box_thresh=0.5,
                    rec_batch_num=1  # 배치 크기 최소화
                )
            
            self.logger.info(f"PaddleOCR 초기화 완료")
            
        except Exception as e:
            self.logger.error(f"PaddleOCR 초기화 실패: {e}")
            self.paddle_ocr = None
    
    def preprocess_image_optimized(self, image: np.ndarray) -> np.ndarray:
        """최적화된 이미지 전처리 (간소화 모드 지원)"""
        start_time = time.time()
        
        # 캐시 확인
        cached = self.cache.get_preprocessed_image(image)
        if cached is not None:
            return cached
        
        try:
            # 간소화 모드 확인 (레이턴시 1초 이상이면 강제 활성화)
            simple_mode = self.config._config.get('ocr_preprocess', {}).get('simple_mode', False)
            
            # 최대 간소화 모드 (가장 빠른 처리)
            if simple_mode:
                # 그레이스케일 변환만
                if len(image.shape) == 3:
                    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
                else:
                    gray = image
                
                # 단순 크기 조정 (2배만)
                height, width = gray.shape[:2]
                if min(width, height) < 100:
                    gray = cv2.resize(gray, (width*2, height*2), interpolation=cv2.INTER_LINEAR)
                
                # 간단한 임계값 처리만
                _, processed = cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY)
                
            else:
                # 일반 모드 (기존 처리)
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
                
                # 대비 향상만 (노이즈 제거 생략)
                clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
                enhanced = clahe.apply(gray)
                
                # 이진화
                _, processed = cv2.threshold(enhanced, 0, 255, 
                                           cv2.THRESH_BINARY | cv2.THRESH_OTSU)
            
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
        """실제 OCR 수행 (안전성 강화)"""
        if not self.paddle_ocr:
            return OptimizedOCRResult()
        
        try:
            # 이미지 유효성 검사
            if image is None or image.size == 0:
                return OptimizedOCRResult()
            
            # 최소 크기 확인
            if len(image.shape) < 2 or min(image.shape[:2]) < 10:
                return OptimizedOCRResult()
            
            # 전처리
            processed = self.preprocess_image_optimized(image)
            
            # 전처리된 이미지 검증
            if processed is None or processed.size == 0:
                return OptimizedOCRResult()
            
            # OCR 실행 (메모리 안정성 강화)
            with suppress_stdout_stderr():
                # 이미지 데이터 타입 및 메모리 레이아웃 보장
                if processed.dtype != np.uint8:
                    processed = processed.astype(np.uint8)
                
                # 연속 메모리 배열로 변환
                if not processed.flags['C_CONTIGUOUS']:
                    processed = np.ascontiguousarray(processed)
                
                # 3채널로 변환 (PaddleOCR 요구사항)
                if len(processed.shape) == 2:
                    processed = cv2.cvtColor(processed, cv2.COLOR_GRAY2BGR)
                elif len(processed.shape) == 3 and processed.shape[2] == 4:
                    processed = cv2.cvtColor(processed, cv2.COLOR_BGRA2BGR)
                
                # 이미지 크기 검증 (최소 크기 보장)
                h, w = processed.shape[:2]
                if h < 16 or w < 16:
                    # 너무 작은 이미지는 리사이즈
                    processed = cv2.resize(processed, (max(32, w*2), max(32, h*2)))
                
                # 메모리 복사본 생성 (원본 데이터 보호)
                processed_copy = processed.copy()
                
                result = self.paddle_ocr.ocr(processed_copy)
            
            # 결과 유효성 검사
            if not result or len(result) == 0 or not result[0]:
                return OptimizedOCRResult()
            
            # 텍스트 추출 및 보정
            all_text = []
            total_confidence = 0
            count = 0
            
            for line in result[0]:
                if line and len(line) >= 2 and line[1]:
                    text = line[1][0] if line[1][0] else ""
                    confidence = float(line[1][1]) if line[1][1] else 0.0
                    
                    if confidence > 0.3 and text.strip():  # 낮은 임계값
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
        """배치 OCR 처리 (안전성 강화)"""
        if not images_with_regions:
            return []
        
        futures = []
        valid_items = []
        
        # 유효한 이미지만 필터링
        for image, region in images_with_regions:
            try:
                if image is not None and image.size > 0 and len(image.shape) >= 2:
                    if min(image.shape[:2]) >= 10:  # 최소 크기 확인
                        valid_items.append((image, region))
            except Exception as e:
                self.logger.debug(f"이미지 유효성 검사 실패: {e}")
        
        if not valid_items:
            return [OptimizedOCRResult() for _ in images_with_regions]
        
        # 이미지 크기 기준으로 정렬 (작은 이미지 먼저 처리)
        try:
            sorted_items = sorted(valid_items, 
                                key=lambda x: x[0].shape[0] * x[0].shape[1])
        except Exception:
            sorted_items = valid_items
        
        # 스레드 풀에 작업 제출
        for image, region in sorted_items:
            try:
                future = self.executor.submit(self.perform_ocr_cached, image, region)
                futures.append((future, region))
            except Exception as e:
                self.logger.error(f"OCR 작업 제출 실패: {e}")
                futures.append((None, region))
        
        # 결과 수집
        results = []
        completed_count = 0
        timeout_per_item = 2.0  # 타임아웃 단축 (2초)
        
        for future, region in futures:
            if future is None:
                results.append(OptimizedOCRResult())
                continue
                
            try:
                result = future.result(timeout=timeout_per_item)
                results.append(result if result else OptimizedOCRResult())
                completed_count += 1
            except Exception as e:
                self.logger.debug(f"배치 OCR 실패 (region: {region}): {e}")
                results.append(OptimizedOCRResult())
        
        # 원래 크기에 맞춰 결과 패딩
        while len(results) < len(images_with_regions):
            results.append(OptimizedOCRResult())
        
        if completed_count > 0:
            avg_time = sum(r.processing_time_ms for r in results if r.processing_time_ms > 0) / completed_count
            if avg_time > 500:  # 500ms 이상일 때만 로깅
                self.logger.info(f"배치 OCR 평균 시간: {avg_time:.1f}ms")
        
        return results[:len(images_with_regions)]  # 정확한 크기로 반환
    
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
        """성능 데이터 기반 설정 최적화 (워커 수 유지)"""
        # 워커 수는 유지하고 다른 최적화 적용
        current_workers = self.executor._max_workers
        self.logger.info(f"현재 OCR 워커 수 유지: {current_workers}")
        
        # 레이턴시가 높으면 전처리 최적화
        avg_latency = performance_data.get('avg_ocr_latency', 0)
        if avg_latency > 100:
            # 간소화된 전처리 모드 활성화
            self.config._config['ocr_preprocess']['simple_mode'] = True
            self.config._config['ocr_preprocess']['scale'] = 2.0  # 스케일 감소
            self.config._config['ocr_preprocess']['gaussian_blur'] = False  # 블러 비활성화
            self.config._config['ocr_preprocess']['apply_sharpen'] = False  # 샤프닝 비활성화
            self.logger.info(f"OCR 전처리 최적화 적용 (레이턴시: {avg_latency:.1f}ms)")
        elif avg_latency < 50:
            # 레이턴시가 낮으면 품질 향상
            self.config._config['ocr_preprocess']['scale'] = 3.0
            self.config._config['ocr_preprocess']['gaussian_blur'] = True
            self.config._config['ocr_preprocess']['apply_sharpen'] = True
            self.logger.info(f"OCR 품질 향상 모드 (레이턴시: {avg_latency:.1f}ms)")
        
        # 캐시 히트율이 낮으면 캐시 크기 증가
        cache_hit_rate = (self.cache_hit_count / self.total_ocr_count * 100) if self.total_ocr_count > 0 else 0
        if cache_hit_rate < 30 and self.cache:
            self.cache.increase_cache_size()
            self.logger.info(f"캐시 크기 증가 (히트율: {cache_hit_rate:.1f}%)")
    
    def cleanup(self):
        """리소스 정리"""
        self.executor.shutdown(wait=True)
        if self.cache:
            self.cache.save_cache_to_disk()
        self.logger.info("OCR 서비스 정리 완료")