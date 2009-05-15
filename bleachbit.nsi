;  BleachBit
;  Copyright (C) 2009 Andrew Ziem
;  http://bleachbit.sourceforge.net
; 
;  This program is free software: you can redistribute it and/or modify
;  it under the terms of the GNU General Public License as published by
;  the Free Software Foundation, either version 3 of the License, or
;  (at your option) any later version.
; 
;  This program is distributed in the hope that it will be useful,
;  but WITHOUT ANY WARRANTY; without even the implied warranty of
;  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
;  GNU General Public License for more details.
; 
;  You should have received a copy of the GNU General Public License
;  along with this program.  If not, see <http://www.gnu.org/licenses/>.



;--------------------------------
;Include Modern UI

  !include "MUI2.nsh"

  
;--------------------------------
;General

  ;Name and file
  Name "BleachbBit"
  OutFile "BleachBit-setup.exe"

  ;Default installation folder
  InstallDir "$PROGRAMFILES\BleachBit"
  
  ;Get installation folder from registry if available
  InstallDirRegKey HKCU "Software\BleachBit" ""

  ;Request application privileges for Windows Vista
  RequestExecutionLevel user
  
  ;Best compression
  SetCompressor /SOLID lzma

  
;--------------------------------
;Interface Settings

  !define MUI_ABORTWARNING

  
;--------------------------------
;Pages

  !insertmacro MUI_PAGE_LICENSE "COPYING"
  !insertmacro MUI_PAGE_DIRECTORY
  !insertmacro MUI_PAGE_INSTFILES
  
  !insertmacro MUI_UNPAGE_CONFIRM
  !insertmacro MUI_UNPAGE_INSTFILES

  
;--------------------------------
;Languages
 
  !insertmacro MUI_LANGUAGE "English"
  
  
;--------------------------------
;Default section
section
    setOutPath $INSTDIR
	File /r "dist\*.*"
	;File  "dist\*.*"
	File "bleachbit.png"
	
	setOutPath $INSTDIR\cleaners
	File ".\cleaners\*.xml"
 
    writeUninstaller "$INSTDIR\uninstall.exe"
 
	CreateDirectory "$SMPROGRAMS\BleachBit"
    createShortCut "$SMPROGRAMS\BleachBit\Uninstall.lnk" "$INSTDIR\uninstall.exe"
	createShortCut "$SMPROGRAMS\BleachBit\BleachBit.lnk" "$INSTDIR\BleachBit.exe"
sectionEnd

 
;--------------------------------
;Uninstaller Section

section "Uninstall"
 
    RMDir /r "$SMPROGRAMS\Bleachbit"
	RMDir /r "$INSTDIR"   
	DeleteRegKey HKCU "Software\BleachBit"
sectionEnd

