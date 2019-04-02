;  vim: ts=4:sw=4:expandtab
;
;  BleachBit
;  Copyright (C) 2008-2019 Andrew Ziem
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

;  @app BleachBit NSIS Installer Script
;  @url https://nsis.sourceforge.io/Main_Page
;  @os Windows
;  @scriptversion v2.3.1020
;  @scriptdate 2019-04-02
;  @scriptby Andrew Ziem (2009-05-14 - 2019-01-21) & Tobias B. Besemer (2019-03-31 - 2019-04-02)
;  @tested ok v2.0.0, Windows 7
;  @testeddate 2019-04-01
;  @testedby https://github.com/Tobias-B-Besemer
;  @note 


;--------------------------------
;System

; Request application privileges for Windows Vista
; NsisMultiUser sets this, when needed.
; RequestExecutionLevel admin


;--------------------------------
;Include FileFunc.nsh

; FileFunc.nsh for e.g. command line arguments managment requested
; by issue #437 "Install option to skip desktop icon"
!include FileFunc.nsh


;--------------------------------
;Include Modern UI

!include MUI2.nsh


;--------------------------------
;General

; Name and file
!define COMPANY_NAME "BleachBit" ; used by NsisMultiUser
!define PRODNAME "BleachBit"
!define PRODURL "https://www.bleachbit.org"
!define BLEACHBIT_LICENSE "..\COPYING" ; keep it general
; Look at the section "License used in MUI_PAGE_LICENSE" for a Multi-Language-Solution!

Name "${prodname}"

!ifdef NoTranslations
  OutFile "${prodname}-${VERSION}-setup-English.exe"
  ; Unicode requires NSIS version 3 or later
  Unicode true
!else
  OutFile "${prodname}-${VERSION}-setup.exe"
  ; Unicode requires NSIS version 3 or later
  Unicode true
!endif

; Default installation folder
; NsisMultiUser sets the directory.
; InstallDir "$PROGRAMFILES\${prodname}"

; Get installation folder from registry if available
InstallDirRegKey HKCU "Software\${prodname}" ""


;--------------------------------
;Packing

; Best compression
; SetCompressor /SOLID lzma
; https://ci.appveyor.com/ do already "SetCompressor /FINAL zlib"

; Reserve Files
; If you are using solid compression, files that are required before
; the actual installation should be stored first in the data block,
; because this will make your installer start faster.
!insertmacro MUI_RESERVEFILE_LANGDLL


;--------------------------------
;Multi-User

; See https://github.com/Drizin/NsisMultiUser
!addplugindir /x86-ansi ".\NsisPluginsAnsi\"
!addplugindir /x86-unicode ".\NsisPluginsUnicode\"
!addincludedir ".\NsisInclude"
!include UAC.nsh
!include NsisMultiUser.nsh
!include LogicLib.nsh
!include StdUtils.nsh

!define PRODUCT_NAME "${prodname}" ; exact copy to another name for multi-user script
!define PROGEXE "${prodname}.exe"
!define MULTIUSER_INSTALLMODE_ALLOW_BOTH_INSTALLATIONS 0
!define MULTIUSER_INSTALLMODE_ALLOW_ELEVATION 1
!define MULTIUSER_INSTALLMODE_ALLOW_ELEVATION_IF_SILENT 0
!define MULTIUSER_INSTALLMODE_DEFAULT_ALLUSERS 1
!define MULTIUSER_INSTALLMODE_DEFAULT_CURRENTUSER 1
!define MULTIUSER_INSTALLMODE_64_BIT 0
!define MULTIUSER_INSTALLMODE_NO_HELP_DIALOG 1


;--------------------------------
;Interface Settings

!define MUI_ABORTWARNING

; Show all languages, despite user's codepage
!define MUI_LANGDLL_ALLLANGUAGES


;--------------------------------
;Language Selection Dialog Settings

; Remember the installer language
!define MUI_LANGDLL_REGISTRY_ROOT "HKCU"
!define MUI_LANGDLL_REGISTRY_KEY "Software\${prodname}"
!define MUI_LANGDLL_REGISTRY_VALUENAME "Installer Language"


;--------------------------------
;Languages

