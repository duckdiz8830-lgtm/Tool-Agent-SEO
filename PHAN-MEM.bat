@echo off
chcp 65001 >nul
title LOTECH AUTOPOST VER 4.4.1.1
cd /d "%~dp0"

rem Uu tien Python rieng trong thu muc python\, khong co thi dung Python cua may.
set "PYW=%~dp0python\pythonw.exe"
set "PY=%~dp0python\python.exe"
if exist "%PYW%" (
  "%PY%" -c "import tkinter" >nul 2>&1
  if not errorlevel 1 (
    echo  [OK] Dang mo phan mem bang Python rieng...
    echo       Neu khong thay cua so hien ra sau vai giay, kiem tra lai
    echo       thu vien bang cach bam CAI-DAT-LAN-DAU.bat.
    start "" "%PYW%" "%~dp0giao-dien.py"
    exit /b
  )
)

python --version >nul 2>&1
if errorlevel 1 (
  echo  [X] May chua co Python va chua cai ban rieng.
  echo.
  echo  NGUYEN NHAN: khong tim thay Python nao tren may.
  echo  CACH XU LY:
  echo   Cach 1 ^(nen^): bam dup CAI-DAT-LAN-DAU.bat, cho vai phut.
  echo   Cach 2: vao https://www.python.org/downloads/ cai Python,
  echo           nho TICH o "Add python.exe to PATH".
  echo.
  pause
  exit /b
)

python -c "import requests, openpyxl, bleach, fitz, tksheet" >nul 2>&1
if errorlevel 1 (
  echo  Dang cai thu vien lan dau, cho khoang 1 phut...
  python -m pip install --quiet --upgrade pip
  python -m pip install --quiet -r "%~dp0requirements.txt"
)
python -c "import requests, openpyxl, bleach, fitz, tksheet" >nul 2>&1
if errorlevel 1 (
  echo.
  echo  [X] Cai thu vien that bai.
  echo.
  echo  NGUYEN NHAN: pip khong cai duoc dependency trong requirements.txt ^(co the do
  echo  mang cong ty chan, hoac khong co quyen ghi vao thu muc Python^).
  echo  CACH XU LY: mo Command Prompt, go tay dong nay roi thu lai:
  echo      python -m pip install -r requirements.txt
  echo.
  pause
  exit /b
)

echo  [OK] Thu vien du. Dang mo phan mem...
echo       Cua so phan mem se hien ra trong vai giay. Neu can xem ket qua
echo       nhanh khong mo GUI, dung 5-KIEM-TRA-KET-QUA.bat.
start "" pythonw "%~dp0giao-dien.py"
