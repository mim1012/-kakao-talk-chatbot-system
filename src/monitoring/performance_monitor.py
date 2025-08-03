"""
성능 모니터링 시스템
실시간 성능 메트릭 수집 및 분석
"""
from __future__ import annotations

import time
import psutil
import threading
import queue
from collections import deque
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Callable
import logging
import json
from datetime import datetime

@dataclass
class PerformanceMetrics:
    """성능 메트릭 데이터"""
    timestamp: float
    cpu_percent: float
    memory_percent: float
    memory_mb: float
    ocr_latency_ms: Optional[float] = None
    screen_capture_ms: Optional[float] = None
    automation_latency_ms: Optional[float] = None
    detection_count: int = 0
    automation_count: int = 0
    active_threads: int = 0
    queue_size: int = 0

@dataclass
class PerformanceStats:
    """성능 통계"""
    avg_cpu: float = 0.0
    avg_memory: float = 0.0
    avg_ocr_latency: float = 0.0
    avg_capture_latency: float = 0.0
    total_detections: int = 0
    total_automations: int = 0
    uptime_seconds: float = 0.0
    peak_memory_mb: float = 0.0
    peak_cpu_percent: float = 0.0

class PerformanceMonitor:
    """실시간 성능 모니터링 클래스"""
    
    def __init__(self, sample_interval: float = 1.0, history_size: int = 300):
        """
        Args:
            sample_interval: 샘플링 간격 (초)
            history_size: 히스토리 크기 (최근 N개 샘플 저장)
        """
        self.sample_interval = sample_interval
        self.history_size = history_size
        self.logger = logging.getLogger(__name__)
        
        # 메트릭 히스토리
        self.metrics_history: deque[PerformanceMetrics] = deque(maxlen=history_size)
        
        # 실시간 카운터
        self._detection_counter = 0
        self._automation_counter = 0
        self._start_time = time.time()
        
        # 레이턴시 추적
        self._ocr_latencies: deque[float] = deque(maxlen=100)
        self._capture_latencies: deque[float] = deque(maxlen=100)
        self._automation_latencies: deque[float] = deque(maxlen=100)
        
        # 모니터링 스레드
        self._monitoring_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        
        # 콜백 함수들
        self._callbacks: List[Callable[[PerformanceMetrics], None]] = []
        
        # 프로세스 정보
        self._process = psutil.Process()
        
    def start(self):
        """모니터링 시작"""
        if self._monitoring_thread and self._monitoring_thread.is_alive():
            self.logger.warning("성능 모니터가 이미 실행 중입니다")
            return
        
        self._stop_event.clear()
        self._monitoring_thread = threading.Thread(
            target=self._monitoring_loop,
            name="PerformanceMonitor",
            daemon=True
        )
        self._monitoring_thread.start()
        self.logger.info("성능 모니터링 시작")
    
    def stop(self):
        """모니터링 중지"""
        self._stop_event.set()
        if self._monitoring_thread:
            self._monitoring_thread.join(timeout=2.0)
        self.logger.info("성능 모니터링 중지")
    
    def _monitoring_loop(self):
        """모니터링 루프"""
        while not self._stop_event.is_set():
            try:
                # 성능 메트릭 수집
                metrics = self._collect_metrics()
                
                # 히스토리에 추가
                self.metrics_history.append(metrics)
                
                # 콜백 실행
                for callback in self._callbacks:
                    try:
                        callback(metrics)
                    except Exception as e:
                        self.logger.error(f"콜백 실행 오류: {e}")
                
                # 다음 샘플까지 대기
                self._stop_event.wait(self.sample_interval)
                
            except Exception as e:
                self.logger.error(f"모니터링 루프 오류: {e}")
    
    def _collect_metrics(self) -> PerformanceMetrics:
        """현재 성능 메트릭 수집"""
        # CPU 및 메모리 정보
        cpu_percent = self._process.cpu_percent(interval=0.1)
        memory_info = self._process.memory_info()
        memory_percent = self._process.memory_percent()
        memory_mb = memory_info.rss / 1024 / 1024
        
        # 평균 레이턴시 계산
        avg_ocr_latency = sum(self._ocr_latencies) / len(self._ocr_latencies) if self._ocr_latencies else None
        avg_capture_latency = sum(self._capture_latencies) / len(self._capture_latencies) if self._capture_latencies else None
        avg_automation_latency = sum(self._automation_latencies) / len(self._automation_latencies) if self._automation_latencies else None
        
        # 활성 스레드 수
        active_threads = threading.active_count()
        
        return PerformanceMetrics(
            timestamp=time.time(),
            cpu_percent=cpu_percent,
            memory_percent=memory_percent,
            memory_mb=memory_mb,
            ocr_latency_ms=avg_ocr_latency,
            screen_capture_ms=avg_capture_latency,
            automation_latency_ms=avg_automation_latency,
            detection_count=self._detection_counter,
            automation_count=self._automation_counter,
            active_threads=active_threads,
            queue_size=0  # 큐 크기는 외부에서 설정
        )
    
    def record_ocr_latency(self, latency_ms: float):
        """OCR 레이턴시 기록"""
        self._ocr_latencies.append(latency_ms)
    
    def record_capture_latency(self, latency_ms: float):
        """스크린 캡처 레이턴시 기록"""
        self._capture_latencies.append(latency_ms)
    
    def record_automation_latency(self, latency_ms: float):
        """자동화 레이턴시 기록"""
        self._automation_latencies.append(latency_ms)
    
    def increment_detection_count(self):
        """감지 카운트 증가"""
        self._detection_counter += 1
    
    def increment_automation_count(self):
        """자동화 카운트 증가"""
        self._automation_counter += 1
    
    def set_queue_size(self, size: int):
        """큐 크기 설정"""
        if self.metrics_history:
            self.metrics_history[-1].queue_size = size
    
    def get_current_stats(self) -> PerformanceStats:
        """현재 통계 반환"""
        if not self.metrics_history:
            return PerformanceStats()
        
        # 최근 메트릭들로 통계 계산
        recent_metrics = list(self.metrics_history)
        
        cpu_values = [m.cpu_percent for m in recent_metrics]
        memory_values = [m.memory_mb for m in recent_metrics]
        ocr_latencies = [m.ocr_latency_ms for m in recent_metrics if m.ocr_latency_ms]
        capture_latencies = [m.screen_capture_ms for m in recent_metrics if m.screen_capture_ms]
        
        return PerformanceStats(
            avg_cpu=sum(cpu_values) / len(cpu_values) if cpu_values else 0,
            avg_memory=sum(memory_values) / len(memory_values) if memory_values else 0,
            avg_ocr_latency=sum(ocr_latencies) / len(ocr_latencies) if ocr_latencies else 0,
            avg_capture_latency=sum(capture_latencies) / len(capture_latencies) if capture_latencies else 0,
            total_detections=self._detection_counter,
            total_automations=self._automation_counter,
            uptime_seconds=time.time() - self._start_time,
            peak_memory_mb=max(memory_values) if memory_values else 0,
            peak_cpu_percent=max(cpu_values) if cpu_values else 0
        )
    
    def get_metrics_history(self, last_n: Optional[int] = None) -> List[PerformanceMetrics]:
        """메트릭 히스토리 반환"""
        if last_n:
            return list(self.metrics_history)[-last_n:]
        return list(self.metrics_history)
    
    def add_callback(self, callback: Callable[[PerformanceMetrics], None]):
        """메트릭 업데이트 콜백 추가"""
        self._callbacks.append(callback)
    
    def remove_callback(self, callback: Callable[[PerformanceMetrics], None]):
        """콜백 제거"""
        if callback in self._callbacks:
            self._callbacks.remove(callback)
    
    def export_metrics(self, filepath: str):
        """메트릭을 JSON 파일로 내보내기"""
        try:
            metrics_data = [
                {
                    'timestamp': m.timestamp,
                    'cpu_percent': m.cpu_percent,
                    'memory_mb': m.memory_mb,
                    'ocr_latency_ms': m.ocr_latency_ms,
                    'detection_count': m.detection_count,
                    'automation_count': m.automation_count
                }
                for m in self.metrics_history
            ]
            
            stats = self.get_current_stats()
            
            export_data = {
                'export_time': datetime.now().isoformat(),
                'stats': {
                    'avg_cpu': stats.avg_cpu,
                    'avg_memory': stats.avg_memory,
                    'avg_ocr_latency': stats.avg_ocr_latency,
                    'total_detections': stats.total_detections,
                    'total_automations': stats.total_automations,
                    'uptime_seconds': stats.uptime_seconds
                },
                'metrics': metrics_data
            }
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"메트릭 내보내기 완료: {filepath}")
            
        except Exception as e:
            self.logger.error(f"메트릭 내보내기 실패: {e}")

