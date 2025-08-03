# 카카오톡 OCR 챗봇 시스템

OCR 기반 카카오톡 자동 응답 챗봇 시스템

## 프로젝트 구조

```
카카오톡_챗봇_시스템/
├── src/                    # 소스 코드
│   ├── core/              # 핵심 모듈
│   │   ├── config_manager.py      # 설정 관리
│   │   ├── grid_manager.py        # 그리드/셀 관리
│   │   └── service_container.py   # 서비스 컨테이너
│   ├── ocr/               # OCR 관련
│   │   ├── enhanced_ocr_service.py    # 향상된 OCR 서비스
│   │   ├── enhanced_ocr_corrector.py  # OCR 보정
│   │   └── ocr_service.py             # 기본 OCR 서비스
│   ├── monitoring/        # 모니터링
│   │   ├── improved_monitoring_thread.py  # 개선된 모니터링 스레드
│   │   └── monitor_manager.py            # 모니터 관리
│   ├── automation/        # 자동화
│   │   ├── automation_service.py         # 자동화 서비스
│   │   └── smart_input_automation.py     # 스마트 입력 자동화
│   └── gui/               # GUI
│       ├── optimized_chatbot_system.py   # 최적화된 챗봇 시스템 (메인)
│       ├── grid_overlay_system.py        # 그리드 오버레이
│       └── complete_chatbot_system.py    # 전체 챗봇 시스템
├── tools/                 # 도구 및 유틸리티
│   ├── verify_screen_coordinates.py  # 화면 좌표 검증
│   ├── visual_cell_overlay.py        # 시각적 셀 오버레이
│   └── adjust_coordinates.py         # 좌표 조정 도구
├── tests/                 # 테스트
│   ├── test_basic_structure.py
│   ├── test_enhanced_detection.py
│   ├── test_integration.py
│   └── test_ocr_detection.py
├── docs/                  # 문서
│   └── cleanup_report.md            # 정리 보고서
├── main.py               # 메인 진입점
├── config.json           # 설정 파일
└── requirements.txt      # 의존성

```

## 실행 방법

### 1. 메인 애플리케이션 실행
```bash
python main.py
```

### 2. 좌표 검증 도구
```bash
python tools/verify_screen_coordinates.py
```

### 3. 시각적 오버레이
```bash
python tools/visual_cell_overlay.py
```

### 4. 좌표 조정 도구
```bash
python tools/adjust_coordinates.py
```

## 주요 기능

- **OCR 기반 텍스트 감지**: PaddleOCR을 사용한 한글 텍스트 인식
- **다중 전처리 전략**: 6가지 이상의 이미지 전처리 방법
- **자동 복구 메커니즘**: OCR 엔진 오류 시 자동 복구
- **실시간 모니터링**: 30개 셀 동시 모니터링
- **트리거 패턴 매칭**: 사용자 정의 패턴 감지 및 자동 응답
- **시각적 디버깅 도구**: 좌표 확인 및 조정 도구

## 최근 개선사항

1. **프로젝트 구조 정리** (2025-08-02)
   - 중복 파일 제거
   - 모듈별 디렉토리 구조화
   - 테스트 및 도구 분리

2. **OCR 성능 개선**
   - 다중 전처리 전략 구현
   - 스레드 안전성 강화
   - 자동 복구 메커니즘 추가

3. **디버깅 도구 추가**
   - 실시간 좌표 검증
   - 시각적 오버레이
   - 좌표 조정 도구

## 문제 해결

### OCR이 텍스트를 감지하지 못하는 경우
1. `tools/verify_screen_coordinates.py` 실행하여 좌표 확인
2. `tools/adjust_coordinates.py`로 좌표 조정
3. 카카오톡 창이 올바른 위치에 있는지 확인

### 성능 문제
- `config.json`에서 모니터링 주기 조정
- 불필요한 셀 비활성화
- 디버그 이미지 저장 비활성화

## 의존성

```
PyQt5>=5.15.0
paddlepaddle>=2.4.0
paddleocr>=2.7.0
opencv-python>=4.8.0
numpy>=1.24.0
Pillow>=10.0.0
screeninfo>=0.8.1
pyautogui>=0.9.54
keyboard>=0.13.5
mss>=9.0.1
```