; Languages additionaly available in bleachbit_lang.nsh and NsisMultiUserLang.nsh are in comments
!insertmacro MUI_LANGUAGE "English"
!ifndef NoTranslations
; !insertmacro MUI_LANGUAGE "AFRIKAANS"
  !insertmacro MUI_LANGUAGE "Albanian"
  !insertmacro MUI_LANGUAGE "Arabic"
  !insertmacro MUI_LANGUAGE "Armenian"
  !insertmacro MUI_LANGUAGE "Asturian"
  !insertmacro MUI_LANGUAGE "Basque"
  !insertmacro MUI_LANGUAGE "Belarusian"
  !insertmacro MUI_LANGUAGE "Bosnian"
; !insertmacro MUI_LANGUAGE "BRETON"
  !insertmacro MUI_LANGUAGE "Bulgarian"
  !insertmacro MUI_LANGUAGE "Catalan"
; !insertmacro MUI_LANGUAGE "CORSICAN"
  !insertmacro MUI_LANGUAGE "Croatian"
  !insertmacro MUI_LANGUAGE "Czech"
  !insertmacro MUI_LANGUAGE "Danish"
  !insertmacro MUI_LANGUAGE "Dutch"
; !insertmacro MUI_LANGUAGE "ESPERANTO"
  !insertmacro MUI_LANGUAGE "Estonian"
; !insertmacro MUI_LANGUAGE "FARSI"
  !insertmacro MUI_LANGUAGE "Finnish"
  !insertmacro MUI_LANGUAGE "French"
  !insertmacro MUI_LANGUAGE "Galician"
; !insertmacro MUI_LANGUAGE "GEORGIAN"
  !insertmacro MUI_LANGUAGE "German"
  !insertmacro MUI_LANGUAGE "Greek"
  !insertmacro MUI_LANGUAGE "Hebrew"
  !insertmacro MUI_LANGUAGE "Hungarian"
; !insertmacro MUI_LANGUAGE "ICELANDIC"
  !insertmacro MUI_LANGUAGE "Indonesian"
; !insertmacro MUI_LANGUAGE "IRISH"
  !insertmacro MUI_LANGUAGE "Italian"
  !insertmacro MUI_LANGUAGE "Japanese"
  !insertmacro MUI_LANGUAGE "Korean"
  !insertmacro MUI_LANGUAGE "Kurdish"
  !insertmacro MUI_LANGUAGE "Latvian"
  !insertmacro MUI_LANGUAGE "Lithuanian"
; !insertmacro MUI_LANGUAGE "LUXEMBOURGISH"
; !insertmacro MUI_LANGUAGE "MACEDONIAN"
  !insertmacro MUI_LANGUAGE "Malay"
; !insertmacro MUI_LANGUAGE "MONGOLIAN"
  !insertmacro MUI_LANGUAGE "Norwegian"
  !insertmacro MUI_LANGUAGE "NorwegianNynorsk"
; !insertmacro MUI_LANGUAGE "PASHTO"
  !insertmacro MUI_LANGUAGE "Polish"
  !insertmacro MUI_LANGUAGE "Portuguese"
  !insertmacro MUI_LANGUAGE "PortugueseBR"
  !insertmacro MUI_LANGUAGE "Romanian"
  !insertmacro MUI_LANGUAGE "Russian"
; !insertmacro MUI_LANGUAGE "SCOTSGAELIC"
  !insertmacro MUI_LANGUAGE "Serbian"
; !insertmacro MUI_LANGUAGE "SERBIANLATIN"
  !insertmacro MUI_LANGUAGE "SimpChinese"
  !insertmacro MUI_LANGUAGE "Slovak"
  !insertmacro MUI_LANGUAGE "Slovenian"
  !insertmacro MUI_LANGUAGE "Spanish"
; !insertmacro MUI_LANGUAGE "SPANISHINTERNATIONAL"
  !insertmacro MUI_LANGUAGE "Swedish"
; !insertmacro MUI_LANGUAGE "TATAR"
  !insertmacro MUI_LANGUAGE "Thai"
  !insertmacro MUI_LANGUAGE "TradChinese"
  !insertmacro MUI_LANGUAGE "Turkish"
  !insertmacro MUI_LANGUAGE "Ukrainian"
  !insertmacro MUI_LANGUAGE "Uzbek"
  !insertmacro MUI_LANGUAGE "Vietnamese"
; !insertmacro MUI_LANGUAGE "WELSH"
!endif

!include NsisMultiUserLang.nsh

!include bleachbit_lang.nsh


;--------------------------------
;License used in MUI_PAGE_LICENSE

