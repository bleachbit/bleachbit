;  vim: ts=4:sw=4:expandtab
;
;  BleachBit
;  Copyright (C) 2008-2021 Andrew Ziem
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

;  @scriptversion v3.0.1.1429
;  @scriptdate 2019-12-01


;--------------------------------
;Pack header:

; Compress installer exehead with an executable compressor.

; Paths should be absolute to allow building from any location.
; Note that your executable compressor should not compress the first icon.

!ifdef packhdr
  ;Using UPX path info from setup_py2exe.py ->
  !packhdr "$%TEMP%\exehead.tmp" '"\upx\upx.exe" -9 -q "$%TEMP%\exehead.tmp"'
!endif


;--------------------------------
;Include Modern UI

  !include "MUI2.nsh"


;--------------------------------
;General

  ;Name and file
  !define prodname "BleachBit"
  !define COMPANY_NAME "BleachBit" ; # used by NsisMultiUser
  Name "${prodname}"
!ifdef NoTranslations
  OutFile "${prodname}-${VERSION}-setup-English.exe"
!else
  OutFile "${prodname}-${VERSION}-setup.exe"
!endif

; Unicode requires NSIS version 3 or later
Unicode true


;--------------------------------
;MultiUser defines

; https://github.com/Drizin/NsisMultiUser/wiki/Defines
!define PRODUCT_NAME "${prodname}" ; exact copy to another name for multi-user script
; !define VERSION "2.3"
; "VERSION" already defined!
!define PROGEXE "${prodname}.exe"
; !define COMPANY_NAME "BleachBit"
; "COMPANY_NAME" already defined!

; An option (MULTIUSER_INSTALLMODE_ALLOW_BOTH_INSTALLATIONS) defines whether simultaneous per-user
; and per-machine installations on the same machine are allowed. If set to disallow, the installer
; always requires elevation when there's per-machine installation in order to remove it first.
!define MULTIUSER_INSTALLMODE_ALLOW_BOTH_INSTALLATIONS 0
; Decision to don't ALLOW_BOTH_INSTALLATIONS was, because it's just to risky to have to versions
; installed at the same time and BB maybe run into unknown issues.
; This means now, that maybe a per-machine installation gets deinstalled and a per-user installation
; gets preferenced!

; An option (MULTIUSER_INSTALLMODE_ALLOW_ELEVATION) defines whether elevation if allowed.
; If elevation is disabled, the per-machine option becomes available only if the (un)installer
; is started elevated from Windows and is disabled otherwise.
!define MULTIUSER_INSTALLMODE_ALLOW_ELEVATION 1

!define MULTIUSER_INSTALLMODE_ALLOW_ELEVATION_IF_SILENT 0

; MULTIUSER_INSTALLMODE_DEFAULT_ALLUSERS:
; 0 or 1, (only available if MULTIUSER_INSTALLMODE_ALLOW_ELEVATION = 1 and there are 0 or 2 installations
; on the system) when running as user and is set to 1, per-machine installation is pre-selected, otherwise
; per-user installation.
!define MULTIUSER_INSTALLMODE_DEFAULT_ALLUSERS 1

; MULTIUSER_INSTALLMODE_DEFAULT_CURRENTUSER:
; 0 or 1, (only available if there are 0 or 2 installations on the system) when running as admin and
; is set to 1, per-user installation is pre-selected, otherwise per-machine installation.
!define MULTIUSER_INSTALLMODE_DEFAULT_CURRENTUSER 0

!define MULTIUSER_INSTALLMODE_64_BIT 0
!define MULTIUSER_INSTALLMODE_INSTDIR "${prodname}"


;--------------------------------
;Installer-/UnInstaller-Attributes - Version Information
; https://nsis.sourceforge.io/Docs/Chapter4.html#versioninfo

;!define File_VERSION 2.3.0.0
; Later:
!define File_VERSION ${VERSION}.0

!ifdef NoTranslations
  VIAddVersionKey /LANG=1033 "ProductName" "BleachBit"
  VIAddVersionKey /LANG=1033 "CompanyName" "BleachBit.org"
  VIAddVersionKey /LANG=1033 "LegalCopyright" "Andrew Ziem"
  VIAddVersionKey /LANG=1033 "FileDescription" "BleachBit Setup"
  VIAddVersionKey /LANG=1033 "ProductVersion" "${File_VERSION}"
  VIAddVersionKey /LANG=1033 "FileVersion" "${File_VERSION}"
!endif

!ifndef NoTranslations
  VIAddVersionKey /LANG=0 "ProductName" "BleachBit"
  VIAddVersionKey /LANG=0 "CompanyName" "BleachBit.org"
  VIAddVersionKey /LANG=0 "LegalCopyright" "Andrew Ziem"
  VIAddVersionKey /LANG=0 "FileDescription" "BleachBit Setup"
  VIAddVersionKey /LANG=0 "ProductVersion" "${File_VERSION}"
  VIAddVersionKey /LANG=0 "FileVersion" "${File_VERSION}"
