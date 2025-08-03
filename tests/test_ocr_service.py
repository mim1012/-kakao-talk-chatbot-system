"""
OCR 서비스 단위 테스트
"""
import pytest
import numpy as np
from unittest.mock import Mock, patch, MagicMock
from ocr.enhanced_ocr_corrector import EnhancedOCRCorrector
from ocr.optimized_ocr_service import OptimizedOCRService, OptimizedOCRResult

class TestEnhancedOCRCorrector:
    """OCR 보정기 테스트"""
    
    @pytest.mark.unit
    @pytest.mark.ocr
    def test_exact_pattern_matching(self):
        """정확한 패턴 매칭 테스트"""
        corrector = EnhancedOCRCorrector()
        
        # 정확한 패턴들
        exact_patterns = [
            "들어왔습니다",
            "입장했습니다",
            "참여했습니다",
            "접속했습니다"
        ]
        
        for pattern in exact_patterns:
            is_trigger, matched = corrector.check_trigger_pattern(pattern)
            assert is_trigger is True
            assert matched == pattern
    
    @pytest.mark.unit
    @pytest.mark.ocr
    def test_ocr_error_correction(self):
        """OCR 오류 보정 테스트"""
        corrector = EnhancedOCRCorrector()
        
        # 일반적인 OCR 오류 패턴들
        error_patterns = [
            ("들머왔습니다", "들어왔습니다"),
            ("둘어왔습니다", "들어왔습니다"),
            ("들어왔시니다", "들어왔습니다"),
            ("들어왔느니다", "들어왔습니다"),
            ("들어왔슴니다", "들어왔습니다"),
            ("틀어왔습니다", "들어왔습니다"),
            ("입정했습니다", "입장했습니다"),
            ("참어했습니다", "참여했습니다")
        ]
        
        for error_text, expected in error_patterns:
            is_trigger, matched = corrector.check_trigger_pattern(error_text)
            assert is_trigger is True
            assert matched == expected
    
    @pytest.mark.unit
    @pytest.mark.ocr
    def test_partial_matching(self):
        """부분 매칭 테스트"""
        corrector = EnhancedOCRCorrector()
        
        # 부분 텍스트
        partial_texts = [
            "님이 들어왔습니다",
            "들어왔습니다!",
            "방에 입장했습니다",
            "채팅방에 참여했습니다"
        ]
        
        for text in partial_texts:
            is_trigger, _ = corrector.check_trigger_pattern(text)
            assert is_trigger is True
    
    @pytest.mark.unit
    @pytest.mark.ocr
    def test_non_trigger_patterns(self):
        """트리거가 아닌 패턴 테스트"""
        corrector = EnhancedOCRCorrector()
        
        non_triggers = [
            "안녕하세요",
            "반갑습니다",
            "감사합니다",
            "잘 부탁드립니다",
            ""
        ]
        
        for text in non_triggers:
            is_trigger, _ = corrector.check_trigger_pattern(text)
            assert is_trigger is False
    
    @pytest.mark.unit
    @pytest.mark.ocr
    def test_fuzzy_matching(self):
        """퍼지 매칭 테스트"""
        corrector = EnhancedOCRCorrector()
        
        # 유사도가 높은 텍스트
        similar_texts = [
            "들어왔습니",  # 마지막 글자 누락
            "들어왔습다",  # 마지막 글자 오류
            "들어습니다",  # 중간 글자 누락
        ]
        
        for text in similar_texts:
            # 임계값을 낮춰서 테스트
            is_match, pattern = corrector.fuzzy_match_patterns(text, threshold=0.7)
            assert is_match is True

