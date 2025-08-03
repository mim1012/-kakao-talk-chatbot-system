# 설치 가이드

## 시스템 요구사항

### 최소 요구사항
- **OS**: Windows 10 (버전 1909 이상)
- **Python**: 3.11.x (3.13은 numpy 호환성 문제로 권장하지 않음)
- **RAM**: 4GB
- **저장공간**: 2GB 이상
- **모니터**: 1920x1080 해상도

### 권장 요구사항
- **OS**: Windows 11
- **Python**: 3.11.9
- **RAM**: 8GB 이상
- **저장공간**: 5GB 이상
- **모니터**: 듀얼 모니터 (1920x1080)
- **GPU**: CUDA 지원 GPU (선택사항)

## 사전 준비사항

### 1. Python 설치

1. [Python 3.11.9](https://www.python.org/downloads/release/python-3119/) 다운로드
2. 설치 시 "Add Python to PATH" 체크
3. 설치 확인:
   ```cmd
   python --version
   # Python 3.11.9
   ```

### 2. Git 설치 (선택사항)

1. [Git for Windows](https://git-scm.com/download/win) 다운로드
2. 기본 설정으로 설치

### 3. Visual C++ Redistributable 설치

PaddleOCR 실행에 필요합니다:
- [Microsoft Visual C++ Redistributable](https://aka.ms/vs/17/release/vc_redist.x64.exe)

## 설치 단계

### 1단계: 프로젝트 다운로드

#### Git을 사용하는 경우:
```bash
git clone https://github.com/your-repo/kakaotalk-ocr-chatbot.git
cd kakaotalk-ocr-chatbot
```

#### ZIP 파일로 다운로드하는 경우:
1. GitHub에서 "Code" → "Download ZIP" 클릭
2. 원하는 위치에 압축 해제
3. 압축 해제한 폴더로 이동

### 2단계: 가상환경 생성

```bash
# 가상환경 생성
python -m venv venv

# 가상환경 활성화 (Windows)
venv\Scripts\activate

# 가상환경 활성화 확인 (프롬프트에 (venv) 표시)
```

### 3단계: 기본 패키지 설치

```bash
# pip 업그레이드
python -m pip install --upgrade pip

# 기본 의존성 설치
pip install -r requirements.txt
```

### 4단계: PaddleOCR 설치

#### CPU 버전 (권장):
```bash
pip install paddlepaddle==2.5.2
```

#### GPU 버전 (CUDA 11.7):
```bash
pip install paddlepaddle-gpu==2.5.2
```

### 5단계: 추가 의존성 확인

```bash
# 설치 확인 스크립트 실행
python tools/check_installation.py
```

## 설정 파일 구성

### 1. config.json 생성

```json
{
    "grid_rows": 3,
    "grid_cols": 5,
    "ocr_interval_sec": 0.3,
    "cooldown_sec": 5,
    "trigger_patterns": ["들어왔습니다", "입장했습니다"],
    "reply_message": "어서오세요!",
    "ui_constants": {
        "ocr_area_y_offset": 100,
        "ocr_area_height": 80,
        "overlay_height": 120,
        "grid_line_width": 3,
        "trigger_box_color": [0, 255, 0],
        "normal_box_color": [255, 255, 255],
        "cooldown_box_color": [255, 0, 0]
    },
    "ocr_preprocess": {
        "use_gpu": false,
        "lang": "korean",
        "det": true,
        "rec": true,
        "cls": false
    }
}
```

### 2. 로깅 설정 (선택사항)

`logging_config.json` 생성:
```json
{
    "version": 1,
    "disable_existing_loggers": false,
    "formatters": {
        "default": {
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        }
    },
    "handlers": {
        "file": {
            "class": "logging.handlers.RotatingFileHandler",
            "filename": "logs/chatbot.log",
            "maxBytes": 10485760,
            "backupCount": 5,
            "formatter": "default"
        }
    },
    "root": {
        "level": "INFO",
        "handlers": ["file"]
    }
}
```

## 첫 실행

### 1. 기본 실행
```bash
python main.py
```

### 2. 배치 파일로 실행
```bash
run_with_qt.bat
```

### 3. 테스트 실행
```bash
# 단위 테스트
pytest tests/test_final_fixed.py -v

# OCR 테스트
python tools/test_ocr_simple.py
```

## 문제 해결

### 1. ModuleNotFoundError: No module named 'paddleocr'
```bash
pip install paddleocr
```

### 2. ImportError: DLL load failed
Visual C++ Redistributable 재설치 필요

### 3. numpy 관련 오류 (Python 3.13)
Python 3.11로 다운그레이드:
```bash
# 가상환경 삭제
deactivate
rmdir /s venv

# Python 3.11로 재설치
py -3.11 -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

### 4. PyQt5 관련 오류
```bash
# PyQt5 재설치
pip uninstall PyQt5 PyQt5-Qt5 PyQt5-sip
pip install PyQt5==5.15.9
```

### 5. 권한 오류
관리자 권한으로 실행:
1. cmd를 관리자 권한으로 실행
2. 프로젝트 폴더로 이동
3. `python main.py` 실행

## GPU 가속 설정 (선택사항)

### CUDA 설치
1. [CUDA Toolkit 11.7](https://developer.nvidia.com/cuda-11-7-0-download-archive) 다운로드
2. [cuDNN 8.4](https://developer.nvidia.com/cudnn) 다운로드
3. 환경변수 설정

### PaddleOCR GPU 설정
```python
# config.json
{
    "ocr_preprocess": {
        "use_gpu": true,
        "gpu_mem": 500
    }
}
```

## 다른 PC로 이전

### 1. 이전 패키지 생성
```bash
python create_transfer_package.py
```

### 2. 새 PC에서 설치
```bash
# 패키지 압축 해제 후
python setup_on_new_pc.py
```

## 업데이트

### Git을 사용하는 경우:
```bash
git pull origin main
pip install -r requirements.txt --upgrade
```

### 수동 업데이트:
1. 최신 버전 다운로드
2. config.json 백업
3. 새 버전으로 교체
4. config.json 복원

## 제거

### 1. 가상환경 제거
```bash
deactivate
rmdir /s venv
```

### 2. 프로젝트 폴더 삭제
```bash
rmdir /s "카카오톡 챗봇 시스템"
```

### 3. 레지스트리 정리 (선택사항)
OCR 모델 캐시 제거:
```bash
rmdir /s "%USERPROFILE%\.paddleocr"
```