; For maybe later... Tobias.
; LangString BLEACHBIT_LICENSE ${LANG_ENGLISH} "..\COPYING"
; LangString BLEACHBIT_LICENSE ${LANG_FRENCH} "..\COPYING_Fre"
; LangString BLEACHBIT_LICENSE ${LANG_GERMAN} "..\COPYING_Ger"


;--------------------------------
;PageEx License

; For maybe later... Tobias.

; Translations of "License"
; LangString License_Text ${LANG_ENGLISH} "License"
; LangString License_Text ${LANG_FRENCH} "Licence"
; LangString License_Text ${LANG_GERMAN} "Lizenz"

; LicenseLangString
; Does the same as LangString only it loads the string from a text/RTF file and defines
; a special LangString that can be used only by LicenseData.
; LicenseLangString License_Data ${LANG_ENGLISH} license-english.txt
; LicenseLangString License_Data ${LANG_FRENCH} license-french.txt
; LicenseLangString License_Data ${LANG_GERMAN} license-german.txt

; LicenseData
; Specifies a text file or a RTF file to use for the license that the user can read.
; Omit this to not have a license displayed. Note that the file must be in the evil DOS text format (\r\n, yeah!).
; If you make your license file a RTF file it is recommended you edit it with WordPad and not MS Word.
; Using WordPad will result in a much smaller file.

; https://nsis.sourceforge.io/Reference/PageEx
; PageEx License
  ; LicenseText $(License_Text)
  ; LicenseData $(License_Data)
  ; LicenseForceSelection checkbox
; PageExEnd


;--------------------------------
;Command Line Variable

!define COMMAND_LINE_NO_DESKTOP_SHORTCUT "No" ; If "Yes": NO DESKTOP SHORTCUT!


;--------------------------------
;Installer Functions

