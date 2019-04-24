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
;  @scriptversion v2.3.0.1080
;  @scriptdate 2019-04-24
;  @scriptby Andrew Ziem (2009-05-14 - 2019-01-21) & Tobias B. Besemer (2019-03-31 - 2019-04-24)
;  @tested ok v2.3.0.1080, Windows 7
;  @testeddate 2019-04-24
;  @testedby https://github.com/Tobias-B-Besemer
;  @note 


;--------------------------------
;Pack header:

; Compress installer exehead with an executable compressor (such as UPX / Petite).

; Paths should be absolute to allow building from any location.
; Note that your executable compressor should not compress the first icon.

!ifdef packhdr
  !packhdr "$%TEMP%\exehead.tmp" '"C:\Program Files\UPX\upx.exe" -9 -q "$%TEMP%\exehead.tmp"'
  ;!packhdr "$%TEMP%\exehead.tmp" '"C:\Program Files\Petite\petite.exe" -9 -b0 -r** -p0 -y "$%TEMP%\exehead.tmp"'
!endif


;--------------------------------
;General defines

; Set this "!define" if you want to generate a installer at home:
; Format: 1.2.3.4
; !define VERSION "2.3.0.1053"

; These "!define"s specify the build you get: (Only set one!)
; !define NoTranslations ; -> "${prodname}-${VERSION}-Setup-English_US-only.exe"
; !define BetaTester     ; -> "${prodname}-${VERSION}-Setup-Beta-Tester.exe"
; !define AlphaTester    ; -> "${prodname}-${VERSION}-Setup-Alpha-Tester.exe"

!define COMPANY_NAME "BleachBit.org" ; used by NsisMultiUser
!define PRODNAME "BleachBit"
; !define LICENSE "$(MUI_LICENSE)" ; keep it general ; MUI_LICENSE gets list under MUI_PAGEs
!define UNINSTALL_FILENAME "uninstall.exe" ; suggested by NsisMultiUser
!define PRODURL "https://www.bleachbit.org"

; !define PathToCleanerML ".." ; Andrew
; !define PathToCleanerML ".." ; Tobias

; Define for InstallDate in Registry:
!define /date InstallDate "%Y%m%d"


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
;Installer-/UnInstaller-Attributes - General Attributes
; https://nsis.sourceforge.io/Docs/Chapter4.html#attribgen

; Unicode requires NSIS version 3 or later
; https://nsis.sourceforge.io/Docs/Chapter1.html#intro-unicode
; ANSI is for Windows 9x!
Unicode true

; ManifestSupportedOS:
ManifestSupportedOS all

; XPStyle:
XPStyle on

; ShowInstDetails/ShowUninstDetails:
ShowInstDetails show
ShowUninstDetails show

; Icons:
Icon "${NSISDIR}\Contrib\Graphics\Icons\orange-install-nsis.ico"
UninstallIcon "${NSISDIR}\Contrib\Graphics\Icons\orange-uninstall-nsis.ico"


;--------------------------------
;Installer-/UnInstaller-Attributes - Version Information
; https://nsis.sourceforge.io/Docs/Chapter4.html#versioninfo

!define File_VERSION 2.3.0.0
; Later:
;!define File_VERSION ${VERSION}

!ifdef NoTranslations
  VIAddVersionKey /LANG=1033 "ProductName" "BleachBit"
  VIAddVersionKey /LANG=1033 "CompanyName" "BleachBit.org"
  VIAddVersionKey /LANG=1033 "LegalCopyright" "BleachBit.org"
  VIAddVersionKey /LANG=1033 "FileDescription" "BleachBit Setup"
  VIAddVersionKey /LANG=1033 "ProductVersion" "${File_VERSION}"
  VIAddVersionKey /LANG=1033 "FileVersion" "${File_VERSION}"
!endif

!ifndef NoTranslations
  VIAddVersionKey /LANG=0 "ProductName" "BleachBit"
  VIAddVersionKey /LANG=0 "CompanyName" "BleachBit.org"
  VIAddVersionKey /LANG=0 "LegalCopyright" "BleachBit.org"
  VIAddVersionKey /LANG=0 "FileDescription" "BleachBit Setup"
  VIAddVersionKey /LANG=0 "ProductVersion" "${File_VERSION}"
  VIAddVersionKey /LANG=0 "FileVersion" "${File_VERSION}"
!endif

VIProductVersion ${File_VERSION}
VIFileVersion ${File_VERSION}


;--------------------------------
;Installer-/UnInstaller-Attributes - Compiler Flags
; https://nsis.sourceforge.io/Docs/Chapter4.html#flags

; Set default compressor:
; https://ci.appveyor.com/ do already "SetCompressor /FINAL zlib"
; Best compression: https://nsis.sourceforge.io/Docs/Chapter1.html#intro-features
!ifdef Compressor
  SetCompressor /SOLID lzma
!endif

Name "${prodname}"

; https://nsis.sourceforge.io/Reference/!ifdef
!ifndef NoTranslations
  !ifdef BetaTester
    ; Beta-Tester includes CleanerML/Release-Cleaners
    OutFile "${prodname}-${VERSION}-Setup-Beta-Tester.exe"
  !endif
  !ifdef AlphaTester
    ; Alpha-Tester includes CleanerML/Pending&Release-Cleaners
    OutFile "${prodname}-${VERSION}-Setup-Alpha-Tester.exe"
    !define BetaTester
  !endif
  !ifndef BetaTester
    OutFile "${prodname}-${VERSION}-Setup.exe"
  !endif
!endif

!ifdef NoTranslations
  OutFile "${prodname}-${VERSION}-Setup-English_US-only.exe"
!endif

!ifdef NoSectionShred
  ; Definded but not used!
!endif

!ifdef NoInstTypes ; allow user to switch the usage of InstTypes
  ; Definded but not used!
!endif


;--------------------------------
;AddPluginDir & AddIncludeDir

; See: https://github.com/Drizin/NsisMultiUser
!AddPluginDir /x86-unicode ".\NsisPluginsUnicode\"

; https://nsis.sourceforge.io/Reference/!addincludedir
!AddIncludeDir ".\NsisIncludeOthers"
!AddIncludeDir ".\NsisIncludeOwn"


;--------------------------------
;System

; Request application privileges for Windows Vista:
; NsisMultiUser sets this, when needed.
; RequestExecutionLevel admin

; Default installation folder
; NsisMultiUser sets the directory.
; InstallDir "$PROGRAMFILES\${prodname}"

