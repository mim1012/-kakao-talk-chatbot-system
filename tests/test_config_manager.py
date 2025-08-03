"""
ConfigManager 단위 테스트
"""
import pytest
import json
from pathlib import Path
from core.config_manager import ConfigManager

class TestConfigManager:
    """ConfigManager 테스트 클래스"""
    
    @pytest.mark.unit
    def test_load_valid_config(self, mock_config_file):
        """유효한 설정 파일 로드 테스트"""
        manager = ConfigManager(mock_config_file)
        
        assert manager.grid_rows == 3
        assert manager.grid_cols == 5
        assert manager.ocr_interval_sec == 0.5
        assert manager.cooldown_sec == 5
        assert "들어왔습니다" in manager.trigger_patterns
    
    @pytest.mark.unit
    def test_load_missing_config(self, temp_dir):
        """존재하지 않는 설정 파일 처리 테스트"""
        missing_path = Path(temp_dir) / "missing.json"
        
        with pytest.raises(FileNotFoundError):
            ConfigManager(str(missing_path))
    
    @pytest.mark.unit
    def test_invalid_json_config(self, temp_dir):
        """잘못된 JSON 형식 처리 테스트"""
        invalid_path = Path(temp_dir) / "invalid.json"
        with open(invalid_path, 'w') as f:
            f.write("{invalid json}")
        
        with pytest.raises(json.JSONDecodeError):
            ConfigManager(str(invalid_path))
    
    @pytest.mark.unit
    def test_config_validation(self, temp_dir):
        """설정 값 검증 테스트"""
        # 잘못된 값이 있는 설정
        invalid_config = {
            "grid_rows": -1,  # 음수 값
            "grid_cols": 0,   # 0 값
            "ocr_interval_sec": "not_a_number",  # 잘못된 타입
            "cooldown_sec": 5
        }
        
        config_path = Path(temp_dir) / "invalid_values.json"
        with open(config_path, 'w') as f:
            json.dump(invalid_config, f)
        
        # ConfigManager가 기본값으로 대체하는지 확인
        manager = ConfigManager(str(config_path))
        assert manager.grid_rows > 0  # 기본값으로 대체됨
        assert manager.grid_cols > 0
    
    @pytest.mark.unit
    def test_chatroom_configs(self, mock_config_file):
        """채팅방 설정 로드 테스트"""
        manager = ConfigManager(mock_config_file)
        
        # chatroom_configs가 없어도 에러 없이 처리
        assert hasattr(manager, 'chatroom_configs')
    
    @pytest.mark.unit
    def test_ocr_preprocess_config(self, mock_config_file):
        """OCR 전처리 설정 테스트"""
        manager = ConfigManager(mock_config_file)
        
        assert hasattr(manager, 'ocr_preprocess')
        # 기본값 확인
        assert manager.ocr_preprocess.get('scale', 1.0) > 0
    
    @pytest.mark.unit
    def test_automation_config(self, temp_dir):
        """자동화 설정 테스트"""
        config = {
            "grid_rows": 3,
            "grid_cols": 5,
            "automation_config": {
                "max_retries": 5,
                "clipboard_retry_count": 3,
                "max_concurrent_ocr": 6
            }
        }
        
        config_path = Path(temp_dir) / "automation.json"
        with open(config_path, 'w') as f:
            json.dump(config, f)
        
        manager = ConfigManager(str(config_path))
        assert manager.automation_config['max_retries'] == 5
        assert manager.automation_config['max_concurrent_ocr'] == 6
    
    @pytest.mark.unit
    def test_reload_config(self, mock_config_file):
        """설정 재로드 테스트"""
        manager = ConfigManager(mock_config_file)
        original_rows = manager.grid_rows
        
        # 파일 수정
        with open(mock_config_file, 'r') as f:
            config = json.load(f)
        config['grid_rows'] = 10
        with open(mock_config_file, 'w') as f:
            json.dump(config, f)
        
        # 재로드
        manager.load_config()
        assert manager.grid_rows == 10
        assert manager.grid_rows != original_rows