Function .onInit

  ; Handle the command line parameters
  command_line:
  ${GetParameters} $R0

  ; Case: /?
  ${GetOptionsS} $R0 "/?" $R1
  ${IfNot} ${errors}
    ; SetErrorLevel 0 - normal execution (no error)
    SetErrorLevel 0
    Goto command_line_help
  ${EndIf}

  ; Case: -?
  ${GetOptionsS} $R0 "-?" $R1
  ${IfNot} ${errors}
    ; SetErrorLevel 0 - normal execution (no error)
    SetErrorLevel 0
    Goto command_line_help
  ${EndIf}

  ; Case: /h
  ${GetOptionsS} $R0 "/h" $R1
  ${IfNot} ${errors}
    ; SetErrorLevel 0 - normal execution (no error)
    SetErrorLevel 0
    Goto command_line_help
  ${EndIf}

  ; Case: -h
  ${GetOptionsS} $R0 "-h" $R1
  ${IfNot} ${errors}
    ; SetErrorLevel 0 - normal execution (no error)
    SetErrorLevel 0
    Goto command_line_help
  ${EndIf}

  ; Case: --help
  ${GetOptionsS} $R0 "--help" $R1
  ${IfNot} ${errors}
    ; SetErrorLevel 0 - normal execution (no error)
    SetErrorLevel 0
    Goto command_line_help
  ${EndIf}

  ; Case: /error-code
  ${GetOptionsS} $R0 "/error-code" $R1
  ${IfNot} ${errors}
    ; Copied from NsisMultiUser.nsh (starting line 480) and modified
    MessageBox MB_ICONINFORMATION "Error codes (decimal):$\r$\n\
      0$\t- normal execution (no error)$\r$\n\
      1$\t- (un)installation aborted by user (Cancel button)$\r$\n\
      2$\t- (un)installation aborted by script$\r$\n\
      666$\t- uninstaller had QuietUninstallString$\r$\n\
      666660$\t- invalid command-line parameters$\r$\n\
      666661$\t- elevation is not allowed by defines$\r$\n\
      666662$\t- uninstaller detected there's no installed version$\r$\n\
      666663$\t- executing uninstaller from the installer failed$\r$\n\
      666666$\t- cannot start elevated instance$\r$\n\
      other$\t- Windows error code when trying to start elevated instance$\r$\n\
      more$\t- in the documentation and on request"
    ; SetErrorLevel 0 - normal execution (no error)
    SetErrorLevel 0
    Abort
  ${EndIf}

  ; Case: (/allusers or /currentuser) (/S) /uninstall
  ; In case "${GetOptionsS} $R0":
  ${GetOptionsS} $R0 "/uninstall" $R1
  ${IfNot} ${errors}
    ${GetOptionsS} $R0 "/allusers" $R1
    ${IfNot} ${errors}
      Goto uninstall_old
    ${EndIf}
    ${GetOptionsS} $R0 "/currentuser" $R1
    ${IfNot} ${errors}
      Goto uninstall_old
    ${EndIf}
    MessageBox MB_ICONINFORMATION "Error:$\r$\n\
      $\r$\n\
      Called: (/S) /uninstall$\r$\n\
      $\r$\n\
      /uninstall:$\r$\n\
      (installer only) run uninstaller, requires '/allusers' or '/currentuser',$\r$\n\
      case-insensitive$\r$\n\
      $\r$\n\
      /allusers:$\r$\n\
      uninstall for all users, case-insensitive$\r$\n\
      $\r$\n\
      /currentuser:$\r$\n\
      uninstall for current user only, case-insensitive$\r$\n\
      $\r$\n\
      /S:$\r$\n\
      silent mode, requires '/allusers' or '/currentuser', case-sensitive"
    ; SetErrorLevel 666660 - invalid command-line parameters
    SetErrorLevel 666660
    Abort
  ${EndIf}

  ; Case: (/allusers or /currentuser) (/S) /no-desktop-shortcut (/D)
  ${GetOptionsS} $R0 "/no-desktop-shortcut" $R1
  ${IfNot} ${errors}
    ${GetOptionsS} $R0 "/S" $R1
    ${IfNot} ${errors}
      ${GetOptionsS} $R0 "/allusers" $R1
      ${IfNot} ${errors}
        Goto previous_version_check
      ${EndIf}
      ${GetOptionsS} $R0 "/currentuser" $R1
      ${IfNot} ${errors}
        Goto previous_version_check
      ${EndIf}
      Goto error_no-desktop-shortcut
    ${EndIf}
    Goto error_no-desktop-shortcut
  ${EndIf}

  ; Case: (/allusers or /currentuser) /S (/D)
  ${GetOptionsS} $R0 "/S" $R1
  ${IfNot} ${errors}
    ${GetOptionsS} $R0 "/allusers" $R1
    ${IfNot} ${errors}
      Goto previous_version_check
    ${EndIf}
    ${GetOptionsS} $R0 "/currentuser" $R1
    ${IfNot} ${errors}
      Goto previous_version_check
    ${EndIf}
    MessageBox MB_ICONINFORMATION "Error:$\r$\n\
      $\r$\n\
      Called: /S (/D)$\r$\n\
      $\r$\n\
      /S:$\r$\n\
      silent mode, requires '/allusers' or '/currentuser', case-sensitive$\r$\n\
      $\r$\n\
      /allusers:$\r$\n\
      (un)install for all users, case-insensitive$\r$\n\
      $\r$\n\
      /currentuser:$\r$\n\
      (un)install for current user only, case-insensitive$\r$\n\
      $\r$\n\
      /D:$\r$\n\
      (installer only) set install directory, must be last parameter,$\r$\n\
      without quotes, case-sensitive"
    ; SetErrorLevel 666660 - invalid command-line parameters
    SetErrorLevel 666660
    Abort
  ${EndIf}

  ; Case: /allusers
  ${GetOptionsS} $R0 "/allusers" $R1
  ${IfNot} ${errors}
    Goto previous_version_check
  ${EndIf}

  ; Case: /currentuser
  ${GetOptionsS} $R0 "/currentuser" $R1
  ${IfNot} ${errors}
    Goto previous_version_check
  ${EndIf}

  ; Case: No Parameter
  ; In case $R0 == "": (No "${GetOptionsS} $R0"!)
  ${If} $R0 == ""
    Goto previous_version_check
  ${EndIf}

  ; In case of just /D:
  ${GetOptionsS} $R0 "/D" $R1
  ${IfNot} ${errors}
    MessageBox MB_ICONINFORMATION "Error:$\r$\n\
      $\r$\n\
      Called: $R0$\r$\n\
      $\r$\n\
      /D:$\r$\n\
      (installer only) set install directory, must be last parameter, without$\r$\n\
      quotes, requires '/allusers' or '/currentuser', case-sensitive$\r$\n\
      $\r$\n\
      /S:$\r$\n\
      silent mode, requires '/allusers' or '/currentuser', case-sensitive$\r$\n\
      $\r$\n\
      /allusers:$\r$\n\
      uninstall for all users, case-insensitive$\r$\n\
      $\r$\n\
      /currentuser:$\r$\n\
      uninstall for current user only, case-insensitive"
    ; SetErrorLevel 666660 - invalid command-line parameters
    SetErrorLevel 666660
    Abort
  ${EndIf}

  ; In case of a unknow parameter:
  MessageBox MB_ICONINFORMATION "Error:$\r$\n\
    $\r$\n\
    Called: $R0$\r$\n\
    $\r$\n\
    $R0 - Unknown parameter!"
  ; SetErrorLevel 666660 - invalid command-line parameters
  SetErrorLevel 666660
  Goto command_line_help

  error_no-desktop-shortcut:
  MessageBox MB_ICONINFORMATION "Error:$\r$\n\
    $\r$\n\
    Called: (/allusers or /currentuser) (/S) /no-desktop-shortcut (/D)$\r$\n\
    $\r$\n\
    /no-desktop-shortcut:$\r$\n\
    (silent mode only) install without desktop shortcut, must be$\r$\n\
    last parameter before '/D' (if used), case-sensitive$\r$\n\
    $\r$\n\
    /S:$\r$\n\
    silent mode, requires '/allusers' or '/currentuser', case-sensitive$\r$\n\
    $\r$\n\
    /allusers:$\r$\n\
    install for all users, case-insensitive$\r$\n\
    $\r$\n\
    /currentuser:$\r$\n\
    install for current user only, case-insensitive$\r$\n\
    $\r$\n\
    /D:$\r$\n\
    (installer only) set install directory, must be last parameter,$\r$\n\
    without quotes, case-sensitive"
  ; SetErrorLevel 666660 - invalid command-line parameters
  SetErrorLevel 666660
  Abort

  command_line_help:
  ; Copied from NsisMultiUser.nsh (starting line 480) and modified
  MessageBox MB_ICONINFORMATION "Usage:$\r$\n\
    $\r$\n\
    /allusers:$\r$\n\
    (un)install for all users, case-insensitive$\r$\n\
    $\r$\n\
    /currentuser:$\r$\n\
    (un)install for current user only, case-insensitive$\r$\n\
    $\r$\n\
    /uninstall:$\r$\n\
    (installer only) run uninstaller, requires '/allusers' or '/currentuser',$\r$\n\
    case-insensitive$\r$\n\
    $\r$\n\
    /S:$\r$\n\
    silent mode, requires '/allusers' or '/currentuser', case-sensitive$\r$\n\
    $\r$\n\
    /no-desktop-shortcut:$\r$\n\
    (silent mode only) install without desktop shortcut, must be$\r$\n\
    last parameter before '/D' (if used), case-sensitive$\r$\n\
    $\r$\n\
    /D:$\r$\n\
    (installer only) set install directory, must be last parameter,$\r$\n\
    without quotes, case-sensitive$\r$\n\
    $\r$\n\
    /error-code:$\r$\n\
    the error codes the program gives back$\r$\n\
    $\r$\n\
    /?:$\r$\n\
    display this message"
  Abort

  previous_version_check:
  ; Check whether application is already installed
  ReadRegStr $R0 HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${prodname}" \
    "UninstallString"
  ; If not already installed, skip uninstallation
  StrCmp $R0 "" new_install
  Goto upgrade_uninstall_msg

  upgrade_uninstall_msg:
  MessageBox MB_OKCANCEL|MB_ICONEXCLAMATION "$(BLEACHBIT_UPGRADE_UNINSTALL)" /SD IDOK IDOK uninstall_old
  ; SetErrorLevel 2 - (un)installation aborted by script
  SetErrorLevel 2
  Abort

  uninstall_old:
  ; If installing in silent mode, also uninstall in silent mode
  Var /GLOBAL uninstaller_cmd
  StrCpy $uninstaller_cmd "$R0 _?=$INSTDIR"
  IfSilent 0 +2
  StrCpy $uninstaller_cmd "$uninstaller_cmd /S"
  ; Actually run the uninstaller and SetErrorLevel (needed to restore QuietUninstallString)
  ExecWait $uninstaller_cmd ${ERRORLEVEL}
  ; ErrorLevel = 1 - uninstallation aborted by user (Cancel button)
  ; ErrorLevel = 2 - uninstallation aborted by script
  ; Debug-Box:
  MessageBox MB_ICONINFORMATION "ErrorLevel: ${ERRORLEVEL}"
  ${If} ${ERRORLEVEL} == "1"
  ${OrIf} ${ERRORLEVEL} == "2"
    Abort
  ${EndIf}
  ${If} $R0 == "/uninstall"
    Abort
  ${EndIf}
  Goto new_install

  new_install:
  Goto end

  end:
