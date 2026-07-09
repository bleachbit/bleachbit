@echo off
REM Run a subset of unit tests as a normal (medium-integrity) non-admin user.
REM Complements psexec-low-integrity-tests.bat: registry and recycle-bin tests
REM need medium integrity; locked-file and service tests need non-admin token.
setlocal
cd /d "%~dp0.."
set "REPO=%CD%"
set "LOG=%REPO%\psexec_nonadmin_tests.log"
set "DESTRUCTIVE_TESTS=T"
set "PYTHONWARNINGS=error"
set "GITHUB_ACTIONS=true"
set "COVERAGE_FILE=%REPO%\.coverage.nonadmin"

if not defined PYTHON_EXE (
    if exist "%REPO%\vcpkg_installed\x86-windows\tools\python3\python.exe" (
        set "PYTHON_EXE=%REPO%\vcpkg_installed\x86-windows\tools\python3\python.exe"
    ) else (
        echo ERROR: PYTHON_EXE is not set> "%LOG%"
        exit /b 1
    )
)

(
    echo === psexec non-admin tests ===
    echo CD=%CD%
    echo USERNAME=%USERNAME%
    echo PYTHON_EXE=%PYTHON_EXE%
    echo TEMP=%TEMP%
    echo COVERAGE_FILE=%COVERAGE_FILE%
) > "%LOG%"

"%PYTHON_EXE%" -c "from win32com.shell import shell; print('IsUserAnAdmin:', shell.IsUserAnAdmin())" >> "%LOG%" 2>&1
echo.>> "%LOG%"

"%PYTHON_EXE%" -m coverage run -m unittest -v ^
    tests.TestWindows.WindowsTestCase.test_delete_registry_key ^
    tests.TestWindows.WindowsTestCase.test_delete_registry_value ^
    tests.TestWindows.WindowsTestCase.test_detect_registry_key ^
    tests.TestWindows.WindowsTestCase.test_get_recycle_bin ^
    tests.TestWindows.WindowsTestCase.test_get_recycle_bin_destructive ^
    tests.TestWindows.WindowsTestCase.test_broken_link_in_recycle_bin ^
    tests.TestWindows.WindowsTestCase.test_empty_recycle_bin ^
    tests.TestWindows.WindowsTestCase.test_empty_recycle_bin_per_drive_destructive ^
    tests.TestWindows.WindowsTestCase.test_empty_recycle_bin_all_drives_destructive ^
    tests.TestWorker.WorkerTestCase.test_Locked ^
    tests.TestWindows.WindowsTestCase.test_run_net_service_command_not_admin ^
    tests.TestWindows.WindowsTestCase.test_delete_locked_file ^
    tests.TestWindows.WindowsTestCase.test_file_wipe >> "%LOG%" 2>&1
exit /b %ERRORLEVEL%
