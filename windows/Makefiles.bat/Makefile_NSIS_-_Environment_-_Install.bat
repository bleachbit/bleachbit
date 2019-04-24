if not exist "C:\Program Files (x86)\BleachBit\*.*" goto error
cd ..
cd ..
if not exist dist md dist
if not exist cleanerml md cleanerml
if not exist cleanerml\release md cleanerml\release
if not exist cleanerml\pending md cleanerml\pending
xcopy "C:\Program Files (x86)\BleachBit\*.*" dist /E /H /K
copy I:\GitHub\cleanerml\release\*.* cleanerml\release
copy I:\GitHub\cleanerml\pending\*.* cleanerml\pending
cd cleanerml\pending
del README.md
cd ..
cd ..
cd dist
if exist BleachBit.exe.log del BleachBit.exe.log
del COPYING
del uninstall.exe
cd share
del bleachbit.png
rem rmdir cleaners /s
cd ..
cd ..
cd windows
cd Makefiles.bat
goto end

:error
echo. BleachBit missing!

:end
pause