; Get installation folder from registry if available
; https://nsis.sourceforge.io/Reference/InstallDirRegKey
; We do this on ".onInit"!
; InstallDirRegKey HKCU "Software\${prodname}" ""


;--------------------------------
;Include NSH-Files and insert Macros

; Include LogicLib:
; https://nsis.sourceforge.io/LogicLib
!include LogicLib.nsh

; Include Sections:
!include Sections.nsh

; Include FileFunc:
; E.g. needed for ${GetSize}
!include FileFunc.nsh

; Include StdUtils:
; https://nsis.sourceforge.io/StdUtils_plug-in
; https://github.com/lordmulder/stdutils
; include StdUtils.nsh

; Include Modern UI 2:
!include MUI2.nsh

; Include MultiUser:
; See: https://github.com/Drizin/NsisMultiUser
!include NsisMultiUser.nsh


;--------------------------------
;Reserve Files
; If you are using solid compression, files that are required before
; the actual installation should be stored first in the data block,
; because this will make your installer start faster.
;!insertmacro MUI_RESERVEFILE_LANGDLL


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
!insertmacro MUI_PAGE_LICENSE "$(MUI_LICENSE)"
!define MUI_PAGE_CUSTOMFUNCTION_PRE "MULTIUSER_PAGE_INSTALLMODE_Pre"
!define MUI_PAGE_CUSTOMFUNCTION_LEAVE "MULTIUSER_PAGE_INSTALLMODE_Leave"
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
!define MUI_UNWELCOMEFINISHPAGE_BITMAP "picture.MUI2\bleachbit_164x314.bmp"
!insertmacro MUI_UNPAGE_WELCOME
!insertmacro MUI_UNPAGE_CONFIRM
!define MUI_PAGE_CUSTOMFUNCTION_PRE "un.MULTIUSER_UnPAGE_INSTALLMODE_Pre"
!define MUI_PAGE_CUSTOMFUNCTION_LEAVE "un.MULTIUSER_UnPAGE_INSTALLMODE_Leave"
!insertmacro MULTIUSER_UNPAGE_INSTALLMODE
; MUI_UNPAGE_DIRECTORY not needed, ATM.
; !insertmacro MUI_UNPAGE_DIRECTORY
!insertmacro MUI_UNPAGE_COMPONENTS
UninstallText $(BLEACHBIT_UNINSTALL_TEXT)
!insertmacro MUI_UNPAGE_INSTFILES
!define MUI_UNFINISHPAGE_NOAUTOCLOSE
!insertmacro MUI_UNPAGE_FINISH

; MUI_LANGUAGE[EX] should be inserted after the MUI_[UN]PAGE_* macros!

;--------------------------------
;Include after the MUI_[UN]PAGE_* macros some more NSH-Files

; Our Language Code:
; Must be loaded before the language files!
!include bleachbit_language_code.nsh
!include bleachbit_language_strings.nsh

; NsisMultiUser Language Files:
; Must be loaded after MUI_PAGEs!
!include NsisMultiUserLang.nsh

; NsisMultiUser LVC Addon Language Files:
; Must be loaded after MUI_LANGUAGE (bleachbit_language_code.nsh)!
!include NsisMultiUser_LVC_Addon_Lang.nsh

; Include NsisMultiUser LVC Addon:
; See: https://github.com/LV-Crew
; Must be loaded after MULTIUSER_PAGE_INSTALLMODE!
!include NsisMultiUser_LVC_Addon.nsh

; Include NsisMultiUser BleachBit Addon:
; Must be loaded after MULTIUSER_PAGE_INSTALLMODE!
!include NsisMultiUser_BB_Addon.nsh


;--------------------------------
;Installation Types

; From: https://nsis.sourceforge.io/SetSectionInInstType,_ClearSectionInInstType

; The defines for more than 8 installation types are included in
; Sections.nsh
 
!ifndef NoInstTypes  ; allow user to switch the usage of InstTypes
  InstType $(BLEACHBIT_INSTALLATIONTYPE_COMPLETE) ; ${INSTTYPE_1}
  InstType $(BLEACHBIT_INSTALLATIONTYPE_STANDARD) ; ${INSTTYPE_2}
  InstType $(BLEACHBIT_INSTALLATIONTYPE_MINIMAL)  ; ${INSTTYPE_3}
!endif


;--------------------------------
;Add/Remove callback functions

!macro SectionList BB_Language_InstallerSections_Translations_PerformRemoveOperations
  ; This macro used to perform operation on multiple sections.
  !insertmacro "${BB_Language_InstallerSections_Translations_PerformRemoveOperations}" "Cleaners Stable"
  !ifdef BetaTester
    !insertmacro "${BB_Language_InstallerSections_Translations_PerformRemoveOperations}" "Cleaners Beta"
    !ifdef AlphaTester
      !insertmacro "${BB_Language_InstallerSections_Translations_PerformRemoveOperations}" "Cleaners Alpha"
    !endif
  !endif
  !insertmacro "${BB_Language_InstallerSections_Translations_PerformRemoveOperations}" "Installer"
  !insertmacro "${BB_Language_InstallerSections_Translations_PerformRemoveOperations}" "Shortcuts Start Menu"
  !insertmacro "${BB_Language_InstallerSections_Translations_PerformRemoveOperations}" "Shortcut Desktop"
  !insertmacro "${BB_Language_InstallerSections_Translations_PerformRemoveOperations}" "Shortcut Quick Launch"
  !insertmacro "${BB_Language_InstallerSections_Translations_PerformRemoveOperations}" "Shortcut Autostart"
  !ifndef NoTranslations
    !include bleachbit_language_code_addremove_performremoveoperations.nsi
  !endif
  !insertmacro "${BB_Language_InstallerSections_Translations_PerformRemoveOperations}" "Shred for Explorer"
!macroend


;--------------------------------
;Macro/Function "Uninstall"

; We need to move the code from Section "Uninstall" into a function that he can
; be executed from command line with /uninstall, too.
; As we only can call functions starting with "un." from the uninstaller section,
; and only functions without "un." from the installer section, we have to move the
; funtion into a macro.

