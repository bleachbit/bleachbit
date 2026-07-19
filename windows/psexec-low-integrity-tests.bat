@echo off
REM Run a subset of unit tests under PsExec -l (Low Mandatory Integrity).
REM Low Integrity strips admin and sandboxes like IE Protected Mode (LocalLow
REM temp, no HKCU writes, no recycle bin). Exclude those tests here.
setlocal
set "LOW_DIR=%USERPROFILE%\AppData\LocalLow"
set "LOG=%LOW_DIR%\psexec_tests.log"
set "TEMP=%LOW_DIR%"
set "TMP=%LOW_DIR%"
set "DESTRUCTIVE_TESTS=T"
set "PYTHONWARNINGS=error"
set "GITHUB_ACTIONS=true"
set "COVERAGE_FILE=%LOW_DIR%\.coverage.psexec"
set "BLEACHBIT_TEST_OPTIONS_DIR=%LOW_DIR%\BleachBit"

(
    echo === psexec low integrity tests ===
    echo CD=%CD%
    echo PYTHON_EXE=%PYTHON_EXE%
    echo TEMP=%TEMP%
    echo COVERAGE_FILE=%COVERAGE_FILE%
) > "%LOG%"

if not defined PYTHON_EXE (
    echo ERROR: PYTHON_EXE is not set>> "%LOG%"
    exit /b 1
)

cd /d "%~dp0.."
if errorlevel 1 (
    echo ERROR: Failed to cd to repo root>> "%LOG%"
    exit /b 1
)

echo Repo root: %CD%>> "%LOG%"
echo.>> "%LOG%"

"%PYTHON_EXE%" -m coverage run -m unittest -v ^
    tests.TestWorker.WorkerTestCase.test_Locked ^
    tests.TestWorker.WorkerTestCase.test_AccessDenied ^
    tests.TestWorker.WorkerTestCase.test_DoesNotExist ^
    tests.TestWorker.WorkerTestCase.test_RuntimeError ^
    tests.TestWorker.WorkerTestCase.test_Truncate ^
    tests.TestWindows.WindowsTestCase.test_run_net_service_command_not_admin ^
    tests.TestWindows.WindowsTestCase.test_delete_updates ^
    tests.TestWindows.WindowsTestCase.test_delete_parent_lock_needed ^
    tests.TestWindows.WindowsTestCase.test_delete_with_parent_lock_reuses_handle ^
    tests.TestWindows.WindowsTestCase.test_delete_with_parent_lock_closes_handle_on_delete_error ^
    tests.TestWindows.WindowsTestCase.test_delete_locked_file >> "%LOG%" 2>&1
exit /b %ERRORLEVEL%
