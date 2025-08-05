# 🔧 가상환경 PaddleOCR 설정 가이드

## 🚨 현재 문제
- PaddleOCR이 가상환경에 설치되지 않음
- QTextCursor 경고 (수정됨)

## ✅ 해결 방법

### 1단계: PaddleOCR 설치
```batch
install_paddleocr_venv.bat
```

이 스크립트는:
- 가상환경 활성화
- PaddlePaddle 2.5.2 설치 (Python 3.11 호환)
- PaddleOCR 2.7.0.3 설치
- 필요한 의존성 모두 설치

### 2단계: 설치 확인
```powershell
# PowerShell에서
.\venv\Scripts\Activate.ps1
python check_venv.py
```

### 3단계: 프로그램 실행
```powershell
# 가상환경 활성화 상태에서
python main.py
```

## 📦 수동 설치 (필요시)

PowerShell에서 가상환경 활성화 후:
```powershell
.\venv\Scripts\Activate.ps1

# PaddleOCR 설치
pip install paddlepaddle==2.5.2
pip install paddleocr==2.7.0.3

# 추가 의존성
pip install shapely pyclipper imgaug
```

## 🔍 설치 확인

```python
# Python에서 테스트
from paddleocr import PaddleOCR
ocr = PaddleOCR(lang='korean')
print("PaddleOCR 설치 성공!")
```

## ⚠️ 주의사항

### Python 버전
- Python 3.11 권장
- Python 3.13은 호환성 문제 있음

### PaddleOCR 버전
- paddlepaddle==2.5.2 (3.11 호환)
- paddleocr==2.7.0.3 (안정 버전)

### 첫 실행
- 모델 다운로드로 시간 소요 (정상)
- 약 100MB 다운로드

## 🎯 빠른 실행

1. **PaddleOCR 설치**
   ```batch
   install_paddleocr_venv.bat
   ```

2. **확인**
   ```batch
   venv\Scripts\activate
   python check_venv.py
   ```

3. **실행**
   ```batch
   python main.py
   ```

## ✅ 수정된 문제들

1. **subprocess.STARTUPINFO** - main.py 수정됨
2. **QTextCursor 경고** - chatbot_gui.py 수정됨
3. **PaddleOCR API** - 2.7.0.3 버전 호환

## 📝 트러블슈팅

### "PaddleOCR not available" 오류
→ `install_paddleocr_venv.bat` 실행

### "No module named paddle" 오류
→ 가상환경이 활성화되었는지 확인
```powershell
.\venv\Scripts\Activate.ps1
```

### GUI가 열리지 않음
→ PyQt5 재설치
```powershell
pip install --force-reinstall PyQt5==5.15.10
```

## 🚀 완료!

모든 설정이 끝났습니다. PaddleOCR을 설치하고 프로그램을 실행하세요!