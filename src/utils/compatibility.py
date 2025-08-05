"""
Python 3.13 호환성 모듈
"""
import os
import warnings

# 환경변수 설정
os.environ.setdefault('KMP_DUPLICATE_LIB_OK', 'TRUE')
os.environ.setdefault('CUDA_VISIBLE_DEVICES', '-1')

# 경고 억제
warnings.filterwarnings("ignore", category=DeprecationWarning)
warnings.filterwarnings("ignore", message=".*numpy.*")

def apply_all_patches():
    """모든 호환성 패치 적용"""
    pass

# 자동 적용
apply_all_patches()
