@echo off
REM BleachBit
REM Copyright (C) 2008-2015 Andrew Ziem
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
set UPX_EXE=upx.exe
set UPX_OPTS=--best --crp-ms=999999 --nrv2e

echo Checking for 32-bit Python
%PYTHON_DIR%\python.exe  -c "import struct;bits= 8 * struct.calcsize('P');print 'Python bits:', bits;exit(0 if bits==32 else 1)"
if "%ERRORLEVEL%" neq "0" echo Python is not 32-bit
if "%ERRORLEVEL%" neq "0" goto error_general

echo Getting BleachBit version
for /f "delims=" %%a in ('%PYTHON_DIR%\python.exe -c "import bleachbit.Common; print bleachbit.Common.APP_VERSION"') do @set BB_VER=%%a
echo BleachBit version %BB_VER%

echo Checking for translations
set CANARY=locale
if not exist %CANARY% echo run "make -C po local" to build translations
if not exist %CANARY% goto error_canary

echo Checking for GTK
set CANARY=%GTK_DIR%
if not exist %CANARY% goto error_canary

echo Checking PyGTK+ library
%PYTHON_DIR%\python.exe  -c "import pygtk"
if "%ERRORLEVEL%" neq "0" goto error_general

echo Checking Python win32 library
%PYTHON_DIR%\python.exe  -c "import win32file"
if "%ERRORLEVEL%" neq "0" goto error_general

echo Checking for UPX
if not exist %UPX_EXE% echo Download UPX executable from http://upx.sourceforge.net/
if not exist %UPX_EXE% goto error_general

echo Checking for CodeSign.bat
if not exist CodeSign.bat echo CodeSign.bat not found: code signing is not available
if not exist CodeSign.bat pause

echo Checking for NSIS
if not exist %NSIS_EXE% echo NSIS executable not found: will try to build portable BleachBit
if not exist %NSIS_EXE% pause

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
if not exist %CANARY% goto error_canary

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
if not exist %CANARY% goto error_canary

echo Copying BleachBit cleaners
xcopy cleaners\*xml dist\share\cleaners\ /i /s /q

echo Checking for CleanerML
set CANARY=dist\share\cleaners\internet_explorer.xml
if not exist %CANARY% goto error_canary

echo Checking for Linux-only cleaners
if exist dist\share\cleaners\wine.xml echo "grep -l os=.linux. dist/share/cleaners/*xml | xargs rm -f"
if exist dist\share\cleaners\wine.xml pause

echo Signing code
call CodeSign.bat dist\bleachbit.exe
call CodeSign.bat dist\bleachbit_console.exe

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
if not exist %CANARY% goto error_canary

echo Building portable
rd /s /q BleachBit-portable
xcopy /e /i dist BleachBit-Portable
echo [Portable] > BleachBit-Portable\BleachBit.ini
%SZ_EXE% a -mx=9 -md=32m BleachBit-%BB_VER%-portable.zip BleachBit-portable

:nsis
echo Building installer
if     "%1" == "fast" %NSIS_EXE% /X"SetCompressor /FINAL zlib" /DVERSION=%BB_VER% windows\bleachbit.nsi
if not "%1" == "fast" %NSIS_EXE% /DVERSION=%BB_VER% windows\bleachbit.nsi
echo Signing code
call CodeSign.bat windows\BleachBit-%BB_VER%-setup.exe
if not "%1" == "fast" %NSIS_EXE% /DNoTranslations /DVERSION=%BB_VER% windows\bleachbit.nsi
if not "%1" == "fast" echo Signing code
if not "%1" == "fast" call CodeSign.bat windows\BleachBit-%BB_VER%-setup-English.exe

echo Zipping installer
REM Please note that the archive does not have the folder name
%SZ_EXE% a -mx=9 -md=32m windows\BleachBit-%BB_VER%-setup.zip .\windows\BleachBit-%BB_VER%-setup.exe

echo Success!
goto exit

:error_canary
echo %CANARY% not found

:error_general
echo Process aborted because of error!

:exit


