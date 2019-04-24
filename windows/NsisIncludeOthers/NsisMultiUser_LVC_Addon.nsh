;  LV-Crew
;  Copyright (C) 2019 Tobias B. Besemer
;  https://www.LV-Crew.org
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

;  @app NSIS Installer Script - NsisMultiUser_LVC_Addon.nsh
;  @url https://github.com/LV-Crew
;  @os Windows
;  @scriptversion v1.0.0
;  @scriptdate 2019-04-18
;  @scriptby Tobias B. Besemer (2019-03-31 - 2019-04-18)
;  @tested ok v1.0.0, Windows 7
;  @testeddate 2019-04-18
;  @testedby https://github.com/Tobias-B-Besemer
;  @note Addon for https://github.com/Drizin/NsisMultiUser/

;  Notes:
;  ======
;  NsisMultiUser Addon to handle command line parameters.
;  
;  Include MultiUser LVC Addon in header with:
;  !include NsisMultiUser_LVC_Addon.nsh
;  Must be loaded after MULTIUSER_PAGE_INSTALLMODE!
;  
;  Load the NsisMultiUser_LVC_Addon-Language-File with:
;  !include NsisMultiUser_LVC_Addon_Lang.nsh
;  Must be loaded after MUI_LANGUAGE!
;  
;  Load MultiUser LVC Addon Header Macro in header with:
;  !insertmacro NsisMultiUser_LVC_Addon_Header_Macro
;  
;  Initialize NsisMultiUser_LVC_Addon in ".onInit":
;  !insertmacro NsisMultiUser_LVC_Addon_onInit
;  
;  Start NsisMultiUser_LVC_Addon-onInit-Functionality in ".onInit":
;  Call NsisMultiUser_LVC_Addon_onInit
;  
;  Insering the macros MUI_LANGDLL_DISPLAY & MULTIUSER_INIT after
;  "Call NsisMultiUser_LVC_Addon_CLI" that they don't effect the
;  error messages of the command line!
;  
;  Create a "Section -Post" and a "Section -un.Post" as last sections
;  and the "Call NsisMultiUser_LVC_Addon_SectionPost" and
;  "Call un.NsisMultiUser_LVC_Addon_SectionPost".
;  
;  Initialize NsisMultiUser_LVC_Addon in "un.onInit":
;  !insertmacro NsisMultiUser_LVC_Addon_un.onInit
;  
;  Start NsisMultiUser_LVC_Addon-onInit-Functionality in "un.onInit":
;  Call NsisMultiUser_LVC_Addon_un.onInit
;  
;  To handle "/uninstall" in "Function .onInit", there must be
;  a Function "uninstallfunction".
;  
;  Create the Error Level in "uninstallfunction" as first point with:
;  Call ${un}NsisMultiUser_LVC_Addon_ErrorLevel-666_Set
;  
;  Use "Call $NsisMultiUser_LVC_Addon_ErrorLevel-666_Handle" as last point
;  in your Section "Core", to handle Error Level 666 if "SystemComponent" was set.
;  $NsisMultiUser_LVC_Addon_ErrorLevel-666_Handle restores the old setting.
;  
;  "!insertmacro MUI_LANGDLL_DISPLAY", or "!insertmacro UMUI_MULTILANG_GET" musst
;  be loaded after "Call NsisMultiUser_LVC_Addon_onInit"!
;  Same by "Call un.NsisMultiUser_LVC_Addon_un.onInit"!
;  
;  Set NsisMultiUser_LVC_Addon_GUI_Update with "!define" to "Yes", if you use UMUI_PAGE_UPDATE!
;  
;  "NsisMultiUser_LVC_Addon_Upgrade" gets "Yes" if installer got started with "/upgrade"!
;  
;  You can turn the command line help off with define "Yes" for NsisMultiUser_LVC_Addon_NO_HELP_DIALOG!

; FileFunc.nsh for e.g. command line arguments managment:
!include FileFunc.nsh

; Always show the language selection dialog, even if a language has been stored
; in the registry. The language stored in the registry will be selected by default.
; We need also "MUI_LANGDLL_ALWAYSSHOW", or the user can never ever change his language!
!ifndef NoTranslations
  !define /IfNDef MUI_LANGDLL_ALWAYSSHOW
!endif

; Turn "MULTIUSER_INSTALLMODE" command line HELP off!
!define /IfNDef MULTIUSER_INSTALLMODE_NO_HELP_DIALOG 1
!define /redef MULTIUSER_INSTALLMODE_NO_HELP_DIALOG 1

; Turn "NsisMultiUser_LVC_Addon" command line HELP on!
!define /IfNDef NsisMultiUser_LVC_Addon_NO_HELP_DIALOG No

; Set to "Yes" if you use GUI Update:
!define /IfNDef NsisMultiUser_LVC_Addon_GUI_UPDATE No

; Command Line Variable:
; If "Yes": NO DESKTOP SHORTCUT!
Var NsisMultiUser_LVC_Addon_Command_Line_No_Desktop_Shortcut

; Error Level Variable:
; If 666: Installation was with "SystemComponent"!
Var NsisMultiUser_LVC_Addon_ErrorLevel

; Uninstaller Path and Command:
Var NsisMultiUser_LVC_Addon_Uninstaller_CMD
Var NsisMultiUser_LVC_Addon_Uninstaller_Path

; Gets "Yes" if installer got started with "/upgrade":
Var NsisMultiUser_LVC_Addon_Upgrade

