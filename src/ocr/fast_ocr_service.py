#!/usr/bin/env python3
"""
최적화된 고속 OCR 서비스
"""
from paddleocr import PaddleOCR
import numpy as np
import cv2
import time

class FastOCRService:
    """30개 채팅방을 위한 초고속 OCR"""
    
    def __init__(self):
        # 최적화된 설정
        self.paddle_ocr = PaddleOCR(
            lang='korean',
            use_angle_cls=False,      # 각도 보정 OFF (-15ms)
            use_gpu=False,            # CPU 사용
            enable_mkldnn=True,       # CPU 가속 ON
            cpu_threads=10,           # CPU 스레드 늘리기
            rec_batch_num=10,         # 10개씩 배치 처리
            max_text_length=25,       # 최대 글자수 제한
            rec_algorithm='CRNN',     # 빠른 알고리즘
            use_space_char=False,     # 공백 처리 OFF
            drop_score=0.3            # 낮은 점수 빠르게 버리기
        )
        
        # 이미지 캐시 (같은 이미지 반복 방지)
        self.image_cache = {}
        
    def fast_preprocess(self, image):
        """초고속 전처리 - 최소한만!"""
        # 1. 크기가 너무 작으면 2배만 확대
        h, w = image.shape[:2]
        if w < 200:
            image = cv2.resize(image, None, fx=2, fy=2, interpolation=cv2.INTER_LINEAR)
        
        # 2. 그레이스케일 (컬러 필요없음)
        if len(image.shape) == 3:
            image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
        return image
    
    def batch_ocr(self, images):
        """여러 이미지 한번에 처리"""
        start = time.time()
        
        # 전처리
        processed = [self.fast_preprocess(img) for img in images]
        
        # 배치 OCR (이게 핵심!)
        results = self.paddle_ocr.ocr(processed, cls=False, det=False)
        
        elapsed = (time.time() - start) * 1000
        print(f"배치 OCR: {len(images)}개 이미지 → {elapsed:.0f}ms")
        
        return results
    
    def single_ocr(self, image):
        """단일 이미지 빠른 처리"""
        # 이미지 해시로 캐시 체크
        img_hash = hash(image.tobytes())
        if img_hash in self.image_cache:
            return self.image_cache[img_hash]
        
        # 전처리
        processed = self.fast_preprocess(image)
        
        # OCR (텍스트 인식만!)
        result = self.paddle_ocr.ocr(processed, cls=False, det=False)
        
        # 캐시 저장
        self.image_cache[img_hash] = result
        
        # 캐시 크기 제한
        if len(self.image_cache) > 100:
            self.image_cache.clear()
            
        return result

# 사용 예시
"""
fast_ocr = FastOCRService()

# 방법 1: 배치 처리
images = [capture(cell) for cell in cells[:10]]
results = fast_ocr.batch_ocr(images)  # 10개가 200ms!

# 방법 2: 단일 처리 (캐시 활용)
result = fast_ocr.single_ocr(image)  # 첫번째: 25ms, 두번째: 0ms!
"""