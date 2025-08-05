"""
import 패치 모듈
numpy, cv2 등의 import를 대체 모듈로 리다이렉트
"""
import sys
from pathlib import Path

# 현재 모듈 경로
current_dir = Path(__file__).parent

def patch_imports():
    """import 패치 적용"""
    # numpy import 패치
    try:
        import numpy
    except ImportError:
        # numpy 대체 모듈을 numpy로 등록
        from . import numpy_replacement
        sys.modules['numpy'] = numpy_replacement
        sys.modules['np'] = numpy_replacement
        print("[PATCH] numpy를 대체 모듈로 패치")
    except Exception as e:
        print(f"[PATCH] numpy DLL 오류로 인한 대체 모듈 사용: {e}")
        from . import numpy_replacement
        sys.modules['numpy'] = numpy_replacement
        sys.modules['np'] = numpy_replacement
    
    # cv2 import 패치
    try:
        import cv2
    except ImportError:
        from . import opencv_replacement
        sys.modules['cv2'] = opencv_replacement
        print("[PATCH] cv2를 대체 모듈로 패치")
    except Exception as e:
        print(f"[PATCH] cv2 오류로 인한 대체 모듈 사용: {e}")
        from . import opencv_replacement
        sys.modules['cv2'] = opencv_replacement

# 자동 패치 적용
patch_imports()
