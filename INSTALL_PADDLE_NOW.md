# 🚀 지금 바로 PaddleOCR 설치하기

## PowerShell에서 실행 (가상환경 활성화된 상태에서)

### 방법 1: 배치 파일 실행
```powershell
.\install_paddleocr_venv.bat
```

### 방법 2: 직접 명령어 실행 (권장)

**복사해서 붙여넣기:**

```powershell
# 1. pip 업그레이드
python -m pip install --upgrade pip

# 2. PaddlePaddle 설치 (Python 3.11용)
pip install paddlepaddle==2.5.2

# 3. PaddleOCR 설치
pip install paddleocr==2.7.0.3

# 4. 추가 의존성
pip install shapely pyclipper imgaug scikit-image lmdb tqdm visualdl

# 5. 설치 확인
python -c "import paddle; print(f'✅ PaddlePaddle {paddle.__version__} 설치 완료')"
python -c "from paddleocr import PaddleOCR; print('✅ PaddleOCR 설치 완료')"
```

## 🔍 한 줄씩 실행하기

가상환경이 활성화된 상태에서:

```powershell
pip install paddlepaddle==2.5.2
```

잠시 기다린 후:

```powershell
pip install paddleocr==2.7.0.3
```

## ✅ 설치 확인

```powershell
python check_venv.py
```

## 🎯 설치 후 바로 실행

```powershell
python main.py
```

## ⚠️ 오류 발생시

### "No matching distribution found"
Python 3.13을 사용 중일 수 있습니다. Python 3.11 권장:
```powershell
python --version
```

### 설치가 느린 경우
정상입니다. PaddlePaddle은 크기가 큽니다 (약 400MB).

## 📝 전체 과정 (처음부터)

```powershell
# 1. 가상환경 확인
python --version

# 2. PaddlePaddle 설치
pip install paddlepaddle==2.5.2

# 3. PaddleOCR 설치  
pip install paddleocr==2.7.0.3

# 4. 확인
python -c "from paddleocr import PaddleOCR; print('OK')"

# 5. 실행
python main.py
```

지금 바로 위 명령어를 실행하세요!