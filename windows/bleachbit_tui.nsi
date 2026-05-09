; NSIS installer for BleachBit TUI (Terminal UI).
;
; SPDX-License-Identifier: GPL-3.0-or-later
; Copyright (c) 2008-2026 Andrew Ziem.
;
; This work is licensed under the terms of the GNU GPL, version 3 or
; later.  See the COPYING file in the top-level directory.
;



;--------------------------------
;Pack header:

!ifdef packhdr
  ;Using UPX path info from windows/setup.py ->
  !packhdr "$%TEMP%\exehead.tmp" '"\upx\upx.exe" -9 -q "$%TEMP%\exehead.tmp"'
!endif


;--------------------------------
;Include Modern UI

  !include "MUI2.nsh"


;--------------------------------
;General

  ;Name and file
  !define prodname "BleachBit TUI"
  ; prodpath has no spaces for use in StrCmp, directory paths, etc.
  !define prodpath "BleachBit-TUI"
  !define PROG_AUTHOR "Andrew Ziem"
  !define PROG_COPYRIGHT "Andrew Ziem"
  BrandingText "${PROG_COPYRIGHT}"
  Name "${prodname}"

  OutFile "BleachBit-TUI-${VERSION}-setup.exe"

  ; Unicode requires NSIS version 3 or later
  Unicode true


;--------------------------------
;MultiUser defines

; https://github.com/Drizin/NsisMultiUser/wiki/Defines
!define PRODUCT_NAME "${prodname}"
!define PROGEXE "bleachbit_tui.exe"

!define MULTIUSER_INSTALLMODE_ALLOW_BOTH_INSTALLATIONS 0
!define MULTIUSER_INSTALLMODE_ALLOW_ELEVATION 1
!define MULTIUSER_INSTALLMODE_ALLOW_ELEVATION_IF_SILENT 0
!define MULTIUSER_INSTALLMODE_DEFAULT_ALLUSERS 1
!define MULTIUSER_INSTALLMODE_DEFAULT_CURRENTUSER 0

; TUI is 64-bit
!define MULTIUSER_INSTALLMODE_64_BIT 1
!define MULTIUSER_INSTALLMODE_INSTDIR "${prodpath}"


;--------------------------------
;Installer-/UnInstaller-Attributes - Version Information

!define File_VERSION ${VERSION}.0

VIAddVersionKey /LANG=0 "ProductName"     "${prodname}"
VIAddVersionKey /LANG=0 "ProductVersion"  "${File_VERSION}"
VIAddVersionKey /LANG=0 "Comments"        ""
VIAddVersionKey /LANG=0 "CompanyName"     "BleachBit.org"
VIAddVersionKey /LANG=0 "LegalTrademarks" "${PROG_AUTHOR}"
VIAddVersionKey /LANG=0 "LegalCopyright"  "${PROG_COPYRIGHT}"
VIAddVersionKey /LANG=0 "FileVersion"     "${File_VERSION}"
VIAddVersionKey /LANG=0 "FileDescription" "${prodname} Setup"

VIProductVersion ${File_VERSION}
VIFileVersion ${File_VERSION}


;--------------------------------
  ;Default installation folder
  ; NsisMultiUser sets the directory.

  ;Get installation folder from registry if available
  InstallDirRegKey HKCU "Software\${prodname}" ""


;--------------------------------
;Installer-/UnInstaller-Attributes - Compiler Flags

!ifdef Compressor
  SetCompressor /SOLID lzma
!endif


;--------------------------------
; Multi-user plugins

!addplugindir /x86-unicode ".\NsisPluginsUnicode\"
!addincludedir ".\NsisInclude"
!include UAC.nsh
!include NsisMultiUser.nsh
!include LogicLib.nsh
!include StdUtils.nsh
!include WinVer.nsh

Caption "$(INSTALLER_CAPTION)"

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

; General:
!define /IfNDef MUI_ICON "${NSISDIR}\Contrib\Graphics\Icons\orange-install-nsis.ico"
!define /IfNDef MUI_UNICON "${NSISDIR}\Contrib\Graphics\Icons\orange-uninstall-nsis.ico"
!define MUI_HEADERIMAGE
!define MUI_HEADERIMAGE_BITMAP "picture.MUI2\bleachbit_150x57.bmp"

; Installer:
!define MUI_WELCOMEFINISHPAGE_BITMAP "picture.MUI2\bleachbit_164x314.bmp"
!insertmacro MUI_PAGE_WELCOME
!define MUI_LICENSEPAGE_RADIOBUTTONS
!insertmacro MUI_PAGE_LICENSE "..\COPYING"
!insertmacro MULTIUSER_PAGE_INSTALLMODE
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES
!define MUI_FINISHPAGE_NOAUTOCLOSE
; No "Run" checkbox — TUI runs in a terminal, so auto-launch is meaningless
!define MUI_FINISHPAGE_LINK "$(BLEACHBIT_MUI_FINISHPAGE_LINK)"
!define MUI_FINISHPAGE_LINK_LOCATION "https://www.bleachbit.org"
!define MUI_FINISHPAGE_NOREBOOTSUPPORT
!insertmacro MUI_PAGE_FINISH

; Uninstaller:
!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MULTIUSER_UNPAGE_INSTALLMODE
!insertmacro MUI_UNPAGE_INSTFILES


;--------------------------------
;Languages

!insertmacro MUI_LANGUAGE "English"
!insertmacro MUI_LANGUAGE "Arabic"
!insertmacro MUI_LANGUAGE "Bulgarian"
!insertmacro MUI_LANGUAGE "Catalan"
!insertmacro MUI_LANGUAGE "Croatian"
!insertmacro MUI_LANGUAGE "Czech"
!insertmacro MUI_LANGUAGE "Danish"
!insertmacro MUI_LANGUAGE "Dutch"
!insertmacro MUI_LANGUAGE "Finnish"
!insertmacro MUI_LANGUAGE "French"
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


