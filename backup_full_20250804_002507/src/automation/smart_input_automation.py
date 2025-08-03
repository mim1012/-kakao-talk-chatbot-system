#!/usr/bin/env python3
"""
스마트 입력 자동화 시스템
텍스트 박스 감지 및 자동 입력 처리
"""
from __future__ import annotations

import cv2
import numpy as np
import pyautogui
import pyperclip
import time
import mss
import logging
from dataclasses import dataclass

# PyAutoGUI 설정
pyautogui.FAILSAFE = False
pyautogui.PAUSE = 0.1  # 각 동작 간 최소 대기 시간

# Windows DPI 인식 설정
try:
    import ctypes
    from ctypes import wintypes
    
    # DPI 인식 설정
    ctypes.windll.shcore.SetProcessDpiAwareness(2)  # PROCESS_PER_MONITOR_DPI_AWARE
    
    # 스케일링 비율 가져오기
    def get_dpi_scale():
        try:
            user32 = ctypes.windll.user32
            dpi = user32.GetDpiForSystem()
            return dpi / 96.0  # 96 DPI가 100% 스케일
        except:
            return 1.0
    
    DPI_SCALE = get_dpi_scale()
    print(f"DPI 스케일 감지: {DPI_SCALE}")
    
except Exception as e:
    print(f"DPI 설정 실패: {e}")
    DPI_SCALE = 1.0

@dataclass
class ClickResult:
    """클릭 결과 데이터"""
    success: bool
    position: tuple[int, int]
    method: str
    confidence: float = 0.0
    message: str = ""