!macro uninstallmacro un
  Function ${un}uninstallfunction
    ; Set Error Level 666 if "SystemComponent" was set.
    Call ${un}NsisMultiUser_LVC_Addon_ErrorLevel-666_Set

    ; Core and all folders & files in $INSTDIR:
    RMDir /r "$INSTDIR"

    ; Delete normal, Start menu shortcuts:
    RMDir /r "$SMPROGRAMS\${prodname}"

    ; Delete Desktop shortcut:
    Delete "$DESKTOP\BleachBit.lnk"

    ; Delete Quick launch shortcut:
    Delete "$QUICKLAUNCH\BleachBit.lnk"

    ; Delete Autostart shortcut:
    Delete "$SMSTARTUP\BleachBit.lnk"

    ; Remove file association (Shredder):
    DeleteRegKey HKCR "AllFileSystemObjects\shell\shred.bleachbit"

    ; We only delete the registry keys to BleachBit if we don't make a upgrade
    StrCmp $NsisMultiUser_LVC_Addon_Upgrade "Yes" after_registry

    ${if} $MultiUser.InstallMode == "AllUsers" ; setting defaults
      DeleteRegKey HKLM "Software\${prodname}"
      DeleteRegKey HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${prodname}"
      DeleteRegKey HKLM "SOFTWARE\Wow6432Node\Microsoft\Windows\CurrentVersion\Uninstall\${prodname}"
    ${else}
      DeleteRegKey HKCU "Software\${prodname}"
      DeleteRegKey HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\${prodname}"
    ${endif}

    ; Remove the uninstaller from registry as the very last step - if something goes wrong, let the user run it again.
    !insertmacro MULTIUSER_RegistryRemoveInstallInfo

    after_registry:

    ; And in the example follows after that:
    Delete "$INSTDIR\${UNINSTALL_FILENAME}"
    RMDir /r "$INSTDIR"
  FunctionEnd
!macroend

; Insert function as an installer and uninstaller function:
!insertmacro uninstallmacro ""
!insertmacro uninstallmacro "un."


;--------------------------------
;Installer Sections

; BleachBit Core
Section SectionCore "Core" ; (Required)
  ; "SectionIn RO" means: Section defined mandatory, so that the user can not unselect them!
  SectionIn RO

  ; Copy files
  SetOutPath "$INSTDIR\"
  File "..\dist\*.*"
  File "..\COPYING"
!ifndef NoTranslations
  SetOutPath "$INSTDIR\license\"
  File "..\license\*.*"
!endif
  SetOutPath "$INSTDIR\data\"
  File /r "..\dist\data\*.*"
  SetOutPath "$INSTDIR\etc\"
  File /r "..\dist\etc\*.*"
  SetOutPath "$INSTDIR\lib\"
  File /r "..\dist\lib\*.*"
  SetOutPath "$INSTDIR\share\"
  File /r "..\dist\share\*.*"
  File "..\bleachbit.png"

  ; Write uninstaller
  WriteUninstaller "$INSTDIR\uninstall.exe"

  ; Register uninstaller in Add/Remove Programs
  !insertmacro MULTIUSER_RegistryAddInstallInfo ; add registry keys
  ${if} $MultiUser.InstallMode == "AllUsers" ; setting defaults
    WriteRegStr SHCTX "${MULTIUSER_INSTALLMODE_UNINSTALL_REGISTRY_KEY_PATH}" \
      "Contact" "info@bleachbit.org"
    WriteRegStr SHCTX "${MULTIUSER_INSTALLMODE_UNINSTALL_REGISTRY_KEY_PATH}" \
      "HelpLink" "https://www.bleachbit.org/help"
    WriteRegStr SHCTX "${MULTIUSER_INSTALLMODE_UNINSTALL_REGISTRY_KEY_PATH}" \
      "URLInfoAbout" "https://www.bleachbit.org/"
    WriteRegStr SHCTX "${MULTIUSER_INSTALLMODE_UNINSTALL_REGISTRY_KEY_PATH}" \
      "URLUpdateInfo" "https://www.bleachbit.org/download"
    ; https://nsis.sourceforge.io/Add_uninstall_information_to_Add/Remove_Programs#Recommended_values
    WriteRegStr SHCTX "${MULTIUSER_INSTALLMODE_UNINSTALL_REGISTRY_KEY_PATH}" \
      "QuietUninstallString" '"$INSTDIR\unistall.exe" /allusers /S /D="$INSTDIR"'
  ${else}
    WriteRegStr SHCTX "${MULTIUSER_INSTALLMODE_UNINSTALL_REGISTRY_KEY_PATH}$0" \
      "Contact" "info@bleachbit.org"
    WriteRegStr SHCTX "${MULTIUSER_INSTALLMODE_UNINSTALL_REGISTRY_KEY_PATH}$0" \
      "HelpLink" "https://www.bleachbit.org/help"
    WriteRegStr SHCTX "${MULTIUSER_INSTALLMODE_UNINSTALL_REGISTRY_KEY_PATH}$0" \
      "URLInfoAbout" "https://www.bleachbit.org/"
    WriteRegStr SHCTX "${MULTIUSER_INSTALLMODE_UNINSTALL_REGISTRY_KEY_PATH}$0" \
      "URLUpdateInfo" "https://www.bleachbit.org/download"
    ; https://nsis.sourceforge.io/Add_uninstall_information_to_Add/Remove_Programs#Recommended_values
    WriteRegStr SHCTX "${MULTIUSER_INSTALLMODE_UNINSTALL_REGISTRY_KEY_PATH}$0" \
      "QuietUninstallString" '"$INSTDIR\unistall.exe" /currentuser /S /D="$INSTDIR"'
  ${endif}

  ; Handle Error Level 666 if "SystemComponent" was set.
  ; Restores the old settings by install.
  Call NsisMultiUser_LVC_Addon_ErrorLevel-666_Handle
SectionEnd

; BleachBit Cleaners
SectionGroup SectionGroupCleaners "Group Cleaners"
  Section SectionCleanersStable "Cleaners Stable"
    SetOutPath "$INSTDIR\share\cleaners\"
    File "..\dist\share\cleaners\*.*"
  SectionEnd
  !macro "Remove_${Cleaners Stable}"
    ;Removes component
    Delete "$INSTDIR\share\cleaners\*.*"
  !macroend

!ifdef BetaTester
  Section SectionCleanersBeta "Cleaners Beta"
    SetOutPath "$INSTDIR\share\cleaners\"
    File "${PathToCleanerML}\cleanerml\release\*.*"
  SectionEnd
  !macro "Remove_${Cleaners Beta}"
    ;Removes component
    Delete "$INSTDIR\share\cleaners\*.*"
  !macroend

