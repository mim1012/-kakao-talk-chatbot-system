#!/usr/bin/env python3
"""
변화 감지 기반 모니터링
이미지 변화가 있을 때만 OCR 실행하여 성능 최적화
"""
import cv2
import numpy as np
import time
from typing import Dict, Optional, Tuple
import logging

logger = logging.getLogger(__name__)


class ChangeDetectionMonitor:
    """이미지 변화 감지를 통한 OCR 최적화"""
    
    def __init__(self, change_threshold: float = 0.05):
        """
        Args:
            change_threshold: 변화 감지 임계값 (0.0 ~ 1.0, 기본값 5%)
        """
        self.change_threshold = change_threshold
        self.previous_images: Dict[str, np.ndarray] = {}
        self.last_change_time: Dict[str, float] = {}
        self.skip_count = 0
        self.total_checks = 0
        self.is_initialized: Dict[str, bool] = {}  # 각 셀의 초기화 상태 추적
        
    def has_changed(self, cell_id: str, current_image: np.ndarray) -> bool:
        """
        이미지에 의미있는 변화가 있는지 확인
        
        Args:
            cell_id: 셀 식별자
            current_image: 현재 캡처된 이미지
            
        Returns:
            bool: 변화가 감지되면 True
        """
        self.total_checks += 1
        
        # 첫 번째 캡처는 항상 변화로 간주 (초기 OCR 처리를 위해)
        if cell_id not in self.previous_images:
            self.previous_images[cell_id] = current_image.copy()
            self.last_change_time[cell_id] = time.time()
            self.is_initialized[cell_id] = True  # 초기화 완료 표시
            logger.info(f"셀 {cell_id}: 초기 OCR 처리를 위해 변화로 간주")
            return True
            
        try:
            previous = self.previous_images[cell_id]
            
            # 이미지 크기가 다르면 변화로 간주
            if previous.shape != current_image.shape:
                self.previous_images[cell_id] = current_image.copy()
                self.last_change_time[cell_id] = time.time()
                return True
            
            # 그레이스케일로 변환하여 비교
            if len(current_image.shape) == 3:
                current_gray = cv2.cvtColor(current_image, cv2.COLOR_BGR2GRAY)
                previous_gray = cv2.cvtColor(previous, cv2.COLOR_BGR2GRAY)
            else:
                current_gray = current_image
                previous_gray = previous
                
            # 픽셀 차이 계산
            diff = cv2.absdiff(current_gray, previous_gray)
            
            # 노이즈 제거를 위한 임계값 적용 (30 이상 차이나는 픽셀만 카운트)
            _, thresh = cv2.threshold(diff, 30, 255, cv2.THRESH_BINARY)
            
            # 변화된 픽셀 비율 계산
            changed_pixels = np.sum(thresh > 0)
            total_pixels = thresh.size
            change_ratio = changed_pixels / total_pixels
            
            # 변화 감지
            has_change = change_ratio > self.change_threshold
            
            if has_change:
                # 변화가 있으면 이미지 업데이트
                self.previous_images[cell_id] = current_image.copy()
                self.last_change_time[cell_id] = time.time()
                logger.debug(f"셀 {cell_id}: 변화 감지됨 ({change_ratio:.1%})")
            else:
                self.skip_count += 1
                
            return has_change
            
        except Exception as e:
            logger.error(f"변화 감지 중 오류: {e}")
            # 오류 발생 시 안전하게 변화로 간주
            return True
    
    def get_change_region(self, cell_id: str, current_image: np.ndarray) -> Optional[Tuple[int, int, int, int]]:
        """
        변화가 발생한 영역의 좌표 반환 (향후 부분 OCR용)
        
        Returns:
            tuple: (x, y, width, height) 또는 None
        """
        if cell_id not in self.previous_images:
            return None
            
        try:
            previous = self.previous_images[cell_id]
            
            # 그레이스케일 변환
            if len(current_image.shape) == 3:
                current_gray = cv2.cvtColor(current_image, cv2.COLOR_BGR2GRAY)
                previous_gray = cv2.cvtColor(previous, cv2.COLOR_BGR2GRAY)
            else:
                current_gray = current_image
                previous_gray = previous
                
            # 차이 계산
            diff = cv2.absdiff(current_gray, previous_gray)
            _, thresh = cv2.threshold(diff, 30, 255, cv2.THRESH_BINARY)
            
            # 변화 영역 찾기
            contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            if contours:
                # 가장 큰 변화 영역 찾기
                largest_contour = max(contours, key=cv2.contourArea)
                x, y, w, h = cv2.boundingRect(largest_contour)
                return (x, y, w, h)
                
        except Exception as e:
            logger.error(f"변화 영역 감지 중 오류: {e}")
            
        return None
    
    def clear_history(self, cell_id: Optional[str] = None):
        """
        저장된 이미지 히스토리 삭제
        
        Args:
            cell_id: 특정 셀만 삭제하려면 지정, None이면 전체 삭제
        """
        if cell_id:
            self.previous_images.pop(cell_id, None)
            self.last_change_time.pop(cell_id, None)
            self.is_initialized.pop(cell_id, None)
        else:
            self.previous_images.clear()
            self.last_change_time.clear()
            self.is_initialized.clear()
    
    def get_statistics(self) -> Dict[str, float]:
        """
        변화 감지 통계 반환
        """
        skip_ratio = self.skip_count / self.total_checks if self.total_checks > 0 else 0
        
        return {
            "total_checks": self.total_checks,
            "skipped_ocr": self.skip_count,
            "skip_ratio": skip_ratio,
            "efficiency_gain": skip_ratio * 100,  # 퍼센트로 표시
            "active_cells": len(self.previous_images),
            "initialized_cells": len(self.is_initialized)
        }
    
    def get_cell_idle_time(self, cell_id: str) -> float:
        """
        특정 셀의 마지막 변화 이후 경과 시간
        """
        if cell_id in self.last_change_time:
            return time.time() - self.last_change_time[cell_id]
        return 0.0
    
    def is_cell_initialized(self, cell_id: str) -> bool:
        """
        특정 셀이 초기 OCR 처리를 완료했는지 확인
        """
        return self.is_initialized.get(cell_id, False)
    
    def get_uninitialized_cells(self, all_cell_ids: list[str]) -> list[str]:
        """
        아직 초기화되지 않은 셀 ID 목록 반환
        """
        return [cell_id for cell_id in all_cell_ids if not self.is_cell_initialized(cell_id)]


