# API Reference

## Core Services

### ConfigManager

설정 파일을 로드하고 관리하는 클래스입니다.

#### 생성자
```python
ConfigManager(config_path: str = "config.json")
```

#### 주요 속성
- `grid_rows: int` - 그리드 행 수
- `grid_cols: int` - 그리드 열 수
- `ocr_interval_sec: float` - OCR 스캔 간격
- `cooldown_sec: int` - 쿨다운 시간
- `trigger_patterns: list[str]` - 트리거 패턴 목록
- `ui_constants: UIConstants` - UI 관련 상수
- `timing_config: TimingConfig` - 타이밍 설정
- `automation_config: AutomationConfig` - 자동화 설정

#### 메서드
```python
def get(self, key: str, default: Any = None) -> Any:
    """설정 값을 가져옵니다."""
    
def reload(self) -> None:
    """설정을 다시 로드합니다."""
```

### GridManager

화면 그리드를 관리하는 클래스입니다.

#### 생성자
```python
GridManager(config_manager: ConfigManager)
```

#### 주요 메서드
```python
def get_cells_for_cycle(self) -> list[GridCell]:
    """현재 사이클에서 처리할 셀 목록을 반환합니다."""
    
def update_cell_cooldowns(self) -> None:
    """모든 셀의 쿨다운 상태를 업데이트합니다."""
    
def reset_all_cells(self) -> None:
    """모든 셀을 초기 상태로 리셋합니다."""
    
def get_statistics(self) -> dict[str, Any]:
    """그리드 통계를 반환합니다."""
```

### GridCell

개별 그리드 셀을 나타내는 데이터클래스입니다.

#### 속성
```python
@dataclass
class GridCell:
    id: str
    bounds: tuple[int, int, int, int]  # (x, y, width, height)
    ocr_area: tuple[int, int, int, int]
    status: CellStatus = CellStatus.IDLE
    enabled: bool = True
    last_triggered: float = 0.0
    cooldown_until: float = 0.0
    detected_text: str = ""
    detected_text_position: tuple[int, int] | None = None
    trigger_count: int = 0
    monitor_index: int = 0
```

#### 메서드
```python
def set_triggered(self, text: str = "", position: tuple[int, int] | None = None) -> None:
    """셀을 트리거 상태로 설정합니다."""
    
def set_cooldown(self, duration_sec: float) -> None:
    """셀을 쿨다운 상태로 설정합니다."""
    
def set_idle(self) -> None:
    """셀을 유휴 상태로 리셋합니다."""
    
def can_be_triggered(self) -> bool:
    """셀이 트리거 가능한지 확인합니다."""
```

## OCR Services

### OCRService

OCR 처리를 담당하는 메인 서비스입니다.

#### 생성자
```python
OCRService(config_manager: ConfigManager, container: ServiceContainer)
```

#### 주요 메서드
```python
def process_cell(self, cell: GridCell, callback: Callable) -> None:
    """단일 셀을 OCR 처리합니다."""
    
def process_batch(self, cells: list[GridCell], callback: Callable) -> None:
    """여러 셀을 배치로 처리합니다."""
    
def capture_screen_area(self, bounds: tuple[int, int, int, int]) -> np.ndarray:
    """화면 영역을 캡처합니다."""
```

### EnhancedOCRCorrector

OCR 결과의 오류를 보정하는 클래스입니다.

#### 메서드
```python
def correct_text(self, text: str) -> str:
    """OCR 텍스트 오류를 보정합니다."""
    
def check_trigger_pattern(self, text: str) -> tuple[bool, str]:
    """텍스트가 트리거 패턴과 일치하는지 확인합니다."""
    
def normalize_text(self, text: str) -> str:
    """텍스트를 정규화합니다."""
```

## Cache Services

### CacheManager

캐싱을 관리하는 서비스입니다.

#### 메서드
```python
def get_cached_image(self, image_hash: str) -> np.ndarray | None:
    """캐시된 이미지를 가져옵니다."""
    
def cache_image(self, image_hash: str, processed_image: np.ndarray) -> None:
    """처리된 이미지를 캐시합니다."""
    
def get_cached_ocr(self, cache_key: str) -> str | None:
    """캐시된 OCR 결과를 가져옵니다."""
    
def cache_ocr(self, cache_key: str, text: str) -> None:
    """OCR 결과를 캐시합니다."""
```

