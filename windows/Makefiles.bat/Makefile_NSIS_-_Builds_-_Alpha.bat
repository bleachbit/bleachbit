@echo off
cd ..
rem "C:\Program Files (x86)\NSIS\makensis.exe" /V3 bleachbit\windows\bleachbit.nsi
"C:\Program Files (x86)\NSIS\makensis.exe" /V3 /DVERSION=2.3.0.1080 /DAlphaTester /DPathToCleanerML=".." /Dpackhdr /DCompressor bleachbit.nsi
rem "C:\Program Files (x86)\NSIS\makensis.exe" /V2 bleachbit\windows\bleachbit.nsi
rem "C:\Program Files (x86)\NSIS\makensis.exe" /V1 bleachbit\windows\bleachbit.nsi
pause
rem move bleachbit\windows\BleachBit-*.exe .
dir
pause
