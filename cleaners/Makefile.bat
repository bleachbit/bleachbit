@echo off
if "%1"=="" goto shorthelp
if "%1"=="-help" goto help
if "%1"=="-file" goto help
if "%1"=="-folder" goto help
goto shorthelp

:help
echo.
echo Copyright (C) 2019 by Andrew Ziem and Tobias B. Besemer.  All rights reserved.
echo License is GNU GPL version 3 or later - http://gnu.org/licenses/gpl.html.
echo This is free software: You are free to change and redistribute it.
echo There is NO WARRANTY, to the extent permitted by law.
echo.
echo Based on "Makefile" of Andrew Ziem.
echo.
echo Version: 0.4.0
echo Date: 2019-03-12
echo.
if "%1"=="-file" goto file
if "%1"=="-folder" goto folder
echo Requirements:
echo - MinGW
echo - msys-libxml2-bin of MinGW and its dependencies
echo - msys-diffutils-bin of MinGW and its dependencies
rem echo - msys-grep-bin of MinGW and its dependencies
echo - Path to MinGW\msys\1.0\bin\ in the system environment variable "path"
echo.
if "%1"=="-help" goto shorthelp

:errorfile
echo [file] missing!
goto shorthelp

:errorfolder
echo [folder] missing!
goto shorthelp

:shorthelp
echo.
echo Makefile.bat makes CleanerML files pretty and test them.
echo.
echo Usage: Makefile.bat [option] [file/folder]
echo        -help : Shows more help
echo        -file : Makes the [file] pretty and tests it
echo        -folder : Makes the files in [folder] pretty and test them
echo.
echo CleanerML on GitHub: https://github.com/az0/cleanerml
goto end

:folder
if "%2"=="" goto errorfolder

for %%f in (.\%2\*.xml) do Makefile.bat -file %%f
goto end

:file
if "%2"=="" goto errorfile

rem Make pretty:
xmllint --format %2 >%2.pretty
diff -q %2 %2.pretty
echo.

rem A "if not" to prevent 0-Byte-File because e.g. xmllint not found...
if not exist %2.pretty goto somethingmissing

rem ...and some code to prevent 0-Byte-File because e.g. XML Syntax Problems...
FOR /F "usebackq" %%A IN ('%2.pretty') DO set size=%%~zA
if %size% LSS 1 (
    echo We got a problem !!! 0-Byte !!! I revert !!!
    del %2.pretty
    goto end
)

rem -> File there, and no 0-Bytes! ->
del %2
move %2.pretty %2
echo.
echo %2 is pretty now!
echo.

:test
rem Make test:

:workaround-xmllint-schema-crash
rem goto end

if exist ..\doc\cleaner_markup_language.xsd xmllint --noout --schema ..\bleachbit\doc\cleaner_markup_language.xsd %2
if exist ..\doc\cleaner_markup_language.xsd goto end
if exist ..\bleachbit\doc\cleaner_markup_language.xsd xmllint --noout --schema ..\bleachbit\doc\cleaner_markup_language.xsd %2
if exist ..\bleachbit\doc\cleaner_markup_language.xsd goto end
echo.
echo cleaner_markup_language.xsd missing !!!
goto end

:somethingmissing
echo Something missing !!!
echo Do you have installed xmllint ???
echo Do you have the path to MinGW\msys\1.0\bin\ in the system environment variable "path" ???
goto end

:end