!ifdef AlphaTester
  Section SectionCleanersAlpha "Cleaners Alpha"
    SetOutPath "$INSTDIR\share\cleaners\"
    File "${PathToCleanerML}\cleanerml\pending\*.*"
  SectionEnd
  !macro "Remove_${Cleaners Alpha}"
    ;Removes component
    Delete "$INSTDIR\share\cleaners\*.*"
  !macroend
!endif
!endif
SectionGroupEnd

; BleachBit Installer
Section SectionInstaller "Installer"
  ; We need to copy the installer in four steps to make sure the install "arrives" in all cases!
  ; We can't use installer.exe as name, because installer.exe seems to be a protected name!
  ; https://stackoverflow.com/questions/14936193/nsis-how-to-get-the-filename-of-the-installer-executable
  ; https://nsis.sourceforge.io/Get_installer_filename
  IfFileExists "$INSTDIR\install.exe" +4 0
  CopyFiles /SILENT "$EXEDIR\$EXEFILE" "$INSTDIR"
  SetOutPath "$INSTDIR"
  Rename /REBOOTOK "$INSTDIR\$EXEFILE" "install.exe"

  ${if} $MultiUser.InstallMode == "AllUsers" ; setting defaults
    WriteRegDWORD SHCTX "${MULTIUSER_INSTALLMODE_UNINSTALL_REGISTRY_KEY_PATH}" \
      "NoRepair" 0
    WriteRegDWORD SHCTX "${MULTIUSER_INSTALLMODE_UNINSTALL_REGISTRY_KEY_PATH}" \
      "NoModify" 0
    WriteRegStr SHCTX "${MULTIUSER_INSTALLMODE_UNINSTALL_REGISTRY_KEY_PATH}" \
      "ModifyPath" '"$INSTDIR\install.exe" /allusers /D="$INSTDIR"'
  ${else}
    WriteRegDWORD SHCTX "${MULTIUSER_INSTALLMODE_UNINSTALL_REGISTRY_KEY_PATH}$0" \
      "NoRepair" 0
    WriteRegDWORD SHCTX "${MULTIUSER_INSTALLMODE_UNINSTALL_REGISTRY_KEY_PATH}$0" \
      "NoModify" 0
    WriteRegStr SHCTX "${MULTIUSER_INSTALLMODE_UNINSTALL_REGISTRY_KEY_PATH}$0" \
      "ModifyPath" '"$INSTDIR\install.exe" /currentuser /D="$INSTDIR"'
  ${endif}
SectionEnd
!macro "Remove_${Installer}"
  ;Removes component
  Delete "$INSTDIR\installer.exe"
  ${if} $MultiUser.InstallMode == "AllUsers" ; setting defaults
    WriteRegDWORD SHCTX "${MULTIUSER_INSTALLMODE_UNINSTALL_REGISTRY_KEY_PATH}" \
      "NoRepair" 1
    DeleteRegValue SHCTX "${MULTIUSER_INSTALLMODE_UNINSTALL_REGISTRY_KEY_PATH}" \
      "NoModify"
    DeleteRegValue SHCTX "${MULTIUSER_INSTALLMODE_UNINSTALL_REGISTRY_KEY_PATH}" \
      "ModifyPath"
  ${else}
    WriteRegDWORD SHCTX "${MULTIUSER_INSTALLMODE_UNINSTALL_REGISTRY_KEY_PATH}$0" \
      "NoRepair" 1
    DeleteRegValue SHCTX "${MULTIUSER_INSTALLMODE_UNINSTALL_REGISTRY_KEY_PATH}$0" \
      "NoModify"
    DeleteRegValue SHCTX "${MULTIUSER_INSTALLMODE_UNINSTALL_REGISTRY_KEY_PATH}$0" \
      "ModifyPath"
  ${endif}
!macroend

