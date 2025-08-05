# Python 3.11 설치 및 설정 가이드

## 1. Python 3.11 설치

### 방법 1: 공식 웹사이트에서 다운로드
1. https://www.python.org/downloads/ 접속
2. Python 3.11.9 다운로드 (최신 3.11 버전)
3. 설치시 **"Add Python to PATH"** 체크 필수!

### 방법 2: Windows Store에서 설치
```powershell
# Windows Store에서 Python 3.11 검색 후 설치
# 또는 PowerShell에서:
winget install Python.Python.3.11
```

## 2. Python 3.11 확인

```batch
python --version
```
출력: `Python 3.11.x`

만약 여전히 3.13이 나온다면:
```batch
py -3.11 --version
```

## 3. 가상환경 생성 (Python 3.11)

```batch
# 기존 가상환경 삭제
rmdir /s /q venv

# Python 3.11로 새 가상환경 생성
py -3.11 -m venv venv

# 또는 Python 3.11 경로 직접 지정
C:\Python311\python.exe -m venv venv
```

## 4. 가상환경 활성화

```batch
venv\Scripts\activate
```

## 5. 패키지 설치

```batch
# pip 업그레이드
python -m pip install --upgrade pip

# 필수 패키지 설치
pip install -r requirements_py311.txt
```

## 6. 시스템 경로 확인

Python 3.11이 기본으로 실행되도록 시스템 PATH 설정:

1. 시스템 속성 → 고급 → 환경 변수
2. 시스템 변수에서 Path 편집
3. Python 3.11 경로가 Python 3.13보다 위에 있는지 확인:
   - `C:\Python311\Scripts\`
   - `C:\Python311\`
   - (Python 3.13 경로는 제거하거나 아래로 이동)

## 7. 확인

```batch
# 가상환경 활성화 후
python --version
# 출력: Python 3.11.x

# pip 확인
pip --version
# 출력: ... (python 3.11)
```

## 문제 해결

### Python 3.11이 없는 경우
직접 다운로드: https://www.python.org/downloads/release/python-3119/
- Windows installer (64-bit) 선택

### 여러 Python 버전이 설치된 경우
Python Launcher 사용:
```batch
py -3.11 -m venv venv
```

### pip가 작동하지 않는 경우
```batch
python -m ensurepip --upgrade
```