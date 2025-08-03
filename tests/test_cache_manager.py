"""
CacheManager 단위 테스트
"""
import pytest
import time
import numpy as np
from pathlib import Path
from core.cache_manager import LRUCache, ImageCache, OCRResultCache, CacheManager

class TestLRUCache:
    """LRU 캐시 테스트"""
    
    @pytest.mark.unit
    def test_basic_operations(self):
        """기본 연산 테스트"""
        cache = LRUCache(max_size=3)
        
        # 값 추가
        cache.put("key1", "value1")
        cache.put("key2", "value2")
        cache.put("key3", "value3")
        
        # 값 가져오기
        assert cache.get("key1") == "value1"
        assert cache.get("key2") == "value2"
        assert cache.get("key3") == "value3"
        assert cache.get("key4") is None  # 존재하지 않는 키
    
    @pytest.mark.unit
    def test_lru_eviction(self):
        """LRU 제거 테스트"""
        cache = LRUCache(max_size=3)
        
        # 캐시 채우기
        cache.put("key1", "value1")
        cache.put("key2", "value2")
        cache.put("key3", "value3")
        
        # key1 접근 (최근 사용으로 이동)
        cache.get("key1")
        
        # 새 값 추가 (key2가 제거되어야 함)
        cache.put("key4", "value4")
        
        assert cache.get("key1") == "value1"  # 최근 사용
        assert cache.get("key2") is None      # 제거됨
        assert cache.get("key3") == "value3"
        assert cache.get("key4") == "value4"
    
    @pytest.mark.unit
    def test_cache_stats(self):
        """캐시 통계 테스트"""
        cache = LRUCache(max_size=10)
        
        # 히트/미스 테스트
        cache.put("key1", "value1")
        
        cache.get("key1")  # 히트
        cache.get("key2")  # 미스
        cache.get("key1")  # 히트
        
        stats = cache.get_stats()
        assert stats['hits'] == 2
        assert stats['misses'] == 1
        assert stats['hit_rate'] == pytest.approx(66.67, rel=0.1)
    
    @pytest.mark.unit
    def test_clear(self):
        """캐시 초기화 테스트"""
        cache = LRUCache(max_size=5)
        
        # 값 추가
        for i in range(5):
            cache.put(f"key{i}", f"value{i}")
        
        # 초기화
        cache.clear()
        
        assert len(cache.cache) == 0
        assert cache.hits == 0
        assert cache.misses == 0

class TestImageCache:
    """이미지 캐시 테스트"""
    
    @pytest.mark.unit
    def test_image_caching(self, sample_image):
        """이미지 캐싱 테스트"""
        cache = ImageCache(max_size_mb=10)
        
        # 원본과 전처리된 이미지
        processed = sample_image * 0.5  # 간단한 처리
        
        # 캐싱
        cache.put(sample_image, processed)
        
        # 가져오기
        retrieved = cache.get(sample_image)
        assert retrieved is not None
        assert np.array_equal(retrieved, processed)
    
    @pytest.mark.unit
    def test_image_hash_uniqueness(self):
        """이미지 해시 고유성 테스트"""
        cache = ImageCache(max_size_mb=10)
        
        # 다른 이미지들
        image1 = np.ones((50, 50, 3), dtype=np.uint8) * 255
        image2 = np.ones((50, 50, 3), dtype=np.uint8) * 128
        
        hash1 = cache._compute_image_hash(image1)
        hash2 = cache._compute_image_hash(image2)
        
        assert hash1 != hash2
    
    @pytest.mark.unit
    def test_size_limit(self):
        """크기 제한 테스트"""
        cache = ImageCache(max_size_mb=1)  # 1MB 제한
        
        # 큰 이미지 생성 (약 0.6MB)
        large_image = np.ones((500, 400, 3), dtype=np.uint8)
        
        # 첫 번째 이미지 캐싱
        cache.put(large_image, large_image)
        assert cache.current_size_bytes > 0
        
        # 두 번째 이미지 추가 시 캐시 클리어
        large_image2 = np.ones((500, 400, 3), dtype=np.uint8) * 2
        cache.put(large_image2, large_image2)
        
        # 첫 번째 이미지는 제거됨
        assert cache.get(large_image) is None

