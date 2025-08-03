#!/usr/bin/env python3
"""Qt 플러그인 문제 해결 스크립트"""
import os
import sys
import shutil
from pathlib import Path

def fix_qt_plugin():
    """Qt 플러그인 경로 문제 해결"""
    
    print("Qt 플러그인 문제 해결 중...")
    
    # 가상환경 경로 찾기
    venv_path = Path(sys.executable).parent.parent
    qt_plugin_source = venv_path / "Lib" / "site-packages" / "PyQt5" / "Qt5" / "plugins"
    
    if not qt_plugin_source.exists():
        print(f"오류: Qt 플러그인 폴더를 찾을 수 없습니다: {qt_plugin_source}")
        return False
    
    # 실행 파일 옆에 platforms 폴더 복사
    exe_dir = Path(sys.executable).parent
    platforms_dest = exe_dir / "platforms"
    
    if not platforms_dest.exists():
        print(f"platforms 폴더를 복사 중: {platforms_dest}")
        shutil.copytree(qt_plugin_source / "platforms", platforms_dest)
        print("✓ platforms 폴더 복사 완료")
    else:
        print("✓ platforms 폴더가 이미 존재합니다")
    
    # 환경 변수 설정 확인
    print("\n환경 변수 설정:")
    print(f"QT_PLUGIN_PATH={qt_plugin_source}")
    print(f"QT_QPA_PLATFORM_PLUGIN_PATH={qt_plugin_source / 'platforms'}")
    
    # 테스트
    print("\nPyQt5 테스트 중...")
    try:
        from PyQt5.QtWidgets import QApplication
        app = QApplication([])
        print("✓ PyQt5가 정상적으로 로드되었습니다!")
        return True
    except Exception as e:
        print(f"✗ PyQt5 로드 실패: {e}")
        return False

if __name__ == "__main__":
    if fix_qt_plugin():
        print("\n성공! 이제 main.py를 실행할 수 있습니다.")
    else:
        print("\n실패! PyQt5를 재설치해보세요:")
        print("pip uninstall -y PyQt5 PyQt5-Qt5 PyQt5-sip")
        print("pip install PyQt5==5.15.10")