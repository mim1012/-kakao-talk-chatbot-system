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
        
        # 빠른 처리를 위한 최적화 설정
        ocr_instance = PaddleOCR(
            lang='korean',
            use_angle_cls=False,  # 각도 분류기 비활성화
            enable_mkldnn=False,  # MKLDNN 비활성화
            det_db_box_thresh=0.3,  # 박스 임계값 낮춤 (빠른 감지)
            rec_batch_num=1,  # 배치 크기 줄임
            max_text_length=10,  # 최대 텍스트 길이 제한
            use_gpu=False,  # GPU 비활성화 (CPU가 더 빠를 수 있음)
            det_limit_side_len=640  # 이미지 크기 제한 (빠른 처리)
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