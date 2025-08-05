#!/usr/bin/env python3
"""간단한 OCR 테스트"""
import sys
import os
import io
import cv2

# UTF-8 설정
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# 환경 변수 설정
os.environ['PPOCR_LOG_LEVEL'] = 'ERROR'
os.environ['GLOG_minloglevel'] = '3'
os.environ['GLOG_logtostderr'] = '0'

sys.path.insert(0, 'src')

from utils.suppress_output import suppress_stdout_stderr

print("간단한 OCR 테스트 시작...")

# 샘플 이미지 로드
img_path = "screenshots/debug/sample_monitor_0_cell_0_0_141240.png"
image = cv2.imread(img_path)

if image is None:
    print("이미지를 로드할 수 없습니다!")
    sys.exit(1)

print(f"이미지 로드 완료: {image.shape}")

# PaddleOCR 직접 테스트
try:
    with suppress_stdout_stderr():
        from paddleocr import PaddleOCR
        
        # 간단한 설정으로 OCR 초기화
        ocr = PaddleOCR(
            lang='korean',
            use_angle_cls=False,
            enable_mkldnn=False
        )
        
        # OCR 수행
        result = ocr.ocr(image)
        
    print("\nOCR 결과:")
    print(f"Result type: {type(result)}")
    if result:
        print(f"Result length: {len(result)}")
        if len(result) > 0:
            print(f"First element: {result[0]}")
            print(f"First element type: {type(result[0])}")
    
    # 결과 파싱 시도
    if result and len(result) > 0:
        for item in result:
            if isinstance(item, dict) and 'res' in item:
                # 새로운 형식
                for detection in item['res']:
                    text = detection.get('text', '')
                    score = detection.get('score', 0.0)
                    print(f"  '{text}' (신뢰도: {score:.2f})")
            elif isinstance(item, list):
                # 기존 형식
                for detection in item:
                    if len(detection) >= 2 and detection[1]:
                        text = detection[1][0] if isinstance(detection[1], list) else detection[1]
                        print(f"  '{text}'")
    else:
        print("  텍스트를 찾을 수 없습니다.")
        
        # 이미지 전처리 후 재시도
        print("\n이미지 전처리 후 재시도...")
        
        # 그레이스케일 변환
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # 이미지 크기 확대
        scale = 2.0
        width = int(gray.shape[1] * scale)
        height = int(gray.shape[0] * scale)
        resized = cv2.resize(gray, (width, height), interpolation=cv2.INTER_CUBIC)
        
        # 이진화
        _, binary = cv2.threshold(resized, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        
        # 전처리된 이미지 저장
        cv2.imwrite("debug_preprocessed.png", binary)
        print("전처리된 이미지 저장: debug_preprocessed.png")
        
        with suppress_stdout_stderr():
            result2 = ocr.ocr(binary)
            
        if result2 and result2[0]:
            print("\n전처리 후 OCR 결과:")
            for idx, detection in enumerate(result2[0]):
                if detection[1]:
                    text = detection[1][0]
                    conf = detection[1][1]
                    print(f"  [{idx}] '{text}' (신뢰도: {conf:.2f})")
        else:
            print("전처리 후에도 텍스트를 찾을 수 없습니다.")
        
except Exception as e:
    print(f"OCR 오류: {e}")
    import traceback
    traceback.print_exc()