; BleachBit Shortcuts
SectionGroup /e SectionGroupShortcuts "Group Shortcuts"
  ; BleachBit Start Menu Shortcuts
  Section SectionShortcutsStartMenu "Shortcuts Start Menu"
    ; Use NsisMultiUser_BB_Addon_SetShellVarContextFunction to use the right folders (All Users/Current User)
    Call NsisMultiUser_BB_Addon_SetShellVarContextFunction
    SetOutPath "$INSTDIR\" ; this affects CreateShortCut's 'Start in' directory
    CreateDirectory "$SMPROGRAMS\${prodname}"
    CreateShortCut "$SMPROGRAMS\${prodname}\${prodname}.lnk" \
      "$INSTDIR\${prodname}.exe"
    CreateShortCut "$SMPROGRAMS\${prodname}\${prodname} $(BLEACHBIT_COMPONENT_SHORTCUTS_STARTMENU_LINK_NO_UAC).lnk" \
      "$INSTDIR\${prodname}.exe" \
      "--no-uac --gui"
    CreateShortCut "$SMPROGRAMS\${prodname}\${prodname} $(BLEACHBIT_COMPONENT_SHORTCUTS_STARTMENU_LINK_DEBUGGING_TERMINAL).lnk" \
      "$INSTDIR\${prodname}_console.exe"
    WriteINIStr "$SMPROGRAMS\${prodname}\${prodname} $(BLEACHBIT_COMPONENT_SHORTCUTS_STARTMENU_LINK_HOME_PAGE).url" \
      "InternetShortcut" "URL" "https://www.bleachbit.org/"
    IfFileExists "$INSTDIR\install.exe" 0 +6
      ${if} $MultiUser.InstallMode == "AllUsers" ; setting defaults
        CreateShortCut "$SMPROGRAMS\${prodname}\${prodname} $(BLEACHBIT_COMPONENT_SHORTCUTS_STARTMENU_LINK_REPAIR).lnk" "$INSTDIR\install.exe" '/allusers /D="$INSTDIR"'
      ${else}
        CreateShortCut "$SMPROGRAMS\${prodname}\${prodname} $(BLEACHBIT_COMPONENT_SHORTCUTS_STARTMENU_LINK_REPAIR).lnk" "$INSTDIR\install.exe" '/currentuser /D="$INSTDIR"'
      ${endif}
    CreateShortCut "$SMPROGRAMS\${prodname}\${prodname} $(BLEACHBIT_COMPONENT_SHORTCUTS_STARTMENU_LINK_UNINSTALL).lnk" \
      "$INSTDIR\uninstall.exe"
    Call NsisMultiUser_BB_Addon_RefreshShellIcons
  SectionEnd
  !macro "Remove_${Shortcuts Start Menu}"
    ;Removes component
    Call NsisMultiUser_BB_Addon_SetShellVarContextFunction
    RMDir /r "$SMPROGRAMS\${prodname}\"
  !macroend

  ; BleachBit Desktop Shortcut
  Section SectionShortcutsDesktop "Shortcut Desktop"
    ; Checking for NsisMultiUser_LVC_Addon_Command_Line_No_Desktop_Shortcut. It's "No" by default. If "Yes": NO DESKTOP SHORTCUT!
    ${if} $NsisMultiUser_LVC_Addon_Command_Line_No_Desktop_Shortcut == "No"
      ; Use NsisMultiUser_BB_Addon_SetShellVarContextFunction to use the right folders (All Users/Current User)
      Call NsisMultiUser_BB_Addon_SetShellVarContextFunction
      SetOutPath "$INSTDIR\" ; this affects CreateShortCut's 'Start in' directory
      CreateShortcut "$DESKTOP\BleachBit.lnk" "$INSTDIR\${prodname}.exe"
      Call NsisMultiUser_BB_Addon_RefreshShellIcons
    ${endif}
  SectionEnd
  !macro "Remove_${Shortcut Desktop}"
    ;Removes component
    Call NsisMultiUser_BB_Addon_SetShellVarContextFunction
    Delete "$DESKTOP\BleachBit.lnk"
  !macroend

  ; BleachBit Quick Launch Shortcut
  Section /o SectionShortcutsQuickLaunch "Shortcut Quick Launch"
    ; Use NsisMultiUser_BB_Addon_SetShellVarContextFunction to use the right folders (All Users/Current User)
    Call NsisMultiUser_BB_Addon_SetShellVarContextFunction
    SetOutPath "$INSTDIR\" ; this affects CreateShortCut's 'Start in' directory
    CreateShortcut "$QUICKLAUNCH\BleachBit.lnk" "$INSTDIR\${prodname}.exe"
    Call NsisMultiUser_BB_Addon_RefreshShellIcons
  SectionEnd
  !macro "Remove_${Shortcut Quick Launch}"
    ;Removes component
    Call NsisMultiUser_BB_Addon_SetShellVarContextFunction
    Delete "$QUICKLAUNCH\BleachBit.lnk"
  !macroend

  ; BleachBit Autostart Shortcut
  Section /o SectionShortcutsAutostart "Shortcut Autostart"
    ; Use NsisMultiUser_BB_Addon_SetShellVarContextFunction to use the right folders (All Users/Current User)
    Call NsisMultiUser_BB_Addon_SetShellVarContextFunction
    SetOutPath "$INSTDIR\" ; this affects CreateShortCut's 'Start in' directory
    ; Making shortcuts run minimized in NSIS:
    ; https://stackoverflow.com/questions/1018563/making-shortcuts-run-minimized-in-nsis
    CreateShortcut "$SMSTARTUP\BleachBit.lnk" "$INSTDIR\${prodname}.exe" "" "" "" SW_SHOWMINIMIZED
    Call NsisMultiUser_BB_Addon_RefreshShellIcons
  SectionEnd
  !macro "Remove_${Shortcut Autostart}"
    ;Removes component
    Call NsisMultiUser_BB_Addon_SetShellVarContextFunction
    Delete "$SMSTARTUP\BleachBit.lnk"
  !macroend
SectionGroupEnd

; BleachBit Translations
SectionGroup SectionGroupTranslations "Group Translations"
  !include bleachbit_language_code_installsection_translations.nsi
SectionGroupEnd

; Section for making Shred Integration Optional
!ifndef NoSectionShred
  Section SectionShredForExplorer "Shred for Explorer"
    ; register file association verb
    WriteRegStr HKCR "AllFileSystemObjects\shell\shred.bleachbit" "" "$(BLEACHBIT_SHREDFOREXPLORER_SHELL_TITLE)"
    WriteRegStr HKCR "AllFileSystemObjects\shell\shred.bleachbit" "Icon" "$INSTDIR\bleachbit.exe,0"
    WriteRegStr HKCR "AllFileSystemObjects\shell\shred.bleachbit\command" "" '"$INSTDIR\bleachbit.exe" --gui --no-uac --shred "%1"'
  SectionEnd
  !macro "Remove_${Shred for Explorer}"
    ;Removes component
    DeleteRegKey HKCR "AllFileSystemObjects\shell\shred.bleachbit"
  !macroend
!endif


;--------------------------------
;Descriptions for the Installer Components

; USE A LANGUAGE STRING IF YOU WANT YOUR DESCRIPTIONS TO BE LANGUAGE SPECIFIC

; Assign descriptions to sections:
; Variable/Constant must be declared by Installer Sections! Place MUI_FUNCTION_DESCRIPTION after it!
!insertmacro MUI_FUNCTION_DESCRIPTION_BEGIN
  !insertmacro MUI_DESCRIPTION_TEXT "${Core}" $(BLEACHBIT_COMPONENT_CORE_DESCRIPTION)
  !insertmacro MUI_DESCRIPTION_TEXT "${Group Cleaners}" $(BLEACHBIT_COMPONENTGROUP_CLEANERS_DESCRIPTION)
  !insertmacro MUI_DESCRIPTION_TEXT "${Cleaners Stable}" $(BLEACHBIT_COMPONENT_CLEANERS_STABLE_DESCRIPTION)
  !ifdef BetaTester
    !insertmacro MUI_DESCRIPTION_TEXT "${Cleaners Beta}" $(BLEACHBIT_COMPONENT_CLEANERS_BETA_DESCRIPTION)
    !ifdef AlphaTester
      !insertmacro MUI_DESCRIPTION_TEXT "${Cleaners Alpha}" $(BLEACHBIT_COMPONENT_CLEANERS_ALPHA_DESCRIPTION)
    !endif
  !endif
  !insertmacro MUI_DESCRIPTION_TEXT "${Installer}" $(BLEACHBIT_COMPONENT_INSTALLER_DESCRIPTION)
  !insertmacro MUI_DESCRIPTION_TEXT "${Group Shortcuts}" $(BLEACHBIT_COMPONENTGROUP_SHORTCUTS_DESCRIPTION)
  !insertmacro MUI_DESCRIPTION_TEXT "${Shortcuts Start Menu}" $(BLEACHBIT_COMPONENT_SHORTCUTS_STARTMENU_DESCRIPTION)
  !insertmacro MUI_DESCRIPTION_TEXT "${Shortcut Desktop}" $(BLEACHBIT_COMPONENT_SHORTCUTS_DESKTOP_DESCRIPTION)
  !insertmacro MUI_DESCRIPTION_TEXT "${Shortcut Quick Launch}" $(BLEACHBIT_COMPONENT_SHORTCUTS_QUICKLAUNCH_DESCRIPTION)
  !insertmacro MUI_DESCRIPTION_TEXT "${Shortcut Autostart}" $(BLEACHBIT_COMPONENT_SHORTCUTS_AUTOSTART_DESCRIPTION)
  !insertmacro MUI_DESCRIPTION_TEXT "${Group Translations}" $(BLEACHBIT_COMPONENTGROUP_TRANSLATIONS_DESCRIPTION)
  !insertmacro BB_Language_Installer_MUI_Description_Text_Translations
  !ifndef NoSectionShred
    !insertmacro MUI_DESCRIPTION_TEXT "${Shred for Explorer}" $(BLEACHBIT_COMPONENT_SHREDFOREXPLORER_DESCRIPTION)
  !endif
