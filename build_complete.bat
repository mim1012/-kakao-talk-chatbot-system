@echo off
echo ============================================================
echo 카카오톡 OCR 챗봇 완전한 EXE 빌드
echo ============================================================
echo.

REM 기존 빌드 정리
if exist dist rmdir /s /q dist
if exist build rmdir /s /q build

echo 빌드 시작... (10-15분 소요)
echo.

pyinstaller --onefile ^
    --name KakaoOCRChatbot ^
    --add-data "config.json;." ^
    --add-data "src;src" ^
    --hidden-import mss ^
    --hidden-import mss.windows ^
    --hidden-import screeninfo ^
    --hidden-import paddleocr ^
    --hidden-import paddlepaddle ^
    --hidden-import PyQt5 ^
    --hidden-import PyQt5.QtCore ^
    --hidden-import PyQt5.QtGui ^
    --hidden-import PyQt5.QtWidgets ^
    --hidden-import win32com ^
    --hidden-import win32api ^
    --hidden-import win32gui ^
    --hidden-import win32con ^
    --hidden-import pyautogui ^
    --hidden-import pynput ^
    --hidden-import pyperclip ^
    --hidden-import cv2 ^
    --hidden-import PIL ^
    --hidden-import numpy ^
    --collect-all mss ^
    --collect-all screeninfo ^
    --collect-all PyQt5 ^
    --console ^
    --noconfirm ^
    main.py

echo.
if exist dist\KakaoOCRChatbot.exe (
    echo ✅ 빌드 성공!
    copy config.json dist\ >nul
    echo.
    echo 실행 파일: dist\KakaoOCRChatbot.exe
) else (
    echo ❌ 빌드 실패!
)

pause