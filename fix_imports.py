#!/usr/bin/env python3
"""
Fix imports after project reorganization
"""
import os
import re
from pathlib import Path

# Import mappings
IMPORT_MAPPINGS = {
    # Core imports
    r'from config_manager import': 'from core.config_manager import',
    r'from grid_manager import': 'from core.grid_manager import',
    r'from service_container import': 'from core.service_container import',
    r'import config_manager': 'import core.config_manager',
    r'import grid_manager': 'import core.grid_manager',
    r'import service_container': 'import core.service_container',
    
    # OCR imports
    r'from enhanced_ocr_service import': 'from ocr.enhanced_ocr_service import',
    r'from enhanced_ocr_corrector import': 'from ocr.enhanced_ocr_corrector import',
    r'from ocr_service import': 'from ocr.ocr_service import',
    r'import enhanced_ocr_service': 'import ocr.enhanced_ocr_service',
    r'import enhanced_ocr_corrector': 'import ocr.enhanced_ocr_corrector',
    r'import ocr_service': 'import ocr.ocr_service',
    
    # Monitoring imports
    r'from improved_monitoring_thread import': 'from monitoring.improved_monitoring_thread import',
    r'from monitor_manager import': 'from monitoring.monitor_manager import',
    r'import improved_monitoring_thread': 'import monitoring.improved_monitoring_thread',
    r'import monitor_manager': 'import monitoring.monitor_manager',
    
    # Automation imports
    r'from automation_service import': 'from automation.automation_service import',
    r'from smart_input_automation import': 'from automation.smart_input_automation import',
    r'import automation_service': 'import automation.automation_service',
    r'import smart_input_automation': 'import automation.smart_input_automation',
    
    # GUI imports (for cross-references)
    r'from optimized_chatbot_system import': 'from gui.optimized_chatbot_system import',
    r'from grid_overlay_system import': 'from gui.grid_overlay_system import',
    r'from complete_chatbot_system import': 'from gui.complete_chatbot_system import',
    r'from fixed_gui_system import': 'from gui.fixed_gui_system import',
}

def fix_imports_in_file(file_path):
    """Fix imports in a single file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # Apply all import mappings
        for old_pattern, new_pattern in IMPORT_MAPPINGS.items():
            content = re.sub(old_pattern, new_pattern, content)
        
        # Only write if changed
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"Fixed imports in: {file_path}")
            return True
        
        return False
    
    except Exception as e:
        print(f"Error processing {file_path}: {e}")
        return False

def main():
    """Fix all imports in src directory."""
    src_dir = Path("src")
    fixed_count = 0
    
    # Process all Python files in src
    for py_file in src_dir.rglob("*.py"):
        if fix_imports_in_file(py_file):
            fixed_count += 1
    
    print(f"\nTotal files fixed: {fixed_count}")

if __name__ == "__main__":
    main()