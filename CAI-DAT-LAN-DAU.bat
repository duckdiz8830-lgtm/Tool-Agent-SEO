@echo off
chcp 65001 >nul
title LOTECH AUTOPOST VER 4.2 - Cai dat lan dau
cd /d "%~dp0"
setlocal

set "PYVER=3.11.9"
set "PYDIR=%~dp0python"
set "MARK=%PYDIR%\_setup-complete"

if exist "%MARK%" (
  echo  [OK] Da cai roi. Bam dup PHAN-MEM.bat de chay.
  echo       Muon cai lai thi xoa thu muc python\ roi chay lai file nay.
  pause
  exit /b
)

echo  ====================================================
echo   CAI DAT LAN DAU - tai Python rieng cho phan mem
echo  ====================================================
echo.
echo  Se tai khoang 40MB. Chi lam MOT LAN, lan sau khong can mang.
echo  Python nay nam rieng trong thu muc python\, KHONG dung
echo  toi Python dang co san tren may.
echo.
pause

mkdir "%PYDIR%" 2>nul
set "TMPZ=%TEMP%\lotech-py.zip"

echo.
echo  [1/4] Tai Python %PYVER% ...
powershell -NoProfile -Command ^
  "$ErrorActionPreference='Stop'; [Net.ServicePointManager]::SecurityProtocol=[Net.SecurityProtocolType]::Tls12; Invoke-WebRequest 'https://www.python.org/ftp/python/%PYVER%/python-%PYVER%-embed-amd64.zip' -OutFile '%TMPZ%'" || goto :loi_mang
powershell -NoProfile -Command "Expand-Archive -Force '%TMPZ%' '%PYDIR%'" || goto :loi

echo  [2/4] Mo khoa site-packages ...
powershell -NoProfile -Command ^
  "$f=Get-ChildItem '%PYDIR%\python*._pth' | Select-Object -First 1; $t=Get-Content $f.FullName; $t=$t -replace '^#\s*import site','import site'; if($t -notcontains 'Lib\site-packages'){$t+='Lib\site-packages'}; Set-Content $f.FullName $t" || goto :loi

echo  [3/4] Cai pip va thu vien theo requirements.txt ...
powershell -NoProfile -Command ^
  "[Net.ServicePointManager]::SecurityProtocol=[Net.SecurityProtocolType]::Tls12; Invoke-WebRequest 'https://bootstrap.pypa.io/get-pip.py' -OutFile '%TEMP%\get-pip.py'" || goto :loi_mang
"%PYDIR%\python.exe" "%TEMP%\get-pip.py" --no-warn-script-location -q || goto :loi
"%PYDIR%\python.exe" -m pip install --no-warn-script-location -q -r "%~dp0requirements.txt" || goto :loi

echo  [4/4] Lay tkinter tu Python dang cai tren may (neu co) ...
rem Ban Python "embeddable" chinh thuc KHONG kem tkinter. Cach chac an nhat la
rem chep nguyen bo tcl/tkinter tu MOT ban Python day du dang chay tot tren may
rem nay, thay vi tai mot goi ngoai chua kiem chung duoc cau truc ben trong.
where python >nul 2>nul
if errorlevel 1 goto :khong_co_python_he_thong

for /f "delims=" %%P in ('where python 2^>nul') do (
  if not defined SYS_PY set "SYS_PY=%%P"
)
for %%D in ("%SYS_PY%") do set "SYS_DIR=%%~dpD"

if not exist "%SYS_DIR%tcl" goto :thieu_tk
if not exist "%SYS_DIR%Lib\tkinter" goto :thieu_tk

xcopy /e /i /y /q "%SYS_DIR%tcl" "%PYDIR%\tcl" >nul
xcopy /e /i /y /q "%SYS_DIR%Lib\tkinter" "%PYDIR%\Lib\tkinter" >nul
copy /y "%SYS_DIR%DLLs\_tkinter.pyd" "%PYDIR%\" >nul 2>nul
copy /y "%SYS_DIR%DLLs\tcl86t.dll" "%PYDIR%\" >nul 2>nul
copy /y "%SYS_DIR%DLLs\tk86t.dll" "%PYDIR%\" >nul 2>nul
copy /y "%SYS_DIR%tcl86t.dll" "%PYDIR%\" >nul 2>nul
copy /y "%SYS_DIR%tk86t.dll" "%PYDIR%\" >nul 2>nul

"%PYDIR%\python.exe" -c "import tkinter" >nul 2>nul
if errorlevel 1 goto :thieu_tk

:xong
echo python=%PYVER%> "%MARK%"
echo setup_date=%DATE% %TIME%>> "%MARK%"
echo.
echo  ====================================================
echo   XONG. Tu gio bam dup PHAN-MEM.bat la chay.
echo   Khong can cai Python, khong can mang.
echo  ====================================================
del "%TMPZ%" "%TEMP%\get-pip.py" 2>nul
pause
exit /b

:khong_co_python_he_thong
echo.
echo  [!] Khong tim thay Python nao dang cai tren may de lay tkinter.
echo      Phan mem van dung duoc: cac lenh chay ngam (autopost.py, kiemthu.py)
echo      dung Python rieng nay binh thuong, khong can tkinter.
echo      Rieng giao dien do hoa (PHAN-MEM.bat) se can Python cai tren may:
echo      vao python.org tai ve, khi cai TICH san muc "tcl/tk and IDLE".
echo python=%PYVER% (khong co tkinter)> "%MARK%"
echo setup_date=%DATE% %TIME%>> "%MARK%"
pause
exit /b

:thieu_tk
echo.
echo  [!] Tim thay Python he thong nhung khong lay duoc tkinter day du.
echo      Phan mem se tu dung Python cai san tren may cho giao dien.
echo      Cac lenh chay ngam van dung Python rieng nay binh thuong.
echo python=%PYVER% (khong co tkinter)> "%MARK%"
echo setup_date=%DATE% %TIME%>> "%MARK%"
pause
exit /b

:loi_mang
echo.
echo  [X] Khong tai duoc. Kiem tra mang, hoac cong ty chan python.org.
echo      Van chay duoc bang Python cai san tren may: bam PHAN-MEM.bat
pause
exit /b

:loi
echo.
echo  [X] Cai dat that bai o buoc tren. Xoa thu muc python\ roi thu lai.
echo      Van chay duoc bang Python cai san tren may: bam PHAN-MEM.bat
pause
exit /b
