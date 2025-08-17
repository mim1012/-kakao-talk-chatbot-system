"""
Fast OCR Adapter
고속 OCR 엔진을 기존 시스템과 통합하는 어댑터
"""

import numpy as np
import logging
from typing import List, Tuple, Optional
from ocr.base_ocr_service import BaseOCRService, OCRResult
from ocr.fast_ocr_engine import FastOCREngine, FastOCRResult
from ocr.enhanced_ocr_corrector import EnhancedOCRCorrector

class FastOCRAdapter(BaseOCRService):
    """고속 OCR 어댑터"""
    
    def __init__(self, config_manager=None):
        super().__init__(config_manager)
        self.logger = logging.getLogger(__name__)
        
        # 설정
        self.use_gpu = config_manager.get('use_gpu', False) if config_manager else False
        self.num_workers = config_manager.get('ocr_workers', 3) if config_manager else 3
        
        # 고속 OCR 엔진 초기화
        self.fast_engine = None
        self._initialize_ocr_engine()
        
        # OCR 교정기
        self.corrector = EnhancedOCRCorrector()
        
        self.logger.info(f"Fast OCR Adapter 초기화 완료 (워커: {self.num_workers}, GPU: {self.use_gpu})")
    
    def _initialize_ocr_engine(self) -> bool:
        """OCR 엔진 초기화"""
        try:
            self.fast_engine = FastOCREngine(
                num_workers=self.num_workers,
                use_gpu=self.use_gpu
            )
            return True
        except Exception as e:
            self.logger.error(f"Fast OCR 엔진 초기화 실패: {e}")
            return False
    
    def _perform_ocr_internal(self, image: np.ndarray) -> List[Tuple[str, float, Tuple[int, int]]]:
        """내부 OCR 처리"""
        try:
            if not self.fast_engine:
                return []
            
            # 고속 OCR 처리
            fast_result = self.fast_engine.process_single(image)
            
            # 결과를 BaseOCRService 형식으로 변환
            return [(fast_result.text, fast_result.confidence, (0, 0))]
            
        except Exception as e:
            self.logger.error(f"OCR 내부 처리 오류: {e}")
            return []
    
    def perform_ocr_with_recovery(self, image: np.ndarray, cell_id: str = "") -> OCRResult:
        """빠른 OCR 처리"""
        try:
            # 이미지 유효성 검사
            if image is None or image.size == 0:
                self.logger.warning(f"잘못된 이미지 ({cell_id}): None 또는 빈 이미지")
                return OCRResult("", 0.0, debug_info={'error': 'invalid_image'})
            
            # 고속 OCR 처리
            self.logger.debug(f"OCR 처리 시작 ({cell_id}): 이미지 크기 {image.shape}")
            fast_result = self.fast_engine.process_single(image)
            
            # 안전한 속성 접근
            text = getattr(fast_result, 'text', '') if fast_result else ''
            confidence = getattr(fast_result, 'confidence', 0.0) if fast_result else 0.0
            processing_time = getattr(fast_result, 'processing_time', 0.0) if fast_result else 0.0
            from_cache = getattr(fast_result, 'from_cache', False) if fast_result else False
            
            # 원본 텍스트 로깅
            if text:
                self.logger.info(f"원본 OCR 결과 ({cell_id}): '{text}' (신뢰도: {confidence:.2f})")
            else:
                self.logger.debug(f"OCR 텍스트 없음 ({cell_id})")
            
            # 텍스트 교정
            corrected_text = self.corrector.correct_text(text) if text else ""
            if corrected_text != text:
                self.logger.info(f"텍스트 교정 ({cell_id}): '{text}' -> '{corrected_text}'")
            
            # OCRResult로 변환
            result = OCRResult(
                text=corrected_text,
                confidence=confidence,
                position=(0, 0),
                debug_info={
                    'processing_time': processing_time,
                    'from_cache': from_cache,
                    'original_text': text,
                    'cell_id': cell_id,
                    'image_shape': image.shape
                }
            )
            
            return result
            
        except Exception as e:
            self.logger.error(f"Fast OCR 처리 오류 ({cell_id}): {e}")
            import traceback
            self.logger.error(f"오류 상세: {traceback.format_exc()}")
            return OCRResult("", 0.0, debug_info={'error': str(e), 'cell_id': cell_id})
    
    def perform_batch_ocr(self, images: List[Tuple[np.ndarray, Optional[str]]]) -> List[OCRResult]:
        """배치 OCR 처리"""
        try:
            if not images:
                return []
            
            # 이미지만 안전하게 추출
            img_list = []
            for item in images:
                try:
                    if isinstance(item, tuple) and len(item) >= 1:
                        img_list.append(item[0])
                    elif isinstance(item, np.ndarray):
                        img_list.append(item)
                    else:
                        self.logger.warning(f"잘못된 이미지 형식: {type(item)}")
                        img_list.append(np.zeros((10, 10, 3), dtype=np.uint8))  # 더미 이미지
                except Exception as extract_error:
                    self.logger.error(f"이미지 추출 오류: {extract_error}")
                    img_list.append(np.zeros((10, 10, 3), dtype=np.uint8))  # 더미 이미지
            
            if not img_list:
                return [OCRResult("", 0.0) for _ in images]
            
            # 병렬 배치 처리
            fast_results = self.fast_engine.process_batch(img_list)
            
            # 결과 개수 검증
            if len(fast_results) != len(images):
                self.logger.warning(f"결과 개수 불일치: 입력 {len(images)}, 출력 {len(fast_results)}")
                # 부족한 결과를 빈 결과로 채움
                while len(fast_results) < len(images):
                    fast_results.append(None)
            
            # OCRResult로 변환
            ocr_results = []
            for i, fast_result in enumerate(fast_results):
                try:
                    # 안전한 속성 접근
                    if fast_result is not None:
                        text = getattr(fast_result, 'text', '') if fast_result else ''
                        confidence = getattr(fast_result, 'confidence', 0.0) if fast_result else 0.0
                        processing_time = getattr(fast_result, 'processing_time', 0.0) if fast_result else 0.0
                        from_cache = getattr(fast_result, 'from_cache', False) if fast_result else False
                        
                        # 텍스트 교정
                        corrected_text = self.corrector.correct_text(text) if text else ""
                    else:
                        text = ""
                        corrected_text = ""
                        confidence = 0.0
                        processing_time = 0.0
                        from_cache = False
                    
                    result = OCRResult(
                        text=corrected_text,
                        confidence=confidence,
                        position=(0, 0),
                        debug_info={
                            'processing_time': processing_time,
                            'from_cache': from_cache,
                            'original_text': text,
                            'batch_index': i
                        }
                    )
                    ocr_results.append(result)
                    
                except Exception as inner_e:
                    self.logger.error(f"결과 변환 오류 (인덱스 {i}): {inner_e}")
                    # 빈 결과 추가
                    ocr_results.append(OCRResult("", 0.0, debug_info={'error': str(inner_e), 'batch_index': i}))
            
            return ocr_results
            
        except Exception as e:
            self.logger.error(f"Batch OCR 처리 오류: {e}")
            import traceback
            self.logger.error(f"오류 상세: {traceback.format_exc()}")
            return [OCRResult("", 0.0, debug_info={'error': str(e)}) for _ in images]
    
    def check_trigger_patterns(self, ocr_result: OCRResult) -> bool:
        """트리거 패턴 체크"""
        if not ocr_result or not ocr_result.text:
            return False
        
        # 설정에서 트리거 패턴 가져오기
        if hasattr(self, 'config_manager') and self.config_manager:
            trigger_patterns = self.config_manager.get('trigger_patterns', ['들어왔습니다'])
        else:
            trigger_patterns = ['들어왔습니다']
        
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