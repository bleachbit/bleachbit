;  vim: ts=4:sw=4:expandtab
;
;  BleachBit
;  Copyright (C) 2008-2018 Andrew Ziem
;  https://www.bleachbit.org
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
!ifdef NoTranslations
  OutFile "${prodname}-${VERSION}-setup-English.exe"
!else
  OutFile "${prodname}-${VERSION}-setup.exe"
  ; Unicode requires NSIS version 3 or later
  Unicode true
!endif

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

  !insertmacro MUI_PAGE_LICENSE "..\COPYING"
  !insertmacro MUI_PAGE_COMPONENTS
  !insertmacro MUI_PAGE_DIRECTORY
  !insertmacro MUI_PAGE_INSTFILES

  !define MUI_FINISHPAGE_NOAUTOCLOSE
  !define MUI_FINISHPAGE_RUN "$INSTDIR\${prodname}.exe"
  !define MUI_FINISHPAGE_LINK "Visit the ${prodname} web site"
  !define MUI_FINISHPAGE_LINK_LOCATION "https://www.bleachbit.org"
  !insertmacro MUI_PAGE_FINISH

  !insertmacro MUI_UNPAGE_CONFIRM
  !insertmacro MUI_UNPAGE_INSTFILES


;--------------------------------
;Languages

  !insertmacro MUI_LANGUAGE "English"
!ifndef NoTranslations
  !insertmacro MUI_LANGUAGE "Albanian"
  !insertmacro MUI_LANGUAGE "Arabic"
  !insertmacro MUI_LANGUAGE "Armenian"
  !insertmacro MUI_LANGUAGE "Asturian"
  !insertmacro MUI_LANGUAGE "Basque"
  !insertmacro MUI_LANGUAGE "Belarusian"
  !insertmacro MUI_LANGUAGE "Bosnian"
  !insertmacro MUI_LANGUAGE "Bulgarian"
  !insertmacro MUI_LANGUAGE "Catalan"
  !insertmacro MUI_LANGUAGE "Croatian"
  !insertmacro MUI_LANGUAGE "Czech"
  !insertmacro MUI_LANGUAGE "Danish"
  !insertmacro MUI_LANGUAGE "Dutch"
  !insertmacro MUI_LANGUAGE "Estonian"
  !insertmacro MUI_LANGUAGE "Finnish"
  !insertmacro MUI_LANGUAGE "French"
  !insertmacro MUI_LANGUAGE "Galician"
  !insertmacro MUI_LANGUAGE "German"
  !insertmacro MUI_LANGUAGE "Greek"
  !insertmacro MUI_LANGUAGE "Hebrew"
  !insertmacro MUI_LANGUAGE "Hungarian"
  !insertmacro MUI_LANGUAGE "Indonesian"
  !insertmacro MUI_LANGUAGE "Italian"
  !insertmacro MUI_LANGUAGE "Japanese"
  !insertmacro MUI_LANGUAGE "Korean"
  !insertmacro MUI_LANGUAGE "Kurdish"
  !insertmacro MUI_LANGUAGE "Latvian"
  !insertmacro MUI_LANGUAGE "Lithuanian"
  !insertmacro MUI_LANGUAGE "Malay"
  !insertmacro MUI_LANGUAGE "Norwegian"
  !insertmacro MUI_LANGUAGE "NorwegianNynorsk"
  !insertmacro MUI_LANGUAGE "Polish"
  !insertmacro MUI_LANGUAGE "Portuguese"
  !insertmacro MUI_LANGUAGE "PortugueseBR"
  !insertmacro MUI_LANGUAGE "Romanian"
  !insertmacro MUI_LANGUAGE "Russian"
  !insertmacro MUI_LANGUAGE "Serbian"
  !insertmacro MUI_LANGUAGE "SimpChinese"
  !insertmacro MUI_LANGUAGE "Slovak"
  !insertmacro MUI_LANGUAGE "Slovenian"
  !insertmacro MUI_LANGUAGE "Spanish"
  !insertmacro MUI_LANGUAGE "Swedish"
  !insertmacro MUI_LANGUAGE "Thai"
  !insertmacro MUI_LANGUAGE "TradChinese"
  !insertmacro MUI_LANGUAGE "Turkish"
  !insertmacro MUI_LANGUAGE "Ukrainian"
  !insertmacro MUI_LANGUAGE "Uzbek"
  !insertmacro MUI_LANGUAGE "Vietnamese"
!endif

;--------------------------------
;Function

; http://nsis.sourceforge.net/RefreshShellIcons
Function RefreshShellIcons
  !define SHCNE_ASSOCCHANGED 0x08000000
  !define SHCNF_IDLIST 0
  System::Call 'shell32.dll::SHChangeNotify(i, i, i, i) v (${SHCNE_ASSOCCHANGED}, ${SHCNF_IDLIST}, 0, 0)'
FunctionEnd

