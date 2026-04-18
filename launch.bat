@echo off
setlocal

set SCRIPT_DRIVE=%~d0
set CURRENT_DRIVE=%CD:~0,2%
if /i not "%SCRIPT_DRIVE%"=="%CURRENT_DRIVE%" %SCRIPT_DRIVE%
cd "%~dp0"
set ROOT=%~dp0
set VENV_DIR=%ROOT%venv

if exist "%ROOT%.git\" (
    echo Pulling latest updates...
    git pull
)

if not exist "%VENV_DIR%\Scripts\activate.bat" (
    echo Creating virtual environment...
    python -m venv "%VENV_DIR%"
    if errorlevel 1 (
        echo Failed to create virtual environment. Is Python installed?
        pause
        exit /b 1
    )
)

echo Installing/updating dependencies...
"%VENV_DIR%\Scripts\pip.exe" install -r "%ROOT%requirements.txt" --quiet
if errorlevel 1 (
    echo Failed to install dependencies.
    pause
    exit /b 1
)

"%VENV_DIR%\Scripts\python.exe" "%ROOT%movinator.py"