class TestOptimizedOCRService:
    """최적화된 OCR 서비스 테스트"""
    
    @pytest.fixture
    def mock_config_manager(self, test_config):
        """모의 ConfigManager"""
        mock = Mock()
        mock._config = test_config
        return mock
    
    @pytest.fixture
    def mock_cache_manager(self):
        """모의 CacheManager"""
        mock = Mock()
        mock.get_preprocessed_image.return_value = None
        mock.get_ocr_result.return_value = None
        return mock
    
    @pytest.fixture
    def ocr_service(self, mock_config_manager, mock_cache_manager):
        """테스트용 OCR 서비스"""
        with patch('ocr.optimized_ocr_service.PaddleOCR'):
            service = OptimizedOCRService(
                mock_config_manager,
                mock_cache_manager
            )
            return service
    
    @pytest.mark.unit
    @pytest.mark.ocr
    def test_ocr_result_creation(self):
        """OCR 결과 객체 생성 테스트"""
        result = OptimizedOCRResult(
            text="테스트 텍스트",
            confidence=0.95,
            position=(100, 200),
            processing_time_ms=25.5,
            cache_hit=False
        )
        
        assert result.text == "테스트 텍스트"
        assert result.confidence == 0.95
        assert result.position == (100, 200)
        assert result.processing_time_ms == 25.5
        assert result.cache_hit is False
        assert result.timestamp > 0
    
    @pytest.mark.unit
    @pytest.mark.ocr
    def test_image_preprocessing(self, ocr_service, sample_image):
        """이미지 전처리 테스트"""
        processed = ocr_service.preprocess_image_optimized(sample_image)
        
        # 전처리된 이미지가 반환되는지 확인
        assert processed is not None
        assert isinstance(processed, np.ndarray)
    
    @pytest.mark.unit
    @pytest.mark.ocr
    def test_optimal_scale_calculation(self, ocr_service):
        """최적 스케일 계산 테스트"""
        # 작은 이미지 -> 확대
        assert ocr_service._calculate_optimal_scale(30, 30) == 4.0
        assert ocr_service._calculate_optimal_scale(70, 70) == 2.0
        
        # 보통 이미지 -> 그대로
        assert ocr_service._calculate_optimal_scale(200, 200) == 1.0
        
        # 큰 이미지 -> 축소
        assert ocr_service._calculate_optimal_scale(600, 600) == 0.5
    
    @pytest.mark.unit
    @pytest.mark.ocr
    def test_cache_hit(self, ocr_service, mock_cache_manager, sample_image):
        """캐시 히트 테스트"""
        # 캐시에서 결과 반환하도록 설정
        cached_data = {
            'text': '캐시된 텍스트',
            'confidence': 0.9,
            'position': (0, 0)
        }
        mock_cache_manager.get_ocr_result.return_value = cached_data
        
        # OCR 수행
        result = ocr_service.perform_ocr_cached(
            sample_image,
            region=(0, 0, 100, 100)
        )
        
        assert result.text == '캐시된 텍스트'
        assert result.cache_hit is True
        assert result.processing_time_ms < 1.0  # 캐시 히트는 빠름
    
    @pytest.mark.unit
    @pytest.mark.ocr
    def test_trigger_pattern_check(self, ocr_service):
        """트리거 패턴 확인 테스트"""
        # 트리거 패턴
        assert ocr_service.check_trigger_patterns("들어왔습니다") is True
        assert ocr_service.check_trigger_patterns("입장했습니다") is True
        
        # 트리거가 아닌 패턴
        assert ocr_service.check_trigger_patterns("안녕하세요") is False
        assert ocr_service.check_trigger_patterns("") is False
    
    @pytest.mark.unit
    @pytest.mark.ocr
    @patch('ocr.optimized_ocr_service.ThreadPoolExecutor')
    def test_batch_ocr_processing(self, mock_executor, ocr_service, sample_image):
        """배치 OCR 처리 테스트"""
        # Mock Future 객체
        mock_future = Mock()
        mock_future.result.return_value = OptimizedOCRResult(
            text="배치 텍스트",
            confidence=0.85
        )
        
        # ThreadPoolExecutor mock 설정
        mock_executor_instance = Mock()
        mock_executor_instance.submit.return_value = mock_future
        mock_executor.return_value = mock_executor_instance
        ocr_service.executor = mock_executor_instance
        
        # 배치 처리
        images_with_regions = [
            (sample_image, (0, 0, 100, 100)),
            (sample_image, (100, 0, 100, 100))
        ]
        
        results = ocr_service.perform_batch_ocr(images_with_regions)
        
        assert len(results) == 2
        assert all(isinstance(r, OptimizedOCRResult) for r in results)
    
    @pytest.mark.unit
    @pytest.mark.ocr
    def test_statistics(self, ocr_service):
        """통계 테스트"""
        # 초기 통계
        stats = ocr_service.get_statistics()
        assert stats['total_ocr_count'] == 0
        assert stats['cache_hit_count'] == 0
        
        # OCR 수행 시뮬레이션
        ocr_service.total_ocr_count = 10
        ocr_service.cache_hit_count = 3
        
        stats = ocr_service.get_statistics()
        assert stats['total_ocr_count'] == 10
        assert stats['cache_hit_count'] == 3
        assert stats['cache_hit_rate'] == 30.0
    
    @pytest.mark.unit
    @pytest.mark.ocr
    def test_performance_optimization(self, ocr_service):
        """성능 최적화 설정 테스트"""
        # 높은 CPU 사용률
        perf_data = {'cpu_percent': 85.0, 'avg_ocr_latency': 50}
        ocr_service.optimize_settings(perf_data)
        
        # 설정이 조정되었는지 확인
        assert ocr_service.executor._max_workers < 6
        
        # 높은 레이턴시
        perf_data = {'cpu_percent': 50.0, 'avg_ocr_latency': 150}
        ocr_service.optimize_settings(perf_data)
        
        # 간소화 모드가 활성화되었는지 확인
        assert ocr_service.config._config.get('ocr_preprocess', {}).get('simple_mode', False)