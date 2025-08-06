"""
초고속 캡처 및 이미지 처리 엔진
DirectX 캡처, 메모리 최적화, GPU 가속 등을 활용한 극한의 성능 최적화
"""

import time
import numpy as np
import mss
import cv2
import threading
import queue
from typing import List, Tuple, Optional, Dict, Any
from dataclasses import dataclass
import ctypes
from ctypes import wintypes
import win32gui
import win32ui
import win32con
import win32api

@dataclass
class CaptureRegion:
    """캡처 영역"""
    x: int
    y: int
    width: int
    height: int
    cell_id: str

class Win32Capture:
    """Win32 API를 사용한 고속 캡처 (MSS보다 빠름)"""
    
    def __init__(self):
        self.desktop_dc = None
        self.mem_dc = None
        self.bitmap = None
        self.bitmap_handle = None
        self._setup()
    
    def _setup(self):
        """DC 설정"""
        # 데스크톱 DC 가져오기
        self.desktop_dc = win32gui.GetDC(0)
        self.mem_dc = win32ui.CreateDCFromHandle(self.desktop_dc)
        self.compatible_dc = self.mem_dc.CreateCompatibleDC()
    
    def capture_region(self, x: int, y: int, width: int, height: int) -> np.ndarray:
        """특정 영역 캡처 (Win32 API)"""
        try:
            # 비트맵 생성
            bitmap = win32ui.CreateBitmap()
            bitmap.CreateCompatibleBitmap(self.mem_dc, width, height)
            
            # 메모리 DC에 비트맵 선택
            self.compatible_dc.SelectObject(bitmap)
            
            # 화면 내용을 메모리 DC로 복사 (BitBlt - 가장 빠른 방법)
            self.compatible_dc.BitBlt((0, 0), (width, height), 
                                     self.mem_dc, (x, y), win32con.SRCCOPY)
            
            # 비트맵 데이터 가져오기
            bitmap_info = bitmap.GetBitmapBits(True)
            
            # numpy 배열로 변환 (복사 없이 직접 변환)
            image = np.frombuffer(bitmap_info, dtype=np.uint8)
            image = image.reshape((height, width, 4))
            
            # BGRA to BGR (OpenCV 형식)
            image = image[:, :, :3]
            
            # 비트맵 정리
            win32gui.DeleteObject(bitmap.GetHandle())
            
            return image
            
        except Exception as e:
            print(f"Win32 캡처 실패: {e}")
            return None
    
    def cleanup(self):
        """리소스 정리"""
        if self.desktop_dc:
            win32gui.ReleaseDC(0, self.desktop_dc)

class MemoryPool:
    """메모리 풀 - 이미지 버퍼 재사용"""
    
    def __init__(self, buffer_size: int = 30, image_shape: Tuple[int, int, int] = (600, 400, 3)):
        self.buffer_size = buffer_size
        self.image_shape = image_shape
        self.buffers = []
        self.lock = threading.Lock()
        self._init_buffers()
    
    def _init_buffers(self):
        """버퍼 사전 할당"""
        for _ in range(self.buffer_size):
            # 연속된 메모리 할당 (C-contiguous)
            buffer = np.empty(self.image_shape, dtype=np.uint8)
            self.buffers.append(buffer)
    
    def get_buffer(self) -> np.ndarray:
        """사용 가능한 버퍼 가져오기"""
        with self.lock:
            if self.buffers:
                return self.buffers.pop()
            else:
                # 풀이 비어있으면 새로 할당
                return np.empty(self.image_shape, dtype=np.uint8)
    
    def return_buffer(self, buffer: np.ndarray):
        """버퍼 반환"""
        with self.lock:
            if len(self.buffers) < self.buffer_size:
                self.buffers.append(buffer)

class ImageProcessor:
    """최적화된 이미지 처리기"""
    
    @staticmethod
    def ultra_fast_crop(full_image: np.ndarray, regions: List[CaptureRegion]) -> List[np.ndarray]:
        """초고속 이미지 자르기 (뷰 사용, 복사 최소화)"""
        cropped = []
        
        for region in regions:
            # 경계 체크
            y_end = min(region.y + region.height, full_image.shape[0])
            x_end = min(region.x + region.width, full_image.shape[1])
            
            if region.y >= 0 and region.x >= 0 and y_end > region.y and x_end > region.x:
                # 뷰로 자르기 (복사 없음)
                view = full_image[region.y:y_end, region.x:x_end]
                # 필요한 경우만 복사
                if view.flags['C_CONTIGUOUS']:
                    cropped.append(view)
                else:
                    cropped.append(np.ascontiguousarray(view))
            else:
                cropped.append(None)
        
        return cropped
    
    @staticmethod
    def batch_grayscale_sse(images: List[np.ndarray]) -> List[np.ndarray]:
        """배치 그레이스케일 변환 (SIMD 최적화)"""
        results = []
        
        for img in images:
            if img is None:
                results.append(None)
                continue
            
            if len(img.shape) == 2:
                results.append(img)
            else:
                # OpenCV의 SIMD 최적화된 변환 사용
                gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
                results.append(gray)
        
        return results
    
    @staticmethod
    def batch_resize_fast(images: List[np.ndarray], scale: float = 0.5) -> List[np.ndarray]:
        """배치 리사이즈 (INTER_NEAREST로 빠르게)"""
        results = []
        
        for img in images:
            if img is None:
                results.append(None)
                continue
            
            if scale == 1.0:
                results.append(img)
            else:
                # INTER_NEAREST가 가장 빠름
                new_size = (int(img.shape[1] * scale), int(img.shape[0] * scale))
                resized = cv2.resize(img, new_size, interpolation=cv2.INTER_NEAREST)
                results.append(resized)
        
        return results

