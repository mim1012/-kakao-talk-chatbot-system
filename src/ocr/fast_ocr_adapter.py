"""
Fast OCR Adapter
고속 OCR 엔진을 기존 시스템과 통합하는 어댑터
"""

import numpy as np
import logging
from typing import List, Tuple, Optional
from src.ocr.base_ocr_service import BaseOCRService, OCRResult
from src.ocr.fast_ocr_engine import FastOCREngine, FastOCRResult
from src.ocr.enhanced_ocr_corrector import EnhancedOCRCorrector

class FastOCRAdapter(BaseOCRService):
    """고속 OCR 어댑터"""
    
    def __init__(self, config_manager=None):
        super().__init__(config_manager)
        self.logger = logging.getLogger(__name__)
        
        # 설정
        use_gpu = config_manager.get('use_gpu', False) if config_manager else False
        num_workers = config_manager.get('ocr_workers', 3) if config_manager else 3
        
        # 고속 OCR 엔진 초기화
        self.fast_engine = FastOCREngine(
            num_workers=num_workers,
            use_gpu=use_gpu
        )
        
        # OCR 교정기
        self.corrector = EnhancedOCRCorrector()
        
        self.logger.info(f"Fast OCR Adapter 초기화 완료 (워커: {num_workers}, GPU: {use_gpu})")
    
    def perform_ocr_with_recovery(self, image: np.ndarray, cell_id: str = "") -> OCRResult:
        """빠른 OCR 처리"""
        try:
            # 고속 OCR 처리
            fast_result = self.fast_engine.process_single(image)
            
            # 텍스트 교정
            corrected_text = self.corrector.correct(fast_result.text)
            
            # OCRResult로 변환
            result = OCRResult(
                text=corrected_text,
                confidence=fast_result.confidence,
                position=(0, 0),
                debug_info={
                    'processing_time': fast_result.processing_time,
                    'from_cache': fast_result.from_cache,
                    'original_text': fast_result.text
                }
            )
            
            return result
            
        except Exception as e:
            self.logger.error(f"Fast OCR 처리 오류 ({cell_id}): {e}")
            return OCRResult("", 0.0)
    
    def perform_batch_ocr(self, images: List[Tuple[np.ndarray, Optional[str]]]) -> List[OCRResult]:
        """배치 OCR 처리"""
        try:
            # 이미지만 추출
            img_list = [img for img, _ in images]
            
            # 병렬 배치 처리
            fast_results = self.fast_engine.process_batch(img_list)
            
            # OCRResult로 변환
            ocr_results = []
            for fast_result in fast_results:
                # 텍스트 교정
                corrected_text = self.corrector.correct(fast_result.text)
                
                result = OCRResult(
                    text=corrected_text,
                    confidence=fast_result.confidence,
                    position=(0, 0),
                    debug_info={
                        'processing_time': fast_result.processing_time,
                        'from_cache': fast_result.from_cache,
                        'original_text': fast_result.text
                    }
                )
                ocr_results.append(result)
            
            return ocr_results
            
        except Exception as e:
            self.logger.error(f"Batch OCR 처리 오류: {e}")
            return [OCRResult("", 0.0) for _ in images]
    
    def check_trigger_patterns(self, ocr_result: OCRResult) -> bool:
        """트리거 패턴 체크"""
        if not ocr_result or not ocr_result.text:
            return False
        
        # 설정에서 트리거 패턴 가져오기
        trigger_patterns = self.config_manager.get('trigger_patterns', ['들어왔습니다']) if self.config_manager else ['들어왔습니다']
        
        # 정규화된 텍스트로 체크
        normalized = ocr_result.normalized_text.lower()
        for pattern in trigger_patterns:
            if pattern.lower() in normalized:
                return True
        
        return False
    
    def is_available(self) -> bool:
        """서비스 사용 가능 여부"""
        return True
    
    def get_statistics(self) -> dict:
        """통계 정보"""
        return self.fast_engine.get_stats()
    
    def shutdown(self):
        """서비스 종료"""
        self.fast_engine.shutdown()