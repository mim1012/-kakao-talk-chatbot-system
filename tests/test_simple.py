"""
간단한 테스트 - numpy 없이
"""
import pytest
import time
from core.config_manager import ConfigManager
from core.grid_manager import GridCell, CellStatus

class TestSimple:
    """간단한 단위 테스트"""
    
    @pytest.mark.unit
    def test_grid_cell_basic(self):
        """GridCell 기본 테스트"""
        cell = GridCell(
            id="test_cell",
            bounds=(0, 0, 100, 100),
            ocr_area=(10, 10, 80, 80),
            monitor_index=0
        )
        
        assert cell.id == "test_cell"
        assert cell.status == CellStatus.IDLE
        assert cell.bounds == (0, 0, 100, 100)
        assert cell.ocr_area == (10, 10, 80, 80)
        assert cell.monitor_index == 0
        assert cell.enabled is True
        
    @pytest.mark.unit
    def test_grid_cell_cooldown(self):
        """GridCell 쿨다운 테스트"""
        cell = GridCell(
            id="test",
            bounds=(0, 0, 100, 100),
            ocr_area=(0, 0, 100, 100)
        )
        
        # 쿨다운 설정
        cell.set_cooldown(5.0)
        assert cell.status == CellStatus.COOLDOWN
        assert cell.cooldown_until > time.time()
        
    @pytest.mark.unit
    def test_ocr_corrector_basic(self):
        """OCR 보정기 기본 테스트"""
        from ocr.enhanced_ocr_corrector import EnhancedOCRCorrector
        
        corrector = EnhancedOCRCorrector()
        
        # 정확한 패턴
        is_trigger, matched = corrector.check_trigger_pattern("들어왔습니다")
        assert is_trigger is True
        assert matched == "들어왔습니다"
        
        # 오류 패턴
        is_trigger, matched = corrector.check_trigger_pattern("들머왔습니다")
        assert is_trigger is True
        assert matched == "들어왔습니다"
        
        # 트리거 아님
        is_trigger, _ = corrector.check_trigger_pattern("안녕하세요")
        assert is_trigger is False
        
    @pytest.mark.unit
    def test_cache_basic(self):
        """캐시 기본 테스트"""
        from core.simple_cache import SimpleLRUCache
        
        cache = SimpleLRUCache(max_size=3)
        
        # 추가
        cache.put("key1", "value1")
        cache.put("key2", "value2")
        
        # 가져오기
        assert cache.get("key1") == "value1"
        assert cache.get("key2") == "value2"
        assert cache.get("key3") is None
        
        # 통계
        stats = cache.get_stats()
        assert stats['hits'] == 2
        assert stats['misses'] == 1