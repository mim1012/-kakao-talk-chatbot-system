# 🚀 간단 설치 (PyMuPDF 오류 해결)

## PowerShell에서 실행

가상환경이 활성화된 상태에서:

### 1. PaddleOCR만 설치 (PyMuPDF 제외)
```powershell
pip install paddlepaddle==2.5.2
pip install --no-deps paddleocr==2.7.0.3
```

### 2. 필수 의존성 설치
```powershell
pip install opencv-python==4.6.0.66
pip install opencv-contrib-python==4.6.0.66
pip install shapely pyclipper Pillow
pip install numpy==1.24.3 scipy scikit-image
pip install imgaug lmdb rapidfuzz
pip install attrdict beautifulsoup4 lxml
```

### 3. 설치 확인
```powershell
python -c "from paddleocr import PaddleOCR; ocr = PaddleOCR(lang='korean'); print('✅ PaddleOCR 설치 성공!')"
```

### 4. 프로그램 실행
```powershell
python main.py
```

## 또는 배치 파일 사용
```powershell
.\install_paddle_minimal.bat
```

## ⚠️ 참고
- PyMuPDF는 PDF 파일 처리용 (선택사항)
- 이미지 OCR은 PyMuPDF 없이 작동
- 설치 오류는 무시해도 됨

## ✅ 핵심 패키지만 확인
```powershell
python -c "import paddle; print('PaddlePaddle OK')"
python -c "from paddleocr import PaddleOCR; print('PaddleOCR OK')"
```

이제 작동합니다!