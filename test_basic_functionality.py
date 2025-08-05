#!/usr/bin/env python3
"""Basic functionality test without GUI"""
import sys
import os
import io

# Set UTF-8 encoding for stdout
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Set environment variables to suppress logs
os.environ['PPOCR_LOG_LEVEL'] = 'ERROR'
os.environ['PADDLEX_LOG_LEVEL'] = 'ERROR'
os.environ['PADDLE_LOG_LEVEL'] = 'ERROR'
os.environ['GLOG_v'] = '0'
os.environ['GLOG_minloglevel'] = '3'

sys.path.insert(0, 'src')

print("=" * 60)
print("기본 기능 테스트")
print("=" * 60)

# 1. 설정 관리자 테스트
print("\n1. 설정 관리자 테스트...")
try:
    from core.config_manager import ConfigManager
    config = ConfigManager()
    print(f"✅ 설정 로드 성공: {config.config_path}")
    print(f"   - 그리드 크기: {config.get('grid_rows')}x{config.get('grid_cols')}")
    print(f"   - OCR 간격: {config.get('ocr_interval_sec')}초")
    print(f"   - 트리거 패턴: {config.get('trigger_patterns')}")
except Exception as e:
    print(f"❌ 설정 관리자 오류: {e}")

# 2. OCR 보정기 테스트
print("\n2. OCR 보정기 테스트...")
try:
    from ocr.enhanced_ocr_corrector import EnhancedOCRCorrector
    corrector = EnhancedOCRCorrector()
    
    test_texts = [
        "들머왔습니다",
        "들어왔습니다",
        "님이 들어왔습니다",
        "입장하셨습니다"
    ]
    
    for text in test_texts:
        is_match, pattern = corrector.check_trigger_pattern(text)
        if is_match:
            print(f"✅ '{text}' → 매칭됨 (패턴: {pattern})")
        else:
            print(f"   '{text}' → 매칭 안됨")
            
except Exception as e:
    print(f"❌ OCR 보정기 오류: {e}")

# 3. 캐시 관리자 테스트
print("\n3. 캐시 관리자 테스트...")
try:
    from core.cache_manager import CacheManager
    cache = CacheManager()
    
    # 테스트 데이터 캐싱
    import numpy as np
    test_image = np.zeros((100, 100, 3), dtype=np.uint8)
    cache_key = cache.get_image_hash(test_image)
    
    # OCR 결과 캐싱
    from ocr.enhanced_ocr_service import OCRResult
    test_result = OCRResult("테스트", 0.95)
    cache.cache_ocr_result(cache_key, test_result)
    
    # 캐시 확인
    cached = cache.get_cached_ocr_result(cache_key)
    if cached and cached.text == "테스트":
        print("✅ 캐시 저장/조회 성공")
    else:
        print("❌ 캐시 기능 오류")
        
except Exception as e:
    print(f"❌ 캐시 관리자 오류: {e}")

# 4. 성능 모니터 테스트
print("\n4. 성능 모니터 테스트...")
try:
    from monitoring.performance_monitor import PerformanceMonitor
    monitor = PerformanceMonitor()
    
    # 테스트 메트릭 기록
    monitor.record_ocr_time(0.1)
    monitor.record_detection("test_cell", "테스트 감지")
    
    metrics = monitor.get_current_metrics()
    print(f"✅ 성능 모니터 초기화 성공")
    print(f"   - 평균 OCR 시간: {metrics.get('ocr_time_avg', 0):.3f}초")
    print(f"   - 감지 횟수: {metrics.get('detection_count', 0)}")
    
except Exception as e:
    print(f"❌ 성능 모니터 오류: {e}")

# 5. 서비스 컨테이너 테스트
print("\n5. 서비스 컨테이너 테스트...")
try:
    from core.service_container import ServiceContainer
    container = ServiceContainer(config)
    
    print("✅ 서비스 컨테이너 초기화 성공")
    print(f"   - OCR 서비스: {'사용가능' if container.ocr_service else '사용불가'}")
    print(f"   - 자동화 서비스: {'사용가능' if container.automation_service else '사용불가'}")
    print(f"   - 캐시 관리자: {'사용가능' if container.cache_manager else '사용불가'}")
    
except Exception as e:
    print(f"❌ 서비스 컨테이너 오류: {e}")

# 6. PaddleOCR 가용성 테스트
print("\n6. PaddleOCR 가용성 테스트...")
try:
    from utils.suppress_output import suppress_stdout_stderr
    
    with suppress_stdout_stderr():
        from paddleocr import PaddleOCR
        from ocr.safe_paddleocr import create_safe_paddleocr
        
        ocr = create_safe_paddleocr()
        if ocr:
            print("✅ PaddleOCR 초기화 성공 (로그 억제됨)")
        else:
            print("⚠️ PaddleOCR 초기화 실패")
            
except ImportError:
    print("❌ PaddleOCR가 설치되지 않음")
except Exception as e:
    print(f"❌ PaddleOCR 테스트 오류: {e}")

print("\n" + "=" * 60)
print("테스트 완료")
print("=" * 60)