class SmartInputAutomation:
    """스마트 입력 자동화 클래스"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.response_messages = [
            "어서와요👋\n\n▪ 보이스룸이 켜져있을 경우 오른쪽 상단 ❌ 또는 ☰ 메뉴에서 '공지사항' 먼저 확인해 주세요!\n\n▪ 채팅방 하트 꾹 눌러주세요❤\n\n▪입장하시면 같이 인사해주세요❤"
        ]
        
        # 타이밍 설정
        self.timing = {
            'click_delay': 0.3,
            'paste_delay': 0.2,
            'send_delay': 0.5,
            'verification_delay': 1.0
        }
    
    def find_text_input_position(self, cell_bounds: tuple[int, int, int, int], 
                                ocr_area: tuple[int, int, int, int],
                                method: str = "ocr_based") -> ClickResult:
        """텍스트 입력 위치 찾기"""
        
        match method:
            case "ocr_based":
                return self._find_input_ocr_based(cell_bounds, ocr_area)
            case "template_matching":
                return self._find_input_template_matching(cell_bounds, ocr_area)
            case "adaptive_search":
                return self._find_input_adaptive_search(cell_bounds, ocr_area)
            case "multi_strategy":
                return self._find_input_multi_strategy(cell_bounds, ocr_area)
            case _:
                return ClickResult(False, (0, 0), "unknown", 0.0, "Unknown method")
    
    def _find_input_ocr_based(self, cell_bounds: tuple[int, int, int, int], 
                             ocr_area: tuple[int, int, int, int]) -> ClickResult:
        """OCR 영역 기반 입력 위치 계산"""
        try:
            ocr_x, ocr_y, ocr_w, ocr_h = ocr_area
            
            # 셀 하단으로부터 위로 5px 떨어진 곳, 중앙 X 좌표
            cell_x, cell_y, cell_w, cell_h = cell_bounds
            input_x = cell_x + cell_w // 2
            input_y = cell_y + cell_h - 5
            
            self.logger.info(f"📊 셀 정보: 위치=({cell_x}, {cell_y}), 크기=({cell_w}, {cell_h})")
            self.logger.info(f"🎯 계산된 클릭 위치: 중앙X={input_x}, 하단-5px={input_y}")
            
            # 안전 범위 확인 (셀 범위 내에 있는지 체크)
            if not (cell_x <= input_x <= cell_x + cell_w and 
                    cell_y <= input_y <= cell_y + cell_h):
                # 범위를 벗어나면 기본 위치로 조정
                input_x = cell_x + cell_w // 2
                input_y = cell_y + cell_h - 5
            
            return ClickResult(
                success=True,
                position=(input_x, input_y),
                method="ocr_based",
                confidence=0.9,
                message=f"OCR 기반 위치: ({input_x}, {input_y})"
            )
            
        except Exception as e:
            return ClickResult(False, (0, 0), "ocr_based", 0.0, f"Error: {e}")
    
    def _find_input_template_matching(self, cell_bounds: tuple[int, int, int, int], 
                                     ocr_area: tuple[int, int, int, int]) -> ClickResult:
        """템플릿 매칭으로 흰색 텍스트 박스 찾기"""
        try:
            cell_x, cell_y, cell_w, cell_h = cell_bounds
            
            # 셀 하단 영역 캡처 (텍스트 박스가 있을 가능성이 높은 영역)
            search_area = {
                'left': cell_x,
                'top': cell_y + cell_h - 100,  # 하단 100px 영역
                'width': cell_w,
                'height': 100
            }
            
            with mss.mss() as sct:
                screenshot = sct.grab(search_area)
                image = np.array(screenshot)
                
                # BGR로 변환
                image_bgr = cv2.cvtColor(image, cv2.COLOR_BGRA2BGR)
                
                # 흰색 텍스트 박스 감지
                white_boxes = self._detect_white_text_boxes(image_bgr)
                
                if white_boxes:
                    # 가장 큰 흰색 영역을 텍스트 박스로 가정
                    best_box = max(white_boxes, key=lambda x: x[2] * x[3])
                    box_x, box_y, box_w, box_h = best_box
                    
                    # 절대 좌표로 변환
                    abs_x = cell_x + box_x + box_w // 2
                    abs_y = cell_y + cell_h - 100 + box_y + box_h // 2
                    
                    return ClickResult(
                        success=True,
                        position=(abs_x, abs_y),
                        method="template_matching",
                        confidence=0.8,
                        message=f"템플릿 매칭 성공: {box_w}x{box_h} 박스"
                    )
                else:
                    # 템플릿 매칭 실패 시 기본 위치 사용 (셀 하단으로부터 5px 위)
                    fallback_x = cell_x + cell_w // 2
                    fallback_y = cell_y + cell_h - 5
                    
                    return ClickResult(
                        success=True,
                        position=(fallback_x, fallback_y),
                        method="template_matching_fallback",
                        confidence=0.5,
                        message="템플릿 매칭 실패, 기본 위치 사용"
                    )
                    
        except Exception as e:
            return ClickResult(False, (0, 0), "template_matching", 0.0, f"Error: {e}")
    
    def _detect_white_text_boxes(self, image: np.ndarray) -> list[tuple[int, int, int, int]]:
        """흰색 텍스트 박스 감지"""
        try:
            # 그레이스케일 변환
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
            # 흰색 영역 감지 (임계값: 200 이상)
            _, white_mask = cv2.threshold(gray, 200, 255, cv2.THRESH_BINARY)
            
            # 노이즈 제거
            kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
            white_mask = cv2.morphologyEx(white_mask, cv2.MORPH_CLOSE, kernel)
            white_mask = cv2.morphologyEx(white_mask, cv2.MORPH_OPEN, kernel)
            
            # 컨투어 찾기
            contours, _ = cv2.findContours(white_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            boxes = []
            for contour in contours:
                x, y, w, h = cv2.boundingRect(contour)
                
                # 텍스트 박스 같은 크기 필터링 (너무 작거나 크지 않은)
                if 50 <= w <= 300 and 15 <= h <= 50:
                    # 종횡비 확인 (텍스트 박스는 보통 가로가 세로보다 길다)
                    aspect_ratio = w / h
                    if 2.0 <= aspect_ratio <= 10.0:
                        boxes.append((x, y, w, h))
            
            return boxes
            
        except Exception as e:
            self.logger.error(f"흰색 텍스트 박스 감지 오류: {e}")
            return []
    
    def _find_input_adaptive_search(self, cell_bounds: tuple[int, int, int, int], 
                                   ocr_area: tuple[int, int, int, int]) -> ClickResult:
        """적응형 검색 - 여러 위치 시도"""
        try:
            cell_x, cell_y, cell_w, cell_h = cell_bounds
            ocr_x, ocr_y, ocr_w, ocr_h = ocr_area
            
            # 후보 위치들 (우선순위 순) - 모두 셀 하단으로부터 5px 위 기준
            candidate_positions = [
                # 기본 위치 (셀 하단 5px 위)
                (cell_x + cell_w // 2, cell_y + cell_h - 5),
                (cell_x + cell_w // 2, cell_y + cell_h - 3),
                (cell_x + cell_w // 2, cell_y + cell_h - 7),
                
                # 셀 하단 기반 변형
                (cell_x + cell_w // 2, cell_y + cell_h - 10),
                (cell_x + cell_w // 2, cell_y + cell_h - 15),
                (cell_x + cell_w // 2, cell_y + cell_h - 8),
                
                # 좌우 변형 (셀 하단 5px 위 기준)
                (cell_x + cell_w * 0.4, cell_y + cell_h - 5),
                (cell_x + cell_w * 0.6, cell_y + cell_h - 5),
            ]
            
            # 각 위치의 적합성 평가
            best_position = None
            best_score = 0
            
            for pos_x, pos_y in candidate_positions:
                # 범위 확인
                if not (cell_x <= pos_x <= cell_x + cell_w and 
                        cell_y <= pos_y <= cell_y + cell_h):
                    continue
                
                # 점수 계산 (셀 하단 5px 위에 가까울수록 높은 점수)
                target_y = cell_y + cell_h - 5  # 목표 위치: 셀 하단 5px 위
                distance_from_target = abs(pos_y - target_y)
                x_center_distance = abs(pos_x - (cell_x + cell_w // 2))  # 중앙에서 떨어진 거리
                
                score = 100 - distance_from_target * 2.0 - x_center_distance * 0.1
                
                if score > best_score:
                    best_score = score
                    best_position = (int(pos_x), int(pos_y))
            
            if best_position:
                return ClickResult(
                    success=True,
                    position=best_position,
                    method="adaptive_search",
                    confidence=best_score / 100.0,
                    message=f"적응형 검색 성공: 점수 {best_score:.1f}"
                )
            else:
                return ClickResult(False, (0, 0), "adaptive_search", 0.0, "적합한 위치 없음")
                
        except Exception as e:
            return ClickResult(False, (0, 0), "adaptive_search", 0.0, f"Error: {e}")
    
    def _find_input_multi_strategy(self, cell_bounds: tuple[int, int, int, int], 
                                  ocr_area: tuple[int, int, int, int]) -> ClickResult:
        """다중 전략 - 여러 방법을 조합"""
        try:
            strategies = ["ocr_based", "template_matching", "adaptive_search"]
            results = []
            
            for strategy in strategies:
                result = self.find_text_input_position(cell_bounds, ocr_area, strategy)
                if result.success:
                    results.append(result)
            
            if not results:
                return ClickResult(False, (0, 0), "multi_strategy", 0.0, "모든 전략 실패")
            
            # 가장 높은 신뢰도의 결과 선택
            best_result = max(results, key=lambda x: x.confidence)
            best_result.method = "multi_strategy"
            best_result.message = f"최고 전략: {best_result.method} (신뢰도: {best_result.confidence:.2f})"
            
            return best_result
            
        except Exception as e:
            return ClickResult(False, (0, 0), "multi_strategy", 0.0, f"Error: {e}")
    
    def execute_auto_input(self, cell_bounds: tuple[int, int, int, int], 
                          ocr_area: tuple[int, int, int, int],
                          message: str | None = None,
                          method: str = "multi_strategy") -> bool:
        """자동 입력 실행"""
        try:
            self.logger.info(f"🎯 자동화 시작 - 셀: {cell_bounds}, OCR: {ocr_area}, 방법: {method}")
            
            # 1단계: 입력 위치 찾기
            click_result = self.find_text_input_position(cell_bounds, ocr_area, method)
            
            if not click_result.success:
                self.logger.error(f"❌ 1단계 실패 - 입력 위치 찾기: {click_result.message}")
                return False
            
            self.logger.info(f"✅ 1단계 성공 - 입력 위치: {click_result.position}, 신뢰도: {click_result.confidence}")
            
            # 2단계: 메시지 준비
            if message is None:
                import random
                message = random.choice(self.response_messages)
            
            self.logger.info(f"✅ 2단계 성공 - 메시지 준비 완료 (길이: {len(message)}자)")
            
            # 3단계: 클립보드에 메시지 복사
            if not self._copy_to_clipboard(message):
                self.logger.error("❌ 3단계 실패 - 클립보드 복사 실패")
                return False
            
            self.logger.info("✅ 3단계 성공 - 클립보드 복사 완료")
            
            # 4단계: 텍스트 박스 클릭
            if not self._click_position(click_result.position):
                self.logger.error(f"❌ 4단계 실패 - 텍스트 박스 클릭 실패: {click_result.position}")
                return False
            
            self.logger.info(f"✅ 4단계 성공 - 텍스트 박스 클릭: {click_result.position}")
            
            # 5단계: 기존 텍스트 선택 및 삭제
            time.sleep(self.timing['click_delay'])
            pyautogui.hotkey('ctrl', 'a')  # 전체 선택
            time.sleep(0.1)
            pyautogui.press('delete')  # 삭제
            self.logger.info("✅ 5단계 성공 - 기존 텍스트 삭제")
            
            # 6단계: 붙여넣기
            time.sleep(self.timing['paste_delay'])
            pyautogui.hotkey('ctrl', 'v')
            self.logger.info("✅ 6단계 성공 - 메시지 붙여넣기")
            
            # 7단계: 전송
            time.sleep(self.timing['send_delay'])
            pyautogui.press('enter')
            self.logger.info("✅ 7단계 성공 - 엔터키 전송")
            
            # 8단계: 전송 확인
            time.sleep(self.timing['verification_delay'])
            success = self._verify_message_sent(click_result.position)
            
            if success:
                self.logger.info(f"🎉 전체 자동화 성공! 메시지 전송됨")
            else:
                self.logger.error(f"❌ 8단계 실패 - 메시지 전송 확인 실패")
            
            return success
            
        except Exception as e:
            self.logger.error(f"자동 입력 실행 오류: {e}")
            return False
    
    def _copy_to_clipboard(self, text: str, max_retries: int = 3) -> bool:
        """클립보드에 텍스트 복사"""
        for attempt in range(max_retries):
            try:
                pyperclip.copy(text)
                time.sleep(0.1)
                
                # 복사 확인
                if pyperclip.paste() == text:
                    return True
                    
            except Exception as e:
                self.logger.warning(f"클립보드 복사 시도 {attempt + 1} 실패: {e}")
                time.sleep(0.2)
        
        return False
    
    def _click_position(self, position: tuple[int, int]) -> bool:
        """위치 클릭 - DPI 스케일링 고려"""
        try:
            x, y = position
            
            # DPI 스케일링 보정 적용
            scaled_x = int(x / DPI_SCALE) if DPI_SCALE != 1.0 else x
            scaled_y = int(y / DPI_SCALE) if DPI_SCALE != 1.0 else y
            
            self.logger.info(f"🖱️ 원본 좌표: ({x}, {y})")
            if DPI_SCALE != 1.0:
                self.logger.info(f"🔧 DPI 보정 좌표: ({scaled_x}, {scaled_y}) (스케일: {DPI_SCALE})")
            
            # 현재 마우스 위치 확인
            current_x, current_y = pyautogui.position()
            self.logger.info(f"📍 현재 마우스 위치: ({current_x}, {current_y})")
            
            # 마우스 이동 (보정된 좌표 사용)
            pyautogui.moveTo(scaled_x, scaled_y, duration=0.3)
            time.sleep(0.2)
            
            # 이동 후 위치 확인
            moved_x, moved_y = pyautogui.position()
            self.logger.info(f"🎯 이동 후 마우스 위치: ({moved_x}, {moved_y})")
            
            # 좌표 불일치 확인 (보정된 좌표와 비교)
            tolerance = max(5, int(10 * DPI_SCALE))  # DPI에 따른 허용 오차
            if abs(moved_x - scaled_x) > tolerance or abs(moved_y - scaled_y) > tolerance:
                self.logger.warning(f"⚠️ 마우스 위치 불일치! 목표:({scaled_x}, {scaled_y}) 실제:({moved_x}, {moved_y})")
                
                # 강제로 다시 이동 시도
                pyautogui.moveTo(scaled_x, scaled_y, duration=0.1)
                time.sleep(0.1)
            
            # 클릭 (실제 마우스 위치에서)
            final_x, final_y = pyautogui.position()
            pyautogui.click(final_x, final_y)
            self.logger.info(f"✅ 클릭 완료: ({final_x}, {final_y})")
            
            return True
            
        except Exception as e:
            self.logger.error(f"❌ 클릭 실패: {e}")
            return False
    
    def _verify_message_sent(self, input_position: tuple[int, int]) -> bool:
        """메시지 전송 확인"""
        try:
            # 입력창 다시 클릭
            pyautogui.click(input_position[0], input_position[1])
            time.sleep(0.2)
            
            # 전체 선택 후 복사
            pyautogui.hotkey('ctrl', 'a')
            time.sleep(0.1)
            pyautogui.hotkey('ctrl', 'c')
            time.sleep(0.1)
            
            # 클립보드 내용 확인 (비어있으면 전송됨)
            current_text = pyperclip.paste().strip()
            return len(current_text) == 0
            
        except Exception as e:
            self.logger.warning(f"전송 확인 실패: {e}")
            return False
    
    def test_input_detection(self, cell_bounds: tuple[int, int, int, int], 
                           ocr_area: tuple[int, int, int, int]) -> dict:
        """입력 감지 테스트"""
        results = {}
        methods = ["ocr_based", "template_matching", "adaptive_search", "multi_strategy"]
        
        for method in methods:
            result = self.find_text_input_position(cell_bounds, ocr_area, method)
            results[method] = {
                'success': result.success,
                'position': result.position,
                'confidence': result.confidence,
                'message': result.message
            }
        
        return results

# 사용 예시 및 테스트
def test_smart_automation():
    """스마트 자동화 테스트"""
    automation = SmartInputAutomation()
    
    # 테스트용 셀 데이터
    cell_bounds = (100, 100, 400, 300)  # x, y, width, height
    ocr_area = (110, 250, 380, 40)      # x, y, width, height
    
    print("🧪 스마트 입력 자동화 테스트")
    print("=" * 50)
    
    # 각 방법 테스트
    test_results = automation.test_input_detection(cell_bounds, ocr_area)
    
    for method, result in test_results.items():
        status = "✅" if result['success'] else "❌"
        print(f"{status} {method}: {result['position']} (신뢰도: {result['confidence']:.2f})")
        print(f"   메시지: {result['message']}")
    
    print("\n🎯 추천 방법: multi_strategy (가장 안정적)")
    print("📝 사용법:")
    print("   automation.execute_auto_input(cell_bounds, ocr_area, '응답 메시지')")

if __name__ == "__main__":
    test_smart_automation()