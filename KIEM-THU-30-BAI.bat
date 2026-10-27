@echo off
chcp 65001 >nul
title LOTECH AUTOPOST VER 4.2 - Nghiem thu 30 bai
cd /d "%~dp0"
set PY=%~dp0python\python.exe
if not exist "%PY%" set PY=python

echo  ====================================================
echo   NGHIEM THU 30 BAI - tu cham 5 moc
echo  ====================================================
echo.
echo   thu   = khong goi AI, chi kiem tra khung va kho du lieu
echo   sinh  = goi AI that, ghi ra file, chua dang web
echo   nhap  = goi AI that va dang draft len WordPress
echo.
set /p CD=  Che do (thu / sinh / nhap), Enter = sinh:
if "%CD%"=="" set CD=sinh
set /p SL=  So bai, Enter = 30:
if "%SL%"=="" set SL=30
echo.
"%PY%" kiemthu.py --site site1 --so %SL% --che-do %CD%
echo.
pause
