@echo off
REM ============================================================================
REM GenAI Pipeline Automation - Windows Batch Launcher
REM ============================================================================
REM
REM This script provides an easy way to run the pipeline on Windows.
REM It handles environment setup and delegates to Python orchestrator.
REM
REM Usage:
REM   pipeline.bat                    - Run full pipeline
REM   pipeline.bat stage1             - Run Stage 1 only
REM   pipeline.bat stage2             - Run Stage 2 only (Colab)
REM   pipeline.bat download           - Download results only
REM   pipeline.bat auth               - Setup authentication
REM   pipeline.bat help               - Show this help
REM
REM ============================================================================

setlocal enabledelayedexpansion

REM Get the directory where this batch file is located
set SCRIPT_DIR=%~dp0
set AUTOMATION_DIR=%SCRIPT_DIR%automation
set SCRIPTS_DIR=%AUTOMATION_DIR%\scripts

REM Colors for output (if supported)
set COLOR_RESET=[0m
set COLOR_GREEN=[92m
set COLOR_YELLOW=[93m
set COLOR_RED=[91m
set COLOR_BLUE=[94m

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo %COLOR_RED%ERROR: Python is not installed or not in PATH%COLOR_RESET%
    echo.
    echo Please install Python 3.8+ from https://www.python.org/
    echo Make sure to check "Add Python to PATH" during installation
    exit /b 1
)

echo %COLOR_BLUE%============================================================================%COLOR_RESET%
echo %COLOR_BLUE%         GenAI Pipeline Automation - Orchestrator%COLOR_RESET%
echo %COLOR_BLUE%============================================================================%COLOR_RESET%
echo.

REM Parse command line arguments
set COMMAND=%1
if "%COMMAND%"=="" (
    set COMMAND=full
)

REM Convert to lowercase for comparison
for %%A in (full stage1 stage2 download auth help) do (
    if /i "%COMMAND%"=="%%A" set COMMAND=%%A
)

REM Route to appropriate handler
if "%COMMAND%"=="help" goto show_help
if "%COMMAND%"=="auth" goto setup_auth
if "%COMMAND%"=="stage1" goto run_stage1
if "%COMMAND%"=="stage2" goto run_stage2
if "%COMMAND%"=="download" goto run_download
if "%COMMAND%"=="full" goto run_full

echo %COLOR_RED%ERROR: Unknown command '%COMMAND%'%COLOR_RESET%
echo.
goto show_help

REM ============================================================================

:show_help
echo Usage:
echo   pipeline.bat [COMMAND]
echo.
echo Commands:
echo   full                - Run complete pipeline (Stage 1 + Upload + Stage 2 + Download)
echo   stage1              - Run Stage 1 only (local analysis + upload to Drive)
echo   stage2              - Trigger Stage 2 on Colab (assumes inputs on Drive)
echo   download            - Download Stage 2 results from Drive
echo   auth                - Setup Google Drive authentication (ONE-TIME)
echo   help                - Show this message
echo.
echo Examples:
echo   pipeline.bat                   ^# Full pipeline
echo   pipeline.bat stage1            ^# Only Stage 1
echo   pipeline.bat auth              ^# Setup credentials
echo.
echo More info: See automation/README.md
exit /b 0

REM ============================================================================

:setup_auth
echo %COLOR_YELLOW%Setting up Google Drive authentication...%COLOR_RESET%
echo.
echo This requires OAuth 2.0 credentials from Google Cloud Console.
echo See instructions in: automation/scripts/auth_setup.py
echo.

python "%SCRIPTS_DIR%\auth_setup.py"

if errorlevel 1 (
    echo %COLOR_RED%Authentication setup failed%COLOR_RESET%
    exit /b 1
) else (
    echo %COLOR_GREEN%Authentication setup complete!%COLOR_RESET%
    exit /b 0
)

REM ============================================================================

:run_stage1
echo %COLOR_YELLOW%Running Stage 1 (Repository Analysis + Upload)...%COLOR_RESET%
echo.

python "%SCRIPTS_DIR%\orchestrate_pipeline.py" --stage1-only

if errorlevel 1 (
    echo %COLOR_RED%Stage 1 failed%COLOR_RESET%
    exit /b 1
) else (
    echo %COLOR_GREEN%Stage 1 completed successfully!%COLOR_RESET%
    exit /b 0
)

REM ============================================================================

:run_stage2
echo %COLOR_YELLOW%Triggering Stage 2 on Google Colab...%COLOR_RESET%
echo.

python "%SCRIPTS_DIR%\orchestrate_pipeline.py" --stage2-only

if errorlevel 1 (
    echo %COLOR_RED%Stage 2 trigger failed%COLOR_RESET%
    exit /b 1
) else (
    echo %COLOR_GREEN%Stage 2 triggered!%COLOR_RESET%
    exit /b 0
)

REM ============================================================================

:run_download
echo %COLOR_YELLOW%Downloading Stage 2 results from Google Drive...%COLOR_RESET%
echo.

python "%SCRIPTS_DIR%\orchestrate_pipeline.py" --download-only

if errorlevel 1 (
    echo %COLOR_RED%Download failed%COLOR_RESET%
    exit /b 1
) else (
    echo %COLOR_GREEN%Download completed!%COLOR_RESET%
    exit /b 0
)

REM ============================================================================

:run_full
echo %COLOR_YELLOW%Running FULL PIPELINE...%COLOR_RESET%
echo.
echo This will:
echo   1. Run Stage 1 (repository analysis) locally
echo   2. Upload outputs to Google Drive
echo   3. Trigger Stage 2 execution on Google Colab (GPU)
echo   4. Download final results
echo.
echo Estimated time: 1-2 hours
echo.

python "%SCRIPTS_DIR%\orchestrate_pipeline.py"

if errorlevel 1 (
    echo %COLOR_RED%Pipeline failed%COLOR_RESET%
    exit /b 1
) else (
    echo %COLOR_GREEN%Pipeline completed successfully!%COLOR_RESET%
    exit /b 0
)

REM ============================================================================

endlocal
