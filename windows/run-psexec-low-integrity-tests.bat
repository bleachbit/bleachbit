@echo off
REM AppVeyor wrapper: run low-integrity test subset via PsExec and print the log.
REM PsExec -l = Low Mandatory Integrity (stricter than a normal user). See
REM psexec-low-integrity-tests.bat for the curated unittest list.
setlocal
cd /d "%~dp0.."
set "REPO=%CD%"
set "LOG=%USERPROFILE%\AppData\LocalLow\psexec_tests.log"
if exist "%LOG%" del /q "%LOG%"

psexec.exe -accepteula -l -i -w "%REPO%" cmd /c "%REPO%\windows\psexec-low-integrity-tests.bat"
set EXITCODE=%ERRORLEVEL%

echo.
echo === psexec exit code: %EXITCODE% ===
if exist "%LOG%" (
    echo === psexec test log ===
    type "%LOG%"
) else (
    echo Log not found: %LOG%
)

exit /b %EXITCODE%
