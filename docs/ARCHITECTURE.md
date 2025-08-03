# 시스템 아키텍처

## 개요

카카오톡 OCR 챗봇 시스템은 모듈화된 아키텍처로 설계되어 있으며, 각 컴포넌트가 명확한 책임을 가지고 있습니다.

## 아키텍처 다이어그램

```
┌─────────────────────────────────────────────────────────────────┐
│                          Main Entry Point                        │
│                            (main.py)                             │
└────────────────────────────────┬────────────────────────────────┘
                                 │
                    ┌────────────┴────────────┐
                    │   Service Container     │
                    │ (Dependency Injection)  │
                    └────────────┬────────────┘
                                 │
        ┌────────────────────────┼────────────────────────┐
        │                        │                        │
┌───────┴────────┐     ┌────────┴────────┐     ┌────────┴────────┐
│  Core Services │     │  OCR Services   │     │  GUI Services   │
├────────────────┤     ├─────────────────┤     ├─────────────────┤
│ ConfigManager  │     │ OCRService      │     │ ChatbotGUI      │
│ GridManager    │     │ OCRCorrector    │     │ OverlayWidget   │
│ CacheManager   │     │ OptimizedOCR    │     │ PerformanceTab  │
└────────────────┘     └─────────────────┘     └─────────────────┘
        │                        │                        │
        └────────────────────────┼────────────────────────┘
                                 │
                    ┌────────────┴────────────┐
                    │   Monitoring Services   │
                    ├──────────────────────────┤
                    │ MonitorManager          │
                    │ PerformanceMonitor      │
                    │ MonitoringThread        │
                    └──────────────────────────┘
```

## 핵심 컴포넌트

### 1. Service Container (의존성 주입)

**역할**: 모든 서비스의 생명주기 관리 및 의존성 주입

```python
class ServiceContainer:
    def __init__(self):
        self._services = {}
        self._factories = {}
        self._singletons = {}
```

**주요 기능**:
- 서비스 등록 및 조회
- 싱글톤 패턴 구현
- 순환 의존성 방지

### 2. Configuration Management

**ConfigManager**: 시스템 설정 중앙 관리

```python
@dataclass
class UIConstants:
    ocr_area_y_offset: int = 100
    ocr_area_height: int = 80
    overlay_height: int = 120

@dataclass
class TimingConfig:
    click_delay: float = 0.2
    clipboard_delay: float = 0.1
```

### 3. Grid Management System

**GridManager**: 화면을 그리드로 분할하여 관리

```python
@dataclass
class GridCell:
    id: str
    bounds: tuple[int, int, int, int]
    ocr_area: tuple[int, int, int, int]
    status: CellStatus
```

**특징**:
- 30개 셀 (3x5 그리드 x 2 모니터)
- 각 셀별 독립적인 상태 관리
- 쿨다운 메커니즘

### 4. OCR Processing Pipeline

```
이미지 캡처 → 전처리 → OCR 인식 → 오류 보정 → 결과 반환
     ↓           ↓         ↓          ↓           ↓
  PIL/mss    OpenCV   PaddleOCR   Corrector   Callback
```

**OCRService 구조**:
- 멀티스레드 처리
- 배치 처리 지원
- GPU 가속 옵션

**EnhancedOCRCorrector**:
- 정규식 기반 패턴 매칭
- 편집 거리 알고리즘
- 한글 특화 보정

### 5. Caching System

**CacheManager**: 2단계 캐싱 시스템

```python
class CacheManager:
    def __init__(self):
        self.image_cache = LRUCache(max_size=1000)
        self.ocr_cache = LRUCache(max_size=2000)
```

**캐싱 전략**:
- 이미지 해시 기반 캐싱
- TTL(Time To Live) 지원
- 메모리 효율적인 LRU 정책

### 6. Performance Monitoring

**PerformanceMonitor**: 실시간 성능 추적

```python
@dataclass
class PerformanceMetrics:
    cpu_percent: float
    memory_percent: float
    ocr_latency_ms: float
    cache_hit_rate: float
```

**모니터링 항목**:
- CPU/메모리 사용률
- OCR 처리 시간
- 캐시 효율성
- 응답 시간

### 7. GUI Architecture

**통합 GUI (ChatbotGUI)**:
- PyQt5 기반
- 탭 구조 (메인, 설정, 로그, 성능)
- MVC 패턴 적용

**오버레이 시스템**:
- 투명 윈도우
- 실시간 상태 표시
- 멀티모니터 지원

## 데이터 흐름

### OCR 처리 흐름

1. **모니터링 시작**
   ```
   MonitoringThread.start()
   └── GridManager.get_cells_for_cycle()
       └── OCRService.process_batch()
   ```

2. **이미지 처리**
   ```
   capture_screen_area()
   └── CacheManager.get_cached_image()
       └── preprocess_image()
           └── PaddleOCR.ocr()
   ```

3. **텍스트 처리**
   ```
   OCRCorrector.correct_text()
   └── check_trigger_pattern()
       └── ActionAutomation.execute()
   ```

4. **상태 업데이트**
   ```
   GridCell.set_triggered()
   └── GridCell.set_cooldown()
       └── GUI.update_overlay()
   ```

## 스레드 모델

### 메인 스레드
- GUI 이벤트 처리
- 사용자 입력 처리

### 모니터링 스레드
- OCR 처리 큐 관리
- 주기적 스캔

### OCR 워커 스레드들
- 병렬 OCR 처리
- 최대 6개 동시 실행

### 성능 모니터 스레드
- 시스템 메트릭 수집
- 1초 간격 샘플링

## 확장성 고려사항

### 플러그인 시스템
```python
class ActionPlugin:
    def can_handle(self, text: str) -> bool:
        pass
    
    def execute(self, cell: GridCell, text: str):
        pass
```

### 다국어 지원
- OCR 언어 설정
- 보정 패턴 국제화

### 스케일링
- 멀티 GPU 지원
- 분산 처리 가능

## 보안 고려사항

### 입력 검증
- OCR 결과 sanitization
- 설정 값 범위 검증

### 권한 관리
- 최소 권한 원칙
- 안전한 자동화

### 로깅
- 민감정보 마스킹
- 감사 로그

## 성능 최적화

### 메모리 관리
- 주기적 가비지 컬렉션
- 캐시 크기 제한

### CPU 최적화
- 배치 처리
- 병렬화

### I/O 최적화
- 비동기 처리
- 버퍼링

## 향후 개선 방향

1. **마이크로서비스화**
   - OCR 서비스 분리
   - REST API 제공

2. **클라우드 지원**
   - 원격 모니터링
   - 중앙 관리

3. **AI 고도화**
   - 딥러닝 기반 오류 보정
   - 컨텍스트 인식