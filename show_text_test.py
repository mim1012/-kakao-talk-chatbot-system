#!/usr/bin/env python3
"""
화면에 "들어왔습니다" 텍스트를 표시하여 OCR 테스트
"""
import tkinter as tk
from tkinter import font

def show_test_text():
    """테스트용 텍스트를 화면에 표시"""
    root = tk.Tk()
    root.title("OCR 테스트")
    root.geometry("400x200+100+100")  # 크기와 위치 설정
    root.configure(bg='white')
    
    # 큰 폰트로 텍스트 표시
    test_font = font.Font(family="Arial", size=24, weight="bold")
    
    label = tk.Label(
        root, 
        text="들어왔습니다",
        font=test_font,
        bg='white',
        fg='black',
        pady=50
    )
    label.pack(expand=True)
    
    # 설명 라벨
    info_label = tk.Label(
        root,
        text="이 창을 오버레이 영역에 위치시키고\n메인 프로그램에서 감지되는지 확인하세요",
        font=("Arial", 10),
        bg='white',
        fg='gray'
    )
    info_label.pack()
    
    print("🔍 테스트 창이 열렸습니다.")
    print("💡 이 창을 드래그하여 오버레이 영역(화면 하단 100px)에 위치시키세요.")
    print("📱 메인 프로그램에서 '🎯🎯🎯 감지!' 메시지가 나타나는지 확인하세요.")
    
    root.mainloop()

if __name__ == "__main__":
    show_test_text()