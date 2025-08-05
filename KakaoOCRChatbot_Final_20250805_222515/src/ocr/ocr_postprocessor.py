"""
OCR 후처리 시스템 - 결과 품질 향상
"""
from __future__ import annotations

import re
import difflib
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
import logging

@dataclass
class OCRCandidate:
    """OCR 후보 결과"""
    text: str
    confidence: float
    source: str  # 어떤 전략에서 나온 결과인지
    position: Tuple[int, int]

class OCRPostProcessor:
    """OCR 결과 후처리 및 품질 향상"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # 한글 OCR 일반적인 오류 패턴
        self.common_corrections = {
            # 자음/모음 혼동
            'ㅗ': 'o', 'ㅓ': 'ㅣ', 'ㅣ': 'l', 'ㅡ': '-',
            # 숫자/글자 혼동
            '0': 'ㅇ', '1': 'ㅣ', '5': 'ㅅ',
            # 일반적인 오타
            '든어왔습니다': '들어왔습니다',
            '들머왔습니다': '들어왔습니다',
            '들어왔습니디': '들어왔습니다',
            '들어완습니다': '들어왔습니다',
            '툴어왔습니다': '들어왔습니다',
        }
        
        # 카카오톡 메시지 패턴
        self.kakao_patterns = [
            r'.*님이\s*(채팅방에\s*)?(들어왔습니다|입장했습니다|참여했습니다)',
            r'.*님이\s*(들어왔습니다|입장|참여)',
            r'.*(들어왔습니다|입장했습니다|참여했습니다)',
            r'.*님.*들어왔.*',
            r'.*입장.*',
            r'.*참여.*'
        ]
        
        # 금지 패턴 (시간, 날짜 등)
        self.blacklist_patterns = [
            r'^\d{1,2}:\d{2}$',  # 시간
            r'^\d{4}-\d{2}-\d{2}$',  # 날짜
            r'^[0-9\s\-:]+$',  # 숫자만
            r'^[a-zA-Z\s]+$',  # 영어만
            r'^.{1,2}$',  # 너무 짧은 텍스트
        ]
    
    def process_multiple_candidates(self, candidates: List[OCRCandidate]) -> Optional[OCRCandidate]:
        """여러 OCR 후보 결과를 종합하여 최적 결과 선택"""
        if not candidates:
            return None
        
        # 1단계: 금지 패턴 필터링
        filtered_candidates = []
        for candidate in candidates:
            if not self._is_blacklisted(candidate.text):
                filtered_candidates.append(candidate)
        
        if not filtered_candidates:
            return None
        
        # 2단계: 오류 교정
        corrected_candidates = []
        for candidate in filtered_candidates:
            corrected_text = self._apply_corrections(candidate.text)
            corrected_candidates.append(OCRCandidate(
                text=corrected_text,
                confidence=candidate.confidence,
                source=candidate.source,
                position=candidate.position
            ))
        
        # 3단계: 패턴 매칭 점수 계산
        scored_candidates = []
        for candidate in corrected_candidates:
            pattern_score = self._calculate_pattern_score(candidate.text)
            total_score = candidate.confidence * 0.6 + pattern_score * 0.4
            scored_candidates.append((candidate, total_score))
        
        # 4단계: 최고 점수 선택
        if scored_candidates:
            best_candidate, best_score = max(scored_candidates, key=lambda x: x[1])
            self.logger.debug(f"Selected best candidate: '{best_candidate.text}' "
                            f"(score: {best_score:.3f}, source: {best_candidate.source})")
            return best_candidate
        
        return None
    
    def _is_blacklisted(self, text: str) -> bool:
        """금지 패턴 확인"""
        if not text or len(text.strip()) == 0:
            return True
        
        for pattern in self.blacklist_patterns:
            if re.match(pattern, text.strip()):
                return True
        
        return False
    
    def _apply_corrections(self, text: str) -> str:
        """일반적인 OCR 오류 교정"""
        corrected = text
        
        # 정확한 매칭 교정
        for wrong, correct in self.common_corrections.items():
            corrected = corrected.replace(wrong, correct)
        
        # 유사도 기반 교정 (중요 키워드에 대해)
        key_phrases = ['들어왔습니다', '님이', '입장했습니다', '참여했습니다']
        for phrase in key_phrases:
            # 문자열에서 유사한 부분 찾기
            words = corrected.split()
            for i, word in enumerate(words):
                similarity = difflib.SequenceMatcher(None, word, phrase).ratio()
                if similarity > 0.7:  # 70% 이상 유사하면 교정
                    words[i] = phrase
                    corrected = ' '.join(words)
                    break
        
        return corrected
    
    def _calculate_pattern_score(self, text: str) -> float:
        """패턴 매칭 점수 계산"""
        if not text:
            return 0.0
        
        max_score = 0.0
        
        for pattern in self.kakao_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                # 매칭된 패턴의 정확도에 따라 점수 부여
                match_length = len(match.group())
                total_length = len(text)
                score = match_length / total_length
                max_score = max(max_score, score)
        
        # 키워드 기반 점수 추가
        keyword_scores = []
        keywords = ['들어왔습니다', '님이', '입장', '참여']
        for keyword in keywords:
            if keyword in text:
                keyword_scores.append(1.0)
            else:
                # 부분 매칭 점수
                best_match = 0.0
                for word in text.split():
                    similarity = difflib.SequenceMatcher(None, word, keyword).ratio()
                    best_match = max(best_match, similarity)
                keyword_scores.append(best_match)
        
        keyword_score = max(keyword_scores) if keyword_scores else 0.0
        
        return max(max_score, keyword_score)
    
    def enhance_single_result(self, text: str, confidence: float) -> Tuple[str, float]:
        """단일 OCR 결과 향상"""
        if self._is_blacklisted(text):
            return "", 0.0
        
        corrected_text = self._apply_corrections(text)
        pattern_score = self._calculate_pattern_score(corrected_text)
        
        # 패턴 매칭이 좋으면 신뢰도 향상
        enhanced_confidence = confidence
        if pattern_score > 0.7:
            enhanced_confidence = min(confidence + 0.2, 1.0)
        elif pattern_score > 0.5:
            enhanced_confidence = min(confidence + 0.1, 1.0)
        
        return corrected_text, enhanced_confidence
    
    def get_correction_stats(self) -> Dict:
        """교정 통계 정보"""
        return {
            'correction_rules': len(self.common_corrections),
            'pattern_rules': len(self.kakao_patterns),
            'blacklist_rules': len(self.blacklist_patterns)
        }