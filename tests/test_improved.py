"""
개선된 테스트 - 실제 구현에 맞춤
"""
import pytest
import time
import json
from pathlib import Path

# 간단한 테스트들만
class TestImproved:
    """개선된 단위 테스트"""
    
    @pytest.mark.unit
    def test_grid_cell_dataclass(self):
        """GridCell dataclass 테스트"""
        from core.grid_manager import GridCell, CellStatus
        
        # 기본 생성
        cell = GridCell(
            id="test_cell",
            bounds=(0, 0, 100, 100),
            ocr_area=(10, 10, 80, 80)
        )
        
        assert cell.id == "test_cell"
        assert cell.status == CellStatus.IDLE
        assert cell.enabled is True
        assert cell.last_triggered == 0.0
        assert cell.cooldown_until == 0.0
        assert cell.monitor_index == 0
        
    @pytest.mark.unit
    def test_grid_cell_methods(self):
        """GridCell 메서드 테스트"""
        from core.grid_manager import GridCell, CellStatus
        
        cell = GridCell(
            id="test",
            bounds=(0, 0, 100, 100),
            ocr_area=(0, 0, 100, 100)
        )
        
        # 트리거 테스트
        cell.set_triggered("테스트 텍스트", (50, 50))
        assert cell.status == CellStatus.TRIGGERED
        assert cell.detected_text == "테스트 텍스트"
        assert cell.detected_text_position == (50, 50)
        assert cell.last_triggered > 0
        assert cell.trigger_count == 1
        
        # 쿨다운 테스트
        cell.set_cooldown(5.0)
        assert cell.status == CellStatus.COOLDOWN
        assert cell.cooldown_until > time.time()
        
    @pytest.mark.unit
    def test_ocr_corrector_patterns(self):
        """OCR 보정 패턴 테스트"""
        from ocr.enhanced_ocr_corrector import EnhancedOCRCorrector
        
        corrector = EnhancedOCRCorrector()
        
        # 다양한 오류 패턴 테스트
        test_cases = [
            ("들어왔습니다", True, "들어왔습니다"),
            ("들머왔습니다", True, "들어왔습니다"),
            ("들어왔슴니다", True, "들어왔습니다"),
            ("들어왔ㅅ니다", True, "들어왔습니다"),
            ("입장했습니다", True, "입장했습니다"),
            ("참여했습니다", True, "참여했습니다"),
            ("안녕하세요", False, ""),
            ("", False, ""),
        ]
        
        for text, expected_match, expected_pattern in test_cases:
            is_match, pattern = corrector.check_trigger_pattern(text)
            assert is_match == expected_match
            if expected_match:
                assert pattern == expected_pattern
    
    @pytest.mark.unit
    def test_simple_cache_operations(self):
        """간단한 캐시 연산 테스트"""
        from core.simple_cache import SimpleLRUCache
        
        cache = SimpleLRUCache(max_size=3)
        
        # 기본 동작
        cache.put("k1", "v1")
        cache.put("k2", "v2")
        assert cache.get("k1") == "v1"
        assert cache.get("k2") == "v2"
        assert cache.get("k3") is None
        
        # LRU 제거
        cache.put("k3", "v3")
        cache.get("k1")  # k1을 최근 사용으로
        cache.put("k4", "v4")  # k2가 제거되어야 함
        
        assert cache.get("k1") == "v1"
        assert cache.get("k2") is None
        assert cache.get("k3") == "v3"
        assert cache.get("k4") == "v4"
        
        # 통계
        stats = cache.get_stats()
        assert stats['hits'] > 0
        assert stats['misses'] > 0
        assert stats['size'] == 3
        
    @pytest.mark.unit
    def test_config_loading_basics(self):
        """설정 로드 기본 테스트"""
        from core.config_manager import ConfigManager
        
        # 임시 설정 파일
        config_data = {
            "grid_rows": 3,
            "grid_cols": 5,
            "ocr_interval_sec": 0.5,
            "cooldown_sec": 5,
            "trigger_patterns": ["들어왔습니다"]
        }
        
        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(config_data, f)
            temp_path = f.name
        
        try:
            # 설정 로드
            manager = ConfigManager(temp_path)
            assert manager.grid_rows == 3
            assert manager.grid_cols == 5
            assert manager.ocr_interval_sec == 0.5
            assert manager.cooldown_sec == 5
            assert "들어왔습니다" in manager.trigger_patterns
            
        finally:
            Path(temp_path).unlink()
    
    @pytest.mark.unit
    def test_cell_status_enum(self):
        """CellStatus enum 테스트"""
        from core.grid_manager import CellStatus
        
        # Enum 값들
        assert CellStatus.IDLE == "idle"
        assert CellStatus.TRIGGERED == "triggered"
        assert CellStatus.COOLDOWN == "cooldown"
        assert CellStatus.DISABLED == "disabled"
        
        # String 변환
        assert str(CellStatus.IDLE) == "idle"
        
    @pytest.mark.unit
    def test_ocr_corrector_normalization(self):
        """텍스트 정규화 테스트"""
        from ocr.enhanced_ocr_corrector import EnhancedOCRCorrector
        
        corrector = EnhancedOCRCorrector()
        
        # 정규화 테스트
        assert corrector.normalize_text("들어 왔습니다") == "들어왔습니다"
        assert corrector.normalize_text("들어왔습니다!") == "들어왔습니다"
        assert corrector.normalize_text("  들어왔습니다  ") == "들어왔습니다"
        assert corrector.normalize_text("") == ""