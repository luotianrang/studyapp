@echo off
chcp 65001 >nul 2>&1

title StudyApp

echo ============================================
echo   StudyApp - Starting...
echo ============================================
echo.

cd /d "%~dp0"
set "BASE_DIR=%~dp0"

rem --- Find python ---
where python >nul 2>&1
if not errorlevel 1 (
    set "PYTHON=python"
    goto install
)

rem --- Try bundled python ---
set "BUNDLED=%BASE_DIR%..\..\..\..\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"
if exist "%BUNDLED%" (
    set "PYTHON=%BUNDLED%"
    echo [INFO] Using bundled Python
    goto install
)

echo [ERROR] Python not found. Install Python 3.10+
echo https://www.python.org/downloads/
pause
exit /b 1

:install
echo Python: %PYTHON%
echo.
echo [1/2] Checking dependencies...
"%PYTHON%" -m pip install -q fastapi uvicorn sqlalchemy PyMuPDF openai python-multipart python-jose[cryptography] bcrypt 2>nul
if errorlevel 1 (
    echo [WARNING] Some deps may have failed, continuing...
)

echo [2/2] Starting server...
echo.
echo ============================================
echo   Server starting at http://localhost:8899
echo   Press Ctrl+C to stop
echo ============================================
echo.

"%PYTHON%" -m uvicorn backend.main:app --host 0.0.0.0 --port 8899

pause
