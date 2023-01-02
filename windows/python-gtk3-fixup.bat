:: Fixup vcpkg python and gtk3 build for PyGObject
@echo off
if [%1] == [] goto usage

set gtk3dir=%1
set scriptdir=%~dp0

:: girepostiry
mkdir "%PYTHON_HOME%\lib\girepository-1.0"
xcopy /e /d "%gtk3dir%\lib\girepository-1.0" "%PYTHON_HOME%\lib\girepository-1.0"
if errorlevel 1 exit 1

:: gtk3 dependencies
for /f "tokens=*" %%i in (%scriptdir%\python-gtk3-deps.lst) DO (
    xcopy /e /d "%gtk3dir%\%%i" "%PYTHON_HOME%"
    if errorlevel 1 exit 1
)

set PATH=%PATH%;%PYTHON_HOME%
mkdir %PYTHON_HOME%\lib\gdk-pixbuf-2.0\2.10.0
set GDK_PIXBUF_MODULE_FILE=%PYTHON_HOME%\lib\gdk-pixbuf-2.0\2.10.0\loaders.cache
%gtk3dir%\tools\gdk-pixbuf\gdk-pixbuf-query-loaders --update-cache %PYTHON_HOME%\pixbufloader-svg.dll

:: done
exit 0

:usage
echo Usage: %~n0 gtk3-root