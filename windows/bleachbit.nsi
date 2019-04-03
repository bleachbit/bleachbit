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
;  @scriptversion v2.3.1041
;  @scriptdate 2019-04-03
;  @scriptby Andrew Ziem (2009-05-14 - 2019-01-21) & Tobias B. Besemer (2019-03-31 - 2019-04-03)
;  @tested ok v2.3.1040, Windows 7
;  @testeddate 2019-04-03
;  @testedby https://github.com/Tobias-B-Besemer
;  @note 


;--------------------------------
;General defines

!define COMPANY_NAME "BleachBit" ; used by NsisMultiUser
!define PRODNAME "BleachBit"
!define UNINSTALL_FILENAME "uninstall.exe" ; suggested by NsisMultiUser
!define PRODURL "https://www.bleachbit.org"
!define BLEACHBIT_LICENSE "..\COPYING" ; keep it general
; Look at the section "License used in MUI_PAGE_LICENSE" for a Multi-Language-Solution!


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
; alaways requires elevation when there's per-machine installation in order to remove it first.
!define MULTIUSER_INSTALLMODE_ALLOW_BOTH_INSTALLATIONS 1

; An option (MULTIUSER_INSTALLMODE_ALLOW_ELEVATION) defines whether elevation if allowed.
; If elevation is disabled, the per-machine option becomes available only if the (un)installer
; is started elevated from Windows and is disabled otherwise.
!define MULTIUSER_INSTALLMODE_ALLOW_ELEVATION 1

!define MULTIUSER_INSTALLMODE_ALLOW_ELEVATION_IF_SILENT 0
!define MULTIUSER_INSTALLMODE_DEFAULT_ALLUSERS 1
!define MULTIUSER_INSTALLMODE_DEFAULT_CURRENTUSER 0
!define MULTIUSER_INSTALLMODE_64_BIT 0
!define MULTIUSER_INSTALLMODE_NO_HELP_DIALOG 1
!define MULTIUSER_INSTALLMODE_INSTDIR "${prodname}"


;--------------------------------
;Packing

; Best compression
; SetCompressor /SOLID lzma
; https://ci.appveyor.com/ do already "SetCompressor /FINAL zlib"

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

!ifdef NoSectionShred
  ; Definded but not used!
!endif


;--------------------------------
;AddPluginDir MultiUser

; See: https://github.com/Drizin/NsisMultiUser
!addplugindir /x86-ansi ".\NsisPluginsAnsi\"
!addplugindir /x86-unicode ".\NsisPluginsUnicode\"
!addincludedir ".\NsisInclude"


;--------------------------------
;Reserve Files

; If you are using solid compression, files that are required before
; the actual installation should be stored first in the data block,
; because this will make your installer start faster.
!insertmacro MUI_RESERVEFILE_LANGDLL


;--------------------------------
;System

; Request application privileges for Windows Vista:
; NsisMultiUser sets this, when needed.
; RequestExecutionLevel admin

; Default installation folder
; NsisMultiUser sets the directory.
; InstallDir "$PROGRAMFILES\${prodname}"

; Get installation folder from registry if available
InstallDirRegKey HKCU "Software\${prodname}" ""


;--------------------------------
;Include FileFunc.nsh

; FileFunc.nsh for e.g. command line arguments managment requested
; by issue #437 "Install option to skip desktop icon"
!include FileFunc.nsh


;--------------------------------
;Include Modern UI

!include MUI2.nsh


;--------------------------------
;Include MultiUser

; See: https://github.com/Drizin/NsisMultiUser
!include UAC.nsh
!include NsisMultiUser.nsh
!include LogicLib.nsh
!include StdUtils.nsh


;--------------------------------
;Pages

; Installer:
!define MUI_WELCOMEFINISHPAGE_BITMAP "bleachbit_164x314.bmp"
!define MUI_HEADERIMAGE_BITMAP "bleachbit_150x57.bmp"
!insertmacro MUI_PAGE_WELCOME
!define MUI_LICENSEPAGE_RADIOBUTTONS
!insertmacro MUI_PAGE_LICENSE "${BLEACHBIT_LICENSE}"
!insertmacro MULTIUSER_PAGE_INSTALLMODE
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_COMPONENTS
!insertmacro MUI_PAGE_INSTFILES
!define MUI_FINISHPAGE_NOAUTOCLOSE
!define MUI_FINISHPAGE_RUN "$INSTDIR\${prodname}.exe"
!define MUI_FINISHPAGE_LINK "$(BLEACHBIT_MUI_FINISHPAGE_LINK)"
!define MUI_FINISHPAGE_LINK_LOCATION "${PRODURL}"
!define MUI_FINISHPAGE_NOREBOOTSUPPORT
!insertmacro MUI_PAGE_FINISH

