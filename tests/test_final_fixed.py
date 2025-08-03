"""
최종 수정된 통합 테스트
"""
import pytest
import json
import tempfile
import time
from pathlib import Path
from core.config_manager import ConfigManager, ChatroomConfig, AutomationConfig, TimingConfig
from core.grid_manager import GridCell, CellStatus, GridManager
from ocr.enhanced_ocr_corrector import EnhancedOCRCorrector
from core.simple_cache import SimpleLRUCache

class TestConfigManagerFixed:
    """ConfigManager 테스트 - 실제 dataclass 구조에 맞춤"""
    
    @pytest.mark.unit
    def test_load_valid_config(self):
        """유효한 설정 파일 로드 테스트"""
        config_data = {
            "grid_rows": 3,
            "grid_cols": 5,
            "ocr_interval_sec": 1.0,
            "cooldown_sec": 5,
            "trigger_patterns": ["들어왔습니다", "입장했습니다"]
        }
        
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "config.json"
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, ensure_ascii=False)
            
            manager = ConfigManager(str(config_path))
            
            assert manager.grid_rows == 3
            assert manager.grid_cols == 5
            assert manager.ocr_interval_sec == 1.0
            assert manager.cooldown_sec == 5
            assert len(manager.trigger_patterns) == 2
    
    @pytest.mark.unit
    def test_chatroom_configs_correct(self):
        """채팅방 설정 테스트 - 올바른 구조"""
        config_data = {
            "chatroom_configs": [
                {
                    "x": 100,
                    "y": 200,
                    "width": 400,
                    "height": 600,
                    "input_x": 150,
                    "input_y": 500,
                    "ocr_x": 100,
                    "ocr_y": 400,
                    "ocr_w": 300,
                    "ocr_h": 50
                }
            ]
        }
        
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "config.json"
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, ensure_ascii=False)
            
            manager = ConfigManager(str(config_path))
            
            assert len(manager.chatroom_configs) == 1
            assert manager.chatroom_configs[0].x == 100
            assert manager.chatroom_configs[0].input_x == 150
    
    @pytest.mark.unit
    def test_automation_config_correct(self):
        """자동화 설정 테스트 - 올바른 구조"""
        config_data = {
            "automation_config": {
                "max_retries": 5,
                "clipboard_retry_count": 10,
                "cells_per_cycle": 15
            }
        }
        
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "automation.json"
            with open(config_path, 'w') as f:
                json.dump(config_data, f)
            
            manager = ConfigManager(str(config_path))
            
            # AutomationConfig dataclass fields
            assert manager.automation_config.max_retries == 5
            assert manager.automation_config.clipboard_retry_count == 10
            assert manager.automation_config.cells_per_cycle == 15
    
    @pytest.mark.unit
    def test_timing_config_correct(self):
        """타이밍 설정 테스트 - 올바른 구조"""
        manager = ConfigManager("non_existent.json")
        
        # 실제 TimingConfig dataclass fields
        assert hasattr(manager.timing_config, 'click_delay')
        assert hasattr(manager.timing_config, 'clipboard_delay')
        assert hasattr(manager.timing_config, 'paste_delay')
        assert manager.timing_config.click_delay > 0
        assert manager.timing_config.clipboard_delay > 0

class TestGridCellFixed:
    """GridCell 테스트"""
    
    @pytest.mark.unit
    def test_cell_creation(self):
        """셀 생성 테스트"""
        cell = GridCell(
            id="test_cell",
            bounds=(0, 0, 100, 100),
            ocr_area=(10, 10, 80, 80),
            monitor_index=0
        )
        
        assert cell.id == "test_cell"
        assert cell.status == CellStatus.IDLE
        assert cell.bounds == (0, 0, 100, 100)
        assert cell.enabled is True
    
    @pytest.mark.unit
    def test_cell_trigger(self):
        """셀 트리거 테스트"""
        cell = GridCell(
            id="test",
            bounds=(0, 0, 100, 100),
            ocr_area=(0, 0, 100, 100)
        )
        
        # 트리거 설정
        cell.set_triggered("테스트 텍스트", (50, 50))
        assert cell.status == CellStatus.TRIGGERED
        assert cell.detected_text == "테스트 텍스트"
        assert cell.last_triggered > 0
    
    @pytest.mark.unit
    def test_cell_cooldown(self):
        """셀 쿨다운 테스트"""
        cell = GridCell(
            id="test",
            bounds=(0, 0, 100, 100),
            ocr_area=(0, 0, 100, 100)
        )
        
        # 쿨다운 설정
        cell.set_cooldown(0.1)
        assert cell.status == CellStatus.COOLDOWN
        assert cell.can_be_triggered() is False
        
        # 쿨다운 후
        time.sleep(0.2)
        assert cell.is_in_cooldown() is False
        assert cell.status == CellStatus.IDLE

class TestOCRCorrector:
    """OCR 보정기 테스트"""
    
    @pytest.mark.unit
    def test_ocr_patterns(self):
        """OCR 패턴 매칭 테스트"""
        corrector = EnhancedOCRCorrector()
        
        # 정확한 패턴
        is_trigger, matched = corrector.check_trigger_pattern("들어왔습니다")
        assert is_trigger is True
        assert matched == "들어왔습니다"
        
        # 오류 패턴
        is_trigger, matched = corrector.check_trigger_pattern("들머왔습니다")
        assert is_trigger is True
        assert matched == "들어왔습니다"
    
    @pytest.mark.unit
    def test_text_normalization(self):
        """텍스트 정규화 테스트"""
        corrector = EnhancedOCRCorrector()
        
        assert corrector.normalize_text("들어 왔습니다") == "들어왔습니다"
        assert corrector.normalize_text("  들어왔습니다  ") == "들어왔습니다"

class TestSimpleCache:
    """간단한 캐시 테스트"""
    
    @pytest.mark.unit
    def test_cache_operations(self):
        """캐시 기본 동작 테스트"""
        cache = SimpleLRUCache(max_size=3)
        
        # 추가 및 조회
        cache.put("k1", "v1")
        cache.put("k2", "v2")
        assert cache.get("k1") == "v1"
        assert cache.get("k2") == "v2"
        
        # LRU 동작
        cache.put("k3", "v3")
        cache.get("k1")  # k1 최근 사용
        cache.put("k4", "v4")  # k2 제거됨
        
        assert cache.get("k1") == "v1"
        assert cache.get("k2") is None
        assert cache.get("k3") == "v3"
        assert cache.get("k4") == "v4"