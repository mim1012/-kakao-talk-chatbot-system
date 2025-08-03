"""
PerformanceMonitor 단위 테스트
"""
import pytest
import time
import json
from pathlib import Path
from unittest.mock import Mock, patch
from monitoring.performance_monitor import (
    PerformanceMetrics, PerformanceStats, 
    PerformanceMonitor, PerformanceOptimizer
)

class TestPerformanceMetrics:
    """성능 메트릭 테스트"""
    
    @pytest.mark.unit
    @pytest.mark.performance
    def test_metrics_creation(self):
        """메트릭 생성 테스트"""
        metrics = PerformanceMetrics(
            timestamp=time.time(),
            cpu_percent=45.5,
            memory_percent=30.2,
            memory_mb=512.5,
            ocr_latency_ms=25.5,
            detection_count=10,
            automation_count=5
        )
        
        assert metrics.cpu_percent == 45.5
        assert metrics.memory_percent == 30.2
        assert metrics.memory_mb == 512.5
        assert metrics.ocr_latency_ms == 25.5
        assert metrics.detection_count == 10
        assert metrics.automation_count == 5

class TestPerformanceMonitor:
    """성능 모니터 테스트"""
    
    @pytest.fixture
    def monitor(self):
        """테스트용 모니터"""
        return PerformanceMonitor(sample_interval=0.1, history_size=10)
    
    @pytest.mark.unit
    @pytest.mark.performance
    def test_monitor_creation(self, monitor):
        """모니터 생성 테스트"""
        assert monitor.sample_interval == 0.1
        assert monitor.history_size == 10
        assert len(monitor.metrics_history) == 0
    
    @pytest.mark.unit
    @pytest.mark.performance
    @patch('psutil.Process')
    def test_metrics_collection(self, mock_process, monitor):
        """메트릭 수집 테스트"""
        # psutil 모킹
        mock_proc_instance = Mock()
        mock_proc_instance.cpu_percent.return_value = 50.0
        mock_proc_instance.memory_percent.return_value = 25.0
        mock_proc_instance.memory_info.return_value.rss = 536870912  # 512MB
        mock_process.return_value = mock_proc_instance
        
        # 모니터 재생성 (모킹 적용)
        monitor = PerformanceMonitor(sample_interval=0.1)
        
        # 메트릭 수집
        metrics = monitor._collect_metrics()
        
        assert metrics.cpu_percent == 50.0
        assert metrics.memory_percent == 25.0
        assert metrics.memory_mb == 512.0
    
    @pytest.mark.unit
    @pytest.mark.performance
    def test_latency_recording(self, monitor):
        """레이턴시 기록 테스트"""
        # OCR 레이턴시 기록
        monitor.record_ocr_latency(25.5)
        monitor.record_ocr_latency(30.0)
        monitor.record_ocr_latency(20.0)
        
        # 평균 계산 확인
        assert len(monitor._ocr_latencies) == 3
        avg_latency = sum(monitor._ocr_latencies) / len(monitor._ocr_latencies)
        assert avg_latency == pytest.approx(25.17, rel=0.1)
        
        # 캡처 레이턴시
        monitor.record_capture_latency(5.0)
        monitor.record_capture_latency(7.0)
        assert len(monitor._capture_latencies) == 2
    
    @pytest.mark.unit
    @pytest.mark.performance
    def test_counter_increments(self, monitor):
        """카운터 증가 테스트"""
        # 초기값
        assert monitor._detection_counter == 0
        assert monitor._automation_counter == 0
        
        # 증가
        monitor.increment_detection_count()
        monitor.increment_detection_count()
        monitor.increment_automation_count()
        
        assert monitor._detection_counter == 2
        assert monitor._automation_counter == 1
    
    @pytest.mark.unit
    @pytest.mark.performance
    @patch('psutil.Process')
    def test_monitoring_loop(self, mock_process, monitor):
        """모니터링 루프 테스트"""
        # psutil 모킹
        mock_proc_instance = Mock()
        mock_proc_instance.cpu_percent.return_value = 45.0
        mock_proc_instance.memory_percent.return_value = 20.0
        mock_proc_instance.memory_info.return_value.rss = 268435456  # 256MB
        mock_process.return_value = mock_proc_instance
        
        # 모니터 재생성
        monitor = PerformanceMonitor(sample_interval=0.05)
        
        # 모니터링 시작
        monitor.start()
        
        # 샘플 수집 대기
        time.sleep(0.2)
        
        # 모니터링 중지
        monitor.stop()
        
        # 메트릭이 수집되었는지 확인
        assert len(monitor.metrics_history) > 0
        assert monitor.metrics_history[0].cpu_percent == 45.0
    
    @pytest.mark.unit
    @pytest.mark.performance
    def test_get_current_stats(self, monitor):
        """현재 통계 테스트"""
        # 일부 데이터 추가
        monitor._detection_counter = 100
        monitor._automation_counter = 80
        monitor._ocr_latencies.extend([20.0, 30.0, 25.0])
        
        # 메트릭 히스토리 추가 (모의)
        for i in range(5):
            metrics = PerformanceMetrics(
                timestamp=time.time(),
                cpu_percent=40.0 + i,
                memory_percent=20.0,
                memory_mb=500.0 + i*10,
                ocr_latency_ms=25.0
            )
            monitor.metrics_history.append(metrics)
        
        # 통계 가져오기
        stats = monitor.get_current_stats()
        
        assert stats.total_detections == 100
        assert stats.total_automations == 80
        assert stats.avg_cpu == 42.0  # (40+41+42+43+44)/5
        assert stats.peak_cpu_percent == 44.0
        assert stats.avg_ocr_latency == 25.0
    
    @pytest.mark.unit
    @pytest.mark.performance
    def test_callback_system(self, monitor):
        """콜백 시스템 테스트"""
        callback_called = []
        
        def test_callback(metrics):
            callback_called.append(metrics)
        
        # 콜백 추가
        monitor.add_callback(test_callback)
        
        # 메트릭 수집 (콜백 호출됨)
        metrics = monitor._collect_metrics()
        for callback in monitor._callbacks:
            callback(metrics)
        
        assert len(callback_called) == 1
        assert isinstance(callback_called[0], PerformanceMetrics)
        
        # 콜백 제거
        monitor.remove_callback(test_callback)
        assert len(monitor._callbacks) == 0
    
    @pytest.mark.unit
    @pytest.mark.performance
    def test_metrics_export(self, monitor, temp_dir):
        """메트릭 내보내기 테스트"""
        # 테스트 데이터 추가
        for i in range(3):
            metrics = PerformanceMetrics(
                timestamp=time.time(),
                cpu_percent=45.0,
                memory_percent=25.0,
                memory_mb=512.0,
                detection_count=i*10,
                automation_count=i*5
            )
            monitor.metrics_history.append(metrics)
        
        monitor._detection_counter = 30
        monitor._automation_counter = 15
        
        # 내보내기
        export_path = Path(temp_dir) / "test_metrics.json"
        monitor.export_metrics(str(export_path))
        
        # 파일 확인
        assert export_path.exists()
        
        # 내용 확인
        with open(export_path, 'r') as f:
            data = json.load(f)
        
        assert 'export_time' in data
        assert 'stats' in data
        assert 'metrics' in data
        assert len(data['metrics']) == 3
        assert data['stats']['total_detections'] == 30

