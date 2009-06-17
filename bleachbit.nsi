;  vim: ts=4:sw=4:expandtab
;
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
  RequestExecutionLevel admin

  ;Best compression
  SetCompressor /SOLID lzma


;--------------------------------
;Interface Settings

  !define MUI_ABORTWARNING


;--------------------------------
;Language Selection Dialog Settings

  ;Remember the installer language
  !define MUI_LANGDLL_REGISTRY_ROOT "HKCU" 
  !define MUI_LANGDLL_REGISTRY_KEY "Software\BleachBit" 
  !define MUI_LANGDLL_REGISTRY_VALUENAME "Installer Language"


;--------------------------------
;Pages

  !insertmacro MUI_PAGE_LICENSE "COPYING"
  !insertmacro MUI_PAGE_DIRECTORY
  !insertmacro MUI_PAGE_INSTFILES

  !define MUI_FINISHPAGE_NOAUTOCLOSE
  !define MUI_FINISHPAGE_RUN "$INSTDIR\BleachBit.exe"
  !define MUI_FINISHPAGE_LINK "Visit the BleachBit web site"
  !define MUI_FINISHPAGE_LINK_LOCATION "http://bleachbit.sourceforge.net"
  !insertmacro MUI_PAGE_FINISH

  !insertmacro MUI_UNPAGE_CONFIRM
  !insertmacro MUI_UNPAGE_INSTFILES


;--------------------------------
;Languages

  !insertmacro MUI_LANGUAGE "English"
  !insertmacro MUI_LANGUAGE "Arabic"
  !insertmacro MUI_LANGUAGE "Bulgarian"
  !insertmacro MUI_LANGUAGE "Catalan"
  !insertmacro MUI_LANGUAGE "Czech"
  !insertmacro MUI_LANGUAGE "Danish"
  !insertmacro MUI_LANGUAGE "Finnish"
  !insertmacro MUI_LANGUAGE "French"
  !insertmacro MUI_LANGUAGE "German"
  !insertmacro MUI_LANGUAGE "Hebrew"
  !insertmacro MUI_LANGUAGE "Hungarian"
  !insertmacro MUI_LANGUAGE "Italian"
  !insertmacro MUI_LANGUAGE "Portuguese"
  !insertmacro MUI_LANGUAGE "PortugueseBR"
  !insertmacro MUI_LANGUAGE "Russian"
  !insertmacro MUI_LANGUAGE "Serbian"
  !insertmacro MUI_LANGUAGE "Slovak"
  !insertmacro MUI_LANGUAGE "Spanish"
  !insertmacro MUI_LANGUAGE "Turkish"


;--------------------------------
;Default section
section
    SetOutPath $INSTDIR
    File /r "dist\*.*"
    File "COPYING"

    SetOutPath "$INSTDIR\share\"
    File "bleachbit.png"

    SetOutPath "$INSTDIR\share\cleaners\"
    File ".\cleaners\*.xml"

    WriteUninstaller "$INSTDIR\uninstall.exe"

    CreateDirectory "$SMPROGRAMS\BleachBit"
    CreateShortCut "$SMPROGRAMS\BleachBit\Uninstall.lnk" "$INSTDIR\uninstall.exe"
    CreateShortCut "$SMPROGRAMS\BleachBit\BleachBit.lnk" "$INSTDIR\BleachBit.exe"
sectionEnd


;--------------------------------
;Installer Functions

Function .onInit

  !insertmacro MUI_LANGDLL_DISPLAY

FunctionEnd


;--------------------------------
;Uninstaller Section

UninstallText "BleachBit will be uninstalled from the following folder.  Click Uninstall to start the uninstallation.  WARNING: The uninstaller completely removes the installation directory including any files (such as custom cleaners) that you may have added or changed."

Section "Uninstall"
    RMDir /r "$SMPROGRAMS\Bleachbit"
    RMDir /r "$INSTDIR"
    DeleteRegKey HKCU "Software\BleachBit"
SectionEnd


;--------------------------------
;Uninstaller Functions

Function un.onInit

  !insertmacro MUI_UNGETLANGUAGE
  
FunctionEnd

