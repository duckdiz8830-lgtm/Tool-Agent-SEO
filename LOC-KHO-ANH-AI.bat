@echo off
cd /d "%~dp0"
if exist "python\python.exe" ("python\python.exe" loc_kho_anh_ai.py) else (python loc_kho_anh_ai.py)
pause
