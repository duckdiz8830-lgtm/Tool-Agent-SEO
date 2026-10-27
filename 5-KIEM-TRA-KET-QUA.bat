@echo off
chcp 65001 >nul
title LOTECH AUTOPOST VER 4.2 - Kiem tra ket qua
cd /d "%~dp0"

rem Chi la wrapper goi cong_cu_kiem_tra_ket_qua.py - KHONG co logic doc DB
rem o day, toan bo logic nam trong file .py (dung chung voi giao-dien.py).

set PY=%~dp0python\python.exe
if not exist "%PY%" set PY=python

echo  ====================================================
echo   KIEM TRA KET QUA - doc du lieu tu database
echo  ====================================================
echo.

"%PY%" --version >nul 2>&1
if errorlevel 1 (
  echo  [X] Khong tim thay Python. Bam CAI-DAT-LAN-DAU.bat truoc.
  echo.
  pause
  exit /b
)

"%PY%" "%~dp0cong_cu_kiem_tra_ket_qua.py" %*
if errorlevel 1 (
  echo.
  echo  [X] Co loi xay ra khi doc du lieu. Xem chi tiet ben tren.
  echo.
  pause
  exit /b
)

echo.
echo  ====================================================
echo   XONG. File du lieu: phase2-du-lieu.db (cung thu muc nay^)
echo  ====================================================
pause
