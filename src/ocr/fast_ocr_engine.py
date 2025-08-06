"""
고속 OCR 엔진
병렬 처리, 캐싱, 이미지 전처리 최적화를 통한 OCR 성능 개선
"""

import cv2
import numpy as np
import time
import hashlib
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Tuple, Optional, Dict, Any
from dataclasses import dataclass
from paddleocr import PaddleOCR
import logging

@dataclass
class FastOCRResult:
    """빠른 OCR 결과"""
    text: str
    confidence: float
    processing_time: float
    from_cache: bool = False

class ImagePreprocessor:
    """최적화된 이미지 전처리기"""
    
    @staticmethod
    def fast_preprocess(image: np.ndarray) -> np.ndarray:
        """빠른 전처리 - 최소한의 처리만"""
        # 이미 그레이스케일이면 스킵
        if len(image.shape) == 2:
            return image
            
        # BGR/BGRA to Grayscale (빠른 변환)
        if image.shape[2] == 4:
            # BGRA -> BGR
            image = image[:, :, :3]
        
        # 빠른 그레이스케일 변환
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # 간단한 대비 향상 (CLAHE 대신 더 빠른 방법)
        # 히스토그램 균등화는 CLAHE보다 3-4배 빠름
        gray = cv2.equalizeHist(gray)
        
        return gray
    
    @staticmethod
    def ultra_fast_preprocess(image: np.ndarray) -> np.ndarray:
        """초고속 전처리 - 그레이스케일 변환만"""
        if len(image.shape) == 2:
            return image
            
        if image.shape[2] == 4:
            image = image[:, :, :3]
            
        return cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

class OCRCache:
    """고속 OCR 캐시"""
    
    def __init__(self, max_size: int = 100, ttl: float = 5.0):
        self.cache: Dict[str, Tuple[FastOCRResult, float]] = {}
        self.max_size = max_size
        self.ttl = ttl
        self.lock = threading.Lock()
        self.hits = 0
        self.misses = 0
    
    def _get_hash(self, image: np.ndarray) -> str:
        """이미지 해시 생성 (빠른 버전)"""
        # 이미지를 축소하여 해시 계산 속도 향상
        small = cv2.resize(image, (32, 32))
        return hashlib.md5(small.tobytes()).hexdigest()
    
    def get(self, image: np.ndarray) -> Optional[FastOCRResult]:
        """캐시에서 결과 조회"""
        img_hash = self._get_hash(image)
        
        with self.lock:
            if img_hash in self.cache:
                result, timestamp = self.cache[img_hash]
                if time.time() - timestamp < self.ttl:
                    self.hits += 1
                    result.from_cache = True
                    return result
                else:
                    del self.cache[img_hash]
            
            self.misses += 1
            return None
    
    def put(self, image: np.ndarray, result: FastOCRResult):
        """캐시에 결과 저장"""
        img_hash = self._get_hash(image)
        
        with self.lock:
            # 캐시 크기 제한
            if len(self.cache) >= self.max_size:
                # 가장 오래된 항목 제거
                oldest_key = min(self.cache.keys(), 
                               key=lambda k: self.cache[k][1])
                del self.cache[oldest_key]
            
            self.cache[img_hash] = (result, time.time())
    
    def get_stats(self) -> Dict[str, Any]:
        """캐시 통계"""
        total = self.hits + self.misses
        hit_rate = self.hits / total if total > 0 else 0
        return {
            'hits': self.hits,
            'misses': self.misses,
            'hit_rate': hit_rate,
            'size': len(self.cache)
        }

