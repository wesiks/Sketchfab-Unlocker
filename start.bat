@echo off
setlocal
cd /d "%~dp0"
if exist "%~dp0SketchfabUnlocker.exe" (
    start "" "%~dp0SketchfabUnlocker.exe"
    exit /b 0
)
where pythonw >nul 2>&1
if %errorlevel% equ 0 (
    start "" pythonw "%~dp0gui.py"
    exit /b 0
)
where pyw >nul 2>&1
if %errorlevel% equ 0 (
    start "" pyw -3 "%~dp0gui.py"
    exit /b 0
)
where py >nul 2>&1
if %errorlevel% equ 0 (
    start "" py -3 "%~dp0gui.py"
    exit /b 0
)
where python >nul 2>&1
if %errorlevel% equ 0 (
    start "" python "%~dp0gui.py"
    exit /b 0
)
exit /b 1