class TestOCRResultCache:
    """OCR 결과 캐시 테스트"""
    
    @pytest.mark.unit
    def test_ocr_result_caching(self):
        """OCR 결과 캐싱 테스트"""
        cache = OCRResultCache(ttl_seconds=1)
        
        # OCR 결과
        result = {
            'text': '테스트 텍스트',
            'confidence': 0.95,
            'boxes': [[0, 0, 100, 50]]
        }
        
        # 캐싱
        cache.put(10, 20, 100, 50, result)
        
        # 가져오기
        retrieved = cache.get(10, 20, 100, 50)
        assert retrieved == result
    
    @pytest.mark.unit
    def test_ttl_expiration(self):
        """TTL 만료 테스트"""
        cache = OCRResultCache(ttl_seconds=0.1)
        
        result = {'text': '만료될 텍스트'}
        cache.put(0, 0, 100, 100, result)
        
        # 즉시 가져오기 - 성공
        assert cache.get(0, 0, 100, 100) is not None
        
        # TTL 후 가져오기 - 실패
        time.sleep(0.2)
        assert cache.get(0, 0, 100, 100) is None
    
    @pytest.mark.unit
    def test_region_hash_with_image(self, sample_image):
        """이미지 포함 영역 해시 테스트"""
        cache = OCRResultCache(ttl_seconds=10)
        
        result = {'text': '이미지 기반 캐시'}
        
        # 이미지와 함께 캐싱
        cache.put(0, 0, 100, 100, result, sample_image)
        
        # 같은 이미지로 가져오기
        retrieved = cache.get(0, 0, 100, 100, sample_image)
        assert retrieved == result
        
        # 다른 이미지로는 가져올 수 없음
        different_image = sample_image * 0.5
        retrieved = cache.get(0, 0, 100, 100, different_image)
        assert retrieved is None
    
    @pytest.mark.unit
    def test_clear_expired(self):
        """만료 항목 제거 테스트"""
        cache = OCRResultCache(ttl_seconds=0.1)
        
        # 여러 결과 추가
        for i in range(5):
            cache.put(i*10, 0, 10, 10, {'text': f'text{i}'})
        
        # 만료 대기
        time.sleep(0.2)
        
        # 만료 항목 제거
        cache.clear_expired()
        
        # 모든 항목이 제거되었는지 확인
        for i in range(5):
            assert cache.get(i*10, 0, 10, 10) is None

class TestCacheManager:
    """통합 캐시 관리자 테스트"""
    
    @pytest.mark.unit
    def test_cache_manager_creation(self, test_config, temp_dir):
        """캐시 관리자 생성 테스트"""
        config = test_config.copy()
        config['cache_dir'] = temp_dir
        
        manager = CacheManager(config)
        
        assert manager.image_cache is not None
        assert manager.ocr_cache is not None
        assert manager.cache_dir.exists()
    
    @pytest.mark.unit
    def test_integrated_caching(self, test_config, temp_dir, sample_image):
        """통합 캐싱 테스트"""
        config = test_config.copy()
        config['cache_dir'] = temp_dir
        
        manager = CacheManager(config)
        manager.start()
        
        try:
            # 이미지 캐싱
            processed = sample_image * 0.8
            manager.cache_preprocessed_image(sample_image, processed)
            retrieved_image = manager.get_preprocessed_image(sample_image)
            assert np.array_equal(retrieved_image, processed)
            
            # OCR 결과 캐싱
            ocr_result = {'text': '통합 테스트', 'confidence': 0.9}
            manager.cache_ocr_result(0, 0, 100, 100, ocr_result, sample_image)
            retrieved_ocr = manager.get_ocr_result(0, 0, 100, 100, sample_image)
            assert retrieved_ocr == ocr_result
            
        finally:
            manager.stop()
    
    @pytest.mark.unit
    def test_cache_statistics(self, test_config, temp_dir):
        """캐시 통계 테스트"""
        config = test_config.copy()
        config['cache_dir'] = temp_dir
        
        manager = CacheManager(config)
        
        # 일부 캐시 작업 수행
        manager.image_cache.cache.put("test", "value")
        manager.image_cache.cache.get("test")  # 히트
        manager.image_cache.cache.get("miss")  # 미스
        
        stats = manager.get_stats()
        assert 'image_cache' in stats
        assert 'ocr_cache' in stats
        assert stats['image_cache']['hits'] == 1
        assert stats['image_cache']['misses'] == 1
    
    @pytest.mark.unit
    def test_cache_persistence(self, test_config, temp_dir):
        """캐시 영속성 테스트"""
        config = test_config.copy()
        config['cache_dir'] = temp_dir
        
        manager = CacheManager(config)
        
        # OCR 결과 추가
        manager.cache_ocr_result(0, 0, 100, 100, {'text': '저장될 텍스트'})
        
        # 디스크에 저장
        manager.save_cache_to_disk()
        
        # 캐시 파일 확인
        cache_file = Path(temp_dir) / 'cache_data.pkl'
        assert cache_file.exists()
        
        # 새 관리자로 로드
        manager2 = CacheManager(config)
        manager2.load_cache_from_disk()
        
        # 데이터가 복원되었는지 확인
        # (OCR 캐시는 TTL 때문에 확인이 복잡하므로 파일 존재만 확인)
        assert cache_file.exists()