# 문제 해결 가이드

## 자주 발생하는 문제

### 1. 프로그램이 시작되지 않음

#### 증상
- 더블클릭해도 반응 없음
- 검은 창이 잠깐 나타났다가 사라짐

#### 해결방법

1. **Python 버전 확인**
   ```cmd
   python --version
   ```
   - Python 3.11.x 필요 (3.13은 호환성 문제)

2. **가상환경 활성화 확인**
   ```cmd
   venv\Scripts\activate
   ```

3. **의존성 재설치**
   ```cmd
   pip install -r requirements.txt --force-reinstall
   ```

4. **로그 확인**
   ```cmd
   python main.py 2> error.log
   type error.log
   ```

### 2. OCR이 텍스트를 인식하지 못함

#### 증상
- 모니터링은 작동하나 텍스트 감지 안됨
- 오버레이는 표시되나 녹색으로 변하지 않음

#### 해결방법

1. **화면 설정 확인**
   - Windows 배율: 100% 설정
   - 해상도: 1920x1080 확인
   - 카카오톡 전체화면 모드

2. **OCR 영역 조정**
   ```json
   // config.json
   {
       "ui_constants": {
           "ocr_area_y_offset": 100,  // 이 값을 조정
           "ocr_area_height": 80      // 필요시 높이도 조정
       }
   }
   ```

3. **OCR 테스트**
   ```cmd
   python tools\test_ocr_simple.py
   ```

4. **PaddleOCR 재설치**
   ```cmd
   pip uninstall paddleocr paddlepaddle
   pip install paddleocr paddlepaddle
   ```

### 3. 자동 응답이 작동하지 않음

#### 증상
- 텍스트는 감지되나 응답하지 않음
- 클릭이나 타이핑이 안됨

#### 해결방법

1. **관리자 권한 실행**
   - run_with_qt.bat 우클릭 → 관리자 권한으로 실행

2. **카카오톡 창 확인**
   - 카카오톡이 최상위 창인지 확인
   - 다른 프로그램이 가리지 않도록 조치

3. **입력 위치 재설정**
   - 테스트 자동화 기능으로 위치 확인
   - config.json에서 좌표 수정

4. **안티바이러스 예외 추가**
   - Windows Defender에 폴더 예외 추가
   - 자동화 프로그램으로 오인 방지

### 4. 성능 문제

#### 증상
- CPU 사용률 높음
- 프로그램 응답 속도 느림
- 메모리 사용량 과다

#### 해결방법

1. **OCR 간격 조정**
   ```json
   {
       "ocr_interval_sec": 0.5  // 0.3 → 0.5로 증가
   }
   ```

2. **그리드 크기 축소**
   ```json
   {
       "grid_rows": 2,  // 3 → 2로 감소
       "grid_cols": 3   // 5 → 3으로 감소
   }
   ```

3. **캐시 크기 조정**
   ```python
   # src/core/cache_manager.py
   self.image_cache = LRUCache(max_size=500)  # 1000 → 500
   ```

4. **불필요한 로깅 비활성화**
   - 로그 레벨을 WARNING 이상으로 설정

### 5. PyQt5 관련 오류

#### 증상
- "could not find or load the Qt platform plugin"
- PyQt5 import 오류

#### 해결방법

1. **PyQt5 재설치**
   ```cmd
   pip uninstall PyQt5 PyQt5-Qt5 PyQt5-sip
   pip install PyQt5==5.15.9
   ```

2. **Qt 플러그인 경로 설정**
   ```cmd
   set QT_PLUGIN_PATH=%VIRTUAL_ENV%\Lib\site-packages\PyQt5\Qt5\plugins
   ```

3. **run_with_qt.bat 사용**
   - 환경변수 자동 설정됨

### 6. numpy/scipy 호환성 문제

#### 증상
- "numpy.dtype size changed" 경고
- numpy 관련 ImportError

#### 해결방법

1. **Python 3.11 사용**
   - Python 3.13은 numpy 호환성 문제 있음

2. **호환 버전 설치**
   ```cmd
   pip install numpy==1.24.3 scipy==1.10.1
   ```

3. **SimpleLRUCache 사용**
   - numpy 없이 작동하는 캐시 구현 사용

### 7. 멀티모니터 문제

#### 증상
- 오버레이가 잘못된 모니터에 표시
- 좌표가 맞지 않음

#### 해결방법

1. **주 디스플레이 설정**
   - Windows 설정 → 디스플레이 → 주 디스플레이 지정

2. **모니터 순서 확인**
   ```python
   # 모니터 정보 확인
   python -c "import screeninfo; print(list(screeninfo.get_monitors()))"
   ```

3. **수동 오프셋 조정**
   - config.json에서 모니터별 오프셋 설정

### 8. 한글 인코딩 문제

#### 증상
- 한글이 깨져서 표시
- UnicodeDecodeError

#### 해결방법

1. **UTF-8 인코딩 설정**
   ```python
   # 파일 읽기 시
   with open(file, 'r', encoding='utf-8') as f:
   ```

2. **시스템 로케일 확인**
   ```cmd
   chcp 65001  # UTF-8로 변경
   ```

3. **config.json 인코딩 확인**
   - 메모장에서 UTF-8로 저장

## 디버깅 방법

### 1. 상세 로그 활성화

```python
# main.py 상단에 추가
import logging
logging.basicConfig(level=logging.DEBUG)
```

### 2. OCR 결과 덤프

```python
# src/monitoring/monitoring_thread.py
def _on_ocr_complete(self, cell, result, confidence, raw_results):
    print(f"OCR Result: {result}")
    print(f"Raw: {raw_results}")
```

### 3. 스크린샷 저장

```python
# OCR 전 이미지 저장
import cv2
cv2.imwrite(f"debug_{cell.id}.png", image)
```

### 4. 성능 프로파일링

```cmd
python -m cProfile -o profile.stats main.py
python -m pstats profile.stats
```

## 오류 메시지별 해결법

### "CUDA out of memory"
- GPU 메모리 부족
- use_gpu를 false로 설정

### "Permission denied"
- 관리자 권한으로 실행
- 파일이 다른 프로세스에서 사용 중

### "Connection refused"
- 방화벽 설정 확인
- localhost 접근 허용

### "Module not found"
- 가상환경 활성화 확인
- requirements.txt 재설치

## 로그 파일 위치

- **메인 로그**: `logs/chatbot.log`
- **에러 로그**: `logs/error.log`
- **성능 로그**: `logs/performance.log`

## 지원 받기

1. **로그 수집**
   ```cmd
   python tools\collect_debug_info.py
   ```

2. **시스템 정보 포함**
   - OS 버전
   - Python 버전
   - GPU 정보

3. **재현 단계 설명**
   - 정확한 동작 순서
   - 스크린샷 첨부

4. **Issue 생성**
   - GitHub Issues에 템플릿 따라 작성