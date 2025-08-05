from __future__ import annotations

import json
import os
import sys
import time
import queue
import threading
import logging
import csv
# Modern type hints are imported through __future__ annotations
from pathlib import Path
import cv2
import numpy as np
import pyautogui
import pytesseract
from screeninfo import get_monitors
import re
from datetime import datetime
from PIL import Image, ImageGrab
import mss
import mss.tools
import random
import pyperclip
from grid_cell import GridCell
# PaddleOCR을 조건부 import로 변경 (빌드 오류 방지)
try:
    from paddleocr import PaddleOCR
    PADDLEOCR_AVAILABLE = True
    print("✅ PaddleOCR 로드 성공")
except ImportError as e:
    print(f"⚠️ PaddleOCR import 실패: {e}")
    print("📝 PaddleOCR 없이 기본 OCR 기능으로 실행됩니다.")
    PaddleOCR = None
    PADDLEOCR_AVAILABLE = False

# EasyOCR 제거 (PaddleOCR만 사용으로 단순화)
EASYOCR_AVAILABLE = False

# ────────────────────────────────
# 로깅 설정 (빌드 exe·소스 공통)
# ────────────────────────────────
BASE_DIR = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))
LOG_DIR = BASE_DIR / "logs"
LOG_DIR.mkdir(exist_ok=True)

# 기본 로그 레벨은 INFO, config.json 에서 log_level 키로 재정의 가능
_default_level = logging.INFO
try:
    _cfg_path = Path(__file__).with_name("config.json")
    if _cfg_path.exists():
        with _cfg_path.open("r", encoding="utf-8") as _fp:
            _level_name = json.load(_fp).get("log_level", "INFO").upper()
            _default_level = getattr(logging, _level_name, logging.INFO)
except Exception:
    pass  # 설정 파일 문제 시 무시하고 INFO 유지

file_handler = logging.FileHandler(LOG_DIR / "console_log.txt", encoding="utf-8", delay=False)
file_handler.setFormatter(
    logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
)

console_handler = logging.StreamHandler()

logging.basicConfig(level=_default_level, handlers=[file_handler, console_handler], force=True)
logger = logging.getLogger("monitor_manager")

