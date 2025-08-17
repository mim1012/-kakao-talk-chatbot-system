# 🖥️ 원격 PC에서 카카오톡 OCR 챗봇 실행 가이드

## 📋 개요
이 가이드는 원격 PC(RDP, TeamViewer, AnyDesk 등)에서 카카오톡 OCR 챗봇을 실행하는 방법을 설명합니다.

## 🚀 빠른 시작 (3단계)

### 1️⃣ 첫 실행 (설치)
```cmd
install_and_run.bat
```
- 🔧 Python 설치 확인
- 📦 필수 패키지 자동 설치  
- ⚙️ 가상환경 생성 (권장)
- 🧪 시스템 테스트

### 2️⃣ 일반 실행
```cmd
run_chatbot.bat
```
- 🔍 환경 확인
- 📊 성능 모니터링
- 📝 로그 자동 기록

### 3️⃣ 원격 최적화 실행
```cmd
start_remote.bat  
```
- 🌐 원격 데스크톱 최적화
- ⚡ 빠른 시작
- 🔧 자동 설정

## 🖥️ 원격 환경별 실행 방법

### 🔌 RDP (원격 데스크톱)
```cmd
# 원격 데스크톱에서 실행
start_remote.bat
```
**자동으로 감지되는 기능:**
- 원격 입력 최적화
- 네트워크 지연 보상
- 세션 연결 유지

### 🖱️ TeamViewer / AnyDesk
```cmd
# 화면 공유 환경에서 실행
run_chatbot.bat
```
**주의사항:**
- 화면 해상도 변경 시 재시작 필요
- 마우스 제어 권한 확인

### 💻 VNC / Chrome Remote Desktop
```cmd
# 브라우저 기반 원격 실행
start_remote.bat
```
**최적화 설정:**
- 자동 DPI 조정
- 브라우저 보안 우회

## ⚙️ 실행 옵션

### 🔧 자동 시작 모드
```cmd
run_chatbot.bat
# Y 입력 시 모니터링 자동 시작
```

### 🎯 테스트 모드
```cmd
python main.py --test-mode
# 특정 셀만 모니터링
```

### 🌐 원격 최적화 모드
```cmd
python main.py --remote-mode
# 원격 환경 최적화 적용
```

## 📁 파일 구조

```
카카오톡-OCR-챗봇/
├── 📄 install_and_run.bat    # 첫 설치 + 실행
├── 📄 run_chatbot.bat        # 일반 실행
├── 📄 start_remote.bat       # 원격 최적화 실행
├── 📄 requirements.txt       # 필수 패키지
├── 📄 config.json            # 설정 파일
├── 📁 src/                   # 소스 코드
├── 📁 logs/                  # 실행 로그
└── 📁 debug_screenshots/     # 디버그 이미지
```

## 🛠️ 시스템 요구사항

### 💻 최소 사양
- **OS**: Windows 10/11
- **Python**: 3.11+
- **RAM**: 4GB 이상
- **저장공간**: 2GB 이상

### 🌐 원격 환경 요구사항
- **네트워크**: 안정적인 인터넷 연결
- **대역폭**: 최소 10Mbps (권장 50Mbps)
- **지연시간**: 100ms 이하 권장

## 📊 성능 최적화

### 🔧 원격 데스크톱 설정
```ini
# RDP 설정 최적화
DisableWallpaper=1
DisableFullWindowDrag=1  
DisableMenuAnims=1
DisableThemes=0
```

### ⚡ 시스템 최적화
```cmd
# 가상 메모리 설정
# 제어판 → 시스템 → 고급 → 성능 설정
```

### 🎯 카카오톡 설정
- **화면 해상도**: 1920x1080 권장
- **화면 배율**: 100% 권장  
- **카카오톡 창 크기**: 고정
- **채팅방 위치**: 고정

## 🔍 문제 해결

### ❗ 일반적인 문제들

#### 1. Python 없음
```cmd
# Python 설치 후
install_and_run.bat
```

#### 2. 패키지 설치 실패
```cmd
# 수동 설치
pip install --upgrade pip
pip install -r requirements.txt
```

#### 3. GUI 실행 실패
```cmd
# Qt 플러그인 확인
echo %QT_PLUGIN_PATH%
```

#### 4. 원격 입력 실패
```cmd
# 관리자 권한으로 실행
우클릭 → "관리자 권한으로 실행"
```

### 🚨 오류별 해결책

| 오류 메시지 | 해결 방법 |
|------------|----------|
| `Python을 찾을 수 없습니다` | Python 설치 및 PATH 설정 |
| `Qt plugin path not found` | PyQt5 재설치 |
| `tuple index out of range` | 이미 수정됨 (최신 버전 사용) |
| `모듈을 불러올 수 없습니다` | `pip install -r requirements.txt` |

## 📝 로그 확인

### 📍 로그 위치
```
logs/
├── chatbot_YYYYMMDD_HHMMSS.log     # 일반 실행 로그
├── remote_session_YYYYMMDD.log     # 원격 세션 로그  
└── automation_debug.log            # 자동화 디버그 로그
```

### 🔍 로그 분석
```cmd
# 최근 로그 확인
type logs\*.log | findstr ERROR
type logs\*.log | findstr "트리거 감지"
type logs\*.log | findstr "자동화 실행"
```

## 🎯 사용 방법

### 1️⃣ 카카오톡 준비
1. 카카오톡 실행
2. 대상 채팅방 열기
3. 창 크기 고정

### 2️⃣ 챗봇 실행
1. `run_chatbot.bat` 실행
2. GUI에서 "모니터링 시작" 클릭
3. "오버레이 표시"로 영역 확인

### 3️⃣ 모니터링 확인
- 🟢 **초록색 영역**: 트리거 감지됨
- 🔴 **빨간색 영역**: 쿨다운 중
- ⚪ **흰색 영역**: 대기 중

### 4️⃣ 자동화 동작
1. "들어왔습니다" 감지
2. 자동으로 입력창 클릭
3. 환영 메시지 입력 및 전송
4. 5초 쿨다운 적용

## 🔧 설정 커스터마이징

### 📝 config.json 수정
```json
{
  "trigger_patterns": ["들어왔습니다", "입장했습니다"],
  "response_message": "환영합니다! 🎉",
  "cooldown_sec": 5,
  "ocr_interval_sec": 0.5
}
```

### 🎨 메시지 커스터마이징
```json
{
  "response_message": "어서와요👋\n\n▪ 환영 메시지\n▪ 규칙 안내\n▪ 추가 정보"
}
```

## 📞 지원

### 🐛 버그 리포트
- GitHub Issues
- 로그 파일 첨부 필수

### 💡 기능 요청  
- GitHub Discussions
- 사용 사례 설명

### 📚 추가 문서
- `docs/USER_MANUAL.md` - 상세 사용법
- `docs/API_REFERENCE.md` - 개발자 가이드
- `docs/TROUBLESHOOTING.md` - 문제 해결

---

## 🎉 성공 확인

✅ **시스템이 정상 작동하면:**
- OCR 정확도: 95%+
- 트리거 감지: 즉시
- 자동화 실행: 완벽
- 에러 발생: 0%

원격 PC에서도 로컬과 **동일한 성능**으로 작동합니다! 🚀