!macro NsisMultiUser_LVC_Addon_Set_NsisMultiUser un
; Macro/Function "NsisMultiUser_LVC_Addon_Set_NsisMultiUser"
; It figured out that in some cases we get a wrong "$INSTDIR" (via command line). Seems to be a bug in
; NsisMultiUser we can't find for now. So to go sure, we set some values before we start again with
; NsisMultiUser.
; As we need NsisMultiUser_LVC_Addon_Set_NsisMultiUser on different places, and must call it each time,
; we move it into a Function.
; As we only can call functions starting with "un." from the uninstaller section,
; and only functions without "un." from the installer section, we need to move the
; funtion into a macro.
; Insert function as an installer and uninstaller function:
; !insertmacro NsisMultiUser_LVC_Addon_Set_NsisMultiUser ""
; !insertmacro NsisMultiUser_LVC_Addon_Set_NsisMultiUser "un."
  Function ${un}NsisMultiUser_LVC_Addon_Set_NsisMultiUser
    ${if} $CmdLineDir != ""
      StrCpy $INSTDIR $CmdLineDir
      Goto FunctionEnd
    ${endif}

    ${if} $MultiUser.InstallMode == "CurrentUser"
      Goto CurrentUser
    ${endif}

    ${if} $MultiUser.InstallMode == "AllUsers"
      Goto AllUsers
    ${endif}

    ; Check for old install (path) and set "$MultiUser.InstallMode", "$CmdLineInstallMode", "$HasPerUserInstallation",
    ; "$HasPerMachineInstallation", "$INSTDIR", "$CmdLineDir", "SetShellVarContext" & "UMUI_DEFAULT_SHELLVARCONTEXT":
    CurrentUser:
    ReadRegStr $R1 HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\${prodname}" "InstallLocation"
    ${if} $R1 != ""
      StrCpy $MultiUser.InstallMode "CurrentUser"
      StrCpy $CmdLineInstallMode "currentuser"
      StrCpy $HasPerUserInstallation 1
      StrCpy $INSTDIR "$R1"
      StrCpy $CmdLineDir $INSTDIR
      StrCpy $PerUserInstallationFolder $INSTDIR
      SetShellVarContext current
      !define /redef UMUI_DEFAULT_SHELLVARCONTEXT current
      Goto FunctionEnd
    ${endif}
    ${if} $MultiUser.InstallMode == "CurrentUser"
      StrCpy $CmdLineInstallMode "currentuser"
      StrCpy $HasPerUserInstallation 0
      IfFileExists '"$%AppData%"\*.*' 0 +3
      StrCpy $INSTDIR '"$%AppData%"\${prodname}' ; In double inverted comma, or else problems with paths with spaces!
      Goto +3
      IfFileExists "C:\*.*" 0 +3
      StrCpy $INSTDIR "C:\${prodname}"
      StrCpy $CmdLineDir $INSTDIR
      StrCpy $PerUserInstallationFolder $INSTDIR
      SetShellVarContext current
      !define /redef UMUI_DEFAULT_SHELLVARCONTEXT current
      Goto FunctionEnd
    ${endif}
    AllUsers:
    ReadRegStr $R1 HKLM "SOFTWARE\Wow6432Node\Microsoft\Windows\CurrentVersion\Uninstall\${prodname}" "InstallLocation"
    ${if} $R1 != ""
      StrCpy $MultiUser.InstallMode "AllUsers"
      StrCpy $CmdLineInstallMode "allusers"
      StrCpy $HasPerMachineInstallation 1
      StrCpy $INSTDIR "$R1"
      StrCpy $CmdLineDir $INSTDIR
      StrCpy $PerMachineInstallationFolder $INSTDIR
      SetShellVarContext all
      !define /redef UMUI_DEFAULT_SHELLVARCONTEXT all
    ${endif}
    ReadRegStr $R1 HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${prodname}" "InstallLocation"
    ${if} $R1 != ""
      StrCpy $MultiUser.InstallMode "AllUsers"
      StrCpy $CmdLineInstallMode "allusers"
      StrCpy $HasPerMachineInstallation 1
      StrCpy $INSTDIR "$R1"
      StrCpy $CmdLineDir $INSTDIR
      StrCpy $PerMachineInstallationFolder $INSTDIR
      SetShellVarContext all
      !define /redef UMUI_DEFAULT_SHELLVARCONTEXT all
    ${endif}

    ; If $MultiUser.InstallMode is still "", then set "$MultiUser.InstallMode", "$CmdLineInstallMode", "$HasPerUserInstallation",
    ; "$HasPerMachineInstallation", "$INSTDIR", "$CmdLineDir", "SetShellVarContext" & "UMUI_DEFAULT_SHELLVARCONTEXT":
    ${if} $MultiUser.InstallMode == ""
      StrCpy $MultiUser.InstallMode "AllUsers"
      StrCpy $CmdLineInstallMode "allusers"
      StrCpy $HasPerMachineInstallation 0
      StrCpy $HasPerUserInstallation 0
      IfFileExists '"$%ProgramFiles(x86)%"\*.*' 0 +3
      StrCpy $INSTDIR '"$%ProgramFiles(x86)%"\${prodname}' ; In double inverted comma, or else problems with paths with spaces!
      Goto +3
      IfFileExists '"$%ProgramFiles%"\*.*' 0 +3
      StrCpy $INSTDIR '"$%ProgramFiles%"\${prodname}' ; In double inverted comma, or else problems with paths with spaces!
      StrCpy $CmdLineDir $INSTDIR
      StrCpy $PerMachineInstallationFolder $INSTDIR
      SetShellVarContext all
      !define /redef UMUI_DEFAULT_SHELLVARCONTEXT all
    ${endif}

    FunctionEnd:
  FunctionEnd
!macroend

!insertmacro NsisMultiUser_LVC_Addon_Set_NsisMultiUser ""
!insertmacro NsisMultiUser_LVC_Addon_Set_NsisMultiUser "un."

