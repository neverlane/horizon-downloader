@echo off
setlocal
cd /d "%~dp0"

where py >nul 2>nul
if %errorlevel%==0 (
    py -3 download.py %*
) else (
    python download.py %*
)
set "EXIT_CODE=%errorlevel%"

if "%~1"=="" pause
exit /b %EXIT_CODE%
