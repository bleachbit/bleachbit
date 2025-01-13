echo Installing the build environment into the current working directory.
powershell.exe -ExecutionPolicy ByPass -File "%~dp0\msys-install.ps1"
if %errorlevel% neq 0 (
    echo msys-install.ps1 failed.
    exit /b %errorlevel%
)

powershell.exe -ExecutionPolicy ByPass -File "%~dp0\python-gtk3-install.ps1"