FunctionEnd
; And now starts the GUI Installer...


;--------------------------------
;Function RefreshShellIcons

; http://nsis.sourceforge.net/RefreshShellIcons
Function RefreshShellIcons
  !define SHCNE_ASSOCCHANGED 0x08000000
  !define SHCNF_IDLIST 0
  System::Call 'shell32.dll::SHChangeNotify(i, i, i, i) v (${SHCNE_ASSOCCHANGED}, ${SHCNF_IDLIST}, 0, 0)'
FunctionEnd


;--------------------------------
;Pages

; Installer:
  ; !insertmacro MUI_PAGE_WELCOME
  !insertmacro MUI_PAGE_LICENSE "$(BLEACHBIT_LICENSE)"
  !insertmacro MULTIUSER_PAGE_INSTALLMODE
  !insertmacro MUI_PAGE_DIRECTORY
  !insertmacro MUI_PAGE_COMPONENTS
  !insertmacro MUI_PAGE_INSTFILES

  !define MUI_FINISHPAGE_NOAUTOCLOSE
  !define MUI_FINISHPAGE_RUN "$INSTDIR\${prodname}.exe"
  !define MUI_FINISHPAGE_LINK "$(BLEACHBIT_MUI_FINISHPAGE_LINK)"
  !define MUI_FINISHPAGE_LINK_LOCATION "$(PRODURL)"
  !insertmacro MUI_PAGE_FINISH

