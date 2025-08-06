"""
강화된 OCR 텍스트 보정 모듈
PaddleOCR의 한글 인식 오류를 자동으로 보정하여 "들어왔습니다" 패턴을 정확히 감지
"""
from __future__ import annotations

import re
import logging
from difflib import SequenceMatcher
import unicodedata


class EnhancedOCRCorrector:
    """강화된 OCR 텍스트 보정기"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # 기본 트리거 패턴들
        self.base_patterns = [
            "들어왔습니다",
            "입장했습니다", 
            "참여했습니다",
            "접속했습니다",
            "참가했습니다"
        ]
        
        # OCR 오인식 패턴 매핑 (실제 관찰된 오류들)
        self.ocr_corrections = {
            # "들어왔습니다" 변형들
            "들머왔습니다": "들어왔습니다",
            "둘어왔습니다": "들어왔습니다", 
            "들어왔시니다": "들어왔습니다",
            "들어왔느니다": "들어왔습니다",
            "들어왔습니타": "들어왔습니다",
            "들어왔스니다": "들어왔습니다",
            "들어왔슴니다": "들어왔습니다",
            "들어왔읍니다": "들어왔습니다",
            "들어왔ㅅ니다": "들어왔습니다",
            "들어왔ㅁ니다": "들어왔습니다",
            "들어왔7니다": "들어왔습니다",
            "들어왔5니다": "들어왔습니다",
            "틀어왔습니다": "들어왔습니다",
            "들머왔읍니다": "들어왔습니다",
            "들어와습니다": "들어왔습니다",
            "들어왔슴다": "들어왔습니다",
            "들어왔니다": "들어왔습니다",
            
            # "입장했습니다" 변형들  
            "입정했습니다": "입장했습니다",
            "입장햤습니다": "입장했습니다",
            "입장했스니다": "입장했습니다",
            "입장했슴니다": "입장했습니다",
            "입장했읍니다": "입장했습니다",
            "입잠했습니다": "입장했습니다",
            "입창했습니다": "입장했습니다",
            
            # "참여했습니다" 변형들
            "참어했습니다": "참여했습니다",
            "참여햤습니다": "참여했습니다", 
            "참여했스니다": "참여했습니다",
            "참여했슴니다": "참여했습니다",
            "참여했읍니다": "참여했습니다",
            "잠여했습니다": "참여했습니다",
            "참야했습니다": "참여했습니다"
        }
        
        # 문자별 OCR 오인식 매핑
        self.char_corrections = {
            # ㅇ계열 오류
            '머': ['어', '며'],
            '며': ['어', '머'], 
            '어': ['머', '며'],
            
            # ㅅ계열 오류  
            '스': ['습', '슴'],
            '슴': ['습', '스'],
            '습': ['스', '슴', 'ㅅ', '5', '7'],
            'ㅅ': ['습', '스', '5', '7'],
            '5': ['습', 'ㅅ', 's'],
            '7': ['습', 'ㅅ', 't'],
            
            # ㄴ계열 오류
            '니': ['느', 'ㄴ'],
            '느': ['니', 'ㄴ'],
            'ㄴ': ['니', '느'],
            
            # 기타 유사 문자
            '읍': ['습', '웁'],
            '웁': ['읍', '습'],
            '타': ['다', '따'],
            '따': ['다', '타'],
            '틀': ['들', '를'],
            '둘': ['들', '툴'],
            '정': ['장', '점'],
            '잠': ['참', '점'],
            '창': ['장', '창'],
            '어': ['머', '여'],
            '야': ['여', '어']
        }
        
        # 숫자-한글 혼동 패턴
        self.number_char_map = {
            '0': ['ㅇ', '○'],
            '1': ['ㅣ', 'ㄱ', 'l', 'I'],
            '5': ['ㅅ', 's', 'S'],
            '7': ['ㅅ', 't', 'T'],
            '8': ['ㅂ', 'B']
        }
    
    def normalize_text(self, text: str) -> str:
        """텍스트 정규화"""
        if not text:
            return ""
        
        # 유니코드 정규화
        text = unicodedata.normalize('NFC', text)
        
        # 공백, 특수문자 제거
        text = re.sub(r'[^\w가-힣]', '', text)
        
        # 연속된 동일 문자 축약 (예: "습습니다" -> "습니다")
        text = re.sub(r'(.)\1+', r'\1', text)
        
        return text.strip()
    
    def apply_direct_corrections(self, text: str) -> str:
        """직접 매핑된 오류 보정"""
        normalized = self.normalize_text(text)
        
        # 정확한 매칭부터 시도
        for error, correct in self.ocr_corrections.items():
            if error in normalized:
                corrected = normalized.replace(error, correct)
                if corrected != normalized:
                    self.logger.debug(f"직접 보정: '{text}' -> '{correct}' (패턴: {error})")
                    return correct
        
        return normalized
    
    def generate_character_variations(self, text: str) -> list[str]:
        """문자별 변형 생성"""
        variations = [text]
        
        # 각 문자에 대해 가능한 오인식 변형 생성
        for i, char in enumerate(text):
            if char in self.char_corrections:
                new_variations = []
                for variation in variations:
                    for alt_char in self.char_corrections[char]:
                        new_var = variation[:i] + alt_char + variation[i+1:]
                        new_variations.append(new_var)
                variations.extend(new_variations)
        
        # 중복 제거
        return list(set(variations))
    
    def fuzzy_match_patterns(self, text: str, threshold: float = 0.8) -> tuple[bool, str]:
        """퍼지 매칭으로 유사한 패턴 찾기"""
        normalized = self.normalize_text(text)
        
        for pattern in self.base_patterns:
            similarity = SequenceMatcher(None, normalized, pattern).ratio()
            
            if similarity >= threshold:
                self.logger.debug(f"퍼지 매칭: '{text}' -> '{pattern}' (유사도: {similarity:.2f})")
                return True, pattern
        
        return False, ""
    
    def advanced_pattern_matching(self, text: str) -> tuple[bool, str]:
        """고급 패턴 매칭"""
        normalized = self.normalize_text(text)
        
        # 1. 핵심 키워드 기반 매칭
        core_keywords = {
            "들어왔습니다": ["들", "어", "왔", "습", "니", "다"],
            "입장했습니다": ["입", "장", "했", "습", "니", "다"], 
            "참여했습니다": ["참", "여", "했", "습", "니", "다"]
        }
        
        for pattern, keywords in core_keywords.items():
            match_count = sum(1 for keyword in keywords if keyword in normalized)
            match_ratio = match_count / len(keywords)
            
            # 70% 이상 키워드가 매칭되면 해당 패턴으로 인식
            if match_ratio >= 0.7:
                self.logger.debug(f"키워드 매칭: '{text}' -> '{pattern}' (매칭률: {match_ratio:.2f})")
                return True, pattern
        
        # 2. 길이 기반 매칭 (비슷한 길이의 텍스트)
        if 5 <= len(normalized) <= 8:  # "들어왔습니다" 길이 범위
            for pattern in self.base_patterns:
                if abs(len(normalized) - len(pattern)) <= 2:
                    # 문자 단위 유사도 검사
                    common_chars = set(normalized) & set(pattern)
                    if len(common_chars) >= len(pattern) * 0.6:
                        self.logger.debug(f"길이+문자 매칭: '{text}' -> '{pattern}'")
                        return True, pattern
        
        return False, ""
    
    def check_trigger_pattern(self, text: str) -> tuple[bool, str]:
        """종합적인 트리거 패턴 검사"""
        if not text or len(text.strip()) < 3:
            return False, ""
        
        original_text = text
        
        # 1단계: 직접 보정 시도
        corrected = self.apply_direct_corrections(text)
        for pattern in self.base_patterns:
            if pattern in corrected:
                self.logger.info(f"✅ 직접 보정 매칭: '{original_text}' -> '{pattern}'")
                return True, pattern
        
        # 2단계: 문자 변형 검사
        variations = self.generate_character_variations(self.normalize_text(text))
        for variation in variations:
            for pattern in self.base_patterns:
                if pattern in variation:
                    self.logger.info(f"✅ 문자 변형 매칭: '{original_text}' -> '{pattern}' (변형: {variation})")
                    return True, pattern
        
        # 3단계: 퍼지 매칭
        is_match, matched_pattern = self.fuzzy_match_patterns(text, threshold=0.75)
        if is_match:
            self.logger.info(f"✅ 퍼지 매칭: '{original_text}' -> '{matched_pattern}'")
            return True, matched_pattern
        
        # 4단계: 고급 패턴 매칭
        is_match, matched_pattern = self.advanced_pattern_matching(text)
        if is_match:
            self.logger.info(f"✅ 고급 매칭: '{original_text}' -> '{matched_pattern}'")
            return True, matched_pattern
        
        # 5단계: 부분 문자열 매칭 (느슨한 검사)
        normalized = self.normalize_text(text)
        for pattern in self.base_patterns:
            # 패턴의 핵심 부분 추출
            if "들어왔" in normalized or "들머왔" in normalized or "둘어왔" in normalized:
                self.logger.info(f"✅ 부분 매칭: '{original_text}' -> '들어왔습니다'")
                return True, "들어왔습니다"
            elif "입장" in normalized and "했" in normalized:
                self.logger.info(f"✅ 부분 매칭: '{original_text}' -> '입장했습니다'")
                return True, "입장했습니다"
            elif "참여" in normalized and "했" in normalized:
                self.logger.info(f"✅ 부분 매칭: '{original_text}' -> '참여했습니다'")
                return True, "참여했습니다"
        
        return False, ""
    
    def add_custom_correction(self, error_text: str, correct_text: str):
        """사용자 정의 보정 패턴 추가"""
        self.ocr_corrections[error_text] = correct_text
        self.logger.info(f"사용자 정의 보정 추가: '{error_text}' -> '{correct_text}'")
    
    def correct_text(self, text: str) -> str:
        """텍스트 보정 (호환성을 위한 별칭 메서드)"""
        return self.apply_direct_corrections(text)
    
    def get_correction_stats(self) -> dict[str, int]:
        """보정 통계 반환"""
        return {
            "total_corrections": len(self.ocr_corrections),
            "base_patterns": len(self.base_patterns),
            "char_corrections": len(self.char_corrections)
        }


# 테스트 함수
def test_ocr_corrector():
    """OCR 보정기 테스트"""
    corrector = EnhancedOCRCorrector()
    
    # 테스트 케이스들
    test_cases = [
        # 정확한 텍스트
        "들어왔습니다",
        "입장했습니다",
        "참여했습니다",
        
        # 일반적인 OCR 오류들
        "들머왔습니다",
        "둘어왔습니다", 
        "들어왔시니다",
        "들어왔느니다",
        "들어왔슴니다",
        "들어왔읍니다",
        "들어왔ㅅ니다",
        "들어왔7니다",
        "들어왔5니다",
        "틀어왔습니다",
        
        # 공백이나 특수문자 포함
        "들어왔습니다.",
        "들 어 왔 습 니 다",
        "들어왔습니다!!",
        
        # 부분 매칭 케이스
        "들어왔",
        "입장했",
        "참여했",
        
        # 매칭되지 않아야 할 케이스
        "안녕하세요",
        "반갑습니다", 
        "감사합니다"
    ]
    
    print("🧪 OCR 보정기 테스트 시작")
    print("=" * 50)
    
    for i, test_text in enumerate(test_cases, 1):
        is_match, matched_pattern = corrector.check_trigger_pattern(test_text)
        
        status = "✅ 매칭" if is_match else "❌ 비매칭"
        result = f"-> {matched_pattern}" if is_match else ""
        
        print(f"{i:2d}. '{test_text}' {status} {result}")
    
    print("\n📊 보정기 통계:")
    stats = corrector.get_correction_stats()
    for key, value in stats.items():
        print(f"   {key}: {value}")


if __name__ == "__main__":
    test_ocr_corrector()