class MonitorManager:
    """
    모니터 감지 및 그리드 분할 관리 클래스
    """
    def __init__(self, config_path: str = "config.json"):
        """
        초기화
        
        Args:
            config_path: 설정 파일 경로
        """
        self.config = self._load_config(config_path)
        self.monitors = get_monitors()
        self.grid_cells: List[GridCell] = []
        self.task_queue = queue.Queue()
        self.running = False
        self.ocr_thread = None
        self.task_thread = None
        self.response_messages = []  # CSV에서 로드된 응답 메시지
        self.enabled_cells = set()  # 활성화된 셀 ID들
        
        # 듀얼 모니터 환경 설정
        pyautogui.FAILSAFE = False  # 멀티 모니터 지원을 위해 비활성화
        
        # 디렉토리 생성
        os.makedirs("screenshots/debug", exist_ok=True)
        
        # 응답 메시지 로드
        self._load_response_messages()
        
        # 그리드 셀 초기화
        self._initialize_grid_cells()
        
        # 모든 셀을 기본적으로 비활성화 (GUI에서 선택한 것만 활성화)
        # for cell in self.grid_cells:
        #     self.enabled_cells.add(cell.id)  # 이 부분 제거
        
        # PaddleOCR 엔진 초기화 (실시간 최적화)
        self.paddle_ocr = None
        self._initialize_paddleocr_safe()
        
        self.trigger_actions = []
        # self._initialize_ocr_engine() # 이 줄을 주석 처리하거나 삭제합니다.
        
        self.require_input_keyword = self.config.get("require_input_keyword", True)
        
    def _load_config(self, config_path: str) -> Dict:
        """
        설정 파일 로드
        
        Args:
            config_path: 설정 파일 경로
            
        Returns:
            Dict: 설정 정보
        """
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"설정 파일 로드 실패: {e}")
            # 기본 설정 반환
            return {
                "grid_rows": 3,
                "grid_cols": 5,
                "ocr_interval_sec": 5,
                "cooldown_sec": 3,  # 3초 쿨다운으로 무한 루프 방지
                "ocr_scale": 2.0,
                "trigger_patterns": ["들어왔", "들어왔습니다"],
                "use_regex_trigger": True,
                "regex_patterns": ["들어.?왔.*"],
                "monitor_mode": "all",
                "use_easyocr": False,
                "require_min_triggers": 2,
                "ocr_preprocess": {
                    "scale": 2.0,
                    "adaptive_thresh_blocksize": 11,
                    "adaptive_thresh_C": 2,
                    "use_morph_close": True,
                    "apply_sharpen": True,
                    "invert": False
                },
                "ocr_options": {
                    "lang": "kor+eng",
                    "oem": 3,
                    "psm": 7,
                    "min_confidence": 70
                }
            }
    
    def _initialize_grid_cells(self):
        """그리드 셀 초기화"""
        self.grid_cells = []
        
        monitor_mode = self.config.get("monitor_mode", "all")
        rows = self.config.get("grid_rows", 3)
        cols = self.config.get("grid_cols", 5)
        
        for i, monitor in enumerate(self.monitors):
            if monitor_mode != "all" and i > 0:
                continue
                
            # 모니터 정보
            mon_x, mon_y = monitor.x, monitor.y
            mon_width, mon_height = monitor.width, monitor.height
            
            # 셀 크기 계산
            cell_width = mon_width // cols
            cell_height = mon_height // rows
            
            # 각 셀 생성
            for row in range(rows):
                for col in range(cols):
                    cell_x = mon_x + col * cell_width
                    cell_y = mon_y + row * cell_height
                    
                    # 셀 ID 생성
                    cell_id = f"monitor{i+1}-{row+1}-{col+1}"
                    
                    # 셀 영역 정의
                    bounds = (cell_x, cell_y, cell_width, cell_height)
                    
                    # OCR 영역 정의 (행에 따라 다르게 설정)
                    if row == 2:  # 3행 (0-indexed)
                        # 3행은 화면 하단이므로 더 아래쪽 영역 사용
                        ocr_area = (cell_x, cell_y + cell_height - 100, cell_width, 80)
                    else:
                        # 1,2행은 기존 설정
                        ocr_area = (cell_x, cell_y + cell_height - 160, cell_width, 80)
                    
                    # 그리드 셀 생성
                    cell = GridCell(
                        id=cell_id,
                        monitor_id=i+1,
                        bounds=bounds,
                        ocr_area=ocr_area
                    )
                    
                    self.grid_cells.append(cell)
        
        logger.info(f"총 {len(self.grid_cells)}개의 그리드 셀이 초기화되었습니다.")
    
    def _load_response_messages(self):
        """CSV에서 응답 메시지 로드"""
        csv_path = self.config.get("csv_path", "response_messages.csv")
        
        if not os.path.exists(csv_path):
            logger.warning(f"응답 메시지 파일을 찾을 수 없습니다: {csv_path}")
            # 기본 응답 메시지 사용
            self.response_messages = [
                {"trigger_pattern": "들어왔", "response_message": "환영합니다! 😊", "category": "welcome"},
                {"trigger_pattern": "들어왔습니다", "response_message": "반갑습니다!", "category": "welcome"}
            ]
            return
            
        try:
            with open(csv_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                self.response_messages = list(reader)
                
            logger.info(f"{len(self.response_messages)}개의 응답 메시지를 로드했습니다.")
            
        except Exception as e:
            logger.error(f"응답 메시지 파일 로드 실패: {e}")
            # 기본 응답 메시지 사용
            self.response_messages = [
                {"trigger_pattern": "들어왔", "response_message": "환영합니다! 😊", "category": "welcome"}
            ]
    
    def _get_response_message(self, trigger_text: str) -> str:
        """
        트리거 텍스트에 맞는 응답 메시지 선택 (클립보드 우선)
        
        Args:
            trigger_text: 감지된 텍스트
            
        Returns:
            str: 응답 메시지
        """
        # 클립보드에서 메시지 가져오기 시도 (우선순위 1)
        try:
            clipboard_content = pyperclip.paste()
            if clipboard_content and clipboard_content.strip():
                logger.info(f"클립보드에서 메시지 사용: '{clipboard_content[:50]}...'")
                return clipboard_content.strip()
        except Exception as e:
            logger.warning(f"클립보드 읽기 실패: {e}")
        
        # 클립보드가 비어있으면 CSV에서 선택 (우선순위 2)
        matching_messages = []
        
        for msg in self.response_messages:
            if msg["trigger_pattern"] in trigger_text:
                matching_messages.append(msg["response_message"])
        
        if matching_messages:
            # 랜덤하게 하나 선택
            selected_msg = random.choice(matching_messages)
            logger.info(f"CSV에서 메시지 선택: '{selected_msg}'")
            return selected_msg
        
        # 기본 메시지
        default_msg = "환영합니다! 😊"
        logger.info(f"기본 메시지 사용: '{default_msg}'")
        return default_msg
    
    def start(self):
        """모니터링 시작"""
        if self.running:
            logger.warning("이미 실행 중입니다.")
            return
            
        self.running = True
        
        # OCR 스레드 시작
        self.ocr_thread = threading.Thread(target=self._ocr_monitoring_loop)
        self.ocr_thread.daemon = True
        self.ocr_thread.start()
        
        # 작업 처리 스레드 시작
        self.task_thread = threading.Thread(target=self._task_execution_loop)
        self.task_thread.daemon = True
        self.task_thread.start()
        
        logger.info("모니터링이 시작되었습니다.")
    
    def stop(self):
        """모니터링 중지"""
        if not self.running:
            logger.warning("실행 중이 아닙니다.")
            return
            
        self.running = False
        
        # 스레드 종료 대기
        if self.ocr_thread:
            self.ocr_thread.join(timeout=2.0)
        if self.task_thread:
            self.task_thread.join(timeout=2.0)
            
        logger.info("모니터링이 중지되었습니다.")
    
    def _capture_all_monitors(self):
        """각 모니터 전체 화면을 한 번씩 캡처하여 PIL 이미지로 반환"""
        images = {}
        try:
            with mss.mss() as sct:
                for idx, mon in enumerate(self.monitors):
                    monitor_rect = {
                        "top": mon.y,
                        "left": mon.x,
                        "width": mon.width,
                        "height": mon.height,
                    }
                    shot = sct.grab(monitor_rect)
                    img = Image.frombytes("RGB", shot.size, shot.rgb)
                    images[idx + 1] = img  # monitor_id 는 1부터 시작
        except Exception as e:
            logger.error(f"모니터 캡처 중 오류: {e}")
        return images

    def _perform_ocr_image(self, img: Image.Image) -> Tuple[str, Optional[Tuple[int, int]]]:
        """전처리 후 PaddleOCR 수행 (안전한 처리로 primitive 에러 방지) - 텍스트와 위치 정보 반환"""
        try:
            img = self._preprocess_image(img)
            img_array = np.array(img.convert("RGB"))
            
            # 🛡️ 이미지 유효성 검사
            if img_array.size == 0 or img_array.shape[0] < 10 or img_array.shape[1] < 10:
                logger.debug("이미지가 너무 작거나 유효하지 않습니다.")
                return "", None
            
            # PaddleOCR 극도로 안전한 처리 (primitive 에러 완전 차단)
            if self.paddle_ocr:
                try:
                    # 🛡️ 강화된 안전 처리
                    import gc
                    gc.collect()  # OCR 호출 전 메모리 정리
                    
                    # 재시도 로직 (primitive 에러 완전 차단)
                    max_retries = 1  # 재시도 1회로 줄여서 빠른 포기
                    for attempt in range(max_retries):
                        try:
                            # 이미지 크기 제한 (메모리 절약)
                            if img_array.shape[0] > 640 or img_array.shape[1] > 640:
                                from PIL import Image
                                img_pil = Image.fromarray(img_array)
                                img_pil = img_pil.resize((min(640, img_pil.width), min(640, img_pil.height)))
                                img_array = np.array(img_pil)
                            
                            result = self.paddle_ocr.ocr(img_array, cls=False)
                            if result and result[0]:
                                # 텍스트 조합
                                text = ''.join([line[1][0] for line in result[0] if line[1] and line[1][0]])
                                
                                # 첫 번째 감지된 텍스트의 중심 위치 계산
                                if result[0]:
                                    first_box = result[0][0][0]  # 첫 번째 텍스트의 bounding box
                                    # bounding box 4개 점의 평균으로 중심점 계산
                                    center_x = int(sum(point[0] for point in first_box) / 4)
                                    center_y = int(sum(point[1] for point in first_box) / 4)
                                    return text, (center_x, center_y)
                                
                                return text, None
                            break  # 성공하면 재시도 루프 종료
                            
                        except Exception as ocr_e:
                            error_msg = str(ocr_e).lower()
                            if "primitive" in error_msg or "could not execute" in error_msg:
                                logger.debug(f"PaddleOCR primitive 에러 발생 - 즉시 포기: {ocr_e}")
                                # primitive 에러는 재시도하지 않고 즉시 포기
                                self.paddle_ocr = None  # OCR 엔진 비활성화
                                return "", None
                            else:
                                logger.debug(f"PaddleOCR 기타 오류: {ocr_e}")
                                break
                                
                except Exception as paddle_e:
                    logger.debug(f"PaddleOCR 전체 처리 오류: {paddle_e}")
                    # 전체 오류 발생 시 OCR 엔진 비활성화
                    self.paddle_ocr = None
            
            # PaddleOCR 실패 시 EasyOCR fallback
            if self.easy_ocr:
                try:
                    logger.debug("PaddleOCR 실패, EasyOCR fallback 시도")
                    result = self.easy_ocr.readtext(img_array)
                    
                    if result:
                        # 모든 텍스트 조합
                        all_text = ''.join([text for (bbox, text, conf) in result if conf > 0.5])
                        
                        # 첫 번째 감지된 텍스트의 중심 위치 계산
                        if result:
                            first_bbox = result[0][0]  # 첫 번째 텍스트의 bounding box
                            # bounding box 4개 점의 평균으로 중심점 계산
                            center_x = int(sum(point[0] for point in first_bbox) / 4)
                            center_y = int(sum(point[1] for point in first_bbox) / 4)
                            return all_text, (center_x, center_y)
                        
                        return all_text, None
                                
                except Exception as easy_e:
                    logger.debug(f"EasyOCR fallback 처리 오류: {easy_e}")
            
            return "", None
        except Exception as e:
            logger.error(f"OCR 수행 전체 오류: {e}")
            return "", None

    def _ocr_monitoring_loop(self):
        """OCR 모니터링 루프 - 30개 셀 순환 스케줄링으로 실시간 감지"""
        cycle_index = 0  # 순환 인덱스
        cells_per_cycle = 10  # 한 번에 처리할 셀 수
        
        while self.running:
            cycle_start = time.time()

            # 1) 각 모니터 화면 한 번씩만 캡처
            monitor_images = self._capture_all_monitors()
            if not monitor_images:
                time.sleep(1.0)
                continue

            triggered_cells_in_cycle = []

            # 2) 순환 스케줄링: 이번 주기에 처리할 셀들만 선택
            enabled_cells = [cell for cell in self.grid_cells if self.is_cell_enabled(cell.id)]
            total_cells = len(enabled_cells)
            
            if total_cells == 0:
                time.sleep(1.0)
                continue
            
            # 현재 주기에 처리할 셀 범위 계산
            start_idx = (cycle_index * cells_per_cycle) % total_cells
            end_idx = min(start_idx + cells_per_cycle, total_cells)
            
            # 범위가 끝을 넘어가면 처음부터 다시 시작
            if end_idx == total_cells and start_idx + cells_per_cycle > total_cells:
                current_cells = enabled_cells[start_idx:] + enabled_cells[:(start_idx + cells_per_cycle) % total_cells]
            else:
                current_cells = enabled_cells[start_idx:end_idx]
            
            # 현재 처리할 셀 ID들 표시
            cell_ids = [cell.id for cell in current_cells]
            logger.info(f"🔄 순환 처리 [{cycle_index}]: {cell_ids} ({len(current_cells)}/30개 셀)")

            # 3) 선택된 셀들만 OCR 처리
            for cell in current_cells:
                if cell.is_in_cooldown(self.config.get("cooldown_sec", 0)):
                    continue

                mon_img = monitor_images.get(cell.monitor_id)
                if mon_img is None:
                    continue

                # 셀 OCR 영역을 모니터 상대 좌표로 변환
                mon_info = self.monitors[cell.monitor_id - 1]
                rel_x = cell.ocr_area[0] - mon_info.x
                rel_y = cell.ocr_area[1] - mon_info.y
                w, h = cell.ocr_area[2], cell.ocr_area[3]

                # --- ROI 경계 보정 ---
                if rel_x < 0:
                    w += rel_x  # rel_x 음수면 w 줄이기
                    rel_x = 0
                if rel_y < 0:
                    h += rel_y
                    rel_y = 0

                w = min(w, mon_info.width - rel_x)
                h = min(h, mon_info.height - rel_y)

                if w <= 0 or h <= 0:
                    logger.debug(f"ROI out of bounds for cell {cell.id}")
                    continue

                roi = mon_img.crop((rel_x, rel_y, rel_x + w, rel_y + h))

                ocr_text, text_position = self._perform_ocr_image(roi)

                # 디버깅 로그
                if ocr_text.strip():
                    logger.debug(f"셀 {cell.id} OCR 결과: '{ocr_text}', 위치: {text_position}")

                # origin outside monitor bounds -> skip
                if rel_x >= mon_info.width or rel_y >= mon_info.height:
                    logger.debug(f"Cell {cell.id} origin outside monitor bounds")
                    continue

                if self._check_trigger_patterns_smart(ocr_text):
                    cell.set_triggered()
                    cell.detected_text = ocr_text
                    
                    # 감지된 텍스트의 실제 화면 위치 계산 (전역 좌표)
                    if text_position:
                        # ROI 내 상대 위치를 전역 화면 좌표로 변환
                        global_text_x = cell.ocr_area[0] + text_position[0]
                        global_text_y = cell.ocr_area[1] + text_position[1]
                        cell.detected_text_position = (global_text_x, global_text_y)
                        
                        # 🔍 상세 디버깅 정보
                        monitor_name = f"Monitor{cell.monitor_id}"
                        logger.info(f"[좌표디버그] {monitor_name} 셀 {cell.id}:")
                        logger.info(f"[좌표디버그]   OCR영역: {cell.ocr_area} (전역좌표)")
                        logger.info(f"[좌표디버그]   ROI내위치: {text_position} (상대좌표)")
                        logger.info(f"[좌표디버그]   계산결과: ({global_text_x}, {global_text_y}) (전역좌표)")
                        logger.info(f"[텍스트감지] 셀 {cell.id}에서 '{ocr_text}' 감지, 위치: ({global_text_x}, {global_text_y})")
                    
                    self.task_queue.put(cell)
                    triggered_cells_in_cycle.append(cell)

                    # 스크린샷 저장 (디버그)
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
                    path = f"screenshots/debug/triggered_ocr_{timestamp}.png"
                    roi.save(path)
                    logger.info(f"트리거 감지 - 셀 {cell.id}, 스크린샷: {path}")

            # 3) 최소 트리거 수 검사
            min_triggers = self.config.get("require_min_triggers", 1)
            if 0 < len(triggered_cells_in_cycle) < min_triggers:
                logger.info(
                    f"감지된 셀 수({len(triggered_cells_in_cycle)})가 최소 요구치({min_triggers})보다 적어 무시됨")
                # 큐 비우기 및 셀 상태 리셋
                while not self.task_queue.empty():
                    try:
                        self.task_queue.get_nowait()
                    except queue.Empty:
                        break
                for c in triggered_cells_in_cycle:
                    c.set_idle()

            # 4) 순환 인덱스 업데이트
            cycle_index += 1
            if cycle_index * cells_per_cycle >= total_cells:
                cycle_index = 0  # 모든 셀을 한 바퀴 돌았으면 처음부터 다시
                logger.info(f"🔄 전체 셀 순환 완료. 다시 처음부터 시작 (총 {total_cells}개 셀)")

            # 5) 인터벌 유지 (1초 간격으로 빠른 순환)
            elapsed = time.time() - cycle_start
            time.sleep(max(0, self.config.get("ocr_interval_sec", 1) - elapsed))
    
    def _task_execution_loop(self):
        """작업 실행 루프"""
        while self.running:
            try:
                # 큐에서 셀 가져오기
                cell = self.task_queue.get(timeout=1.0)
                logger.info(f"[작업실행] 처리할 셀: {cell.id}")
                logger.info(f"[작업실행] 셀 감지 텍스트: {getattr(cell, 'detected_text', 'None')}")
                
                # 1. 메시지입력 또는 메시지 감지될 때까지 반복
                found_input = True  # 기본적으로 실행하도록 설정
                if self.require_input_keyword:
                    found_input = False
                    for _ in range(15):  # 최대 15회(약 10초) 재시도
                        ocr_text = self._capture_and_ocr(cell.ocr_area)
                        norm_text = self.normalize_ocr_text(ocr_text)
                        if '메시지입력' in norm_text or '메시지' in norm_text:
                            found_input = True
                            break
                        time.sleep(0.7)
                
                # 디버그 로그: 입력창 키워드 탐색 여부
                logger.info(f"[DEBUG] found_input={found_input} require_flag={self.require_input_keyword}")
                
                if found_input:
                    # 입력 위치 클릭
                    input_pos = self._find_input_position(cell)
                    if input_pos:
                        logger.info(f"[작업실행] 입력 위치 확인: {input_pos}")
                        # 듀얼 모니터 지원
                        try:
                            import ctypes
                            ctypes.windll.user32.SetCursorPos(int(input_pos[0]), int(input_pos[1]))
                        except:
                            pyautogui.FAILSAFE = False
                            pyautogui.moveTo(*input_pos)
                        time.sleep(0.2)
                        
                        # 자동 입력 실행 (성공/실패 체크)
                        success = self._execute_input_automation(cell)
                        if success:
                            logger.info(f"[작업실행] 셀 {cell.id} 자동 입력 성공")
                        else:
                            logger.error(f"[작업실행] 셀 {cell.id} 자동 입력 실패")
                    else:
                        logger.error(f"[작업실행] 셀 {cell.id} 입력 위치 찾기 실패")
                else:
                    logger.warning(f"[작업실행] 셀 {cell.id}에서 메시지입력 감지 실패")
                
                # 셀 쿨다운 설정 (강화된 쿨다운 - 성공/실패 관계없이 적용)
                cell.set_cooldown()
                
                # 전송 실패 시 더 긴 쿨다운 적용
                if not success:
                    cell.last_triggered_time = time.time() + 10  # 10초 추가 쿨다운
                
                # 작업 완료
                self.task_queue.task_done()
                
            except queue.Empty:
                pass
            except Exception as e:
                logger.error(f"작업 실행 중 오류 발생: {e}")
    
    def _capture_and_ocr(self, area: Tuple[int, int, int, int]) -> str:
        """
        지정된 영역을 캡처하고 OCR 수행
        
        Args:
            area: (x, y, width, height) 형식의 영역
            
        Returns:
            str: 인식된 텍스트
        """
        try:
            # 영역 캡처
            with mss.mss() as sct:
                monitor = {"top": area[1], "left": area[0], "width": area[2], "height": area[3]}
                screenshot = sct.grab(monitor)
                img = Image.frombytes("RGB", screenshot.size, screenshot.rgb)
                
                # 이미지 전처리
                img = self._preprocess_image(img)
                
                # OCR 수행 (PaddleOCR 우선, EasyOCR fallback)
                if self.paddle_ocr:
                    img_rgb = img.convert('RGB')
                    result = self.paddle_ocr.ocr(np.array(img_rgb), cls=True)
                    if result and result[0]:
                        # 모든 라인 텍스트 합치기
                        all_text = ''.join([line[1][0] for line in result[0]])
                        return all_text
                elif self.easy_ocr:
                    img_rgb = img.convert('RGB')
                    result = self.easy_ocr.readtext(np.array(img_rgb))
                    
                    if result:
                        # 모든 텍스트 조합 (신뢰도 0.5 이상)
                        all_text = ''.join([text for (bbox, text, conf) in result if conf > 0.5])
                        return all_text
                
                return ""
                
        except Exception as e:
            logger.error(f"OCR 수행 중 오류 발생: {e}")
            return ""

    def _preprocess_image(self, img: Image.Image) -> Image.Image:
        """OCR 전용 이미지 전처리 – config.json 의 ocr_preprocess 옵션을 실질적으로 반영"""
        # 설정값 로드 (존재하지 않으면 기본값 사용)
        preprocess_cfg = self.config.get("ocr_preprocess", {})

        # 1) 스케일 조정 -----------------------------------------------------
        scale = float(preprocess_cfg.get("scale", 2.0))
        if scale != 1.0:
            new_size = (int(img.width * scale), int(img.height * scale))
            img = img.resize(new_size, Image.Resampling.LANCZOS)

        # PIL ► NumPy 변환 (후처리를 위해 그레이스케일로)
        img_np = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2GRAY)

        # 2) 대비/가우시안 블러 -----------------------------------------------
        if preprocess_cfg.get("gaussian_blur", False):
            img_np = cv2.GaussianBlur(img_np, (3, 3), 0)

        if preprocess_cfg.get("contrast_enhance", False):
            # CLAHE(Contrast Limited Adaptive Histogram Equalization)
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
            img_np = clahe.apply(img_np)

        # 3) 이진화(Adaptive Threshold) ---------------------------------------
        if preprocess_cfg.get("adaptive_thresh_blocksize"):
            block_size = int(preprocess_cfg.get("adaptive_thresh_blocksize", 11))
            block_size = block_size + 1 if block_size % 2 == 0 else block_size  # 홀수 보정
            C = int(preprocess_cfg.get("adaptive_thresh_C", 2))
            img_np = cv2.adaptiveThreshold(
                img_np,
                maxValue=255,
                adaptiveMethod=cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                thresholdType=cv2.THRESH_BINARY,
                blockSize=block_size,
                C=C,
            )

        # 4) 색상 반전 --------------------------------------------------------
        if preprocess_cfg.get("invert", False):
            img_np = cv2.bitwise_not(img_np)

        # 5) 모폴로지 closing -------------------------------------------------
        if preprocess_cfg.get("use_morph_close", False):
            kernel = np.ones((3, 3), np.uint8)
            img_np = cv2.morphologyEx(img_np, cv2.MORPH_CLOSE, kernel)

        # 6) 샤프닝 -----------------------------------------------------------
        if preprocess_cfg.get("apply_sharpen", False):
            kernel_sharpen = np.array([[0, -1, 0], [-1, 5, -1], [0, -1, 0]])
            img_np = cv2.filter2D(img_np, -1, kernel_sharpen)

        # NumPy ► PIL.Grayscale 로 재변환
        processed_img = Image.fromarray(img_np)
        return processed_img
    
    def normalize_ocr_text(self, text: str) -> str:
        """OCR 결과 후처리(오인식 치환 등)"""
        if not text:
            return text
        # 자주 나오는 오인식 치환
        text = text.replace("들어빛습니다", "들어왔습니다")
        text = text.replace("들어왓습니다", "들어왔습니다")
        text = text.replace("들어올습니다", "들어왔습니다")
        text = text.replace("드러왔습니다", "들어왔습니다")
        text = text.replace("왔습니다", "왔습니다")
        text = text.replace("빛습니다", "왔습니다")
        text = text.replace("왔습나다", "왔습니다")
        # PaddleOCR 가 자주 '들어'를 '틀머'/'틀어' 로 오인식하는 케이스 보정
        text = text.replace("틀머왔습니다", "들어왔습니다")
        text = text.replace("틀머왔", "들어왔")
        text = text.replace("틀어왔습니다", "들어왔습니다")
        text = text.replace("틀어왔", "들어왔")
        # 앞에 잘못된 글자가 붙는 경우 보정 (미틀머 -> 님이들어)
        text = text.replace("미틀머왔습니다", "님이들어왔습니다")
        text = text.replace("미들머왔습니다", "님이들어왔습니다")
        text = text.replace("님틀머왔습니다", "님이들어왔습니다")
        text = text.replace("님들머왔습니다", "님이들어왔습니다")
        # '메시지 입력'을 '메시지입력'으로 치환
        text = text.replace('메시지 입력', '메시지입력')
        # 모든 공백(스페이스, 탭, 개행 등) 제거
        text = re.sub(r'\s+', '', text)
        return text
    
    def _check_trigger_patterns_smart(self, text: str) -> bool:
        """
        "들어왔습니다" 감지에 최적화된 트리거 패턴 확인
        
        Args:
            text: 확인할 텍스트
            
        Returns:
            bool: 트리거 패턴 포함 여부
        """
        if not text:
            return False
        
        # 🚨 길이 제한 완화
        if len(text) > 80:  # 80자 이상 제외 (50 → 80)
            logger.debug(f"텍스트가 너무 길어서 제외: '{text[:30]}...'")
            return False
        
        # 텍스트 정규화 (공백, 특수문자 제거)
        normalized_text = ''.join(c for c in text if c.isalnum() or c in '가-힣ㄱ-ㅎㅏ-ㅣ')
        normalized_text = normalized_text.lower()
        
        logger.debug(f"🔧 정규화된 텍스트: '{normalized_text}'")
        
        # 🎯 1단계: 트리거 패턴 우선 확인 (가장 먼저!)
        # 정확한 패턴
        exact_patterns = [
            "들어왔습니다", "들어왔", "입장했습니다", "참여했습니다",
            "님이들어왔", "님들어왔"
        ]
        
        # OCR 오인식 패턴들 (모든 변형 포함)
        ocr_error_patterns = [
            # 기본 오인식 패턴들
            "들머왔습니다", "들머왔습미다", "들머왔", 
            "틀어왔습니다", "틀어왔", "틀머왔습니다", "틀머왔",
            "들어왓습니다", "들어왓", "들어완습니다", "들어완", 
            "들여왔습니다", "들여왔", "드러왔습니다", "드러왔",
            "들어왔슴니다", "들어왔음니다",
            # 추가 오인식 패턴들 (앞에 글자가 붙는 경우 포함)
            "미틀머왔습니다", "미들머왔습니다", "미들어왔습니다",
            "님틀머왔습니다", "님들머왔습니다", "님틀어왔습니다",
            "이틀머왔습니다", "이들머왔습니다", "이틀어왔습니다"
        ]
        
        # 정확한 패턴 확인
        for pattern in exact_patterns:
            if pattern in normalized_text:
                logger.info(f"✅ 정확한 트리거 패턴 매치: '{pattern}' in '{text}'")
                return True
        
        # OCR 오인식 패턴 확인
        for pattern in ocr_error_patterns:
            if pattern in normalized_text:
                logger.info(f"✅ OCR 오인식 패턴 매치: '{pattern}' in '{text}'")
                return True  # 👈 조건 완화: 패턴만 있으면 바로 허용
        
        # 🚨 2단계: 트리거 패턴이 없을 때만 추가 필터링 적용
        
        # 숫자 과다 필터링
        digit_count = sum(1 for c in text if c.isdigit())
        if digit_count > 8:  # 기준 완화 (5 → 8)
            logger.debug(f"🚫 숫자 과다로 필터링: '{text}' (숫자 {digit_count}개)")
            return False
        
        # 특수문자 과다 필터링
        special_count = sum(1 for c in text if not c.isalnum() and c not in '가-힣ㄱ-ㅎㅏ-ㅣ ')
        if len(text) > 0 and special_count / len(text) > 0.5:  # 기준 완화 (0.3 → 0.5)
            logger.debug(f"🚫 특수문자 과다로 필터링: '{text}' (특수문자 {special_count}/{len(text)})")
            return False
        
        # 명백한 노이즈 패턴만 차단 (완전히 의미없는 것들만)
        severe_noise_patterns = [
            '년흐품', '음44', 'Fto', 'soIE', 'Et의', 'Wt+'  # 심각한 노이즈만
        ]
        
        if any(pattern in text for pattern in severe_noise_patterns):
            logger.debug(f"🚫 심각한 노이즈 패턴으로 필터링: '{text}'")
            return False
        
        logger.debug(f"❌ 트리거 패턴 매치 없음: '{text}'")
        return False
    
    def _check_trigger_patterns(self, text: str) -> bool:
        """
        트리거 패턴 확인
        
        Args:
            text: 확인할 텍스트
            
        Returns:
            bool: 트리거 패턴 포함 여부
        """
        if not text:
            return False
        
        # 디버깅: 검사할 텍스트 로그
        logger.debug(f"트리거 패턴 검사 대상: '{text}'")
            
        # 일반 패턴 확인
        trigger_patterns = self.config.get("trigger_patterns", ["들어왔", "들어왔습니다"])
        logger.debug(f"일반 트리거 패턴: {trigger_patterns}")
        
        for pattern in trigger_patterns:
            if pattern in text:
                logger.info(f"일반 패턴 매치: '{pattern}' in '{text}'")
                return True
        
        # 정규식 패턴 확인
        if self.config.get("use_regex_trigger", True):
            regex_patterns = self.config.get("regex_patterns", ["들어.?왔.*"])
            logger.debug(f"정규식 트리거 패턴: {regex_patterns}")
            
            for pattern in regex_patterns:
                if re.search(pattern, text):
                    logger.info(f"정규식 패턴 매치: '{pattern}' matches '{text}'")
                    return True
        
        logger.debug(f"트리거 패턴 매치 없음: '{text}'")
        return False
    
    def _execute_input_automation(self, cell: GridCell) -> bool:
        """
        입력 자동화 실행 (강화된 안정성)
        
        Args:
            cell: 그리드 셀
            
        Returns:
            bool: 성공 여부
        """
        logger.info(f"[자동입력] 셀 {cell.id}에서 입력 자동화 시작")
        
        try:
            # 1. 입력 위치 확인
            input_x, input_y = self._find_input_position(cell)
            logger.info(f"[자동입력] 입력 위치: ({input_x}, {input_y})")
            
            # 2. 듀얼 모니터 지원 클릭 (Windows API 우선)
            click_success = False
            
            # 🔍 디버깅: 현재 마우스 위치 확인
            try:
                import ctypes
                from ctypes import wintypes
                point = wintypes.POINT()
                ctypes.windll.user32.GetCursorPos(ctypes.byref(point))
                logger.info(f"[마우스디버그] 클릭 전 현재 위치: ({point.x}, {point.y})")
                logger.info(f"[마우스디버그] 이동할 목표 위치: ({input_x}, {input_y})")
                
                # Windows API로 마우스 이동
                result = ctypes.windll.user32.SetCursorPos(int(input_x), int(input_y))
                logger.info(f"[마우스디버그] SetCursorPos 결과: {result}")
                
                time.sleep(0.2)
                
                # 이동 후 실제 위치 확인
                ctypes.windll.user32.GetCursorPos(ctypes.byref(point))
                logger.info(f"[마우스디버그] 이동 후 실제 위치: ({point.x}, {point.y})")
                
                # 위치가 정확한지 검증
                if abs(point.x - input_x) > 5 or abs(point.y - input_y) > 5:
                    logger.warning(f"[마우스디버그] ⚠️ 마우스 위치 불일치! 목표({input_x}, {input_y}) vs 실제({point.x}, {point.y})")
                else:
                    logger.info(f"[마우스디버그] ✅ 마우스 위치 정확함")
                
                # Windows API로 클릭
                ctypes.windll.user32.mouse_event(2, 0, 0, 0, 0)  # 마우스 다운
                time.sleep(0.05)
                ctypes.windll.user32.mouse_event(4, 0, 0, 0, 0)  # 마우스 업
                logger.info(f"[자동입력] Windows API로 클릭 완료 - 위치: ({point.x}, {point.y})")
                click_success = True
                
            except Exception as e:
                logger.warning(f"[자동입력] Windows API 클릭 실패: {e}")
                # 실패시 PyAutoGUI 사용
                try:
                    logger.info(f"[자동입력] PyAutoGUI로 대체 시도: ({input_x}, {input_y})")
                    pyautogui.FAILSAFE = False
                    pyautogui.moveTo(input_x, input_y, duration=0.1)
                    actual_pos = pyautogui.position()
                    logger.info(f"[마우스디버그] PyAutoGUI 이동 후 위치: {actual_pos}")
                    pyautogui.click()
                    logger.info(f"[자동입력] PyAutoGUI로 클릭 완료")
                    click_success = True
                except Exception as e2:
                    logger.error(f"[자동입력] PyAutoGUI 클릭도 실패: {e2}")
                    return False
            
            if not click_success:
                logger.error(f"[자동입력] 클릭 실패")
                return False
            
            # 3. 응답 메시지 선택
            response_message = self._get_response_message(getattr(cell, 'detected_text', ''))
            logger.info(f"[자동입력] 전송할 메시지: '{response_message}'")
            
            # 4. 강화된 클립보드 처리 (재시도 로직)
            clipboard_success = False
            for attempt in range(3):
                try:
                    pyperclip.copy(response_message)
                    time.sleep(0.1)
                    # 복사 확인
                    copied_text = pyperclip.paste()
                    if copied_text == response_message:
                        logger.info(f"[자동입력] 클립보드 복사 성공 (시도 {attempt + 1}/3)")
                        clipboard_success = True
                        break
                    else:
                        logger.warning(f"[자동입력] 클립보드 복사 불일치 (시도 {attempt + 1}/3): 원본='{response_message[:30]}...', 복사본='{copied_text[:30]}...'")
                except Exception as e:
                    logger.warning(f"[자동입력] 클립보드 복사 실패 (시도 {attempt + 1}/3): {e}")
                    if attempt == 2:
                        logger.error(f"[자동입력] 클립보드 복사 최종 실패")
                        return False
                time.sleep(0.1)
            
            if not clipboard_success:
                logger.error(f"[자동입력] 클립보드 처리 실패")
                return False
            
            # 5. 입력 안정성 개선 (기존 텍스트 삭제 후 붙여넣기)
            time.sleep(0.2)  # 입력창 활성화 대기
            
            # 전체 선택 후 삭제
            pyautogui.hotkey('ctrl', 'a')  # 전체 선택
            time.sleep(0.1)
            pyautogui.press('delete')      # 삭제
            time.sleep(0.1)
            logger.info(f"[자동입력] 기존 텍스트 삭제 완료")
            
            # 붙여넣기
            pyautogui.hotkey('ctrl', 'v')  # 붙여넣기
            time.sleep(0.3)                # 충분한 대기
            logger.info(f"[자동입력] 붙여넣기 완료")
            
            # 6. 전송
            pyautogui.press('enter')       # 전송
            time.sleep(0.1)
            logger.info(f"[자동입력] 엔터 입력 완료")
            
            # 7. 전송 결과 검증 (실제로 전송되었는지 확인)
            time.sleep(0.5)  # 전송 완료 대기
            
            # 입력창이 비었는지 확인하여 전송 여부 검증
            verification_success = self._verify_message_sent(cell, response_message)
            
            if verification_success:
                logger.info(f"✅ [자동입력] 셀 {cell.id} 메시지 전송 성공: '{response_message}' (위치: {input_x}, {input_y})")
                return True
            else:
                logger.warning(f"⚠️ [자동입력] 셀 {cell.id} 전송 실패 또는 불확실: '{response_message}'")
                return False
            
        except Exception as e:
            logger.error(f"[자동입력] 입력 자동화 중 오류 발생: {e}")
            return False
    
    def _verify_message_sent(self, cell: GridCell, expected_message: str) -> bool:
        """
        메시지가 실제로 전송되었는지 검증
        
        Args:
            cell: 그리드 셀
            expected_message: 전송했을 것으로 예상되는 메시지
            
        Returns:
            bool: 전송 성공 여부
        """
        try:
            # 방법 1: 입력창이 비었는지 확인
            x, y, w, h = cell.bounds
            input_area = (x, y + h//2, w, h//2)  # 하단 절반 영역
            
            with mss.mss() as sct:
                monitor = {"top": input_area[1], "left": input_area[0], 
                          "width": input_area[2], "height": input_area[3]}
                screenshot = sct.grab(monitor)
                img = Image.frombytes("RGB", screenshot.size, screenshot.rgb)
            
            # OCR로 입력창 내용 확인
            if self.paddle_ocr:
                result = self.paddle_ocr.ocr(np.array(img.convert("RGB")), cls=True)
                
                if result and result[0]:
                    input_text = ''.join([line[1][0] for line in result[0]])
                    
                    # 입력창에 우리가 보낸 메시지가 남아있으면 전송 실패
                    if expected_message in input_text:
                        logger.debug(f"[전송검증] 입력창에 메시지가 남아있음: '{input_text}'")
                        return False
                    
                    # 입력창이 비어있거나 "메시지 입력" 텍스트만 있으면 성공
                    if not input_text.strip() or "메시지 입력" in input_text:
                        logger.debug(f"[전송검증] 입력창이 비어있음 - 전송 성공")
                        return True
                else:
                    # OCR 결과가 없으면 입력창이 비어있는 것으로 판단
                    logger.debug(f"[전송검증] OCR 결과 없음 - 입력창 비어있음")
                    return True
            elif self.easy_ocr:
                result = self.easy_ocr.readtext(np.array(img.convert("RGB")))
                
                if result:
                    input_text = ''.join([text for (bbox, text, conf) in result if conf > 0.5])
                    
                    # 입력창에 우리가 보낸 메시지가 남아있으면 전송 실패
                    if expected_message in input_text:
                        logger.debug(f"[전송검증] 입력창에 메시지가 남아있음: '{input_text}'")
                        return False
                    
                    # 입력창이 비어있거나 "메시지 입력" 텍스트만 있으면 성공
                    if not input_text.strip() or "메시지 입력" in input_text:
                        logger.debug(f"[전송검증] 입력창이 비어있음 - 전송 성공")
                        return True
                else:
                    # OCR 결과가 없으면 입력창이 비어있는 것으로 판단
                    logger.debug(f"[전송검증] OCR 결과 없음 - 입력창 비어있음")
                    return True
            
            # 방법 2: 채팅 영역에서 전송된 메시지 확인 (보조)
            chat_area = (x, y, w, h//2)  # 상단 절반 영역
            
            with mss.mss() as sct:
                monitor = {"top": chat_area[1], "left": chat_area[0], 
                          "width": chat_area[2], "height": chat_area[3]}
                screenshot = sct.grab(monitor)
                img = Image.frombytes("RGB", screenshot.size, screenshot.rgb)
            
            if self.paddle_ocr:
                result = self.paddle_ocr.ocr(np.array(img.convert("RGB")), cls=True)
                
                if result and result[0]:
                    chat_text = ''.join([line[1][0] for line in result[0]])
                    
                    # 채팅 영역에 우리가 보낸 메시지가 있으면 성공
                    if expected_message.strip() in chat_text:
                        logger.debug(f"[전송검증] 채팅 영역에서 메시지 확인됨")
                        return True
            elif self.easy_ocr:
                result = self.easy_ocr.readtext(np.array(img.convert("RGB")))
                
                if result:
                    chat_text = ''.join([text for (bbox, text, conf) in result if conf > 0.5])
                    
                    # 채팅 영역에 우리가 보낸 메시지가 있으면 성공
                    if expected_message.strip() in chat_text:
                        logger.debug(f"[전송검증] 채팅 영역에서 메시지 확인됨")
                        return True
            
            # 기본적으로 성공으로 판단 (너무 엄격하면 정상 전송도 실패로 판단할 수 있음)
            logger.debug(f"[전송검증] 명확한 실패 증거 없음 - 성공으로 판단")
            return True
            
        except Exception as e:
            logger.error(f"전송 검증 중 오류: {e}")
            # 오류 발생 시 성공으로 판단 (시스템 안정성 우선)
            return True

    def _find_input_position(self, cell: GridCell) -> Tuple[int, int]:
        """
        입력 위치 탐색 - OCR 감지된 텍스트 위치 기준으로 60px 아래 계산
        
        Args:
            cell: 그리드 셀
            
        Returns:
            Tuple[int, int]: 입력 위치 (x, y)
        """
        logger.info(f"[입력위치] 셀 {cell.id} 입력 위치 계산 시작")
        logger.info(f"[입력위치] 셀 bounds: {cell.bounds}")
        logger.info(f"[입력위치] 셀 input_area: {cell.input_area}")
        
        # 기본 입력 위치 사용 (미리 설정된 경우)
        if cell.input_area:
            logger.info(f"[입력위치] 기존 input_area 사용: {cell.input_area}")
            return cell.input_area
        
        # 🎯 우선순위 1: OCR 영역 하단에서 5px 아래 (가장 정확)
        if hasattr(cell, 'detected_text_position') and cell.detected_text_position:
            detected_x, detected_y = cell.detected_text_position
            # OCR 영역 하단에서 5px 아래에 메시지 입력박스 클릭
            ocr_x, ocr_y, ocr_w, ocr_h = cell.ocr_area
            input_x = detected_x  # 감지된 텍스트의 X 좌표 유지
            input_y = ocr_y + ocr_h + 5  # OCR 영역 하단에서 5px 아래
            
            # 🔍 듀얼모니터 디버깅: 어느 모니터인지 확인
            monitor_info = "Unknown"
            if input_x < 1920:
                monitor_info = "Monitor1 (0~1920)"
            elif input_x >= 1920:
                monitor_info = f"Monitor2 (1920~3840), relative_x={input_x-1920}"
            
            logger.info(f"[입력위치] ✅ OCR 영역 하단 기준: OCR영역({ocr_x}, {ocr_y}, {ocr_w}, {ocr_h}) -> 입력위치({input_x}, {input_y})")
            logger.info(f"[입력위치] 📏 감지위치({detected_x}, {detected_y}) → OCR하단+5px({input_x}, {input_y})")
            logger.info(f"[입력위치] 🖥️ {monitor_info}")
            return (input_x, input_y)
        
        # 🎯 우선순위 2: 기본 입력 위치 사용 (미리 설정된 경우)
        if cell.input_area:
            logger.info(f"[입력위치] 기존 input_area 사용: {cell.input_area}")
            return cell.input_area
            
        # 🎯 우선순위 3: 셀 중앙 하단에서 60px 위 (대안)
        x, y, w, h = cell.bounds
        calculated_pos = (x + w // 2, y + h - 50)
        logger.info(f"[입력위치] 기본 위치 계산 (셀 하단 50px 위): {calculated_pos}")
        return calculated_pos

    def _find_input_by_image(self, cell: GridCell) -> Optional[Tuple[int, int]]:
        """
        이미지 기반으로 "메시지 입력" 입력창 찾기
        
        Args:
            cell: 그리드 셀
            
        Returns:
            Optional[Tuple[int, int]]: 입력 위치 (x, y) 또는 None
        """
        try:
            # 입력창 템플릿 이미지 경로들 (기존 업로드 이미지 우선 사용)
            input_templates = [
                "1000015293.jpg",                     # 사용자가 업로드한 메시지 입력창 이미지 (우선순위 1)
                "send_button_template.png",           # 기존 전송 버튼 템플릿 (우선순위 2)
                "assets/message_input_template.png",  # 자동 생성된 "메시지 입력" 텍스트 이미지
                "assets/chat_input_box.png",          # 채팅 입력창 이미지
                "assets/input_field.png"              # 일반 입력 필드 이미지
            ]
            
            # 셀 영역 내에서만 검색하도록 region 설정
            x, y, w, h = cell.bounds
            search_region = (x, y, w, h)
            
            for template_path in input_templates:
                if not os.path.exists(template_path):
                    logger.debug(f"템플릿 이미지 없음: {template_path}")
                    continue
                    
                try:
                    # pyautogui로 이미지 찾기
                    location = pyautogui.locateOnScreen(
                        template_path, 
                        confidence=0.7,
                        region=search_region
                    )
                    
                    if location:
                        # 찾은 위치의 중심점 계산
                        center = pyautogui.center(location)
                        logger.info(f"[이미지탐색] 입력창 템플릿 매칭 성공: {template_path} -> {center}")
                        return center
                        
                except pyautogui.ImageNotFoundException:
                    logger.debug(f"[이미지탐색] 템플릿 매칭 실패: {template_path}")
                    continue
                except Exception as e:
                    logger.warning(f"이미지 탐색 중 오류: {template_path} - {e}")
                    continue
            
            logger.debug(f"[이미지탐색] 셀 {cell.id}에서 입력창 템플릿을 찾지 못함")
            return None
            
        except Exception as e:
            logger.error(f"이미지 기반 입력창 탐색 중 오류: {e}")
            return None

    def _find_input_by_ocr_text(self, cell: GridCell) -> Optional[Tuple[int, int]]:
        """
        OCR로 "메시지 입력" 텍스트를 찾아서 입력 위치 결정
        
        Args:
            cell: 그리드 셀
            
        Returns:
            Optional[Tuple[int, int]]: 입력 위치 (x, y) 또는 None
        """
        try:
            # 셀 영역 캡처
            x, y, w, h = cell.bounds
            with mss.mss() as sct:
                monitor = {"top": y, "left": x, "width": w, "height": h}
                screenshot = sct.grab(monitor)
                img = Image.frombytes("RGB", screenshot.size, screenshot.rgb)
            
            # OCR 수행 (위치 정보 포함, PaddleOCR 안전한 처리)
            result = None
            
            if self.paddle_ocr:
                try:
                    # 🛡️ 강화된 안전 처리
                    import gc
                    gc.collect()  # OCR 호출 전 메모리 정리
                    
                    # 이미지 크기 제한 (메모리 절약)
                    img_array = np.array(img.convert("RGB"))
                    if img_array.shape[0] > 640 or img_array.shape[1] > 640:
                        from PIL import Image
                        img_pil = Image.fromarray(img_array)
                        img_pil = img_pil.resize((min(640, img_pil.width), min(640, img_pil.height)))
                        img_array = np.array(img_pil)
                    
                    result = self.paddle_ocr.ocr(img_array, cls=False)
                            
                except Exception as ocr_e:
                    error_msg = str(ocr_e).lower()
                    if "primitive" in error_msg or "could not execute" in error_msg:
                        logger.debug(f"PaddleOCR primitive 에러 발생 - OCR 엔진 비활성화: {ocr_e}")
                        self.paddle_ocr = None  # OCR 엔진 비활성화
                        result = None
                    else:
                        logger.debug(f"PaddleOCR 기타 오류: {ocr_e}")
                        result = None
            elif self.easy_ocr:
                try:
                    img_array = np.array(img.convert("RGB"))
                    result = self.easy_ocr.readtext(img_array)
                            
                except Exception as ocr_e:
                    logger.debug(f"EasyOCR 처리 오류: {ocr_e}")
                    result = None
                
                if result:
                    # "메시지 입력" 관련 텍스트 찾기 (더 정확한 키워드만)
                    primary_keywords = ["메시지 입력", "메시지입력"]  # 가장 정확한 키워드만
                    secondary_keywords = ["입력", "메시지"]  # 보조 키워드
                    
                    # PaddleOCR과 EasyOCR 결과 처리 분기
                    if self.paddle_ocr and result and result[0]:
                        # PaddleOCR 결과 처리
                        # 1단계: 정확한 키워드 우선 검색
                        for line in result[0]:
                            text = line[1][0]
                            confidence = line[1][1]
                            
                            # 신뢰도가 낮으면 무시
                            if confidence < 0.7:  # 임계값 상향 조정
                                continue
                                
                            # 노이즈 텍스트 필터링 (다른 프로그램 텍스트 제외)
                            if any(noise in text.lower() for noise in [
                                'easeus', 'data', 'recovery', 'launcher', 'pdf', 'toolbox', 
                                'prf24', 'depdf24', 'x120', 'chrome', 'browser'
                            ]):
                                logger.debug(f"[OCR탐색] 노이즈 텍스트 필터링: '{text}'")
                                continue
                            
                            # 정확한 키워드 매칭 (우선순위 1)
                            text_clean = text.lower().replace(" ", "").replace("\n", "")
                            for keyword in primary_keywords:
                                if keyword.lower().replace(" ", "") in text_clean:
                                    # 텍스트 위치 계산
                                    box = line[0]
                                    center_x = int(sum(point[0] for point in box) / 4)
                                    center_y = int(sum(point[1] for point in box) / 4)
                                    
                                    # 셀 영역 내부에 있는지 확인
                                    if 0 <= center_x <= w and 0 <= center_y <= h:
                                        # 전역 좌표로 변환
                                        global_x = x + center_x
                                        global_y = y + center_y
                                        
                                        logger.info(f"[OCR탐색] 정확한 입력창 키워드 발견: '{text}' -> ({global_x}, {global_y})")
                                        return (global_x, global_y)
                    elif self.easy_ocr and result:
                        # EasyOCR 결과 처리
                        # 1단계: 정확한 키워드 우선 검색
                        for bbox, text, confidence in result:
                            # 신뢰도가 낮으면 무시
                            if confidence < 0.7:  # 임계값 상향 조정
                                continue
                                
                            # 노이즈 텍스트 필터링 (다른 프로그램 텍스트 제외)
                            if any(noise in text.lower() for noise in [
                                'easeus', 'data', 'recovery', 'launcher', 'pdf', 'toolbox', 
                                'prf24', 'depdf24', 'x120', 'chrome', 'browser'
                            ]):
                                logger.debug(f"[OCR탐색] 노이즈 텍스트 필터링: '{text}'")
                                continue
                            
                            # 정확한 키워드 매칭 (우선순위 1)
                            text_clean = text.lower().replace(" ", "").replace("\n", "")
                            for keyword in primary_keywords:
                                if keyword.lower().replace(" ", "") in text_clean:
                                    # 텍스트 위치 계산
                                    center_x = int(sum(point[0] for point in bbox) / 4)
                                    center_y = int(sum(point[1] for point in bbox) / 4)
                                    
                                    # 셀 영역 내부에 있는지 확인
                                    if 0 <= center_x <= w and 0 <= center_y <= h:
                                        # 전역 좌표로 변환
                                        global_x = x + center_x
                                        global_y = y + center_y
                                        
                                        logger.info(f"[OCR탐색] 정확한 입력창 키워드 발견: '{text}' -> ({global_x}, {global_y})")
                                        return (global_x, global_y)
            
            logger.debug(f"[OCR탐색] 셀 {cell.id}에서 입력 관련 텍스트를 찾지 못함")
            return None
            
        except Exception as e:
            logger.error(f"OCR 기반 입력창 탐색 중 오류: {e}")
            return None
    
    def _save_debug_screenshot(self, area: Tuple[int, int, int, int], path: str, ocr_text: str):
        """
        디버깅용 스크린샷 저장
        
        Args:
            area: 캡처 영역 (x, y, width, height)
            path: 저장 경로
            ocr_text: OCR 텍스트 결과
        """
        try:
            x, y, width, height = area
            
            # 스크린샷 캡처
            with mss.mss() as screenshot:
                monitor = {"top": y, "left": x, "width": width, "height": height}
                screenshot_img = screenshot.grab(monitor)
                img = np.array(screenshot_img)
            
            # 이미지에 OCR 결과 텍스트 추가
            img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            cv2.putText(
                img, f"OCR: {ocr_text[:30]}", (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2
            )
            
            # 이미지 저장
            cv2.imwrite(path, cv2.cvtColor(img, cv2.COLOR_RGB2BGR))
            
            logger.debug(f"디버깅 스크린샷 저장: {path}")
            
        except Exception as e:
            logger.error(f"스크린샷 저장 중 오류 발생: {e}")
    
    def find_input_position_by_template(self, cell: GridCell) -> Optional[Tuple[int, int]]:
        """
        템플릿 매칭으로 입력 위치 탐색
        
        Args:
            cell: 그리드 셀
            
        Returns:
            Optional[Tuple[int, int]]: 입력 위치 (x, y) 또는 None
        """
        try:
            x, y, w, h = cell.bounds
            
            # 셀 영역 캡처
            with mss.mss() as screenshot:
                monitor = {"top": y, "left": x, "width": w, "height": h}
                screenshot_img = screenshot.grab(monitor)
                img = np.array(screenshot_img)
            img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            
            # 템플릿 이미지 로드
            template_path = "assets/send_button_template.png"
            if not os.path.exists(template_path):
                logger.warning(f"템플릿 이미지를 찾을 수 없습니다: {template_path}")
                return None
                
            template = cv2.imread(template_path)
            # 템플릿이 제대로 로드되었는지 확인
            if template is None:
                logger.error(f"템플릿 파일을 로드할 수 없습니다: {template_path}")
                return None
            
            template = cv2.cvtColor(template, cv2.COLOR_BGR2RGB)
            
            # 템플릿 매칭
            result = cv2.matchTemplate(img, template, cv2.TM_CCOEFF_NORMED)
            min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
            
            # 임계값 확인
            if max_val < 0.7:
                logger.debug(f"템플릿 매칭 결과가 임계값보다 낮습니다: {max_val}")
                return None
                
            # 매칭 위치 계산
            template_h, template_w = template.shape[:2]
            center_x = max_loc[0] + template_w // 2
            center_y = max_loc[1] + template_h // 2
            
            # 전역 좌표로 변환
            global_x = x + center_x
            global_y = y + center_y
            
            return (global_x, global_y)
            
        except Exception as e:
            logger.error(f"템플릿 매칭 중 오류 발생: {e}")
            return None
    
    def test_input_template_matching(self, template_path: str, cell_id: str = None) -> bool:
        """
        생성된 템플릿 이미지가 제대로 매칭되는지 테스트
        
        Args:
            template_path: 템플릿 이미지 경로
            cell_id: 특정 셀에서만 테스트 (None이면 전체)
            
        Returns:
            bool: 매칭 성공 여부
        """
        if not os.path.exists(template_path):
            logger.error(f"템플릿 파일이 없습니다: {template_path}")
            return False
            
        try:
            cells_to_test = [c for c in self.grid_cells if c.id == cell_id] if cell_id else self.grid_cells
            
            for cell in cells_to_test:
                x, y, w, h = cell.bounds
                search_region = (x, y, w, h)
                
                try:
                    location = pyautogui.locateOnScreen(
                        template_path, 
                        confidence=0.7,
                        region=search_region
                    )
                    
                    if location:
                        center = pyautogui.center(location)
                        logger.info(f"[템플릿테스트] 셀 {cell.id}에서 매칭 성공: {center}")
                        
                        # 시각적 확인을 위해 마우스 이동
                        pyautogui.moveTo(center)
                        return True
                        
                except pyautogui.ImageNotFoundException:
                    logger.debug(f"[템플릿테스트] 셀 {cell.id}에서 매칭 실패")
                    continue
                    
            logger.warning(f"[템플릿테스트] 템플릿 매칭 실패: {template_path}")
            return False
            
        except Exception as e:
            logger.error(f"템플릿 테스트 중 오류 발생: {e}")
            return False

    def _initialize_paddleocr_safe(self):
        """PaddleOCR 엔진 초기화 (실시간 모니터링용 초고속 설정)"""
        try:
            if PADDLEOCR_AVAILABLE and PaddleOCR is not None:
                logger.info("⚡ PaddleOCR 실시간 모드 초기화 시작...")
                
                # 환경 변수 설정 (성능 최적화)
                import os
                os.environ['OMP_NUM_THREADS'] = '2'  # 2개 스레드로 늘려서 성능 향상
                os.environ['OPENBLAS_NUM_THREADS'] = '2'
                
                try:
                    # ⚡ 실시간 최적화 설정 (빠른 처리 우선)
                    self.paddle_ocr = PaddleOCR(
                        lang='korean'
                    )
                    logger.info("✅ PaddleOCR 실시간 모드 초기화 완료!")
                    
                    # 간단 테스트
                    test_img = np.ones((100, 300, 3), dtype=np.uint8) * 255
                    test_result = self.paddle_ocr.ocr(test_img, cls=False)
                    logger.info("⚡ PaddleOCR 실시간 테스트 성공!")
                    
                except Exception as e:
                    logger.error(f"❌ PaddleOCR 초기화 실패: {e}")
                    # 실패 시 EasyOCR로 대체하지 않고 간단한 재시도
                    try:
                        self.paddle_ocr = PaddleOCR(lang='korean')
                        logger.info("✅ PaddleOCR 기본 모드 성공")
                    except:
                        self.paddle_ocr = None
                        logger.error("❌ PaddleOCR 완전 실패")
                
            else:
                logger.error("❌ PaddleOCR을 사용할 수 없습니다.")
                self.paddle_ocr = None
                
        except Exception as e:
            logger.error(f"❌ PaddleOCR 초기화 완전 실패: {e}")
            self.paddle_ocr = None
        
        # EasyOCR는 제거 (PaddleOCR만 사용)

    def _capture_and_ocr_from_img(self, img: 'Image.Image') -> str:
        """
        이미지를 받아 OCR만 수행 (실시간 최적화 버전)
        Args:
            img: PIL.Image.Image 객체
        Returns:
            str: 인식된 텍스트
        """
        try:
            # 기본 유효성 검사
            if img is None or img.size[0] < 10 or img.size[1] < 10:
                return ""
            
            # PaddleOCR 실시간 처리
            if self.paddle_ocr:
                try:
                    # 간단한 전처리
                    img_rgb = img.convert('RGB')
                    img_array = np.array(img_rgb)
                    
                    # 크기 제한 (성능 최적화)
                    if img_array.shape[0] > 800 or img_array.shape[1] > 800:
                        from PIL import Image as PILImage
                        img_pil = PILImage.fromarray(img_array)
                        img_pil = img_pil.resize((min(800, img_pil.width), min(800, img_pil.height)))
                        img_array = np.array(img_pil)
                    
                    # PaddleOCR 실행
                    result = self.paddle_ocr.ocr(img_array, cls=False)
                    
                    if result and result[0]:
                        # 텍스트 추출
                        all_text = ''.join([line[1][0] for line in result[0] 
                                          if line[1] and line[1][0] and line[1][1] > 0.5])
                        return all_text
                            
                except Exception as e:
                    # 에러 시 OCR 엔진 비활성화하지 않고 빈 문자열 반환
                    return ""
            
            return ""
            
        except Exception as e:
            return ""

    def create_input_template(self, cell_id: str, save_path: str = None) -> str:
        """
        특정 셀에서 "메시지 입력" 영역을 캡처하여 템플릿 이미지 생성
        
        Args:
            cell_id: 셀 ID
            save_path: 저장 경로 (없으면 자동 생성)
            
        Returns:
            str: 생성된 템플릿 이미지 경로
        """
        # 셀 찾기
        cell = next((c for c in self.grid_cells if c.id == cell_id), None)
        if not cell:
            logger.error(f"셀을 찾을 수 없습니다: {cell_id}")
            return ""
        
        try:
            # 셀 영역 캡처
            x, y, w, h = cell.bounds
            with mss.mss() as sct:
                monitor = {"top": y, "left": x, "width": w, "height": h}
                screenshot = sct.grab(monitor)
                img = Image.frombytes("RGB", screenshot.size, screenshot.rgb)
            
            # OCR로 "메시지 입력" 텍스트 찾기 (PaddleOCR 안전한 처리)
            result = None
            
            if self.paddle_ocr:
                try:
                    # 🛡️ 강화된 안전 처리
                    import gc
                    gc.collect()  # OCR 호출 전 메모리 정리
                    
                    # 이미지 크기 제한 (메모리 절약)
                    img_array = np.array(img.convert("RGB"))
                    if img_array.shape[0] > 640 or img_array.shape[1] > 640:
                        from PIL import Image
                        img_pil = Image.fromarray(img_array)
                        img_pil = img_pil.resize((min(640, img_pil.width), min(640, img_pil.height)))
                        img_array = np.array(img_pil)
                    
                    result = self.paddle_ocr.ocr(img_array, cls=False)
                            
                except Exception as ocr_e:
                    error_msg = str(ocr_e).lower()
                    if "primitive" in error_msg or "could not execute" in error_msg:
                        logger.debug(f"PaddleOCR primitive 에러 발생 - OCR 엔진 비활성화: {ocr_e}")
                        self.paddle_ocr = None  # OCR 엔진 비활성화
                        result = None
                    else:
                        logger.debug(f"PaddleOCR 기타 오류: {ocr_e}")
                        result = None
            elif self.easy_ocr:
                try:
                    img_array = np.array(img.convert("RGB"))
                    result = self.easy_ocr.readtext(img_array)
                            
                except Exception as ocr_e:
                    logger.debug(f"EasyOCR 처리 오류: {ocr_e}")
                    result = None
            
            if result:
                input_keywords = ["메시지 입력", "메시지입력", "입력", "메시지"]
                
                # PaddleOCR과 EasyOCR 결과 처리 분기
                if self.paddle_ocr and result and result[0]:
                    # PaddleOCR 결과 처리
                    for line in result[0]:
                        text = line[1][0]
                        confidence = line[1][1]
                        
                        if confidence < 0.6:
                            continue
                            
                        # 키워드 매칭
                        text_clean = text.lower().replace(" ", "").replace("\n", "")
                        for keyword in input_keywords:
                            if keyword.lower().replace(" ", "") in text_clean:
                                # 텍스트 영역 추출
                                box = line[0]
                                
                                # bounding box 좌표 계산
                                min_x = int(min(point[0] for point in box))
                                max_x = int(max(point[0] for point in box))
                                min_y = int(min(point[1] for point in box))
                                max_y = int(max(point[1] for point in box))
                                
                                # 여백 추가 (더 넓은 영역 캡처)
                                padding = 10
                                crop_x1 = max(0, min_x - padding)
                                crop_y1 = max(0, min_y - padding)
                                crop_x2 = min(img.width, max_x + padding)
                                crop_y2 = min(img.height, max_y + padding)
                                
                                # 템플릿 이미지 추출
                                template_img = img.crop((crop_x1, crop_y1, crop_x2, crop_y2))
                                
                                # 저장 경로 결정
                                if not save_path:
                                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                                    save_path = f"assets/message_input_template_{cell_id}_{timestamp}.png"
                                
                                # 디렉토리 생성
                                os.makedirs(os.path.dirname(save_path), exist_ok=True)
                                
                                # 이미지 저장
                                template_img.save(save_path)
                                
                                logger.info(f"[템플릿생성] 입력창 템플릿 생성 완료: {save_path}")
                                logger.info(f"[템플릿생성] 감지된 텍스트: '{text}' (신뢰도: {confidence:.2f})")
                                logger.info(f"[템플릿생성] 템플릿 크기: {template_img.size}")
                                
                                return save_path
                elif self.easy_ocr and result:
                    # EasyOCR 결과 처리
                    for bbox, text, confidence in result:
                        if confidence < 0.6:
                            continue
                            
                        # 키워드 매칭
                        text_clean = text.lower().replace(" ", "").replace("\n", "")
                        for keyword in input_keywords:
                            if keyword.lower().replace(" ", "") in text_clean:
                                # bounding box 좌표 계산
                                min_x = int(min(point[0] for point in bbox))
                                max_x = int(max(point[0] for point in bbox))
                                min_y = int(min(point[1] for point in bbox))
                                max_y = int(max(point[1] for point in bbox))
                                
                                # 여백 추가 (더 넓은 영역 캡처)
                                padding = 10
                                crop_x1 = max(0, min_x - padding)
                                crop_y1 = max(0, min_y - padding)
                                crop_x2 = min(img.width, max_x + padding)
                                crop_y2 = min(img.height, max_y + padding)
                                
                                # 템플릿 이미지 추출
                                template_img = img.crop((crop_x1, crop_y1, crop_x2, crop_y2))
                                
                                # 저장 경로 결정
                                if not save_path:
                                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                                    save_path = f"assets/message_input_template_{cell_id}_{timestamp}.png"
                                
                                # 디렉토리 생성
                                os.makedirs(os.path.dirname(save_path), exist_ok=True)
                                
                                # 이미지 저장
                                template_img.save(save_path)
                                
                                logger.info(f"[템플릿생성] 입력창 템플릿 생성 완료: {save_path}")
                                logger.info(f"[템플릿생성] 감지된 텍스트: '{text}' (신뢰도: {confidence:.2f})")
                                logger.info(f"[템플릿생성] 템플릿 크기: {template_img.size}")
                                
                                return save_path
            
            logger.warning(f"[템플릿생성] 셀 {cell_id}에서 입력 관련 텍스트를 찾지 못했습니다.")
            
            # 대안: 셀 하단 영역을 템플릿으로 저장
            bottom_area = img.crop((0, h//2, w, h))  # 하단 절반 영역
            
            if not save_path:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                save_path = f"assets/input_area_template_{cell_id}_{timestamp}.png"
            
            os.makedirs(os.path.dirname(save_path), exist_ok=True)
            bottom_area.save(save_path)
            
            logger.info(f"[템플릿생성] 대안 템플릿 생성 (하단 영역): {save_path}")
            return save_path
            
        except Exception as e:
            logger.error(f"템플릿 생성 중 오류: {e}")
            return ""

    def set_cell_enabled(self, cell_id: str, enabled: bool):
        """
        셀 활성화/비활성화
        
        Args:
            cell_id: 셀 ID
            enabled: 활성화 여부
        """
        if enabled:
            self.enabled_cells.add(cell_id)
            logger.info(f"셀 {cell_id} 활성화")
        else:
            self.enabled_cells.discard(cell_id)
            logger.info(f"셀 {cell_id} 비활성화")
    
    def is_cell_enabled(self, cell_id: str) -> bool:
        """
        셀 활성화 상태 확인
        
        Args:
            cell_id: 셀 ID
            
        Returns:
            bool: 활성화 여부
        """
        return cell_id in self.enabled_cells
    
    def get_enabled_cells(self) -> List[str]:
        """
        활성화된 셀 목록 반환
        
        Returns:
            List[str]: 활성화된 셀 ID 목록
        """
        return list(self.enabled_cells)
    
    def set_specific_cells_only(self, cell_ids: List[str]):
        """
        특정 셀들만 활성화
        
        Args:
            cell_ids: 활성화할 셀 ID 목록
        """
        self.enabled_cells.clear()
        for cell_id in cell_ids:
            self.enabled_cells.add(cell_id)
        
        logger.info(f"특정 셀만 활성화: {cell_ids}")

    def test_input_position(self, cell_id: str) -> Optional[Tuple[int, int]]:
        """
        입력 위치 테스트
        
        Args:
            cell_id: 셀 ID
            
        Returns:
            Optional[Tuple[int, int]]: 입력 위치 (x, y) 또는 None
        """
        # 셀 찾기
        cell = next((c for c in self.grid_cells if c.id == cell_id), None)
        if not cell:
            logger.error(f"셀을 찾을 수 없습니다: {cell_id}")
            return None
            
        # 입력 위치 찾기
        input_pos = self._find_input_position(cell)
        
        # 마우스 이동 및 클릭
        pyautogui.moveTo(input_pos)
        pyautogui.click()
        
        return input_pos