!insertmacro MUI_FUNCTION_DESCRIPTION_END


;--------------------------------
;Installer Functions

Function .onInit
  ; Start NsisMultiUser_LVC_Addon_onInit-Functionality:
  Call NsisMultiUser_LVC_Addon_onInit

  ; Insert Macro MUI_LANGDLL_DISPLAY:
  ; This is the language display dialog!
  ; MUI_LANGDLL_DISPLAY should only be used after inserting the MUI_LANGUAGE macro(s)!
  ; Command IfSilent not valid outside Section or Function!
  !insertmacro MUI_LANGDLL_DISPLAY

  ; Add the Sections to the InstTypes:
  ; MUI_LANGDLL_DISPLAY must be loaded first!
  ; (BB_Language_InstallerSections_Translations_SetSectionInInstType use "$Language"!)
  !insertmacro SetSectionInInstType "${Core}" "${INSTTYPE_1}"
  !insertmacro SetSectionInInstType "${Core}" "${INSTTYPE_2}"
  !insertmacro SetSectionInInstType "${Core}" "${INSTTYPE_3}"
  !insertmacro SetSectionInInstType "${Cleaners Stable}" "${INSTTYPE_1}"
  !insertmacro SetSectionInInstType "${Cleaners Stable}" "${INSTTYPE_2}"
  !insertmacro SetSectionInInstType "${Cleaners Stable}" "${INSTTYPE_3}"
  !ifdef BetaTester
    !insertmacro SetSectionInInstType "${Cleaners Beta}" "${INSTTYPE_1}"
    !insertmacro SetSectionInInstType "${Cleaners Beta}" "${INSTTYPE_2}"
    !insertmacro SetSectionInInstType "${Cleaners Beta}" "${INSTTYPE_3}"
    !ifdef AlphaTester
      !insertmacro SetSectionInInstType "${Cleaners Alpha}" "${INSTTYPE_1}"
      !insertmacro SetSectionInInstType "${Cleaners Alpha}" "${INSTTYPE_2}"
      !insertmacro SetSectionInInstType "${Cleaners Alpha}" "${INSTTYPE_3}"
    !endif
  !endif
  !insertmacro SetSectionInInstType "${Installer}" "${INSTTYPE_1}"
  !insertmacro SetSectionInInstType "${Installer}" "${INSTTYPE_2}"
  !insertmacro SetSectionInInstType "${Shortcuts Start Menu}" "${INSTTYPE_1}"
  !insertmacro SetSectionInInstType "${Shortcuts Start Menu}" "${INSTTYPE_2}"
  !insertmacro SetSectionInInstType "${Shortcuts Start Menu}" "${INSTTYPE_3}"
  !insertmacro SetSectionInInstType "${Shortcut Desktop}" "${INSTTYPE_1}"
  !insertmacro SetSectionInInstType "${Shortcut Desktop}" "${INSTTYPE_2}"
  !insertmacro SetSectionInInstType "${Shortcut Quick Launch}" "${INSTTYPE_1}"
  !insertmacro SetSectionInInstType "${Shortcut Autostart}" "${INSTTYPE_1}"
  !insertmacro BB_Language_Installer_SetSectionInInstType_Translations
  !ifndef NoSectionShred
    !insertmacro SetSectionInInstType "${Shred for Explorer}" "${INSTTYPE_1}"
    !insertmacro SetSectionInInstType "${Shred for Explorer}" "${INSTTYPE_2}"
    !insertmacro SetSectionInInstType "${Shred for Explorer}" "${INSTTYPE_3}"
  !endif

  ; Set the current Installation Type to 1. (1 = "Standard")
  ; SetCurInstType must be set after "!insertmacro SetSectionInInstType"!
  ; https://nsis.sourceforge.io/Reference/SetCurInstType
  !ifndef NoTranslations
    SetCurInstType 1
  !endif
  !ifdef NoTranslations
    SetCurInstType 2
  !endif

  ; Reads components status from registry
  ; But only if it is not a fresh install!
  !insertmacro SectionList "NsisMultiUser_BB_Addon_AddRemove_InitSection"
FunctionEnd

; And now starts the GUI Installer...

Function MULTIUSER_PAGE_INSTALLMODE_Pre
  ; It figured out that in some cases we get a wrong "$INSTDIR" (via command line). Seems to be a bug in
  ; NsisMultiUser we can't find for now. So to go sure, we set some values before we start again with
  ; NsisMultiUser.
  Call NsisMultiUser_LVC_Addon_Set_NsisMultiUser
FunctionEnd

Function MULTIUSER_PAGE_INSTALLMODE_Leave
  ${if} $MultiUser.InstallMode == "AllUsers" ; setting defaults
    SetShellVarContext all
    !define /redef UMUI_PARAMS_REGISTRY_ROOT HKLM
  ${else}
    SetShellVarContext current
    !define /redef UMUI_PARAMS_REGISTRY_ROOT HKCU
  ${endif}

  ; SectionSetText:
  !insertmacro BB_Language_Installer_SectionSetText
FunctionEnd

Section -FinishComponents
  ; Removes unselected components and writes component status to registry
  !insertmacro SectionList "NsisMultiUser_BB_Addon_AddRemove_FinishSection"
SectionEnd

; Keep this section last. It must be last because that is when the
; actual size is known.
; This is a hidden section.
Section "-Write Install Size"
  !insertmacro MULTIUSER_RegistryAddInstallSizeInfo