; Uninstaller:
!define MUI_UNWELCOMEFINISHPAGE_BITMAP "bleachbit_164x314.bmp"
!define MUI_HEADERIMAGE_UNBITMAP "bleachbit_150x57.bmp"
!insertmacro MUI_UNPAGE_WELCOME
!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MULTIUSER_UNPAGE_INSTALLMODE
; MUI_UNPAGE_DIRECTORY not needed, ATM.
; !insertmacro MUI_UNPAGE_DIRECTORY
!insertmacro MUI_UNPAGE_COMPONENTS
!insertmacro MUI_UNPAGE_INSTFILES
!define MUI_UNFINISHPAGE_NOAUTOCLOSE
!insertmacro MUI_UNPAGE_FINISH

; MUI_LANGUAGE[EX] should be inserted after the MUI_[UN]PAGE_* macros!


;--------------------------------
;Interface Settings

; Show a message box with a warning when the user wants to close the installer:
!define MUI_ABORTWARNING
!define MUI_ABORTWARNING_CANCEL_DEFAULT
!define MUI_UNABORTWARNING
!define MUI_UNABORTWARNING_CANCEL_DEFAULT

; Show all languages, despite user's codepage:
; https://nsis.sourceforge.io/Why_does_the_language_selection_dialog_hide_some_languages
!define MUI_LANGDLL_ALLLANGUAGES


;--------------------------------
;Language Selection Dialog Settings

; Better not doing that, or the user can never ever change his language!
; OK, we give it with the new code a try again... ^^
; Seems to doesn't work! At least at Windows 7, 64-bit!
; No Registry Key HKCU\Software\${prodname}!

; Remember the installer language
!define MUI_LANGDLL_REGISTRY_ROOT "HKCU"
!define MUI_LANGDLL_REGISTRY_KEY "Software\${prodname}"
!define MUI_LANGDLL_REGISTRY_VALUENAME "Installer Language"


;--------------------------------
;Languages

; MUI_LANGUAGE[EX] should be inserted after the MUI_[UN]PAGE_* macros!

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
;Macro/Function "Uninstall"

; We need to move the code from Section "Uninstall" into a function that he can
; be executed from command line with /uninstall, too.
; As we only can call functions starting with "un." from the uninstaller section,
; and only functions without "un." from the installer section, we have to move the
; funtion into a macro.

!macro uninstallmacro un
  Function ${un}uninstallfunction
    ; Core:
    RMDir /r "$INSTDIR"
    DeleteRegKey HKCU "Software\${prodname}"

    ; Use SetShellVarContext to use the right folders.
    ; See: https://nsis.sourceforge.io/Reference/SetShellVarContext
    ${if} $MultiUser.InstallMode == "AllUsers" ; setting defaults
      SetShellVarContext all
    ${else}
      SetShellVarContext current
    ${endif}

    ; Delete normal, Start menu shortcuts
    RMDir /r "$SMPROGRAMS\${prodname}"

    ; Delete Desktop shortcut
    Delete "$DESKTOP\BleachBit.lnk"

    ; Delete Quick launch shortcut
    Delete "$QUICKLAUNCH\BleachBit.lnk"

    ; Delete Autostart shortcut
    Delete "$SMSTARTUP\BleachBit.lnk"

    ; Remove file association (Shredder)
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

    ; Remove the uninstaller from registry as the very last step - if sth. goes wrong, let the user run it again
    !insertmacro MULTIUSER_RegistryRemoveInstallInfo 

    ; And in the example follows after that:
    Delete "$INSTDIR\${UNINSTALL_FILENAME}"
    RMDir "$INSTDIR"
  FunctionEnd
!macroend

; Insert function as an installer and uninstaller function:
!insertmacro uninstallmacro ""
!insertmacro uninstallmacro "un."


;--------------------------------
;Installer Functions

