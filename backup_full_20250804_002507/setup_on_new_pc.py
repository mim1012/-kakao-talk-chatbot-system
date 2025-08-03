#!/usr/bin/env python3
"""
새 컴퓨터에서 카카오톡 챗봇 시스템 설정 스크립트
Python 3.11 필요
"""
import os
import sys
import subprocess
import platform

def main():
    print("=" * 60)
    print("카카오톡 챗봇 시스템 설치 도우미")
    print("=" * 60)
    
    # Python 버전 확인
    python_version = sys.version_info
    print(f"\n현재 Python 버전: {python_version.major}.{python_version.minor}.{python_version.micro}")
    
    if python_version.major != 3 or python_version.minor < 11:
        print("❌ Python 3.11 이상이 필요합니다!")
        return
    
    print("✅ Python 버전 확인 완료")
    
    # 가상환경 생성
    print("\n1. 가상환경 생성 중...")
    if not os.path.exists("venv"):
        subprocess.run([sys.executable, "-m", "venv", "venv"])
        print("✅ 가상환경 생성 완료")
    else:
        print("✅ 가상환경이 이미 존재합니다")
    
    # 가상환경 경로
    if platform.system() == "Windows":
        pip_path = os.path.join("venv", "Scripts", "pip")
        python_path = os.path.join("venv", "Scripts", "python")
    else:
        pip_path = os.path.join("venv", "bin", "pip")
        python_path = os.path.join("venv", "bin", "python")
    
    # 패키지 설치
    print("\n2. 필수 패키지 설치 중...")
    print("   (시간이 걸릴 수 있습니다)")
    
    try:
        subprocess.run([pip_path, "install", "-r", "requirements.txt"], check=True)
        print("✅ 패키지 설치 완료")
    except subprocess.CalledProcessError:
        print("❌ 패키지 설치 중 오류 발생")
        print("   requirements.txt 파일이 있는지 확인해주세요")
        return
    
    # 설정 파일 확인
    print("\n3. 설정 파일 확인 중...")
    if os.path.exists("config.json"):
        print("✅ config.json 파일 확인됨")
    else:
        print("⚠️  config.json 파일이 없습니다")
        print("   프로그램 실행 시 기본 설정이 생성됩니다")
    
    # 실행 방법 안내
    print("\n" + "=" * 60)
    print("설치 완료!")
    print("=" * 60)
    print("\n실행 방법:")
    
    if platform.system() == "Windows":
        print("1. 명령 프롬프트에서:")
        print("   venv\\Scripts\\activate")
        print("   python main.py")
        print("\n2. 또는 run.bat 파일 실행")
    else:
        print("1. 터미널에서:")
        print("   source venv/bin/activate")
        print("   python main.py")
    
    print("\n주의사항:")
    print("- 화면 해상도와 DPI 설정에 따라 좌표 조정이 필요할 수 있습니다")
    print("- tools/adjust_coordinates.py를 실행하여 좌표를 조정하세요")
    
    # run.bat 파일 생성 (Windows)
    if platform.system() == "Windows":
        print("\n실행 파일 생성 중...")
        with open("run.bat", "w") as f:
            f.write("@echo off\n")
            f.write("call venv\\Scripts\\activate\n")
            f.write("python main.py\n")
            f.write("pause\n")
        print("✅ run.bat 파일 생성 완료")

if __name__ == "__main__":
    main()