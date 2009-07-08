;  vim: ts=4:sw=4:expandtab
;
;  BleachBit
;  Copyright (C) 2009 Andrew Ziem
;  http://bleachbit-project.appspot.com
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
  !define prodname "BleachBit"
  Name "${prodname}"
  OutFile "${prodname}-setup.exe"

  ;Default installation folder
  InstallDir "$PROGRAMFILES\${prodname}"

  ;Get installation folder from registry if available
  InstallDirRegKey HKCU "Software\${prodname}" ""

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
  !define MUI_LANGDLL_REGISTRY_KEY "Software\${prodname}"
  !define MUI_LANGDLL_REGISTRY_VALUENAME "Installer Language"


;--------------------------------
;Pages

  !insertmacro MUI_PAGE_LICENSE "COPYING"
  !insertmacro MUI_PAGE_COMPONENTS
  !insertmacro MUI_PAGE_DIRECTORY
  !insertmacro MUI_PAGE_INSTFILES

  !define MUI_FINISHPAGE_NOAUTOCLOSE
  !define MUI_FINISHPAGE_RUN "$INSTDIR\${prodname}.exe"
  !define MUI_FINISHPAGE_LINK "Visit the ${prodname} web site"
  !define MUI_FINISHPAGE_LINK_LOCATION "http://bleachbit-project.appspot.com"
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
  !insertmacro MUI_LANGUAGE "Dutch"
  !insertmacro MUI_LANGUAGE "Finnish"
  !insertmacro MUI_LANGUAGE "French"
  !insertmacro MUI_LANGUAGE "German"
  !insertmacro MUI_LANGUAGE "Hebrew"
  !insertmacro MUI_LANGUAGE "Hungarian"
  !insertmacro MUI_LANGUAGE "Italian"
  !insertmacro MUI_LANGUAGE "Norwegian"
  !insertmacro MUI_LANGUAGE "Portuguese"
  !insertmacro MUI_LANGUAGE "PortugueseBR"
  !insertmacro MUI_LANGUAGE "Russian"
  !insertmacro MUI_LANGUAGE "Serbian"
  !insertmacro MUI_LANGUAGE "SimpChinese"
  !insertmacro MUI_LANGUAGE "Slovak"
  !insertmacro MUI_LANGUAGE "Spanish"
  !insertmacro MUI_LANGUAGE "Polish"
  !insertmacro MUI_LANGUAGE "Turkish"


;--------------------------------
;Default section
Section Core (Required)
    SectionIn RO

    SetOutPath $INSTDIR
    File /r "dist\*.*"
    File "COPYING"

    SetOutPath "$INSTDIR\share\"
    File "bleachbit.png"

    WriteUninstaller "$INSTDIR\uninstall.exe"

    SetOutPath "$INSTDIR\"
    CreateDirectory "$SMPROGRAMS\${prodname}"
    CreateShortCut "$SMPROGRAMS\${prodname}\Uninstall.lnk" "$INSTDIR\uninstall.exe"

    # register uninstaller in Add/Remove Programs
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${prodname}" \
        "DisplayName" "${prodname}"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${prodname}" \
        "HelpLink" "http://bleachbit-project.appspot.com/"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${prodname}" \
        "NoModify" "1"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${prodname}" \
        "NoRepair" "1"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${prodname}" \
        "UninstallString" "$INSTDIR\uninstall.exe"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${prodname}" \
        "URLInfoAbout" "http://bleachbit-project.appspot.com/"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${prodname}" \
        "URLUpdateInfo" "http://bleachbit-project.appspot.com/"
SectionEnd


SectionGroup Shortcuts
    Section "Start menu" SectionStart
        SetOutPath "$INSTDIR\" # this affects CreateShortCut's 'Start in' directory
        CreateShortCut "$SMPROGRAMS\${prodname}\${prodname}.lnk" "$INSTDIR\${prodname}.exe"
    SectionEnd

    Section "Desktop" SectionDesktop
        SetOutPath "$INSTDIR\" # this affects CreateShortCut's 'Start in' directory
        CreateShortcut "$DESKTOP\BleachBit.lnk" "$INSTDIR\${prodname}.exe"
    SectionEnd
SectionGroupEnd

;--------------------------------
;Installer Functions

Function .onInit

  !insertmacro MUI_LANGDLL_DISPLAY

  ; uninstall old before installing new
  ReadRegStr $R0 HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${prodname}" \
     "UninstallString"

  StrCmp $R0 "" new_install

  MessageBox MB_OKCANCEL|MB_ICONEXCLAMATION \
    "${prodname} is already installed.  Click 'OK' to uninstall the old version before \
    upgrading, or click 'Cancel' to abort the upgrade." \
    IDOK uninstall_old
    Abort

  uninstall_old:
  ExecWait '$R0 _?=$INSTDIR'

  new_install:


FunctionEnd


;--------------------------------
;Uninstaller Section

UninstallText "BleachBit will be uninstalled from the following folder.  Click Uninstall to start the uninstallation.  WARNING: The uninstaller completely removes the installation directory including any files (such as custom cleaners) that you may have added or changed."

Section "Uninstall"
    Delete "$DESKTOP\BleachBit.lnk"
    RMDir /r "$SMPROGRAMS\${prodname}"
    RMDir /r "$INSTDIR"
    DeleteRegKey HKCU "Software\${prodname}"
    # remove registration in Add/Remove Programs
    DeleteRegKey HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${prodname}"
SectionEnd


;--------------------------------
;Uninstaller Functions

Function un.onInit

  !insertmacro MUI_UNGETLANGUAGE

FunctionEnd