Function .onInit
  ; Command line variable:
  ; If "Yes": NO DESKTOP SHORTCUT!
  Var /GLOBAL COMMAND_LINE_NO_DESKTOP_SHORTCUT
  StrCpy $COMMAND_LINE_NO_DESKTOP_SHORTCUT "No"

  ; Get the command line parameters...
  ${GetParameters} $R0

  ; ...and handle the command line parameters...

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

  ; Case: /error-codes
  ${GetOptionsS} $R0 "/error-codes" $R1
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
      Goto inseringmacros
    ${EndIf}
    ${GetOptionsS} $R0 "/currentuser" $R1
    ${IfNot} ${errors}
      Goto inseringmacros
    ${EndIf}
    MessageBox MB_ICONINFORMATION "Error:$\r$\n\
      $\r$\n\
      Called: (/S) /uninstall$\r$\n\
      $\r$\n\
      '/uninstall':$\r$\n\
      (installer only) run uninstaller, requires '/allusers' or '/currentuser',$\r$\n\
      case-insensitive$\r$\n\
      $\r$\n\
      '/allusers':$\r$\n\
      uninstall for all users, case-insensitive$\r$\n\
      $\r$\n\
      '/currentuser':$\r$\n\
      uninstall for current user only, case-insensitive$\r$\n\
      $\r$\n\
      '/S':$\r$\n\
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
        StrCpy $COMMAND_LINE_NO_DESKTOP_SHORTCUT "Yes"
        Goto previous_version_check
      ${EndIf}
      ${GetOptionsS} $R0 "/currentuser" $R1
      ${IfNot} ${errors}
        StrCpy $COMMAND_LINE_NO_DESKTOP_SHORTCUT "Yes"
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
      '/S':$\r$\n\
      silent mode, requires '/allusers' or '/currentuser', case-sensitive$\r$\n\
      $\r$\n\
      '/allusers':$\r$\n\
      (un)install for all users, case-insensitive$\r$\n\
      $\r$\n\
      '/currentuser':$\r$\n\
      (un)install for current user only, case-insensitive$\r$\n\
      $\r$\n\
      '/D':$\r$\n\
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

  ; In case of just /D:
  ${GetOptionsS} $R0 "/D" $R1
  ${IfNot} ${errors}
    MessageBox MB_ICONINFORMATION "Error:$\r$\n\
      $\r$\n\
      Called: $R0$\r$\n\
      $\r$\n\
      '/D':$\r$\n\
      (installer only) set install directory, must be last parameter, without$\r$\n\
      quotes, requires '/allusers' or '/currentuser', case-sensitive$\r$\n\
      $\r$\n\
      '/S':$\r$\n\
      silent mode, requires '/allusers' or '/currentuser', case-sensitive$\r$\n\
      $\r$\n\
      '/allusers':$\r$\n\
      uninstall for all users, case-insensitive$\r$\n\
      $\r$\n\
      '/currentuser':$\r$\n\
      uninstall for current user only, case-insensitive"
    ; SetErrorLevel 666660 - invalid command-line parameters
    SetErrorLevel 666660
    Abort
  ${EndIf}

  ; Case: No Parameter
  ; In case $R0 == "": (No "${GetOptionsS} $R0"!)
  ${If} $R0 == ""
    Goto previous_version_check
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
    '/no-desktop-shortcut':$\r$\n\
    (silent mode only) install without desktop shortcut, must be$\r$\n\
    last parameter before '/D' (if used), case-sensitive$\r$\n\
    $\r$\n\
    '/S':$\r$\n\
    silent mode, requires '/allusers' or '/currentuser', case-sensitive$\r$\n\
    $\r$\n\
    '/allusers':$\r$\n\
    install for all users, case-insensitive$\r$\n\
    $\r$\n\
    '/currentuser':$\r$\n\
    install for current user only, case-insensitive$\r$\n\
    $\r$\n\
    '/D':$\r$\n\
    (installer only) set install directory, must be last parameter,$\r$\n\
    without quotes, case-sensitive"
  ; SetErrorLevel 666660 - invalid command-line parameters
  SetErrorLevel 666660
  Abort

  command_line_help:
  ; Copied from NsisMultiUser.nsh (starting line 480) and modified
  MessageBox MB_ICONINFORMATION "Usage:$\r$\n\
    $\r$\n\
    '/allusers':$\r$\n\
    (un)install for all users, case-insensitive$\r$\n\
    $\r$\n\
    '/currentuser':$\r$\n\
    (un)install for current user only, case-insensitive$\r$\n\
    $\r$\n\
    '/uninstall':$\r$\n\
    (installer only) run uninstaller, requires '/allusers' or '/currentuser',$\r$\n\
    case-insensitive$\r$\n\
    $\r$\n\
    '/S':$\r$\n\
    silent mode, requires '/allusers' or '/currentuser', case-sensitive$\r$\n\
    $\r$\n\
    '/no-desktop-shortcut':$\r$\n\
    (silent mode only) install without desktop shortcut, must be last$\r$\n\
    parameter before '/D' (if used), case-sensitive$\r$\n\
    $\r$\n\
    '/D':$\r$\n\
    (installer only) set install directory, must be last parameter, without$\r$\n\
    quotes, case-sensitive$\r$\n\
    $\r$\n\
    '/error-codes':$\r$\n\
    the error codes the program gives back$\r$\n\
    $\r$\n\
    '/?':$\r$\n\
    display this message"
  Abort

  previous_version_check: ; and uninstall old
  ; Check whether application is already installed
  ; Wow6432Node is e.g. used on Windows 7 64-bit for 32-bit programs
  ReadRegStr $R1 HKLM "SOFTWARE\Wow6432Node\Microsoft\Windows\CurrentVersion\Uninstall\${prodname}" "UninstallString"
  IfErrors 0 +10
  ReadRegStr $R1 HKLM "SOFTWARE\Wow6432Node\Microsoft\Windows\CurrentVersion\Uninstall\${prodname}" "QuietUninstallString"
  IfErrors 0 +8
  ReadRegStr $R1 HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${prodname}" "UninstallString"
  IfErrors 0 +6
  ReadRegStr $R1 HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${prodname}" "QuietUninstallString"
  IfErrors 0 +4
  ReadRegStr $R1 HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\${prodname}" "UninstallString"
  IfErrors 0 +2
  ReadRegStr $R1 HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\${prodname}" "QuietUninstallString"
  ; If not already installed, skip uninstallation
  StrCmp $R1 "" no_uninstall_possible
  ; Save the uninstaller for later:
  Var /GLOBAL uninstaller_cmd
  StrCpy $uninstaller_cmd "$R1"
  ; We also need the InstallLocation:
  ReadRegStr $R2 HKLM "SOFTWARE\Wow6432Node\Microsoft\Windows\CurrentVersion\Uninstall\${prodname}" "InstallLocation"
  IfErrors 0 +4
  ReadRegStr $R2 HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${prodname}" "InstallLocation"
  IfErrors 0 +2
  ReadRegStr $R2 HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\${prodname}" "InstallLocation"
  Var /GLOBAL uninstaller_path
  StrCpy $uninstaller_path "$R2"
  StrCmp $uninstaller_path "" 0 +3
  ; If not set, we have a problem... ^^ (...but BleachBit set it normaly.)
  StrCpy $uninstaller_path "$%Temp%"
  MessageBox MB_OKCANCEL|MB_ICONEXCLAMATION "$(BLEACHBIT_UPGRADE_UNINSTALL)" /SD IDOK IDOK true IDCANCEL false
  false:
  ; SetErrorLevel 1 - (un)installation aborted by user (Cancel button)
  SetErrorLevel 1
  Abort
  true:
  ; If installing in silent mode, also uninstall in silent mode
  IfSilent 0 +2
  StrCpy $uninstaller_cmd "$uninstaller_cmd /S"
  ; Run the old uninstaller and SetErrorLevel (needed to restore QuietUninstallString):
  StrCpy $uninstaller_cmd "$uninstaller_cmd _?=$uninstaller_path"
  ExecWait $uninstaller_cmd $R6
  Var /GLOBAL ErrorLevel
  StrCpy $ErrorLevel "$R6"
  ; ErrorLevel = 1 - uninstallation aborted by user (Cancel button)
  ; ErrorLevel = 2 - uninstallation aborted by script
  ; ErrorLevel = 666 - installation was with QuietUninstallString
  MessageBox MB_ICONINFORMATION "ErrorLevel: $R6 / $ErrorLevel / $R0" ; Debug-Box
  ${If} $ErrorLevel == "1"
  ${OrIf} $ErrorLevel == "2"
    Abort
  ${EndIf}
  ; ErrorLevel = 666 do we handle later!
  Goto inseringmacros

  no_uninstall_possible:
  ; If BleachBit is installed - we can't detect it, ATM!
  ; Move on! ^^

  inseringmacros:
  ; It starts the GUI and loads the Installer Sections...
  ; Insering the macros at the end that they don't effect the error messages of the command line.

  ; Insert Macro MULTIUSER_INIT:
  ; Must be loaded after "!insertmacro MULTIUSER_PAGE_INSTALLMODE"!
  ; Command Call not valid outside Section or Function!
  !insertmacro MULTIUSER_INIT

  ; Insert Macro MUI_LANGDLL_DISPLAY:
  ; This is the language display dialog!
  ; MUI_LANGDLL_DISPLAY should only be used after inserting the MUI_LANGUAGE macro(s)!
  ; Command IfSilent not valid outside Section or Function!
  !insertmacro MUI_LANGDLL_DISPLAY

  ; But first handle this case: /allusers or /currentuser (/S) /uninstall
  ${GetOptionsS} $R0 "/uninstall" $R1
  ${IfNot} ${errors}
    Call uninstallfunction
    Abort
  ${EndIf}
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
;Installer Sections

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
  ${if} $MultiUser.InstallMode == "AllUsers" ; setting defaults
    WriteRegStr SHCTX "${MULTIUSER_INSTALLMODE_UNINSTALL_REGISTRY_KEY_PATH}" \
      "HelpLink" "https://www.bleachbit.org/help"
    WriteRegStr SHCTX "${MULTIUSER_INSTALLMODE_UNINSTALL_REGISTRY_KEY_PATH}" \
      "URLInfoAbout" "https://www.bleachbit.org/"
    WriteRegStr SHCTX "${MULTIUSER_INSTALLMODE_UNINSTALL_REGISTRY_KEY_PATH}" \
      "URLUpdateInfo" "https://www.bleachbit.org/download"
    WriteRegDWORD SHCTX "${MULTIUSER_INSTALLMODE_UNINSTALL_REGISTRY_KEY_PATH}" \
      "NoModify" 0
  ${else}
    WriteRegStr SHCTX "${MULTIUSER_INSTALLMODE_UNINSTALL_REGISTRY_KEY_PATH}$0" \
      "HelpLink" "https://www.bleachbit.org/help"
    WriteRegStr SHCTX "${MULTIUSER_INSTALLMODE_UNINSTALL_REGISTRY_KEY_PATH}$0" \
      "URLInfoAbout" "https://www.bleachbit.org/"
    WriteRegStr SHCTX "${MULTIUSER_INSTALLMODE_UNINSTALL_REGISTRY_KEY_PATH}$0" \
      "URLUpdateInfo" "https://www.bleachbit.org/download"
    WriteRegDWORD SHCTX "${MULTIUSER_INSTALLMODE_UNINSTALL_REGISTRY_KEY_PATH}$0" \
      "NoModify" 0
  ${endif}

  ; Restore QuietUninstallString
  ${if} $ErrorLevel == "666"
    ${if} $MultiUser.InstallMode == "AllUsers" ; setting defaults
      ReadRegStr $7 SHCTX "${MULTIUSER_INSTALLMODE_UNINSTALL_REGISTRY_KEY_PATH}" "UninstallString"
      WriteRegStr SHCTX "${MULTIUSER_INSTALLMODE_UNINSTALL_REGISTRY_KEY_PATH}" "QuietUninstallString" "$7"
      DeleteRegValue SHCTX "${MULTIUSER_INSTALLMODE_UNINSTALL_REGISTRY_KEY_PATH}" "UninstallString"
    ${else}
      ReadRegStr $7 SHCTX "${MULTIUSER_INSTALLMODE_UNINSTALL_REGISTRY_KEY_PATH}$0" "UninstallString"
      WriteRegStr SHCTX "${MULTIUSER_INSTALLMODE_UNINSTALL_REGISTRY_KEY_PATH}$0" "QuietUninstallString" "$7"
      DeleteRegValue SHCTX "${MULTIUSER_INSTALLMODE_UNINSTALL_REGISTRY_KEY_PATH}$0" "UninstallString"
    ${endif}
  ${endif}
