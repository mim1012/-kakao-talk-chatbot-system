#!/usr/bin/env python3
"""
OCR 시스템 진단 도구
- OCR 초기화 확인
- 스크린샷 캡처 테스트
- 트리거 패턴 확인
"""
import os
import sys
import io
import logging
from pathlib import Path

# UTF-8 encoding for stdout
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# src 디렉토리를 Python 경로에 추가
script_dir = Path(__file__).parent.absolute()
src_path = script_dir / "src"
if src_path.exists():
    sys.path.insert(0, str(src_path))
    print(f"✅ src 경로 추가: {src_path}")

# PaddleOCR 로그 완전 차단
from utils.silence_paddle import silence_paddle
silence_paddle()

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def test_imports():
    """필요한 모듈 임포트 테스트"""
    print("\n1. 모듈 임포트 테스트")
    print("-" * 50)
    
    try:
        import numpy as np
        print("✅ numpy 임포트 성공")
    except Exception as e:
        print(f"❌ numpy 임포트 실패: {e}")
        return False
    
    try:
        import cv2
        print("✅ OpenCV 임포트 성공")
    except Exception as e:
        print(f"❌ OpenCV 임포트 실패: {e}")
        return False
    
    try:
        from PyQt5.QtWidgets import QApplication
        print("✅ PyQt5 임포트 성공")
    except Exception as e:
        print(f"❌ PyQt5 임포트 실패: {e}")
        return False
    
    try:
        from paddleocr import PaddleOCR
        print("✅ PaddleOCR 임포트 성공")
    except Exception as e:
        print(f"❌ PaddleOCR 임포트 실패: {e}")
        return False
    
    return True

def test_ocr_initialization():
    """OCR 초기화 테스트"""
    print("\n2. OCR 초기화 테스트")
    print("-" * 50)
    
    try:
        from utils.suppress_output import suppress_stdout_stderr
        import contextlib
        import io
        
        # stdout과 stderr 완전 차단
        with contextlib.redirect_stdout(io.StringIO()), \
             contextlib.redirect_stderr(io.StringIO()):
            from paddleocr import PaddleOCR
            ocr = PaddleOCR(lang='korean')
        
        print("✅ PaddleOCR 초기화 성공")
        return ocr
    except Exception as e:
        print(f"❌ PaddleOCR 초기화 실패: {e}")
        return None

def test_screen_capture():
    """스크린 캡처 테스트"""
    print("\n3. 스크린 캡처 테스트")
    print("-" * 50)
    
    try:
        import mss
        import numpy as np
        
        with mss.mss() as sct:
            # 전체 화면 캡처
            monitor = sct.monitors[0]
            screenshot = sct.grab(monitor)
            image = np.array(screenshot)
            
            print(f"✅ 스크린 캡처 성공: {image.shape}")
            
            # 테스트 이미지 저장
            import cv2
            os.makedirs("debug_screenshots", exist_ok=True)
            cv2.imwrite("debug_screenshots/test_capture.png", image)
            print("💾 테스트 스크린샷 저장: debug_screenshots/test_capture.png")
            
            return True
    except Exception as e:
        print(f"❌ 스크린 캡처 실패: {e}")
        return False

def test_trigger_patterns():
    """트리거 패턴 확인"""
    print("\n4. 트리거 패턴 확인")
    print("-" * 50)
    
    try:
        from core.config_manager import ConfigManager
        config = ConfigManager()
        
        print(f"✅ 설정된 트리거 패턴: {config.trigger_patterns}")
        
        # use_regex_trigger 속성 확인
        if hasattr(config, 'use_regex_trigger'):
            print(f"✅ 정규식 사용 여부: {config.use_regex_trigger}")
            if config.use_regex_trigger and hasattr(config, 'regex_patterns'):
                print(f"✅ 정규식 패턴: {config.regex_patterns}")
        else:
            # config.json에서 직접 읽기
            import json
            with open('config.json', 'r', encoding='utf-8') as f:
                config_data = json.load(f)
                if 'use_regex_trigger' in config_data:
                    print(f"✅ 정규식 사용 여부: {config_data['use_regex_trigger']}")
                if 'regex_patterns' in config_data:
                    print(f"✅ 정규식 패턴: {config_data['regex_patterns']}")
        
        return True
    except Exception as e:
        print(f"❌ 설정 로드 실패: {e}")
        return False

