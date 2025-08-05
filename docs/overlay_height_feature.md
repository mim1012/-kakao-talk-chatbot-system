# 오버레이 높이 조정 기능

## 개요
GUI에서 오버레이 높이를 10px 단위로 조절할 수 있는 기능이 추가되었습니다.

## 구현 내용

### 1. GUI 요소 추가 (src/gui/chatbot_gui.py)
```python
# 오버레이 높이 조정 슬라이더 (라인 906-918)
self.overlay_height_slider = QSlider(Qt.Horizontal)
self.overlay_height_slider.setMinimum(30)
self.overlay_height_slider.setMaximum(200)
self.overlay_height_slider.setSingleStep(10)
self.overlay_height_slider.setPageStep(10)
self.overlay_height_slider.setValue(100)  # 기본값 100px
self.overlay_height_slider.valueChanged.connect(self.on_overlay_height_changed)
self.overlay_height_label = QLabel("100px")
```

### 2. 높이 변경 처리 메서드 (라인 1102-1124)
```python
def on_overlay_height_changed(self, value):
    """오버레이 높이 변경 처리"""
    # 10px 단위로 맞춤
    value = (value // 10) * 10
    self.overlay_height_slider.setValue(value)
    self.overlay_height_label.setText(f"{value}px")
    
    # config의 ui_constants 업데이트
    if hasattr(self.services.config_manager, 'ui_constants'):
        self.services.config_manager.ui_constants.overlay_height = value
    else:
        # ui_constants가 없으면 생성
        self.services.config_manager.ui_constants = type('UIConstants', (), {'overlay_height': value})()
    
    # GridManager의 셀들 업데이트
    self.services.grid_manager._create_grid_cells()
    
    # 오버레이가 표시 중이면 업데이트
    if self.overlay:
        self.overlay.update()
    
    self.log(f"오버레이 높이 변경: {value}px")
```

### 3. GridManager 통합 (src/core/grid_manager.py)
```python
# OCR 영역 계산 시 오버레이 높이 사용 (라인 149-157)
overlay_height = ui_constants.overlay_height if hasattr(ui_constants, 'overlay_height') else 100
ocr_x = cell_x
ocr_y = cell_y + cell_height - overlay_height  # 셀 하단 오버레이 영역
ocr_width = cell_width  # 너비는 셀 전체
ocr_height = overlay_height  # GUI에서 설정된 높이
ocr_area = (ocr_x, ocr_y, ocr_width, ocr_height)
```

### 4. GridOverlayWidget 표시 (라인 754-758)
```python
# OCR 영역 표시
ocr_x, ocr_y, ocr_w, ocr_h = cell.ocr_area
ocr_pen = QPen(QColor(255, 255, 0, 150), 2, Qt.DashLine)
painter.setPen(ocr_pen)
painter.drawRect(ocr_x, ocr_y, ocr_w, ocr_h)
```

## 사용 방법

1. GUI의 "고급 설정" 탭으로 이동
2. "오버레이 높이" 슬라이더를 원하는 값으로 조정 (30px ~ 200px)
3. 슬라이더가 자동으로 10px 단위로 스냅됩니다
4. 변경사항이 즉시 적용되며, 모든 셀의 OCR 영역이 재계산됩니다
5. "오버레이 표시" 버튼을 클릭하면 노란색 점선으로 OCR 영역이 표시됩니다

## 기술적 세부사항

- **최소값**: 30px (너무 작으면 텍스트 감지가 어려움)
- **최대값**: 200px (셀 높이를 초과하지 않도록)
- **단위**: 10px (정확한 조정을 위해)
- **실시간 업데이트**: 슬라이더 조정 즉시 적용
- **영속성**: ui_constants를 통해 설정값 유지

## 향후 개선사항

1. config.json에 오버레이 높이 설정 저장
2. 모니터별로 다른 오버레이 높이 설정
3. 프리셋 버튼 추가 (예: 소형 50px, 중형 100px, 대형 150px)