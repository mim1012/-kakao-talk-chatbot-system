"""
스마트 캐시 시스템 - 성능 최적화를 위한 지능형 캐싱
"""
from __future__ import annotations

import time
import hashlib
import numpy as np
from typing import Dict, Optional, Tuple
from dataclasses import dataclass
from collections import OrderedDict
import logging

@dataclass
class CacheEntry:
    """캐시 항목"""
    data: any
    timestamp: float
    access_count: int
    last_access: float
    hit_rate: float = 0.0

class SmartCache:
    """지능형 캐시 시스템"""
    
    def __init__(self, max_size: int = 1000, ttl: float = 300):
        self.max_size = max_size
        self.ttl = ttl  # Time to live in seconds
        self._cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self.stats = {
            'hits': 0,
            'misses': 0,
            'evictions': 0,
            'total_requests': 0
        }
        self.logger = logging.getLogger(__name__)
    
    def _generate_key(self, image: np.ndarray, prefix: str = "") -> str:
        """이미지 기반 캐시 키 생성"""
        image_hash = hashlib.md5(image.tobytes()).hexdigest()
        return f"{prefix}_{image_hash}" if prefix else image_hash
    
    def get(self, key: str) -> Optional[any]:
        """캐시에서 값 조회"""
        self.stats['total_requests'] += 1
        current_time = time.time()
        
        if key in self._cache:
            entry = self._cache[key]
            
            # TTL 확인
            if current_time - entry.timestamp > self.ttl:
                self._remove(key)
                self.stats['misses'] += 1
                return None
            
            # 액세스 정보 업데이트
            entry.access_count += 1
            entry.last_access = current_time
            entry.hit_rate = self.stats['hits'] / self.stats['total_requests']
            
            # LRU 업데이트
            self._cache.move_to_end(key)
            
            self.stats['hits'] += 1
            return entry.data
        
        self.stats['misses'] += 1
        return None
    
    def put(self, key: str, value: any) -> None:
        """캐시에 값 저장"""
        current_time = time.time()
        
        if key in self._cache:
            # 기존 항목 업데이트
            self._cache[key].data = value
            self._cache[key].timestamp = current_time
            self._cache.move_to_end(key)
        else:
            # 새 항목 추가
            if len(self._cache) >= self.max_size:
                self._evict_least_valuable()
            
            self._cache[key] = CacheEntry(
                data=value,
                timestamp=current_time,
                access_count=1,
                last_access=current_time
            )
    
    def _evict_least_valuable(self) -> None:
        """가장 가치가 낮은 항목 제거"""
        if not self._cache:
            return
        
        current_time = time.time()
        
        # 가치 점수 계산: 최근성 + 사용 빈도 + 히트율
        least_valuable_key = None
        lowest_score = float('inf')
        
        for key, entry in self._cache.items():
            age = current_time - entry.timestamp
            recency_score = 1.0 / (1.0 + age / 3600)  # 1시간 기준
            frequency_score = min(entry.access_count / 10.0, 1.0)
            hit_rate_score = entry.hit_rate
            
            total_score = recency_score + frequency_score + hit_rate_score
            
            if total_score < lowest_score:
                lowest_score = total_score
                least_valuable_key = key
        
        if least_valuable_key:
            self._remove(least_valuable_key)
            self.stats['evictions'] += 1
    
    def _remove(self, key: str) -> None:
        """캐시에서 항목 제거"""
        if key in self._cache:
            del self._cache[key]
    
    def clear_expired(self) -> int:
        """만료된 항목들 정리"""
        current_time = time.time()
        expired_keys = [
            key for key, entry in self._cache.items()
            if current_time - entry.timestamp > self.ttl
        ]
        
        for key in expired_keys:
            self._remove(key)
        
        return len(expired_keys)
    
    def get_stats(self) -> Dict:
        """캐시 통계 반환"""
        hit_rate = (self.stats['hits'] / self.stats['total_requests'] * 100 
                   if self.stats['total_requests'] > 0 else 0)
        
        return {
            'size': len(self._cache),
            'max_size': self.max_size,
            'hit_rate': f"{hit_rate:.1f}%",
            'hits': self.stats['hits'],
            'misses': self.stats['misses'],
            'evictions': self.stats['evictions'],
            'total_requests': self.stats['total_requests']
        }
    
    def optimize(self) -> None:
        """캐시 최적화"""
        # 만료된 항목 정리
        expired_count = self.clear_expired()
        
        # 사용률이 낮은 항목 제거
        if len(self._cache) > self.max_size * 0.8:
            current_time = time.time()
            low_usage_keys = [
                key for key, entry in self._cache.items()
                if entry.access_count < 2 and 
                   current_time - entry.last_access > self.ttl / 2
            ]
            
            for key in low_usage_keys[:len(low_usage_keys)//2]:
                self._remove(key)
        
        if expired_count > 0:
            self.logger.debug(f"Cache optimized: removed {expired_count} expired entries")

class ImageCache(SmartCache):
    """이미지 전용 캐시"""
    
    def cache_ocr_result(self, image: np.ndarray, result: any, cell_id: str = "") -> None:
        """OCR 결과 캐싱"""
        key = self._generate_key(image, f"ocr_{cell_id}")
        self.put(key, result)
    
    def get_ocr_result(self, image: np.ndarray, cell_id: str = "") -> Optional[any]:
        """OCR 결과 조회"""
        key = self._generate_key(image, f"ocr_{cell_id}")
        return self.get(key)
    
    def cache_preprocessed_image(self, original: np.ndarray, processed: np.ndarray, 
                               strategy_name: str) -> None:
        """전처리된 이미지 캐싱"""
        key = self._generate_key(original, f"preprocess_{strategy_name}")
        self.put(key, processed)
    
    def get_preprocessed_image(self, original: np.ndarray, strategy_name: str) -> Optional[np.ndarray]:
        """전처리된 이미지 조회"""
        key = self._generate_key(original, f"preprocess_{strategy_name}")
        return self.get(key)