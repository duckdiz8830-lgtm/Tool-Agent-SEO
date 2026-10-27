@echo off
setlocal
cd /d "%~dp0"
if exist "python\python.exe" (
  "python\python.exe" loc_kho_anh.py
) else (
  python loc_kho_anh.py
)
endlocal