; Uninstaller:
  ; !insertmacro MUI_UNPAGE_WELCOME
  !insertmacro MULTIUSER_UNPAGE_INSTALLMODE
  !insertmacro MUI_UNPAGE_CONFIRM
  ; !insertmacro MUI_UNPAGE_COMPONENTS
  !insertmacro MUI_UNPAGE_INSTFILES
  ; !insertmacro MUI_UNPAGE_FINISH


;--------------------------------
;Insert Macro

; MUI_LANGUAGE[EX] should be inserted after the MUI_[UN]PAGE_* macros!

; Language display dialog
!insertmacro MUI_LANGDLL_DISPLAY

!insertmacro MULTIUSER_INIT


;--------------------------------
;Descriptions for the Installer Components

;USE A LANGUAGE STRING IF YOU WANT YOUR DESCRIPTIONS TO BE LANGAUGE SPECIFIC

;Assign descriptions to sections
!insertmacro MUI_FUNCTION_DESCRIPTION_BEGIN
  !insertmacro MUI_DESCRIPTION_TEXT ${SectionCore} $(BLEACHBIT_COMPONENT_CORE_DESCRIPTION)
  !insertmacro MUI_DESCRIPTION_TEXT ${SectionShortcuts} $(BLEACHBIT_COMPONENTGROUP_SHORTCUTS_DESCRIPTION)
  !insertmacro MUI_DESCRIPTION_TEXT ${SectionStartMenu} $(BLEACHBIT_COMPONENT_STARTMENU_DESCRIPTION)
  !insertmacro MUI_DESCRIPTION_TEXT ${SectionDesktop} $(BLEACHBIT_COMPONENT_DESKTOP_DESCRIPTION)
  !insertmacro MUI_DESCRIPTION_TEXT ${SectionQuickLaunch} $(BLEACHBIT_COMPONENT_QUICKLAUNCH_DESCRIPTION)
  !insertmacro MUI_DESCRIPTION_TEXT ${SectionAutostart} $(BLEACHBIT_COMPONENT_AUTOSTART_DESCRIPTION)
  !insertmacro MUI_DESCRIPTION_TEXT ${SectionTranslations} $(BLEACHBIT_COMPONENT_TRANSLATIONS_DESCRIPTION)
  !insertmacro MUI_DESCRIPTION_TEXT ${SectionShred} $(BLEACHBIT_COMPONENT_INTEGRATESHRED_DESCRIPTION)
!insertmacro MUI_FUNCTION_DESCRIPTION_END


;--------------------------------
;Installer Section

