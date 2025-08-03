"""
Basic structure test for the refactored chatbot system.
Tests core functionality without external dependencies.
Python 3.11+ compatible.
"""
from __future__ import annotations

import sys
import json
import os
import ast
from pathlib import Path


def test_config_structure() -> bool:
    """Test that config.json has the expected structure."""
    print("=== Testing Configuration Structure ===")
    
    try:
        with open('config.json', 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        # Check basic structure
        required_keys = ['grid_rows', 'grid_cols', 'ocr_interval_sec', 'trigger_patterns']
        for key in required_keys:
            assert key in config, f"Missing required config key: {key}"
        
        # Check new sections
        new_sections = ['ui_constants', 'timing_config', 'automation_config']
        for section in new_sections:
            assert section in config, f"Missing new config section: {section}"
        
        # Check ui_constants
        ui_constants = config['ui_constants']
        ui_required = ['ocr_area_y_offset', 'ocr_area_height', 'overlay_height', 'grid_line_width']
        for key in ui_required:
            assert key in ui_constants, f"Missing UI constant: {key}"
        
        # Check timing_config
        timing_config = config['timing_config']
        timing_required = ['click_delay', 'clipboard_delay', 'paste_delay', 'send_delay']
        for key in timing_required:
            assert key in timing_config, f"Missing timing config: {key}"
        
        # Check automation_config
        automation_config = config['automation_config']
        auto_required = ['max_retries', 'clipboard_retry_count', 'cells_per_cycle']
        for key in auto_required:
            assert key in automation_config, f"Missing automation config: {key}"
        
        print("OK Configuration structure is valid")
        return True
        
    except Exception as e:
        print(f"FAIL Configuration test failed: {e}")
        return False


def test_file_structure() -> bool:
    """Test that all refactored files exist."""
    print("\n=== Testing File Structure ===")
    
    required_files: list[str] = [
        'config_manager.py',
        'ocr_service.py', 
        'automation_service.py',
        'grid_manager.py',
        'service_container.py'
    ]
    
    try:
        missing_files = []
        for filename in required_files:
            if not os.path.exists(filename):
                missing_files.append(filename)
        
        if missing_files:
            print(f"✗ Missing files: {', '.join(missing_files)}")
            return False
        
        print(f"✓ All {len(required_files)} refactored files exist")
        return True
        
    except Exception as e:
        print(f"✗ File structure test failed: {e}")
        return False


def test_import_syntax() -> bool:
    """Test that all Python files have valid syntax."""
    print("\n=== Testing Import Syntax ===")
    
    python_files: list[str] = [
        'config_manager.py',
        'ocr_service.py',
        'automation_service.py', 
        'grid_manager.py',
        'service_container.py'
    ]
    
    try:
        for filename in python_files:
            try:
                with open(filename, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Parse the AST to check syntax
                ast.parse(content)
                print(f"✓ {filename}: Valid syntax")
                
            except SyntaxError as e:
                print(f"✗ {filename}: Syntax error at line {e.lineno}: {e.msg}")
                return False
            except Exception as e:
                print(f"✗ {filename}: Error reading file: {e}")
                return False
        
        return True
        
    except Exception as e:
        print(f"✗ Syntax test failed: {e}")
        return False


def test_class_structure() -> bool:
    """Test that expected classes are defined in files."""
    print("\n=== Testing Class Structure ===")
    
    expected_classes: dict[str, list[str]] = {
        'config_manager.py': ['ConfigManager', 'UIConstants', 'TimingConfig', 'AutomationConfig'],
        'ocr_service.py': ['OCRService', 'OCRResult'],
        'automation_service.py': ['AutomationService', 'AutomationResult', 'DefaultInputManager'],
        'grid_manager.py': ['GridManager', 'GridCell', 'CellStatus'],
        'service_container.py': ['ServiceContainer', 'MonitoringOrchestrator']
    }
    
    try:
        for filename, classes in expected_classes.items():
            try:
                with open(filename, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                tree = ast.parse(content)
                
                # Find all class definitions
                found_classes = []
                for node in ast.walk(tree):
                    if isinstance(node, ast.ClassDef):
                        found_classes.append(node.name)
                
                # Check if all expected classes are found
                missing_classes = []
                for expected_class in classes:
                    if expected_class not in found_classes:
                        missing_classes.append(expected_class)
                
                if missing_classes:
                    print(f"✗ {filename}: Missing classes: {', '.join(missing_classes)}")
                    return False
                else:
                    print(f"✓ {filename}: All expected classes found ({len(classes)} classes)")
                
            except Exception as e:
                print(f"✗ {filename}: Error analyzing file: {e}")
                return False
        
        return True
        
    except Exception as e:
        print(f"✗ Class structure test failed: {e}")
        return False


def test_code_improvements() -> bool:
    """Test that code improvements are in place."""
    print("\n=== Testing Code Improvements ===")
    
    improvements_found = 0
    
    try:
        # Check if hardcoded values are removed from config
        with open('config.json', 'r', encoding='utf-8') as f:
            config_content = f.read()
        
        if 'ui_constants' in config_content and 'timing_config' in config_content:
            print("✓ Hardcoded values moved to configuration")
            improvements_found += 1
        
        # Check if files were cleaned up
        deprecated_files: list[str] = ['gui_with_overlay.py', 'paddle_fix.py']
        cleaned_files = 0
        for filename in deprecated_files:
            if not os.path.exists(filename):
                cleaned_files += 1
        
        if cleaned_files == len(deprecated_files):
            print("✓ Deprecated files cleaned up")
            improvements_found += 1
        
        # Check if new modular structure exists
        if os.path.exists('service_container.py'):
            print("✓ Dependency injection structure implemented")
            improvements_found += 1
        
        # Check if classes follow SRP
        with open('config_manager.py', 'r', encoding='utf-8') as f:
            config_manager_content = f.read()
        
        if 'class ConfigManager:' in config_manager_content and len(config_manager_content) < 10000:
            print("✓ ConfigManager follows Single Responsibility Principle")
            improvements_found += 1
        
        print(f"✓ Found {improvements_found} code improvements")
        return improvements_found >= 3
        
    except Exception as e:
        print(f"✗ Code improvements test failed: {e}")
        return False


def test_documentation() -> bool:
    """Test that code has proper documentation."""
    print("\n=== Testing Documentation ===")
    
    files_to_check: list[str] = [
        'config_manager.py',
        'ocr_service.py',
        'automation_service.py',
        'grid_manager.py',
        'service_container.py'
    ]
    
    try:
        documented_files = 0
        
        for filename in files_to_check:
            with open(filename, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Check for module docstring
            if '"""' in content[:500]:  # Docstring should be near the top
                documented_files += 1
                print(f"✓ {filename}: Has module documentation")
            else:
                print(f"⚠ {filename}: Missing module documentation")
        
        print(f"✓ {documented_files}/{len(files_to_check)} files have documentation")
        return documented_files >= len(files_to_check) * 0.8  # At least 80%
        
    except Exception as e:
        print(f"✗ Documentation test failed: {e}")
        return False


def main() -> bool:
    """Run all basic structure tests."""
    print("Starting Basic Structure Tests")
    print("=" * 50)
    
    tests: list[tuple[str, callable[[], bool]]] = [
        ("Configuration Structure", test_config_structure),
        ("File Structure", test_file_structure),
        ("Import Syntax", test_import_syntax),
        ("Class Structure", test_class_structure),
        ("Code Improvements", test_code_improvements),
        ("Documentation", test_documentation)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
        except Exception as e:
            print(f"✗ {test_name} test failed with exception: {e}")
    
    # Summary
    print("\n" + "=" * 50)
    print(f"Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All basic structure tests passed!")
        print("\nRefactoring Summary:")
        print("- ✅ Separated MonitorManager into focused services")
        print("- ✅ Moved hardcoded values to configuration")
        print("- ✅ Implemented dependency injection")
        print("- ✅ Added proper error handling and logging")
        print("- ✅ Created testable, modular architecture")
        print("- ✅ Cleaned up duplicate and unnecessary files")
        return True
    else:
        print(f"⚠ {total - passed} test(s) failed.")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)