### SimpleLRUCache

LRU 캐시 구현체입니다.

#### 생성자
```python
SimpleLRUCache(max_size: int = 1000)
```

#### 메서드
```python
def get(self, key: str) -> Any | None:
    """캐시에서 값을 가져옵니다."""
    
def put(self, key: str, value: Any) -> None:
    """캐시에 값을 저장합니다."""
    
def clear(self) -> None:
    """캐시를 비웁니다."""
    
def get_stats(self) -> dict[str, int]:
    """캐시 통계를 반환합니다."""
```

## Monitoring Services

### MonitorManager

모니터링을 관리하는 메인 클래스입니다.

#### 생성자
```python
MonitorManager(container: ServiceContainer)
```

#### 메서드
```python
def start_monitoring(self) -> None:
    """모니터링을 시작합니다."""
    
def stop_monitoring(self) -> None:
    """모니터링을 중지합니다."""
    
def is_monitoring(self) -> bool:
    """모니터링 중인지 확인합니다."""
```

### PerformanceMonitor

성능 모니터링 클래스입니다.

#### 메서드
```python
def start_monitoring(self) -> None:
    """성능 모니터링을 시작합니다."""
    
def stop_monitoring(self) -> None:
    """성능 모니터링을 중지합니다."""
    
def get_current_metrics(self) -> PerformanceMetrics:
    """현재 성능 메트릭을 가져옵니다."""
    
def get_metrics_history(self, seconds: int = 60) -> list[PerformanceMetrics]:
    """지정된 시간의 메트릭 히스토리를 가져옵니다."""
```

## Automation Services

### ActionAutomation

자동화 액션을 처리하는 클래스입니다.

#### 메서드
```python
def execute_click_action(self, position: tuple[int, int]) -> bool:
    """클릭 액션을 실행합니다."""
    
def send_kakao_message(self, message: str) -> bool:
    """카카오톡 메시지를 전송합니다."""
    
def verify_action_success(self) -> bool:
    """액션 성공 여부를 확인합니다."""
```

## GUI Components

### ChatbotGUI

메인 GUI 클래스입니다.

#### 시그널
```python
monitoring_started = pyqtSignal()
monitoring_stopped = pyqtSignal()
overlay_toggled = pyqtSignal(bool)
settings_changed = pyqtSignal(dict)
```

#### 주요 메서드
```python
def start_monitoring(self) -> None:
    """모니터링을 시작합니다."""
    
def stop_monitoring(self) -> None:
    """모니터링을 중지합니다."""
    
def toggle_overlay(self) -> None:
    """오버레이를 토글합니다."""
    
def update_performance_display(self) -> None:
    """성능 표시를 업데이트합니다."""
```

## 유틸리티 함수

### 이미지 처리
```python
def preprocess_image(image: np.ndarray, strategy: str = "adaptive") -> np.ndarray:
    """이미지를 전처리합니다."""
    
def calculate_image_hash(image: np.ndarray) -> str:
    """이미지의 해시를 계산합니다."""
```

### 텍스트 처리
```python
def normalize_korean_text(text: str) -> str:
    """한글 텍스트를 정규화합니다."""
    
def calculate_edit_distance(s1: str, s2: str) -> int:
    """두 문자열 간의 편집 거리를 계산합니다."""
```

## 예외 클래스

```python
class OCRException(Exception):
    """OCR 처리 중 발생하는 예외"""
    
class ConfigException(Exception):
    """설정 관련 예외"""
    
class AutomationException(Exception):
    """자동화 처리 중 발생하는 예외"""
```

## 상수 및 열거형

### CellStatus
```python
class CellStatus(StrEnum):
    IDLE = "idle"
    TRIGGERED = "triggered"
    COOLDOWN = "cooldown"
    DISABLED = "disabled"
```

### 기본 설정값
```python
DEFAULT_CONFIG = {
    "grid_rows": 3,
    "grid_cols": 5,
    "ocr_interval_sec": 0.3,
    "cooldown_sec": 5,
    "trigger_patterns": ["들어왔습니다"],
    "reply_message": "어서오세요!"
}