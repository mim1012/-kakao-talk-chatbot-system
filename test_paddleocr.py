#!/usr/bin/env python3
"""
PaddleOCR 설치 및 작동 테스트
"""
import sys
import os
import io
from pathlib import Path

# UTF-8 encoding
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# src 디렉토리를 Python 경로에 추가
script_dir = Path(__file__).parent.absolute()
src_path = script_dir / "src"
if src_path.exists():
    sys.path.insert(0, str(src_path))
    print(f"✅ src 경로 추가: {src_path}")

print("=" * 60)
print("PaddleOCR 설치 상태 확인")
print("=" * 60)

# 1. 패키지 설치 확인
print("\n1. 패키지 설치 상태:")
print("-" * 40)

try:
    import paddle
    print(f"✅ PaddlePaddle 설치됨: {paddle.__version__}")
except ImportError as e:
    print(f"❌ PaddlePaddle 설치 안됨: {e}")

try:
    import paddleocr
    print(f"✅ PaddleOCR 설치됨: {paddleocr.__version__}")
except ImportError as e:
    print(f"❌ PaddleOCR 설치 안됨: {e}")

# 2. PaddleOCR 클래스 import 테스트
print("\n2. PaddleOCR 클래스 import 테스트:")
print("-" * 40)

try:
    from paddleocr import PaddleOCR
    print("✅ PaddleOCR 클래스 import 성공")
    PADDLEOCR_AVAILABLE = True
except ImportError as e:
    print(f"❌ PaddleOCR 클래스 import 실패: {e}")
    PADDLEOCR_AVAILABLE = False
except Exception as e:
    print(f"❌ 예상치 못한 오류: {e}")
    PADDLEOCR_AVAILABLE = False

# 3. PaddleOCR 초기화 테스트
if PADDLEOCR_AVAILABLE:
    print("\n3. PaddleOCR 초기화 테스트:")
    print("-" * 40)
    
    try:
        # 로그 억제
        os.environ['PPOCR_LOG_LEVEL'] = 'ERROR'
        os.environ['GLOG_minloglevel'] = '3'
        
        print("초기화 중... (첫 실행시 모델 다운로드로 시간이 걸릴 수 있습니다)")
        
        # PaddleOCR 초기화
        ocr = PaddleOCR(
            lang='korean',
            use_gpu=False,
            show_log=False
        )
        
        print("✅ PaddleOCR 초기화 성공")
        
        # 간단한 테스트 이미지로 OCR 테스트
        import numpy as np
        test_image = np.ones((100, 300, 3), dtype=np.uint8) * 255
        
        print("\n4. OCR 기능 테스트:")
        print("-" * 40)
        
        result = ocr.ocr(test_image)
        print("✅ OCR 실행 성공")
        
        if result:
            print(f"   결과 타입: {type(result)}")
            print(f"   결과 길이: {len(result)}")
        
    except Exception as e:
        print(f"❌ PaddleOCR 초기화/실행 실패: {e}")
        import traceback
        traceback.print_exc()

# 4. 프로젝트 코드에서 import 테스트
print("\n5. 프로젝트 모듈에서 import 테스트:")
print("-" * 40)

try:
    # suppress_output 모듈 테스트
    from utils.suppress_output import suppress_stdout_stderr
    print("✅ suppress_output 모듈 import 성공")
except ImportError as e:
    print(f"❌ suppress_output 모듈 import 실패: {e}")

try:
    # optimized_ocr_service 모듈 테스트
    from ocr.optimized_ocr_service import OptimizedOCRService, PADDLEOCR_AVAILABLE
    print(f"✅ OptimizedOCRService 모듈 import 성공")
    print(f"   PADDLEOCR_AVAILABLE = {PADDLEOCR_AVAILABLE}")
except ImportError as e:
    print(f"❌ OptimizedOCRService 모듈 import 실패: {e}")
    import traceback
    traceback.print_exc()

# 5. 의존성 확인
print("\n6. 관련 의존성 확인:")
print("-" * 40)

dependencies = [
    'numpy',
    'cv2',
    'PIL',
    'shapely',
    'pyclipper',
    'imgaug'
]

for dep in dependencies:
    try:
        module = __import__(dep)
        version = getattr(module, '__version__', 'unknown')
        print(f"✅ {dep}: {version}")
    except ImportError:
        print(f"⚠️ {dep}: 설치 안됨")

# 6. 해결 방법 제안
print("\n" + "=" * 60)
print("진단 결과 및 해결 방법")
print("=" * 60)

if not PADDLEOCR_AVAILABLE:
    print("\n❌ PaddleOCR을 사용할 수 없습니다.")
    print("\n해결 방법:")
    print("1. PaddleOCR 재설치:")
    print("   pip uninstall paddleocr paddlepaddle -y")
    print("   pip install paddlepaddle==2.5.2")
    print("   pip install paddleocr==2.7.0.3")
    print("\n2. Python 3.11 사용 권장:")
    print("   Python 3.13은 호환성 문제가 있을 수 있습니다.")
    print("\n3. 의존성 설치:")
    print("   pip install shapely pyclipper imgaug")
else:
    print("\n✅ PaddleOCR이 정상적으로 작동합니다!")
    print("\n참고사항:")
    print("- 첫 실행시 모델 다운로드로 시간이 걸릴 수 있습니다.")
    print("- GPU를 사용하려면 CUDA 설치가 필요합니다.")
    print("- 한글 OCR은 'lang=korean' 옵션이 필요합니다.")