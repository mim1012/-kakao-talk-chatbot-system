"""
카카오톡 OCR 챗봇 EXE 빌드 스크립트
모든 종속성을 포함한 단일 실행 파일 생성
"""
import os
import sys
import shutil
import subprocess
from pathlib import Path

def clean_build_folders():
    """빌드 폴더 정리"""
    folders_to_clean = ['build', 'dist', '__pycache__']
    for folder in folders_to_clean:
        if os.path.exists(folder):
            print(f"Cleaning {folder}...")
            shutil.rmtree(folder)
    
    # .spec 파일의 임시 폴더도 정리
    for item in os.listdir('.'):
        if item.endswith('.pyc') or item.endswith('.pyo'):
            os.remove(item)

def build_exe():
    """PyInstaller를 사용한 EXE 빌드"""
    print("=" * 60)
    print("카카오톡 OCR 챗봇 EXE 빌드 시작")
    print("=" * 60)
    
    # 1. 기존 빌드 폴더 정리
    clean_build_folders()
    
    # 2. PyInstaller 실행
    print("\n빌드 시작...")
    cmd = [
        sys.executable, '-m', 'PyInstaller',
        '--clean',  # 임시 파일 정리
        '--noconfirm',  # 기존 출력 덮어쓰기
        'kakao_chatbot.spec'
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"빌드 실패:\n{result.stderr}")
            return False
        print("빌드 성공!")
        
    except Exception as e:
        print(f"빌드 중 오류 발생: {e}")
        return False
    
    # 3. 추가 파일 복사
    print("\n추가 파일 복사 중...")
    dist_path = Path('dist')
    
    # config.json 복사 (spec에서 처리하지만 확실하게)
    if os.path.exists('config.json'):
        shutil.copy2('config.json', dist_path / 'config.json')
        print("- config.json 복사 완료")
    
    # 실행 배치 파일 생성
    batch_content = """@echo off
echo ============================================================
echo 카카오톡 OCR 챗봇 시스템
echo ============================================================
echo.
echo 프로그램을 시작합니다...
echo.
KakaoOCRChatbot.exe
pause
"""
    
    with open(dist_path / 'run_chatbot.bat', 'w', encoding='utf-8') as f:
        f.write(batch_content)
    print("- 실행 배치 파일 생성 완료")
    
    # 4. 사용 안내 파일 생성
    readme_content = """카카오톡 OCR 챗봇 시스템
========================

1. 실행 방법:
   - run_chatbot.bat 파일을 더블클릭하여 실행
   - 또는 KakaoOCRChatbot.exe를 직접 실행

2. 처음 실행 시:
   - PaddleOCR 모델 다운로드로 시간이 걸릴 수 있습니다 (1-2분)
   - 인터넷 연결이 필요합니다

3. 주의사항:
   - config.json 파일을 통해 설정 변경 가능
   - 카카오톡 창 위치가 config.json의 설정과 일치해야 함
   - Windows Defender가 차단할 경우 "추가 정보" → "실행" 클릭

4. 문제 해결:
   - 실행되지 않을 경우: 관리자 권한으로 실행
   - OCR이 작동하지 않을 경우: 카카오톡 창 위치 확인
   - 에러 발생 시: 콘솔 창의 메시지 확인

5. 시스템 요구사항:
   - Windows 10/11 64bit
   - 최소 4GB RAM
   - 약 2GB 디스크 공간
"""
    
    with open(dist_path / 'README.txt', 'w', encoding='utf-8') as f:
        f.write(readme_content)
    print("- README.txt 생성 완료")
    
    # 5. 빌드 정보 출력
    exe_path = dist_path / 'KakaoOCRChatbot.exe'
    if exe_path.exists():
        exe_size = exe_path.stat().st_size / (1024 * 1024)  # MB 단위
        print(f"\n✅ 빌드 완료!")
        print(f"📁 위치: {exe_path.absolute()}")
        print(f"📊 크기: {exe_size:.2f} MB")
        print(f"\n배포 폴더: {dist_path.absolute()}")
        print("이 폴더를 압축하여 다른 컴퓨터로 전송하면 됩니다.")
        return True
    else:
        print("\n❌ EXE 파일이 생성되지 않았습니다.")
        return False

if __name__ == "__main__":
    success = build_exe()
    if success:
        print("\n빌드가 성공적으로 완료되었습니다!")
        print("dist 폴더를 확인하세요.")
    else:
        print("\n빌드 실패. 오류 메시지를 확인하세요.")
        sys.exit(1)