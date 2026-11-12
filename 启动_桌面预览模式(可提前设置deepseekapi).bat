@echo off
cd /d "%~dp0"
if exist "VRC-TransKey.exe" (
    "VRC-TransKey.exe" --desktop
) else (
    ".venv\Scripts\python.exe" main.py --desktop
)
