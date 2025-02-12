@echo off
rem
rem This script is expected to be run from current directory
rem The output is produced in vcpkg_installed\ subdirectory
rem

set VCPKG_ROOT=c:\vcpkg

%VCPKG_ROOT%\vcpkg --triplet=x86-windows install
if errorlevel 1 goto error
rem %VCPKG_ROOT%\vcpkg --triplet=x64-windows install
if errorlevel 1 goto error

cd vcpkg_installed
zip -X -r gtk3.24-x86-windows.zip x86-windows -x x86-windows\debug\*
rem zip -X -r gtk3.24-x86-windows-debug.zip x86-windows\debug
rem zip -X -r gtk3.24-x64-windows.zip x64-windows -x x64-windows\debug\*
rem zip -X -r gtk3.24-x64-windows-debug.zip x64-windows\debug 
cd ..

:error
