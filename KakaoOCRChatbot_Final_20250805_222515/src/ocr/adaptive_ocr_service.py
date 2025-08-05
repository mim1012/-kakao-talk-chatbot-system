"""
적응형 OCR 서비스 - 실시간 성능 조정
"""
from __future__ import annotations

import cv2
import numpy as np
import time
import logging
from typing import List, Dict, Tuple
from dataclasses import dataclass
from ocr.enhanced_ocr_service import EnhancedOCRService, OCRResult
from core.config_manager import ConfigManager

@dataclass
class OCRStrategy:
    """OCR 전처리 전략"""
    name: str
    scale: float
    threshold_block: int
    threshold_c: int
    use_sharpen: bool
    use_morph: bool
    use_invert: bool
    success_rate: float = 0.0
    usage_count: int = 0

class AdaptiveOCRService(EnhancedOCRService):
    """성능 기반 적응형 OCR 서비스"""
    
    def __init__(self, config_manager: ConfigManager):
        super().__init__(config_manager)
        
        # 다양한 전처리 전략들
        self.strategies = [
            OCRStrategy("기본", 4.0, 11, 2, True, True, True),
            OCRStrategy("고해상도", 6.0, 15, 4, True, False, True),
            OCRStrategy("저노이즈", 3.0, 9, 1, False, True, False),
            OCRStrategy("고대비", 4.0, 13, 3, True, True, True),
            OCRStrategy("간단", 2.0, 11, 2, False, False, False)
        ]
        
        self.current_strategy_idx = 0
        self.strategy_performance = {}
        self.adaptation_interval = 50  # 50번마다 전략 재평가
        self.ocr_attempts = 0
        
    def get_best_strategy(self) -> OCRStrategy:
        """현재 최고 성능 전략 반환"""
        if not self.strategy_performance:
            return self.strategies[0]
        
        best_strategy = max(self.strategies, 
                          key=lambda s: s.success_rate if s.usage_count > 5 else 0)
        return best_strategy
    
    def preprocess_image_adaptive(self, image: np.ndarray, strategy: OCRStrategy) -> np.ndarray:
        """적응형 이미지 전처리"""
        try:
            # 그레이스케일 변환
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
            
            # 샤프닝
            if strategy.use_sharpen:
                kernel = np.array([[-1,-1,-1], [-1,9,-1], [-1,-1,-1]])
                gray = cv2.filter2D(gray, -1, kernel)
            
            # 적응형 임계값
            binary = cv2.adaptiveThreshold(
                gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                cv2.THRESH_BINARY, strategy.threshold_block, strategy.threshold_c
            )
            
            # 모폴로지 연산
            if strategy.use_morph:
                kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2))
                binary = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)
            
            # 반전
            if strategy.use_invert:
                binary = cv2.bitwise_not(binary)
            
            return binary
            
        except Exception as e:
            self.logger.error(f"Adaptive preprocessing failed: {e}")
            return image
    
    def perform_ocr_with_adaptation(self, image: np.ndarray, cell_id: str = "") -> OCRResult:
        """적응형 OCR 수행"""
        self.ocr_attempts += 1
        
        # 주기적으로 전략 재평가
        if self.ocr_attempts % self.adaptation_interval == 0:
            self._evaluate_strategies()
        
        # 현재 최적 전략 선택
        strategy = self.get_best_strategy()
        
        # 전처리
        processed_image = self.preprocess_image_adaptive(image, strategy)
        
        # OCR 수행
        start_time = time.time()
        try:
            results = self.paddle_ocr.ocr(processed_image, cls=True)
            processing_time = time.time() - start_time
            
            if results and results[0]:
                for detection in results[0]:
                    if detection[1]:
                        text = detection[1][0]
                        confidence = detection[1][1]
                        
                        # 성공률 업데이트
                        self._update_strategy_performance(strategy, True, confidence, processing_time)
                        
                        position = (int(detection[0][0][0]), int(detection[0][0][1]))
                        return OCRResult(text, confidence, position, {
                            'strategy': strategy.name,
                            'processing_time': processing_time
                        })
            
            # 결과 없음
            self._update_strategy_performance(strategy, False, 0, processing_time)
            return OCRResult(debug_info={'strategy': strategy.name})
            
        except Exception as e:
            self._update_strategy_performance(strategy, False, 0, time.time() - start_time)
            return OCRResult(debug_info={'error': str(e), 'strategy': strategy.name})
    
    def _update_strategy_performance(self, strategy: OCRStrategy, success: bool, 
                                   confidence: float, processing_time: float):
        """전략 성능 통계 업데이트"""
        strategy.usage_count += 1
        
        if success and confidence > 0.5:
            # 신뢰도와 속도를 종합한 점수
            score = confidence * (1.0 / max(processing_time, 0.01))
            strategy.success_rate = (strategy.success_rate * (strategy.usage_count - 1) + score) / strategy.usage_count
        else:
            # 실패 시 점수 감소
            strategy.success_rate = (strategy.success_rate * (strategy.usage_count - 1)) / strategy.usage_count
    
    def _evaluate_strategies(self):
        """전략 성능 평가 및 순위 조정"""
        sorted_strategies = sorted(self.strategies, 
                                 key=lambda s: s.success_rate if s.usage_count > 5 else 0, 
                                 reverse=True)
        
        self.logger.info("전략 성능 평가:")
        for i, strategy in enumerate(sorted_strategies[:3]):
            self.logger.info(f"  {i+1}. {strategy.name}: 성공률 {strategy.success_rate:.3f} "
                           f"(사용 {strategy.usage_count}회)")
    
    def get_performance_report(self) -> Dict:
        """성능 리포트 생성"""
        return {
            'total_attempts': self.ocr_attempts,
            'strategies': [
                {
                    'name': s.name,
                    'success_rate': s.success_rate,
                    'usage_count': s.usage_count
                } for s in sorted(self.strategies, key=lambda x: x.success_rate, reverse=True)
            ],
            'best_strategy': self.get_best_strategy().name
        }