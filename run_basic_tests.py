#!/usr/bin/env python3
"""
기본 테스트 실행 스크립트 (numpy 의존성 없는 테스트만)
"""
import sys
import subprocess

def run_basic_tests():
    """기본 테스트 실행"""
    print("=" * 60)
    print("기본 단위 테스트 실행")
    print("=" * 60)
    
    # numpy 의존성이 없는 테스트만 실행
    cmd = [
        sys.executable, "-m", "pytest",
        "tests/test_simple.py",
        "tests/test_config_manager.py",
        "tests/test_grid_manager.py",
        "-v",
        "--tb=short",
        "-k", "not (cache_manager or ocr_service or performance)",
        "--no-cov"  # 커버리지 비활성화 (빠른 실행)
    ]
    
    try:
        result = subprocess.run(cmd)
        return result.returncode
    except Exception as e:
        print(f"테스트 실행 오류: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(run_basic_tests())