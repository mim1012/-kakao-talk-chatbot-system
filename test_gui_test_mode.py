#!/usr/bin/env python3
"""GUI 테스트 모드 확인"""
import sys
import os
import io

# UTF-8 설정
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# 환경 변수 설정
os.environ['PPOCR_LOG_LEVEL'] = 'ERROR'
os.environ['GLOG_minloglevel'] = '3'

sys.path.insert(0, 'src')

from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt

print("=" * 60)
print("GUI 테스트 모드 확인")
print("=" * 60)

# GUI 모듈 임포트 확인
try:
    from gui.chatbot_gui import UnifiedChatbotGUI
    print("✅ GUI 모듈 임포트 성공")
    
    # Qt 앱 생성 (표시하지 않음)
    app = QApplication(sys.argv)
    
    # GUI 인스턴스 생성
    window = UnifiedChatbotGUI()
    
    # 테스트 모드 관련 위젯 확인
    if hasattr(window, 'test_mode_checkbox'):
        print("✅ 테스트 모드 체크박스 존재")
        print(f"   - 초기 상태: {'체크됨' if window.test_mode_checkbox.isChecked() else '체크 안됨'}")
    else:
        print("❌ 테스트 모드 체크박스 없음")
        
    if hasattr(window, 'test_cell_combo'):
        print("✅ 셀 선택 콤보박스 존재")
        print(f"   - 셀 개수: {window.test_cell_combo.count()}")
        print(f"   - 초기 활성화: {'활성' if window.test_cell_combo.isEnabled() else '비활성'}")
        
        # 몇 개 셀 표시
        if window.test_cell_combo.count() > 0:
            print("   - 샘플 셀:")
            for i in range(min(3, window.test_cell_combo.count())):
                print(f"     [{i}] {window.test_cell_combo.itemText(i)}")
    else:
        print("❌ 셀 선택 콤보박스 없음")
        
    # 테스트 모드 토글 테스트
    if hasattr(window, 'test_mode_checkbox'):
        print("\n테스트 모드 토글 테스트:")
        
        # 체크박스 체크
        window.test_mode_checkbox.setChecked(True)
        window.toggle_test_mode(Qt.Checked)
        print("✅ 테스트 모드 활성화")
        print(f"   - 콤보박스 상태: {'활성' if window.test_cell_combo.isEnabled() else '비활성'}")
        
        # 체크박스 해제
        window.test_mode_checkbox.setChecked(False)
        window.toggle_test_mode(Qt.Unchecked)
        print("✅ 테스트 모드 비활성화")
        print(f"   - 콤보박스 상태: {'활성' if window.test_cell_combo.isEnabled() else '비활성'}")
    
    print("\n✅ 모든 테스트 완료!")
    
except Exception as e:
    print(f"❌ 오류 발생: {e}")
    import traceback
    traceback.print_exc()

print("=" * 60)