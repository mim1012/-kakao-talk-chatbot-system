#!/usr/bin/env python3
"""
변화 감지 기능 테스트
"""
import numpy as np
import cv2
import time
from src.monitoring.change_detection import ChangeDetectionMonitor

def create_test_image(text="", bg_color=(255, 255, 255)):
    """테스트 이미지 생성"""
    img = np.full((100, 300, 3), bg_color, dtype=np.uint8)
    
    if text:
        font = cv2.FONT_HERSHEY_SIMPLEX
        cv2.putText(img, text, (10, 50), font, 0.5, (0, 0, 0), 1, cv2.LINE_AA)
    
    return img

def test_change_detection():
    """변화 감지 테스트"""
    print("=== 변화 감지 테스트 시작 ===\n")
    
    # 변화 감지기 생성
    detector = ChangeDetectionMonitor(change_threshold=0.05)
    
    # 테스트 1: 첫 번째 이미지는 항상 변화로 감지
    print("테스트 1: 첫 번째 이미지")
    img1 = create_test_image("안녕하세요")
    result = detector.has_changed("cell_1", img1)
    print(f"  결과: {'변화 감지' if result else '변화 없음'} (예상: 변화 감지)")
    
    # 테스트 2: 동일한 이미지는 변화 없음
    print("\n테스트 2: 동일한 이미지")
    img2 = create_test_image("안녕하세요")
    result = detector.has_changed("cell_1", img2)
    print(f"  결과: {'변화 감지' if result else '변화 없음'} (예상: 변화 없음)")
    
    # 테스트 3: 다른 텍스트는 변화 감지
    print("\n테스트 3: 다른 텍스트")
    img3 = create_test_image("들어왔습니다")
    result = detector.has_changed("cell_1", img3)
    print(f"  결과: {'변화 감지' if result else '변화 없음'} (예상: 변화 감지)")
    
    # 테스트 4: 작은 변화 (배경색 약간 변경)
    print("\n테스트 4: 작은 변화")
    img4 = create_test_image("들어왔습니다", bg_color=(250, 250, 250))
    result = detector.has_changed("cell_1", img4)
    print(f"  결과: {'변화 감지' if result else '변화 없음'} (예상: 변화 없음)")
    
    # 테스트 5: 큰 변화 (배경색 크게 변경)
    print("\n테스트 5: 큰 변화")
    img5 = create_test_image("들어왔습니다", bg_color=(100, 100, 100))
    result = detector.has_changed("cell_1", img5)
    print(f"  결과: {'변화 감지' if result else '변화 없음'} (예상: 변화 감지)")
    
    # 통계 출력
    print("\n=== 변화 감지 통계 ===")
    stats = detector.get_statistics()
    print(f"  총 체크 횟수: {stats['total_checks']}")
    print(f"  OCR 스킵 횟수: {stats['skipped_ocr']}")
    print(f"  스킵 비율: {stats['skip_ratio']:.1%}")
    print(f"  효율성 향상: {stats['efficiency_gain']:.1f}%")
    print(f"  활성 셀 수: {stats['active_cells']}")

def test_real_scenario():
    """실제 시나리오 시뮬레이션"""
    print("\n\n=== 실제 시나리오 시뮬레이션 ===")
    print("30개 채팅방, 10초간 모니터링 시뮬레이션\n")
    
    detector = ChangeDetectionMonitor(change_threshold=0.05)
    
    # 30개 셀 초기화
    cells = [f"cell_{i}" for i in range(30)]
    
    # 10번의 스캔 사이클 시뮬레이션
    total_ocr_without_detection = 0
    total_ocr_with_detection = 0
    
    for cycle in range(10):
        print(f"\n사이클 {cycle + 1}:")
        ocr_count = 0
        
        for cell_id in cells:
            # 10% 확률로 채팅방에 변화 발생
            if np.random.random() < 0.1:
                # 새 메시지가 왔다고 가정
                img = create_test_image(f"메시지 {cycle}", 
                                      bg_color=(np.random.randint(200, 255),) * 3)
            else:
                # 변화 없음
                img = create_test_image("기존 메시지", bg_color=(255, 255, 255))
            
            if detector.has_changed(cell_id, img):
                ocr_count += 1
        
        total_ocr_without_detection += 30  # 변화 감지 없이는 모든 셀 OCR
        total_ocr_with_detection += ocr_count
        
        print(f"  변화 감지로 OCR 실행: {ocr_count}/30개 셀")
        print(f"  절약된 OCR: {30 - ocr_count}개")
    
    # 최종 통계
    print("\n=== 최종 통계 ===")
    stats = detector.get_statistics()
    print(f"  변화 감지 없이 총 OCR: {total_ocr_without_detection}회")
    print(f"  변화 감지로 총 OCR: {total_ocr_with_detection}회")
    print(f"  OCR 감소율: {(1 - total_ocr_with_detection/total_ocr_without_detection):.1%}")
    print(f"  평균 스킵율: {stats['skip_ratio']:.1%}")
    print(f"  효율성 향상: {stats['efficiency_gain']:.1f}%")

if __name__ == "__main__":
    test_change_detection()
    test_real_scenario()