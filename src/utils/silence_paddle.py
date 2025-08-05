"""
PaddleOCR 로그를 완전히 차단하는 유틸리티
"""
import os
import sys
import logging

def silence_paddle():
    """PaddleOCR의 모든 출력을 차단"""
    
    # 환경 변수 설정
    os.environ['GLOG_v'] = '0'
    os.environ['GLOG_logtostderr'] = '0'
    os.environ['GLOG_minloglevel'] = '3'
    os.environ['FLAGS_logtostderr'] = '0'
    os.environ['FLAGS_minloglevel'] = '3'
    os.environ['FLAGS_v'] = '0'
    
    # PaddleOCR 관련 환경 변수
    os.environ['PPOCR_LOG_LEVEL'] = 'ERROR'
    os.environ['PADDLEX_LOG_LEVEL'] = 'ERROR'
    os.environ['PADDLE_LOG_LEVEL'] = 'ERROR'
    os.environ['PADDLEOCR_SHOW_PROGRESS'] = '0'
    os.environ['PADDLEX_SHOW_PROGRESS'] = '0'
    os.environ['TQDM_DISABLE'] = '1'
    
    # Windows 특정 설정
    if sys.platform == 'win32':
        os.environ['GLOG_log_dir'] = 'NUL'
        # subprocess.STARTUPINFO를 재정의하면 문제가 발생하므로 제거
    
    # 로깅 레벨 설정
    logging.getLogger('paddle').setLevel(logging.ERROR)
    logging.getLogger('paddleocr').setLevel(logging.ERROR)
    logging.getLogger('paddlex').setLevel(logging.ERROR)
    logging.getLogger('ppocr').setLevel(logging.ERROR)
    
    # 경고 무시
    import warnings
    warnings.filterwarnings('ignore')