"""
캐시 관리 시스템
이미지 전처리 및 OCR 결과 캐싱
"""
from __future__ import annotations

import time
import hashlib
import pickle
import json
from collections import OrderedDict
from typing import Any, Optional, Tuple, Dict
import numpy as np
from pathlib import Path
import logging
import threading

class LRUCache:
    """LRU (Least Recently Used) 캐시 구현"""
    
    def __init__(self, max_size: int = 1000):
        self.max_size = max_size
        self.cache: OrderedDict[str, Tuple[Any, float]] = OrderedDict()
        self.lock = threading.RLock()
        self.hits = 0
        self.misses = 0
        
    def get(self, key: str) -> Optional[Any]:
        """캐시에서 값 가져오기"""
        with self.lock:
            if key in self.cache:
                # LRU 업데이트 - 최근 사용으로 이동
                value, timestamp = self.cache.pop(key)
                self.cache[key] = (value, time.time())
                self.hits += 1
                return value
            self.misses += 1
            return None
    
    def put(self, key: str, value: Any):
        """캐시에 값 저장"""
        with self.lock:
            # 기존 키가 있으면 제거
            if key in self.cache:
                self.cache.pop(key)
            
            # 새 값 추가
            self.cache[key] = (value, time.time())
            
            # 크기 제한 확인
            if len(self.cache) > self.max_size:
                # 가장 오래된 항목 제거
                self.cache.popitem(last=False)
    
    def clear(self):
        """캐시 초기화"""
        with self.lock:
            self.cache.clear()
            self.hits = 0
            self.misses = 0
    
    def get_stats(self) -> Dict[str, Any]:
        """캐시 통계 반환"""
        with self.lock:
            total = self.hits + self.misses
            hit_rate = (self.hits / total * 100) if total > 0 else 0
            return {
                'size': len(self.cache),
                'max_size': self.max_size,
                'hits': self.hits,
                'misses': self.misses,
                'hit_rate': hit_rate,
                'total_requests': total
            }

class ImageCache:
    """이미지 전처리 결과 캐시"""
    
    def __init__(self, max_size_mb: int = 500):
        self.max_size_bytes = max_size_mb * 1024 * 1024
        self.cache = LRUCache(max_size=1000)
        self.current_size_bytes = 0
        self.logger = logging.getLogger(__name__)
        
    def _compute_image_hash(self, image: np.ndarray) -> str:
        """이미지 해시 계산"""
        # 이미지를 바이트로 변환하여 해시 계산
        image_bytes = image.tobytes()
        return hashlib.md5(image_bytes).hexdigest()
    
    def _estimate_size(self, image: np.ndarray) -> int:
        """이미지 크기 추정 (바이트)"""
        return image.nbytes
    
    def get(self, image: np.ndarray) -> Optional[np.ndarray]:
        """캐시에서 전처리된 이미지 가져오기"""
        key = self._compute_image_hash(image)
        return self.cache.get(key)
    
    def put(self, original: np.ndarray, processed: np.ndarray):
        """전처리된 이미지 캐시에 저장"""
        key = self._compute_image_hash(original)
        size = self._estimate_size(processed)
        
        # 크기 제한 확인
        if self.current_size_bytes + size > self.max_size_bytes:
            self.logger.info("이미지 캐시 크기 제한 도달, 오래된 항목 제거")
            # 간단한 구현: 전체 캐시 클리어
            self.clear()
        
        self.cache.put(key, processed)
        self.current_size_bytes += size
    
    def clear(self):
        """캐시 초기화"""
        self.cache.clear()
        self.current_size_bytes = 0
    
    def get_stats(self) -> Dict[str, Any]:
        """캐시 통계"""
        stats = self.cache.get_stats()
        stats['size_mb'] = self.current_size_bytes / 1024 / 1024
        stats['max_size_mb'] = self.max_size_bytes / 1024 / 1024
        return stats

class OCRResultCache:
    """OCR 결과 캐시"""
    
    def __init__(self, ttl_seconds: int = 60):
        self.ttl_seconds = ttl_seconds
        self.cache = LRUCache(max_size=500)
        self.logger = logging.getLogger(__name__)
        
    def _compute_region_hash(self, x: int, y: int, w: int, h: int, 
                            image_hash: Optional[str] = None) -> str:
        """영역 해시 계산"""
        # 위치와 크기를 기반으로 해시 생성
        region_str = f"{x}_{y}_{w}_{h}"
        if image_hash:
            region_str += f"_{image_hash}"
        return hashlib.md5(region_str.encode()).hexdigest()
    
    def get(self, x: int, y: int, w: int, h: int, 
            image: Optional[np.ndarray] = None) -> Optional[Dict[str, Any]]:
        """캐시에서 OCR 결과 가져오기"""
        image_hash = None
        if image is not None:
            image_hash = hashlib.md5(image.tobytes()).hexdigest()[:8]
        
        key = self._compute_region_hash(x, y, w, h, image_hash)
        result = self.cache.get(key)
        
        if result:
            # TTL 확인
            cached_data, cached_time = result
            if time.time() - cached_time > self.ttl_seconds:
                return None
            return cached_data
        
        return None
    
    def put(self, x: int, y: int, w: int, h: int, 
            ocr_result: Dict[str, Any], image: Optional[np.ndarray] = None):
        """OCR 결과 캐시에 저장"""
        image_hash = None
        if image is not None:
            image_hash = hashlib.md5(image.tobytes()).hexdigest()[:8]
        
        key = self._compute_region_hash(x, y, w, h, image_hash)
        self.cache.put(key, (ocr_result, time.time()))
    
    def clear_expired(self):
        """만료된 항목 제거"""
        current_time = time.time()
        expired_keys = []
        
        with self.cache.lock:
            for key, (value, timestamp) in self.cache.cache.items():
                if current_time - timestamp > self.ttl_seconds:
                    expired_keys.append(key)
            
            for key in expired_keys:
                self.cache.cache.pop(key)
        
        if expired_keys:
            self.logger.info(f"만료된 OCR 캐시 항목 {len(expired_keys)}개 제거")

