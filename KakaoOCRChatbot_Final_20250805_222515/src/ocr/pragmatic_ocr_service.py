"""
실용적 OCR 서비스 - 트레이드오프를 고려한 현실적 최적화
복잡성을 최소화하면서 핵심 개선사항만 적용
"""
from __future__ import annotations

import cv2
import time
import logging
import numpy as np
from typing import Optional, Dict, Any, List
from dataclasses import dataclass

from ocr.enhanced_ocr_service import EnhancedOCRService, OCRResult
from core.config_manager import ConfigManager

@dataclass
class SimpleStrategy:
    """단순화된 전처리 전략"""
    name: str
    scale: float
    threshold_block: int
    threshold_c: int
    success_count: int = 0
    total_count: int = 0
    
    @property
    def success_rate(self) -> float:
        return self.success_count / self.total_count if self.total_count > 0 else 0.0

class PragmaticOCRService(EnhancedOCRService):
    """실용적 OCR 서비스 - 최소한의 복잡성으로 최대 효과"""
    
    def __init__(self, config_manager: ConfigManager):
        super().__init__(config_manager)
        
        # 3가지 핵심 전략만 사용 (복잡성 최소화)
        self.strategies = [
            SimpleStrategy("표준", 4.0, 11, 2),     # 기본 고품질
            SimpleStrategy("빠름", 2.0, 9, 1),      # 속도 우선
            SimpleStrategy("정확", 6.0, 15, 3),     # 정확도 우선
        ]
        
        self.current_strategy_idx = 0
        self.adaptation_counter = 0
        self.adaptation_threshold = 20  # 20번마다 전략 재평가
        
        # 간단한 결과 캐시 (메모리 사용량 제한)
        self.simple_cache = {}
        self.cache_max_size = 50  # 최대 50개만 캐시
        self.cache_hits = 0
        self.cache_requests = 0
        
        # 한글 OCR 핵심 오류만 교정
        self.core_corrections = {
            '든어왔습니다': '들어왔습니다',
            '들머왔습니다': '들어왔습니다', 
            '들어완습니다': '들어왔습니다',
            '툴어왔습니다': '들어왔습니다',
            '들어왔습니디': '들어왔습니다',
        }
        
        self.logger.info("PragmaticOCRService initialized (lightweight mode)")
    
    def perform_ocr_pragmatic(self, image: np.ndarray, cell_id: str = "") -> OCRResult:
        """실용적 OCR 수행 - 트레이드오프 고려"""
        start_time = time.time()
        self.cache_requests += 1
        
        # 1단계: 간단한 캐시 확인 (이미지 해시 기반)
        import hashlib
        image_hash = hashlib.md5(image.tobytes()).hexdigest()[:16]  # 16자리만 사용
        
        if image_hash in self.simple_cache:
            self.cache_hits += 1
            cached_result = self.simple_cache[image_hash]
            # 캐시된 결과 복사하여 반환
            return OCRResult(
                cached_result.text,
                cached_result.confidence,
                cached_result.position,
                {'cache_hit': True, 'processing_time': time.time() - start_time}
            )
        
        # 2단계: 현재 최적 전략으로 OCR 수행
        current_strategy = self.strategies[self.current_strategy_idx]
        result = self._try_single_strategy(image, current_strategy, cell_id)
        
        # 3단계: 실패 시에만 다른 전략 시도 (오버헤드 최소화)
        if not result or result.confidence < 0.6:
            # 다음 전략 1개만 시도
            next_idx = (self.current_strategy_idx + 1) % len(self.strategies)
            next_strategy = self.strategies[next_idx]
            backup_result = self._try_single_strategy(image, next_strategy, cell_id)
            
            # 더 좋은 결과가 있으면 사용
            if backup_result and backup_result.confidence > (result.confidence if result else 0):
                result = backup_result
                current_strategy = next_strategy
        
        # 4단계: 결과 처리 및 학습
        processing_time = time.time() - start_time
        
        if result and result.confidence > 0.3:
            # 성공 기록
            current_strategy.total_count += 1
            if result.confidence > 0.7:
                current_strategy.success_count += 1
            
            # 간단한 텍스트 교정
            corrected_text = self._apply_simple_corrections(result.text)
            
            # 캐시에 저장 (크기 제한)
            if len(self.simple_cache) >= self.cache_max_size:
                # 가장 오래된 항목 제거 (FIFO)
                oldest_key = next(iter(self.simple_cache))
                del self.simple_cache[oldest_key]
            
            final_result = OCRResult(
                corrected_text,
                result.confidence,
                result.position,
                {
                    'strategy': current_strategy.name,
                    'processing_time': processing_time,
                    'cache_hit': False
                }
            )
            
            self.simple_cache[image_hash] = final_result
            
            # 주기적으로 전략 재평가
            self.adaptation_counter += 1
            if self.adaptation_counter >= self.adaptation_threshold:
                self._simple_adaptation()
                self.adaptation_counter = 0
            
            return final_result
        
        else:
            # 실패 기록
            current_strategy.total_count += 1
            return OCRResult(debug_info={'processing_time': processing_time})
    
    def _try_single_strategy(self, image: np.ndarray, strategy: SimpleStrategy, cell_id: str) -> Optional[OCRResult]:
        """단일 전략으로 OCR 시도"""
        try:
            # 간단한 전처리 (복잡성 최소화)
            processed = self._simple_preprocess(image, strategy)
            
            # OCR 수행
            results = self.paddle_ocr.ocr(processed, cls=True)
            
            if results and results[0]:
                for detection in results[0]:
                    if detection[1]:
                        text = detection[1][0]
                        confidence = detection[1][1]
                        position = (int(detection[0][0][0]), int(detection[0][0][1]))
                        
                        return OCRResult(text, confidence, position)
            
            return None
            
        except Exception as e:
            self.logger.debug(f"Strategy {strategy.name} failed: {e}")
            return None
    
    def _simple_preprocess(self, image: np.ndarray, strategy: SimpleStrategy) -> np.ndarray:
        """단순화된 전처리"""
        try:
            # 그레이스케일
            if len(image.shape) == 3:
                gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            else:
                gray = image.copy()
            
            # 크기 조정
            if strategy.scale != 1.0:
                height, width = gray.shape
                new_width = int(width * strategy.scale)
                new_height = int(height * strategy.scale)
                gray = cv2.resize(gray, (new_width, new_height), interpolation=cv2.INTER_CUBIC)
            
            # 적응형 임계값만 적용 (핵심 전처리)
            binary = cv2.adaptiveThreshold(
                gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                cv2.THRESH_BINARY, strategy.threshold_block, strategy.threshold_c
            )
            
            # 간단한 노이즈 제거
            kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2))
            binary = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)
            
            return binary
            
        except Exception:
            return image
    
    def _apply_simple_corrections(self, text: str) -> str:
        """핵심 오류만 교정"""
        corrected = text
        for wrong, correct in self.core_corrections.items():
            corrected = corrected.replace(wrong, correct)
        return corrected
    
    def _simple_adaptation(self):
        """간단한 전략 적응"""
        # 성공률이 가장 높은 전략으로 변경
        best_strategy_idx = 0
        best_rate = 0
        
        for i, strategy in enumerate(self.strategies):
            if strategy.total_count >= 5 and strategy.success_rate > best_rate:
                best_rate = strategy.success_rate
                best_strategy_idx = i
        
        if best_strategy_idx != self.current_strategy_idx:
            old_strategy = self.strategies[self.current_strategy_idx].name
            new_strategy = self.strategies[best_strategy_idx].name
            self.current_strategy_idx = best_strategy_idx
            self.logger.info(f"Strategy adapted: {old_strategy} -> {new_strategy} "
                           f"(success rate: {best_rate:.1%})")
    
    def get_simple_stats(self) -> Dict[str, Any]:
        """간단한 성능 통계"""
        cache_hit_rate = (self.cache_hits / self.cache_requests * 100 
                         if self.cache_requests > 0 else 0)
        
        return {
            'cache_hit_rate': f"{cache_hit_rate:.1f}%",
            'cache_size': len(self.simple_cache),
            'current_strategy': self.strategies[self.current_strategy_idx].name,
            'strategies': [
                {
                    'name': s.name,
                    'success_rate': f"{s.success_rate:.1%}",
                    'total_attempts': s.total_count
                } for s in self.strategies
            ]
        }
    
    def cleanup_cache(self):
        """캐시 정리 (메모리 관리)"""
        if len(self.simple_cache) > self.cache_max_size * 0.8:
            # 절반만 유지
            items = list(self.simple_cache.items())
            self.simple_cache = dict(items[len(items)//2:])
            self.logger.debug("Cache cleaned up")