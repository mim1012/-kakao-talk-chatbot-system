#!/usr/bin/env python3
"""
최적화된 병렬 모니터링 시스템
- 변화 감지
- 적응형 우선순위
- 병렬 처리
"""
import threading
import queue
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Optional, Tuple
import numpy as np
import mss
import logging
from dataclasses import dataclass

from .change_detection import ChangeDetectionMonitor
from .adaptive_monitor import AdaptivePriorityManager, AdaptiveMonitoringStrategy

logger = logging.getLogger(__name__)


@dataclass
class MonitoringResult:
    """모니터링 결과"""
    cell_id: str
    has_change: bool
    ocr_result: Optional[any] = None
    trigger_found: bool = False
    processing_time: float = 0.0


class OptimizedParallelMonitor:
    """
    모든 최적화 기술을 통합한 병렬 모니터링 시스템
    """
    
    def __init__(self, grid_manager, ocr_service, config):
        self.grid_manager = grid_manager
        self.ocr_service = ocr_service
        self.config = config
        
        # 최적화 컴포넌트
        self.change_detector = ChangeDetectionMonitor(change_threshold=0.05)
        self.priority_manager = AdaptivePriorityManager(
            base_interval=config.get('ocr_interval_sec', 0.3)
        )
        self.adaptive_strategy = AdaptiveMonitoringStrategy(self.priority_manager)
        
        # 병렬 처리 설정
        self.capture_workers = config.get('parallel_processing', {}).get('capture_workers', 4)
        self.ocr_workers = config.get('parallel_processing', {}).get('ocr_workers', 4)  # 설정에서 읽기
        
        # 스레드 풀
        self.capture_pool = ThreadPoolExecutor(max_workers=self.capture_workers)
        self.ocr_pool = ThreadPoolExecutor(max_workers=self.ocr_workers)
        
        # 큐 (백프레셔를 위해 크기 제한)
        self.result_queue = queue.Queue(maxsize=100)  # 최대 100개까지만
        
        # 상태
        self.running = False
        self.stats = {
            'total_scans': 0,
            'changes_detected': 0,
            'triggers_found': 0,
            'avg_scan_time': 0,
            'skipped_by_change': 0,
            'skipped_by_priority': 0
        }
        
        # 모든 셀 등록
        for cell in grid_manager.cells:
            self.priority_manager.register_cell(cell.id)
    
    def start(self):
        """모니터링 시작"""
        self.running = True
        monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        monitor_thread.start()
        logger.info("최적화된 병렬 모니터링 시작")
    
    def stop(self):
        """모니터링 중지"""
        self.running = False
        self.capture_pool.shutdown(wait=True)
        self.ocr_pool.shutdown(wait=True)
        logger.info("모니터링 중지")
    
    def _monitor_loop(self):
        """메인 모니터링 루프"""
        # 초기화 단계: 모든 셀에 대해 첫 OCR 스캔 수행
        logger.info("초기화: 모든 셀에 대한 첫 OCR 스캔 시작...")
        self._initialize_all_cells()
        logger.info("초기화 완료: 모든 셀이 OCR 처리됨")
        
        while self.running:
            try:
                cycle_start = time.time()
                
                # 1. 스캔할 셀 선택 (적응형 우선순위)
                all_cell_ids = [cell.id for cell in self.grid_manager.cells 
                               if cell.can_be_triggered()]
                cells_to_scan = self.adaptive_strategy.get_cells_to_scan(
                    all_cell_ids, 
                    max_batch=15
                )
                
                if not cells_to_scan:
                    time.sleep(0.1)
                    continue
                
                self.stats['total_scans'] += 1
                
                # 2. 큐 크기 확인 (백프레셔)
                if self.result_queue.qsize() > 80:
                    logger.warning(f"큐 포화 경고: {self.result_queue.qsize()}/100")
                    cells_to_scan = cells_to_scan[:len(cells_to_scan)//2]  # 절반만 처리
                    time.sleep(0.1)  # 짧은 대기
                
                # 병렬 캡처 및 처리
                results = self._parallel_process_cells(cells_to_scan)
                
                # 3. 결과 처리 및 우선순위 업데이트
                scan_results = {}
                for result in results:
                    if result.trigger_found:
                        self.stats['triggers_found'] += 1
                        self.result_queue.put(result)
                    
                    scan_results[result.cell_id] = result.trigger_found
                
                # 4. 적응형 전략에 결과 보고
                self.adaptive_strategy.report_results(scan_results)
                
                # 5. 사이클 시간 측정
                cycle_time = time.time() - cycle_start
                self._update_stats(cycle_time)
                
                # 동적 대기 시간
                sleep_time = max(0.05, self.config.get('ocr_interval_sec', 0.3) - cycle_time)
                time.sleep(sleep_time)
                
            except Exception as e:
                logger.error(f"모니터링 루프 오류: {e}")
                time.sleep(1)
    
    def _initialize_all_cells(self):
        """모든 셀에 대해 초기 OCR 스캔 수행"""
        all_cell_ids = [cell.id for cell in self.grid_manager.cells]
        uninitialized = self.change_detector.get_uninitialized_cells(all_cell_ids)
        
        if not uninitialized:
            logger.info("모든 셀이 이미 초기화됨")
            return
        
        logger.info(f"초기화할 셀 수: {len(uninitialized)}")
        
        # 배치로 나누어 처리 (메모리 효율성)
        batch_size = 5
        for i in range(0, len(uninitialized), batch_size):
            batch = uninitialized[i:i+batch_size]
            logger.info(f"초기화 배치 {i//batch_size + 1}/{(len(uninitialized) + batch_size - 1)//batch_size}: {batch}")
            
            # 각 셀에 대해 캡처 및 OCR 수행 (변화 감지 우회)
            futures = []
            for cell_id in batch:
                future = self.capture_pool.submit(self._initialize_cell, cell_id)
                futures.append((future, cell_id))
            
            # 결과 대기
            for future, cell_id in futures:
                try:
                    future.result(timeout=10)  # 10초 타임아웃
                except Exception as e:
                    logger.error(f"셀 {cell_id} 초기화 실패: {e}")
            
            # 배치 간 잠시 대기
            time.sleep(0.5)
    
    def _initialize_cell(self, cell_id: str):
        """단일 셀 초기화 (첫 OCR 수행)"""
        try:
            # 셀 정보 가져오기
            cell = next((c for c in self.grid_manager.cells if c.id == cell_id), None)
            if not cell:
                logger.error(f"셀 {cell_id}를 찾을 수 없음")
                return
            
            # 이미지 캡처
            with mss.mss() as sct:
                region = cell.region
                monitor = {
                    "left": region[0],
                    "top": region[1], 
                    "width": region[2] - region[0],
                    "height": region[3] - region[1]
                }
                screenshot = sct.grab(monitor)
                image = np.array(screenshot)
            
            # BGR로 변환 (mss는 BGRA 반환)
            if image.shape[2] == 4:
                image = cv2.cvtColor(image, cv2.COLOR_BGRA2BGR)
            
            # 변화 감지기에 등록 (첫 캡처이므로 항상 True 반환)
            self.change_detector.has_changed(cell_id, image)
            
            # OCR 수행
            ocr_result, trigger_found = self._perform_ocr(cell_id, image)
            
            if trigger_found:
                logger.info(f"🎯 초기화 중 트리거 발견: {cell_id}")
                self.result_queue.put(MonitoringResult(
                    cell_id=cell_id,
                    has_change=True,
                    trigger_found=True,
                    ocr_result=ocr_result,
                    processing_time=0
                ))
            
            logger.info(f"셀 {cell_id} 초기화 완료")
            
        except Exception as e:
            logger.error(f"셀 {cell_id} 초기화 오류: {e}")
    
    def _parallel_process_cells(self, cell_ids: List[str]) -> List[MonitoringResult]:
        """셀들을 병렬로 처리"""
        futures = []
        results = []
        
        # 병렬 캡처 및 변화 감지
        capture_futures = {}
        for cell_id in cell_ids:
            future = self.capture_pool.submit(self._capture_and_detect, cell_id)
            capture_futures[future] = cell_id
        
        # 캡처 결과 수집 및 OCR 제출
        ocr_futures = {}
        for future in as_completed(capture_futures):
            cell_id = capture_futures[future]
            try:
                capture_result = future.result()
                if capture_result:  # 변화가 감지된 경우만
                    image, region = capture_result
                    ocr_future = self.ocr_pool.submit(
                        self._perform_ocr, cell_id, image
                    )
                    ocr_futures[ocr_future] = (cell_id, time.time())
                else:
                    # 변화 없음 (이미 _capture_and_detect에서 카운트됨)
                    results.append(MonitoringResult(
                        cell_id=cell_id,
                        has_change=False,
                        trigger_found=False
                    ))
            except Exception as e:
                logger.error(f"캡처 오류 {cell_id}: {e}")
        
        # OCR 결과 수집
        for future in as_completed(ocr_futures):
            cell_id, start_time = ocr_futures[future]
            try:
                ocr_result, trigger_found = future.result()
                processing_time = time.time() - start_time
                
                results.append(MonitoringResult(
                    cell_id=cell_id,
                    has_change=True,
                    ocr_result=ocr_result,
                    trigger_found=trigger_found,
                    processing_time=processing_time
                ))
                
                if trigger_found:
                    logger.info(f"트리거 감지: {cell_id}")
                    
            except Exception as e:
                logger.error(f"OCR 오류 {cell_id}: {e}")
        
        return results
    
    def _capture_and_detect(self, cell_id: str) -> Optional[Tuple[np.ndarray, Tuple]]:
        """화면 캡처 및 변화 감지"""
        cell = self._get_cell_by_id(cell_id)
        if not cell:
            return None
        
        try:
            # 각 스레드에서 독립적인 mss 인스턴스 생성
            with mss.mss() as sct:
                # 캡처
                x, y, w, h = cell.ocr_area
                monitor = {"left": x, "top": y, "width": w, "height": h}
                screenshot = sct.grab(monitor)
                image = np.array(screenshot)
                
                # 변화 감지
                if self.change_detector.has_changed(cell_id, image):
                    self.stats['changes_detected'] += 1
                    logger.debug(f"변화 감지됨: {cell_id}")
                    return (image, (x, y, w, h))
                else:
                    self.stats['skipped_by_change'] += 1
                    return None
                
        except Exception as e:
            logger.error(f"캡처 실패 {cell_id}: {e}")
            return None
    
    def _perform_ocr(self, cell_id: str, image: np.ndarray) -> Tuple[any, bool]:
        """OCR 수행 및 트리거 확인"""
        try:
            # OCR 실행
            result = self.ocr_service.perform_ocr(image)
            
            # 트리거 패턴 확인
            trigger_found = False
            if result and result.text:
                trigger_patterns = self.config.get('trigger_patterns', ['들어왔습니다'])
                for pattern in trigger_patterns:
                    if pattern in result.text:
                        trigger_found = True
                        break
            
            return result, trigger_found
            
        except Exception as e:
            logger.error(f"OCR 실패 {cell_id}: {e}")
            return None, False
    
    def _get_cell_by_id(self, cell_id: str):
        """ID로 셀 찾기"""
        for cell in self.grid_manager.cells:
            if cell.id == cell_id:
                return cell
        return None
    
    def _update_stats(self, cycle_time: float):
        """통계 업데이트"""
        # 이동 평균으로 평균 스캔 시간 계산
        alpha = 0.1
        self.stats['avg_scan_time'] = (
            alpha * cycle_time + 
            (1 - alpha) * self.stats['avg_scan_time']
        )
    
    def get_statistics(self) -> Dict:
        """통계 정보 반환"""
        change_stats = self.change_detector.get_statistics()
        priority_stats = self.priority_manager.get_statistics()
        
        return {
            **self.stats,
            'change_detection': change_stats,
            'priority_management': priority_stats,
            'capture_workers': self.capture_workers,
            'ocr_workers': self.ocr_workers
        }
    
    def get_next_result(self, timeout: float = 0.1) -> Optional[MonitoringResult]:
        """다음 감지 결과 가져오기"""
        try:
            return self.result_queue.get(timeout=timeout)
        except queue.Empty:
            return None


class MonitoringOrchestrator:
    """
    모니터링 오케스트레이터
    여러 모니터링 전략을 조합하여 사용
    """
    
    def __init__(self, grid_manager, ocr_service, config):
        self.monitor = OptimizedParallelMonitor(grid_manager, ocr_service, config)
        self.automation_queue = queue.Queue()
        self.running = False
        
    def start(self):
        """모니터링 시작"""
        self.running = True
        self.monitor.start()
        
        # 결과 처리 스레드
        result_thread = threading.Thread(target=self._process_results, daemon=True)
        result_thread.start()
        
        logger.info("모니터링 오케스트레이터 시작")
    
    def stop(self):
        """모니터링 중지"""
        self.running = False
        self.monitor.stop()
    
    def _process_results(self):
        """감지 결과 처리"""
        while self.running:
            result = self.monitor.get_next_result()
            if result and result.trigger_found:
                # 자동화 큐에 추가
                self.automation_queue.put({
                    'cell_id': result.cell_id,
                    'text': result.ocr_result.text if result.ocr_result else '',
                    'timestamp': time.time()
                })
    
    def get_automation_task(self, timeout: float = 0.1) -> Optional[Dict]:
        """자동화 작업 가져오기"""
        try:
            return self.automation_queue.get(timeout=timeout)
        except queue.Empty:
            return None
    
    def get_statistics(self) -> Dict:
        """전체 통계"""
        return self.monitor.get_statistics()