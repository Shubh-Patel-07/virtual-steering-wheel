@echo off
setlocal
cd /d "%~dp0"

rem Keep MediaPipe/Matplotlib cache inside the project folder.
set "MPLCONFIGDIR=%~dp0.mplconfig"
if not exist "%MPLCONFIGDIR%" mkdir "%MPLCONFIGDIR%"

rem Prefer the Python launcher, then the normal PATH, then the standard
rem per-user install location used during setup.
where py >nul 2>nul
if not errorlevel 1 (
    py -3 steering_wheel.py
    goto :end
)

where python >nul 2>nul
if not errorlevel 1 (
    python steering_wheel.py
    goto :end
)

if exist "%LocalAppData%\Programs\Python\Python312\python.exe" (
    "%LocalAppData%\Programs\Python\Python312\python.exe" steering_wheel.py
    goto :end
)

echo.
echo Python was not found. Please reopen this project after installing Python.
pause
exit /b 1

:end
if errorlevel 1 (
    echo.
    echo The app stopped with an error.
    pause
)
endlocal
