"""
간단한 캐시 구현 (numpy 의존성 없음)
테스트 및 기본 기능용
"""
from collections import OrderedDict
import time
import threading

class SimpleLRUCache:
    """numpy 없는 간단한 LRU 캐시"""
    
    def __init__(self, max_size: int = 100):
        self.max_size = max_size
        self.cache = OrderedDict()
        self.lock = threading.RLock()
        self.hits = 0
        self.misses = 0
        
    def get(self, key: str):
        """캐시에서 값 가져오기"""
        with self.lock:
            if key in self.cache:
                # LRU 업데이트
                value = self.cache.pop(key)
                self.cache[key] = value
                self.hits += 1
                return value
            self.misses += 1
            return None
    
    def put(self, key: str, value):
        """캐시에 값 저장"""
        with self.lock:
            if key in self.cache:
                self.cache.pop(key)
            
            self.cache[key] = value
            
            if len(self.cache) > self.max_size:
                self.cache.popitem(last=False)
    
    def clear(self):
        """캐시 초기화"""
        with self.lock:
            self.cache.clear()
            self.hits = 0
            self.misses = 0
    
    def get_stats(self):
        """캐시 통계"""
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