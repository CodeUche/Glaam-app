@echo off
setlocal EnableDelayedExpansion

echo.
echo ============================================================
echo   GlamConnect -- Build Standalone .exe
echo ============================================================
echo.

:: ── Locate Python ──────────────────────────────────────────────────────────
where py >nul 2>&1
if %errorlevel%==0 (
    set PYTHON=py
) else (
    where python >nul 2>&1
    if %errorlevel%==0 (
        set PYTHON=python
    ) else (
        echo [ERROR] Python not found. Install Python 3.10+ from https://python.org
        pause
        exit /b 1
    )
)

for /f "tokens=*" %%v in ('%PYTHON% --version 2^>^&1') do echo [OK] Found %%v

:: ── Move into the backend directory ────────────────────────────────────────
cd /d "%~dp0backend"
echo [INFO] Working directory: %cd%
echo.

:: ── Install build dependencies ──────────────────────────────────────────────
echo [1/4] Installing PyInstaller...
%PYTHON% -m pip install --quiet --upgrade pyinstaller
if %errorlevel% neq 0 (
    echo [ERROR] Failed to install PyInstaller.
    pause & exit /b 1
)
echo [OK] PyInstaller ready.
echo.

:: ── Install standalone requirements (no PostgreSQL / Redis / Gunicorn) ───────
echo [2/4] Installing standalone requirements...
:: Uses requirements_standalone.txt which omits psycopg2, redis, celery,
:: daphne, gunicorn, boto3 — none of these are needed for the SQLite .exe.
:: --only-binary :all: prevents pip from trying to compile C extensions from
:: source (avoids the pg_config / PostgreSQL header errors).
%PYTHON% -m pip install --quiet --only-binary :all: -r requirements_standalone.txt
if %errorlevel% neq 0 (
    echo [ERROR] pip install failed.
    echo         Check that you have internet access and try again.
    pause & exit /b 1
)
echo [OK] Requirements installed.
echo.

:: ── Build the .exe ──────────────────────────────────────────────────────────
echo [3/4] Building GlamConnect.exe (this takes 2-5 minutes)...
echo       Do not close this window.
echo.
:: Tell PyInstaller's Django hook to analyse settings_standalone (not the
:: production settings that require PostgreSQL / Redis / Celery broker).
set DJANGO_SETTINGS_MODULE=config.settings_standalone
%PYTHON% -m PyInstaller standalone.spec --clean --noconfirm
if %errorlevel% neq 0 (
    echo.
    echo [ERROR] PyInstaller build failed. See output above for details.
    pause & exit /b 1
)

:: ── Verify output ────────────────────────────────────────────────────────────
echo.
if exist "dist\GlamConnect.exe" (
    echo [4/4] Build complete!
    echo.
    echo ============================================================
    echo   Output: backend\dist\GlamConnect.exe
    echo ============================================================
    echo.
    echo   Share or copy GlamConnect.exe anywhere on a Windows PC.
    echo   Double-click to start. A browser will open automatically.
    echo.
    echo   First run creates a local SQLite database next to the .exe.
    echo   Demo accounts:
    echo     Admin  : admin@glamconnect.com   / Admin@1234!
    echo     Artist : artist@glamconnect.com  / Artist@1234!
    echo     Client : client@glamconnect.com  / Client@1234!
    echo.
    echo   Ctrl+C in the server window to stop.
    echo ============================================================
    echo.

    :: Ask if they want to run it now
    set /p RUN_NOW="Run GlamConnect.exe now? (Y/N): "
    if /i "!RUN_NOW!"=="Y" (
        start "" "dist\GlamConnect.exe"
    )
) else (
    echo [ERROR] dist\GlamConnect.exe was not created. Check the log above.
)

pause