!macro NsisMultiUser_LVC_Addon_SectionPost un
; Macro/Function "NsisMultiUser_LVC_Addon_SectionPost"
; Save the Language Selection Dialog Setting
; As we need NsisMultiUser_LVC_Addon_SectionPost on different places, and must call it each time,
; we move it into a Function.
; As we only can call functions starting with "un." from the uninstaller section,
; and only functions without "un." from the installer section, we need to move the
; funtion into a macro.
; We need also "MUI_LANGDLL_ALWAYSSHOW", or the user can never ever change his language!
; Locale ID:
; https://docs.microsoft.com/en-us/openspecs/windows_protocols/ms-lcid/a9eac961-e77d-41a6-90a5-ce1a8b0cdb9c
; Insert function as an installer and uninstaller function:
; !insertmacro NsisMultiUser_LVC_Addon_SectionPost ""
; !insertmacro NsisMultiUser_LVC_Addon_SectionPost "un."
  Function ${un}NsisMultiUser_LVC_Addon_SectionPost
    IfFileExists "$INSTDIR\*.*" +1 +2
    ${if} $MultiUser.InstallMode == "AllUsers" ; setting defaults
      WriteRegDWORD SHCTX "${MULTIUSER_INSTALLMODE_UNINSTALL_REGISTRY_KEY_PATH}" "Language" $Language
    ${else}
      WriteRegDWORD SHCTX "${MULTIUSER_INSTALLMODE_UNINSTALL_REGISTRY_KEY_PATH}$0" "Language" $Language
    ${endif}
  FunctionEnd
!macroend

!insertmacro NsisMultiUser_LVC_Addon_SectionPost ""
!insertmacro NsisMultiUser_LVC_Addon_SectionPost "un."

!macro NsisMultiUser_LVC_Addon_ErrorLevel-666_Set un
; Macro/Function "NsisMultiUser_LVC_Addon_ErrorLevel-666_Set"
; Set Error Level 666 if "SystemComponent" was set.
; As we need NsisMultiUser_LVC_Addon_ErrorLevel-666_Set on different places, and must call it each time,
; we move it into a Function.
; As we only can call functions starting with "un." from the uninstaller section,
; and only functions without "un." from the installer section, we need to move the
; funtion into a macro.
; Insert function as an installer and uninstaller function:
; !insertmacro NsisMultiUser_LVC_Addon_ErrorLevel-666_Set ""
; !insertmacro NsisMultiUser_LVC_Addon_ErrorLevel-666_Set "un."
  Function ${un}NsisMultiUser_LVC_Addon_ErrorLevel-666_Set
    ; Check for SystemComponent and SetErrorLevel 666
    ClearErrors
    ReadRegStr $5 SHCTX "${MULTIUSER_INSTALLMODE_UNINSTALL_REGISTRY_KEY_PATH}" "SystemComponent"
    IfErrors 0 +3
    ReadRegStr $5 SHCTX "${MULTIUSER_INSTALLMODE_UNINSTALL_REGISTRY_KEY_PATH}$0" "SystemComponent"
    IfErrors +2 0
    SetErrorLevel 666
  FunctionEnd
!macroend

!insertmacro NsisMultiUser_LVC_Addon_ErrorLevel-666_Set ""
!insertmacro NsisMultiUser_LVC_Addon_ErrorLevel-666_Set "un."

!macro NsisMultiUser_LVC_Addon_ErrorLevel-666_Handle
; Macro/Function "NsisMultiUser_LVC_Addon_ErrorLevel-666_Handle"
; Handle Error Level 666 if "SystemComponent" was set.
; Restores the old settings by install.
  Function NsisMultiUser_LVC_Addon_ErrorLevel-666_Handle
    ; Restore SystemComponent
    ${if} $NsisMultiUser_LVC_Addon_ErrorLevel == "666"
      ${if} $MultiUser.InstallMode == "AllUsers" ; setting defaults
        WriteRegStr SHCTX "${MULTIUSER_INSTALLMODE_UNINSTALL_REGISTRY_KEY_PATH}" "SystemComponent" "1"
      ${else}
        WriteRegStr SHCTX "${MULTIUSER_INSTALLMODE_UNINSTALL_REGISTRY_KEY_PATH}$0" "SystemComponent" "1"
      ${endif}
    ${endif}
  FunctionEnd
!macroend

!insertmacro NsisMultiUser_LVC_Addon_ErrorLevel-666_Handle