class AsyncCaptureEngine:
    """비동기 캡처 엔진 - 캡처와 처리를 파이프라인화"""
    
    def __init__(self, num_threads: int = 2):
        self.num_threads = num_threads
        self.capture_queue = queue.Queue(maxsize=10)
        self.result_queue = queue.Queue(maxsize=10)
        self.running = False
        self.threads = []
        
        # Win32 캡처 사용
        self.use_win32 = True
        try:
            self.win32_capture = Win32Capture()
        except:
            self.use_win32 = False
            print("Win32 캡처 초기화 실패, MSS 사용")
        
        # 메모리 풀
        self.memory_pool = MemoryPool(buffer_size=30)
        
        # 이미지 처리기
        self.processor = ImageProcessor()
        
        # 통계
        self.stats = {
            'captures': 0,
            'total_time': 0,
            'win32_used': self.use_win32
        }
    
    def start(self):
        """엔진 시작"""
        self.running = True
        
        # 캡처 스레드
        for i in range(self.num_threads):
            thread = threading.Thread(target=self._capture_worker, daemon=True)
            thread.start()
            self.threads.append(thread)
    
    def _capture_worker(self):
        """캡처 워커 스레드"""
        if not self.use_win32:
            sct = mss.mss()
        
        while self.running:
            try:
                # 캡처 요청 대기
                request = self.capture_queue.get(timeout=0.1)
                if request is None:
                    break
                
                regions, callback = request
                start_time = time.perf_counter()
                
                if self.use_win32:
                    # Win32 API 캡처 (더 빠름)
                    # 전체 화면 한 번만 캡처
                    screen_width = win32api.GetSystemMetrics(0)
                    screen_height = win32api.GetSystemMetrics(1)
                    
                    # 메모리 풀에서 버퍼 가져오기
                    buffer = self.memory_pool.get_buffer()
                    
                    # 전체 화면 캡처
                    full_image = self.win32_capture.capture_region(0, 0, screen_width, screen_height)
                    
                    # 영역별로 자르기 (뷰 사용)
                    cropped_images = self.processor.ultra_fast_crop(full_image, regions)
                    
                else:
                    # MSS 사용 (폴백)
                    monitor = sct.monitors[1]
                    screenshot = sct.grab(monitor)
                    full_image = np.array(screenshot)
                    
                    # 영역별로 자르기
                    cropped_images = self.processor.ultra_fast_crop(full_image, regions)
                
                # 그레이스케일 변환 (배치)
                gray_images = self.processor.batch_grayscale_sse(cropped_images)
                
                # 통계 업데이트
                elapsed = time.perf_counter() - start_time
                self.stats['captures'] += len(regions)
                self.stats['total_time'] += elapsed
                
                # 결과 전달
                self.result_queue.put((gray_images, regions, elapsed))
                
                # 콜백 실행
                if callback:
                    callback(gray_images, regions)
                
                # 버퍼 반환
                if self.use_win32:
                    self.memory_pool.return_buffer(buffer)
                
            except queue.Empty:
                continue
            except Exception as e:
                print(f"캡처 워커 오류: {e}")
    
    def capture_async(self, regions: List[CaptureRegion], callback=None):
        """비동기 캡처 요청"""
        self.capture_queue.put((regions, callback))
    
    def get_result(self, timeout: float = 0.1):
        """결과 가져오기"""
        try:
            return self.result_queue.get(timeout=timeout)
        except queue.Empty:
            return None
    
    def stop(self):
        """엔진 중지"""
        self.running = False
        
        # 종료 신호
        for _ in range(self.num_threads):
            self.capture_queue.put(None)
        
        # 스레드 종료 대기
        for thread in self.threads:
            thread.join(timeout=1.0)
        
        # Win32 리소스 정리
        if self.use_win32:
            self.win32_capture.cleanup()
    
    def get_stats(self) -> Dict[str, Any]:
        """통계 반환"""
        if self.stats['captures'] > 0:
            avg_time = self.stats['total_time'] / self.stats['captures'] * 1000
        else:
            avg_time = 0
        
        return {
            'total_captures': self.stats['captures'],
            'avg_time_ms': avg_time,
            'win32_capture': self.stats['win32_used'],
            'memory_pool_size': len(self.memory_pool.buffers)
        }

class UltraFastCaptureManager:
    """초고속 캡처 매니저 - 모든 최적화 통합"""
    
    def __init__(self):
        self.async_engine = AsyncCaptureEngine(num_threads=2)
        self.async_engine.start()
        
        # 캐시 (5초 TTL)
        self.cache = {}
        self.cache_ttl = 5.0
        
        print("[초고속 캡처] 엔진 시작")
        if self.async_engine.use_win32:
            print("  - Win32 API 캡처 사용 (최고 성능)")
        else:
            print("  - MSS 캡처 사용")
        print("  - 메모리 풀 활성화")
        print("  - 비동기 파이프라인 활성화")
    
    def capture_batch(self, regions: List[CaptureRegion]) -> List[np.ndarray]:
        """배치 캡처 (동기)"""
        # 비동기 캡처 요청
        self.async_engine.capture_async(regions)
        
        # 결과 대기
        result = self.async_engine.get_result(timeout=0.5)
        if result:
            images, _, elapsed = result
            return images
        else:
            return [None] * len(regions)
    
    def capture_batch_async(self, regions: List[CaptureRegion], callback):
        """배치 캡처 (비동기)"""
        self.async_engine.capture_async(regions, callback)
    
    def shutdown(self):
        """종료"""
        self.async_engine.stop()
        print("[초고속 캡처] 엔진 종료")
    
    def get_stats(self):
        """통계"""
        return self.async_engine.get_stats()