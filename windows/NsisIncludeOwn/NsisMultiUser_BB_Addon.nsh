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

;  @app NSIS Installer Script - NsisMultiUser_BB_Addon.nsh
;  @url https://github.com/bleachbit
;  @os Windows
;  @scriptversion v1.0.0
;  @scriptdate 2019-04-17
;  @scriptby Tobias B. Besemer (2019-04-07 - 2019-04-17)
;  @tested ok v1.0.0, Windows 7
;  @testeddate 2019-04-17
;  @testedby https://github.com/Tobias-B-Besemer
;  @note 

;  Notes:
;  ======
;  NsisMultiUser Addon for advanced multi user functionality.
;  
;  Must be loaded after MULTIUSER_PAGE_INSTALLMODE!

; Always show the language selection dialog, even if a language has been stored
; in the registry. The language stored in the registry will be selected by default.
; We need also "MUI_LANGDLL_ALWAYSSHOW", or the user can never ever change his language!
; Make this define a comment, if you use NsisMultiUser_LVC_Addon.nsh!
!ifndef NoTranslations
  !define /IfNDef MUI_LANGDLL_ALWAYSSHOW
!endif

; Interface Settings:
; Show all languages, despite user's codepage:
; https://nsis.sourceforge.io/Why_does_the_language_selection_dialog_hide_some_languages
!ifndef NoTranslations
  !define /IfNDef MUI_LANGDLL_ALLLANGUAGES
!endif

; Show a message box with a warning when the user wants to close the installer:
!define MUI_ABORTWARNING
!define MUI_ABORTWARNING_CANCEL_DEFAULT
!define MUI_UNABORTWARNING
!define MUI_UNABORTWARNING_CANCEL_DEFAULT

; Add/Remove system macros:
; From: https://nsis.sourceforge.io/Add/Remove_Functionality + modified by Tobias
Var NsisMultiUser_BB_Addon_AddRemove_SecFlags
Var NsisMultiUser_BB_Addon_AddRemove_RegFlags

!macro NsisMultiUser_BB_Addon_SetShellVarContextMacro un
  ; Macro/Function "NsisMultiUser_BB_Addon_SetShellVarContext":
  ; As we need SetShellVarContext on different places, and must call it each time,
  ; we move it into a Function.
  ; As we only can call functions starting with "un." from the uninstaller section,
  ; and only functions without "un." from the installer section, we have to move the
  ; funtion into a macro.
  ; Insert function as an installer and uninstaller function:
  ; !insertmacro NsisMultiUser_BB_Addon_SetShellVarContextMacro ""
  ; !insertmacro NsisMultiUser_BB_Addon_SetShellVarContextMacro "un."
  Function ${un}NsisMultiUser_BB_Addon_SetShellVarContextFunction
    ; Use SetShellVarContext to use the right folders.
    ; See: https://nsis.sourceforge.io/Reference/SetShellVarContext
    ${if} $MultiUser.InstallMode == "AllUsers" ; setting defaults
      SetShellVarContext all
    ${else}
      SetShellVarContext current
    ${endif}
  FunctionEnd
!macroend

; Macro/Function "NsisMultiUser_BB_Addon_SetShellVarContext":
; Insert function as an installer and uninstaller function:
!insertmacro NsisMultiUser_BB_Addon_SetShellVarContextMacro ""
!insertmacro NsisMultiUser_BB_Addon_SetShellVarContextMacro "un."

;--- Add/Remove system macros: ---

!macro NsisMultiUser_BB_Addon_AddRemove_InitSection SecName
  ; This macro reads component installed flag from the registry and
  ; changes checked state of the section on the components page.
  ; Input: section index constant name specified in Section command.

  ; But only if it is not a fresh install!
  ReadRegStr $1 SHCTX "${MULTIUSER_INSTALLMODE_UNINSTALL_REGISTRY_KEY_PATH}" "InstallLocation"
  ${if} $1 != ""
    Goto "start_${SecName}"
  ${endif}
  ReadRegStr $1 SHCTX "${MULTIUSER_INSTALLMODE_UNINSTALL_REGISTRY_KEY_PATH}$0" "InstallLocation"
  ${if} $1 != ""
    Goto "start_${SecName}"
  ${endif}
  Goto "default_${SecName}"

  "start_${SecName}:"
  ClearErrors
  ; Reading component status from registry
  ${if} $MultiUser.InstallMode == "AllUsers" ; setting defaults
    ReadRegDWORD $NsisMultiUser_BB_Addon_AddRemove_RegFlags HKLM "Software\${prodname}\Components\${SecName}" "Installed"
  ${else}
    ReadRegDWORD $NsisMultiUser_BB_Addon_AddRemove_RegFlags HKCU "Software\${prodname}\Components\${SecName}" "Installed"
  ${endif}
  IfErrors "default_${SecName}"
  ; Status will stay default if registry value not found
  ; (component was never installed)
  IntOp $NsisMultiUser_BB_Addon_AddRemove_RegFlags $NsisMultiUser_BB_Addon_AddRemove_RegFlags & 0x0001  ;Turn off all other bits
  SectionGetFlags "${${SecName}}" $NsisMultiUser_BB_Addon_AddRemove_SecFlags  ;Reading default section flags
  IntOp $NsisMultiUser_BB_Addon_AddRemove_SecFlags $NsisMultiUser_BB_Addon_AddRemove_SecFlags & 0xFFFE  ;Turn lowest (enabled) bit off
  IntOp $NsisMultiUser_BB_Addon_AddRemove_SecFlags $NsisMultiUser_BB_Addon_AddRemove_RegFlags | $NsisMultiUser_BB_Addon_AddRemove_SecFlags  ;Change lowest bit

  ; Writing modified flags
  SectionSetFlags ${${SecName}} $NsisMultiUser_BB_Addon_AddRemove_SecFlags

  "default_${SecName}:"
