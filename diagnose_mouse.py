#!/usr/bin/env python3
"""마우스 제어 진단 도구"""
import ctypes
import time
import sys
import os

print("마우스 제어 진단")
print("=" * 60)

# 1. 기본 정보
print("\n[시스템 정보]")
print(f"Python 버전: {sys.version}")
print(f"작업 디렉토리: {os.getcwd()}")
print(f"관리자 권한: {'예' if ctypes.windll.shell32.IsUserAnAdmin() else '아니오'}")

# 2. 원격 세션 확인
print("\n[원격 세션 확인]")
session_name = os.environ.get('SESSIONNAME', 'Console')
print(f"세션 이름: {session_name}")
print(f"원격 데스크톱: {'예' if 'RDP' in session_name else '아니오'}")

# 프로세스 확인
try:
    import psutil
    remote_apps = []
    for proc in psutil.process_iter(['name']):
        pname = proc.info['name'].lower()
        if any(app in pname for app in ['anydesk', 'teamviewer', 'rustdesk', 'chrome remote']):
            remote_apps.append(proc.info['name'])
    if remote_apps:
        print(f"원격 프로그램 실행 중: {', '.join(remote_apps)}")
except:
    pass

# 3. 마우스 후킹 프로그램 확인
print("\n[마우스 관련 프로세스]")
try:
    import psutil
    mouse_apps = []
    suspicious = ['mouse', 'macro', 'auto', 'clicker', 'recorder', 'synergy', 'barrier']
    for proc in psutil.process_iter(['name']):
        pname = proc.info['name'].lower()
        if any(s in pname for s in suspicious):
            mouse_apps.append(proc.info['name'])
    if mouse_apps:
        print(f"마우스 관련 프로그램: {', '.join(mouse_apps)}")
    else:
        print("특별한 마우스 프로그램 없음")
except:
    pass

# 4. SetCursorPos 직접 테스트
print("\n[SetCursorPos 테스트]")
user32 = ctypes.windll.user32

# 현재 위치
class POINT(ctypes.Structure):
    _fields_ = [("x", ctypes.c_long), ("y", ctypes.c_long)]

pt = POINT()
user32.GetCursorPos(ctypes.byref(pt))
print(f"현재 위치: ({pt.x}, {pt.y})")

# 테스트 이동
new_x, new_y = pt.x + 100, pt.y + 100
print(f"목표 위치: ({new_x}, {new_y})")

result = user32.SetCursorPos(new_x, new_y)
print(f"SetCursorPos 반환값: {result}")

# Windows 에러 확인
if not result:
    error_code = ctypes.windll.kernel32.GetLastError()
    print(f"Windows 에러 코드: {error_code}")

time.sleep(0.5)
user32.GetCursorPos(ctypes.byref(pt))
print(f"실제 위치: ({pt.x}, {pt.y})")

if pt.x == new_x and pt.y == new_y:
    print("✅ 마우스 이동 성공!")
else:
    print("❌ 마우스 이동 실패!")
    
# 5. 보안 소프트웨어 확인
print("\n[보안 소프트웨어]")
try:
    import psutil
    security_apps = []
    security_names = ['defender', 'antivirus', 'kaspersky', 'norton', 'mcafee', 'avast', 'avg', 'eset', 'bitdefender']
    for proc in psutil.process_iter(['name']):
        pname = proc.info['name'].lower()
        if any(s in pname for s in security_names):
            security_apps.append(proc.info['name'])
    if security_apps:
        print(f"보안 프로그램: {', '.join(security_apps)}")
except:
    pass

# 6. 후킹 확인
print("\n[시스템 후킹 확인]")
# 마우스 후킹 여부 확인
is_hooked = user32.GetSystemMetrics(75)  # SM_MOUSEPRESENT
print(f"마우스 존재: {'예' if is_hooked else '아니오'}")

# 7. DPI 설정
print("\n[DPI 설정]")
dpi_aware = user32.IsProcessDPIAware()
print(f"DPI Aware: {'예' if dpi_aware else '아니오'}")

# DPI 설정 시도
try:
    user32.SetProcessDPIAware()
    print("DPI Aware 설정 완료")
except:
    pass

print("\n" + "=" * 60)
print("진단 완료")
print("\n가능한 해결책:")
print("1. 다른 마우스 제어 프로그램 종료")
print("2. 보안 프로그램 일시 중지")
print("3. Windows Defender 실시간 보호 끄기")
print("4. 게임 모드나 집중 지원 모드 끄기")
print("5. 디스플레이 설정에서 배율 100%로 설정")