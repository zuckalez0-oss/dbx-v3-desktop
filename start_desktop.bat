@echo off
setlocal
cd /d "%~dp0"

if exist ".venv_desktop\Scripts\python.exe" (
    ".venv_desktop\Scripts\python.exe" -m desktop_app
) else if exist "venvdb\Scripts\python.exe" (
    "venvdb\Scripts\python.exe" -m desktop_app
) else (
    py -m desktop_app
)

pause