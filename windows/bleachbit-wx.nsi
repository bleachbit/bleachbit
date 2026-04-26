; Simple NSIS installer for BleachBit wxWidgets MVP
; vim: ts=4:sw=4:expandtab

!include "MUI2.nsh"

!define prodname "BleachBit"
Name "${prodname}"
OutFile "BleachBit-${VERSION}-setup.exe"
Unicode true
InstallDir "$PROGRAMFILES64\${prodname}"
RequestExecutionLevel admin

!define MUI_ABORTWARNING
!insertmacro MUI_PAGE_WELCOME
!define MUI_LICENSEPAGE_RADIOBUTTONS
!insertmacro MUI_PAGE_LICENSE "..\COPYING"
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES
!define MUI_FINISHPAGE_NOAUTOCLOSE
!define MUI_FINISHPAGE_RUN "$INSTDIR\bleachbit.exe"
!insertmacro MUI_PAGE_FINISH

!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES

!insertmacro MUI_LANGUAGE "English"

Section "BleachBit" SectionCore
    SectionIn RO
    !include "NsisInclude\FilesToInstall.nsh"
    !include "NsisInclude\LocaleToInstall.nsh"
    WriteUninstaller "$INSTDIR\uninstall.exe"
    CreateDirectory "$SMPROGRAMS\${prodname}"
    CreateShortcut "$SMPROGRAMS\${prodname}\${prodname}.lnk" "$INSTDIR\bleachbit.exe"
    CreateShortcut "$DESKTOP\BleachBit.lnk" "$INSTDIR\bleachbit.exe"
SectionEnd

Section "Uninstall"
    !include "NsisInclude\FilesToUninstall.nsh"
    !include "NsisInclude\LocaleToUninstall.nsh"
    Delete "$INSTDIR\uninstall.exe"
    RMDir /REBOOTOK "$INSTDIR\."
    Delete "$SMPROGRAMS\${prodname}\${prodname}.lnk"
    RMDir "$SMPROGRAMS\${prodname}"
    Delete "$DESKTOP\BleachBit.lnk"
SectionEnd