!macro NsisMultiUser_LVC_Addon_onInit
Function NsisMultiUser_LVC_Addon_onInit
  ; Initialize Command Line Variable:
  ; If "Yes": NO DESKTOP SHORTCUT!
  StrCpy $NsisMultiUser_LVC_Addon_Command_Line_No_Desktop_Shortcut "No"

  ; Get the command line parameters...
  ${GetParameters} $R0

  ; ...and handle the command line parameters...

  ; Case: /?
  ${GetOptions} $R0 "/?" $R1
  ${IfNot} ${errors}
    ; SetErrorLevel 0 - normal execution (no error)
    SetErrorLevel 0
    Goto command_line_help
  ${EndIf}

  ; Case: -?
  ${GetOptions} $R0 "-?" $R1
  ${IfNot} ${errors}
    ; SetErrorLevel 0 - normal execution (no error)
    SetErrorLevel 0
    Goto command_line_help
  ${EndIf}

  ; Case: /h
  ${GetOptions} $R0 "/h" $R1
  ${IfNot} ${errors}
    ; SetErrorLevel 0 - normal execution (no error)
    SetErrorLevel 0
    Goto command_line_help
  ${EndIf}

  ; Case: -h
  ${GetOptions} $R0 "-h" $R1
  ${IfNot} ${errors}
    ; SetErrorLevel 0 - normal execution (no error)
    SetErrorLevel 0
    Goto command_line_help
  ${EndIf}

  ; Case: --help
  ${GetOptions} $R0 "--help" $R1
  ${IfNot} ${errors}
    ; SetErrorLevel 0 - normal execution (no error)
    SetErrorLevel 0
    Goto command_line_help
  ${EndIf}

  ; Case: /error-codes
  ${GetOptions} $R0 "/error-codes" $R1
  ${IfNot} ${errors}
    ; Copied from NsisMultiUser.nsh (starting line 480) and modified
    MessageBox MB_ICONINFORMATION "Error codes (decimal):$\r$\n\
      0$\t- normal execution (no error)$\r$\n\
      1$\t- (un)installation aborted by user (cancel button)$\r$\n\
      2$\t- (un)installation aborted by script$\r$\n\
      666$\t- installation had registry key 'SystemComponent'$\r$\n\
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

  ; Case: (/allusers or /currentuser) (/S) /upgrade
  ${GetOptions} $R0 "/upgrade" $R1
  ${IfNot} ${errors}
    StrCpy $NsisMultiUser_LVC_Addon_Upgrade "Yes"
    ${GetOptions} $R0 "/allusers" $R1
    ${IfNot} ${errors}
      ; Use SetShellVarContext to use the right folders.
      ; See: https://nsis.sourceforge.io/Reference/SetShellVarContext
      SetShellVarContext all
      StrCpy $MultiUser.InstallMode "AllUsers"
      ${GetOptionsS} $R0 "/S" $R1
      ${IfNot} ${errors}
        SetSilent silent
      ${EndIf}
      Goto previous_version_check
    ${EndIf}
    ${GetOptions} $R0 "/currentuser" $R1
    ${IfNot} ${errors}
      ; Use SetShellVarContext to use the right folders.
      ; See: https://nsis.sourceforge.io/Reference/SetShellVarContext
      SetShellVarContext current
      StrCpy $MultiUser.InstallMode "CurrentUser"
      ${GetOptionsS} $R0 "/S" $R1
      ${IfNot} ${errors}
        SetSilent silent
      ${EndIf}
      Goto previous_version_check
    ${EndIf}
    Goto previous_version_check
  ${EndIf}

  ; Case: (/allusers or /currentuser) (/S) /downgrade
  ${GetOptions} $R0 "/downgrade" $R1
  ${IfNot} ${errors}
    ${GetOptions} $R0 "/allusers" $R1
    ${IfNot} ${errors}
      ; Use SetShellVarContext to use the right folders.
      ; See: https://nsis.sourceforge.io/Reference/SetShellVarContext
      SetShellVarContext all
      StrCpy $MultiUser.InstallMode "AllUsers"
      ${GetOptionsS} $R0 "/S" $R1
      ${IfNot} ${errors}
        SetSilent silent
      ${EndIf}
      Goto downgrade
    ${EndIf}
    ${GetOptions} $R0 "/currentuser" $R1
    ${IfNot} ${errors}
      ; Use SetShellVarContext to use the right folders.
      ; See: https://nsis.sourceforge.io/Reference/SetShellVarContext
      SetShellVarContext current
      StrCpy $MultiUser.InstallMode "CurrentUser"
      ${GetOptionsS} $R0 "/S" $R1
      ${IfNot} ${errors}
        SetSilent silent
      ${EndIf}
      Goto downgrade
    ${EndIf}
    Goto downgrade
  ${EndIf}

  ; Case: (/allusers or /currentuser) (/S) /uninstall
  ; In case "${GetOptionsS} $R0":
  ${GetOptions} $R0 "/uninstall" $R1
  ${IfNot} ${errors}
    ${GetOptions} $R0 "/allusers" $R1
    ${IfNot} ${errors}
      StrCpy $MultiUser.InstallMode "AllUsers"
      Call NsisMultiUser_LVC_Addon_Set_NsisMultiUser
      Call uninstallfunction
      ${GetOptionsS} $R0 "/S" $R1
      ${If} ${errors}
        MessageBox MB_ICONINFORMATION "$(NsisMultiUser_LVC_Addon_Uninstall_Done)"
      ${EndIf}
      Abort
    ${EndIf}
    ${GetOptions} $R0 "/currentuser" $R1
    ${IfNot} ${errors}
      StrCpy $MultiUser.InstallMode "CurrentUser"
      Call NsisMultiUser_LVC_Addon_Set_NsisMultiUser
      Call uninstallfunction
      ${GetOptionsS} $R0 "/S" $R1
      ${If} ${errors}
        MessageBox MB_ICONINFORMATION "$(NsisMultiUser_LVC_Addon_Uninstall_Done)"
      ${EndIf}
      Abort
    ${EndIf}
    MessageBox MB_ICONINFORMATION "Error:$\r$\n\
      $\r$\n\
      Called: (/S) /uninstall$\r$\n\
      $\r$\n\
      '/uninstall':$\r$\n\
      run internal uninstaller, requires '/allusers' or '/currentuser',$\r$\n\
      $\r$\n\
      '/allusers':$\r$\n\
      uninstall for all users$\r$\n\
      $\r$\n\
      '/currentuser':$\r$\n\
      uninstall for current user only$\r$\n\
      $\r$\n\
      '/S':$\r$\n\
      silent mode, requires '/allusers' or '/currentuser', case-sensitive"
    ; SetErrorLevel 666660 - invalid command-line parameters
    SetErrorLevel 666660
    Abort
  ${EndIf}

  ; Case: (/allusers or /currentuser) (/S) /no-desktop-shortcut (/D)
  ${GetOptions} $R0 "/no-desktop-shortcut" $R1
  ${IfNot} ${errors}
    ${GetOptionsS} $R0 "/S" $R1
    ${IfNot} ${errors}
      ${GetOptions} $R0 "/allusers" $R1
      ${IfNot} ${errors}
        StrCpy $NsisMultiUser_LVC_Addon_Command_Line_No_Desktop_Shortcut "Yes"
        ; Use SetShellVarContext to use the right folders.
        ; See: https://nsis.sourceforge.io/Reference/SetShellVarContext
        SetShellVarContext all
        StrCpy $MultiUser.InstallMode "AllUsers"
        SetSilent silent
        Goto previous_version_check
      ${EndIf}
      ${GetOptions} $R0 "/currentuser" $R1
      ${IfNot} ${errors}
        StrCpy $NsisMultiUser_LVC_Addon_Command_Line_No_Desktop_Shortcut "Yes"
        ; Use SetShellVarContext to use the right folders.
        ; See: https://nsis.sourceforge.io/Reference/SetShellVarContext
        SetShellVarContext current
        StrCpy $MultiUser.InstallMode "CurrentUser"
        SetSilent silent
        Goto previous_version_check
      ${EndIf}
      Goto error_no-desktop-shortcut
    ${EndIf}
    Goto error_no-desktop-shortcut
  ${EndIf}

  ; Case: (/allusers or /currentuser) /S (/D)
  ${GetOptionsS} $R0 "/S" $R1
  ${IfNot} ${errors}
    ${GetOptions} $R0 "/allusers" $R1
    ${IfNot} ${errors}
      ; Use SetShellVarContext to use the right folders.
      ; See: https://nsis.sourceforge.io/Reference/SetShellVarContext
      SetShellVarContext all
      StrCpy $MultiUser.InstallMode "AllUsers"
      SetSilent silent
      Goto previous_version_check
    ${EndIf}
    ${GetOptions} $R0 "/currentuser" $R1
    ${IfNot} ${errors}
      ; Use SetShellVarContext to use the right folders.
      ; See: https://nsis.sourceforge.io/Reference/SetShellVarContext
      SetShellVarContext current
      StrCpy $MultiUser.InstallMode "CurrentUser"
      SetSilent silent
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
      '/D=[path]':$\r$\n\
      set install directory, without quotes"
    ; SetErrorLevel 666660 - invalid command-line parameters
    SetErrorLevel 666660
    Abort
  ${EndIf}

  ; Case: /allusers
  ${GetOptions} $R0 "/allusers" $R1
  ${IfNot} ${errors}
    SetShellVarContext all
    StrCpy $MultiUser.InstallMode "AllUsers"
    StrCpy $CmdLineInstallMode "allusers"
    Goto previous_version_check
  ${EndIf}

  ; Case: /currentuser
  ${GetOptions} $R0 "/currentuser" $R1
  ${IfNot} ${errors}
    SetShellVarContext current
    StrCpy $MultiUser.InstallMode "CurrentUser"
    StrCpy $CmdLineInstallMode "currentuser"
    Goto previous_version_check
  ${EndIf}

  ; In case of just /D:
  ${GetOptions} $R0 "/D" $R1
  ${IfNot} ${errors}
    MessageBox MB_ICONINFORMATION "Error:$\r$\n\
      $\r$\n\
      Called: $R0$\r$\n\
      $\r$\n\
      '/D=[path]':$\r$\n\
      set install directory, without quotes, requires '/allusers'$\r$\n\
      or '/currentuser'$\r$\n\
      $\r$\n\
      '/S':$\r$\n\
      silent mode, requires '/allusers' or '/currentuser', case-sensitive$\r$\n\
      $\r$\n\
      '/allusers':$\r$\n\
      uninstall for all users$\r$\n\
      $\r$\n\
      '/currentuser':$\r$\n\
      uninstall for current user only"
    ; SetErrorLevel 666660 - invalid command-line parameters
    SetErrorLevel 666660
    Abort
  ${EndIf}

  ; In case of /L=[Language-Code] /NCRC:
  ; This is the command line language switch of UMUI_PAGE_MULTILANGUAGE!
  ${GetOptions} $R0 "/NCRC" $R1
  ${IfNot} ${errors}
    Goto inseringmacros
  ${EndIf}

  ; In case of /modify /L=[Language-Code]:
  ; This is the command line 'modify' switch of UMUI_UNPAGE_MAINTENANCE!
  ${GetOptions} $R0 "/modify" $R1
  ${IfNot} ${errors}
    Goto Add_Remove
  ${EndIf}

  ; In case of /remove /L=[Language-Code]:
  ; This is the command line 'remove' switch of UMUI_UNPAGE_MAINTENANCE!
  ${GetOptions} $R0 "/remove" $R1
  ${IfNot} ${errors}
    Goto Add_Remove
  ${EndIf}

  ; Case: No Parameter
  ; In case $R0 == "":
  ${GetOptions} $R0 "" $R1
  ${If} $R0 == ""
    ${If} ${NsisMultiUser_LVC_Addon_GUI_Update} == "Yes"
      Goto GUI_Update
    ${EndIf}
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
    (silent mode only) install without desktop shortcut$\r$\n\
    $\r$\n\
    '/S':$\r$\n\
    silent mode, requires '/allusers' or '/currentuser', case-sensitive$\r$\n\
    $\r$\n\
    '/allusers':$\r$\n\
    install for all users$\r$\n\
    $\r$\n\
    '/currentuser':$\r$\n\
    install for current user only$\r$\n\
    $\r$\n\
    '/D':$\r$\n\
    set install directory, without quotes"
  ; SetErrorLevel 666660 - invalid command-line parameters
  SetErrorLevel 666660
  Abort

  command_line_help:
  StrCmp ${NsisMultiUser_LVC_Addon_NO_HELP_DIALOG} "Yes" +2
  ; Copied from NsisMultiUser.nsh (starting line 480) and modified
  MessageBox MB_ICONINFORMATION "Usage:$\r$\n\
    $\r$\n\
    '/upgrade':$\r$\n\
    dont remove registry values$\r$\n\
    $\r$\n\
    '/downgrade':$\r$\n\
    ignores version check$\r$\n\
    $\r$\n\
    '/allusers':$\r$\n\
    (un)install for all users$\r$\n\
    $\r$\n\
    '/currentuser':$\r$\n\
    (un)install for current user only$\r$\n\
    $\r$\n\
    '/uninstall':$\r$\n\
    run internal uninstaller, requires '/allusers' or '/currentuser',$\r$\n\
    $\r$\n\
    '/S':$\r$\n\
    silent mode, requires '/allusers' or '/currentuser', case-sensitive$\r$\n\
    $\r$\n\
    '/no-desktop-shortcut':$\r$\n\
    (silent mode only) install without desktop shortcut$\r$\n\
    $\r$\n\
    '/D=[path]':$\r$\n\
    set install directory, without quotes$\r$\n\
    $\r$\n\
    '/error-codes':$\r$\n\
    the error codes the program gives back$\r$\n\
    $\r$\n\
    '/?':$\r$\n\
    display this message"
  Abort

  ; Check the version - "<" "=" ">" and then uninstall old if ">":
  previous_version_check:
  ${If} ${NsisMultiUser_LVC_Addon_GUI_UPDATE} == "Yes"
    Goto GUI_Update
  ${EndIf}
  ; Wow6432Node is e.g. used on Windows 7 64-bit for 32-bit programs
  ReadRegStr $R1 HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\${prodname}" "DisplayVersion"
  IfErrors +3 +1
  StrCpy $HasPerUserInstallation "1"
  Goto +9
  ReadRegStr $R1 HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${prodname}" "DisplayVersion"
  IfErrors +3 +1
  StrCpy $HasPerMachineInstallation "1"
  Goto +5
  ReadRegStr $R1 HKLM "SOFTWARE\Wow6432Node\Microsoft\Windows\CurrentVersion\Uninstall\${prodname}" "DisplayVersion"
  IfErrors +3 +1
  StrCpy $HasPerMachineInstallation "1"
  Goto +1
  ; If not found, try to find the "UninstallString"
  StrCmp $R1 "" install_check
  ${If} "$R1" > "${VERSION}"
    MessageBox MB_ICONINFORMATION "$(NsisMultiUser_LVC_Addon_Newer_Version_Found)"
    Abort
  ${EndIf}
  ${If} "$R1" == "${VERSION}"
    ReadRegStr $PerUserInstallationFolder HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\${prodname}" "InstallLocation"
    ReadRegStr $PerMachineInstallationFolder HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${prodname}" "InstallLocation"
    IfErrors 0 +2
    ReadRegStr $PerMachineInstallationFolder HKLM "SOFTWARE\Wow6432Node\Microsoft\Windows\CurrentVersion\Uninstall\${prodname}" "InstallLocation"
    Goto Add_Remove
  ${EndIf}
  Goto install_check

  ; Go directly to install_check without previous_version_check:
  downgrade:
  ${If} ${NsisMultiUser_LVC_Addon_GUI_UPDATE} == "Yes"
    Goto GUI_Update
  ${EndIf}
  Goto install_check

  ; Check whether application is already installed:
  install_check:
  ${If} ${NsisMultiUser_LVC_Addon_GUI_UPDATE} == "Yes"
    Goto GUI_Update
  ${EndIf}
  ; Wow6432Node is e.g. used on Windows 7 64-bit for 32-bit programs
  ReadRegStr $R2 HKLM "SOFTWARE\Wow6432Node\Microsoft\Windows\CurrentVersion\Uninstall\${prodname}" "UninstallString"
  IfErrors 0 +10
  ReadRegStr $R2 HKLM "SOFTWARE\Wow6432Node\Microsoft\Windows\CurrentVersion\Uninstall\${prodname}" "QuietUninstallString"
  IfErrors 0 +8
  ReadRegStr $R2 HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${prodname}" "UninstallString"
  IfErrors 0 +6
  ReadRegStr $R2 HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${prodname}" "QuietUninstallString"
  IfErrors 0 +4
  ReadRegStr $R2 HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\${prodname}" "UninstallString"
  IfErrors 0 +2
  ReadRegStr $R2 HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\${prodname}" "QuietUninstallString"
  ; If not already installed, skip uninstallation
  StrCmp $R2 "" no_uninstall_possible
  ; Save the uninstaller for later:
  StrCpy $NsisMultiUser_LVC_Addon_Uninstaller_CMD "$R2"
  ; We also need the InstallLocation:
  Goto +9
  ReadRegStr $R3 HKLM "SOFTWARE\Wow6432Node\Microsoft\Windows\CurrentVersion\Uninstall\${prodname}" "InstallLocation"
  IfErrors 0 +5
  ReadRegStr $R3 HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${prodname}" "InstallLocation"
  IfErrors 0 +3
  ReadRegStr $R3 HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\${prodname}" "InstallLocation"
  IfErrors +3 +1
  StrCpy $NsisMultiUser_LVC_Addon_Uninstaller_Path "$R3"
  Goto +2
  StrCpy $NsisMultiUser_LVC_Addon_Uninstaller_Path "$%Temp%" ; If not set, we have a problem... ^^ (...but we set it normaly.)
  MessageBox MB_OKCANCEL|MB_ICONEXCLAMATION "$(NsisMultiUser_LVC_Addon_Uninstall_Before_Upgrade)" /SD IDOK IDOK true IDCANCEL false
  false:
  ; SetErrorLevel 1 - (un)installation aborted by user (Cancel button)
  SetErrorLevel 1
  Abort
  true:
  ; If installing in silent mode, also uninstall in silent mode
  ; IfSilent 0 +2
  ; To make sure we deinstall all components, we run the deinstaller in silent mode:
  StrCpy $NsisMultiUser_LVC_Addon_Uninstaller_CMD "$NsisMultiUser_LVC_Addon_Uninstaller_CMD /S"
  ; As we do a upgrade, we add command line switch /upgrade:
  StrCpy $NsisMultiUser_LVC_Addon_Uninstaller_CMD "$NsisMultiUser_LVC_Addon_Uninstaller_CMD /upgrade"
  ; Run the old uninstaller and SetErrorLevel (needed to restore "SystemComponent"):
  StrCpy $NsisMultiUser_LVC_Addon_Uninstaller_CMD "$NsisMultiUser_LVC_Addon_Uninstaller_CMD _?=$NsisMultiUser_LVC_Addon_Uninstaller_Path"
  ExecWait $NsisMultiUser_LVC_Addon_Uninstaller_CMD $R6
  Delete "$NsisMultiUser_LVC_Addon_Uninstaller_Path\${UNINSTALL_FILENAME}"
  RMDir "$NsisMultiUser_LVC_Addon_Uninstaller_Path"
  StrCpy $NsisMultiUser_LVC_Addon_ErrorLevel "$R6"
  ; ErrorLevel = 1 - uninstallation aborted by user (Cancel button)
  ; ErrorLevel = 2 - uninstallation aborted by script
  ; ErrorLevel = 666 - installation was with "SystemComponent"
  ${If} $NsisMultiUser_LVC_Addon_ErrorLevel == "1"
  ${OrIf} $NsisMultiUser_LVC_Addon_ErrorLevel == "2"
    Abort
  ${EndIf}
  ; ErrorLevel = 666 do we handle later!
  Goto inseringmacros

  no_uninstall_possible:
  ; If program is installed - we can't detect it, ATM!
  ; Move on! ^^
  Goto inseringmacros

  GUI_Update:
  ; We do a GUI Update!
  StrCpy $NsisMultiUser_LVC_Addon_Upgrade "Yes"
  Goto inseringmacros

  Add_Remove:
  ; We do Add/Remove!
  ; Move on from here!
  Goto inseringmacros

  ; Insering the macros at the end that they don't effect the command line management:
  inseringmacros:
  ; Insert Macro MULTIUSER_INIT:
  ; Must be loaded after "!insertmacro MULTIUSER_PAGE_INSTALLMODE"!
  ; Command Call not valid outside Section or Function!
  !insertmacro MULTIUSER_INIT

  ; First handle this case: /D
  ${GetOptions} $R0 "/D=" $R1
  ${IfNot} ${errors}
    StrCpy $CmdLineDir $R1
    StrCpy $INSTDIR $CmdLineDir
  ${EndIf}

  ; It figured out that in some cases we get a wrong "$INSTDIR" (via command line). Seems to be a bug in
  ; NsisMultiUser we can't find for now. So to go sure, we set some values before we start again with
  ; NsisMultiUser.
  Call NsisMultiUser_LVC_Addon_Set_NsisMultiUser

  ; Check for last used NSIS Language and set "$Language":
  ReadRegDWORD $2 SHCTX "${MULTIUSER_INSTALLMODE_UNINSTALL_REGISTRY_KEY_PATH}$0" "Language"
  ${if} $2 != ""
    StrCpy $Language "$2"
  ${endif}
  ReadRegDWORD $2 SHCTX "${MULTIUSER_INSTALLMODE_UNINSTALL_REGISTRY_KEY_PATH}" "Language"
  ${if} $2 != ""
    StrCpy $Language "$2"
  ${endif}

  ; It starts the GUI and loads the Installer Sections...