class FastOCREngine:
    """고속 OCR 엔진"""
    
    def __init__(self, num_workers: int = 3, use_gpu: bool = False):
        self.num_workers = num_workers
        self.use_gpu = use_gpu
        self.logger = logging.getLogger(__name__)
        
        # OCR 인스턴스 풀 (각 워커당 하나)
        self.ocr_pool = []
        self.pool_lock = threading.Lock()
        self._init_ocr_pool()
        
        # 캐시
        self.cache = OCRCache(max_size=200, ttl=10.0)
        
        # 전처리기
        self.preprocessor = ImagePreprocessor()
        
        # 스레드 풀
        self.executor = ThreadPoolExecutor(max_workers=num_workers)
        
    def _init_ocr_pool(self):
        """OCR 인스턴스 풀 초기화"""
        for i in range(self.num_workers):
            try:
                ocr = PaddleOCR(
                    use_angle_cls=False,
                    lang='korean',
                    use_gpu=self.use_gpu,
                    show_log=False,
                    det_db_thresh=0.3,
                    det_db_box_thresh=0.5,
                    rec_batch_num=6,  # 배치 크기 증가
                    max_text_length=25,
                    use_mp=True,  # 멀티프로세싱 사용
                    total_process_num=2,
                    det_limit_side_len=960,  # 더 작은 크기로 제한
                    det_limit_type='min',
                    drop_score=0.5
                )
                self.ocr_pool.append(ocr)
            except Exception as e:
                self.logger.error(f"OCR 인스턴스 {i} 생성 실패: {e}")
    
    def _get_ocr_instance(self):
        """사용 가능한 OCR 인스턴스 가져오기"""
        with self.pool_lock:
            if self.ocr_pool:
                return self.ocr_pool.pop()
        return None
    
    def _return_ocr_instance(self, ocr):
        """OCR 인스턴스 반환"""
        with self.pool_lock:
            self.ocr_pool.append(ocr)
    
    def process_single(self, image: np.ndarray, use_cache: bool = True) -> FastOCRResult:
        """단일 이미지 OCR 처리"""
        start_time = time.perf_counter()
        
        # 캐시 확인
        if use_cache:
            cached = self.cache.get(image)
            if cached:
                return cached
        
        # 전처리
        preprocessed = self.preprocessor.ultra_fast_preprocess(image)
        
        # OCR 실행
        ocr = self._get_ocr_instance()
        if not ocr:
            # 풀이 비어있으면 새로 생성
            ocr = PaddleOCR(
                use_angle_cls=False,
                lang='korean',
                use_gpu=self.use_gpu,
                show_log=False
            )
        
        try:
            results = ocr.ocr(preprocessed, cls=False)
            
            # 결과 파싱
            text = ""
            confidence = 0.0
            
            if results and results[0]:
                texts = []
                confidences = []
                for line in results[0]:
                    if line and len(line) >= 2:
                        txt = line[1][0] if line[1] else ""
                        conf = line[1][1] if line[1] and len(line[1]) > 1 else 0.0
                        texts.append(txt)
                        confidences.append(conf)
                
                text = " ".join(texts)
                confidence = sum(confidences) / len(confidences) if confidences else 0.0
            
            processing_time = time.perf_counter() - start_time
            result = FastOCRResult(text, confidence, processing_time)
            
            # 캐시 저장
            if use_cache:
                self.cache.put(image, result)
            
            return result
            
        finally:
            self._return_ocr_instance(ocr)
    
    def process_batch(self, images: List[np.ndarray]) -> List[FastOCRResult]:
        """배치 OCR 처리 (병렬)"""
        if not images:
            return []
        
        # 작은 배치는 단일 처리
        if len(images) <= 2:
            return [self.process_single(img) for img in images]
        
        # 병렬 처리
        futures = []
        results = [None] * len(images)
        
        for i, image in enumerate(images):
            future = self.executor.submit(self.process_single, image)
            futures.append((i, future))
        
        # 결과 수집
        for i, future in futures:
            try:
                results[i] = future.result(timeout=2.0)
            except Exception as e:
                self.logger.error(f"OCR 처리 실패 (인덱스 {i}): {e}")
                results[i] = FastOCRResult("", 0.0, 0.0)
        
        return results
    
    def process_batch_sequential(self, images: List[np.ndarray]) -> List[FastOCRResult]:
        """순차 배치 처리 (단일 OCR 인스턴스 사용)"""
        if not images:
            return []
        
        results = []
        ocr = self._get_ocr_instance()
        
        if not ocr:
            ocr = PaddleOCR(
                use_angle_cls=False,
                lang='korean',
                use_gpu=self.use_gpu,
                show_log=False,
                rec_batch_num=len(images)  # 전체를 한 배치로
            )
        
        try:
            # 전처리
            preprocessed = [self.preprocessor.ultra_fast_preprocess(img) for img in images]
            
            # 배치 OCR
            for img in preprocessed:
                start_time = time.perf_counter()
                
                # 캐시 확인
                cached = self.cache.get(img)
                if cached:
                    results.append(cached)
                    continue
                
                # OCR 실행
                ocr_results = ocr.ocr(img, cls=False)
                
                # 결과 파싱
                text = ""
                confidence = 0.0
                
                if ocr_results and ocr_results[0]:
                    texts = []
                    confidences = []
                    for line in ocr_results[0]:
                        if line and len(line) >= 2:
                            txt = line[1][0] if line[1] else ""
                            conf = line[1][1] if line[1] and len(line[1]) > 1 else 0.0
                            texts.append(txt)
                            confidences.append(conf)
                    
                    text = " ".join(texts)
                    confidence = sum(confidences) / len(confidences) if confidences else 0.0
                
                processing_time = time.perf_counter() - start_time
                result = FastOCRResult(text, confidence, processing_time)
                
                # 캐시 저장
                self.cache.put(img, result)
                results.append(result)
            
            return results
            
        finally:
            self._return_ocr_instance(ocr)
    
    def shutdown(self):
        """엔진 종료"""
        self.executor.shutdown(wait=True)
        
    def get_stats(self) -> Dict[str, Any]:
        """성능 통계"""
        return {
            'cache': self.cache.get_stats(),
            'pool_size': len(self.ocr_pool),
            'num_workers': self.num_workers
        }