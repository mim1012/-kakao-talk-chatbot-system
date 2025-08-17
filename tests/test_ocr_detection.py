"""
OCR Detection Test Script
Tests the enhanced OCR service with various image conditions
"""
from __future__ import annotations

import sys
import os
from typing import Any
import cv2
import numpy as np
import mss
from PyQt5.QtWidgets import QApplication

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from core.config_manager import ConfigManager
try:
    from ocr.enhanced_ocr_service import EnhancedOCRService
except ImportError:
    from ocr.fast_ocr_adapter import FastOCRAdapter as EnhancedOCRService
from grid.grid_manager import GridManager


def create_test_image_with_text(text: str, width: int = 400, height: int = 100) -> np.ndarray:
    """Create a test image with Korean text using PIL for better Korean support."""
    try:
        from PIL import Image, ImageDraw, ImageFont
        
        # Create PIL image
        img = Image.new('RGB', (width, height), color=(255, 255, 255))
        draw = ImageDraw.Draw(img)
        
        try:
            # Try to use Korean font
            font = ImageFont.truetype("malgun.ttf", 24)
        except:
            try:
                font = ImageFont.truetype("arial.ttf", 24)
            except:
                font = ImageFont.load_default()
        
        # Calculate text position
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        
        x = (width - text_width) // 2
        y = (height - text_height) // 2
        
        # Draw text
        draw.text((x, y), text, fill=(0, 0, 0), font=font)
        
        # Convert to numpy array
        return np.array(img)
        
    except ImportError:
        # Fallback to OpenCV
        img = np.ones((height, width, 3), dtype=np.uint8) * 255
        font = cv2.FONT_HERSHEY_SIMPLEX
        cv2.putText(img, text, (10, 35), font, 1, (0, 0, 0), 2, cv2.LINE_AA)
        return img


def test_ocr_service() -> None:
    """Test the enhanced OCR service."""
    print("🧪 Enhanced OCR Service Test")
    print("=" * 60)
    
    # Initialize services
    config = ConfigManager()
    ocr_service = EnhancedOCRService(config)
    
    # Test 1: Service availability
    print("\n1️⃣ Service Availability Test")
    status = ocr_service.get_status()
    print(f"   OCR Available: {status['available']}")
    print(f"   PaddleOCR Installed: {status['paddleocr_installed']}")
    print(f"   Engine Initialized: {status['engine_initialized']}")
    
    if not status['available']:
        print("❌ OCR service not available. Please install PaddleOCR.")
        return
    
    # Test 2: Screenshot capture and OCR
    print("\n2️⃣ Screenshot Capture Test")
    print("   Capturing screen area...")
    
    with mss.mss() as sct:
        # Capture a small area of the primary monitor
        monitor = sct.monitors[1]  # Primary monitor
        area = {
            'left': monitor['left'] + 100,
            'top': monitor['top'] + 100,
            'width': 300,
            'height': 100
        }
        
        screenshot = sct.grab(area)
        image = np.array(screenshot)
        
        # Convert BGRA to BGR
        if image.shape[2] == 4:
            image = image[:, :, :3]
        
        # Save original screenshot
        cv2.imwrite("debug_screenshots/test_original.png", image)
        print(f"   Screenshot saved: debug_screenshots/test_original.png")
        print(f"   Image shape: {image.shape}")
        
        # Test OCR
        print("\n3️⃣ OCR Detection Test")
        result = ocr_service.perform_ocr_with_recovery(image, "test_capture")
        
        if result.is_valid():
            print(f"   ✅ Text detected: '{result.text}'")
            print(f"   Confidence: {result.confidence:.2f}")
            print(f"   Position: {result.position}")
            
            # Test pattern matching
            is_trigger = ocr_service.check_trigger_patterns(result)
            print(f"   Trigger pattern match: {'Yes' if is_trigger else 'No'}")
        else:
            print(f"   ❌ No text detected")
            if 'all_results' in result.debug_info:
                print(f"   Debug: Tried {len(result.debug_info['all_results'])} strategies")
    
    # Test 3: Multiple cell areas
    print("\n4️⃣ Multiple Cell Test")
    grid_manager = GridManager(config)
    
    # Test first 5 cells
    test_cells = grid_manager.cells[:5]
    
    with mss.mss() as sct:
        for cell in test_cells:
            print(f"\n   Testing {cell.id}:")
            
            try:
                # Capture cell area
                area = {
                    'left': cell.ocr_area[0],
                    'top': cell.ocr_area[1],
                    'width': cell.ocr_area[2],
                    'height': cell.ocr_area[3]
                }
                
                screenshot = sct.grab(area)
                image = np.array(screenshot)
                
                if image.shape[2] == 4:
                    image = image[:, :, :3]
                
                # Perform OCR
                result = ocr_service.perform_ocr_with_recovery(image, cell.id)
                
                if result.is_valid():
                    print(f"      ✅ Detected: '{result.text}' (conf: {result.confidence:.2f})")
                else:
                    print(f"      ⚪ No text detected")
                    
            except Exception as e:
                print(f"      ❌ Error: {e}")
    
    # Test 4: Performance statistics
    print("\n5️⃣ Performance Statistics")
    final_status = ocr_service.get_status()
    stats = final_status['stats']
    
    print(f"   Total attempts: {stats['total_attempts']}")
    print(f"   Success rate: {stats['success_rate']}")
    print(f"   Empty rate: {stats['empty_rate']}")
    print(f"   Error rate: {stats['error_rate']}")
    print(f"   Debug saves: {stats['debug_saves']}")
    
    print("\n✅ Test completed!")
    print("Check 'debug_screenshots/preprocessing' folder for debug images.")


