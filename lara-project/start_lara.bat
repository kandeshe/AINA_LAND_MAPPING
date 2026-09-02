@echo off
title LARA - Agricultural Intelligence and Analysis

REM Get the folder where this BAT file is located
cd /d "%~dp0"

echo ==========================================
echo                 LARA
echo   Agricultural Intelligence and Analysis
echo ==========================================
echo.
echo Project Location:
echo %CD%
echo.
echo Starting LARA...
echo.

if not exist "%~dp0ui.py" (
    echo ERROR: ui.py was not found.
    echo The LARA project structure is incomplete.
    echo.
    pause
    exit /b 1
)

python "%~dp0ui.py"

if errorlevel 1 (
    echo.
    echo ==========================================
    echo LARA stopped because of an error.
    echo ==========================================
    echo.
    pause
)