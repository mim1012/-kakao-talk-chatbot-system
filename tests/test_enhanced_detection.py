#!/usr/bin/env python3
"""
강화된 OCR 감지 시스템 테스트
다양한 OCR 오류 패턴들이 올바르게 "들어왔습니다"로 인식되는지 테스트
"""
from __future__ import annotations

import sys
import time
from enhanced_ocr_corrector import EnhancedOCRCorrector
from service_container import ServiceContainer

def test_ocr_patterns() -> bool:
    """OCR 패턴 인식 테스트"""
    print("=" * 60)
    print("🧪 강화된 OCR 감지 시스템 테스트")
    print("=" * 60)
    
    # 강화된 보정기 초기화
    corrector = EnhancedOCRCorrector()
    
    # 실제 PaddleOCR에서 발생할 수 있는 다양한 오류 패턴들
    test_patterns = [
        # 정확한 패턴들
        ("들어왔습니다", True, "정확한 텍스트"),
        ("입장했습니다", True, "정확한 텍스트"), 
        ("참여했습니다", True, "정확한 텍스트"),
        
        # 일반적인 OCR 오류들
        ("들머왔습니다", True, "ㅓ->ㅁ 오류"),
        ("둘어왔습니다", True, "들->둘 오류"),
        ("틀어왔습니다", True, "들->틀 오류"),
        ("들어왔시니다", True, "습->시 오류"),
        ("들어왔느니다", True, "습->느 오류"),
        ("들어왔슴니다", True, "습->슴 오류"),
        ("들어왔읍니다", True, "습->읍 오류"),
        ("들어왔ㅅ니다", True, "습->ㅅ 오류"),
        ("들어왔5니다", True, "습->5 오류"),
        ("들어왔7니다", True, "습->7 오류"),
        ("들어와습니다", True, "왔->와 오류"),
        ("들어왔습니타", True, "다->타 오류"),
        ("들어왔스니다", True, "습->스 오류"),
        
        # 공백/특수문자 포함
        ("들어왔습니다.", True, "마침표 포함"),
        ("들 어 왔 습 니 다", True, "공백 포함"),
        ("들어왔습니다!!", True, "느낌표 포함"),
        (" 들어왔습니다 ", True, "앞뒤 공백"),
        
        # 입장했습니다 변형들
        ("입정했습니다", True, "장->정 오류"),
        ("입창했습니다", True, "장->창 오류"),
        ("입잠했습니다", True, "장->잠 오류"),
        ("입장햤습니다", True, "했->햤 오류"),
        ("입장했스니다", True, "습->스 오류"),
        ("입장했슴니다", True, "습->슴 오류"),
        
        # 참여했습니다 변형들
        ("참어했습니다", True, "여->어 오류"),
        ("참야했습니다", True, "여->야 오류"),
        ("잠여했습니다", True, "참->잠 오류"),
        ("참여햤습니다", True, "했->햤 오류"),
        ("참여했스니다", True, "습->스 오류"),
        
        # 부분 매칭 케이스
        ("들어왔", True, "짧은 형태"),
        ("입장했", True, "짧은 형태"),
        ("참여했", True, "짧은 형태"),
        
        # 매칭되지 않아야 할 케이스들
        ("안녕하세요", False, "일반 인사"),
        ("반갑습니다", False, "일반 인사"),
        ("감사합니다", False, "일반 인사"),
        ("좋은 하루", False, "일반 문장"),
        ("12345", False, "숫자만"),
        ("", False, "빈 문자열"),
        ("ㅋㅋㅋ", False, "자음만"),
        ("나갔습니다", False, "반대 의미"),
        ("퇴장했습니다", False, "반대 의미"),
        
        # Edge case들
        ("들어왔습니다들어왔습니다", True, "중복"),
        ("abc들어왔습니다xyz", True, "영문 섞임"),
        ("123들머왔습니다456", True, "숫자 섞임"),
    ]
    
    # 테스트 실행
    passed: int = 0
    failed: int = 0
    
    for i, (text, expected, description) in enumerate(test_patterns, 1):
        is_match, matched_pattern = corrector.check_trigger_pattern(text)
        
        # 결과 검증
        if is_match == expected:
            status = "✅ PASS"
            passed += 1
        else:
            status = "❌ FAIL"
            failed += 1
        
        # 결과 출력
        result_info = f"-> {matched_pattern}" if is_match else "-> NO MATCH"
        print(f"{i:2d}. {status} | '{text}' {result_info}")
        print(f"     설명: {description} | 예상: {'매칭' if expected else '비매칭'}")
        
        if i % 10 == 0:  # 10개마다 구분선
            print("-" * 60)
    
    # 최종 결과
    total: int = len(test_patterns)
    success_rate: float = (passed / total) * 100
    
    print("=" * 60)
    print(f"📊 테스트 결과: {passed}/{total} 통과 ({success_rate:.1f}%)")
    
    if success_rate >= 95:
        print("🎉 우수! OCR 보정 시스템이 매우 잘 작동합니다.")
    elif success_rate >= 85:
        print("👍 양호! OCR 보정 시스템이 잘 작동합니다.")  
    elif success_rate >= 70:
        print("⚠️ 보통! 일부 개선이 필요합니다.")
    else:
        print("❌ 불량! OCR 보정 시스템에 문제가 있습니다.")
    
    if failed > 0:
        print(f"⚠️ {failed}개 테스트 실패 - 추가 패턴 보정이 필요할 수 있습니다.")
    
    return success_rate >= 85

