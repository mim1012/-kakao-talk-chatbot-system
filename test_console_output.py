#!/usr/bin/env python3
"""콘솔 출력 테스트"""
import sys
import os

print("=" * 60)
print("콘솔 출력 테스트")
print("=" * 60)

# stdout 상태 확인
print(f"stdout: {sys.stdout}")
print(f"stdout.encoding: {sys.stdout.encoding}")

# 직접 출력
sys.stdout.write("직접 출력 테스트\n")
sys.stdout.flush()

# 콘솔에서 run_with_qt.bat로 실행 시 출력 확인
print("\n주의: run_with_qt.bat로 실행하면 콘솔 로그가 보이지 않을 수 있습니다.")
print("대신 다음과 같이 실행해보세요:")
print("1. 명령 프롬프트에서: python main.py")
print("2. 또는 디버그용: python main.py > debug.log 2>&1")

print("=" * 60)