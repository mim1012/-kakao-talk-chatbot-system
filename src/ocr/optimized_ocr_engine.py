"""
최적화된 OCR 엔진 - 모든 개선사항 통합
"""
from __future__ import annotations

import time
import logging
import numpy as np
from typing import List, Optional, Dict, Any
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass

from ocr.adaptive_ocr_service import AdaptiveOCRService, OCRStrategy
from ocr.ocr_postprocessor import OCRPostProcessor, OCRCandidate
from utils.smart_cache import ImageCache
from core.config_manager import ConfigManager

@dataclass
class OptimizedOCRResult:
    """최적화된 OCR 결과"""
    text: str
    confidence: float
    position: tuple[int, int]
    processing_time: float
    strategy_used: str
    cache_hit: bool
    candidates_count: int
    debug_info: Dict[str, Any]

class OptimizedOCREngine:
    """통합 최적화 OCR 엔진"""
    
    def __init__(self, config_manager: ConfigManager):
        self.config = config_manager
        self.logger = logging.getLogger(__name__)
        
        # 핵심 컴포넌트들
        self.adaptive_service = AdaptiveOCRService(config_manager)
        self.postprocessor = OCRPostProcessor()
        self.cache = ImageCache(max_size=2000, ttl=600)  # 10분 TTL
        
        # 성능 통계
        self.stats = {
            'total_requests': 0,
            'cache_hits': 0,
            'successful_detections': 0,
            'failed_detections': 0,
            'avg_processing_time': 0.0,
            'strategy_performance': {}
        }
        
        # 멀티스레딩
        self.thread_pool = ThreadPoolExecutor(max_workers=3)
        
        self.logger.info("OptimizedOCREngine initialized")
    
    def process_image(self, image: np.ndarray, cell_id: str = "") -> OptimizedOCRResult:
        """이미지 OCR 처리 - 모든 최적화 기법 적용"""
        start_time = time.time()
        self.stats['total_requests'] += 1
        
        # 1단계: 캐시 확인
        cached_result = self.cache.get_ocr_result(image, cell_id)
        if cached_result:
            self.stats['cache_hits'] += 1
            self.logger.debug(f"Cache hit for {cell_id}")
            
            return OptimizedOCRResult(
                text=cached_result.text,
                confidence=cached_result.confidence,
                position=cached_result.position,
                processing_time=time.time() - start_time,
                strategy_used="cached",
                cache_hit=True,
                candidates_count=1,
                debug_info=cached_result.debug_info
            )
        
        # 2단계: 다중 전략 OCR 수행
        candidates = self._process_with_multiple_strategies(image, cell_id)
        
        # 3단계: 후처리 및 최적 결과 선택
        best_result = self.postprocessor.process_multiple_candidates(candidates)
        
        processing_time = time.time() - start_time
        
        if best_result:
            # 성공 결과
            self.stats['successful_detections'] += 1
            
            # 캐시에 저장
            self.cache.cache_ocr_result(image, best_result, cell_id)
            
            # 처리 시간 통계 업데이트
            self._update_processing_time_stats(processing_time)
            
            result = OptimizedOCRResult(
                text=best_result.text,
                confidence=best_result.confidence,
                position=best_result.position,
                processing_time=processing_time,
                strategy_used=best_result.source,
                cache_hit=False,
                candidates_count=len(candidates),
                debug_info={'candidates': len(candidates)}
            )
            
            self.logger.debug(f"OCR success for {cell_id}: '{best_result.text}' "
                            f"({processing_time:.3f}s, {len(candidates)} candidates)")
            
            return result
        else:
            # 실패 결과
            self.stats['failed_detections'] += 1
            
            return OptimizedOCRResult(
                text="",
                confidence=0.0,
                position=(0, 0),
                processing_time=processing_time,
                strategy_used="none",
                cache_hit=False,
                candidates_count=len(candidates),
                debug_info={'reason': 'no_valid_candidates'}
            )
    
    def _process_with_multiple_strategies(self, image: np.ndarray, cell_id: str) -> List[OCRCandidate]:
        """다중 전략으로 OCR 처리"""
        candidates = []
        
        # 최적 전략으로 먼저 시도
        best_strategy = self.adaptive_service.get_best_strategy()
        result = self._try_strategy(image, best_strategy, cell_id)
        if result:
            candidates.append(result)
        
        # 신뢰도가 낮으면 다른 전략들도 시도
        if not candidates or candidates[0].confidence < 0.8:
            # 상위 2개 다른 전략 시도
            other_strategies = [s for s in self.adaptive_service.strategies 
                             if s.name != best_strategy.name][:2]
            
            futures = []
            for strategy in other_strategies:
                future = self.thread_pool.submit(self._try_strategy, image, strategy, cell_id)
                futures.append(future)
            
            for future in futures:
                try:
                    result = future.result(timeout=2.0)  # 2초 타임아웃
                    if result:
                        candidates.append(result)
                except Exception as e:
                    self.logger.debug(f"Strategy execution failed: {e}")
        
        return candidates
    
    def _try_strategy(self, image: np.ndarray, strategy: OCRStrategy, cell_id: str) -> Optional[OCRCandidate]:
        """특정 전략으로 OCR 시도"""
        try:
            # 전처리된 이미지 캐시 확인
            processed_image = self.cache.get_preprocessed_image(image, strategy.name)
            if processed_image is None:
                processed_image = self.adaptive_service.preprocess_image_adaptive(image, strategy)
                self.cache.cache_preprocessed_image(image, processed_image, strategy.name)
            
            # OCR 수행
            results = self.adaptive_service.paddle_ocr.ocr(processed_image, cls=True)
            
            if results and results[0]:
                for detection in results[0]:
                    if detection[1]:
                        text = detection[1][0]
                        confidence = detection[1][1]
                        position = (int(detection[0][0][0]), int(detection[0][0][1]))
                        
                        # 후처리로 텍스트 향상
                        enhanced_text, enhanced_confidence = self.postprocessor.enhance_single_result(text, confidence)
                        
                        if enhanced_text:  # 유효한 결과만 반환
                            return OCRCandidate(
                                text=enhanced_text,
                                confidence=enhanced_confidence,
                                source=strategy.name,
                                position=position
                            )
            
            return None
            
        except Exception as e:
            self.logger.debug(f"Strategy {strategy.name} failed: {e}")
            return None
    
    def _update_processing_time_stats(self, processing_time: float):
        """처리 시간 통계 업데이트"""
        if self.stats['avg_processing_time'] == 0:
            self.stats['avg_processing_time'] = processing_time
        else:
            # 지수 이동 평균
            self.stats['avg_processing_time'] = (
                self.stats['avg_processing_time'] * 0.9 + processing_time * 0.1
            )
    
    def optimize_performance(self):
        """성능 최적화 실행"""
        # 캐시 최적화
        self.cache.optimize()
        
        # 전략 재평가
        self.adaptive_service._evaluate_strategies()
        
        self.logger.debug("Performance optimization completed")
    
    def get_comprehensive_stats(self) -> Dict[str, Any]:
        """종합 성능 통계"""
        cache_stats = self.cache.get_stats()
        adaptive_stats = self.adaptive_service.get_performance_report()
        postprocessor_stats = self.postprocessor.get_correction_stats()
        
        success_rate = (
            self.stats['successful_detections'] / self.stats['total_requests'] * 100
            if self.stats['total_requests'] > 0 else 0
        )
        
        cache_hit_rate = (
            self.stats['cache_hits'] / self.stats['total_requests'] * 100
            if self.stats['total_requests'] > 0 else 0
        )
        
        return {
            'engine_stats': {
                'total_requests': self.stats['total_requests'],
                'success_rate': f"{success_rate:.1f}%",
                'avg_processing_time': f"{self.stats['avg_processing_time']:.3f}s",
                'cache_hit_rate': f"{cache_hit_rate:.1f}%"
            },
            'cache_stats': cache_stats,
            'adaptive_stats': adaptive_stats,
            'postprocessor_stats': postprocessor_stats
        }
    
    def cleanup(self):
        """리소스 정리"""
        self.thread_pool.shutdown(wait=True)
        self.logger.info("OptimizedOCREngine cleanup completed")