!endif

VIProductVersion ${File_VERSION}
VIFileVersion ${File_VERSION}


;--------------------------------
  ;Default installation folder
  ; NsisMultiUser sets the directory.
  ;InstallDir "$PROGRAMFILES\${prodname}"

  ;Get installation folder from registry if available
  InstallDirRegKey HKCU "Software\${prodname}" ""

  ;Request application privileges for Windows Vista
  ; NsisMultiUser sets this, when needed.
  ;RequestExecutionLevel admin


;--------------------------------
;Installer-/UnInstaller-Attributes - Compiler Flags
; https://nsis.sourceforge.io/Docs/Chapter4.html#flags

; Set default compressor:
; https://ci.appveyor.com/ do already "SetCompressor /FINAL zlib"
; Best compression: https://nsis.sourceforge.io/Docs/Chapter1.html#intro-features
!ifdef Compressor
  SetCompressor /SOLID lzma
!endif


;--------------------------------
; Rest of old part "multi-user"

!addplugindir /x86-unicode ".\NsisPluginsUnicode\"
!addincludedir ".\NsisInclude"
!include UAC.nsh
!include NsisMultiUser.nsh
!include LogicLib.nsh
!include StdUtils.nsh


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
!define MUI_COMPONENTSPAGE_SMALLDESC

; Installer:
!define MUI_WELCOMEFINISHPAGE_BITMAP "picture.MUI2\bleachbit_164x314.bmp"
!insertmacro MUI_PAGE_WELCOME
!define MUI_LICENSEPAGE_RADIOBUTTONS
!insertmacro MUI_PAGE_LICENSE "..\COPYING"
;Later:
;!insertmacro MUI_PAGE_LICENSE "$(MUI_LICENSE)"
;!define MUI_PAGE_CUSTOMFUNCTION_PRE "MULTIUSER_PAGE_INSTALLMODE_Pre"
;!define MUI_PAGE_CUSTOMFUNCTION_LEAVE "MULTIUSER_PAGE_INSTALLMODE_Leave"
!insertmacro MULTIUSER_PAGE_INSTALLMODE
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_COMPONENTS
!insertmacro MUI_PAGE_INSTFILES
!define MUI_FINISHPAGE_NOAUTOCLOSE
!define MUI_FINISHPAGE_RUN "$INSTDIR\${prodname}.exe"
!define MUI_FINISHPAGE_LINK "Visit the ${prodname} web site."
;Later:
;!define MUI_FINISHPAGE_LINK "$(BLEACHBIT_MUI_FINISHPAGE_LINK)"
!define MUI_FINISHPAGE_LINK_LOCATION "https://www.bleachbit.org"
;Later:
;!define MUI_FINISHPAGE_LINK_LOCATION "${PRODURL}"
!define MUI_FINISHPAGE_NOREBOOTSUPPORT
!insertmacro MUI_PAGE_FINISH

; Uninstaller:
!define MUI_UNWELCOMEFINISHPAGE_BITMAP "picture.MUI2\bleachbit_164x314.bmp"
!insertmacro MUI_UNPAGE_WELCOME
!insertmacro MUI_UNPAGE_CONFIRM
;Later:
;!define MUI_PAGE_CUSTOMFUNCTION_PRE "un.MULTIUSER_UnPAGE_INSTALLMODE_Pre"
;!define MUI_PAGE_CUSTOMFUNCTION_LEAVE "un.MULTIUSER_UnPAGE_INSTALLMODE_Leave"
!insertmacro MULTIUSER_UNPAGE_INSTALLMODE
; MUI_UNPAGE_DIRECTORY not needed, ATM.
; !insertmacro MUI_UNPAGE_DIRECTORY
!insertmacro MUI_UNPAGE_COMPONENTS
!insertmacro MUI_UNPAGE_INSTFILES
!define MUI_UNFINISHPAGE_NOAUTOCLOSE
!insertmacro MUI_UNPAGE_FINISH

; MUI_LANGUAGE[EX] should be inserted after the MUI_[UN]PAGE_* macros!


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


!include NsisMultiUserLang.nsh

!include "StrFunc.nsh"
# Declare used functions
${StrCase}

;--------------------------------
;Function

; http://nsis.sourceforge.net/RefreshShellIcons
Function RefreshShellIcons
  !define SHCNE_ASSOCCHANGED 0x08000000
  !define SHCNF_IDLIST 0
  System::Call 'shell32.dll::SHChangeNotify(i, i, i, i) v (${SHCNE_ASSOCCHANGED}, ${SHCNF_IDLIST}, 0, 0)'
FunctionEnd

