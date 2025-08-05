#!/usr/bin/env python3
"""
OCR 성능 테스트 및 비교 도구
기존 시스템 vs 최적화된 시스템 성능 비교
"""
import os
import sys
import time
import logging
import numpy as np
import cv2
from typing import List, Dict, Any

# 환경 변수 설정
os.environ['PPOCR_LOG_LEVEL'] = 'ERROR'
os.environ['PADDLEX_LOG_LEVEL'] = 'ERROR'
os.environ['PADDLE_LOG_LEVEL'] = 'ERROR'
os.environ['TQDM_DISABLE'] = '1'

def create_test_images() -> List[np.ndarray]:
    """테스트용 이미지 생성"""
    test_images = []
    
    # 다양한 카카오톡 메시지 시뮬레이션
    messages = [
        "홍길동님이 들어왔습니다",
        "김철수님이 채팅방에 입장했습니다", 
        "이영희님이 참여했습니다",
        "박민수님이 들어왔습니다",
        "최지훈님이 입장했습니다",
        "들어왔습니다",
        "님이 들어왔습니다",
        "12:34",  # 노이즈 데이터
        "안녕하세요",  # 일반 메시지
        "든어왔습니다"  # OCR 오류 시뮬레이션
    ]
    
    for i, message in enumerate(messages):
        # 이미지 생성 (300x80 크기)
        img = np.ones((80, 300, 3), dtype=np.uint8) * 255
        
        # 다양한 조건 시뮬레이션
        if i % 3 == 0:
            # 노이즈 추가
            noise = np.random.randint(0, 50, img.shape, dtype=np.uint8)
            img = cv2.subtract(img, noise)
        elif i % 3 == 1:
            # 약간의 블러
            img = cv2.GaussianBlur(img, (3, 3), 0)
        
        # 텍스트 추가
        font_scale = 0.8 if len(message) > 15 else 1.0
        cv2.putText(img, message, (10, 50), 
                   cv2.FONT_HERSHEY_SIMPLEX, font_scale, (0, 0, 0), 2)
        
        test_images.append(img)
    
    return test_images

def test_original_system(test_images: List[np.ndarray]) -> Dict[str, Any]:
    """기존 시스템 테스트"""
    print("\n=== 기존 시스템 테스트 ===")
    
    try:
        from src.ocr.enhanced_ocr_service import EnhancedOCRService
        from src.core.config_manager import ConfigManager
        
        config = ConfigManager()
        ocr_service = EnhancedOCRService(config)
        
        if not ocr_service.is_available():
            return {'error': 'OCR service not available'}
        
        results = {
            'total_time': 0,
            'successful_detections': 0,
            'failed_detections': 0,
            'detection_details': [],
            'avg_confidence': 0,
            'trigger_matches': 0
        }
        
        total_confidence = 0
        confidence_count = 0
        
        for i, image in enumerate(test_images):
            start_time = time.time()
            
            ocr_result = ocr_service.perform_ocr_with_recovery(image, f"test_{i}")
            processing_time = time.time() - start_time
            
            results['total_time'] += processing_time
            
            if ocr_result.is_valid():
                results['successful_detections'] += 1
                total_confidence += ocr_result.confidence
                confidence_count += 1
                
                # 트리거 패턴 체크
                if ocr_service.check_trigger_patterns(ocr_result):
                    results['trigger_matches'] += 1
                
                results['detection_details'].append({
                    'image_id': i,
                    'text': ocr_result.text,
                    'confidence': ocr_result.confidence,
                    'processing_time': processing_time,
                    'is_trigger': ocr_service.check_trigger_patterns(ocr_result)
                })
                
                print(f"  이미지 {i}: '{ocr_result.text}' (신뢰도: {ocr_result.confidence:.3f}, {processing_time:.3f}s)")
            else:
                results['failed_detections'] += 1
                print(f"  이미지 {i}: 감지 실패 ({processing_time:.3f}s)")
        
        if confidence_count > 0:
            results['avg_confidence'] = total_confidence / confidence_count
        
        return results
        
    except Exception as e:
        return {'error': str(e)}