def test_performance() -> bool:
    """성능 테스트"""
    print("\n" + "=" * 60)
    print("⚡ 성능 테스트")
    print("=" * 60)
    
    corrector = EnhancedOCRCorrector()
    
    # 성능 테스트용 패턴들
    test_texts = [
        "들어왔습니다", "들머왔습니다", "둘어왔습니다", "틀어왔습니다",
        "입장했습니다", "입정했습니다", "참여했습니다", "참어했습니다",
        "안녕하세요", "반갑습니다"
    ] * 10  # 10배 확장
    
    # 성능 측정
    start_time = time.time()
    
    for text in test_texts:
        corrector.check_trigger_pattern(text)
    
    end_time = time.time()
    
    # 결과 계산
    total_time = end_time - start_time
    avg_time = (total_time / len(test_texts)) * 1000  # ms 단위
    throughput = len(test_texts) / total_time  # 초당 처리량
    
    print(f"📈 총 처리량: {len(test_texts)}개 텍스트")
    print(f"📈 총 시간: {total_time:.3f}초")
    print(f"📈 평균 처리 시간: {avg_time:.2f}ms/텍스트")
    print(f"📈 처리량: {throughput:.1f}개/초")
    
    # 실시간 성능 평가
    if avg_time <= 1.0:
        print("🚀 우수한 성능! 실시간 처리에 적합합니다.")
    elif avg_time <= 5.0:
        print("👍 양호한 성능! 실시간 처리 가능합니다.")
    elif avg_time <= 10.0:
        print("⚠️ 보통 성능! 배치 처리 권장합니다.")
    else:
        print("❌ 느린 성능! 최적화가 필요합니다.")
    
    return avg_time <= 5.0

def main() -> bool:
    """메인 테스트 함수"""
    print("🎯 카카오톡 챗봇 강화된 OCR 감지 시스템 종합 테스트")
    print("🔍 다양한 PaddleOCR 오류 패턴 인식 능력 검증")
    print()
    
    # 패턴 인식 테스트
    pattern_success = test_ocr_patterns()
    
    # 성능 테스트
    performance_success = test_performance()
    
    # 최종 평가
    print("\n" + "=" * 60)
    print("🏆 최종 평가")
    print("=" * 60)
    
    if pattern_success and performance_success:
        print("🎉 완벽! 강화된 OCR 시스템이 실전 사용 가능합니다.")
        print("✅ 30개 오버레이에서 실시간 감지 준비 완료!")
        return True
    elif pattern_success:
        print("👍 패턴 인식은 우수하나 성능 최적화가 필요합니다.")
        return True
    elif performance_success:
        print("⚠️ 성능은 좋으나 패턴 인식 정확도 개선이 필요합니다.")
        return False
    else:
        print("❌ 패턴 인식과 성능 모두 개선이 필요합니다.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)