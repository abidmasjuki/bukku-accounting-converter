@echo off
title Bukku Statement Converter CLI / Drag-and-Drop
echo ======================================================================
echo    Bukku Accounting Statement Converter
echo ======================================================================
echo.

if "%~1"=="" (
    echo No file dragged. Running automatic conversion on default accounting folder...
    echo.
    python "%~dp0cli.py"
) else (
    echo Processing dropped file: %~1
    echo.
    python "%~dp0cli.py" -i "%~1"
)

echo.
echo ======================================================================
echo Conversion complete!
echo ======================================================================
pause
