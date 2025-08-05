#!/usr/bin/env python3
"""
적응형 모니터링 시스템
- 영역별 우선순위 관리
- 동적 스캔 주기 조정
"""
import time
import threading
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import logging
from collections import deque

logger = logging.getLogger(__name__)


@dataclass
class CellActivity:
    """셀 활동 정보"""
    cell_id: str
    last_activity_time: float = 0.0
    activity_score: float = 0.0  # 0.0 ~ 1.0
    trigger_count: int = 0
    scan_interval: float = 0.3  # 기본 스캔 주기
    recent_activities: deque = None  # 최근 활동 기록
    
    def __post_init__(self):
        if self.recent_activities is None:
            self.recent_activities = deque(maxlen=10)  # 최근 10개 활동 기록


class AdaptivePriorityManager:
    """적응형 우선순위 관리자"""
    
    def __init__(self, base_interval: float = 0.3):
        self.base_interval = base_interval
        self.cell_activities: Dict[str, CellActivity] = {}
        self.lock = threading.Lock()
        
        # 스캔 주기 범위
        self.min_interval = 0.1  # 가장 활발한 채팅방: 100ms
        self.max_interval = 2.0  # 조용한 채팅방: 2초
        
        # 활동 점수 가중치
        self.recency_weight = 0.5  # 최근성
        self.frequency_weight = 0.3  # 빈도
        self.trigger_weight = 0.2  # 트리거 횟수
        
    def register_cell(self, cell_id: str):
        """셀 등록"""
        with self.lock:
            if cell_id not in self.cell_activities:
                self.cell_activities[cell_id] = CellActivity(
                    cell_id=cell_id,
                    scan_interval=self.base_interval
                )
    
    def update_activity(self, cell_id: str, had_trigger: bool = False):
        """셀 활동 업데이트"""
        with self.lock:
            if cell_id not in self.cell_activities:
                self.register_cell(cell_id)
            
            activity = self.cell_activities[cell_id]
            current_time = time.time()
            
            # 활동 기록
            activity.recent_activities.append({
                'time': current_time,
                'trigger': had_trigger
            })
            
            if had_trigger:
                activity.trigger_count += 1
                activity.last_activity_time = current_time
            
            # 활동 점수 재계산
            self._update_activity_score(activity)
            
            # 스캔 주기 조정
            self._adjust_scan_interval(activity)
    
    def _update_activity_score(self, activity: CellActivity):
        """활동 점수 계산"""
        current_time = time.time()
        
        # 1. 최근성 점수 (최근 5분 이내 활동)
        time_since_last = current_time - activity.last_activity_time
        recency_score = max(0, 1 - (time_since_last / 300))  # 5분 = 300초
        
        # 2. 빈도 점수 (최근 10개 활동 중 트리거 비율)
        if activity.recent_activities:
            trigger_count = sum(1 for a in activity.recent_activities if a['trigger'])
            frequency_score = trigger_count / len(activity.recent_activities)
        else:
            frequency_score = 0
        
        # 3. 누적 트리거 점수 (전체 트리거 횟수, 최대 100회로 정규화)
        trigger_score = min(activity.trigger_count / 100, 1.0)
        
        # 가중 평균
        activity.activity_score = (
            self.recency_weight * recency_score +
            self.frequency_weight * frequency_score +
            self.trigger_weight * trigger_score
        )
    
    def _adjust_scan_interval(self, activity: CellActivity):
        """활동 점수에 따라 스캔 주기 조정"""
        # 활동 점수가 높을수록 짧은 주기
        # 점수 0.0 → 2.0초, 점수 1.0 → 0.1초
        score = activity.activity_score
        
        # 비선형 매핑 (활발한 채팅방에 더 민감하게)
        if score > 0.7:
            # 매우 활발: 0.1 ~ 0.3초
            interval = self.min_interval + (0.2 * (1 - score) / 0.3)
        elif score > 0.3:
            # 보통: 0.3 ~ 0.8초
            interval = 0.3 + (0.5 * (0.7 - score) / 0.4)
        else:
            # 조용함: 0.8 ~ 2.0초
            interval = 0.8 + (1.2 * (0.3 - score) / 0.3)
        
        activity.scan_interval = max(self.min_interval, min(interval, self.max_interval))
        
        logger.debug(f"셀 {activity.cell_id}: 활동점수={score:.2f}, 스캔주기={activity.scan_interval:.1f}초")
    
    def get_priority_cells(self, max_count: int = 15) -> List[Tuple[str, float]]:
        """우선순위가 높은 셀 목록 반환"""
        with self.lock:
            # 활동 점수가 높은 순으로 정렬
            sorted_cells = sorted(
                self.cell_activities.items(),
                key=lambda x: x[1].activity_score,
                reverse=True
            )
            
            # 상위 N개 반환 (cell_id, scan_interval)
            return [(cell.cell_id, cell.scan_interval) 
                    for _, cell in sorted_cells[:max_count]]
    
    def should_scan_cell(self, cell_id: str) -> bool:
        """해당 셀을 지금 스캔해야 하는지 확인"""
        with self.lock:
            if cell_id not in self.cell_activities:
                return True  # 새 셀은 항상 스캔
            
            activity = self.cell_activities[cell_id]
            current_time = time.time()
            
            # 마지막 스캔 시간 확인
            if not hasattr(activity, 'last_scan_time'):
                activity.last_scan_time = 0
            
            # 스캔 주기가 지났는지 확인
            if current_time - activity.last_scan_time >= activity.scan_interval:
                activity.last_scan_time = current_time
                return True
            
            return False
    
    def get_statistics(self) -> Dict:
        """통계 정보 반환"""
        with self.lock:
            active_cells = sum(1 for a in self.cell_activities.values() 
                             if a.activity_score > 0.5)
            quiet_cells = sum(1 for a in self.cell_activities.values() 
                            if a.activity_score < 0.2)
            
            avg_interval = sum(a.scan_interval for a in self.cell_activities.values()) / len(self.cell_activities) if self.cell_activities else 0
            
            return {
                'total_cells': len(self.cell_activities),
                'active_cells': active_cells,
                'quiet_cells': quiet_cells,
                'average_interval': avg_interval,
                'min_interval': min(a.scan_interval for a in self.cell_activities.values()) if self.cell_activities else 0,
                'max_interval': max(a.scan_interval for a in self.cell_activities.values()) if self.cell_activities else 0
            }


