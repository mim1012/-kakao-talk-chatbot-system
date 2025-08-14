"""
최종 EXE 빌드 스크립트
모든 종속성 자동 포함
"""
import subprocess
import sys
import os
import shutil

def build_exe():
    print("="*60)
    print("카카오톡 OCR 챗봇 최종 빌드")
    print("="*60)
    
    # 기존 빌드 폴더 정리
    for folder in ['build', 'dist']:
        if os.path.exists(folder):
            shutil.rmtree(folder)
    
    # PyInstaller 명령
    cmd = [
        sys.executable, '-m', 'PyInstaller',
        '--onefile',
        '--name', 'KakaoOCRChatbot',
        '--add-data', 'config.json;.',
        '--add-data', 'src;src',
        # 숨겨진 임포트 - 실제 사용되는 모듈들
        '--hidden-import', 'mss',
        '--hidden-import', 'mss.windows',
        '--hidden-import', 'screeninfo',
        '--hidden-import', 'paddleocr',
        '--hidden-import', 'PyQt5',
        '--hidden-import', 'PyQt5.QtCore', 
        '--hidden-import', 'PyQt5.QtGui',
        '--hidden-import', 'PyQt5.QtWidgets',
        '--hidden-import', 'win32com.client',
        '--hidden-import', 'win32api',
        '--hidden-import', 'win32gui',
        '--hidden-import', 'win32con',
        '--hidden-import', 'pyautogui',
        '--hidden-import', 'pynput',
        '--hidden-import', 'pynput.keyboard',
        '--hidden-import', 'pynput.mouse',
        '--hidden-import', 'pyperclip',
        '--hidden-import', 'cv2',
        '--hidden-import', 'PIL',
        '--hidden-import', 'numpy',
        '--hidden-import', 'psutil',
        # 프로젝트 모듈들
        '--hidden-import', 'src.core.service_container',
        '--hidden-import', 'src.gui.chatbot_gui',
        '--hidden-import', 'src.ocr.optimized_paddle_service',
        '--hidden-import', 'src.monitoring.improved_monitoring_thread',
        '--hidden-import', 'src.automation.automation_service',
        '--hidden-import', 'src.utils.remote_automation',
        # 전체 수집
        '--collect-all', 'mss',
        '--collect-all', 'screeninfo',
        '--collect-all', 'PyQt5',
        '--console',
        '--noconfirm',
        'main.py'
    ]
    
    print("\n빌드 명령 실행 중...")
    result = subprocess.run(cmd, capture_output=False, text=True)
    
    if result.returncode == 0:
        print("\n✅ 빌드 성공!")
        
        # config.json 복사
        if os.path.exists('config.json'):
            shutil.copy2('config.json', 'dist/config.json')
            print("config.json 복사 완료")
        
        # 사용 안내 생성
        with open('dist/README.txt', 'w', encoding='utf-8') as f:
            f.write("""카카오톡 OCR 챗봇 시스템
========================

실행 방법:
1. KakaoOCRChatbot.exe 실행
2. 처음 실행 시 모델 다운로드 (1-2분)
3. Windows Defender 경고 시 "추가 정보" → "실행"

주의사항:
- config.json 파일 필수
- 인터넷 연결 필요 (첫 실행 시)
""")
        
        print(f"\n📁 빌드 완료: dist/KakaoOCRChatbot.exe")
        return True
    else:
        print(f"\n❌ 빌드 실패: {result.returncode}")
        return False

if __name__ == "__main__":
    success = build_exe()
    sys.exit(0 if success else 1)