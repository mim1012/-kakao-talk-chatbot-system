# 🔧 PyMuPDF 오류 해결 방법

## ❌ 문제
- PyMuPDF가 빌드 실패로 PaddleOCR 설치 차단
- 긴 파일 경로 문제로 tar 추출 실패

## ✅ 해결책: PyMuPDF 제외하고 설치

### PowerShell에서 직접 실행 (권장)

```powershell
# 1. 기존 설치 시도 정리
pip uninstall paddleocr -y

# 2. PaddlePaddle만 먼저 설치
pip install paddlepaddle==2.5.2

# 3. PaddleOCR을 의존성 없이 설치
pip install --no-deps paddleocr==2.7.0.3

# 4. 필수 의존성만 개별 설치
pip install opencv-python==4.6.0.66
pip install shapely pyclipper Pillow numpy==1.24.3

# 5. 테스트
python test_paddle.py
```

### 또는 배치 파일 실행
```powershell
.\install_without_pymupdf.bat
```

## 🎯 빠른 해결책

한 줄로 실행:
```powershell
pip install paddlepaddle==2.5.2 && pip install --no-deps paddleocr==2.7.0.3 && pip install opencv-python shapely pyclipper
```

## ✅ 확인
```powershell
python -c "from paddleocr import PaddleOCR; ocr = PaddleOCR(lang='korean'); print('성공!')"
```

## 📝 참고
- PyMuPDF는 PDF 파일 읽기용 (선택사항)
- 화면 OCR에는 필요 없음
- 이미지 OCR 정상 작동

## 🚀 실행
```powershell
python main.py
```

PyMuPDF 없이도 모든 기능이 작동합니다!