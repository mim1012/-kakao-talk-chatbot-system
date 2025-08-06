"""
Tesseract OCR 서비스 - PaddleOCR보다 빠른 대안
"""
from __future__ import annotations

import logging
import numpy as np
import cv2
from typing import List, Tuple
import pytesseract
from ocr.base_ocr_service import BaseOCRService
from core.config_manager import ConfigManager

# Tesseract 경로 설정 (Windows)
import os
if os.name == 'nt':  # Windows
    # 일반적인 Tesseract 설치 경로
    tesseract_paths = [
        r'C:\Program Files\Tesseract-OCR\tesseract.exe',
        r'C:\Program Files (x86)\Tesseract-OCR\tesseract.exe',
        r'C:\tesseract\tesseract.exe'
    ]
    for path in tesseract_paths:
        if os.path.exists(path):
            pytesseract.pytesseract.tesseract_cmd = path
            break

class TesseractOCRService(BaseOCRService):
    """Tesseract 기반 빠른 OCR 서비스"""
    
    def __init__(self, config_manager: ConfigManager):
        super().__init__(config_manager)
        self.logger = logging.getLogger(__name__)
        
        # Tesseract 설정
        self.custom_config = r'--oem 3 --psm 6 -l kor'  # 한글 OCR
        
        # Tesseract 사용 가능 확인
        try:
            pytesseract.get_tesseract_version()
            self.available = True
            self.logger.info("Tesseract OCR 초기화 성공")
        except Exception as e:
            self.available = False
            self.logger.error(f"Tesseract OCR 초기화 실패: {e}")
    
    def _initialize_ocr_engine(self) -> bool:
        """OCR 엔진 초기화"""
        return self.available
    
    def _perform_ocr_internal(self, image: np.ndarray) -> List[Tuple[str, float, Tuple[int, int]]]:
        """Tesseract을 사용한 내부 OCR 처리"""
        if not self.available:
            return []
        
        try:
            # 이미지 전처리 (간단하게)
            if len(image.shape) == 3:
                gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            else:
                gray = image
            
            # Tesseract OCR 실행
            data = pytesseract.image_to_data(gray, output_type=pytesseract.Output.DICT, config=self.custom_config)
            
            results = []
            for i in range(len(data['text'])):
                text = data['text'][i].strip()
                if text:  # 빈 텍스트 제외
                    conf = int(data['conf'][i]) / 100.0  # 신뢰도를 0-1 범위로 변환
                    if conf > 0:  # 신뢰도가 0보다 큰 경우만
                        x, y = data['left'][i], data['top'][i]
                        results.append((text, conf, (x, y)))
            
            return results
            
        except Exception as e:
            self.logger.error(f"Tesseract OCR 처리 오류: {e}")
            return []
    
    def is_available(self) -> bool:
        """Tesseract 사용 가능 여부 확인"""
        return self.available
    
    def perform_ocr_cached(self, image: np.ndarray, region: tuple[int, int, int, int] | None = None) -> str:
        """캐시를 고려한 OCR 처리"""
        result = self.process_image(image, region)
        return result.text
    
    def perform_batch_ocr(self, images_and_regions: List[Tuple[np.ndarray, tuple]]) -> List[str]:
        """배치 OCR 처리 (순차 처리)"""
        results = []
        for image, region in images_and_regions:
            results.append(self.perform_ocr_cached(image, region))
        return results
    
    def cleanup(self):
        """리소스 정리"""
        super().cleanup()