def test_optimized_system(test_images: List[np.ndarray]) -> Dict[str, Any]:
    """최적화된 시스템 테스트"""
    print("\n=== 최적화된 시스템 테스트 ===")
    
    try:
        from src.ocr.optimized_ocr_engine import OptimizedOCREngine
        from src.core.config_manager import ConfigManager
        
        config = ConfigManager()
        ocr_engine = OptimizedOCREngine(config)
        
        results = {
            'total_time': 0,
            'successful_detections': 0,
            'failed_detections': 0,
            'detection_details': [],
            'avg_confidence': 0,
            'cache_hits': 0,
            'strategies_used': {},
            'candidates_stats': []
        }
        
        total_confidence = 0
        confidence_count = 0
        
        for i, image in enumerate(test_images):
            ocr_result = ocr_engine.process_image(image, f"test_{i}")
            
            results['total_time'] += ocr_result.processing_time
            
            if ocr_result.text:
                results['successful_detections'] += 1
                total_confidence += ocr_result.confidence
                confidence_count += 1
                
                if ocr_result.cache_hit:
                    results['cache_hits'] += 1
                
                # 전략 사용 통계
                strategy = ocr_result.strategy_used
                results['strategies_used'][strategy] = results['strategies_used'].get(strategy, 0) + 1
                
                results['candidates_stats'].append(ocr_result.candidates_count)
                
                results['detection_details'].append({
                    'image_id': i,
                    'text': ocr_result.text,
                    'confidence': ocr_result.confidence,
                    'processing_time': ocr_result.processing_time,
                    'strategy': ocr_result.strategy_used,
                    'cache_hit': ocr_result.cache_hit,
                    'candidates': ocr_result.candidates_count
                })
                
                cache_indicator = " [캐시]" if ocr_result.cache_hit else ""
                print(f"  이미지 {i}: '{ocr_result.text}' (신뢰도: {ocr_result.confidence:.3f}, "
                      f"{ocr_result.processing_time:.3f}s, {ocr_result.strategy_used}){cache_indicator}")
            else:
                results['failed_detections'] += 1
                print(f"  이미지 {i}: 감지 실패 ({ocr_result.processing_time:.3f}s)")
        
        if confidence_count > 0:
            results['avg_confidence'] = total_confidence / confidence_count
        
        # 종합 통계 가져오기
        comprehensive_stats = ocr_engine.get_comprehensive_stats()
        results['engine_stats'] = comprehensive_stats
        
        # 정리
        ocr_engine.cleanup()
        
        return results
        
    except Exception as e:
        return {'error': str(e)}

