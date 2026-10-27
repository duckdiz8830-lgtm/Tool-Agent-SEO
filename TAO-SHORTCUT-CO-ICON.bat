@echo off
chcp 65001 >nul
title LOTECH AUTOPOST - Tao shortcut co icon
cd /d "%~dp0"

echo  ====================================================
echo   TAO SHORTCUT CO ICON RIENG cho PHAN-MEM.bat
echo  ====================================================
echo.
echo  Windows KHONG cho gan icon truc tiep vao file .bat -
echo  phai di qua 1 shortcut (.lnk). File nay tao 1 shortcut
echo  tren Desktop, tro toi PHAN-MEM.bat, dung icon rieng
echo  trong thu muc icon\lotech-autopost.ico.
echo.
echo  Chi can chay file nay 1 LAN. Lan sau mo phan mem bang
echo  shortcut moi tren Desktop, khong can bam PHAN-MEM.bat nua.
echo.
pause

powershell -NoProfile -Command ^
  "$ws = New-Object -ComObject WScript.Shell; $sc = $ws.CreateShortcut([System.IO.Path]::Combine([Environment]::GetFolderPath('Desktop'), 'Lotech Autopost.lnk')); $sc.TargetPath = '%~dp0PHAN-MEM.bat'; $sc.WorkingDirectory = '%~dp0'; $sc.IconLocation = '%~dp0icon\lotech-autopost.ico'; $sc.Description = 'Lotech Autopost - MASTER 4-Profile to AI to WordPress'; $sc.Save()"

if errorlevel 1 (
  echo.
  echo  [X] Tao shortcut khong thanh cong. Co the may chan PowerShell.
  echo      Cach thu cong: chuot phai PHAN-MEM.bat ^> Send to ^>
  echo      Desktop ^(create shortcut^), roi chuot phai shortcut vua
  echo      tao ^> Properties ^> Change Icon ^> chon file
  echo      icon\lotech-autopost.ico trong thu muc nay.
  echo.
  pause
  exit /b
)

echo.
echo  ====================================================
echo   XONG. Xem Desktop, co shortcut "Lotech Autopost" moi.
echo  ====================================================
pause