; BleachBit Core
Section "$(BLEACHBIT_COMPONENT_CORE_TITLE)" SectionCore ; (Required)
  ; "SectionIn RO" means: Section defined mandatory, so that the user can not unselect them!
  SectionIn RO

  ; Copy files
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

  ; Write uninstaller
  WriteUninstaller "$INSTDIR\uninstall.exe"

  ; Register uninstaller in Add/Remove Programs
  !insertmacro MULTIUSER_RegistryAddInstallInfo ; add registry keys
  WriteRegStr SHCTX "${MULTIUSER_INSTALLMODE_UNINSTALL_REGISTRY_KEY_PATH}" \
    "HelpLink" "https://www.bleachbit.org/help"
  WriteRegStr SHCTX "${MULTIUSER_INSTALLMODE_UNINSTALL_REGISTRY_KEY_PATH}" \
    "URLInfoAbout" "https://www.bleachbit.org/"
  WriteRegStr SHCTX "${MULTIUSER_INSTALLMODE_UNINSTALL_REGISTRY_KEY_PATH}" \
    "URLUpdateInfo" "https://www.bleachbit.org/download"
  WriteRegStr SHCTX "${MULTIUSER_INSTALLMODE_UNINSTALL_REGISTRY_KEY_PATH}$0" \
    "HelpLink" "https://www.bleachbit.org/help"
  WriteRegStr SHCTX "${MULTIUSER_INSTALLMODE_UNINSTALL_REGISTRY_KEY_PATH}$0" \
    "URLInfoAbout" "https://www.bleachbit.org/"
  WriteRegStr SHCTX "${MULTIUSER_INSTALLMODE_UNINSTALL_REGISTRY_KEY_PATH}$0" \
    "URLUpdateInfo" "https://www.bleachbit.org/download"

  ; Restore QuietUninstallString
  ${if} ${ERRORLEVEL} == "666"
    ${if} $MultiUser.InstallMode == "AllUsers" ; setting defaults
      ReadRegStr $7 SHCTX "${MULTIUSER_INSTALLMODE_UNINSTALL_REGISTRY_KEY_PATH}" "UninstallString"
      WriteRegStr SHCTX "${MULTIUSER_INSTALLMODE_UNINSTALL_REGISTRY_KEY_PATH}" \
        "QuietUninstallString" "$7"
      DeleteRegValue SHCTX "${MULTIUSER_INSTALLMODE_UNINSTALL_REGISTRY_KEY_PATH}" "UninstallString"
    ${else}
      ReadRegStr $7 SHCTX "${MULTIUSER_INSTALLMODE_UNINSTALL_REGISTRY_KEY_PATH}$0" "UninstallString"
      WriteRegStr SHCTX "${MULTIUSER_INSTALLMODE_UNINSTALL_REGISTRY_KEY_PATH}$0" \
        "QuietUninstallString" "$7"
      DeleteRegValue SHCTX "${MULTIUSER_INSTALLMODE_UNINSTALL_REGISTRY_KEY_PATH}$0" "UninstallString"
    ${endif}
  ${endif}
SectionEnd

; BleachBit Shortcuts
SectionGroup /e "$(BLEACHBIT_COMPONENTGROUP_SHORTCUTS_TITLE)" SectionShortcuts
  ; BleachBit Start Menu Shortcuts
  Section "$(BLEACHBIT_COMPONENT_STARTMENU_TITLE)" SectionStartMenu
    SetOutPath "$INSTDIR\" ; this affects CreateShortCut's 'Start in' directory
    CreateDirectory "$SMPROGRAMS\${prodname}"
    CreateShortCut "$SMPROGRAMS\${prodname}\${prodname}.lnk" \
      "$INSTDIR\${prodname}.exe"
    CreateShortCut "$SMPROGRAMS\${prodname}\${prodname} $(BLEACHBIT_COMPONENT_STARTMENU_LINK_NO_UAC).lnk" \
      "$INSTDIR\${prodname}.exe" \
      "--no-uac --gui"
    CreateShortCut "$SMPROGRAMS\${prodname}\${prodname} $(BLEACHBIT_COMPONENT_STARTMENU_LINK_DEBUGGING_TERMINAL).lnk" \
      "$INSTDIR\${prodname}_console.exe"
    WriteINIStr "$SMPROGRAMS\${prodname}\${prodname} $(BLEACHBIT_COMPONENT_STARTMENU_LINK_HOME_PAGE).url" \
      "InternetShortcut" "URL" "https://www.bleachbit.org/"
    CreateShortCut "$SMPROGRAMS\${prodname}\${prodname} $(BLEACHBIT_COMPONENT_STARTMENU_LINK_UNINSTALL).lnk" \
      "$INSTDIR\uninstall.exe"
    Call RefreshShellIcons
  SectionEnd

  ; BleachBit Desktop Shortcut
  Section "$(BLEACHBIT_COMPONENT_DESKTOP_TITLE)" SectionDesktop
    ; Checking for COMMAND_LINE_NO_DESKTOP_SHORTCUT. It's "No" by default. If "Yes": NO DESKTOP SHORTCUT!
    ${if} ${COMMAND_LINE_NO_DESKTOP_SHORTCUT} == "No"
      SetOutPath "$INSTDIR\" ; this affects CreateShortCut's 'Start in' directory
      CreateShortcut "$DESKTOP\BleachBit.lnk" "$INSTDIR\${prodname}.exe"
      Call RefreshShellIcons
    ${endif}
  SectionEnd

  ; BleachBit Quick Launch Shortcut
  Section /o "$(BLEACHBIT_COMPONENT_QUICKLAUNCH_TITLE)" SectionQuickLaunch
    SetOutPath "$INSTDIR\" ; this affects CreateShortCut's 'Start in' directory
    CreateShortcut "$QUICKLAUNCH\BleachBit.lnk" "$INSTDIR\${prodname}.exe"
    Call RefreshShellIcons
  SectionEnd

  Section /o "$(BLEACHBIT_COMPONENT_AUTOSTART_TITLE)" SectionAutostart
    SetOutPath "$INSTDIR\" ; this affects CreateShortCut's 'Start in' directory
    CreateShortcut "$SMSTARTUP\BleachBit.lnk" "$INSTDIR\${prodname}.exe"
    Call RefreshShellIcons
  SectionEnd
