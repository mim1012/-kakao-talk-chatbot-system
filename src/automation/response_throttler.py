"""
응답 스팸 방지를 위한 스로틀링 및 지수 백오프
"""
import time
import threading
from typing import Dict, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


@dataclass
class ResponseRecord:
    """응답 기록"""
    cell_id: str
    last_response_time: datetime
    response_count: int
    backoff_seconds: float
    
    
class ResponseThrottler:
    """
    응답 스팸 방지 관리자
    - 채팅방별 쿨다운 관리
    - 지수 백오프 적용
    - 스팸 방지
    """
    
    def __init__(self, 
                 base_cooldown: float = 5.0,
                 max_cooldown: float = 60.0,
                 backoff_multiplier: float = 2.0):
        """
        Args:
            base_cooldown: 기본 쿨다운 시간 (초)
            max_cooldown: 최대 쿨다운 시간 (초)
            backoff_multiplier: 백오프 배수
        """
        self.base_cooldown = base_cooldown
        self.max_cooldown = max_cooldown
        self.backoff_multiplier = backoff_multiplier
        
        # 셀별 응답 기록
        self.response_records: Dict[str, ResponseRecord] = {}
        self.lock = threading.Lock()
        
        # 통계
        self.stats = {
            'total_responses': 0,
            'throttled_count': 0,
            'spam_prevented': 0
        }
    
    def can_respond(self, cell_id: str) -> bool:
        """
        해당 셀에 응답 가능한지 확인
        
        Returns:
            True if 응답 가능, False if 쿨다운 중
        """
        with self.lock:
            if cell_id not in self.response_records:
                return True
            
            record = self.response_records[cell_id]
            now = datetime.now()
            
            # 쿨다운 시간 확인
            time_since_last = (now - record.last_response_time).total_seconds()
            
            if time_since_last < record.backoff_seconds:
                self.stats['throttled_count'] += 1
                remaining = record.backoff_seconds - time_since_last
                logger.debug(f"셀 {cell_id} 쿨다운 중 (남은 시간: {remaining:.1f}초)")
                return False
            
            return True
    
    def record_response(self, cell_id: str) -> float:
        """
        응답 기록 및 다음 백오프 시간 계산
        
        Returns:
            다음 응답까지 대기 시간 (초)
        """
        with self.lock:
            now = datetime.now()
            
            if cell_id not in self.response_records:
                # 첫 응답
                self.response_records[cell_id] = ResponseRecord(
                    cell_id=cell_id,
                    last_response_time=now,
                    response_count=1,
                    backoff_seconds=self.base_cooldown
                )
                logger.info(f"셀 {cell_id} 첫 응답 기록 (쿨다운: {self.base_cooldown}초)")
                
            else:
                record = self.response_records[cell_id]
                time_since_last = (now - record.last_response_time).total_seconds()
                
                # 충분한 시간이 지났으면 백오프 리셋
                if time_since_last > self.max_cooldown * 2:
                    record.response_count = 1
                    record.backoff_seconds = self.base_cooldown
                    logger.info(f"셀 {cell_id} 백오프 리셋")
                    
                else:
                    # 지수 백오프 적용
                    record.response_count += 1
                    record.backoff_seconds = min(
                        record.backoff_seconds * self.backoff_multiplier,
                        self.max_cooldown
                    )
                    
                    # 스팸 감지
                    if record.response_count > 5 and time_since_last < 30:
                        self.stats['spam_prevented'] += 1
                        logger.warning(f"셀 {cell_id} 스팸 감지! 백오프: {record.backoff_seconds}초")
                
                record.last_response_time = now
            
            self.stats['total_responses'] += 1
            return self.response_records[cell_id].backoff_seconds
    
    def get_cooldown_remaining(self, cell_id: str) -> float:
        """
        남은 쿨다운 시간 확인
        
        Returns:
            남은 쿨다운 시간 (초), 0 if 응답 가능
        """
        with self.lock:
            if cell_id not in self.response_records:
                return 0.0
            
            record = self.response_records[cell_id]
            now = datetime.now()
            time_since_last = (now - record.last_response_time).total_seconds()
            
            remaining = max(0, record.backoff_seconds - time_since_last)
            return remaining
    
    def reset_cell(self, cell_id: str):
        """특정 셀의 스로틀 기록 리셋"""
        with self.lock:
            if cell_id in self.response_records:
                del self.response_records[cell_id]
                logger.info(f"셀 {cell_id} 스로틀 기록 리셋")
    
    def get_stats(self) -> Dict:
        """통계 반환"""
        with self.lock:
            return {
                **self.stats,
                'active_cooldowns': len(self.response_records),
                'cells_in_cooldown': list(self.response_records.keys())
            }
    
    def cleanup_old_records(self, max_age_hours: int = 24):
        """오래된 기록 정리"""
        with self.lock:
            now = datetime.now()
            cutoff_time = now - timedelta(hours=max_age_hours)
            
            to_remove = []
            for cell_id, record in self.response_records.items():
                if record.last_response_time < cutoff_time:
                    to_remove.append(cell_id)
            
            for cell_id in to_remove:
                del self.response_records[cell_id]
            
            if to_remove:
                logger.info(f"{len(to_remove)}개의 오래된 스로틀 기록 정리")


# 전역 스로틀러 인스턴스
_throttler_instance: Optional[ResponseThrottler] = None


def get_throttler() -> ResponseThrottler:
    """전역 스로틀러 인스턴스 반환"""
    global _throttler_instance
    if _throttler_instance is None:
        _throttler_instance = ResponseThrottler()
    return _throttler_instance