Function .onVerifyInstDir
  ; This callback belongs to MUI_PAGE_DIRECTORY and is called every time the user presses Browse
  ; button and selects install directory. It does not affect typing in the input field.

  ; The purpose is to prevent installation in a shared folder such as %ProgramFiles%
  ; by adding the product name to the end.

  ${GetFileName} $INSTDIR $R0 ; get the last part of the path
  StrCmp $R0 ${prodname} no_append
  StrCpy $INSTDIR "$INSTDIR\${prodname}"
  no_append:
FunctionEnd

;--------------------------------
;Default section
Section Core (Required)
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

    # Build cache now while there is a GUI progress bar.
    DetailPrint "The next step is building font cache, during which you may see a black window."
    DetailPrint "It usually finishes in one minute, but sometimes it takes ten minutes."
    ExecWait '"$instdir\fc-cache.exe"'
SectionEnd


SectionGroup /e Shortcuts
    Section "Start menu" SectionStart
        SetOutPath "$INSTDIR\" # this affects CreateShortCut's 'Start in' directory
        CreateShortCut "$SMPROGRAMS\${prodname}\${prodname}.lnk" "$INSTDIR\${prodname}.exe" \
            "" "$INSTDIR\${prodname}.exe"
        CreateShortCut "$SMPROGRAMS\${prodname}\${prodname} No UAC.lnk" \
            "$INSTDIR\${prodname}.exe" \
            "--no-uac --gui" "$INSTDIR\${prodname}.exe"
        CreateShortCut "$SMPROGRAMS\${prodname}\${prodname} Debugging Terminal.lnk" \
            "$INSTDIR\${prodname}_console.exe" "" "$INSTDIR\${prodname}.exe"
        Call RefreshShellIcons
    SectionEnd

    Section "Desktop" SectionDesktop
        IfSilent 0 addDesktopShortcut
        ${GetParameters} $R0
        ${StrCase} $R0 $R0 "L" # "L" means lowercase
        ${GetOptions} $R0 "/nodesktopshortcut" $R1
        IfErrors addDesktopShortcut doNotAddDesktopShortcut
        addDesktopShortcut:
        SetOutPath "$INSTDIR\" # this affects CreateShortCut's 'Start in' directory
        CreateShortcut "$DESKTOP\BleachBit.lnk" "$INSTDIR\${prodname}.exe"
        Call RefreshShellIcons

        doNotAddDesktopShortcut:

    SectionEnd

    Section /o "Quick launch" SectionQuickLaunch
        SetOutPath "$INSTDIR\" # this affects CreateShortCut's 'Start in' directory
        CreateShortcut "$QUICKLAUNCH\BleachBit.lnk" "$INSTDIR\${prodname}.exe"
        Call RefreshShellIcons
    SectionEnd

SectionGroupEnd


!ifndef NoTranslations
Section Translations
  !include LocaleToInstall.nsh
SectionEnd
!endif

; Section for making Shred Integration optional
!ifndef NoSectionShred
  Section "Integrate Shred" SectionShred
    ; Register Windows Explorer Shell Extension (Shredder)
    WriteRegStr HKCR "${SHRED_REGEX_KEY}" "" 'Shred with BleachBit'
    WriteRegStr HKCR "${SHRED_REGEX_KEY}" "Icon" "$INSTDIR\bleachbit.exe,0"
    WriteRegStr HKCR "${SHRED_REGEX_KEY}\command" "" '"$INSTDIR\bleachbit.exe" --context-menu "%1"'
  SectionEnd
!endif

; Keep this section last. It must be last because that is when the
; actual size is known.
; This is a hidden section.
Section "-Write Install Size"
    !insertmacro MULTIUSER_RegistryAddInstallSizeInfo
SectionEnd

;--------------------------------
;Installer Functions

Function .onInit

  !insertmacro MULTIUSER_INIT

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
    Delete $INSTDIR\bleachbit.exe.log

    !ifndef NoTranslations
      !include LocaleToUninstall.nsh
    !endif

    !include FilesToUninstall.nsh

    DeleteRegKey HKCU "Software\${prodname}"
    # delete normal shortcuts
    RMDir /r "$SMPROGRAMS\${prodname}"
    # delete any extra shortcuts
    Delete "$DESKTOP\BleachBit.lnk"
    Delete "$QUICKLAUNCH\BleachBit.lnk"
    Delete "$SMSTARTUP\BleachBit.lnk"
    # Remove Windows Explorer Shell Extension (Shredder)
    DeleteRegKey HKCR "${SHRED_REGEX_KEY}"

    # Remove the uninstaller as the very last step.
    # If something goes wrong, let the user run it again.
    Delete $INSTDIR\uninstall.exe
    RMDir /REBOOTOK "$INSTDIR\."

    # Remove the uninstaller from registry as the very last step.
    # If something goes wrong, let the user run it again.
    !insertmacro MULTIUSER_RegistryRemoveInstallInfo
SectionEnd


;--------------------------------
;Uninstaller Functions

Function un.onInit

  !insertmacro MULTIUSER_UNINIT

  !insertmacro MUI_UNGETLANGUAGE

FunctionEnd

