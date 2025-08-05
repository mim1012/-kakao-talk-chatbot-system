# 🔧 PaddleOCR GitHub 직접 설치 가이드

## 문제점
- pip 버전의 PaddleOCR은 의존성 충돌 심각
- NumPy/SciPy 버전 호환성 문제
- scikit-image import 오류

## ✅ 해결 방법

### 방법 1: GitHub에서 직접 설치 (권장)

```powershell
# 1. 기존 제거
pip uninstall paddleocr -y

# 2. GitHub에서 설치
pip install git+https://github.com/PaddlePaddle/PaddleOCR.git@release/2.7
```

### 방법 2: ZIP 다운로드 후 설치

1. **다운로드**: https://github.com/PaddlePaddle/PaddleOCR/archive/refs/heads/release/2.7.zip

2. **압축 해제** 

3. **설치** (압축 해제한 폴더에서):
```powershell
cd PaddleOCR-release-2.7
pip install -e .
```

### 방법 3: 클린 설치 스크립트

```powershell
python install_clean_paddleocr.py
```

## 🎯 대안: EasyOCR 사용

PaddleOCR이 계속 문제라면 EasyOCR로 전환:

```powershell
pip uninstall paddleocr paddlepaddle -y
pip install easyocr

# 테스트
python -c "import easyocr; reader = easyocr.Reader(['ko']); print('EasyOCR OK')"
```

## 📝 수동 설치 단계

```powershell
# 1. 필수 패키지 먼저 설치
pip install numpy==1.26.0 scipy==1.11.4
pip install opencv-python==4.8.1.78
pip install shapely pyclipper Pillow

# 2. PaddleOCR 소스 다운로드
git clone https://github.com/PaddlePaddle/PaddleOCR.git
cd PaddleOCR

# 3. 개발 모드로 설치
pip install -e .

# 4. 테스트
python -c "from paddleocr import PaddleOCR; print('성공')"
```

## ⚠️ 그래도 안 되면

### EasyOCR로 코드 수정

```python
# 기존 (PaddleOCR)
from paddleocr import PaddleOCR
ocr = PaddleOCR(lang='korean')

# 변경 (EasyOCR)
import easyocr
ocr = easyocr.Reader(['ko'])
```

## 🚀 즉시 실행 가능한 해결책

```powershell
# 모든 OCR 관련 제거
pip uninstall paddleocr paddlepaddle scikit-image scipy -y

# 깨끗한 재설치
pip install numpy==1.26.0
pip install scipy==1.11.4
pip install scikit-image==0.22.0

# GitHub에서 PaddleOCR
pip install git+https://github.com/PaddlePaddle/PaddleOCR.git
```

이래도 안 되면 EasyOCR을 사용하세요!