class AdaptiveChangeDetector:
    """
    적응형 변화 감지기
    셀별로 다른 임계값을 동적으로 조정
    """
    
    def __init__(self):
        self.detectors: Dict[str, ChangeDetectionMonitor] = {}
        self.cell_activity: Dict[str, float] = {}  # 셀별 활동 수준
        
    def get_detector(self, cell_id: str) -> ChangeDetectionMonitor:
        """
        셀별 전용 감지기 반환
        """
        if cell_id not in self.detectors:
            # 초기 임계값은 표준값으로
            self.detectors[cell_id] = ChangeDetectionMonitor(change_threshold=0.05)
            self.cell_activity[cell_id] = 0.5
            
        return self.detectors[cell_id]
    
    def update_threshold(self, cell_id: str, had_trigger: bool):
        """
        트리거 결과에 따라 임계값 동적 조정
        
        Args:
            cell_id: 셀 식별자
            had_trigger: 실제로 "들어왔습니다"가 감지되었는지 여부
        """
        if cell_id not in self.cell_activity:
            return
            
        # 활동 수준 업데이트 (지수 이동 평균)
        alpha = 0.1
        self.cell_activity[cell_id] = (alpha * float(had_trigger) + 
                                       (1 - alpha) * self.cell_activity[cell_id])
        
        # 활동 수준에 따라 임계값 조정
        # 활동이 많으면 민감하게, 적으면 둔감하게
        activity_level = self.cell_activity[cell_id]
        
        if activity_level > 0.7:
            # 활발한 채팅방 - 더 민감하게
            new_threshold = 0.03
        elif activity_level < 0.3:
            # 조용한 채팅방 - 덜 민감하게
            new_threshold = 0.08
        else:
            # 보통 채팅방
            new_threshold = 0.05
            
        self.detectors[cell_id].change_threshold = new_threshold
        logger.debug(f"셀 {cell_id}: 임계값 조정 {new_threshold:.2%} (활동도: {activity_level:.2f})")