class AdaptiveMonitoringStrategy:
    """적응형 모니터링 전략"""
    
    def __init__(self, priority_manager: AdaptivePriorityManager):
        self.priority_manager = priority_manager
        self.last_full_scan = 0
        self.full_scan_interval = 10.0  # 10초마다 전체 스캔
        
    def get_cells_to_scan(self, all_cells: List[str], max_batch: int = 15) -> List[str]:
        """이번 사이클에 스캔할 셀 선택"""
        current_time = time.time()
        cells_to_scan = []
        
        # 전체 스캔 시간인지 확인
        if current_time - self.last_full_scan > self.full_scan_interval:
            self.last_full_scan = current_time
            # 전체 스캔 시에도 우선순위 순으로
            priority_cells = self.priority_manager.get_priority_cells(len(all_cells))
            return [cell_id for cell_id, _ in priority_cells]
        
        # 각 셀의 스캔 필요성 확인
        for cell_id in all_cells:
            if self.priority_manager.should_scan_cell(cell_id):
                cells_to_scan.append(cell_id)
                
                if len(cells_to_scan) >= max_batch:
                    break
        
        return cells_to_scan
    
    def report_results(self, cell_results: Dict[str, bool]):
        """스캔 결과 보고 (트리거 발생 여부)"""
        for cell_id, had_trigger in cell_results.items():
            self.priority_manager.update_activity(cell_id, had_trigger)