SectionEnd

; BleachBit Shortcuts
SectionGroup /e "$(BLEACHBIT_COMPONENTGROUP_SHORTCUTS_TITLE)" SectionShortcuts
  ; Use SetShellVarContext to use the right folders.
  ; See: https://nsis.sourceforge.io/Reference/SetShellVarContext
  ${if} $MultiUser.InstallMode == "AllUsers" ; setting defaults
    SetShellVarContext all
  ${else}
    SetShellVarContext current
  ${endif}

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
    ${if} $COMMAND_LINE_NO_DESKTOP_SHORTCUT == "No"
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

  ; BleachBit Autostart Shortcut
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
    WriteRegStr HKCR "AllFileSystemObjects\shell\shred.bleachbit" "Icon" "$INSTDIR\bleachbit.exe,0"
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

; BleachBit Core
Section "$(BLEACHBIT_COMPONENT_CORE_TITLE)" SectionUnCore
  Call un.uninstallfunction
SectionEnd

; BleachBit Shortcuts
SectionGroup /e "$(BLEACHBIT_COMPONENTGROUP_SHORTCUTS_TITLE)" SectionUnShortcuts
  ; Use SetShellVarContext to use the right folders.
  ; See: https://nsis.sourceforge.io/Reference/SetShellVarContext
  ${if} $MultiUser.InstallMode == "AllUsers" ; setting defaults
    SetShellVarContext all
  ${else}
    SetShellVarContext current
  ${endif}

  ; BleachBit Start Menu Shortcuts
  Section "$(BLEACHBIT_COMPONENT_STARTMENU_TITLE)" SectionUnStartMenu
    ; Delete normal, Start menu shortcuts
    RMDir /r "$SMPROGRAMS\${prodname}"
  SectionEnd

  ; BleachBit Desktop Shortcut
  Section "$(BLEACHBIT_COMPONENT_DESKTOP_TITLE)" SectionUnDesktop
    ; Delete Desktop shortcut
    Delete "$DESKTOP\BleachBit.lnk"
  SectionEnd

  ; BleachBit Quick Launch Shortcut
  Section "$(BLEACHBIT_COMPONENT_QUICKLAUNCH_TITLE)" SectionUnQuickLaunch
    ; Delete Quick launch shortcut
    Delete "$QUICKLAUNCH\BleachBit.lnk"
  SectionEnd

  ; BleachBit Autostart Shortcut
  Section "$(BLEACHBIT_COMPONENT_AUTOSTART_TITLE)" SectionUnAutostart
    ; Delete Autostart shortcut
    Delete "$SMSTARTUP\BleachBit.lnk"
  SectionEnd
