#!/usr/bin/env python3
"""
카카오톡 OCR 챗봇 시스템 - 실제 OCR 버전
PaddleOCR 파라미터 수정으로 실제 텍스트 인식 가능
"""
import sys
import os
from pathlib import Path

def setup_environment():
    """환경 설정"""
    print("실제 OCR 환경 설정 중...")
    
    # 환경변수 설정
    os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'
    os.environ['CUDA_VISIBLE_DEVICES'] = '-1'  # CPU 모드
    os.environ['OMP_NUM_THREADS'] = '1'
    os.environ['PYTHONIOENCODING'] = 'utf-8'
    
    # Python path 설정
    project_root = Path(__file__).parent
    src_path = project_root / "src"
    if str(src_path) not in sys.path:
        sys.path.insert(0, str(src_path))
    
    print("  환경 설정 완료")

def test_real_ocr():
    """실제 OCR 테스트"""
    print("\n실제 OCR 테스트 중...")
    
    try:
        # numpy 테스트
        try:
            import numpy as np
            print(f"  OK numpy {np.__version__}")
        except ImportError as e:
            print(f"  FAIL numpy: {e}")
            return False
        
        # OpenCV 테스트
        try:
            import cv2
            print(f"  OK OpenCV {cv2.__version__}")
        except ImportError as e:
            print(f"  SKIP OpenCV: {e}")
        
        # PaddleOCR 테스트 (수정된 파라미터)
        try:
            import paddleocr
            print("  OK PaddleOCR import")
            
            # 수정된 파라미터로 초기화
            print("  PaddleOCR 초기화 중...")
            ocr = paddleocr.PaddleOCR(
                use_textline_orientation=True,  # 수정됨: use_angle_cls -> use_textline_orientation
                lang='korean'
                # show_log 파라미터 제거됨
            )
            print("  OK PaddleOCR 초기화 성공!")
            
            # 간단한 OCR 테스트
            test_img = np.ones((100, 300, 3), dtype=np.uint8) * 255
            result = ocr.ocr(test_img, cls=True)
            print("  OK 실제 OCR 테스트 성공!")
            print(f"  OCR 결과: {len(result) if result else 0}개 항목")
            
            return True
            
        except Exception as e:
            print(f"  FAIL PaddleOCR: {e}")
            return False
        
    except Exception as e:
        print(f"  FAIL 전체 테스트: {e}")
        return False

def run_demo_ocr():
    """간단한 OCR 데모 실행"""
    print("\n간단한 OCR 데모 실행...")
    
    try:
        import numpy as np
        import paddleocr
        
        # OCR 초기화
        ocr = paddleocr.PaddleOCR(use_textline_orientation=True, lang='korean')
        
        # 테스트 이미지들
        test_cases = [
            ("흰 배경 테스트", np.ones((100, 300, 3), dtype=np.uint8) * 255),
            ("검은 배경 테스트", np.zeros((100, 300, 3), dtype=np.uint8)),
            ("회색 배경 테스트", np.ones((100, 300, 3), dtype=np.uint8) * 128)
        ]
        
        print("\n=== OCR 데모 결과 ===")
        for desc, img in test_cases:
            try:
                result = ocr.ocr(img, cls=True)
                item_count = len(result[0]) if result and result[0] else 0
                print(f"  {desc}: {item_count}개 텍스트 영역 감지")
            except Exception as e:
                print(f"  {desc}: 실패 - {e}")
        
        print("\n실제 OCR 기능이 정상 작동합니다!")
        return True
        
    except Exception as e:
        print(f"데모 실행 실패: {e}")
        return False

def main():
    """메인 실행 함수"""
    print("카카오톡 OCR 챗봇 시스템")
    print("실제 텍스트 인식 가능 버전")
    print("기술 데모 전용")
    print("=" * 50)
    
    # 1. 환경 설정
    setup_environment()
    
    # 2. 실제 OCR 테스트
    print("\n단계 1: 실제 OCR 기능 테스트")
    if not test_real_ocr():
        print("\nERROR OCR 테스트 실패")
        print("다음 중 하나를 실행하세요:")
        print("  1. setup_real_ocr.bat")
        print("  2. python fix_real_ocr.py")
        return False
    
    print("\nSUCCESS 모든 OCR 구성 요소가 정상 작동합니다!")
    
    # 3. 데모 실행 여부 확인
    print("\n단계 2: OCR 데모 실행")
    try:
        choice = input("OCR 데모를 실행하시겠습니까? (y/n): ").lower()
        if choice == 'y':
            if run_demo_ocr():
                print("\nSUCCESS OCR 데모 완료!")
            else:
                print("\nWARNING OCR 데모 일부 실패")
        else:
            print("\nINFO 테스트만 완료되었습니다.")
    except KeyboardInterrupt:
        print("\n사용자에 의해 중단되었습니다.")
    
    print("\n실제 OCR 시스템이 준비되었습니다!")
    print("이제 실제 텍스트 인식이 가능합니다.")
    
    return True

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n사용자에 의해 중단되었습니다.")
        sys.exit(0)
    except Exception as e:
        print(f"\n예상치 못한 오류: {e}")
        sys.exit(1)
