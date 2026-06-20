@echo off
REM AppVeyor wrapper: create a non-admin user, run tests via PsExec, print log.
setlocal
cd /d "%~dp0.."
set "REPO=%CD%"
set "BB_TEST_USER=BleachBitTest"
set "BB_TEST_PASS=Not-Real-Password_CiTest_9Xv4_73Qa"
set "LOG=%REPO%\psexec_nonadmin_tests.log"
if exist "%LOG%" del /q "%LOG%"
if exist "%REPO%\.coverage.nonadmin" del /q "%REPO%\.coverage.nonadmin"

net user %BB_TEST_USER% /delete /y >nul 2>&1
net user %BB_TEST_USER% %BB_TEST_PASS% /add /y
if errorlevel 1 (
    echo ERROR: Failed to create test user %BB_TEST_USER%
    exit /b 1
)

icacls "%REPO%" /grant "%BB_TEST_USER%:(OI)(CI)M" /T >nul
if errorlevel 1 (
    echo ERROR: Failed to grant write access on %REPO%
    exit /b 1
)

if not defined PYTHON_EXE (
    echo ERROR: PYTHON_EXE is not set in AppVeyor environment
    exit /b 1
)

REM PsExec -u does not inherit the build agent's environment. Write a small
REM launcher to avoid fragile nested quoting in cmd /c.
set "LAUNCH=%REPO%\windows\psexec-nonadmin-launch.bat"
(
    echo @echo off
    echo set "PYTHON_EXE=%PYTHON_EXE%"
    echo set "PYTHON_HOME=%PYTHON_HOME%"
    echo set "DESTRUCTIVE_TESTS=T"
    echo set "PYTHONWARNINGS=error"
    echo set "APPVEYOR=True"
    echo call "%REPO%\windows\psexec-nonadmin-tests.bat"
) > "%LAUNCH%"

psexec.exe -accepteula -i -u %BB_TEST_USER% -p %BB_TEST_PASS% -w "%REPO%" cmd /c "%LAUNCH%"
set EXITCODE=%ERRORLEVEL%

net user %BB_TEST_USER% /delete /y >nul 2>&1

echo.
echo === psexec non-admin exit code: %EXITCODE% ===
if exist "%LOG%" (
    echo === psexec non-admin test log ===
    type "%LOG%"
) else (
    echo Log not found: %LOG%
    if exist "%LAUNCH%" (
        echo Launcher still present - PsExec may not have started the inner script.
        type "%LAUNCH%"
    )
)

if exist "%LAUNCH%" del /q "%LAUNCH%"

exit /b %EXITCODE%