SectionGroupEnd

; BleachBit Translations
!ifndef NoTranslations
  Section "$(BLEACHBIT_COMPONENT_TRANSLATIONS_TITLE)" SectionUnTranslations
    Delete "$INSTDIR\share\locale\*.*"
  SectionEnd
!endif

;Section for making Shred Integration Optional
!ifndef NoSectionShred
  Section "$(BLEACHBIT_COMPONENT_INTEGRATESHRED_TITLE)" SectionUnShred
    ; Remove file association (Shredder)
    DeleteRegKey HKCR "AllFileSystemObjects\shell\shred.bleachbit"
  SectionEnd
!endif


;--------------------------------
;Descriptions for the Installer/Uninstaller Components

;USE A LANGUAGE STRING IF YOU WANT YOUR DESCRIPTIONS TO BE LANGUAGE SPECIFIC

; Assign descriptions to sections:
; Variable/Constant must be declared by Installer Sections! Place MUI_FUNCTION_DESCRIPTION after it!
!insertmacro MUI_FUNCTION_DESCRIPTION_BEGIN
  !insertmacro MUI_DESCRIPTION_TEXT ${SectionCore} $(BLEACHBIT_COMPONENT_CORE_DESCRIPTION)
  !insertmacro MUI_DESCRIPTION_TEXT ${SectionShortcuts} $(BLEACHBIT_COMPONENTGROUP_SHORTCUTS_DESCRIPTION)
  !insertmacro MUI_DESCRIPTION_TEXT ${SectionStartMenu} $(BLEACHBIT_COMPONENT_STARTMENU_DESCRIPTION)
  !insertmacro MUI_DESCRIPTION_TEXT ${SectionDesktop} $(BLEACHBIT_COMPONENT_DESKTOP_DESCRIPTION)
  !insertmacro MUI_DESCRIPTION_TEXT ${SectionQuickLaunch} $(BLEACHBIT_COMPONENT_QUICKLAUNCH_DESCRIPTION)
  !insertmacro MUI_DESCRIPTION_TEXT ${SectionAutostart} $(BLEACHBIT_COMPONENT_AUTOSTART_DESCRIPTION)
!ifndef NoTranslations
  !insertmacro MUI_DESCRIPTION_TEXT ${SectionTranslations} $(BLEACHBIT_COMPONENT_TRANSLATIONS_DESCRIPTION)
!endif
  !insertmacro MUI_DESCRIPTION_TEXT ${SectionShred} $(BLEACHBIT_COMPONENT_INTEGRATESHRED_DESCRIPTION)
!insertmacro MUI_FUNCTION_DESCRIPTION_END


;--------------------------------
;Uninstaller Functions

Function un.onInit

  !insertmacro MULTIUSER_UNINIT

  !insertmacro MUI_UNGETLANGUAGE

FunctionEnd
