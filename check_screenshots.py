#!/usr/bin/env python3
"""
캡처된 스크린샷 확인
"""
import os
from datetime import datetime

def check_screenshots():
    """스크린샷 디렉토리 확인"""
    debug_dir = "screenshots/debug"
    
    print("=" * 60)
    print("캡처된 스크린샷 확인")
    print("=" * 60)
    
    if not os.path.exists(debug_dir):
        print(f"❌ {debug_dir} 폴더가 존재하지 않습니다.")
        print("메인 프로그램을 실행하여 스크린샷을 생성하세요.")
        return
    
    files = os.listdir(debug_dir)
    if not files:
        print(f"❌ {debug_dir} 폴더가 비어있습니다.")
        print("메인 프로그램을 실행하여 스크린샷을 생성하세요.")
        return
    
    print(f"📁 {debug_dir} 폴더:")
    print(f"   총 {len(files)}개 파일")
    
    # 최근 파일들만 표시
    png_files = [f for f in files if f.endswith('.png')]
    png_files.sort(key=lambda x: os.path.getmtime(os.path.join(debug_dir, x)), reverse=True)
    
    print(f"\n📸 최근 캡처된 이미지 (최대 10개):")
    for i, filename in enumerate(png_files[:10]):
        filepath = os.path.join(debug_dir, filename)
        size = os.path.getsize(filepath)
        modified = datetime.fromtimestamp(os.path.getmtime(filepath))
        
        print(f"   {i+1:2d}. {filename}")
        print(f"       크기: {size:,} bytes")
        print(f"       수정: {modified.strftime('%H:%M:%S')}")
        print(f"       경로: {os.path.abspath(filepath)}")
        print()
    
    print("💡 이미지를 열어서 각 셀에서 어떤 내용이 캡처되는지 확인하세요.")
    print("💡 '들어왔습니다' 텍스트가 해당 영역에 표시되어야 감지됩니다.")

if __name__ == "__main__":
    check_screenshots()