!include NsisMultiUserLang.nsh

!include "StrFunc.nsh"
# Declare used functions
${StrCase}

;--------------------------------
;Function

Function RefreshShellIcons
  !define SHCNE_ASSOCCHANGED 0x08000000
  !define SHCNF_IDLIST 0
  System::Call 'shell32.dll::SHChangeNotify(i, i, i, i) v (${SHCNE_ASSOCCHANGED}, ${SHCNF_IDLIST}, 0, 0)'
FunctionEnd

Function .onVerifyInstDir
  ; Prevent installation directly in a shared folder such as %ProgramFiles%
  ${GetFileName} $INSTDIR $R0
  StrCmp $R0 ${prodpath} no_append
  StrCpy $INSTDIR "$INSTDIR\${prodpath}"
  no_append:
FunctionEnd

;--------------------------------
;Default section

Section "$(SECTION_CORE_NAME)" SectionCore
    SectionIn RO

    !include FilesToInstall.nsh

    # uninstaller
    WriteUninstaller "$INSTDIR\uninstall.exe"

    SetOutPath "$INSTDIR\"
    CreateDirectory "$SMPROGRAMS\${prodname}"

    # register uninstaller in Add/Remove Programs
    !insertmacro MULTIUSER_RegistryAddInstallInfo ; add registry keys
    WriteRegStr SHCTX "${MULTIUSER_INSTALLMODE_UNINSTALL_REGISTRY_KEY_PATH}$0" \
        "HelpLink" "https://www.bleachbit.org/help"
    WriteRegStr SHCTX "${MULTIUSER_INSTALLMODE_UNINSTALL_REGISTRY_KEY_PATH}$0" \
        "URLInfoAbout" "https://www.bleachbit.org/"
    WriteRegStr SHCTX "${MULTIUSER_INSTALLMODE_UNINSTALL_REGISTRY_KEY_PATH}$0" \
        "URLUpdateInfo" "https://www.bleachbit.org/download"
    WriteRegStr SHCTX "${MULTIUSER_INSTALLMODE_UNINSTALL_REGISTRY_KEY_PATH}$0" \
                 "DisplayName" "${prodname}"

SectionEnd


SectionGroup /e "$(SECTION_SHORTCUTS_NAME)" SectionShortCuts
    Section "$(SECTION_START_MENU_NAME)" SectionStart
        SetOutPath "$INSTDIR\"
        CreateShortCut "$SMPROGRAMS\${prodname}\${prodname}.lnk" "$INSTDIR\${PROGEXE}" \
            "" "$INSTDIR\${PROGEXE}"
        Call RefreshShellIcons
    SectionEnd

    Section "$(SECTION_DESKTOP_NAME)" SectionDesktop
        IfSilent 0 addDesktopShortcut
        ${GetParameters} $R0
        ${StrCase} $R0 $R0 "L"
        ${GetOptions} $R0 "/nodesktopshortcut" $R1
        IfErrors addDesktopShortcut doNotAddDesktopShortcut
        addDesktopShortcut:
        SetOutPath "$INSTDIR\"
        CreateShortcut "$DESKTOP\${prodname}.lnk" "$INSTDIR\${PROGEXE}"
        Call RefreshShellIcons
        doNotAddDesktopShortcut:
    SectionEnd
SectionGroupEnd


Section "$(SECTION_TRANSLATIONS_NAME)" SectionTranslations
  !include LocaleToInstall.nsh
SectionEnd


; Keep this section last for accurate size reporting
Section "-Write Install Size"
    !insertmacro MULTIUSER_RegistryAddInstallSizeInfo
SectionEnd

;--------------------------------
;Installer Functions

Function .onInit

  ${If} ${AtMostWin7}
    MessageBox MB_OK|MB_ICONEXCLAMATION "This version of Windows is not compatible with this version of BleachBit. Please see https://www.bleachbit.org/bleachbit-windows-7 to download a compatible version." /SD IDOK
    Abort
  ${EndIf}

  !insertmacro MULTIUSER_INIT

  ; Language display dialog
  !insertmacro MUI_LANGDLL_DISPLAY

  ; Check whether application is already installed
  ReadRegStr $R0 HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${prodname}" \
     "UninstallString"

  StrCmp $R0 "" new_install

  MessageBox MB_OKCANCEL|MB_ICONEXCLAMATION \
    "$(ALREADY_INSTALLED)" \
    IDOK uninstall_old
  Abort

  uninstall_old:
    ; Run the uninstaller silently
    ClearErrors
    ExecWait '$R0 /S _?=$INSTDIR'
    IfErrors 0 new_install
    MessageBox MB_ICONSTOP|MB_OK "$(ALREADY_INSTALLED_UNINSTALL_FAILED)"
    Abort

  new_install:

FunctionEnd

Function un.onInit
  !insertmacro MULTIUSER_UNINIT
  !insertmacro MUI_UNGETLANGUAGE
FunctionEnd


;--------------------------------
;Uninstaller Section

Section "Uninstall"

  !include FilesToUninstall.nsh

  Delete "$INSTDIR\uninstall.exe"

  RMDir "$INSTDIR"

  ; Remove shortcuts
  Delete "$SMPROGRAMS\${prodname}\${prodname}.lnk"
  RMDir "$SMPROGRAMS\${prodname}"

  Delete "$DESKTOP\${prodname}.lnk"

  ; Remove registry keys
  !insertmacro MULTIUSER_RegistryRemoveInstallInfo

SectionEnd