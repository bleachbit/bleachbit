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


echo Deleting dist
del /q /s dist > nul

echo Running py2exe
c:\python26\python.exe -OO setup.py py2exe
if not exist dist\bleachbit.exe goto exit

echo Copying GTK files
mkdir dist\etc
xcopy c:\gtk\etc dist\etc /i /s
mkdir dist\lib
xcopy c:\gtk\lib dist\lib /i /s
mkdir dist\share
xcopy c:\gtk\share dist\share /i /s

echo Compressing executables
upx -9 dist\*dll dist\*exe

:exit


