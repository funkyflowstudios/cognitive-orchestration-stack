@echo off
:: Chimera – Cognitive Orchestration Stack launcher
:: Usage: double-click or run "chimera.bat -q \"Your question\""

setlocal
cd /d %~dp0

REM Prefer the project's virtual-env Python if it exists
if exist "venv\Scripts\python.exe" (
    "venv\Scripts\python.exe" -m src.main %*
) else (
    python -m src.main %*
)
endlocal
