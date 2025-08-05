#!/usr/bin/env python3
"""
오버레이 영역 시각화 - 실제로 어디를 스캔하는지 보여줌
"""
import tkinter as tk
from tkinter import ttk
import json
import screeninfo

def show_overlay_regions():
    """오버레이 영역을 화면에 표시"""
    
    # 설정 로드
    with open('config.json', 'r', encoding='utf-8') as f:
        config = json.load(f)
    
    rows = config.get('grid_rows', 3)
    cols = config.get('grid_cols', 5)
    overlay_height = config.get('ui_constants', {}).get('overlay_height', 100)
    
    # 모니터 정보
    monitors = screeninfo.get_monitors()
    
    # 투명 윈도우 생성
    root = tk.Tk()
    root.title("OCR 오버레이 영역")
    root.attributes('-alpha', 0.3)
    root.attributes('-topmost', True)
    root.overrideredirect(True)
    
    # 전체 화면 크기
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    root.geometry(f"{screen_width}x{screen_height}+0+0")
    
    # 캔버스 생성
    canvas = tk.Canvas(root, highlightthickness=0)
    canvas.pack(fill=tk.BOTH, expand=True)
    
    # 그리드 셀의 오버레이 영역 그리기
    for monitor_idx, monitor in enumerate(monitors):
        cell_width = monitor.width // cols
        cell_height = monitor.height // rows
        
        for row in range(rows):
            for col in range(cols):
                # 셀 전체 영역
                cell_x = monitor.x + col * cell_width
                cell_y = monitor.y + row * cell_height
                
                # OCR 영역 (셀 하단 오버레이)
                ocr_x = cell_x
                ocr_y = cell_y + cell_height - overlay_height
                ocr_w = cell_width
                ocr_h = overlay_height
                
                # 셀 ID
                cell_id = f"monitor_{monitor_idx}_cell_{row}_{col}"
                
                # monitor_0_cell_1_3 강조 표시
                if cell_id == "monitor_0_cell_1_3":
                    # 빨간색으로 강조
                    canvas.create_rectangle(ocr_x, ocr_y, ocr_x + ocr_w, ocr_y + ocr_h,
                                          outline='red', width=3, fill='red', stipple='gray50')
                    canvas.create_text(ocr_x + ocr_w//2, ocr_y + ocr_h//2,
                                     text=f"{cell_id}\n(테스트 모드 영역)",
                                     fill='white', font=('Arial', 12, 'bold'))
                else:
                    # 일반 셀은 파란색
                    canvas.create_rectangle(ocr_x, ocr_y, ocr_x + ocr_w, ocr_y + ocr_h,
                                          outline='blue', width=1, fill='blue', stipple='gray75')
                
                # 좌표 표시
                coord_text = f"({ocr_x}, {ocr_y}, {ocr_w}, {ocr_h})"
                canvas.create_text(ocr_x + 5, ocr_y + 5, text=coord_text,
                                 anchor='nw', fill='yellow', font=('Arial', 8))
    
    # 채팅방 설정도 표시
    chatroom_configs = config.get('chatroom_configs', [])
    for idx, chatroom in enumerate(chatroom_configs):
        x = chatroom['ocr_x']
        y = chatroom['ocr_y']
        w = chatroom['ocr_w']
        h = chatroom['ocr_h']
        
        # 초록색으로 채팅방 영역 표시
        canvas.create_rectangle(x, y, x + w, y + h,
                              outline='green', width=2, fill='', dash=(5, 5))
        canvas.create_text(x + w//2, y + 20,
                         text=f"채팅방 {idx+1}\n({x}, {y}, {w}, {h})",
                         fill='green', font=('Arial', 10, 'bold'))
    
    # 설명 추가
    info_text = """
[빨간색] monitor_0_cell_1_3 (현재 테스트 중인 영역)
[파란색] 다른 그리드 셀의 오버레이 영역
[초록색] config.json의 채팅방 영역

ESC키를 눌러 종료
"""
    canvas.create_text(10, 10, text=info_text, anchor='nw',
                      fill='white', font=('Arial', 12))
    
    # ESC로 종료
    root.bind('<Escape>', lambda e: root.quit())
    
    root.mainloop()

if __name__ == "__main__":
    show_overlay_regions()