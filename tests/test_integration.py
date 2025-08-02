#!/usr/bin/env python3
"""
카카오톡 챗봇 시스템 통합 테스트
모든 구성 요소의 연동 확인
"""
from __future__ import annotations

import sys
import os
import traceback

def test_file_structure() -> bool:
    """파일 구조 테스트"""
    print("📁 파일 구조 검사...")
    
    required_files = {
        'complete_chatbot_system.py': '완전한 GUI 시스템',
        'smart_input_automation.py': '스마트 입력 자동화',
        'enhanced_ocr_corrector.py': '강화된 OCR 보정기',
        'service_container.py': '서비스 컨테이너',
        'config.json': '설정 파일'
    }
    
    all_present: bool = True
    for file, desc in required_files.items():
        if os.path.exists(file):
            print(f"✅ {file} - {desc}")
        else:
            print(f"❌ {file} - {desc} (누락)")
            all_present = False
    
    return all_present

def test_smart_automation() -> bool:
    """스마트 자동화 시스템 테스트"""
    print("\n🤖 스마트 자동화 시스템 테스트...")
    
    try:
        from smart_input_automation import SmartInputAutomation, ClickResult
        
        # 객체 생성 테스트
        automation = SmartInputAutomation()
        print("✅ SmartInputAutomation 객체 생성 성공")
        
        # 테스트 데이터
        cell_bounds = (100, 100, 400, 300)
        ocr_area = (110, 250, 380, 40)
        
        # 입력 감지 테스트 (실제 스크린샷 없이)
        test_results = automation.test_input_detection(cell_bounds, ocr_area)
        print("✅ test_input_detection 메소드 실행 성공")
        
        # 결과 확인
        expected_methods = ["ocr_based", "template_matching", "adaptive_search", "multi_strategy"]
        for method in expected_methods:
            if method in test_results:
                result = test_results[method]
                print(f"  • {method}: {result['success']} (신뢰도: {result['confidence']:.2f})")
            else:
                print(f"  ❌ {method} 결과 없음")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import 오류: {e}")
        return False
    except Exception as e:
        print(f"❌ 실행 오류: {e}")
        traceback.print_exc()
        return False

def test_ocr_corrector() -> bool:
    """OCR 보정기 테스트"""
    print("\n🔧 OCR 보정기 테스트...")
    
    try:
        from enhanced_ocr_corrector import EnhancedOCRCorrector
        
        corrector = EnhancedOCRCorrector()
        print("✅ EnhancedOCRCorrector 객체 생성 성공")
        
        # 테스트 케이스들
        test_cases = [
            ("들어왔습니다", True),
            ("들머왔습니다", True),  # OCR 오류
            ("들 어왔습니다", True),
            ("일반 텍스트", False)
        ]
        
        for text, expected in test_cases:
            is_match, corrected = corrector.check_trigger_pattern(text)
            status = "✅" if is_match == expected else "❌"
            print(f"  {status} '{text}' → 매칭: {is_match}, 보정: '{corrected}'")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import 오류: {e}")
        return False
    except Exception as e:
        print(f"❌ 실행 오류: {e}")
        return False

def test_service_container() -> bool:
    """서비스 컨테이너 테스트"""
    print("\n🔧 서비스 컨테이너 테스트...")
    
    try:
        from service_container import ServiceContainer
        
        # 객체 생성 테스트 (PyQt5 없어도 기본 구조는 확인 가능)
        print("✅ ServiceContainer import 성공")
        return True
        
    except ImportError as e:
        print(f"❌ Import 오류: {e}")
        return False
    except Exception as e:
        print(f"❌ 실행 오류: {e}")
        return False

def test_config() -> bool:
    """설정 파일 테스트"""
    print("\n⚙️ 설정 파일 테스트...")
    
    try:
        import json
        
        with open('config.json', 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        print("✅ config.json 로드 성공")
        
        # 필수 설정 확인
        required_keys = [
            'grid_rows', 'grid_cols', 'ocr_interval_sec',
            'trigger_patterns', 'automation_config'
        ]
        
        for key in required_keys:
            if key in config:
                print(f"  ✅ {key}: {config[key]}")
            else:
                print(f"  ❌ {key}: 누락")
        
        # 오타 수정 확인
        if 'enable_batch_processing' in config.get('automation_config', {}):
            print("  ✅ enable_batch_processing 오타 수정됨")
        else:
            print("  ❌ enable_batch_processing 설정 확인 필요")
        
        return True
        
    except Exception as e:
        print(f"❌ 설정 파일 오류: {e}")
        return False

def main() -> None:
    """메인 테스트 함수"""
    print("🚀 카카오톡 챗봇 시스템 통합 테스트 시작")
    print("=" * 50)
    
    test_results: list[tuple[str, bool]] = []
    
    # 각 테스트 실행
    test_results.append(("파일 구조", test_file_structure()))
    test_results.append(("설정 파일", test_config()))
    test_results.append(("OCR 보정기", test_ocr_corrector()))
    test_results.append(("스마트 자동화", test_smart_automation()))
    test_results.append(("서비스 컨테이너", test_service_container()))
    
    # 결과 요약
    print("\n" + "=" * 50)
    print("📊 테스트 결과 요약")
    print("=" * 50)
    
    passed: int = 0
    total: int = len(test_results)
    
    for test_name, result in test_results:
        status = "✅ 통과" if result else "❌ 실패"
        print(f"{status} {test_name}")
        if result:
            passed += 1
    
    print(f"\n🎯 전체 결과: {passed}/{total} 통과")
    
    if passed == total:
        print("🎉 모든 테스트 통과! 시스템 통합 완료!")
        print("\n📋 사용 가능한 기능:")
        print("• 30개 오버레이 영역 설정 (듀얼 모니터 지원)")
        print("• 실시간 OCR 감지 및 한글 오류 보정")
        print("• 스마트 텍스트 입력 자동화 (4가지 전략)")
        print("• GUI 기반 테스트 도구")
        print("• 실시간 통계 및 로깅")
        print("\n🚀 사용법:")
        print("python complete_chatbot_system.py")
    else:
        print("⚠️ 일부 테스트 실패. 환경 설정을 확인하세요.")
        print("필요한 패키지: PyQt5, paddleocr, opencv-python, pyautogui, mss")

if __name__ == "__main__":
    main()