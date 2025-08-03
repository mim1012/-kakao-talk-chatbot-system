# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Architecture Overview

This is a KakaoTalk OCR-based chatbot system that monitors multiple chat windows for Korean text patterns (primarily "들어왔습니다" - "has entered") and automatically responds. The system uses a service-oriented architecture with dependency injection.

### Core Components

1. **Service Container Pattern**: All services are managed through `ServiceContainer` which handles dependency injection and lifecycle management
2. **Grid-Based Monitoring**: Screen divided into 30 cells (15 per monitor on dual monitor setup) for parallel OCR processing
3. **OCR Pipeline**: PaddleOCR → Enhanced OCR Corrector → Trigger Pattern Matching → Automation
4. **Performance Optimization**: Includes caching (LRU for images, TTL for OCR results), performance monitoring, and dynamic batch size adjustment

### Key Services

- **OCR Service**: `OptimizedOCRService` with GPU support, caching, and batch processing
- **Cache Manager**: Two-tier caching with image preprocessing cache and OCR result cache
- **Performance Monitor**: Real-time metrics collection with automatic optimization recommendations
- **Automation Service**: Mouse/keyboard control with retry logic and clipboard management

## Build and Run Commands

```bash
# Main application
python main.py

# Run with Qt plugin fix (Windows)
run_with_qt.bat

# Install dependencies  
pip install -r requirements.txt

# Run tests
python run_tests.py
# Or directly with pytest
python -m pytest tests/ -v --tb=short

# Run specific test
python -m pytest tests/test_simple.py::TestSimple::test_ocr_corrector_basic -v

# Diagnostic tools
python test_ocr_system.py          # Test OCR functionality
python tools/verify_screen_coordinates.py  # Verify screen coordinates
python tools/visual_cell_overlay.py        # Visual overlay for debugging
python tools/adjust_coordinates.py         # Adjust coordinates interactively
```

## Configuration

Main configuration in `config.json`:
- `grid_rows/cols`: Grid division (default 3x5 per monitor)
- `ocr_interval_sec`: OCR cycle interval (default 0.5s)
- `trigger_patterns`: Text patterns to detect
- `chatroom_configs`: Array of chat window positions
- `use_gpu`: Enable GPU acceleration for OCR
- `max_concurrent_ocr`: Number of parallel OCR workers

## Recent Major Changes

1. **GUI Consolidation** (2025-08-04): Merged 3 GUI files into unified `chatbot_gui.py`
2. **Performance Optimization**: Added caching system, performance monitoring, and dynamic optimization
3. **Test Framework**: Added pytest-based unit tests with fixtures and mocking

## Critical Implementation Notes

1. **OCR Error Correction**: The system includes extensive Korean OCR error correction mappings in `enhanced_ocr_corrector.py` to handle common misrecognitions (e.g., "들머왔습니다" → "들어왔습니다")

2. **Thread Safety**: Multiple monitoring threads access shared resources - all state modifications use locks or thread-safe queues

3. **Cooldown System**: Each cell has a 5-second cooldown after detection to prevent duplicate triggers

4. **Image Preprocessing**: Uses 4x scaling, grayscale conversion, and adaptive thresholding for better OCR accuracy

## Common Issues and Solutions

1. **numpy compatibility**: Python 3.13 has issues with numpy - use Python 3.11
2. **PyQt5 platform plugin**: Use `run_with_qt.bat` or set QT_PLUGIN_PATH manually
3. **OCR not detecting**: Check coordinates with verification tools, ensure KakaoTalk windows are in expected positions
4. **High CPU usage**: Reduce `max_concurrent_ocr` in config or increase `ocr_interval_sec`

## Testing Guidelines

- Unit tests use pytest with fixtures defined in `conftest.py`
- Mock external dependencies (PyQt5, numpy, PaddleOCR) for CI/CD
- Performance tests should use the `@pytest.mark.performance` marker
- Coverage target: 60% minimum (`--cov-fail-under=60` in pytest.ini)