FunctionEnd
!macroend

; Initialize NsisMultiUser_LVC_Addon_onInit:
!insertmacro NsisMultiUser_LVC_Addon_onInit

!macro un.NsisMultiUser_LVC_Addon_un.onInit
Function un.NsisMultiUser_LVC_Addon_un.onInit
  ; Get the command line parameters...
  ${GetParameters} $R0

  ; ...and handle the command line parameters...

  ; Case: /?
  ${GetOptions} $R0 "/?" $R1
  ${IfNot} ${errors}
    ; SetErrorLevel 0 - normal execution (no error)
    SetErrorLevel 0
    Goto command_line_help
  ${EndIf}

  ; Case: -?
  ${GetOptions} $R0 "-?" $R1
  ${IfNot} ${errors}
    ; SetErrorLevel 0 - normal execution (no error)
    SetErrorLevel 0
    Goto command_line_help
  ${EndIf}

  ; Case: /h
  ${GetOptions} $R0 "/h" $R1
  ${IfNot} ${errors}
    ; SetErrorLevel 0 - normal execution (no error)
    SetErrorLevel 0
    Goto command_line_help
  ${EndIf}

  ; Case: -h
  ${GetOptions} $R0 "-h" $R1
  ${IfNot} ${errors}
    ; SetErrorLevel 0 - normal execution (no error)
    SetErrorLevel 0
    Goto command_line_help
  ${EndIf}

  ; Case: --help
  ${GetOptions} $R0 "--help" $R1
  ${IfNot} ${errors}
    ; SetErrorLevel 0 - normal execution (no error)
    SetErrorLevel 0
    Goto command_line_help
  ${EndIf}

  ; Case: /error-codes
  ${GetOptions} $R0 "/error-codes" $R1
  ${IfNot} ${errors}
    ; Copied from NsisMultiUser.nsh (starting line 480) and modified
    MessageBox MB_ICONINFORMATION "Error codes (decimal):$\r$\n\
      0$\t- normal execution (no error)$\r$\n\
      1$\t- (un)installation aborted by user (Cancel button)$\r$\n\
      2$\t- (un)installation aborted by script$\r$\n\
      666$\t- installation had registry key 'SystemComponent'$\r$\n\
      666660$\t- invalid command-line parameters$\r$\n\
      666662$\t- uninstaller detected there's no installed version$\r$\n\
      666663$\t- executing uninstaller from the installer failed$\r$\n\
      more$\t- in the documentation and on request"
    ; SetErrorLevel 0 - normal execution (no error)
    SetErrorLevel 0
    Abort
  ${EndIf}

  ; Case: (/allusers or /currentuser) (/S) /upgrade
  ${GetOptions} $R0 "/upgrade" $R1
  ${IfNot} ${errors}
    StrCpy $NsisMultiUser_LVC_Addon_Upgrade "Yes"
    ${GetOptions} $R0 "/allusers" $R1
    ${IfNot} ${errors}
      ; Use SetShellVarContext to use the right folders.
      ; See: https://nsis.sourceforge.io/Reference/SetShellVarContext
      SetShellVarContext all
      StrCpy $MultiUser.InstallMode "AllUsers"
      ${GetOptionsS} $R0 "/S" $R1
      ${IfNot} ${errors}
        SetSilent silent
      ${EndIf}
      Goto end
    ${EndIf}
    ${GetOptions} $R0 "/currentuser" $R1
    ${IfNot} ${errors}
      ; Use SetShellVarContext to use the right folders.
      ; See: https://nsis.sourceforge.io/Reference/SetShellVarContext
      SetShellVarContext current
      StrCpy $MultiUser.InstallMode "CurrentUser"
      ${GetOptionsS} $R0 "/S" $R1
      ${IfNot} ${errors}
        SetSilent silent
      ${EndIf}
      Goto end
    ${EndIf}
    Goto end
  ${EndIf}

  ; Case: (/allusers or /currentuser) /S
  ${GetOptionsS} $R0 "/S" $R1
  ${IfNot} ${errors}
    ${GetOptions} $R0 "/allusers" $R1
    ${IfNot} ${errors}
      ; Use SetShellVarContext to use the right folders.
      ; See: https://nsis.sourceforge.io/Reference/SetShellVarContext
      SetShellVarContext all
      StrCpy $MultiUser.InstallMode "AllUsers"
      StrCpy $HasPerMachineInstallation 1
      SetSilent silent
      Goto end
    ${EndIf}
    ${GetOptions} $R0 "/currentuser" $R1
    ${IfNot} ${errors}
      ; Use SetShellVarContext to use the right folders.
      ; See: https://nsis.sourceforge.io/Reference/SetShellVarContext
      SetShellVarContext current
      StrCpy $MultiUser.InstallMode "CurrentUser"
      StrCpy $HasPerUserInstallation 1
      SetSilent silent
      Goto end
    ${EndIf}
    MessageBox MB_ICONINFORMATION "Error:$\r$\n\
      $\r$\n\
      Called: /S$\r$\n\
      $\r$\n\
      '/S':$\r$\n\
      silent mode, requires '/allusers' or '/currentuser', case-sensitive$\r$\n\
      $\r$\n\
      '/allusers':$\r$\n\
      uninstall for all users$\r$\n\
      $\r$\n\
      '/currentuser':$\r$\n\
      uninstall for current user only"
    ; SetErrorLevel 666660 - invalid command-line parameters
    SetErrorLevel 666660
    Abort
  ${EndIf}

  ; Case: /allusers
  ${GetOptions} $R0 "/allusers" $R1
  ${IfNot} ${errors}
    ; Use SetShellVarContext to use the right folders.
    ; See: https://nsis.sourceforge.io/Reference/SetShellVarContext
    SetShellVarContext all
    StrCpy $MultiUser.InstallMode "AllUsers"
    Goto end
  ${EndIf}

  ; Case: /currentuser
  ${GetOptions} $R0 "/currentuser" $R1
  ${IfNot} ${errors}
    ; Use SetShellVarContext to use the right folders.
    ; See: https://nsis.sourceforge.io/Reference/SetShellVarContext
    SetShellVarContext current
    StrCpy $MultiUser.InstallMode "CurrentUser"
    Goto end
  ${EndIf}

  ; In case of /L=[Language-Code] /NCRC:
  ; This is the command line language switch of UMUI_UNPAGE_MULTILANGUAGE!
  ${GetOptions} $R0 "/NCRC" $R1
  ${IfNot} ${errors}
    Goto end
  ${EndIf}

  ; In case of /modify /L=[Language-Code]:
  ; This is the command line 'modify' switch of UMUI_UNPAGE_MAINTENANCE!
  ${GetOptions} $R0 "/modify" $R1
  ${IfNot} ${errors}
    Goto end
  ${EndIf}

  ; In case of /remove /L=[Language-Code]:
  ; This is the command line 'remove' switch of UMUI_UNPAGE_MAINTENANCE!
  ${GetOptions} $R0 "/remove" $R1
  ${IfNot} ${errors}
    Goto end
  ${EndIf}

  ; Case: No Parameter
  ; In case $R0 == "":
  ${GetOptions} $R0 "" $R1
  ${If} $R0 == ""
    Goto end
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

  command_line_help:
  StrCmp ${NsisMultiUser_LVC_Addon_NO_HELP_DIALOG} "Yes" +2
  ; Copied from NsisMultiUser.nsh (starting line 480) and modified
  MessageBox MB_ICONINFORMATION "Usage:$\r$\n\
    $\r$\n\
    '/allusers':$\r$\n\
    (un)install for all users$\r$\n\
    $\r$\n\
    '/currentuser':$\r$\n\
    (un)install for current user only$\r$\n\
    $\r$\n\
    '/upgrade':$\r$\n\
    dont remove registry values$\r$\n\
    $\r$\n\
    '/S':$\r$\n\
    silent mode, requires '/allusers' or '/currentuser', case-sensitive$\r$\n\
    $\r$\n\
    '/error-codes':$\r$\n\
    the error codes the program gives back$\r$\n\
    $\r$\n\
    '/?':$\r$\n\
    display this message"
  Abort

  end:
  ; Insering the macros at the end that they don't effect the error messages of the command line:
  !insertmacro MULTIUSER_UNINIT

  ; Check for last used NSIS Language and set "$Language":
  ReadRegStr $2 SHCTX "${MULTIUSER_INSTALLMODE_UNINSTALL_REGISTRY_KEY_PATH}$0" "Language"
  ${if} $2 != ""
    StrCpy $Language "$2"
  ${endif}
  ReadRegStr $2 SHCTX "${MULTIUSER_INSTALLMODE_UNINSTALL_REGISTRY_KEY_PATH}" "Language"
  ${if} $2 != ""
    StrCpy $Language "$2"
  ${endif}

  ; It starts the GUI and loads the UnInstaller Sections...
FunctionEnd
!macroend

; Initialize un.NsisMultiUser_LVC_Addon_un.onInit:
!insertmacro un.NsisMultiUser_LVC_Addon_un.onInit

