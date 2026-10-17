@echo off
setlocal

echo ===================================================
echo Starting CatLog Development Runner
echo ===================================================

if not exist ".venv\Scripts\python.exe" (
    echo [INFO] Virtual environment not found. Setting up .venv...
    where uv >nul 2>nul
    if %ERRORLEVEL% EQU 0 (
        uv venv --python 3.11 .venv
        uv pip install -r requirements.txt
    ) else (
        python -m venv .venv
        .venv\Scripts\pip.exe install -r requirements.txt
    )
)

echo [INFO] Running CatLog Desktop Shell...
.venv\Scripts\python.exe main.py %*

endlocal
