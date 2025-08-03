"""
Test script for the refactored chatbot system.
Validates that all services work correctly and integration is successful.
"""
from __future__ import annotations

import logging
import time
import sys
from typing import Callable
from service_container import ServiceContainer, MonitoringOrchestrator


def setup_logging() -> None:
    """Setup logging configuration for testing."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('test_log.txt', encoding='utf-8')
        ]
    )


def test_service_initialization() -> ServiceContainer | None:
    """Test that all services initialize correctly."""
    print("=== Testing Service Initialization ===")
    
    try:
        container = ServiceContainer()
        
        # Test config manager
        config = container.config_manager
        print(f"✓ ConfigManager: Grid {config.grid_rows}x{config.grid_cols}, "
              f"OCR interval: {config.ocr_interval_sec}s")
        
        # Test OCR service
        ocr_status = container.ocr_service.get_status()
        print(f"✓ OCRService: Available={ocr_status['available']}, "
              f"Engine initialized={ocr_status['engine_initialized']}")
        
        # Test automation service
        auto_status = container.automation_service.get_status()
        print(f"✓ AutomationService: Input manager={auto_status['input_manager']}, "
              f"Clipboard manager={auto_status['clipboard_manager']}")
        
        # Test grid manager
        grid_stats = container.grid_manager.get_statistics()
        print(f"✓ GridManager: {grid_stats['total_cells']} cells, "
              f"{grid_stats['enabled_cells']} enabled, {grid_stats['monitors']} monitors")
        
        return container
        
    except Exception as e:
        print(f"✗ Service initialization failed: {e}")
        return None


def test_configuration_loading(container: ServiceContainer) -> bool:
    """Test configuration loading and validation."""
    print("\n=== Testing Configuration Loading ===")
    
    try:
        config = container.config_manager
        
        # Test basic config values
        assert config.grid_rows > 0, "Grid rows must be positive"
        assert config.grid_cols > 0, "Grid cols must be positive"
        assert config.ocr_interval_sec > 0, "OCR interval must be positive"
        assert len(config.trigger_patterns) > 0, "Must have trigger patterns"
        
        # Test UI constants
        ui_constants = config.ui_constants
        assert ui_constants.ocr_area_y_offset > 0, "OCR area offset must be positive"
        assert ui_constants.ocr_area_height > 0, "OCR area height must be positive"
        
        # Test timing config
        timing = config.timing_config
        assert timing.click_delay >= 0, "Click delay must be non-negative"
        assert timing.paste_delay >= 0, "Paste delay must be non-negative"
        
        print("✓ Configuration validation passed")
        return True
        
    except Exception as e:
        print(f"✗ Configuration validation failed: {e}")
        return False


def test_grid_management(container: ServiceContainer) -> bool:
    """Test grid cell creation and management."""
    print("\n=== Testing Grid Management ===")
    
    try:
        grid_manager = container.grid_manager
        
        # Test cell creation
        cells = grid_manager.get_enabled_cells()
        assert len(cells) > 0, "Must have at least one cell"
        
        # Test cell properties
        first_cell = cells[0]
        assert first_cell.id, "Cell must have an ID"
        assert len(first_cell.bounds) == 4, "Cell bounds must have 4 values"
        assert len(first_cell.ocr_area) == 4, "OCR area must have 4 values"
        
        # Test cell state management
        original_status = first_cell.status
        first_cell.set_triggered("test text", (100, 100))
        assert first_cell.detected_text == "test text", "Detected text not set correctly"
        
        first_cell.set_cooldown(1.0)
        assert first_cell.is_in_cooldown(), "Cell should be in cooldown"
        
        first_cell.set_idle()
        assert not first_cell.is_in_cooldown(), "Cell should not be in cooldown after reset"
        
        # Test cycle selection
        cycle_cells = grid_manager.get_cells_for_cycle()
        assert len(cycle_cells) <= container.config_manager.automation_config.cells_per_cycle, \
            "Cycle cells exceed configured limit"
        
        print(f"✓ Grid management: {len(cells)} cells created and tested")
        return True
        
    except Exception as e:
        print(f"✗ Grid management test failed: {e}")
        return False


def test_ocr_service(container: ServiceContainer) -> bool:
    """Test OCR service functionality."""
    print("\n=== Testing OCR Service ===")
    
    try:
        import numpy as np
        
        ocr_service = container.ocr_service
        
        if not ocr_service.is_available():
            print("⚠ OCR service not available (PaddleOCR not installed), skipping OCR tests")
            return True
        
        # Create a test image (white background with some text-like pattern)
        test_image = np.ones((100, 200, 3), dtype=np.uint8) * 255
        
        # Test image preprocessing
        processed = ocr_service.preprocess_image(test_image)
        assert processed is not None, "Image preprocessing failed"
        assert len(processed.shape) >= 2, "Processed image should be at least 2D"
        
        # Test OCR result structure
        from ocr_service import OCRResult
        result = OCRResult("test text", 0.9, (10, 20))
        assert result.text == "test text", "OCR result text not set correctly"
        assert result.confidence == 0.9, "OCR result confidence not set correctly"
        assert result.position == (10, 20), "OCR result position not set correctly"
        
        # Test trigger pattern checking
        test_result = OCRResult("들어왔습니다", 0.8, (0, 0))
        trigger_matched = ocr_service.check_trigger_patterns(test_result)
        assert trigger_matched, "Trigger pattern should match"
        
        print("✓ OCR service functionality tested")
        return True
        
    except Exception as e:
        print(f"✗ OCR service test failed: {e}")
        return False


def test_automation_service(container: ServiceContainer) -> bool:
    """Test automation service functionality."""
    print("\n=== Testing Automation Service ===")
    
    try:
        automation_service = container.automation_service
        
        # Test input position calculation
        cell_bounds = (100, 100, 200, 150)
        detected_position = (120, 110)
        
        # Test with detected position
        input_pos1 = automation_service.find_input_position(cell_bounds, detected_position)
        assert len(input_pos1) == 2, "Input position should be a tuple of 2 values"
        assert input_pos1[0] > 0 and input_pos1[1] > 0, "Input position should be positive"
        
        # Test with fallback position
        input_pos2 = automation_service.find_input_position(cell_bounds, None)
        assert len(input_pos2) == 2, "Fallback input position should be a tuple of 2 values"
        assert input_pos2 != input_pos1, "Fallback position should be different"
        
        # Test response message generation
        message = automation_service.get_response_message()
        assert message, "Response message should not be empty"
        assert isinstance(message, str), "Response message should be a string"
        
        print("✓ Automation service functionality tested")
        return True
        
    except Exception as e:
        print(f"✗ Automation service test failed: {e}")
        return False


def test_system_integration(container: ServiceContainer) -> bool:
    """Test system integration and orchestration."""
    print("\n=== Testing System Integration ===")
    
    try:
        # Test system status
        status = container.get_system_status()
        assert 'monitoring_active' in status, "System status should include monitoring state"
        assert 'config_manager' in status, "System status should include config info"
        assert 'ocr_service' in status, "System status should include OCR status"
        assert 'automation_service' in status, "System status should include automation status"
        assert 'grid_manager' in status, "System status should include grid stats"
        
        # Test monitoring state changes
        assert not container.is_monitoring_active(), "Monitoring should start as inactive"
        
        success = container.start_monitoring()
        if container.ocr_service.is_available():
            assert success, "Should be able to start monitoring when OCR is available"
            assert container.is_monitoring_active(), "Monitoring should be active after start"
        else:
            assert not success, "Should not be able to start monitoring without OCR"
        
        container.stop_monitoring()
        assert not container.is_monitoring_active(), "Monitoring should be inactive after stop"
        
        # Test configuration refresh
        refresh_success = container.refresh_configuration()
        assert refresh_success, "Configuration refresh should succeed"
        
        print("✓ System integration tested")
        return True
        
    except Exception as e:
        print(f"✗ System integration test failed: {e}")
        return False


def run_performance_test(container: ServiceContainer) -> bool:
    """Run a brief performance test."""
    print("\n=== Performance Test ===")
    
    try:
        import time
        
        # Test grid cycle performance
        start_time = time.time()
        for _ in range(100):
            cells = container.grid_manager.get_cells_for_cycle()
            container.grid_manager.update_cell_cooldowns()
        
        grid_time = time.time() - start_time
        print(f"✓ Grid operations: 100 cycles in {grid_time:.3f}s ({grid_time*10:.1f}ms per cycle)")
        
        # Test configuration access performance
        start_time = time.time()
        config = container.config_manager
        for _ in range(1000):
            _ = config.grid_rows
            _ = config.ocr_interval_sec
            _ = config.timing_config.click_delay
        
        config_time = time.time() - start_time
        print(f"✓ Config access: 1000 calls in {config_time:.3f}s ({config_time:.3f}ms per call)")
        
        return True
        
    except Exception as e:
        print(f"✗ Performance test failed: {e}")
        return False


def main() -> bool:
    """Run all tests."""
    setup_logging()
    
    print("Starting Refactored System Tests")
    print("=" * 50)
    
    # Initialize services
    container = test_service_initialization()
    if not container:
        print("\n❌ Service initialization failed. Cannot continue.")
        return False
    
    # Run tests
    tests = [
        ("Configuration Loading", lambda: test_configuration_loading(container)),
        ("Grid Management", lambda: test_grid_management(container)),
        ("OCR Service", lambda: test_ocr_service(container)),
        ("Automation Service", lambda: test_automation_service(container)),
        ("System Integration", lambda: test_system_integration(container)),
        ("Performance Test", lambda: run_performance_test(container))
    ]
    
    passed: int = 0
    total: int = len(tests)
    
    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
        except Exception as e:
            print(f"✗ {test_name} test failed with exception: {e}")
    
    # Cleanup
    container.cleanup()
    
    # Summary
    print("\n" + "=" * 50)
    print(f"Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! The refactored system is working correctly.")
        return True
    else:
        print(f"⚠ {total - passed} test(s) failed. Please review the issues above.")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)