!macroend

!macro NsisMultiUser_BB_Addon_AddRemove_FinishSection SecName
  ; This macro reads section flag set by user and removes the section
  ; if it is not selected.
  ; Then it writes component installed flag to registry
  ; Input: section index constant name specified in Section command.

  SectionGetFlags ${${SecName}} $NsisMultiUser_BB_Addon_AddRemove_SecFlags  ;Reading section flags
  ; Checking lowest bit:
  IntOp $NsisMultiUser_BB_Addon_AddRemove_SecFlags $NsisMultiUser_BB_Addon_AddRemove_SecFlags & 0x0001
  IntCmp $NsisMultiUser_BB_Addon_AddRemove_SecFlags 1 "leave_${SecName}"
    ; Section is not selected:
    ; Calling Section uninstall macro and writing zero installed flag
    !insertmacro "Remove_${${SecName}}"
    ${if} $MultiUser.InstallMode == "AllUsers" ; setting defaults
      WriteRegDWORD HKLM "Software\${prodname}\Components\${SecName}" "Installed" 0
    ${else}
      WriteRegDWORD HKCU "Software\${prodname}\Components\${SecName}" "Installed" 0
    ${endif}
    Goto "exit_${SecName}"

  "leave_${SecName}:"
    ; Section is selected:
    ${if} $MultiUser.InstallMode == "AllUsers" ; setting defaults
      WriteRegDWORD HKLM "Software\${prodname}\Components\${SecName}" "Installed" 1
    ${else}
      WriteRegDWORD HKCU "Software\${prodname}\Components\${SecName}" "Installed" 1
    ${endif}

  "exit_${SecName}:"
!macroend

!macro un.NsisMultiUser_BB_Addon_AddRemove_un.FinishSection SecName
  ; This macro reads section flag set by user and set "Installed" in registry
  ; if it is not a complete uninstall.
  ; Input: section index constant name specified in Section command.

  ${if} $MultiUser.InstallMode == "AllUsers" ; setting defaults
    ReadRegStr $1 SHCTX "${MULTIUSER_INSTALLMODE_UNINSTALL_REGISTRY_KEY_PATH}" "InstallLocation"
    IfErrors 0 +1
    Goto "exit_${SecName}"
    Goto "do_${SecName}"
  ${else}
    ReadRegStr $1 SHCTX "${MULTIUSER_INSTALLMODE_UNINSTALL_REGISTRY_KEY_PATH}$0" "InstallLocation"
    IfErrors 0 +1
    Goto "exit_${SecName}"
    Goto "do_${SecName}"
  ${endif}

  "do_${SecName}:"
  ; Reading section flags:
  SectionGetFlags ${${SecName}} $NsisMultiUser_BB_Addon_AddRemove_SecFlags
  ; Checking lowest bit:
  IntOp $NsisMultiUser_BB_Addon_AddRemove_SecFlags $NsisMultiUser_BB_Addon_AddRemove_SecFlags & 0x0001
  IntCmp $NsisMultiUser_BB_Addon_AddRemove_SecFlags 1 "leave_${SecName}"
    ; Section is not selected:
    ; Writing zero installed flag
    ${if} $MultiUser.InstallMode == "AllUsers" ; setting defaults
      WriteRegDWORD HKLM "Software\${prodname}\Components\${SecName}" "Installed" 0
    ${else}
      WriteRegDWORD HKCU "Software\${prodname}\Components\${SecName}" "Installed" 0
    ${endif}
    Goto "exit_${SecName}"

  "leave_${SecName}:"
    ; Section is selected:
    ${if} $MultiUser.InstallMode == "AllUsers" ; setting defaults
      WriteRegDWORD HKLM "Software\${prodname}\Components\${SecName}" "Installed" 1
    ${else}
      WriteRegDWORD HKCU "Software\${prodname}\Components\${SecName}" "Installed" 1
    ${endif}

  "exit_${SecName}:"
!macroend

;--- End of Add/Remove macros ---

;Function RefreshShellIcons
; http://nsis.sourceforge.net/RefreshShellIcons
Function NsisMultiUser_BB_Addon_RefreshShellIcons
  !define SHCNE_ASSOCCHANGED 0x08000000
  !define SHCNF_IDLIST 0
  System::Call 'shell32.dll::SHChangeNotify(i, i, i, i) v (${SHCNE_ASSOCCHANGED}, ${SHCNF_IDLIST}, 0, 0)'
FunctionEnd