;--------------------------------
;Default section
Section Core (Required)
    SectionIn RO

    SetOutPath $INSTDIR
    File "..\dist\*.*"
    File "..\COPYING"
    SetOutPath $INSTDIR\etc
    File /r "..\dist\etc\*.*"
    SetOutPath $INSTDIR\lib
    File /r "..\dist\lib\*.*"
    SetOutPath $INSTDIR\share
    File "..\dist\share\bleachbit.png"
    SetOutPath $INSTDIR\share\cleaners
    File /r "..\dist\share\cleaners\*.*"
    SetOutPath $INSTDIR\share\themes
    File /r "..\dist\share\themes\*.*"

    SetOutPath "$INSTDIR\share\"
    File "..\bleachbit.png"

    # uninstaller
    WriteUninstaller "$INSTDIR\uninstall.exe"

    SetOutPath "$INSTDIR\"
    CreateDirectory "$SMPROGRAMS\${prodname}"
    CreateShortCut "$SMPROGRAMS\${prodname}\Uninstall.lnk" "$INSTDIR\uninstall.exe"

    # register uninstaller in Add/Remove Programs
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${prodname}" \
        "DisplayName" "${prodname}"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${prodname}" \
        "DisplayVersion" "${VERSION}"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${prodname}" \
        "HelpLink" "https://www.bleachbit.org/help"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${prodname}" \
        "NoModify" "1"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${prodname}" \
        "NoRepair" "1"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${prodname}" \
        "Publisher" "BleachBit"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${prodname}" \
        "UninstallString" "$INSTDIR\uninstall.exe"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${prodname}" \
        "URLInfoAbout" "https://www.bleachbit.org/"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${prodname}" \
        "URLUpdateInfo" "https://www.bleachbit.org/download"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${prodname}" \
        "QuietUninstallString" "$\"$INSTDIR\uninstall.exe$\" /S"
SectionEnd


SectionGroup /e Shortcuts
    Section "Start menu" SectionStart
        SetOutPath "$INSTDIR\" # this affects CreateShortCut's 'Start in' directory
        CreateShortCut "$SMPROGRAMS\${prodname}\${prodname}.lnk" "$INSTDIR\${prodname}.exe"
        CreateShortCut "$SMPROGRAMS\${prodname}\${prodname} No UAC.lnk" \
            "$INSTDIR\${prodname}.exe" \
            "--no-uac --gui"
        CreateShortCut "$SMPROGRAMS\${prodname}\${prodname} Debugging Terminal.lnk" \
            "$INSTDIR\${prodname}_console.exe"
        Call RefreshShellIcons
        WriteINIStr "$SMPROGRAMS\${prodname}\${prodname} Home Page.url" "InternetShortcut" "URL" "https://www.bleachbit.org/"
    SectionEnd

    Section "Desktop" SectionDesktop
        SetOutPath "$INSTDIR\" # this affects CreateShortCut's 'Start in' directory
        CreateShortcut "$DESKTOP\BleachBit.lnk" "$INSTDIR\${prodname}.exe"
        Call RefreshShellIcons
    SectionEnd

    Section /o "Quick launch" SectionQuickLaunch
        SetOutPath "$INSTDIR\" # this affects CreateShortCut's 'Start in' directory
        CreateShortcut "$QUICKLAUNCH\BleachBit.lnk" "$INSTDIR\${prodname}.exe"
        Call RefreshShellIcons
    SectionEnd

    Section /o "Start automatically" SectionStartUp
        SetOutPath "$INSTDIR\" # this affects CreateShortCut's 'Start in' directory
        CreateShortcut "$SMSTARTUP\BleachBit.lnk" "$INSTDIR\${prodname}.exe"
        Call RefreshShellIcons
    SectionEnd

SectionGroupEnd


!ifndef NoTranslations
Section Translations
    SetOutPath $INSTDIR\share\locale
    File /r "..\dist\share\locale\*.*"
SectionEnd
!endif

;Section for making Shred Integration Optional
!ifndef NoSectionShred
Section "Integrate Shred" SectionShred
    # register file association verb
    WriteRegStr HKCR "AllFileSystemObjects\shell\shred.bleachbit" "" 'Shred with BleachBit'
    WriteRegStr HKCR "AllFileSystemObjects\shell\shred.bleachbit\command" "" '"$INSTDIR\bleachbit.exe" --gui --no-uac --shred "%1"'
SectionEnd
!endif

;--------------------------------
;Installer Functions

Function .onInit

  ; Language display dialog
  !insertmacro MUI_LANGDLL_DISPLAY

  ; Check whether application is already installed
  ReadRegStr $R0 HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${prodname}" \
     "UninstallString"

  ; If not already installed, skip uninstallation
  StrCmp $R0 "" new_install

  MessageBox MB_OKCANCEL|MB_ICONEXCLAMATION \
    "${prodname} is already installed.  Click 'OK' to uninstall the old version before \
    upgrading, or click 'Cancel' to abort the upgrade." \
    /SD IDOK \
    IDOK uninstall_old

  Abort

  uninstall_old:
  ; If installing in silent mode, also uninstall in silent mode
  Var /GLOBAL uninstaller_cmd
  StrCpy $uninstaller_cmd '$R0 _?=$INSTDIR'
  IfSilent 0 +2
  StrCpy $uninstaller_cmd "$uninstaller_cmd /S"
  ExecWait $uninstaller_cmd ; Actually run the uninstaller

  new_install:


FunctionEnd


;--------------------------------
;Uninstaller Section

UninstallText "BleachBit will be uninstalled from the following folder.  Click Uninstall to start the uninstallation.  WARNING: The uninstaller completely removes the installation directory including any files (such as custom cleaners) that you may have added or changed."

Section "Uninstall"
    RMDir /r "$INSTDIR"
    DeleteRegKey HKCU "Software\${prodname}"
    # delete normal shortcuts
    RMDir /r "$SMPROGRAMS\${prodname}"
    # delete any extra shortcuts
    Delete "$DESKTOP\BleachBit.lnk"
    Delete "$QUICKLAUNCH\BleachBit.lnk"
    Delete "$SMSTARTUP\BleachBit.lnk"
    # remove file association
    DeleteRegKey HKCR "AllFileSystemObjects\shell\shred.bleachbit"
    # remove registration in Add/Remove Programs
    DeleteRegKey HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${prodname}"
SectionEnd


;--------------------------------
;Uninstaller Functions

Function un.onInit

  !insertmacro MUI_UNGETLANGUAGE

FunctionEnd

