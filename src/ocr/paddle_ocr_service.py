"""
PaddleOCR 구현 서비스
베이스 OCR 서비스를 상속받아 PaddleOCR 엔진을 구현합니다.
"""
from __future__ import annotations

import logging
import numpy as np
import threading
import time
from typing import List, Tuple
from concurrent.futures import ThreadPoolExecutor

from ocr.base_ocr_service import BaseOCRService
from core.config_manager import ConfigManager
from utils.suppress_output import suppress_stdout_stderr

# PaddleOCR 임포트
try:
    from paddleocr import PaddleOCR
    from ocr.safe_paddleocr import create_safe_paddleocr
    PADDLEOCR_AVAILABLE = True
except ImportError:
    PADDLEOCR_AVAILABLE = False
    logging.warning("PaddleOCR를 사용할 수 없습니다.")


class PaddleOCRService(BaseOCRService):
    """PaddleOCR 기반 OCR 서비스"""
    
    # 클래스 레벨 공유 자원
    _ocr_lock = threading.Lock()
    _shared_paddle_ocr = None
    _last_init_time = 0
    
    def __init__(self, config_manager: ConfigManager):
        super().__init__(config_manager)
        
        self.paddle_ocr = None
        self.executor = None
        self.max_workers = config_manager.get('max_concurrent_ocr', 4)
        
        # PaddleOCR 초기화
        if PADDLEOCR_AVAILABLE:
            self._initialize_ocr_engine()
        else:
            self.logger.error("PaddleOCR가 설치되지 않았습니다")
    
    def _initialize_ocr_engine(self) -> bool:
        """PaddleOCR 엔진 초기화"""
        if not PADDLEOCR_AVAILABLE:
            return False
        
        try:
            with self._ocr_lock:
                current_time = time.time()
                
                # 기존 인스턴스 재사용 (30초 이내)
                if (self._shared_paddle_ocr is not None and 
                    current_time - self._last_init_time < 30):
                    self.paddle_ocr = self._shared_paddle_ocr
                    self.logger.info("기존 PaddleOCR 인스턴스 재사용")
                    return True
                
                # 새 인스턴스 생성
                self.logger.info("PaddleOCR 초기화 시작...")
                
                with suppress_stdout_stderr():
                    # GPU 사용 설정
                    use_gpu = self.config.get('use_gpu', False)
                    paddle_config = self.config.get('paddle_ocr_config', {})
                    
                    # GPU 메모리 최적화 설정
                    if use_gpu:
                        import os
                        gpu_memory_fraction = self.config.get('gpu_memory_fraction', 0.3)
                        os.environ['FLAGS_fraction_of_gpu_memory_to_use'] = str(gpu_memory_fraction)
                        os.environ['FLAGS_allocator_strategy'] = 'auto_growth'
                    
                    self.paddle_ocr = create_safe_paddleocr()
                
                # 공유 인스턴스 업데이트
                self._shared_paddle_ocr = self.paddle_ocr
                self._last_init_time = current_time
                
                # 스레드 풀 초기화
                self.executor = ThreadPoolExecutor(max_workers=self.max_workers)
                
                self.logger.info("PaddleOCR 초기화 완료")
                return True
                
        except Exception as e:
            self.logger.error(f"PaddleOCR 초기화 실패: {e}")
            self.paddle_ocr = None
            return False
    
    def _perform_ocr_internal(self, image: np.ndarray) -> List[Tuple[str, float, Tuple[int, int]]]:
        """PaddleOCR을 사용한 내부 OCR 처리"""
        if not self.paddle_ocr:
            return []
        
        try:
            # PaddleOCR 실행
            with suppress_stdout_stderr():
                paddle_results = self.paddle_ocr.ocr(image, cls=True)
            
            if not paddle_results or not paddle_results[0]:
                return []
            
            # 결과 변환
            results = []
            for line in paddle_results[0]:
                if len(line) >= 2:
                    bbox, (text, confidence) = line
                    
                    if text and confidence > 0.1:  # 최소 신뢰도 필터
                        # 바운딩 박스에서 중심점 계산
                        if bbox and len(bbox) >= 4:
                            x_coords = [point[0] for point in bbox]
                            y_coords = [point[1] for point in bbox]
                            center_x = int(sum(x_coords) / len(x_coords))
                            center_y = int(sum(y_coords) / len(y_coords))
                            position = (center_x, center_y)
                        else:
                            position = (0, 0)
                        
                        results.append((text, confidence, position))
            
            return results
            
        except Exception as e:
            self.logger.error(f"PaddleOCR 처리 오류: {e}")
            return []
    
    def is_available(self) -> bool:
        """PaddleOCR 사용 가능 여부 확인"""
        return PADDLEOCR_AVAILABLE and self.paddle_ocr is not None
    
    def perform_ocr_cached(self, image: np.ndarray, region: tuple[int, int, int, int] | None = None) -> str:
        """캐시를 고려한 OCR 처리 (기존 인터페이스 호환성)"""
        result = self.process_image(image, region)
        return result.text
    
    def perform_batch_ocr(self, images_and_regions: List[Tuple[np.ndarray, tuple]]) -> List[str]:
        """배치 OCR 처리"""
        if not self.executor:
            # 순차 처리 폴백
            return [self.perform_ocr_cached(img, region) for img, region in images_and_regions]
        
        try:
            # 병렬 처리
            futures = []
            for image, region in images_and_regions:
                future = self.executor.submit(self.perform_ocr_cached, image, region)
                futures.append(future)
            
            # 결과 수집
            results = []
            for future in futures:
                try:
                    result = future.result(timeout=5.0)  # 5초 타임아웃
                    results.append(result)
                except Exception as e:
                    self.logger.warning(f"배치 OCR 작업 실패: {e}")
                    results.append("")
            
            return results
            
        except Exception as e:
            self.logger.error(f"배치 OCR 처리 오류: {e}")
            # 순차 처리 폴백
            return [self.perform_ocr_cached(img, region) for img, region in images_and_regions]
    
    def cleanup(self):
        """리소스 정리"""
        try:
            if self.executor:
                self.executor.shutdown(wait=True)
                self.executor = None
            
            # 공유 인스턴스는 정리하지 않음 (다른 인스턴스에서 사용 중일 수 있음)
            self.paddle_ocr = None
            
            super().cleanup()
            
        except Exception as e:
            self.logger.error(f"PaddleOCR 서비스 정리 오류: {e}")