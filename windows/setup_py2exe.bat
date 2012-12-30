@echo off
REM BleachBit
REM Copyright (C) 2009 Andrew Ziem
REM http://bleachbit.sourceforge.net
REM
REM This program is free software: you can redistribute it and/or modify
REM it under the terms of the GNU General Public License as published by
REM the Free Software Foundation, either version 3 of the License, or
REM (at your option) any later version.
REM
REM This program is distributed in the hope that it will be useful,
REM but WITHOUT ANY WARRANTY; without even the implied warranty of
REM MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
REM GNU General Public License for more details.
REM
REM You should have received a copy of the GNU General Public License
REM along with this program.  If not, see <http://www.gnu.org/licenses/>.


set GTK_DIR=c:\gtk
set NSIS_EXE="c:\program files\nsis\makensis.exe"
if not exist c:\python27 goto py25
set PYTHON_DIR=c:\python27
set PYTHON_VER=27
goto after_py
:py25
set PYTHON_DIR=c:\python25
set PYTHON_VER=25
:after_py
set SZ_EXE="C:\Program Files\7-Zip\7z.exe"
set UPX_EXE=upx
set UPX_OPTS=--best --crp-ms=999999 --nrv2e

echo Checking for translations
set CANARY=locale
if not exist %CANARY% goto error

echo Checking for GTK
set CANARY=%GTK_DIR%
if not exist %CANARY% goto error

echo Deleting directories build and dist
del /q /s build > nul
del /q /s dist > nul

echo Pre-compressing executables
if not "%1" == "fast" for /r %PYTHON_DIR% %%e in (*.pyd) do %UPX_EXE% %UPX_OPTS% "%%e"
if not "%1" == "fast" for /r %GTK_DIR% %%e in (*.exe,*.dll) do %UPX_EXE% %UPX_OPTS% "%%e"
REM do not pre-compress python25.dll because py2exe modifies it
if not "%1" == "fast" %UPX_EXE% %UPX_OPTS% %windir%\system32\pywintypes%PYTHON_VER%.dll

echo Running py2exe
copy bleachbit.py bleachbit_console.py
%PYTHON_DIR%\python.exe -OO setup.py py2exe
del bleachbit_console.py
set CANARY=dist\bleachbit.exe
if not exist %CANARY% goto error

echo Copying GTK files and icon
copy %GTK_DIR%\bin\intl.dll dist
mkdir dist\etc
xcopy %GTK_DIR%\etc dist\etc /i /s /q
mkdir dist\lib
xcopy %GTK_DIR%\lib dist\lib /i /s /q
mkdir dist\share
copy bleachbit.png dist\share\
xcopy %GTK_DIR%\share dist\share /i /s /q

echo Compressing executables
if not "%1" == "fast" for /r dist %%e in (*.pyd,*.dll,*.exe) do %UPX_EXE% "%%e" %UPX_OPTS%

echo Purging unnecessary GTK+ files
%PYTHON_DIR%\python.exe setup.py clean-dist

echo Copying BleachBit localizations
xcopy locale dist\share\locale /i /s /q
set CANARY=dist\share\locale\es\LC_MESSAGES\bleachbit.mo
if not exist %CANARY% goto error

echo Copying BleachBit cleaners
xcopy cleaners\*xml dist\share\cleaners\ /i /s /q

echo Checking for CleanerML
set CANARY=dist\share\cleaners\internet_explorer.xml
if not exist %CANARY% goto error

echo Checking for Linux-only cleaners
if exist dist\share\cleaners\wine.xml echo "grep -l os=.linux. dist/share/cleaners/*xml | xargs rm -f"
if exist dist\share\cleaners\wine.xml pause

echo Recompressing library.zip with 7-Zip
if "%1" == "fast" goto nsis
if not exist %SZ_EXE% echo %SZ_EXE% does not exist
if not exist %SZ_EXE% goto nsis

cd dist
mkdir library
cd library
%SZ_EXE% x ..\library.zip
echo "Size before 7zip recompression
dir ..\library.zip
del ..\library.zip
%SZ_EXE% a -tzip -mx=9 -mfb=255 ..\library.zip
echo "Size after 7zip recompression
dir ..\library.zip
cd ..\..
rd /s /q dist\library
set CANARY=dist\library.zip
if not exist %CANARY% goto error

echo Building portable
rd /s /q BleachBit-portable
xcopy /e /i dist BleachBit-Portable
echo [Portable] > BleachBit-Portable\BleachBit.ini
%SZ_EXE% a -mx=9 -md=32m BleachBit-0.0.0-portable.zip BleachBit-portable

:nsis
echo Building installer
if     "%1" == "fast" %NSIS_EXE% /X"SetCompressor /FINAL zlib" windows\bleachbit.nsi
if not "%1" == "fast" %NSIS_EXE% windows\bleachbit.nsi

echo Success!
goto exit

:error
echo %CANARY% not found
echo Process aborted because of error!

:exit


