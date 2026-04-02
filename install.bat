@echo off
title Dadarzz Agent Installer
cd /d "%~dp0"

set APP_NAME=Dadarzz Agent
set VENV_DIR=%~dp0.venv
set LAUNCH_SCRIPT=%~dp0launch.bat

echo.
echo ╔══════════════════════════════════════════════╗
echo ║    🧠 Installing %APP_NAME%...              ║
echo ╚══════════════════════════════════════════════╝
echo.

REM ── Step 1: Check for Python 3 ───────────────────────
where python >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    where python3 >nul 2>nul
    if %ERRORLEVEL% NEQ 0 (
        echo ❌ Python 3 is not installed.
        echo.
        echo Please install it from:
        echo   https://www.python.org/downloads/
        echo.
        echo IMPORTANT: Check "Add Python to PATH" during installation!
        echo.
        pause
        exit /b 1
    )
    set PYTHON=python3
) else (
    set PYTHON=python
)

for /f "tokens=*" %%i in ('%PYTHON% --version 2^>^&1') do set PYTHON_VER=%%i
echo ✅ Found %PYTHON_VER%

REM ── Step 2: Create virtual environment ───────────────
if not exist "%VENV_DIR%" (
    echo 📦 Setting up environment...
    %PYTHON% -m venv "%VENV_DIR%"
) else (
    echo ✅ Environment already exists
)

REM ── Step 3: Install dependencies ─────────────────────
echo 📥 Installing dependencies (this may take a minute)...
"%VENV_DIR%\Scripts\pip.exe" install --quiet --upgrade pip
"%VENV_DIR%\Scripts\pip.exe" install --quiet -r "%~dp0requirements.txt"
echo ✅ Dependencies installed

REM ── Step 4: Create desktop shortcut ──────────────────
echo 📎 Creating desktop shortcut...
set SHORTCUT_VBS=%TEMP%\create_shortcut.vbs
echo Set oWS = WScript.CreateObject("WScript.Shell") > "%SHORTCUT_VBS%"
echo sLinkFile = oWS.SpecialFolders("Desktop") ^& "\%APP_NAME%.lnk" >> "%SHORTCUT_VBS%"
echo Set oLink = oWS.CreateShortcut(sLinkFile) >> "%SHORTCUT_VBS%"
echo oLink.TargetPath = "%LAUNCH_SCRIPT%" >> "%SHORTCUT_VBS%"
echo oLink.WorkingDirectory = "%~dp0" >> "%SHORTCUT_VBS%"
echo oLink.Description = "Launch Dadarzz Agent" >> "%SHORTCUT_VBS%"
echo oLink.Save >> "%SHORTCUT_VBS%"
cscript /nologo "%SHORTCUT_VBS%"
del "%SHORTCUT_VBS%"
echo ✅ Desktop shortcut created

echo.
echo ╔══════════════════════════════════════════════╗
echo ║    ✅ Installation complete!                 ║
echo ╠══════════════════════════════════════════════╣
echo ║                                              ║
echo ║  You can now:                                ║
echo ║    • Double-click '%APP_NAME%' on Desktop    ║
echo ║    • Or double-click launch.bat              ║
echo ║                                              ║
echo ╚══════════════════════════════════════════════╝
echo.

set /p LAUNCH_NOW=🚀 Launch now? (Y/n): 
if /i "%LAUNCH_NOW%"=="" set LAUNCH_NOW=Y
if /i "%LAUNCH_NOW%"=="Y" call "%LAUNCH_SCRIPT%"
if /i "%LAUNCH_NOW%"=="y" call "%LAUNCH_SCRIPT%"
pause
