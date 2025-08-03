"""
GridManager 단위 테스트
"""
import pytest
import time
from core.grid_manager import GridManager, GridCell, CellStatus
from core.config_manager import ConfigManager

class TestGridCell:
    """GridCell 테스트"""
    
    @pytest.mark.unit
    def test_cell_creation(self):
        """셀 생성 테스트"""
        cell = GridCell(
            id="M0_R0_C0",
            bounds=(0, 0, 100, 100),
            ocr_area=(10, 10, 80, 80),
            monitor_index=0
        )
        
        assert cell.id == "M0_R0_C0"
        assert cell.monitor_index == 0
        # row, col은 dataclass에 없음
        assert cell.bounds == (0, 0, 100, 100)
        assert cell.status == CellStatus.IDLE
    
    @pytest.mark.unit
    def test_cell_trigger(self):
        """셀 트리거 테스트"""
        cell = GridCell(
            id="test",
            bounds=(0, 0, 100, 100),
            ocr_area=(0, 0, 100, 100)
        )
        
        # 트리거 가능 상태
        assert cell.can_be_triggered() is True
        
        # 트리거 설정
        cell.set_triggered("테스트 텍스트", (50, 50))
        assert cell.status == CellStatus.TRIGGERED
        assert cell.detected_text == "테스트 텍스트"
        assert cell.detected_text_position == (50, 50)
        assert cell.last_triggered_time > 0
    
    @pytest.mark.unit
    def test_cell_cooldown(self):
        """셀 쿨다운 테스트"""
        cell = GridCell(
            id="test",
            bounds=(0, 0, 100, 100),
            ocr_area=(0, 0, 100, 100)
        )
        
        # 쿨다운 설정
        cell.set_cooldown(0.1)  # 0.1초 쿨다운
        assert cell.status == CellStatus.COOLDOWN
        assert cell.can_be_triggered() is False
        
        # 쿨다운 중에는 트리거 불가
        cell.set_triggered("텍스트", (0, 0))
        assert cell.status == CellStatus.COOLDOWN  # 상태 변경 안됨
        
        # 쿨다운 후
        time.sleep(0.2)
        cell.update_cooldown()
        assert cell.status == CellStatus.IDLE
        assert cell.can_be_triggered() is True
    
    @pytest.mark.unit
    def test_cell_reset(self):
        """셀 리셋 테스트"""
        cell = GridCell(
            id="test",
            bounds=(0, 0, 100, 100),
            ocr_area=(0, 0, 100, 100)
        )
        
        # 상태 설정
        cell.set_triggered("텍스트", (50, 50))
        cell.set_cooldown(5.0)
        
        # 리셋
        cell.reset()
        assert cell.status == CellStatus.IDLE
        assert cell.detected_text == ""
        assert cell.cooldown_remaining == 0

class TestGridManager:
    """GridManager 테스트"""
    
    @pytest.mark.unit
    def test_grid_creation(self, mock_config_file, mock_monitors):
        """그리드 생성 테스트"""
        config = ConfigManager(mock_config_file)
        manager = GridManager(config)
        
        # 15개 셀 x 2개 모니터 = 30개
        assert len(manager.cells) == 30
        assert manager.cells_per_monitor == 15
    
    @pytest.mark.unit
    def test_cell_distribution(self, mock_config_file, mock_monitors):
        """셀 분포 테스트"""
        config = ConfigManager(mock_config_file)
        manager = GridManager(config)
        
        # 모니터별 셀 개수 확인
        monitor_0_cells = [c for c in manager.cells if c.monitor_index == 0]
        monitor_1_cells = [c for c in manager.cells if c.monitor_index == 1]
        
        assert len(monitor_0_cells) == 15
        assert len(monitor_1_cells) == 15
    
    @pytest.mark.unit
    def test_update_cooldowns(self, mock_config_file, mock_monitors):
        """쿨다운 업데이트 테스트"""
        config = ConfigManager(mock_config_file)
        manager = GridManager(config)
        
        # 첫 번째 셀에 쿨다운 설정
        manager.cells[0].set_cooldown(0.1)
        
        # 업데이트 전
        assert manager.cells[0].status == CellStatus.COOLDOWN
        
        # 쿨다운 후 업데이트
        time.sleep(0.2)
        manager.update_cell_cooldowns()
        assert manager.cells[0].status == CellStatus.IDLE
    
    @pytest.mark.unit
    def test_get_cells_for_cycle(self, mock_config_file, mock_monitors):
        """사이클용 셀 선택 테스트"""
        config = ConfigManager(mock_config_file)
        manager = GridManager(config)
        
        # 일부 셀에 쿨다운 설정
        for i in range(5):
            manager.cells[i].set_cooldown(5.0)
        
        # 활성 셀만 반환되는지 확인
        active_cells = manager.get_cells_for_cycle()
        assert len(active_cells) <= 15  # 배치 크기 제한
        assert all(cell.can_be_triggered() for cell in active_cells)
    
    @pytest.mark.unit
    def test_reset_all_cells(self, mock_config_file, mock_monitors):
        """모든 셀 리셋 테스트"""
        config = ConfigManager(mock_config_file)
        manager = GridManager(config)
        
        # 여러 셀 상태 변경
        for i in range(10):
            if i % 2 == 0:
                manager.cells[i].set_triggered("텍스트", (0, 0))
            else:
                manager.cells[i].set_cooldown(5.0)
        
        # 전체 리셋
        manager.reset_all_cells()
        
        # 모든 셀이 IDLE 상태인지 확인
        assert all(cell.status == CellStatus.IDLE for cell in manager.cells)
    
    @pytest.mark.unit
    def test_get_statistics(self, mock_config_file, mock_monitors):
        """통계 테스트"""
        config = ConfigManager(mock_config_file)
        manager = GridManager(config)
        
        # 상태 설정
        manager.cells[0].set_triggered("텍스트", (0, 0))
        manager.cells[1].set_cooldown(5.0)
        
        stats = manager.get_statistics()
        assert stats['total_cells'] == 30
        assert stats['idle_cells'] == 28
        assert stats['triggered_cells'] == 1
        assert stats['cooldown_cells'] == 1
    
    @pytest.mark.unit
    def test_refresh_grid(self, mock_config_file, mock_monitors):
        """그리드 새로고침 테스트"""
        config = ConfigManager(mock_config_file)
        manager = GridManager(config)
        
        original_cell_count = len(manager.cells)
        
        # 설정 변경
        config._config['grid_rows'] = 4
        config._config['grid_cols'] = 5
        
        # 그리드 새로고침
        manager.refresh_grid()
        
        # 셀 개수가 변경되었는지 확인 (4*5*2 = 40)
        assert len(manager.cells) == 40
        assert len(manager.cells) != original_cell_count