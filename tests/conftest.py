"""
pytest 공통 fixture 및 설정
"""
import pytest
import sys
import os
import tempfile
import shutil
from pathlib import Path

# src 디렉토리를 Python 경로에 추가
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

# 테스트용 설정
TEST_CONFIG = {
    "grid_rows": 3,
    "grid_cols": 5,
    "ocr_interval_sec": 0.5,
    "cooldown_sec": 5,
    "trigger_patterns": ["들어왔습니다", "입장했습니다"],
    "max_concurrent_ocr": 3,
    "use_gpu": False,
    "cache_dir": "./test_cache",
    "image_cache_size_mb": 100,
    "ocr_cache_ttl": 30
}

@pytest.fixture
def test_config():
    """테스트용 설정 반환"""
    return TEST_CONFIG.copy()

@pytest.fixture
def temp_dir():
    """임시 디렉토리 생성 및 정리"""
    temp_path = tempfile.mkdtemp()
    yield temp_path
    # 테스트 후 정리
    shutil.rmtree(temp_path, ignore_errors=True)

@pytest.fixture
def mock_config_file(temp_dir):
    """테스트용 config.json 파일 생성"""
    import json
    config_path = Path(temp_dir) / "config.json"
    with open(config_path, 'w', encoding='utf-8') as f:
        json.dump(TEST_CONFIG, f, indent=2)
    return str(config_path)

@pytest.fixture
def sample_image():
    """테스트용 샘플 이미지 생성"""
    import numpy as np
    # 100x50 크기의 흰색 배경 이미지
    image = np.ones((50, 100, 3), dtype=np.uint8) * 255
    return image

@pytest.fixture
def sample_text_image():
    """텍스트가 포함된 테스트 이미지 생성"""
    import numpy as np
    import cv2
    
    # 200x100 크기의 흰색 배경
    image = np.ones((100, 200, 3), dtype=np.uint8) * 255
    
    # 검은색 텍스트 추가 (실제로는 OCR 테스트용 이미지 필요)
    cv2.putText(image, "Test", (50, 50), 
                cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 2)
    
    return image

@pytest.fixture
def mock_monitors(monkeypatch):
    """모니터 정보 모킹"""
    class MockMonitor:
        def __init__(self, x, y, width, height):
            self.x = x
            self.y = y
            self.width = width
            self.height = height
    
    mock_monitors_list = [
        MockMonitor(0, 0, 1920, 1080),
        MockMonitor(1920, 0, 1920, 1080)
    ]
    
    def mock_get_monitors():
        return mock_monitors_list
    
    monkeypatch.setattr("screeninfo.get_monitors", mock_get_monitors)
    return mock_monitors_list

@pytest.fixture(autouse=True)
def suppress_gui(monkeypatch):
    """GUI 관련 함수 모킹 (CI/CD 환경용)"""
    # PyQt5 관련 모킹은 필요한 경우에만
    pass

@pytest.fixture
def performance_data():
    """테스트용 성능 데이터"""
    return {
        'cpu_percent': 45.5,
        'memory_mb': 512.3,
        'ocr_latency_ms': 25.5,
        'detection_count': 10,
        'automation_count': 8
    }