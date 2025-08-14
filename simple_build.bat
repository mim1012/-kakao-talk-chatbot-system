@echo off
echo ============================================================
echo 카카오톡 OCR 챗봇 EXE 빌드 (간단 버전)
echo ============================================================
echo.

REM 기존 빌드 폴더 삭제
if exist dist rmdir /s /q dist
if exist build rmdir /s /q build

echo 빌드 시작... (5-10분 소요)
echo.

REM PyInstaller 실행 - 단일 파일로 생성
pyinstaller --onefile ^
    --name KakaoOCRChatbot ^
    --add-data "config.json;." ^
    --add-data "src;src" ^
    --hidden-import paddleocr ^
    --hidden-import paddlepaddle ^
    --hidden-import PyQt5 ^
    --hidden-import win32com ^
    --hidden-import win32api ^
    --hidden-import win32gui ^
    --hidden-import pyautogui ^
    --hidden-import pynput ^
    --hidden-import pyperclip ^
    --hidden-import cv2 ^
    --hidden-import PIL ^
    --hidden-import numpy ^
    --collect-all paddleocr ^
    --collect-all paddlepaddle ^
    --collect-all PyQt5 ^
    --console ^
    --noconfirm ^
    main.py

echo.
if exist dist\KakaoOCRChatbot.exe (
    echo ✅ 빌드 성공!
    echo.
    echo EXE 파일 위치: dist\KakaoOCRChatbot.exe
    echo.
    
    REM config.json 복사
    copy config.json dist\config.json >nul
    
    echo 배포 준비 완료!
    echo dist 폴더를 압축하여 다른 컴퓨터로 전송하세요.
) else (
    echo ❌ 빌드 실패!
    echo 오류 메시지를 확인하세요.
)

echo.
pause