def test_specific_area() -> None:
    """Test OCR on a specific screen area."""
    print("\n🎯 Specific Area OCR Test")
    print("=" * 60)
    
    config = ConfigManager()
    ocr_service = EnhancedOCRService(config)
    
    # Define the area to test (adjust coordinates as needed)
    test_area = {
        'left': 100,
        'top': 100,
        'width': 400,
        'height': 200
    }
    
    print(f"Testing area: {test_area}")
    
    with mss.mss() as sct:
        # Capture
        screenshot = sct.grab(test_area)
        image = np.array(screenshot)
        
        if image.shape[2] == 4:
            image = image[:, :, :3]
        
        # Save for inspection
        cv2.imwrite("debug_screenshots/specific_area_test.png", image)
        
        # Test with different preprocessing strategies
        print("\nTesting with enhanced preprocessing...")
        result = ocr_service.perform_ocr_with_recovery(image, "specific_area")
        
        if result.is_valid():
            print(f"✅ Detected text: '{result.text}'")
            print(f"   Confidence: {result.confidence:.2f}")
            
            if 'all_results' in result.debug_info:
                print(f"\nAll detection results:")
                for r in result.debug_info['all_results']:
                    print(f"   Strategy {r['strategy']}: '{r['text']}' (conf: {r['confidence']:.2f})")
        else:
            print("❌ No text detected")
            
            if 'all_results' in result.debug_info and result.debug_info['all_results']:
                print(f"\nPartial results from strategies:")
                for r in result.debug_info['all_results']:
                    print(f"   Strategy {r['strategy']}: '{r['text']}' (conf: {r['confidence']:.2f})")


def test_trigger_patterns() -> None:
    """Test trigger pattern detection with generated images."""
    print("\n🎯 Trigger Pattern Detection Test")
    print("=" * 60)
    
    # Import FastOCRAdapter
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
    from ocr.fast_ocr_adapter import FastOCRAdapter
    from core.config_manager import ConfigManager
    
    # Initialize services
    config = ConfigManager()
    ocr_adapter = FastOCRAdapter(config)
    
    # Test phrases
    test_phrases = [
        "들어왔습니다",
        "님이 들어왔습니다", 
        "홍길동님이 들어왔습니다",
        "들어왔",
        "들머왔습니다",  # Common OCR error
        "입장했습니다",
        "참여했습니다",
        "안녕하세요",  # Non-trigger
        "안녕히가세요"  # Non-trigger
    ]
    
    print(f"Testing {len(test_phrases)} phrases...")
    
    success_count = 0
    total_count = len(test_phrases)
    
    for i, phrase in enumerate(test_phrases):
        print(f"\n--- Test {i+1}: '{phrase}' ---")
        
        # Create test image
        test_image = create_test_image_with_text(phrase)
        
        # Save test image
        filename = f"test_trigger_{i+1}_{phrase.replace(' ', '_')}.png"
        cv2.imwrite(f"debug_screenshots/{filename}", test_image)
        print(f"Image saved: {filename}")
        
        # Perform OCR
        result = ocr_adapter.perform_ocr_with_recovery(test_image, f"test_{i+1}")
        
        print(f"OCR Result:")
        print(f"  Original: '{result.debug_info.get('original_text', '')}'")
        print(f"  Corrected: '{result.text}'")
        print(f"  Confidence: {result.confidence:.2f}")
        
        # Check trigger pattern
        is_trigger = ocr_adapter.check_trigger_patterns(result)
        print(f"  Trigger detected: {is_trigger}")
        
        # Expected result
        expected_trigger = any(pattern in phrase for pattern in ["들어왔습니다", "들어왔", "입장", "참여"])
        
        if is_trigger == expected_trigger:
            print(f"  ✅ PASS: Expected {expected_trigger}, got {is_trigger}")
            success_count += 1
        else:
            print(f"  ❌ FAIL: Expected {expected_trigger}, got {is_trigger}")
    
    print(f"\n📊 Test Results: {success_count}/{total_count} passed ({success_count/total_count*100:.1f}%)")


if __name__ == "__main__":
    # Create debug directory
    os.makedirs("debug_screenshots", exist_ok=True)
    os.makedirs("debug_screenshots/preprocessing", exist_ok=True)
    os.makedirs("debug_screenshots/target_cell", exist_ok=True)
    
    # Run trigger pattern test
    test_trigger_patterns()
    
    # Run original tests
    # test_ocr_service()
    # test_specific_area()
    
    print("\n🏁 All tests completed!")