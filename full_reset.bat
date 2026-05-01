@echo off
title Full Reset — Removing All Agents...
echo.
echo ============================================
echo   FULL RESET — Removing Everything
echo ============================================
echo.

:: STEP 1 — Kill running agent process
echo [1/7] Stopping running agent...
taskkill /F /IM "WindowsSystemService.exe" >nul 2>&1
echo        Done.

:: STEP 2 — Remove registry startup entry
echo [2/7] Removing registry startup...
reg delete "HKCU\Software\Microsoft\Windows\CurrentVersion\Run" /v "WinSvcHelper" /f >nul 2>&1
reg delete "HKCU\Software\Microsoft\Windows\CurrentVersion\Run" /v "WindowsSvcHelper" /f >nul 2>&1
echo        Done.

:: STEP 3 — Remove VBS startup file
echo [3/7] Removing startup folder entry...
attrib -h "%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup\WinSvcHelper.vbs" >nul 2>&1
del /q "%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup\WinSvcHelper.vbs" >nul 2>&1
echo        Done.

:: STEP 4 — Remove installed EXE folder
echo [4/7] Removing installed EXE...
attrib -h -s "%LOCALAPPDATA%\Microsoft\WindowsApps\SvcHelper" >nul 2>&1
rmdir /s /q "%LOCALAPPDATA%\Microsoft\WindowsApps\SvcHelper" >nul 2>&1
echo        Done.

:: STEP 5 — Remove hidden photo queue
echo [5/7] Removing hidden photo queue...
attrib -h -s "%TEMP%\.msvcr_cache" >nul 2>&1
rmdir /s /q "%TEMP%\.msvcr_cache" >nul 2>&1
echo        Done.

:: STEP 6 — Remove lock file and logs
echo [6/7] Removing logs and lock files...
del /q "%TEMP%\MyBackgroundAgent.lock" >nul 2>&1
rmdir /s /q "%LOCALAPPDATA%\MyBackgroundAgent" >nul 2>&1
echo        Done.

:: STEP 7 — Uninstall Python packages
echo [7/7] Uninstalling Python packages...
pip uninstall opencv-python boto3 botocore s3transfer pyinstaller -y >nul 2>&1
echo        Done.

echo.
echo ============================================
echo   RESET COMPLETE!
echo   Everything removed. Ready for fresh install.
echo   Now run: build.bat then deploy.bat
echo ============================================
echo.
pause
