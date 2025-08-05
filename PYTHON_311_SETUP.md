# 🐍 Python 3.11 전환 가이드

## 📋 빠른 시작 (3단계)

### 1단계: Python 3.11 가상환경 생성
```batch
setup_venv_py311.bat
```

### 2단계: 패키지 설치
```batch
install_py311.bat
```

### 3단계: 프로그램 실행
```batch
start_chatbot_py311.bat
```

---

## 🔍 왜 Python 3.11인가?

### Python 3.13의 문제점:
- ❌ NumPy 호환성 문제 (1.26.4 컴파일 불가)
- ❌ 많은 패키지가 아직 3.13 미지원
- ❌ PaddleOCR이 3.13에서 불안정
- ❌ PyQt5 DLL 로딩 문제

### Python 3.11의 장점:
- ✅ 모든 주요 패키지 완벽 지원
- ✅ NumPy 1.24.3 안정적 작동
- ✅ PaddleOCR 2.7.0.3 완벽 호환
- ✅ PyQt5 문제 없음
- ✅ 성능 최적화됨

---

## 📦 생성된 파일 설명

### 1. `setup_venv_py311.bat`
- Python 3.11 자동 검색
- 가상환경 생성
- 여러 설치 경로 확인

### 2. `install_py311.bat`
- 모든 필수 패키지 설치
- 버전 호환성 검증
- 설치 상태 확인

### 3. `start_chatbot_py311.bat`
- Python 3.11 환경 확인
- 자동으로 가상환경 활성화
- GUI 실행

### 4. `requirements_py311.txt`
- Python 3.11 전용 패키지 목록
- 테스트 완료된 버전들
- 최적화된 의존성

---

## 🛠️ 수동 설정 (필요시)

### Python 3.11이 없는 경우:

#### 옵션 1: 공식 다운로드
```
https://www.python.org/downloads/release/python-3119/
→ Windows installer (64-bit) 다운로드
→ 설치시 "Add Python to PATH" 체크!
```

#### 옵션 2: Windows Store
```powershell
winget install Python.Python.3.11
```

### 가상환경 수동 생성:
```batch
# Python 3.11 찾기
py -3.11 --version

# 가상환경 생성
py -3.11 -m venv venv

# 활성화
venv\Scripts\activate

# 패키지 설치
pip install -r requirements_py311.txt
```

---

## ✅ 체크리스트

설정 전:
- [ ] Python 3.11 설치됨
- [ ] 기존 venv 폴더 삭제

설정 과정:
- [ ] setup_venv_py311.bat 실행
- [ ] install_py311.bat 실행
- [ ] Python 버전 확인 (3.11.x)

실행:
- [ ] start_chatbot_py311.bat 실행
- [ ] GUI 정상 표시
- [ ] 오버레이 기능 작동
- [ ] OCR 모니터링 시작

---

## 🚨 문제 해결

### "Python 3.11을 찾을 수 없습니다"
→ Python 3.11 설치 필요 (위 설치 가이드 참조)

### "pip 명령을 찾을 수 없습니다"
```batch
python -m ensurepip --upgrade
```

### "패키지 설치 실패"
```batch
# pip 업그레이드
python -m pip install --upgrade pip

# 캐시 삭제 후 재설치
pip cache purge
pip install -r requirements_py311.txt
```

### GUI가 열리지 않음
```batch
# PyQt5 재설치
pip uninstall PyQt5 PyQt5-Qt5 PyQt5-sip -y
pip install PyQt5==5.15.10
```

---

## 📊 패키지 버전 비교

| 패키지 | Python 3.13 | Python 3.11 | 상태 |
|--------|------------|-------------|------|
| numpy | 2.1.3 (문제) | 1.24.3 | ✅ 안정 |
| opencv-python | 4.10.0.84 | 4.8.1.78 | ✅ 안정 |
| PyQt5 | 5.15.11 | 5.15.10 | ✅ 안정 |
| paddlepaddle | 3.1.0 | 2.5.2 | ✅ 안정 |
| paddleocr | 3.1.0 | 2.7.0.3 | ✅ 안정 |

---

## 🎯 추천 작업 순서

1. **Python 3.11 설치 확인**
   ```batch
   py -3.11 --version
   ```

2. **배치 파일 실행**
   ```batch
   setup_venv_py311.bat
   install_py311.bat
   ```

3. **프로그램 실행**
   ```batch
   start_chatbot_py311.bat
   ```

4. **테스트**
   - GUI 열기
   - 오버레이 표시
   - 모니터링 시작

---

## 💡 참고사항

- Python 3.11.9가 가장 안정적인 버전
- 가상환경 사용 강력 권장
- 관리자 권한이 필요할 수 있음
- 첫 실행시 PaddleOCR 모델 다운로드 (정상)