SectionEnd

Section -Post
  ; Write/Update the "InstallDate" (also after component add/remove & repair):
  ${if} $MultiUser.InstallMode == "AllUsers" ; setting defaults
    WriteRegStr SHCTX "${MULTIUSER_INSTALLMODE_UNINSTALL_REGISTRY_KEY_PATH}" "InstallDate" "${InstallDate}"
  ${else}
    WriteRegStr SHCTX "${MULTIUSER_INSTALLMODE_UNINSTALL_REGISTRY_KEY_PATH}$0" "InstallDate" "${InstallDate}"
  ${endif}

  ; Macro/Function "NsisMultiUser_LVC_Addon_SectionPost"
  ; Save the Language Selection Dialog Setting
  ; We need also "MUI_LANGDLL_ALWAYSSHOW", or the user can never ever change his language!
  Call NsisMultiUser_LVC_Addon_SectionPost
SectionEnd

;--------------------------------
;Uninstaller Sections

; BleachBit Core
Section un.SectionCore "un.Core"
  ; Use NsisMultiUser_BB_Addon_SetShellVarContextFunction to use the right folders (All Users/Current User)
  Call un.NsisMultiUser_BB_Addon_SetShellVarContextFunction

  Call un.uninstallfunction
SectionEnd

; BleachBit Cleaners
SectionGroup un.SectionGroupCleaners "un.Group Cleaners"
Section un.SectionCleanersStable "un.Cleaners Stable"
  RMDir /r "$INSTDIR\share\cleaners\"
SectionEnd

!ifdef BetaTester
Section un.SectionCleanersBeta "un.Cleaners Beta"
  RMDir /r "$INSTDIR\share\cleaners\"
SectionEnd

!ifdef AlphaTester
Section un.SectionCleanersAlpha "un.Cleaners Alpha"
  RMDir /r "$INSTDIR\share\cleaners\"
SectionEnd
!endif
!endif
SectionGroupEnd

; BleachBit Installer
Section un.SectionInstaller "un.Installer"
  Delete "$INSTDIR\installer.exe"
  ${if} $MultiUser.InstallMode == "AllUsers" ; setting defaults
    DeleteRegValue SHCTX "${MULTIUSER_INSTALLMODE_UNINSTALL_REGISTRY_KEY_PATH}" \
      "NoRepair"
    DeleteRegValue SHCTX "${MULTIUSER_INSTALLMODE_UNINSTALL_REGISTRY_KEY_PATH}" \
      "ModifyPath"
  ${else}
    DeleteRegValue SHCTX "${MULTIUSER_INSTALLMODE_UNINSTALL_REGISTRY_KEY_PATH}$0" \
      "NoRepair"
    DeleteRegValue SHCTX "${MULTIUSER_INSTALLMODE_UNINSTALL_REGISTRY_KEY_PATH}$0" \
      "ModifyPath"
  ${endif}
SectionEnd

; BleachBit Shortcuts
SectionGroup /e un.SectionGroupShortcuts "un.Group Shortcuts"
  ; BleachBit Start Menu Shortcuts
  Section un.SectionShortcutsStartMenu "un.Shortcuts Start Menu"
    ; Use NsisMultiUser_BB_Addon_SetShellVarContextFunction to use the right folders (All Users/Current User)
    Call un.NsisMultiUser_BB_Addon_SetShellVarContextFunction
    ; Delete normal, Start menu shortcuts
    RMDir /r "$SMPROGRAMS\${prodname}\"
  SectionEnd

  ; BleachBit Desktop Shortcut
  Section un.SectionShortcutsDesktop "un.Shortcut Desktop"
    ; Use NsisMultiUser_BB_Addon_SetShellVarContextFunction to use the right folders (All Users/Current User)
    Call un.NsisMultiUser_BB_Addon_SetShellVarContextFunction
    ; Delete Desktop shortcut
    Delete "$DESKTOP\BleachBit.lnk"
  SectionEnd

  ; BleachBit Quick Launch Shortcut
  Section un.SectionShortcutsQuickLaunch "un.Shortcut Quick Launch"
    ; Use NsisMultiUser_BB_Addon_SetShellVarContextFunction to use the right folders (All Users/Current User)
    Call un.NsisMultiUser_BB_Addon_SetShellVarContextFunction
    ; Delete Quick launch shortcut
    Delete "$QUICKLAUNCH\BleachBit.lnk"
  SectionEnd

  ; BleachBit Autostart Shortcut
  Section un.SectionShortcutsAutostart "un.Shortcut Autostart"
    ; Use NsisMultiUser_BB_Addon_SetShellVarContextFunction to use the right folders (All Users/Current User)
    Call un.NsisMultiUser_BB_Addon_SetShellVarContextFunction
    ; Delete Autostart shortcut
    Delete "$SMSTARTUP\BleachBit.lnk"
  SectionEnd
SectionGroupEnd

; BleachBit Translations
SectionGroup un.SectionGroupTranslations "un.Group Translations"
  !include bleachbit_language_code_uninstallsection_translations.nsi
SectionGroupEnd

; Section for making Shred Integration Optional
!ifndef NoSectionShred
  Section un.ShredForExplorer "un.Shred for Explorer"
    ; Remove file association (Shredder)
    DeleteRegKey HKCR "AllFileSystemObjects\shell\shred.bleachbit"
  SectionEnd
!endif


;--------------------------------
;Descriptions for the Uninstaller Components

; USE A LANGUAGE STRING IF YOU WANT YOUR DESCRIPTIONS TO BE LANGUAGE SPECIFIC