class PerformanceOptimizer:
    """성능 최적화 관리자"""
    
    def __init__(self, monitor: PerformanceMonitor):
        self.monitor = monitor
        self.logger = logging.getLogger(__name__)
        
        # 최적화 임계값
        self.cpu_threshold = 80.0  # CPU 사용률 80% 이상
        self.memory_threshold = 1024  # 메모리 1GB 이상
        self.latency_threshold = 100  # 레이턴시 100ms 이상
        
        # 최적화 상태
        self.optimization_active = False
        self.reduced_batch_size = False
        self.reduced_ocr_workers = False
        
    def analyze_and_optimize(self, metrics: PerformanceMetrics):
        """성능 분석 및 최적화"""
        recommendations = []
        
        # CPU 사용률 체크
        if metrics.cpu_percent > self.cpu_threshold:
            recommendations.append("CPU 사용률이 높습니다. OCR 워커 수를 줄이는 것을 권장합니다.")
            self.reduced_ocr_workers = True
        
        # 메모리 사용량 체크
        if metrics.memory_mb > self.memory_threshold:
            recommendations.append("메모리 사용량이 높습니다. 배치 크기를 줄이는 것을 권장합니다.")
            self.reduced_batch_size = True
        
        # OCR 레이턴시 체크
        if metrics.ocr_latency_ms and metrics.ocr_latency_ms > self.latency_threshold:
            recommendations.append("OCR 레이턴시가 높습니다. 이미지 전처리를 최적화하세요.")
        
        return recommendations
    
    def get_optimized_settings(self) -> Dict[str, any]:
        """최적화된 설정 반환"""
        settings = {
            'max_concurrent_ocr': 6,
            'batch_size': 15,
            'ocr_interval': 0.5,
            'image_scale': 4.0
        }
        
        # 성능 이슈가 있으면 설정 조정
        if self.reduced_ocr_workers:
            settings['max_concurrent_ocr'] = 3
        
        if self.reduced_batch_size:
            settings['batch_size'] = 8
            settings['ocr_interval'] = 0.7
        
        return settings