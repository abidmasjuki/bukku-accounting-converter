@echo off
title Bukku Statement Converter CLI / Drag-and-Drop
echo ======================================================================
echo    Bukku Accounting Statement Converter
echo ======================================================================
echo.

if "%~1"=="" (
    echo [No file dragged onto this script]
    echo.
    echo Options:
    echo 1. Drag and drop any bank statement CSV file directly onto this icon.
    echo 2. Launching visual GUI now...
    echo.
    python "%~dp0gui.py"
    exit /b
) else (
    echo Processing file: %~1
    echo.
    python "%~dp0cli.py" -i "%~1"
    echo.
    echo ======================================================================
    echo Conversion complete!
    echo ======================================================================
    pause
)
