#!/usr/bin/env python3
"""
테스트 실행 스크립트
"""
import sys
import os
import io
import subprocess
from pathlib import Path

# UTF-8 인코딩 설정
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
os.environ['PYTHONIOENCODING'] = 'utf-8'

def run_tests():
    """pytest 실행"""
    print("=" * 60)
    print("🧪 카카오톡 챗봇 시스템 단위 테스트 실행")
    print("=" * 60)
    
    # pytest 명령어 구성
    cmd = [
        sys.executable, "-m", "pytest",
        "-v",  # verbose
        "--tb=short",  # 짧은 트레이스백
        "--cov=src",  # 커버리지
        "--cov-report=html",  # HTML 리포트
        "--cov-report=term-missing",  # 터미널 리포트
        "--html=test_report.html",  # HTML 테스트 리포트
        "--self-contained-html",  # 독립 HTML
        "tests/"  # 테스트 디렉토리
    ]
    
    try:
        # 테스트 실행
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        # 결과 출력
        print(result.stdout)
        if result.stderr:
            print("에러 출력:")
            print(result.stderr)
        
        # 성공/실패 메시지
        if result.returncode == 0:
            print("\n✅ 모든 테스트가 성공했습니다!")
            print("📊 커버리지 리포트: htmlcov/index.html")
            print("📋 테스트 리포트: test_report.html")
        else:
            print("\n❌ 일부 테스트가 실패했습니다.")
            
        return result.returncode
        
    except subprocess.CalledProcessError as e:
        print(f"테스트 실행 중 오류 발생: {e}")
        return 1
    except FileNotFoundError:
        print("pytest가 설치되지 않았습니다.")
        print("설치: pip install pytest pytest-cov pytest-html")
        return 1

if __name__ == "__main__":
    sys.exit(run_tests())