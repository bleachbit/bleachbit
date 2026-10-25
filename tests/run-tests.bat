@echo off
REM SPDX-License-Identifier: GPL-3.0-or-later
REM Copyright (c) 2008-2026 Andrew Ziem.
REM Alternative to `make tests-pytest` when make is not installed.
setlocal

set "PYTHON=python"
%PYTHON% --version >nul 2>&1 && goto python_found
set "PYTHON=py -3"
%PYTHON% --version >nul 2>&1 && goto python_found
set "PYTHON=python3"
%PYTHON% --version >nul 2>&1 && goto python_found
echo ERROR: No working Python found. Tried: python, py -3, python3. >&2
exit /b 1
:python_found

pushd "%~dp0.." || exit /b 1
set "PYTHONWARNINGS=error"
set "PYTHONPATH=."

call %PYTHON% -m pytest -n logical --dist=loadgroup -m "not no_xdist" tests
set "EXITCODE=%ERRORLEVEL%"
if not "%EXITCODE%"=="0" goto done

call %PYTHON% -m pytest -m no_xdist tests
set "EXITCODE=%ERRORLEVEL%"

:done
popd
exit /b %EXITCODE%