class TestPerformanceOptimizer:
    """성능 최적화 관리자 테스트"""
    
    @pytest.fixture
    def optimizer(self, monitor):
        """테스트용 최적화 관리자"""
        return PerformanceOptimizer(monitor)
    
    @pytest.mark.unit
    @pytest.mark.performance
    def test_optimization_analysis(self, optimizer):
        """최적화 분석 테스트"""
        # 높은 CPU 사용률
        high_cpu_metrics = PerformanceMetrics(
            timestamp=time.time(),
            cpu_percent=85.0,
            memory_percent=30.0,
            memory_mb=512.0
        )
        
        recommendations = optimizer.analyze_and_optimize(high_cpu_metrics)
        assert len(recommendations) > 0
        assert "CPU 사용률이 높습니다" in recommendations[0]
        
        # 높은 메모리 사용량
        high_memory_metrics = PerformanceMetrics(
            timestamp=time.time(),
            cpu_percent=50.0,
            memory_percent=80.0,
            memory_mb=2048.0
        )
        
        recommendations = optimizer.analyze_and_optimize(high_memory_metrics)
        assert any("메모리 사용량이 높습니다" in r for r in recommendations)
        
        # 높은 레이턴시
        high_latency_metrics = PerformanceMetrics(
            timestamp=time.time(),
            cpu_percent=50.0,
            memory_percent=30.0,
            memory_mb=512.0,
            ocr_latency_ms=150.0
        )
        
        recommendations = optimizer.analyze_and_optimize(high_latency_metrics)
        assert any("OCR 레이턴시가 높습니다" in r for r in recommendations)
    
    @pytest.mark.unit
    @pytest.mark.performance
    def test_optimized_settings(self, optimizer):
        """최적화된 설정 테스트"""
        # 기본 설정
        settings = optimizer.get_optimized_settings()
        assert settings['max_concurrent_ocr'] == 6
        assert settings['batch_size'] == 15
        
        # CPU 부하 시뮬레이션
        optimizer.reduced_ocr_workers = True
        settings = optimizer.get_optimized_settings()
        assert settings['max_concurrent_ocr'] == 3
        
        # 메모리 부하 시뮬레이션
        optimizer.reduced_batch_size = True
        settings = optimizer.get_optimized_settings()
        assert settings['batch_size'] == 8
        assert settings['ocr_interval'] == 0.7