class CacheManager:
    """통합 캐시 관리자"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.logger = logging.getLogger(__name__)
        
        # 캐시 인스턴스
        self.image_cache = ImageCache(
            max_size_mb=self.config.get('image_cache_size_mb', 500)
        )
        self.ocr_cache = OCRResultCache(
            ttl_seconds=self.config.get('ocr_cache_ttl', 60)
        )
        
        # 캐시 파일 경로
        self.cache_dir = Path(self.config.get('cache_dir', './cache'))
        self.cache_dir.mkdir(exist_ok=True)
        
        # 정리 스레드
        self._cleanup_thread = None
        self._stop_cleanup = threading.Event()
        
    def start(self):
        """캐시 관리자 시작"""
        self._stop_cleanup.clear()
        self._cleanup_thread = threading.Thread(
            target=self._cleanup_loop,
            name="CacheCleanup",
            daemon=True
        )
        self._cleanup_thread.start()
        self.logger.info("캐시 관리자 시작")
    
    def stop(self):
        """캐시 관리자 중지"""
        self._stop_cleanup.set()
        if self._cleanup_thread:
            self._cleanup_thread.join(timeout=2.0)
        self.logger.info("캐시 관리자 중지")
    
    def _cleanup_loop(self):
        """주기적 캐시 정리"""
        while not self._stop_cleanup.is_set():
            try:
                # OCR 캐시 만료 항목 제거
                self.ocr_cache.clear_expired()
                
                # 30초마다 정리
                self._stop_cleanup.wait(30)
                
            except Exception as e:
                self.logger.error(f"캐시 정리 오류: {e}")
    
    def get_preprocessed_image(self, image: np.ndarray) -> Optional[np.ndarray]:
        """전처리된 이미지 가져오기"""
        return self.image_cache.get(image)
    
    def cache_preprocessed_image(self, original: np.ndarray, processed: np.ndarray):
        """전처리된 이미지 캐싱"""
        self.image_cache.put(original, processed)
    
    def get_ocr_result(self, x: int, y: int, w: int, h: int, 
                      image: Optional[np.ndarray] = None) -> Optional[Dict[str, Any]]:
        """OCR 결과 가져오기"""
        return self.ocr_cache.get(x, y, w, h, image)
    
    def cache_ocr_result(self, x: int, y: int, w: int, h: int,
                        result: Dict[str, Any], image: Optional[np.ndarray] = None):
        """OCR 결과 캐싱"""
        self.ocr_cache.put(x, y, w, h, result, image)
    
    def get_stats(self) -> Dict[str, Any]:
        """전체 캐시 통계"""
        return {
            'image_cache': self.image_cache.get_stats(),
            'ocr_cache': self.ocr_cache.cache.get_stats()
        }
    
    def clear_all(self):
        """모든 캐시 초기화"""
        self.image_cache.clear()
        self.ocr_cache.cache.clear()
        self.logger.info("모든 캐시 초기화 완료")
    
    def save_cache_to_disk(self):
        """캐시를 디스크에 저장"""
        try:
            cache_file = self.cache_dir / 'cache_data.pkl'
            cache_data = {
                'ocr_cache': dict(self.ocr_cache.cache.cache),
                'stats': self.get_stats(),
                'timestamp': time.time()
            }
            
            with open(cache_file, 'wb') as f:
                pickle.dump(cache_data, f)
            
            self.logger.info(f"캐시 저장 완료: {cache_file}")
            
        except Exception as e:
            self.logger.error(f"캐시 저장 실패: {e}")
    
    def load_cache_from_disk(self):
        """디스크에서 캐시 로드"""
        try:
            cache_file = self.cache_dir / 'cache_data.pkl'
            if not cache_file.exists():
                return
            
            with open(cache_file, 'rb') as f:
                cache_data = pickle.load(f)
            
            # OCR 캐시만 복원 (이미지 캐시는 크기 때문에 제외)
            if 'ocr_cache' in cache_data:
                for key, value in cache_data['ocr_cache'].items():
                    self.ocr_cache.cache.cache[key] = value
            
            self.logger.info(f"캐시 로드 완료: {cache_file}")
            
        except Exception as e:
            self.logger.error(f"캐시 로드 실패: {e}")