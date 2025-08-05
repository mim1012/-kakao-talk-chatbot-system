# 🚀 실행 방법 (Python 3.11 가상환경)

## ✅ 문제 해결 완료
- subprocess.STARTUPINFO 오류 수정
- main.py의 버그 수정

## 📋 실행 단계

### PowerShell에서 실행:
```powershell
# 1. 가상환경 활성화
.\venv\Scripts\Activate.ps1

# 2. Python 버전 확인 (3.11.x 여야 함)
python --version

# 3. 프로그램 실행
python main.py
```

### CMD에서 실행:
```batch
# 1. 배치 파일로 실행 (권장)
run_chatbot.bat

# 또는 수동으로:
venv\Scripts\activate
python main.py
```

## 🔧 패키지가 없다면

### 가상환경에 패키지 설치:
```batch
install_venv_packages.bat
```

### 또는 수동 설치:
```powershell
# 가상환경 활성화 후
pip install numpy==1.24.3
pip install opencv-python==4.6.0.66
pip install PyQt5==5.15.10
pip install mss==9.0.1
pip install pyautogui==0.9.54
pip install pyperclip==1.8.2
pip install screeninfo==0.8.1
pip install paddlepaddle==2.5.2
pip install paddleocr==2.7.0.3
```

## ✅ 수정된 파일들
1. `main.py` - subprocess.STARTUPINFO 버그 수정
2. `test_ocr_system.py` - subprocess 문제 수정
3. `src/utils/silence_paddle.py` - subprocess 문제 수정

## 🎯 지금 바로 실행

PowerShell에서:
```powershell
.\venv\Scripts\Activate.ps1
python main.py
```

또는 간단히:
```batch
run_chatbot.bat
```

## ⚠️ 주의사항
- Python 3.11 가상환경 사용 중
- 첫 실행시 PaddleOCR 모델 다운로드 (정상)
- GUI가 열리면 "모니터링 시작" 클릭