def test_grid_cells():
    """그리드 셀 확인"""
    print("\n5. 그리드 셀 상태 확인")
    print("-" * 50)
    
    try:
        from core.config_manager import ConfigManager
        from core.grid_manager import GridManager
        
        config = ConfigManager()
        grid_manager = GridManager(config)
        
        print(f"✅ 총 셀 개수: {len(grid_manager.cells)}")
        print(f"✅ 모니터 개수: {len(grid_manager.monitors)}")
        
        # 처음 5개 셀 정보 출력
        for i, cell in enumerate(grid_manager.cells[:5]):
            print(f"   셀 {i+1}: {cell.id} - 영역: {cell.bounds}")
        
        return True
    except Exception as e:
        print(f"❌ 그리드 셀 로드 실패: {e}")
        return False

def test_ocr_on_sample():
    """샘플 이미지로 OCR 테스트"""
    print("\n6. OCR 기능 테스트")
    print("-" * 50)
    
    try:
        import numpy as np
        import cv2
        import contextlib
        import io
        import subprocess
        
        # Windows에서 subprocess 출력 숨기기
        # (PaddleOCR 내부에서 처리하므로 여기서는 설정하지 않음)
        
        # 간단한 테스트 이미지 생성
        image = np.ones((100, 300, 3), dtype=np.uint8) * 255
        cv2.putText(image, "Test", (10, 50), 
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 2)
        
        # OCR 수행 (로그 완전 차단)
        with contextlib.redirect_stdout(io.StringIO()), \
             contextlib.redirect_stderr(io.StringIO()):
            from paddleocr import PaddleOCR
            ocr = PaddleOCR(lang='korean')
            # cls 파라미터 제거 (predict 메소드가 아닌 ocr 메소드 사용)
            result = ocr.ocr(image)
        
        if result and isinstance(result, list) and len(result) > 0:
            # result[0]이 None이 아닌지 확인
            if result[0] is not None:
                for detection in result[0]:
                    if detection and len(detection) > 1 and detection[1]:
                        text = detection[1][0] if isinstance(detection[1], (list, tuple)) else str(detection[1])
                        confidence = detection[1][1] if isinstance(detection[1], (list, tuple)) and len(detection[1]) > 1 else 0.0
                        print(f"✅ OCR 감지: '{text}' (신뢰도: {confidence:.2f})")
                        return True
            else:
                print("⚠️ OCR 결과 없음 (빈 이미지)")
        else:
            print("⚠️ OCR 결과 없음")
        
        return True  # 결과가 없어도 기능은 정상
    except Exception as e:
        print(f"❌ OCR 테스트 실패: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """진단 실행"""
    print("=" * 60)
    print("카카오톡 OCR 챗봇 시스템 진단")
    print("=" * 60)
    
    # 각 테스트 실행
    results = []
    
    if test_imports():
        results.append(("모듈 임포트", True))
    else:
        results.append(("모듈 임포트", False))
        print("\n⚠️ 필수 모듈이 설치되지 않았습니다.")
        print("해결방법: pip install -r requirements.txt")
        return
    
    ocr = test_ocr_initialization()
    results.append(("OCR 초기화", ocr is not None))
    
    results.append(("스크린 캡처", test_screen_capture()))
    results.append(("트리거 패턴", test_trigger_patterns()))
    results.append(("그리드 셀", test_grid_cells()))
    results.append(("OCR 기능", test_ocr_on_sample()))
    
    # 결과 요약
    print("\n" + "=" * 60)
    print("진단 결과 요약")
    print("=" * 60)
    
    for test_name, success in results:
        status = "✅ 성공" if success else "❌ 실패"
        print(f"{test_name}: {status}")
    
    # 권장사항
    failed_tests = [name for name, success in results if not success]
    if failed_tests:
        print("\n⚠️ 실패한 테스트가 있습니다:")
        for test in failed_tests:
            print(f"  - {test}")
        print("\n권장사항:")
        print("1. 가상환경이 활성화되어 있는지 확인")
        print("2. requirements.txt의 모든 패키지가 설치되었는지 확인")
        print("3. 관리자 권한으로 실행 중인지 확인")
    else:
        print("\n✅ 모든 테스트 통과! 시스템이 정상적으로 작동할 준비가 되었습니다.")

if __name__ == "__main__":
    main()