SectionGroupEnd

; BleachBit Translations
!ifndef NoTranslations
Section "$(BLEACHBIT_COMPONENT_TRANSLATIONS_TITLE)" SectionTranslations
  SetOutPath $INSTDIR\share\locale
  File /r "..\dist\share\locale\*.*"
SectionEnd
!endif

;Section for making Shred Integration Optional
!ifndef NoSectionShred
Section "$(BLEACHBIT_COMPONENT_INTEGRATESHRED_TITLE)" SectionShred
  ; register file association verb
  WriteRegStr HKCR "AllFileSystemObjects\shell\shred.bleachbit" "" "$(BLEACHBIT_SHELL_TITLE)"
  WriteRegStr HKCR "AllFileSystemObjects\shell\shred.bleachbit" "Icon" "$INSTDIR\bleachbit.exe"
  WriteRegStr HKCR "AllFileSystemObjects\shell\shred.bleachbit\command" "" '"$INSTDIR\bleachbit.exe" --gui --no-uac --shred "%1"'
SectionEnd
!endif

; Keep this section last. It must be last because that is when the
; actual size is known.
; This is a hidden section.
Section "-Write Install Size"
  !insertmacro MULTIUSER_RegistryAddInstallSizeInfo
SectionEnd


;--------------------------------
;Uninstaller Section

UninstallText $(BLEACHBIT_UNINSTALLTEXT)

Section "Uninstall"
  RMDir /r "$INSTDIR"
  DeleteRegKey HKCU "Software\${prodname}"
  ; Delete normal shortcuts
  RMDir /r "$SMPROGRAMS\${prodname}"
  ; Delete any extra shortcuts
  Delete "$DESKTOP\BleachBit.lnk"
  Delete "$QUICKLAUNCH\BleachBit.lnk"
  Delete "$SMSTARTUP\BleachBit.lnk"
  ; Remove file association
  DeleteRegKey HKCR "AllFileSystemObjects\shell\shred.bleachbit"
  ; Check for QuietUninstallString and SetErrorLevel 666
  ClearErrors
  ReadRegStr $5 SHCTX "${MULTIUSER_INSTALLMODE_UNINSTALL_REGISTRY_KEY_PATH}" "QuietUninstallString"
  IfErrors 0 +3
  ReadRegStr $5 SHCTX "${MULTIUSER_INSTALLMODE_UNINSTALL_REGISTRY_KEY_PATH}$0" "QuietUninstallString"
  IfErrors +2 0
  SetErrorLevel 666
  ; Remove the uninstaller from registry as the very last step.
  ; If something goes wrong, let the user run it again.
  !insertmacro MULTIUSER_RegistryRemoveInstallInfo
SectionEnd


;--------------------------------
;Uninstaller Functions

Function un.onInit

  !insertmacro MULTIUSER_UNINIT

  !insertmacro MUI_UNGETLANGUAGE

FunctionEnd