def compare_results(original: Dict[str, Any], optimized: Dict[str, Any]):
    """결과 비교 및 리포트 생성"""
    print("\n" + "="*60)
    print("성능 비교 리포트")
    print("="*60)
    
    if 'error' in original:
        print(f"❌ 기존 시스템 오류: {original['error']}")
        return
    
    if 'error' in optimized:
        print(f"❌ 최적화된 시스템 오류: {optimized['error']}")
        return
    
    # 기본 통계
    print(f"\n📊 기본 성능 비교:")
    print(f"{'항목':<20} {'기존 시스템':<15} {'최적화된 시스템':<15} {'개선율':<10}")
    print("-" * 65)
    
    # 처리 시간
    time_improvement = ((original['total_time'] - optimized['total_time']) / original['total_time'] * 100)
    print(f"{'총 처리 시간':<20} {original['total_time']:.3f}초{'':<7} {optimized['total_time']:.3f}초{'':<7} {time_improvement:+.1f}%")
    
    # 성공률
    orig_success_rate = original['successful_detections'] / (original['successful_detections'] + original['failed_detections']) * 100
    opt_success_rate = optimized['successful_detections'] / (optimized['successful_detections'] + optimized['failed_detections']) * 100
    success_improvement = opt_success_rate - orig_success_rate
    print(f"{'성공률':<20} {orig_success_rate:.1f}%{'':<10} {opt_success_rate:.1f}%{'':<10} {success_improvement:+.1f}%")
    
    # 평균 신뢰도
    confidence_improvement = (optimized['avg_confidence'] - original['avg_confidence']) * 100
    print(f"{'평균 신뢰도':<20} {original['avg_confidence']:.3f}{'':<11} {optimized['avg_confidence']:.3f}{'':<11} {confidence_improvement:+.1f}%")
    
    # 평균 처리 시간
    orig_avg_time = original['total_time'] / len([d for d in original['detection_details'] if d])
    opt_avg_time = optimized['total_time'] / len([d for d in optimized['detection_details'] if d])
    avg_time_improvement = ((orig_avg_time - opt_avg_time) / orig_avg_time * 100)
    print(f"{'이미지당 처리시간':<20} {orig_avg_time:.3f}초{'':<7} {opt_avg_time:.3f}초{'':<7} {avg_time_improvement:+.1f}%")
    
    # 최적화된 시스템만의 특징
    if 'cache_hits' in optimized:
        cache_rate = optimized['cache_hits'] / optimized['successful_detections'] * 100 if optimized['successful_detections'] > 0 else 0
        print(f"{'캐시 적중률':<20} {'N/A':<15} {cache_rate:.1f}%{'':<10} {'NEW'}")
    
    if 'strategies_used' in optimized:
        print(f"\n🎯 사용된 전략 분포:")
        for strategy, count in optimized['strategies_used'].items():
            percentage = count / optimized['successful_detections'] * 100
            print(f"  {strategy}: {count}회 ({percentage:.1f}%)")
    
    if 'candidates_stats' in optimized and optimized['candidates_stats']:
        avg_candidates = sum(optimized['candidates_stats']) / len(optimized['candidates_stats'])
        print(f"\n📈 평균 후보 결과 수: {avg_candidates:.1f}개")
    
    # 트리거 매칭 비교
    if 'trigger_matches' in original:
        print(f"\n🎯 트리거 패턴 매칭:")
        orig_trigger_rate = original['trigger_matches'] / original['successful_detections'] * 100 if original['successful_detections'] > 0 else 0
        print(f"  기존 시스템: {original['trigger_matches']}개 매칭 ({orig_trigger_rate:.1f}%)")
    
    # 상세 엔진 통계 (최적화된 시스템)
    if 'engine_stats' in optimized:
        engine_stats = optimized['engine_stats']['engine_stats']
        print(f"\n🔧 최적화된 엔진 상세 통계:")
        for key, value in engine_stats.items():
            print(f"  {key}: {value}")

def main():
    """성능 테스트 실행"""
    print("OCR 성능 테스트 시작")
    print("="*60)
    
    # 테스트 이미지 생성
    print("테스트 이미지 생성 중...")
    test_images = create_test_images()
    print(f"✅ {len(test_images)}개 테스트 이미지 생성 완료")
    
    # 테스트 이미지 저장 (시각적 확인용)
    os.makedirs("debug_screenshots/performance_test", exist_ok=True)
    for i, img in enumerate(test_images):
        cv2.imwrite(f"debug_screenshots/performance_test/test_image_{i}.png", img)
    
    # 기존 시스템 테스트
    original_results = test_original_system(test_images)
    
    # 최적화된 시스템 테스트  
    optimized_results = test_optimized_system(test_images)
    
    # 결과 비교
    compare_results(original_results, optimized_results)
    
    print(f"\n💾 테스트 이미지는 debug_screenshots/performance_test/ 폴더에 저장되었습니다.")
    print("테스트 완료!")

if __name__ == "__main__":
    main()