"""
최적화된 PaddleOCR 서비스 - 빠른 처리에 집중
"""
import cv2
import numpy as np
import logging
import time
from typing import List, Tuple, Optional
from paddleocr import PaddleOCR
from src.core.config_manager import ConfigManager
from src.ocr.base_ocr_service import BaseOCRService, OCRResult

class OptimizedPaddleService(BaseOCRService):
    """최적화된 PaddleOCR 서비스"""
    
    # 클래스 레벨 공유 인스턴스
    _shared_instance = None
    _init_time = 0
    
    def __init__(self, config_manager: ConfigManager):
        super().__init__(config_manager)
        self.logger = logging.getLogger(__name__)
        
        # PaddleOCR 초기화
        self._initialize_ocr_engine()
        
    def _initialize_ocr_engine(self) -> bool:
        """OCR 엔진 초기화 - 최적 설정"""
        try:
            current_time = time.time()
            
            # 5분 내 재사용
            if (OptimizedPaddleService._shared_instance and 
                current_time - OptimizedPaddleService._init_time < 300):
                self.paddle_ocr = OptimizedPaddleService._shared_instance
                self.logger.info("기존 PaddleOCR 인스턴스 재사용")
                return True
            
            # 최적화 설정으로 새 인스턴스 생성
            self.paddle_ocr = PaddleOCR(
                lang='korean',
                use_angle_cls=False,       # 각도 분류 비활성화
                use_gpu=False,              # CPU 사용
                enable_mkldnn=True,         # MKLDNN 활성화 (Intel CPU 최적화)
                cpu_threads=2,              # CPU 스레드 제한
                det_algorithm='DB',         # 빠른 텍스트 감지
                det_db_thresh=0.5,          # 높은 임계값 (빠른 필터링)
                det_db_box_thresh=0.6,      # 박스 임계값 증가
                det_db_unclip_ratio=1.2,    # 언클립 비율 감소
                det_limit_side_len=160,     # 매우 작은 이미지 제한
                det_db_score_mode='fast',   # 빠른 스코어 모드
                rec_batch_num=1,            # 작은 배치
                max_text_length=15,         # 짧은 텍스트
                rec_algorithm='CRNN',       # 빠른 인식
                rec_image_shape='3, 32, 160',  # 작은 인식 이미지
                use_space_char=False,       # 공백 비활성화
                drop_score=0.3,             # 낮은 점수 드롭
                show_log=False              # 로그 비활성화
            )
            
            OptimizedPaddleService._shared_instance = self.paddle_ocr
            OptimizedPaddleService._init_time = current_time
            
            self.logger.info("최적화된 PaddleOCR 초기화 완료")
            return True
            
        except Exception as e:
            self.logger.error(f"PaddleOCR 초기화 실패: {e}")
            import traceback
            self.logger.debug(f"초기화 스택 트레이스:\n{traceback.format_exc()}")
            self.paddle_ocr = None
            return False
    
    def _perform_ocr_internal(self, image: np.ndarray) -> List[Tuple[str, float, Tuple[int, int]]]:
        """내부 OCR 처리 - 최적화된 버전"""
        if not self.paddle_ocr:
            self.logger.error("PaddleOCR 인스턴스가 초기화되지 않았습니다")
            # 재초기화 시도
            if not self._initialize_ocr_engine():
                return []
        
        try:
            start = time.time()
            
            # 리사이즈는 preprocess_image에서 이미 처리됨
            # 블러 감지 추가
            if self._is_blurry(image):
                self.logger.warning("블러 감지됨, 샤프닝 적용")
                image = self._sharpen_image(image)
            
            # OCR 실행 - 오류 처리 강화
            results = None
            try:
                results = self.paddle_ocr.ocr(image, cls=False)
            except IndexError as idx_err:
                self.logger.debug(f"PaddleOCR IndexError (텍스트 없음): {idx_err}")
                return []
            except Exception as ocr_err:
                self.logger.error(f"PaddleOCR 실행 오류: {ocr_err}")
                return []
            
            elapsed = time.time() - start
            self.logger.debug(f"OCR 처리 시간: {elapsed:.2f}초")
            
            # 결과 상세 로깅
            self.logger.debug(f"OCR 결과 타입: {type(results)}")
            if results is not None:
                self.logger.debug(f"OCR 결과 길이: {len(results) if hasattr(results, '__len__') else 'N/A'}")
                if isinstance(results, list) and len(results) > 0:
                    self.logger.debug(f"results[0] 타입: {type(results[0])}")
            
            # 결과 확인
            if results is None:
                self.logger.debug("OCR 결과가 None입니다")
                return []
            
            # results가 리스트인지 확인
            if not isinstance(results, list):
                self.logger.debug(f"예상치 못한 결과 타입: {type(results)}")
                return []
            
            # results가 비어있는지 확인
            if len(results) == 0:
                self.logger.debug("OCR 결과 리스트가 비어있습니다")
                return []
            
            # results[0]이 None이거나 빈 리스트인 경우 (PaddleOCR은 텍스트가 없으면 [None] 반환)
            if len(results) > 0 and (results[0] is None or (isinstance(results[0], list) and len(results[0]) == 0)):
                self.logger.debug("텍스트가 감지되지 않았습니다")
                return []
            
            # results가 예상된 구조가 아닌 경우 (이미 위에서 검사했으므로 중복 제거)
            # 첫 번째 요소가 iteratable한지 확인 (results가 비어있지 않은 것은 이미 확인됨)
            if len(results) > 0 and not hasattr(results[0], '__iter__'):
                self.logger.debug(f"results[0]이 iteratable하지 않음: {type(results[0])}")
                return []
            
            # 결과 변환 (더 안전한 처리)
            ocr_results = []
            try:
                # results[0]이 안전하게 iterate 가능한지 다시 한번 확인
                if not results or len(results) == 0:
                    return []
                    
                first_result = results[0]
                if first_result is None:
                    return []
                    
                # first_result가 iterable한지 확인
                if not hasattr(first_result, '__iter__'):
                    self.logger.debug(f"first_result가 iterable하지 않음: {type(first_result)}")
                    return []
                
                for i, line in enumerate(first_result):
                    try:
                        # line 구조 확인
                        if not isinstance(line, (list, tuple)) or len(line) < 2:
                            self.logger.debug(f"라인 {i}: 잘못된 구조 - {type(line)}, len={len(line) if hasattr(line, '__len__') else 'N/A'}")
                            continue
                        
                        # 텍스트 정보 확인
                        text_info = line[1]
                        if not text_info or not isinstance(text_info, (list, tuple)) or len(text_info) < 2:
                            self.logger.debug(f"라인 {i}: 텍스트 정보 없음")
                            continue
                        
                        text = str(text_info[0])
                        confidence = float(text_info[1])
                        
                        # 위치 정보 추출 (선택적)
                        position = (0, 0)
                        if line[0] and isinstance(line[0], (list, tuple)) and len(line[0]) > 0:
                            if isinstance(line[0][0], (list, tuple)) and len(line[0][0]) >= 2:
                                try:
                                    position = (int(line[0][0][0]), int(line[0][0][1]))
                                except:
                                    pass
                        
                        ocr_results.append((text, confidence, position))
                        
                    except Exception as e:
                        self.logger.debug(f"라인 {i} 파싱 오류: {e}")
                        continue
            
            except Exception as inner_e:
                self.logger.debug(f"결과 변환 중 오류: {inner_e}")
                return []
                
            return ocr_results
            
        except Exception as e:
            import traceback
            self.logger.error(f"OCR 처리 오류: {e}")
            # 더 자세한 디버그 정보
            self.logger.error(f"results 타입: {type(results) if 'results' in locals() else 'N/A'}")
            if 'results' in locals() and results is not None:
                self.logger.error(f"results 길이: {len(results) if hasattr(results, '__len__') else 'N/A'}")
                if isinstance(results, list) and len(results) > 0:
                    self.logger.error(f"results[0] 타입: {type(results[0])}")
                    self.logger.error(f"results[0] 값: {results[0]}")
            self.logger.debug(f"스택 트레이스:\n{traceback.format_exc()}")
            return []
    
    def is_available(self) -> bool:
        """OCR 엔진 사용 가능 여부"""
        return self.paddle_ocr is not None
    
    def preprocess_image(self, image: np.ndarray, simple_mode: bool = True) -> np.ndarray:
        """이미지 전처리 - 리사이즈 먼저 수행"""
        if image is None or image.size == 0:
            return image
        
        try:
            # 1. 리사이즈 먼저 (레이턴시 개선)
            height, width = image.shape[:2]
            max_size = 320
            
            if width > max_size or height > max_size:
                scale = min(max_size/width, max_size/height)
                new_width = int(width * scale)
                new_height = int(height * scale)
                image = cv2.resize(image, (new_width, new_height), interpolation=cv2.INTER_LINEAR)
            
            # 2. RGBA -> RGB
            if len(image.shape) == 3 and image.shape[2] == 4:
                image = cv2.cvtColor(image, cv2.COLOR_RGBA2RGB)
            
            # 3. 그레이스케일
            if len(image.shape) == 3:
                gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
            else:
                gray = image
            
            # 4. 대비 향상
            gray = cv2.convertScaleAbs(gray, alpha=1.5, beta=10)
            
            # 5. 이진화
            _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            
            return binary
            
        except Exception as e:
            self.logger.error(f"전처리 오류: {e}")
            return image
    
    def _is_blurry(self, image: np.ndarray, threshold: float = 100.0) -> bool:
        """블러 감지 (Laplacian variance)"""
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image
        laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()
        return laplacian_var < threshold
    
    def _sharpen_image(self, image: np.ndarray) -> np.ndarray:
        """이미지 샤프닝"""
        kernel = np.array([[-1,-1,-1],
                          [-1, 9,-1],
                          [-1,-1,-1]])
        return cv2.filter2D(image, -1, kernel)
    
    def perform_ocr_with_recovery(self, image: np.ndarray, cell_id: str = "") -> OCRResult:
        """OCR 처리 with 자동 복구 (호환성을 위한 메서드)"""
        try:
            # BaseOCRService의 process_image 메서드 호출
            result = self.process_image(image)
            
            # 중요한 텍스트만 로그 출력
            if result and result.text:
                # 트리거 패턴이 있는 경우만 INFO 레벨로
                if any(pattern in result.text for pattern in ["들어왔", "입장", "참여"]):
                    self.logger.info(f"{cell_id}: 🎯 트리거 감지 - '{result.text}' (신뢰도: {result.confidence:.2f})")
                else:
                    self.logger.debug(f"{cell_id}: OCR 감지 - '{result.text}' (신뢰도: {result.confidence:.2f})")
            
            return result
            
        except Exception as e:
            self.logger.error(f"OCR 처리 오류 ({cell_id}): {e}")
            return OCRResult()
    
    def check_trigger_patterns(self, ocr_result: OCRResult) -> bool:
        """트리거 패턴 확인"""
        if not ocr_result or not ocr_result.text:
            return False
        
        text = ocr_result.text
        
        # OCR corrector 사용하여 트리거 패턴 확인
        is_match, matched_pattern = self.ocr_corrector.check_trigger_pattern(text)
        
        if is_match:
            self.logger.info(f"🎯 트리거 패턴 감지: '{text}' -> '{matched_pattern}'")
            return True
            
        return False
    
    def get_statistics(self) -> dict:
        """OCR 통계 반환 (성능 모니터링용)"""
        return {
            'total_processed': 0,
            'successful': 0,
            'failed': 0,
            'avg_time': 0.0,
            'cache_hits': 0,
            'cache_misses': 0
        }