; Assign descriptions to sections:
; Variable/Constant must be declared by Uninstaller Sections! Place MUI_UNFUNCTION_DESCRIPTION after it!
!insertmacro MUI_UNFUNCTION_DESCRIPTION_BEGIN
  !insertmacro MUI_DESCRIPTION_TEXT "${un.Core}" $(BLEACHBIT_COMPONENT_CORE_DESCRIPTION)
  !insertmacro MUI_DESCRIPTION_TEXT "${un.Group Cleaners}" $(BLEACHBIT_COMPONENTGROUP_CLEANERS_DESCRIPTION)
  !insertmacro MUI_DESCRIPTION_TEXT "${un.Cleaners Stable}" "Stable"
  !ifdef BetaTester
    !insertmacro MUI_DESCRIPTION_TEXT "${un.Cleaners Beta}" "Beta"
    !ifdef AlphaTester
      !insertmacro MUI_DESCRIPTION_TEXT "${un.Cleaners Alpha}" "Alpha"
    !endif
  !endif
  !insertmacro MUI_DESCRIPTION_TEXT "${un.Installer}" $(BLEACHBIT_COMPONENT_INSTALLER_DESCRIPTION)
  !insertmacro MUI_DESCRIPTION_TEXT "${un.Group Shortcuts}" $(BLEACHBIT_COMPONENTGROUP_SHORTCUTS_DESCRIPTION)
  !insertmacro MUI_DESCRIPTION_TEXT "${un.Shortcuts Start Menu}" $(BLEACHBIT_COMPONENT_SHORTCUTS_STARTMENU_DESCRIPTION)
  !insertmacro MUI_DESCRIPTION_TEXT "${un.Shortcut Desktop}" $(BLEACHBIT_COMPONENT_SHORTCUTS_DESKTOP_DESCRIPTION)
  !insertmacro MUI_DESCRIPTION_TEXT "${un.Shortcut Quick Launch}" $(BLEACHBIT_COMPONENT_SHORTCUTS_QUICKLAUNCH_DESCRIPTION)
  !insertmacro MUI_DESCRIPTION_TEXT "${un.Shortcut Autostart}" $(BLEACHBIT_COMPONENT_SHORTCUTS_AUTOSTART_DESCRIPTION)
  !insertmacro MUI_DESCRIPTION_TEXT "${un.Group Translations}" $(BLEACHBIT_COMPONENTGROUP_TRANSLATIONS_DESCRIPTION)
  !insertmacro BB_Language_UnInstaller_MUI_Description_Text_Translations
  !ifndef Noun.SectionShred
    !insertmacro MUI_DESCRIPTION_TEXT "${un.Shred for Explorer}" $(BLEACHBIT_COMPONENT_SHREDFOREXPLORER_DESCRIPTION)
  !endif
!insertmacro MUI_UNFUNCTION_DESCRIPTION_END


;--------------------------------
;Uninstaller Functions

Function un.onInit
  ; Start un.NsisMultiUser_LVC_Addon_un.onInit-Functionality:
  Call un.NsisMultiUser_LVC_Addon_un.onInit

  !insertmacro MUI_UNGETLANGUAGE

  ; Reads components status from registry
  !insertmacro SectionList "NsisMultiUser_BB_Addon_AddRemove_InitSection"

  # Calculate size of data dirs:
  var /GLOBAL DirSizeCore
  ; ${GetSize} $INSTDIR "/S=0K" $0 $1 $2
  IntFmt $DirSizeCore "0x%08X" "10300" ; hard-coded for now because of installer.exe, cleaners dir, etc.

  var /GLOBAL DirSizeGroupCleaners
  ${GetSize} $INSTDIR\share\cleaners "/S=0K" $0 $1 $2
  IntFmt $DirSizeGroupCleaners "0x%08X" $0

  var /GLOBAL DirSizeInstaller
  ; ${GetSize} $INSTDIR "/S=0K" $0 $1 $2
  IntFmt $DirSizeInstaller "0x%08X" "9500" ; hard-coded for now because it is a single file

  var /GLOBAL DirSizeGroupTranslations
  ${GetSize} $INSTDIR\share\locale "/S=0K" $0 $1 $2
  IntFmt $DirSizeGroupTranslations "0x%08X" $0

  # Add size of data dirs to appropriate section:
  SectionSetSize "${un.Core}" $DirSizeCore
  SectionSetSize "${un.Group Cleaners}" $DirSizeGroupCleaners
  SectionSetSize "${un.Installer}" $DirSizeInstaller
  SectionSetSize "${un.Group Translations}" $DirSizeGroupTranslations
FunctionEnd

; And now starts the GUI UnInstaller...

Function un.MULTIUSER_UnPAGE_INSTALLMODE_Pre
  ; It figured out that in some cases we get a wrong "$INSTDIR" (via command line). Seems to be a bug in
  ; NsisMultiUser we can't find for now. So to go sure, we set some values before we start again with
  ; NsisMultiUser.
  Call un.NsisMultiUser_LVC_Addon_Set_NsisMultiUser
FunctionEnd

Function un.MULTIUSER_UnPAGE_INSTALLMODE_Leave
  ${if} $MultiUser.InstallMode == "AllUsers" ; setting defaults
    SetShellVarContext all
    !define /redef UMUI_PARAMS_REGISTRY_ROOT HKLM
  ${else}
    SetShellVarContext current
    !define /redef UMUI_PARAMS_REGISTRY_ROOT HKCU
  ${endif}

  ; SectionSetText:
  !insertmacro BB_Language_UnInstaller_SectionSetText
FunctionEnd

Section -un.FinishComponents
  ; Writes component status to registry if it is not a complete uninstall
  !insertmacro SectionList "un.NsisMultiUser_BB_Addon_AddRemove_un.FinishSection"
SectionEnd

; Keep this section last. It must be last because that is when the
; actual size is known.
; This is a hidden section.
Section "-un.Write Install Size"
  !insertmacro MULTIUSER_RegistryAddInstallSizeInfo
SectionEnd

Section -un.Post
  ; Update the "InstallDate" (also after component remove):
  ; But only if "InstallDate" still exist (no complete de-install)!
  ${if} $MultiUser.InstallMode == "AllUsers" ; setting defaults
    ReadRegStr $R1 SHCTX "${MULTIUSER_INSTALLMODE_UNINSTALL_REGISTRY_KEY_PATH}" "InstallDate"
    IfErrors +2 +1
    WriteRegStr SHCTX "${MULTIUSER_INSTALLMODE_UNINSTALL_REGISTRY_KEY_PATH}" "InstallDate" "${InstallDate}"
  ${else}
    ReadRegStr $R1 SHCTX "${MULTIUSER_INSTALLMODE_UNINSTALL_REGISTRY_KEY_PATH}$0" "InstallDate"
    IfErrors +2 +1
    WriteRegStr SHCTX "${MULTIUSER_INSTALLMODE_UNINSTALL_REGISTRY_KEY_PATH}$0" "InstallDate" "${InstallDate}"
  ${endif}

  ; Macro/Function "NsisMultiUser_LVC_Addon_SectionPost"
  ; Save the Language Selection Dialog Setting
  ; We need also "MUI_LANGDLL_ALWAYSSHOW", or the user can never ever change his language!
  Call un.NsisMultiUser_LVC_Addon_SectionPost
SectionEnd

