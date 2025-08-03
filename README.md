# 카카오톡 OCR 챗봇 시스템

OCR 기반 카카오톡 자동 응답 시스템으로, 화면의 특정 영역을 모니터링하여 지정된 텍스트를 감지하고 자동으로 응답합니다.

## 주요 기능

- **실시간 OCR 모니터링**: PaddleOCR을 사용한 한글 텍스트 인식
- **멀티모니터 지원**: 듀얼 모니터 환경에서 그리드 기반 모니터링
- **스마트 오류 보정**: 한글 OCR 오류 자동 보정
- **성능 최적화**: LRU 캐싱, 멀티스레딩 처리
- **시각적 오버레이**: 실시간 모니터링 상태 표시

## 시스템 요구사항

- Python 3.11 이상 (3.13은 numpy 호환성 문제 있음)
- Windows 10/11
- 듀얼 모니터 (1920x1080 권장)
- 최소 8GB RAM

## 설치 방법

### 1. 저장소 클론
```bash
git clone https://github.com/your-repo/kakaotalk-ocr-chatbot.git
cd kakaotalk-ocr-chatbot
```

### 2. 가상환경 생성 및 활성화
```bash
python -m venv venv
venv\Scripts\activate  # Windows
```

### 3. 의존성 설치
```bash
pip install -r requirements.txt
```

### 4. PaddleOCR 추가 설정
```bash
# GPU 사용 시
pip install paddlepaddle-gpu

# CPU만 사용 시
pip install paddlepaddle
```

## 사용 방법

### 기본 실행
```bash
python main.py
```

### 배치 파일로 실행
```bash
run_with_qt.bat
```

### 설정 파일 (config.json)
```json
{
    "grid_rows": 3,
    "grid_cols": 5,
    "ocr_interval_sec": 0.3,
    "cooldown_sec": 5,
    "trigger_patterns": ["들어왔습니다", "입장했습니다"],
    "ui_constants": {
        "ocr_area_y_offset": 100,
        "ocr_area_height": 80
    }
}
```

## 프로젝트 구조

```
카카오톡 챗봇 시스템/
├── src/
│   ├── core/               # 핵심 모듈
│   │   ├── config_manager.py    # 설정 관리
│   │   ├── grid_manager.py      # 그리드 셀 관리
│   │   ├── service_container.py # 의존성 주입
│   │   └── cache_manager.py     # 캐시 관리
│   ├── ocr/                # OCR 관련
│   │   ├── ocr_service.py       # OCR 서비스
│   │   └── enhanced_ocr_corrector.py # 오류 보정
│   ├── gui/                # UI 관련
│   │   └── chatbot_gui.py       # 통합 GUI
│   ├── monitoring/         # 모니터링
│   │   ├── monitor_manager.py   # 모니터 관리
│   │   └── performance_monitor.py # 성능 모니터링
│   └── automation/         # 자동화
│       └── action_automation.py # 동작 자동화
├── tests/                  # 테스트
├── docs/                   # 문서
├── tools/                  # 유틸리티
└── main.py                # 진입점
```

## GUI 사용법

### 메인 컨트롤
- **모니터링 시작/중지**: OCR 모니터링 제어
- **오버레이 표시/숨기기**: 그리드 오버레이 토글
- **테스트 자동화**: 동작 테스트

### 설정 탭
- 그리드 크기 조정
- OCR 간격 설정
- 트리거 패턴 관리
- 쿨다운 시간 설정

### 로그 탭
- 실시간 로그 확인
- 로그 레벨 필터링
- 로그 파일 저장

### 성능 탭
- CPU/메모리 사용률
- OCR 처리 시간
- 캐시 히트율
- 응답 시간 통계

## 주요 기능 설명

### OCR 오류 보정
시스템은 다음과 같은 일반적인 OCR 오류를 자동으로 보정합니다:
- "들머왔습니다" → "들어왔습니다"
- "들어왔슴니다" → "들어왔습니다"
- "들어왔ㅅ니다" → "들어왔습니다"

### 성능 최적화
- **LRU 캐싱**: 반복되는 이미지 처리 결과 캐싱
- **배치 처리**: 여러 셀을 동시에 처리
- **멀티스레딩**: OCR 처리를 별도 스레드에서 실행
- **동적 최적화**: 성능 모니터링 기반 자동 조정

### 모니터링 시스템
- 30개 그리드 셀 (듀얼 모니터)
- 각 셀별 독립적인 쿨다운
- 시각적 상태 표시 (녹색: 트리거, 빨간색: 쿨다운)

## 문제 해결

### OCR이 텍스트를 인식하지 못할 때
1. `config.json`의 OCR 영역 설정 확인
2. 화면 해상도가 1920x1080인지 확인
3. 카카오톡 창이 최대화되어 있는지 확인

### 성능이 느릴 때
1. OCR 간격을 늘려보세요 (예: 0.5초)
2. 그리드 크기를 줄여보세요
3. GPU 가속 활성화 확인

### Python 3.13에서 numpy 오류
Python 3.11 사용을 권장합니다.

## 개발자 가이드

### 새로운 OCR 보정 패턴 추가
```python
# src/ocr/enhanced_ocr_corrector.py
CORRECTION_PATTERNS = [
    # 기존 패턴...
    (r'새로운패턴', '올바른텍스트'),
]
```

### 커스텀 액션 추가
```python
# src/automation/action_automation.py
def custom_action(self, cell: GridCell, text: str):
    # 커스텀 동작 구현
    pass
```

## 테스트

### 단위 테스트 실행
```bash
pytest tests/ -v
```

### 특정 테스트만 실행
```bash
pytest tests/test_final_fixed.py -v
```

## 라이선스

이 프로젝트는 MIT 라이선스를 따릅니다.

## 기여 방법

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 지원

문제가 있으시면 Issues 탭에서 새 이슈를 생성해주세요.