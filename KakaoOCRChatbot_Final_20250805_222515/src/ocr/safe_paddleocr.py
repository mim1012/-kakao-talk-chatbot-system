"""
안전한 PaddleOCR 초기화 - Python 3.11 호환성 문제 해결
"""
import os
import sys
import warnings
import numpy as np

# 환경 변수 설정
os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'
os.environ['OMP_NUM_THREADS'] = '1'
os.environ['OPENBLAS_NUM_THREADS'] = '1'
os.environ['MKL_NUM_THREADS'] = '1'
os.environ['VECLIB_MAXIMUM_THREADS'] = '1'
os.environ['NUMEXPR_NUM_THREADS'] = '1'

# numpy 경고 무시
warnings.filterwarnings('ignore', category=UserWarning)
warnings.filterwarnings('ignore', category=FutureWarning)

def create_safe_paddleocr():
    """안전한 PaddleOCR 인스턴스 생성"""
    try:
        from paddleocr import PaddleOCR
        
        # 새로운 PaddleOCR 버전에 맞춘 간단한 설정
        ocr_instance = PaddleOCR(
            lang='korean',
            use_angle_cls=False,  # 각도 분류기 비활성화
            enable_mkldnn=False  # MKLDNN 비활성화 (Tensor 오류 방지)
        )
        
        print("✅ 안전한 PaddleOCR 인스턴스 생성 완료")
        return ocr_instance
        
    except Exception as e:
        print(f"❌ PaddleOCR 초기화 실패: {e}")
        
        # 대체 방법 시도
        try:
            # 최소 설정으로 재시도
            ocr_instance = PaddleOCR(
                lang='korean',
                use_angle_cls=False,
                enable_mkldnn=False,
                use_mp=False
            )
            print("✅ 기본 설정으로 PaddleOCR 초기화 성공")
            return ocr_instance
        except:
            return None