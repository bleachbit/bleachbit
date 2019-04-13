/*

NSIS Ultra-Modern User Interface version 2.0 beta 5
Copyright 2005-2019 SuperPat

Based on:
    NSIS Modern User Interface version 1.81 (Git version: 6b4148e215433dddd1a954291364ef52e44d12e5)
    Copyright 2002-2019 Joost Verburg

*/

!ifndef MUI_INCLUDED
!verbose push 3
!define MUI_INCLUDED
!define UMUI_SYSVERSION "2.0 beta 5"
!define MUI_SYSVERSION "1.81"
!verbose pop
!echo "NSIS Ultra-Modern User Interface version 2.0 beta 5 - Copyright 2005-2019 SuperPat"
!echo "  (Bugfixes and some additions: 2015-2016 - Bodenseematze)"
!echo "Based on: NSIS Modern User Interface version 1.81 - Copyright 2002-2019 Joost Verburg"

;--------------------------------
!verbose push 3
!define /IfNDef MUI_VERBOSE 3
!verbose ${MUI_VERBOSE}

;--------------------------------
;HEADER FILES, DECLARATIONS

!include WinMessages.nsh
!include LogicLib.nsh

!define UMUI_HIDEFIRSTBACKBUTTON    ;don't show the "Back" button on the first shown page,
                                    ;even if it is not the first page defined
Var MUI_TEMP1
Var MUI_TEMP2

Var UMUI_INSTALLFLAG                ; Contains a OR of all the flags define here:

;--------------------------------
;INSTALL FLAGS

;definition of all the install status
!define UMUI_DEFAULT_STATE   0      ; Default state: Any flag set
!define UMUI_CANCELLED       1      ; set by (un).onUserAbort function
!define UMUI_MINIMAL         2      ; set by INSTALLTYPE page
!define UMUI_STANDARD        4      ; set by INSTALLTYPE page
!define UMUI_COMPLETE        8      ; set by INSTALLTYPE page
!define UMUI_CUSTOM          16     ; set by INSTALLTYPE page
!define UMUI_MODIFY          32     ; set by MAINTENANCE page
!define UMUI_REPAIR          64     ; set by MAINTENANCE page
!define UMUI_UPDATE          128    ; set by UPDATE page
!define UMUI_REMOVE          256    ; set by MAINTENANCE and UPDATE pages
!define UMUI_CONTINUE_SETUP  512    ; set by MAINTENANCE and UPDATE pages
!define UMUI_LANGISSET       1024   ; set by UMUI_MULTILANG_GET macro and used by MULTILANGUAGE page
!define UMUI_SAMEVERSION     2048   ; set by (un).onGuiInit function and used by MANTENANCE and UPDATE pages
!define UMUI_DIFFVERSION     4096   ; set by (un).onGuiInit function and used by MANTENANCE and UPDATE pages
!define UMUI_HIDEBACKBUTTON  8192   ; set by (un).onGuiInit function
!define UMUI_ABORTFIRSTTIME  16384  ; set by (un).onGuiInit function and used by MANTENANCE page
!define UMUI_COMPONENTSSET   32768  ; set by COMPONENTS page

;--------------------------------
;INSERT CODE

!macro MUI_INSERT

  !ifndef MUI_INSERT
    !define MUI_INSERT

    !ifdef MUI_PRODUCT | MUI_VERSION
      !warning "The MUI_PRODUCT and MUI_VERSION defines have been removed. Use a normal Name command now."
    !endif

    !insertmacro MUI_INTERFACE

    !insertmacro MUI_FUNCTION_GUIINIT
    !insertmacro MUI_FUNCTION_ABORTWARNING

    !ifdef MUI_IOCONVERT_USED
      !insertmacro INSTALLOPTIONS_FUNCTION_WRITE_CONVERT
    !endif

    !ifdef MUI_UNINSTALLER
      !insertmacro MUI_UNFUNCTION_GUIINIT
      !insertmacro MUI_FUNCTION_UNABORTWARNING

      !ifdef MUI_UNIOCONVERT_USED
        !insertmacro INSTALLOPTIONS_UNFUNCTION_WRITE_CONVERT
      !endif
    !endif

  !endif

!macroend

;--------------------------------
;GENERAL

!macro MUI_DEFAULT SYMBOL CONTENT

  !define /IfNDef "${SYMBOL}" "${CONTENT}"

!macroend

!macro MUI_DEFAULT_IOCONVERT SYMBOL CONTENT

  !ifndef "${SYMBOL}"
    !define "${SYMBOL}" "${CONTENT}"
    !define /IfNDef "${SYMBOL}_DEFAULTSET"
    !define /IfNDef "MUI_${MUI_PAGE_UNINSTALLER_PREFIX}IOCONVERT_USED"
  !else
    !insertmacro MUI_UNSET "${SYMBOL}_DEFAULTSET"
  !endif

!macroend

!macro MUI_SET SYMBOL

  !define /IfNDef "${SYMBOL}"

!macroend

!macro MUI_UNSET SYMBOL

  !ifdef "${SYMBOL}"
    !undef "${SYMBOL}"
  !endif

!macroend

;--------------------------------
;INTERFACE - COMPILE TIME SETTINGS

!macro MUI_INTERFACE

  !ifndef MUI_INTERFACE
    !define MUI_INTERFACE

    !ifdef MUI_INSERT_NSISCONF
      !insertmacro MUI_NSISCONF
    !endif

    !ifdef UMUI_USE_BG
      !define /IfNDef UMUI_BGSKIN ${UMUI_USE_BG}
      !warning "Deprecated: The UMUI_USE_BG define was replaced by UMUI_BGSKIN."
    !endif

    !ifdef MUI_LANGDLL_REGISTRY_ROOT | MUI_LANGDLL_REGISTRY_KEY | MUI_LANGDLL_REGISTRY_VALUENAME
      !warning "Deprecated: The MUI_LANGDLL_REGISTRY_ROOT, MUI_LANGDLL_REGISTRY_KEY and MUI_LANGDLL_REGISTRY_VALUENAME defines were replaced by UMUI_LANGUAGE_REGISTRY_VALUENAME, UMUI_LANGUAGE_REGISTRY_ROOT, UMUI_LANGUAGE_REGISTRY_KEY or you can use also the UMUI_PARAMS_REGISTRY_ROOT & UMUI_PARAMS_REGISTRY_KEY globals parameters."
    !endif

    !ifdef MUI_LANGDLL_ALWAYSSHOW
      !warning "Deprecated: The MUI_LANGDLL_ALWAYSSHOW define was replaced by UMUI_LANGUAGE_ALWAYSSHOW."
      !define /IfNDef UMUI_LANGUAGE_ALWAYSSHOW "${MUI_LANGDLL_ALWAYSSHOW}"
    !endif

    !ifdef UMUI_BGSKIN
      !include "${NSISDIR}\Contrib\UltraModernUI\BGSkins\${UMUI_BGSKIN}.nsh"
    !endif

    !ifdef UMUI_LANGUAGE_REGISTRY_VALUENAME
      !ifndef UMUI_LANGUAGE_REGISTRY_ROOT
        !ifdef UMUI_PARAMS_REGISTRY_ROOT
          !define UMUI_LANGUAGE_REGISTRY_ROOT "${UMUI_PARAMS_REGISTRY_ROOT}"
        !else ifdef MUI_LANGDLL_REGISTRY_ROOT
          !define UMUI_LANGUAGE_REGISTRY_ROOT "${MUI_LANGDLL_REGISTRY_ROOT}"
        !else
          !error "For UMUI_LANGUAGE_REGISTRY_VALUENAME, the UMUI_LANGUAGE_REGISTRY_ROOT & UMUI_LANGUAGE_REGISTRY_KEY parameters or else the UMUI_PARAMS_REGISTRY_ROOT & UMUI_PARAMS_REGISTRY_KEY global parameters must be defined."
        !endif
      !endif
      !ifndef UMUI_LANGUAGE_REGISTRY_KEY
        !ifdef UMUI_PARAMS_REGISTRY_KEY
          !define UMUI_LANGUAGE_REGISTRY_KEY "${UMUI_PARAMS_REGISTRY_KEY}"
        !else ifdef MUI_LANGDLL_REGISTRY_KEY
          !define UMUI_LANGUAGE_REGISTRY_KEY "${MUI_LANGDLL_REGISTRY_KEY}"
        !else
          !error "For UMUI_LANGUAGE_REGISTRY_VALUENAME, the UMUI_LANGUAGE_REGISTRY_ROOT & UMUI_LANGUAGE_REGISTRY_KEY parameters or else the UMUI_PARAMS_REGISTRY_ROOT & UMUI_PARAMS_REGISTRY_KEY global parameters must be defined."
        !endif
      !endif
    !else ifdef MUI_LANGDLL_REGISTRY_VALUENAME
      !define UMUI_LANGUAGE_REGISTRY_VALUENAME "${MUI_LANGDLL_REGISTRY_VALUENAME}"
    !endif

    !ifndef MUI_TEXTCOLOR
      !ifdef UMUI_TEXT_COLOR
        !warning "Deprecated: The UMUI_TEXT_COLOR define was renamed in MUI_TEXTCOLOR since Ultra-Modern UI 2.0 beta 5"
        !define MUI_TEXTCOLOR "${UMUI_TEXT_COLOR}"
      !else ifdef MUI_TEXT_COLOR
        !warning "Deprecated: The MUI_TEXT_COLOR define was renamed in MUI_TEXTCOLOR since Ultra-Modern UI 1.00 beta 2"
        !define MUI_TEXTCOLOR "${MUI_TEXT_COLOR}"
      !endif
    !endif

    !ifdef UMUI_UI_COMPONENTSPAGE_SMALLDESC | UMUI_UI_COMPONENTSPAGE_NODESC
      !warning "Deprecated: The UMUI_UI_COMPONENTSPAGE_SMALLDESC and UMUI_UI_COMPONENTSPAGE_NODESC define were renamed in MUI_UI_COMPONENTSPAGE_SMALLDESC and MUI_UI_COMPONENTSPAGE_NODESC since Ultra-Modern UI 1.00 beta 2"
      !ifdef UMUI_UI_COMPONENTSPAGE_SMALLDESC
        !define /IfNDef MUI_UI_COMPONENTSPAGE_SMALLDESC "${UMUI_UI_COMPONENTSPAGE_SMALLDESC}"
      !endif
      !ifdef UMUI_UI_COMPONENTSPAGE_NODESC
        !define /IfNDef MUI_UI_COMPONENTSPAGE_NODESC "${UMUI_UI_COMPONENTSPAGE_NODESC}"
      !endif
    !endif


!ifndef USE_MUIEx
;-----------------

    !ifdef UMUI_CUSTOM_SKIN
      !define /IfNDef UMUI_SKIN "${UMUI_CUSTOM_SKIN}"
      !warning "Deprecated: The UMUI_CUSTOM_SKIN define is no more necessary and you can simply use the UMUI_SKIN define with your custom skin."
    !endif

    !addincludedir "${NSISDIR}\Contrib\UltraModernUI\Skins\"

    !ifdef UMUI_SKIN
      !include "${UMUI_SKIN}.nsh"
    !endif

    !ifdef MUI_UI
      !warning "The MUI_UI define have been renamed by UMUI_UI in the UMUI mode in order to assure the compatibility with the former Modern UI scripts. Define Ignored"
    !endif

    !ifdef UMUI_HEADERIMAGE_BMP | UMUI_UNHEADERIMAGE_BMP
      !warning "Deprecated: The UMUI_HEADERIMAGE_BMP and UMUI_UNHEADERIMAGE_BMP defines were renamed by UMUI_HEADERBGIMAGE_BMP and UMUI_UNHEADERBGIMAGE_BMP since Ultra-Modern UI 1.00 beta 2."
      !ifdef UMUI_HEADERIMAGE_BMP
        !define /IfNDef UMUI_HEADERBGIMAGE_BMP "${UMUI_HEADERIMAGE_BMP}"
      !endif
      !ifdef UMUI_UNHEADERIMAGE_BMP
        !define /IfNDef UMUI_UNHEADERBGIMAGE_BMP "${UMUI_UNHEADERIMAGE_BMP}"
      !endif
    !endif

    !ifdef MUI_UI_HEADERIMAGE | MUI_UI_HEADERIMAGE_RIGHT | MUI_HEADERIMAGE | MUI_HEADERIMAGE_RIGHT
      !warning "The MUI_UI_HEADERIMAGE, MUI_UI_HEADERIMAGE_RIGHT, MUI_HEADERIMAGE and MUI_HEADERIMAGE_RIGHT defines are not currently supported in the UMUI mode."
    !endif

    !ifdef UMUI_UNIQUEBGIMAGE
      !define /IfNDef UMUI_PAGEBGIMAGE
    !endif
    !ifdef UMUI_UNUNIQUEBGIMAGE
      !define /IfNDef UMUI_UNPAGEBGIMAGE
    !endif

    !ifndef UMUI_ULTRAMODERN_SMALL
      !define /IfNDef UMUI_UI "${NSISDIR}\Contrib\UIs\UltraModernUI\UltraModern.exe"
      !define /IfNDef UMUI_UI_SB "${NSISDIR}\Contrib\UIs\UltraModernUI\UltraModern_sb.exe"
      !define /IfNDef UMUI_UI_NOLEFTIMAGE "${NSISDIR}\Contrib\UIs\UltraModernUI\UltraModern_noleftimage.exe"
    !else
      !define /IfNDef UMUI_UI_SMALL "${NSISDIR}\Contrib\UIs\UltraModernUI\UltraModern_small.exe"
      !define /IfNDef UMUI_UI_SB "${NSISDIR}\Contrib\UIs\UltraModernUI\UltraModern_small_sb.exe"
      !define /IfNDef UMUI_USE_SMALLPAGE
      !ifndef UMUI_UNIQUEBGIMAGE
        !define /IfNDef UMUI_NO_WFA_BGTRANSPARENT
      !endif
    !endif

    !ifndef UMUI_USE_SMALLPAGE
      !define /IfNDef MUI_UI_COMPONENTSPAGE_SMALLDESC "${NSISDIR}\Contrib\UIs\UltraModernUI\UltraModern_smalldesc.exe"
      !define /IfNDef MUI_UI_COMPONENTSPAGE_NODESC "${NSISDIR}\Contrib\UIs\UltraModernUI\UltraModern_nodesc.exe"
      !define /IfNDef UMUI_UI_COMPONENTSPAGE_BIGDESC "${NSISDIR}\Contrib\UIs\UltraModernUI\UltraModern_bigdesc.exe"
    !else
      !define /IfNDef MUI_UI_COMPONENTSPAGE_SMALLDESC "${NSISDIR}\Contrib\UIs\modern_smalldesc.exe"
      !define /IfNDef MUI_UI_COMPONENTSPAGE_NODESC "${NSISDIR}\Contrib\UIs\modern_nodesc.exe"
      !define /IfNDef UMUI_UI_COMPONENTSPAGE_BIGDESC "${NSISDIR}\Contrib\UIs\UltraModernUI\modern_bigdesc.exe"
    !endif

    !define /IfNDef MUI_ICON "${NSISDIR}\Contrib\Graphics\UltraModernUI\Icon.ico"
    !define /IfNDef MUI_UNICON "${NSISDIR}\Contrib\Graphics\UltraModernUI\UnIcon.ico"

    !define /IfNDef MUI_BGCOLOR 4C72B2
    !define /IfNDef MUI_TEXTCOLOR FFFFFF
    !define /IfNDef UMUI_TEXT_LIGHTCOLOR FFFF00
    !define /IfNDef UMUI_HEADERTEXT_COLOR "${MUI_TEXTCOLOR}"

    !define /IfNDef MUI_LICENSEPAGE_BGCOLOR "/windows"
    !define /IfNDef MUI_INSTFILESPAGE_COLORS "${MUI_TEXTCOLOR} ${MUI_BGCOLOR}"
    !define /IfNDef MUI_INSTFILESPAGE_PROGRESSBAR "smooth"

    !define /IfNDef UMUI_LEFTIMAGE_BMP "${NSISDIR}\Contrib\UltraModernUI\Skins\blue\Left.bmp"
    !define /IfNDef UMUI_HEADERBGIMAGE_BMP "${NSISDIR}\Contrib\UltraModernUI\Skins\blue\Header.bmp"
    !define /IfNDef UMUI_BOTTOMIMAGE_BMP "${NSISDIR}\Contrib\UltraModernUI\Skins\blue\Bottom.bmp"
    !define /IfNDef UMUI_BUTTONIMAGE_BMP "${NSISDIR}\Contrib\UltraModernUI\Skins\blue\Button.bmp"
    !define /IfNDef UMUI_SCROLLBARIMAGE_BMP "${NSISDIR}\Contrib\UltraModernUI\Skins\blue\ScrollBar.bmp"
    !define /IfNDef UMUI_PAGEBGIMAGE_BMP "${NSISDIR}\Contrib\UltraModernUI\Skins\blue\PageBG.bmp"

    !define /IfNDef UMUI_UNLEFTIMAGE_BMP "${UMUI_LEFTIMAGE_BMP}"
    !define /IfNDef UMUI_UNHEADERBGIMAGE_BMP "${UMUI_HEADERBGIMAGE_BMP}"
    !define /IfNDef UMUI_UNBOTTOMIMAGE_BMP "${UMUI_BOTTOMIMAGE_BMP}"
    !define /IfNDef UMUI_UNBUTTONIMAGE_BMP "${UMUI_BUTTONIMAGE_BMP}"
    !define /IfNDef UMUI_UNSCROLLBARIMAGE_BMP "${UMUI_SCROLLBARIMAGE_BMP}"
    !define /IfNDef UMUI_UNPAGEBGIMAGE_BMP "${UMUI_PAGEBGIMAGE_BMP}"

    !define /IfNDef UMUI_BRANDINGTEXTFRONTCOLOR 8b8ca4
    !define /IfNDef UMUI_BRANDINGTEXTBACKCOLOR eeeef3

    !define /IfNDef MUI_WELCOMEFINISHPAGE_BITMAP "${NSISDIR}\Contrib\UltraModernUI\Skins\blue\Wizard.bmp"
    !define /IfNDef MUI_UNWELCOMEFINISHPAGE_BITMAP "${MUI_WELCOMEFINISHPAGE_BITMAP}"

    !define /IfNDef UMUI_XPSTYLE Off

    !ifndef UMUI_ULTRAMODERN_SMALL

      ChangeUI all "${UMUI_UI}"

      !ifdef UMUI_NOLEFTIMAGE
        !insertmacro MUI_UNSET UMUI_LEFTIMAGE_BMP
        !insertmacro MUI_UNSET UMUI_UNLEFTIMAGE_BMP
          ChangeUI IDD_INST "${UMUI_UI_NOLEFTIMAGE}"
      !endif

    !else

      !define /IfNDef UMUI_USE_SMALL_PAGES
      ChangeUI all "${UMUI_UI_SMALL}"

    !endif

    !ifdef UMUI_NOHEADERBGIMAGE
      !insertmacro MUI_UNSET UMUI_HEADERBGIMAGE
    !else
      !define /IfNDef UMUI_HEADERBGIMAGE
    !endif

    !ifdef UMUI_HEADERBGIMAGE
      !define /IfNDef MUI_HEADER_TRANSPARENT_TEXT
    !endif

    !ifdef UMUI_NOBOTTOMIMAGE
      !insertmacro MUI_UNSET UMUI_BOTTOMIMAGE_BMP
      !insertmacro MUI_UNSET UMUI_UNBOTTOMIMAGE_BMP
    !endif

    !ifdef UMUI_NO_BUTTONIMAGE
      !insertmacro MUI_UNSET UMUI_BUTTONIMAGE_BMP
      !insertmacro MUI_UNSET UMUI_UNBUTTONIMAGE_BMP
    !endif

    !ifdef UMUI_NO_SCROLLBARIMAGE
      !insertmacro MUI_UNSET UMUI_SCROLLBARIMAGE_BMP
      !insertmacro MUI_UNSET UMUI_UNSCROLLBARIMAGE_BMP
    !endif

!else
;-------

    !ifdef UMUI_SKIN
      !warning "The UMUI_SKIN define is not used in Modern UIEx. Define ignored."
      !undef UMUI_SKIN
    !endif
    !insertmacro MUI_UNSET UMUI_PAGEBGIMAGE
    !insertmacro MUI_UNSET UMUI_UNPAGEBGIMAGE
    !insertmacro MUI_UNSET UMUI_UNIQUEBGIMAGE
    !insertmacro MUI_UNSET UMUI_UNUNIQUEBGIMAGE

    ; by default, UMUI_WELCOMEFINISHABORTPAGE_USE_IMAGE is set
    !ifndef UMUI_WELCOMEFINISHABORTPAGE_NOTUSE_IMAGE
      !define /IfNDef UMUI_WELCOMEFINISHABORTPAGE_USE_IMAGE
    !else
      !insertmacro MUI_UNSET UMUI_WELCOMEFINISHABORTPAGE_USE_IMAGE
    !endif

    !define /IfNDef MUI_UI "${NSISDIR}\Contrib\UIs\modern.exe"
    !define /IfNDef UMUI_UI_SB "${NSISDIR}\Contrib\UIs\UltraModernUI\modern_sb.exe"
    !define /IfNDef MUI_UI_HEADERIMAGE "${NSISDIR}\Contrib\UIs\modern_headerbmp.exe"
    !define /IfNDef MUI_UI_HEADERIMAGE_RIGHT "${NSISDIR}\Contrib\UIs\modern_headerbmpr.exe"
    !define /IfNDef UMUI_UI_HEADERBGIMAGE "${NSISDIR}\Contrib\UIs\UltraModernUI\modern_headerbgimage.exe"
    !define /IfNDef MUI_UI_COMPONENTSPAGE_SMALLDESC "${NSISDIR}\Contrib\UIs\modern_smalldesc.exe"
    !define /IfNDef MUI_UI_COMPONENTSPAGE_NODESC "${NSISDIR}\Contrib\UIs\modern_nodesc.exe"
    !define /IfNDef UMUI_UI_COMPONENTSPAGE_BIGDESC "${NSISDIR}\Contrib\UIs\UltraModernUI\modern_bigdesc.exe"

    !define /IfNDef MUI_ICON "${NSISDIR}\Contrib\Graphics\Icons\modern-install.ico"
    !define /IfNDef MUI_UNICON "${NSISDIR}\Contrib\Graphics\Icons\modern-uninstall.ico"

    !define /IfNDef MUI_LICENSEPAGE_BGCOLOR "/windows"
    !define /IfNDef MUI_INSTFILESPAGE_COLORS "/windows"
    !define /IfNDef MUI_INSTFILESPAGE_PROGRESSBAR "smooth"

    !define /IfNDef MUI_BGCOLOR "FFFFFF"
    !define /IfNDef MUI_TEXTCOLOR "000000"
    !define /IfNDef UMUI_TEXT_LIGHTCOLOR "000000"
    !define /IfNDef UMUI_HEADERTEXT_COLOR "${MUI_TEXTCOLOR}"

    !define /IfNDef UMUI_HEADERBGIMAGE_BMP "${NSISDIR}\Contrib\Graphics\UltraModernUI\HeaderBG.bmp"
    !define /IfNDef UMUI_UNHEADERBGIMAGE_BMP "${UMUI_HEADERBGIMAGE_BMP}"
    !ifdef UMUI_BUTTONIMAGE_BMP
      !define /IfNDef UMUI_UNBUTTONIMAGE_BMP "${UMUI_BUTTONIMAGE_BMP}"
    !endif
    !ifdef UMUI_SCROLLBARIMAGE_BMP
      !define /IfNDef UMUI_UNSCROLLBARIMAGE_BMP "${UMUI_SCROLLBARIMAGE_BMP}"
    !endif

    !define /IfNDef MUI_WELCOMEFINISHPAGE_BITMAP "${NSISDIR}\Contrib\Graphics\Wizard\win.bmp"
    !define /IfNDef MUI_UNWELCOMEFINISHPAGE_BITMAP "${NSISDIR}\Contrib\Graphics\Wizard\win.bmp"

    !ifdef UMUI_BUTTONIMAGE_BMP | UMUI_UNBUTTONIMAGE_BMP
      !define /IfNDef UMUI_XPSTYLE Off
    !else
      !define /IfNDef UMUI_XPSTYLE On
    !endif

    !if "${MUI_WELCOMEFINISHPAGE_BITMAP}" == ""
      !error "Invalid MUI_WELCOMEFINISHPAGE_BITMAP"
    !endif
    !if "${MUI_UNWELCOMEFINISHPAGE_BITMAP}" == ""
      !error "Invalid MUI_UNWELCOMEFINISHPAGE_BITMAP"
    !endif

    !define /IfNDef UMUI_USE_SMALL_PAGES

    !ifdef UMUI_HEADERBGIMAGE

      !define /IfNDef MUI_HEADER_TRANSPARENT_TEXT
      !insertmacro MUI_UNSET MUI_HEADERIMAGE
      !insertmacro MUI_UNSET MUI_HEADERIMAGE_RIGHT

    !else ifdef MUI_HEADERIMAGE

      !define /IfNDef MUI_HEADERIMAGE_BITMAP "${NSISDIR}\Contrib\Graphics\Header\nsis.bmp"

      !ifndef MUI_HEADERIMAGE_UNBITMAP
        !define MUI_HEADERIMAGE_UNBITMAP "${MUI_HEADERIMAGE_BITMAP}"
        !ifdef MUI_HEADERIMAGE_BITMAP_NOSTRETCH
          !define /IfNDef MUI_HEADERIMAGE_UNBITMAP_NOSTRETCH
        !endif
      !endif

      !if "${MUI_HEADERIMAGE_BITMAP}" == ""
        !error "Invalid MUI_HEADERIMAGE_BITMAP"
      !endif
      !if "${MUI_HEADERIMAGE_UNBITMAP}" == ""
        !error "Invalid MUI_HEADERIMAGE_UNBITMAP"
      !endif

      !ifdef MUI_HEADERIMAGE_BITMAP_RTL
        !ifndef MUI_HEADERIMAGE_UNBITMAP_RTL
          !define MUI_HEADERIMAGE_UNBITMAP_RTL "${MUI_HEADERIMAGE_BITMAP_RTL}"
          !ifdef MUI_HEADERIMAGE_BITMAP_RTL_NOSTRETCH
            !define /IfNDef MUI_HEADERIMAGE_UNBITMAP_RTL_NOSTRETCH
          !endif
        !endif
      !endif

      !if "${MUI_HEADERIMAGE_BITMAP_RTL}" == ""
        !error "Invalid MUI_HEADERIMAGE_BITMAP_RTL"
      !endif
      !if "${MUI_HEADERIMAGE_UNBITMAP_RTL}" == ""
        !error "Invalid MUI_HEADERIMAGE_UNBITMAP_RTL"
      !endif
    !endif

    ChangeUI all "${MUI_UI}"

    !ifdef UMUI_HEADERBGIMAGE
      ChangeUI IDD_INST "${UMUI_UI_HEADERBGIMAGE}"
    !else ifdef MUI_HEADERIMAGE
      !ifndef MUI_HEADERIMAGE_RIGHT
        ChangeUI IDD_INST "${MUI_UI_HEADERIMAGE}"
      !else
        ChangeUI IDD_INST "${MUI_UI_HEADERIMAGE_RIGHT}"
      !endif
    !endif

!endif
;-------

    !ifdef MUI_COMPONENTSPAGE_SMALLDESC
      ChangeUI IDD_SELCOM "${MUI_UI_COMPONENTSPAGE_SMALLDESC}"
    !else ifdef MUI_COMPONENTSPAGE_NODESC
      ChangeUI IDD_SELCOM "${MUI_UI_COMPONENTSPAGE_NODESC}"
    !else ifdef UMUI_COMPONENTSPAGE_BIGDESC
      ChangeUI IDD_SELCOM "${UMUI_UI_COMPONENTSPAGE_BIGDESC}"
    !endif

    ; Workaround for unstyled detail button
    !ifdef UMUI_BUTTONIMAGE_BMP | UMUI_UNBUTTONIMAGE_BMP
      !if ! "${UMUI_XPSTYLE}" == "On"
        ChangeUI IDD_INSTFILES "${UMUI_UI_SB}"
      !endif
    !endif

    !ifdef UMUI_WELCOMEFINISHABORTPAGE_USE_IMAGE
      !define /IfNDef UMUI_WELCOMEFINISHABORTPAGE_INI "${NSISDIR}\Contrib\UltraModernUI\Ini\WelcomeFinishAbortImage.ini"
      !define /IfNDef UMUI_UNWELCOMEFINISHABORTPAGE_INI "${NSISDIR}\Contrib\UltraModernUI\Ini\WelcomeFinishAbortImage.ini"
      !define /IfNDef UMUI_ALTERNATEWELCOMEFINISHABORTPAGE_INI "${NSISDIR}\Contrib\UltraModernUI\Ini\AlternateWelcomeFinishAbortImage.ini"
      !define /IfNDef UMUI_UNALTERNATEWELCOMEFINISHABORTPAGE_INI "${NSISDIR}\Contrib\UltraModernUI\Ini\AlternateWelcomeFinishAbortImage.ini"
    !else
      !define /IfNDef UMUI_WELCOMEFINISHABORTPAGE_INI "${NSISDIR}\Contrib\UltraModernUI\Ini\WelcomeFinishAbort.ini"
      !define /IfNDef UMUI_UNWELCOMEFINISHABORTPAGE_INI "${NSISDIR}\Contrib\UltraModernUI\Ini\WelcomeFinishAbort.ini"
      !define /IfNDef UMUI_ALTERNATEWELCOMEFINISHABORTPAGE_INI "${NSISDIR}\Contrib\UltraModernUI\Ini\AlternateWelcomeFinishAbort.ini"
      !define /IfNDef UMUI_UNALTERNATEWELCOMEFINISHABORTPAGE_INI "${NSISDIR}\Contrib\UltraModernUI\Ini\AlternateWelcomeFinishAbort.ini"
    !endif
    !define /IfNDef UMUI_MAINTENANCEUPDATESETUPTYPEPAGE_INI "${NSISDIR}\Contrib\UltraModernUI\Ini\MaintenanceUpdateSetupType.ini"
    !define /IfNDef UMUI_CONFIRMPAGE_INI "${NSISDIR}\Contrib\UltraModernUI\Ini\Confirm.ini"
    !define /IfNDef UMUI_INFORMATIONPAGE_INI "${NSISDIR}\Contrib\UltraModernUI\Ini\Information.ini"
    !define /IfNDef UMUI_ADDITIONALTASKSPAGE_INI "${NSISDIR}\Contrib\UltraModernUI\Ini\AdditionalTasks.ini"
    !define /IfNDef UMUI_SERIALNUMBERPAGE_INI "${NSISDIR}\Contrib\UltraModernUI\Ini\SerialNumber.ini"
    !define /IfNDef UMUI_ALTERNATIVESTARTMENUPAGE_INI "${NSISDIR}\Contrib\UltraModernUI\Ini\AlternativeStartMenu.ini"

    !define /IfNDef MUI_COMPONENTSPAGE_CHECKBITMAP "${NSISDIR}\Contrib\Graphics\Checks\modern.bmp"

    !define /IfNDef UMUI_TEXT_INPUTCOLOR 000000
    !define /IfNDef UMUI_BGINPUTCOLOR FFFFFF

    !define /IfNDef UMUI_DISABLED_BUTTON_TEXT_COLOR 808080
    !define /IfNDef UMUI_SELECTED_BUTTON_TEXT_COLOR 000080
    !define /IfNDef UMUI_BUTTON_TEXT_COLOR 000000

    !define /IfNDef UMUI_UNDISABLED_BUTTON_TEXT_COLOR "${UMUI_DISABLED_BUTTON_TEXT_COLOR}"
    !define /IfNDef UMUI_UNSELECTED_BUTTON_TEXT_COLOR "${UMUI_SELECTED_BUTTON_TEXT_COLOR}"
    !define /IfNDef UMUI_UNBUTTON_TEXT_COLOR "${UMUI_BUTTON_TEXT_COLOR}"

    XPStyle ${UMUI_XPSTYLE}

    !ifdef UMUI_USE_ALTERNATE_PAGE | UMUI_USE_UNALTERNATE_PAGE
      !define /IfNDef UMUI_WELCOMEFINISHABORT_TITLE_FONTSIZE 8
    !else
      !define /IfNDef UMUI_WELCOMEFINISHABORT_TITLE_FONTSIZE 12
    !endif

    Icon "${MUI_ICON}"
    UninstallIcon "${MUI_UNICON}"

    CheckBitmap "${MUI_COMPONENTSPAGE_CHECKBITMAP}"
    LicenseBkColor "${MUI_LICENSEPAGE_BGCOLOR}"
    InstallColors ${MUI_INSTFILESPAGE_COLORS}
    InstProgressFlags ${MUI_INSTFILESPAGE_PROGRESSBAR}

    SubCaption 4 " "
    UninstallSubCaption 2 " "

    !ifdef UMUI_INSTALLDIR_REGISTRY_VALUENAME
      !ifndef UMUI_INSTALLDIR_REGISTRY_ROOT
        !ifdef UMUI_PARAMS_REGISTRY_ROOT
          !define UMUI_INSTALLDIR_REGISTRY_ROOT "${UMUI_PARAMS_REGISTRY_ROOT}"
        !else
          !error "For UMUI_INSTALLDIR_REGISTRY_VALUENAME, the UMUI_INSTALLDIR_REGISTRY_ROOT & UMUI_INSTALLDIR_REGISTRY_KEY parameters or else the UMUI_PARAMS_REGISTRY_ROOT & UMUI_PARAMS_REGISTRY_KEY global parameters must be defined."
        !endif
      !endif
      !ifndef UMUI_INSTALLDIR_REGISTRY_KEY
        !ifdef UMUI_PARAMS_REGISTRY_KEY
          !define UMUI_INSTALLDIR_REGISTRY_KEY "${UMUI_PARAMS_REGISTRY_KEY}"
        !else
          !error "For UMUI_INSTALLDIR_REGISTRY_VALUENAME, the UMUI_INSTALLDIR_REGISTRY_ROOT & UMUI_INSTALLDIR_REGISTRY_KEY parameters or else the UMUI_PARAMS_REGISTRY_ROOT & UMUI_PARAMS_REGISTRY_KEY global parameters must be defined."
        !endif
      !endif
      InstallDirRegKey ${UMUI_INSTALLDIR_REGISTRY_ROOT} "${UMUI_INSTALLDIR_REGISTRY_KEY}" "${UMUI_INSTALLDIR_REGISTRY_VALUENAME}"
    !endif

    !define /IfNDef MUI_ABORTWARNING_TEXT "$(MUI_TEXT_ABORTWARNING)"
    !define /IfNDef MUI_UNABORTWARNING_TEXT "$(MUI_UNTEXT_ABORTWARNING)"

  !endif

!macroend



;--------------------------------
;INTERFACE - RUN-TIME

; Set the background color of the static Pages
!macro UMUI_PAGEBG_INIT
!ifndef USE_MUIEx
;----------------
  FindWindow $MUI_TEMP1 "#32770" "" $HWNDPARENT
  SetCtlColors $MUI_TEMP1 "${MUI_BGCOLOR}" "${MUI_BGCOLOR}"
!endif
;-----
!macroend

; Set transparent the background of the static Pages
!macro UMUI_PAGEBGTRANSPARENT_INIT
!ifndef USE_MUIEx
;----------------
  FindWindow $MUI_TEMP1 "#32770" "" $HWNDPARENT
  !ifdef UMUI_${MUI_PAGE_UNINSTALLER_PREFIX}PAGEBGIMAGE
    SetCtlColors $MUI_TEMP1 "transparent" "transparent"
  !else
    SetCtlColors $MUI_TEMP1 "${MUI_BGCOLOR}" "${MUI_BGCOLOR}"
  !endif
!endif
;-----
!macroend

; Set the background color of the control in a static Pages
!macro UMUI_PAGECTL_INIT ID
!ifndef USE_MUIEx
;-----------------
  FindWindow $MUI_TEMP1 "#32770" "" $HWNDPARENT
  GetDlgItem $MUI_TEMP1 $MUI_TEMP1 ${ID}
  SetCtlColors $MUI_TEMP1 "${MUI_TEXTCOLOR}" "${MUI_BGCOLOR}"
!endif
;-----
!macroend

; Set transparent the background of the control in a static Pages
!macro UMUI_PAGECTLTRANSPARENT_INIT ID
!ifndef USE_MUIEx
;-----------------
  FindWindow $MUI_TEMP1 "#32770" "" $HWNDPARENT
  GetDlgItem $MUI_TEMP1 $MUI_TEMP1 ${ID}
  !ifdef UMUI_${MUI_PAGE_UNINSTALLER_PREFIX}PAGEBGIMAGE
    SetCtlColors $MUI_TEMP1 "${MUI_TEXTCOLOR}" "transparent"
  !else
    SetCtlColors $MUI_TEMP1 "${MUI_TEXTCOLOR}" "${MUI_BGCOLOR}"
  !endif
!endif
;-----
!macroend

; Set the background color and the light text color of the control in a static Pages
!macro UMUI_PAGECTLLIGHT_INIT ID
!ifndef USE_MUIEx
;-----------------
  FindWindow $MUI_TEMP1 "#32770" "" $HWNDPARENT
  GetDlgItem $MUI_TEMP1 $MUI_TEMP1 ${ID}
  SetCtlColors $MUI_TEMP1 "${UMUI_TEXT_LIGHTCOLOR}" "${MUI_BGCOLOR}"
!endif
;-----
!macroend

; Set transparent the background and the light text color of the control in a static Pages
!macro UMUI_PAGECTLLIGHTTRANSPARENT_INIT ID
!ifndef USE_MUIEx
;-----------------
  FindWindow $MUI_TEMP1 "#32770" "" $HWNDPARENT
  GetDlgItem $MUI_TEMP1 $MUI_TEMP1 ${ID}
  !ifdef UMUI_${MUI_PAGE_UNINSTALLER_PREFIX}PAGEBGIMAGE
    SetCtlColors $MUI_TEMP1 "${UMUI_TEXT_LIGHTCOLOR}" "transparent"
  !else
    SetCtlColors $MUI_TEMP1 "${UMUI_TEXT_LIGHTCOLOR}" "${MUI_BGCOLOR}"
  !endif
!endif
;-----
!macroend

; Set the background and text colors of the input control in a static Pages
!macro UMUI_PAGEINPUTCTL_INIT ID
  FindWindow $MUI_TEMP1 "#32770" "" $HWNDPARENT
  GetDlgItem $MUI_TEMP1 $MUI_TEMP1 ${ID}
  SetCtlColors $MUI_TEMP1 "${UMUI_TEXT_INPUTCOLOR}" "${UMUI_BGINPUTCOLOR}"
!macroend

; Change the background on the Welcome/Finish/Abort Pages
!macro UMUI_WFAPAGEBGTRANSPARENT_INIT HWND
!ifndef USE_MUIEx
;----------------
  !ifdef UMUI_${MUI_PAGE_UNINSTALLER_PREFIX}PAGEBGIMAGE
    !ifndef UMUI_NO_WFA_BGTRANSPARENT
      SetCtlColors ${HWND} "" "transparent"
    !else
      SetCtlColors ${HWND} "${MUI_TEXTCOLOR}" "${MUI_BGCOLOR}"
    !endif
  !else
    SetCtlColors ${HWND} "${MUI_TEXTCOLOR}" "${MUI_BGCOLOR}"
  !endif
!else
;-----
  SetCtlColors ${HWND} "${MUI_TEXTCOLOR}" "${MUI_BGCOLOR}"
!endif
;-----
!macroend

; Change the background of IO Pages
!macro UMUI_IOPAGEBGTRANSPARENT_INIT HWND
!ifndef USE_MUIEx
;----------------
  !ifdef UMUI_${MUI_PAGE_UNINSTALLER_PREFIX}PAGEBGIMAGE
    !ifndef UMUI_IONOBGTRANSPARENT
      SetCtlColors ${HWND} "" "transparent"
    !else
      SetCtlColors ${HWND} "${MUI_TEXTCOLOR}" "${MUI_BGCOLOR}"
    !endif
  !else
    SetCtlColors ${HWND} "${MUI_TEXTCOLOR}" "${MUI_BGCOLOR}"
  !endif
!endif
;-----
  !insertmacro MUI_UNSET UMUI_IONOBGTRANSPARENT
!macroend

; Change the background of IO Pages
!macro UMUI_IOPAGEBG_INIT HWND
!ifndef USE_MUIEx
;----------------
  SetCtlColors ${HWND} "${MUI_TEXTCOLOR}" "${MUI_BGCOLOR}"
!endif
;-----
!macroend

; Change transparent the background of the IO Controls
!macro UMUI_IOPAGECTLTRANSPARENT_INIT HWND
!ifndef USE_MUIEx
;-----------------
  !ifdef UMUI_${MUI_PAGE_UNINSTALLER_PREFIX}PAGEBGIMAGE
    SetCtlColors ${HWND} "${MUI_TEXTCOLOR}" "transparent"
  !else
    SetCtlColors ${HWND} "${MUI_TEXTCOLOR}" "${MUI_BGCOLOR}"
  !endif
!else
;-----
  SetCtlColors ${HWND} "${MUI_TEXTCOLOR}" "${MUI_BGCOLOR}"
!endif
;-----
!macroend

; Change the background color of the IO Controls
!macro UMUI_IOPAGECTL_INIT HWND
  SetCtlColors ${HWND} "${MUI_TEXTCOLOR}" "${MUI_BGCOLOR}"
!macroend

; Set the background and text colors of the IO Input Controls
!macro UMUI_IOPAGEINPUTCTL_INIT HWND
  SetCtlColors ${HWND} "${UMUI_TEXT_INPUTCOLOR}" "${UMUI_BGINPUTCOLOR}"
!macroend

; Set the background color and the light text color of the IO Controls
!macro UMUI_IOPAGECTLLIGHT_INIT HWND
  SetCtlColors ${HWND} "${UMUI_TEXT_LIGHTCOLOR}" "${MUI_BGCOLOR}"
!macroend

; Set transparent the background and the light text color of the IO Controls
!macro UMUI_IOPAGECTLLIGHTTRANSPARENT_INIT HWND
!ifndef USE_MUIEx
;-----------------
  !ifdef UMUI_${MUI_PAGE_UNINSTALLER_PREFIX}PAGEBGIMAGE
    SetCtlColors ${HWND} "${UMUI_TEXT_LIGHTCOLOR}" "transparent"
  !else
    SetCtlColors ${HWND} "${UMUI_TEXT_LIGHTCOLOR}" "${MUI_BGCOLOR}"
  !endif
!else
;-----
  SetCtlColors ${HWND} "${UMUI_TEXT_LIGHTCOLOR}" "${MUI_BGCOLOR}"
!endif
;-----
!macroend

!macro MUI_INNERDIALOG_TEXT CONTROL TEXT

  !verbose push
  !verbose ${MUI_VERBOSE}

  FindWindow $MUI_TEMP1 "#32770" "" $HWNDPARENT
  GetDlgItem $MUI_TEMP1 $MUI_TEMP1 ${CONTROL}
  SendMessage $MUI_TEMP1 ${WM_SETTEXT} 0 "STR:${TEXT}"

  !verbose pop

!macroend

!macro MUI_HEADER_TEXT_INTERNAL ID TEXT

  GetDlgItem $MUI_TEMP1 $HWNDPARENT "${ID}"

  !ifndef UMUI_HEADERBGIMAGE
    !ifdef MUI_HEADER_TRANSPARENT_TEXT

      ShowWindow $MUI_TEMP1 ${SW_HIDE}

    !endif
  !endif

  SendMessage $MUI_TEMP1 ${WM_SETTEXT} 0 "STR:${TEXT}"

  !ifndef UMUI_HEADERBGIMAGE
    !ifdef MUI_HEADER_TRANSPARENT_TEXT

      ShowWindow $MUI_TEMP1 ${SW_SHOWNA}

    !endif
  !endif

!macroend

!macro MUI_HEADER_TEXT TEXT SUBTEXT

  !verbose push
  !verbose ${MUI_VERBOSE}

!ifndef USE_MUIEx
;-----------------

  !ifndef UMUI_${MUI_PAGE_UNINSTALLER_PREFIX}UNIQUEBGIMAGE
    SetBrandingImage /IMGID=1034 /RESIZETOFIT "$PLUGINSDIR\Header.bmp"
  !endif

!else
;-----

  !ifdef UMUI_HEADERBGIMAGE
    SetBrandingImage /IMGID=1034 /RESIZETOFIT "$PLUGINSDIR\Header.bmp"
  !endif

  !ifdef MUI_HEADER_TRANSPARENT_TEXT

    LockWindow on

  !endif

!endif
;-----

  !insertmacro MUI_HEADER_TEXT_INTERNAL 1037 "${TEXT}"
  !insertmacro MUI_HEADER_TEXT_INTERNAL 1038 "${SUBTEXT}"

!ifdef USE_MUIEx
;----------------

  !ifdef MUI_HEADER_TRANSPARENT_TEXT

    LockWindow off

  !endif

!endif
;-----

  !verbose pop

!macroend

!macro MUI_HEADER_TEXT_PAGE TEXT SUBTEXT

  !ifdef MUI_PAGE_HEADER_TEXT & MUI_PAGE_HEADER_SUBTEXT
    !insertmacro MUI_HEADER_TEXT "${MUI_PAGE_HEADER_TEXT}" "${MUI_PAGE_HEADER_SUBTEXT}"
  !else ifdef MUI_PAGE_HEADER_TEXT
    !insertmacro MUI_HEADER_TEXT "${MUI_PAGE_HEADER_TEXT}" "${SUBTEXT}"
  !else ifdef MUI_PAGE_HEADER_SUBTEXT
    !insertmacro MUI_HEADER_TEXT "${TEXT}" "${MUI_PAGE_HEADER_SUBTEXT}"
  !else
    !insertmacro MUI_HEADER_TEXT "${TEXT}" "${SUBTEXT}"
  !endif

  !insertmacro MUI_UNSET MUI_PAGE_HEADER_TEXT
  !insertmacro MUI_UNSET MUI_PAGE_HEADER_SUBTEXT

!macroend

!macro MUI_DESCRIPTION_BEGIN

  FindWindow $MUI_TEMP1 "#32770" "" $HWNDPARENT
  GetDlgItem $MUI_TEMP1 $MUI_TEMP1 1043

  StrCmp $0 -1 0 mui.description_begin_done
    SendMessage $MUI_TEMP1 ${WM_SETTEXT} 0 "STR:"

!ifndef USE_MUIEx
;----------------
    !ifndef UMUI_ENABLE_DESCRIPTION_TEXT
      EnableWindow $MUI_TEMP1 0
    !else
      !insertmacro UMUI_PAGECTLLIGHT_INIT 1043
;      !insertmacro UMUI_PAGECTLLIGHTTRANSPARENT_INIT 1043
    !endif
!else
;-----
    EnableWindow $MUI_TEMP1 0
!endif
;-----

    SendMessage $MUI_TEMP1 ${WM_SETTEXT} 0 "STR:$MUI_TEXT"
    Goto mui.description_done
  mui.description_begin_done:

!macroend

!macro MUI_DESCRIPTION_TEXT VAR TEXT

  !verbose push
  !verbose ${MUI_VERBOSE}

  StrCmp $0 ${VAR} 0 mui.description_${VAR}_done
    SendMessage $MUI_TEMP1 ${WM_SETTEXT} 0 "STR:"

!ifndef USE_MUIEx
;----------------
    !ifndef UMUI_ENABLE_DESCRIPTION_TEXT
      EnableWindow $MUI_TEMP1 1
    !else
      !insertmacro UMUI_PAGECTL_INIT 1043
;      !insertmacro UMUI_PAGECTLTRANSPARENT_INIT 1043
    !endif
!else
;-----
    EnableWindow $MUI_TEMP1 1
!endif
;-----

    SendMessage $MUI_TEMP1 ${WM_SETTEXT} 0 "STR:${TEXT}"
    Goto mui.description_done
  mui.description_${VAR}_done:

  !verbose pop

!macroend

!macro MUI_DESCRIPTION_END

  !verbose push
  !verbose ${MUI_VERBOSE}

  mui.description_done:

!ifndef USE_MUIEx
;----------------
  !ifdef UMUI_${MUI_PAGE_UNINSTALLER_PREFIX}PAGEBGIMAGE

; Workaround attempt for stransparent component description
; But all these methods flicker:

; method 1
;    System::Call "user32::LockWindowUpdate(i)i ($MUI_TEMP1)"
;    System::Call "user32::InvalidateRect(i,i,i)i ($MUI_TEMP1, 0, 1)"
;!define RDW_INVALIDATE 0x0001
;!define RDW_ERASE 0x0004
;!define RDW_UPDATENOW 0x0100
;    System::Call "user32::RedrawWindow(i,i,i,i)i ($MUI_TEMP1, 0, 0, ${RDW_INVALIDATE}|${RDW_ERASE}|${RDW_UPDATENOW})"
;    System::Call "user32::LockWindowUpdate(i)i (0)"

; method 2
;    LockWindow on
;    LockWindow off

; method 3
;  FindWindow $MUI_TEMP2 "#32770" "" $HWNDPARENT
;  ShowWindow $MUI_TEMP2 ${SW_HIDE}
;  ShowWindow $MUI_TEMP2 ${SW_SHOW}

  !endif
!endif
;-----

  !verbose pop

!macroend

!macro MUI_ENDHEADER

  IfAbort mui.endheader_abort

    !ifdef MUI_INSTFILESPAGE_FINISHHEADER_TEXT & MUI_INSTFILESPAGE_FINISHHEADER_SUBTEXT
      !insertmacro MUI_HEADER_TEXT "${MUI_INSTFILESPAGE_FINISHHEADER_TEXT}" "${MUI_INSTFILESPAGE_FINISHHEADER_SUBTEXT}"
    !else ifdef MUI_INSTFILESPAGE_FINISHHEADER_TEXT
      !insertmacro MUI_HEADER_TEXT "${MUI_INSTFILESPAGE_FINISHHEADER_TEXT}" "$(MUI_${MUI_PAGE_UNINSTALLER_PREFIX}TEXT_FINISH_SUBTITLE)"
    !else ifdef MUI_INSTFILESPAGE_FINISHHEADER_SUBTEXT
      !insertmacro MUI_HEADER_TEXT "$(MUI_${MUI_PAGE_UNINSTALLER_PREFIX}TEXT_FINISH_TITLE)" "${MUI_INSTFILESPAGE_FINISHHEADER_SUBTEXT}"
    !else
      !insertmacro MUI_HEADER_TEXT "$(MUI_${MUI_PAGE_UNINSTALLER_PREFIX}TEXT_FINISH_TITLE)" "$(MUI_${MUI_PAGE_UNINSTALLER_PREFIX}TEXT_FINISH_SUBTITLE)"
    !endif

  Goto mui.endheader_done

  mui.endheader_abort:

    !ifdef MUI_INSTFILESPAGE_ABORTHEADER_TEXT & MUI_INSTFILESPAGE_ABORTHEADER_SUBTEXT
      !insertmacro MUI_HEADER_TEXT "${MUI_INSTFILESPAGE_ABORTHEADER_TEXT}" "${MUI_INSTFILESPAGE_ABORTHEADER_SUBTEXT}"
    !else ifdef MUI_INSTFILESPAGE_ABORTHEADER_TEXT
      !insertmacro MUI_HEADER_TEXT "${MUI_INSTFILESPAGE_ABORTHEADER_TEXT}" "$(MUI_${MUI_PAGE_UNINSTALLER_PREFIX}TEXT_ABORT_SUBTITLE)"
    !else ifdef MUI_INSTFILESPAGE_ABORTHEADER_SUBTEXT
      !insertmacro MUI_HEADER_TEXT "$(MUI_${MUI_PAGE_UNINSTALLER_PREFIX}TEXT_ABORT_TITLE)" "${MUI_INSTFILESPAGE_ABORTHEADER_SUBTEXT}"
    !else
      !insertmacro MUI_HEADER_TEXT "$(MUI_${MUI_PAGE_UNINSTALLER_PREFIX}TEXT_ABORT_TITLE)" "$(MUI_${MUI_PAGE_UNINSTALLER_PREFIX}TEXT_ABORT_SUBTITLE)"
    !endif

  mui.endheader_done:

!macroend

!macro MUI_ABORTWARNING

  !ifdef MUI_FINISHPAGE_ABORTWARNINGCHECK
    StrCmp $MUI_NOABORTWARNING "1" mui.quit
  !endif

  !ifdef MUI_ABORTWARNING_CANCEL_DEFAULT
    MessageBox MB_YESNO|MB_ICONEXCLAMATION|MB_DEFBUTTON2 "${MUI_ABORTWARNING_TEXT}" IDYES mui.quit
  !else
    MessageBox MB_YESNO|MB_ICONEXCLAMATION "${MUI_ABORTWARNING_TEXT}" IDYES mui.quit
  !endif

  Abort
  mui.quit:

!macroend

!macro MUI_UNABORTWARNING

  !ifdef MUI_UNABORTWARNING_CANCEL_DEFAULT
    MessageBox MB_YESNO|MB_ICONEXCLAMATION|MB_DEFBUTTON2 "${MUI_UNABORTWARNING_TEXT}" IDYES mui.quit
  !else
    MessageBox MB_YESNO|MB_ICONEXCLAMATION "${MUI_UNABORTWARNING_TEXT}" IDYES mui.quit
  !endif

  Abort
  mui.quit:

!macroend

!macro MUI_GUIINIT

  !insertmacro UMUI_WELCOMEFINISHABORTPAGE_INIT ""

!ifdef USE_MUIEx
;----------------
  !insertmacro MUI_HEADERIMAGE_INIT ""
!endif
;----------------

  !insertmacro MUI_GUIINIT_BASIC ""

  !ifdef MUI_FINISHPAGE
    !ifndef MUI_FINISHPAGE_NOAUTOCLOSE
      SetAutoClose true
    !endif
  !endif

!macroend

!macro MUI_UNGUIINIT

  !insertmacro UMUI_WELCOMEFINISHABORTPAGE_INIT "UN"

!ifdef USE_MUIEx
;----------------
  !insertmacro MUI_HEADERIMAGE_INIT ""
!endif
;----------------

  !insertmacro MUI_GUIINIT_BASIC "UN"

  !ifdef MUI_UNFINISHPAGE
    !ifndef MUI_UNFINISHPAGE_NOAUTOCLOSE
      SetAutoClose true
    !endif
  !endif

!macroend

!macro MUI_GUIINIT_BASIC UNPREFIX

  InitPluginsDir

!ifndef USE_MUIEx
;-----------------

  GetDlgItem $MUI_TEMP1 $HWNDPARENT 1037
  CreateFont $MUI_TEMP2 "$(^Font)" "$(^FontSize)" "700"
  SendMessage $MUI_TEMP1 ${WM_SETFONT} $MUI_TEMP2 0
  SetCtlColors $MUI_TEMP1 "${UMUI_HEADERTEXT_COLOR}" "transparent"

  GetDlgItem $MUI_TEMP1 $HWNDPARENT 1038
  SetCtlColors $MUI_TEMP1 "${UMUI_HEADERTEXT_COLOR}" "transparent"

  GetDlgItem $MUI_TEMP1 $HWNDPARENT 1028
  CreateFont $MUI_TEMP2 Arial 10 1400
  SetCtlColors $MUI_TEMP1 ${UMUI_BRANDINGTEXTFRONTCOLOR} "transparent"
  SendMessage $MUI_TEMP1 ${WM_SETFONT} "$MUI_TEMP2" 0
  SendMessage $MUI_TEMP1 ${WM_SETTEXT} 0 "STR:$(^Branding) "

  GetDlgItem $MUI_TEMP1 $HWNDPARENT 1256
  CreateFont $MUI_TEMP2 Arial 10 1400
  SetCtlColors $MUI_TEMP1 ${UMUI_BRANDINGTEXTBACKCOLOR} "transparent"
  SendMessage $MUI_TEMP1 ${WM_SETFONT} "$MUI_TEMP2" 0
  SendMessage $MUI_TEMP1 ${WM_SETTEXT} 0 "STR:$(^Branding) "

  SetCtlColors $HWNDPARENT "${MUI_BGCOLOR}" "${MUI_BGCOLOR}"

  !ifndef UMUI_${UNPREFIX}UNIQUEBGIMAGE

    !ifdef UMUI_${UNPREFIX}LEFTIMAGE_BMP
      ReserveFile "${UMUI_${UNPREFIX}LEFTIMAGE_BMP}"

      SetOutPath "$PLUGINSDIR"
      File /oname=LeftImg.bmp "${UMUI_${UNPREFIX}LEFTIMAGE_BMP}"
      SetBrandingImage /IMGID=1302 /RESIZETOFIT "$PLUGINSDIR\LeftImg.bmp"
    !endif

    !ifdef UMUI_HEADERBGIMAGE
      ReserveFile "${UMUI_${UNPREFIX}HEADERBGIMAGE_BMP}"
      SetOutPath "$PLUGINSDIR"
      File /oname=Header.bmp "${UMUI_${UNPREFIX}HEADERBGIMAGE_BMP}"
      SetBrandingImage /IMGID=1034 /RESIZETOFIT "$PLUGINSDIR\Header.bmp"
    !else
      GetDlgItem $MUI_TEMP1 $HWNDPARENT 1034
      SetCtlColors $MUI_TEMP1 "${MUI_TEXTCOLOR}" "${MUI_BGCOLOR}"
    !endif

    !ifdef UMUI_${UNPREFIX}BOTTOMIMAGE_BMP
      ReserveFile "${UMUI_${UNPREFIX}BOTTOMIMAGE_BMP}"

      SetOutPath "$PLUGINSDIR"
      File /oname=BtmImg.bmp "${UMUI_${UNPREFIX}BOTTOMIMAGE_BMP}"
      SetBrandingImage /IMGID=1305 /RESIZETOFIT "$PLUGINSDIR\BtmImg.bmp"
    !endif

    !ifdef UMUI_${UNPREFIX}PAGEBGIMAGE
      ReserveFile "${UMUI_${UNPREFIX}PAGEBGIMAGE_BMP}"
      SetOutPath "$PLUGINSDIR"
      File /oname=PageBG.bmp "${UMUI_${UNPREFIX}PAGEBGIMAGE_BMP}"
      SetBrandingImage /IMGID=1303 /RESIZETOFIT "$PLUGINSDIR\PageBG.bmp"
    !else
      GetDlgItem $MUI_TEMP1 $HWNDPARENT 1303
      ShowWindow $MUI_TEMP1 ${SW_HIDE}
    !endif

    GetDlgItem $MUI_TEMP1 $HWNDPARENT 1304
    ShowWindow $MUI_TEMP1 ${SW_HIDE}

  !else

    ReserveFile "${UMUI_${UNPREFIX}PAGEBGIMAGE_BMP}"
    SetOutPath "$PLUGINSDIR"
    File /oname=PageBG.bmp "${UMUI_${UNPREFIX}PAGEBGIMAGE_BMP}"
    SetBrandingImage /IMGID=1304 /RESIZETOFIT "$PLUGINSDIR\PageBG.bmp"

    GetDlgItem $MUI_TEMP1 $HWNDPARENT 1302
    ShowWindow $MUI_TEMP1 ${SW_HIDE}
    GetDlgItem $MUI_TEMP1 $HWNDPARENT 1303
    ShowWindow $MUI_TEMP1 ${SW_HIDE}
    GetDlgItem $MUI_TEMP1 $HWNDPARENT 1305
    ShowWindow $MUI_TEMP1 ${SW_HIDE}
    GetDlgItem $MUI_TEMP1 $HWNDPARENT 1034
    ShowWindow $MUI_TEMP1 ${SW_HIDE}

  !endif

  GetDlgItem $MUI_TEMP1 $HWNDPARENT 1018
  SetCtlColors $MUI_TEMP1 "${MUI_TEXTCOLOR}" "${MUI_BGCOLOR}"
  GetDlgItem $MUI_TEMP1 $HWNDPARENT 1045
  ShowWindow $MUI_TEMP1 ${SW_HIDE}
  SetCtlColors $MUI_TEMP1 "${MUI_TEXTCOLOR}" "${MUI_BGCOLOR}"

!else
;-----------------

  GetDlgItem $MUI_TEMP1 $HWNDPARENT 1037
  CreateFont $MUI_TEMP2 "$(^Font)" "$(^FontSize)" "700"
  SendMessage $MUI_TEMP1 ${WM_SETFONT} $MUI_TEMP2 0

  !ifndef MUI_HEADER_TRANSPARENT_TEXT

    SetCtlColors $MUI_TEMP1 "${UMUI_HEADERTEXT_COLOR}" "${MUI_BGCOLOR}"

    GetDlgItem $MUI_TEMP1 $HWNDPARENT 1038
    SetCtlColors $MUI_TEMP1 "${UMUI_HEADERTEXT_COLOR}" "${MUI_BGCOLOR}"

  !else

    SetCtlColors $MUI_TEMP1 "${UMUI_HEADERTEXT_COLOR}" "transparent"

    GetDlgItem $MUI_TEMP1 $HWNDPARENT 1038
    SetCtlColors $MUI_TEMP1 "${UMUI_HEADERTEXT_COLOR}" "transparent"

  !endif

  !ifdef UMUI_HEADERBGIMAGE

    ReserveFile "${UMUI_${UNPREFIX}HEADERBGIMAGE_BMP}"
    SetOutPath "$PLUGINSDIR"
    File /oname=Header.bmp "${UMUI_${UNPREFIX}HEADERBGIMAGE_BMP}"
    SetBrandingImage /IMGID=1034 /RESIZETOFIT "$PLUGINSDIR\Header.bmp"

  !else

    GetDlgItem $MUI_TEMP1 $HWNDPARENT 1034 ; Header background
    SetCtlColors $MUI_TEMP1 "${MUI_TEXTCOLOR}" "${MUI_BGCOLOR}"

  !endif


  GetDlgItem $MUI_TEMP1 $HWNDPARENT 1039 ; Header image
  SetCtlColors $MUI_TEMP1 "${MUI_TEXTCOLOR}" "${MUI_BGCOLOR}"

  GetDlgItem $MUI_TEMP1 $HWNDPARENT 1028
  SetCtlColors $MUI_TEMP1 /BRANDING
  GetDlgItem $MUI_TEMP1 $HWNDPARENT 1256
  SetCtlColors $MUI_TEMP1 /BRANDING
  SendMessage $MUI_TEMP1 ${WM_SETTEXT} 0 "STR:$(^Branding) "

!endif
;----------------


  !ifdef UMUI_${UNPREFIX}BUTTONIMAGE_BMP | UMUI_${UNPREFIX}SCROLLBARIMAGE_BMP
    !insertmacro UMUI_RESERVEFILE_SKINNEDCONTROLS
  !endif

  !ifdef UMUI_${UNPREFIX}BUTTONIMAGE_BMP

    ReserveFile "${UMUI_${UNPREFIX}BUTTONIMAGE_BMP}"

    SetOutPath "$PLUGINSDIR"
    File /oname=ButtonImg.bmp "${UMUI_${UNPREFIX}BUTTONIMAGE_BMP}"

  !endif

  !ifdef UMUI_${UNPREFIX}SCROLLBARIMAGE_BMP

    ReserveFile "${UMUI_${UNPREFIX}SCROLLBARIMAGE_BMP}"

    SetOutPath "$PLUGINSDIR"
    File /oname=ScrollBarImg.bmp "${UMUI_${UNPREFIX}SCROLLBARIMAGE_BMP}"

  !endif

  !ifdef UMUI_${UNPREFIX}BUTTONIMAGE_BMP | UMUI_${UNPREFIX}SCROLLBARIMAGE_BMP

    ;starting SkinnedControls plugin
    !ifdef UMUI_${UNPREFIX}BUTTONIMAGE_BMP & UMUI_${UNPREFIX}SCROLLBARIMAGE_BMP
      SkinnedControls::skinit \
        /disabledtextcolor=${UMUI_${UNPREFIX}DISABLED_BUTTON_TEXT_COLOR} \
        /selectedtextcolor=${UMUI_${UNPREFIX}SELECTED_BUTTON_TEXT_COLOR} \
        /textcolor=${UMUI_${UNPREFIX}BUTTON_TEXT_COLOR} \
        /button=$PLUGINSDIR\ButtonImg.bmp \
        /scrollbar=$PLUGINSDIR\ScrollBarImg.bmp
    !else ifdef UMUI_${UNPREFIX}BUTTONIMAGE_BMP
      SkinnedControls::skinit \
        /disabledtextcolor=${UMUI_${UNPREFIX}DISABLED_BUTTON_TEXT_COLOR} \
        /selectedtextcolor=${UMUI_${UNPREFIX}SELECTED_BUTTON_TEXT_COLOR} \
        /textcolor=${UMUI_${UNPREFIX}BUTTON_TEXT_COLOR} \
        /button=$PLUGINSDIR\ButtonImg.bmp
    !else
      SkinnedControls::skinit /scrollbar=$PLUGINSDIR\ScrollBarImg.bmp
    !endif

  !endif

   ClearErrors

  ;get parameters in a ini file
  !insertmacro UMUI_PARAMETERS_TO_INI

  !insertmacro UMUI_RESTORESHELLVARCONTEXT

!macroend


!macro UMUI_DELETE_PLUGINDIR
  SetOutPath $EXEDIR
  Delete "$PLUGINSDIR\*.*"
  RMDir /r /REBOOTOK $PLUGINSDIR
  ClearErrors
!macroend




; Taken from the NSIS Documentation
!macro UMUI_GET_PARAMETERS

  !define UMUI_UNIQUEID ${__LINE__}

  Push $R0
  Push $R1
  Push $R2
  Push $R3

  StrCpy $R2 1
  StrLen $R3 $CMDLINE

  ;Check for quote or space
  StrCpy $R0 $CMDLINE $R2 ; copy the first char
  StrCmp $R0 '"' 0 +3
    StrCpy $R1 '"'
  Goto loop${UMUI_UNIQUEID}
    StrCpy $R1 " "

  loop${UMUI_UNIQUEID}:
    IntOp $R2 $R2 + 1
    StrCpy $R0 $CMDLINE 1 $R2
    StrCmp $R0 $R1 get${UMUI_UNIQUEID} ;found the " or space char
      StrCmp $R2 $R3 get${UMUI_UNIQUEID} loop${UMUI_UNIQUEID} ;all the $CMDLINE string was viewed

  get${UMUI_UNIQUEID}:
    IntOp $R2 $R2 + 1
    StrCpy $R0 $CMDLINE 1 $R2
    StrCmp $R0 " " get${UMUI_UNIQUEID}
      StrCpy $R0 $CMDLINE "" $R2

  Pop $R3
  Pop $R2
  Pop $R1
  Exch $R0

  !undef UMUI_UNIQUEID

!macroend


; Get all parameters in the command line and put it an ini
;  /S /L=1033 /D="C:\Program Files\Foo" para4 para5 "para 6"
!macro UMUI_PARAMETERS_TO_INI

  Push $R0 ;All the parameters
  Push $R1 ;param counter
  Push $R2 ;char counter
  Push $R3 ;parameters string len
  Push $R4 ;char to compare
  Push $R5 ; param name
  Push $R6 ; param value

  IfFileExists "$PLUGINSDIR\Parameters.ini" end 0

  !insertmacro UMUI_GET_PARAMETERS
  Pop $R0

  StrCpy $R1 0

  ;for each parameters
  while:

    ;If $R0 empty, goto end
    StrLen $R3 $R0
    StrCpy $R2 0

    ;trim the spaces at the begining of the string
    looptrim:
      StrCmp $R2 $R3 end ;all the parameters string was viewed
        StrCpy $R4 $R0 1 $R2
        StrCmp $R4 " " 0 endtrim ;found the space
          IntOp $R2 $R2 + 1
          Goto looptrim
    endtrim:

    StrCpy $R0 $R0 "" $R2
    StrCpy $R2 0

    ;inc num param
    IntOp $R1 $R1 + 1

    ;If the parameter begin with a "/"
    StrCpy $R4 $R0 1 $R2 ;copy the first char

    StrCpy $R5 "" ; name empty
    StrCpy $R6 "" ; value empty

    StrCmp $R4 "/" 0 getval
      IntOp $R2 $R2 - 1
;      Goto getname

    getname:
      ;whait for an = or a space

      IntOp $R2 $R2 + 1
      StrCpy $R4 $R0 1 $R2
      StrCmp $R4 "=" getval1 ;found the =
        StrCmp $R4 " " save ;found the space

          StrCpy $R5 "$R5$R4"
          StrCmp $R2 $R3 save getname ;all the parameters string was viewed

    getval1:
      IntOp $R2 $R2 + 1
    getval:
      StrCpy $R4 $R0 1 $R2
      StrCmp $R4 '"' waitquote 0 ;found a quote

        IntOp $R2 $R2 - 1

        waitspace:
          IntOp $R2 $R2 + 1
          StrCpy $R4 $R0 1 $R2
          StrCmp $R4 " " save ;found the space
            StrCpy $R6 "$R6$R4"
            StrCmp $R2 $R3 save waitspace ;all the parameters string was viewed

        waitquote:
          IntOp $R2 $R2 + 1
          StrCpy $R4 $R0 1 $R2
          StrCmp $R4 '"' save1 ;found the quote
            StrCpy $R6 "$R6$R4"
            StrCmp $R2 $R3 save1 waitquote ;all the parameters string was viewed

    save1:
      IntOp $R2 $R2 + 2
    save:
      WriteIniStr "$PLUGINSDIR\Parameters.ini" "Setting" "Num" "$R1"
      WriteIniStr "$PLUGINSDIR\Parameters.ini" "$R1" "Name" "$R5"
      WriteIniStr "$PLUGINSDIR\Parameters.ini" "$R1" "Value" "$R6"

      StrCmp $R5 "" +2 0
        WriteIniStr "$PLUGINSDIR\Parameters.ini" "$R5" "Value" "$R6"
        StrCpy $R0 $R0 "" $R2

   Goto while
   end:

   Pop $R6
   Pop $R5
   Pop $R4
   Pop $R3
   Pop $R2
   Pop $R1
   Pop $R0

!macroend


!macro UMUI_GETPARAMETERVALUE SWITCH DEFAULT

  Push $R0

  ReadIniStr $R0 "$PLUGINSDIR\Parameters.ini" "${SWITCH}" "Value"
  StrCmp $R0 "" 0 +3
    StrCpy $R0 "${DEFAULT}"
    ClearErrors

  Exch $R0

!macroend

!macro UMUI_PARAMETERISSET SWITCH

  Push $R0

  ClearErrors
  ReadIniStr $R0 "$PLUGINSDIR\Parameters.ini" "${SWITCH}" "Value"

  ; The error flag is set if error
  Exch $R0

!macroend

!macro UMUI_GETNUMPARAM

  Push $R0

  ReadIniStr $R0 "$PLUGINSDIR\Parameters.ini" "Setting" "Num"
  StrCmp $R0 "" 0 +3
    StrCpy $R0 0
    ClearErrors

  Exch $R0

!macroend


!macro UMUI_ADDPARAMTOSAVETOREGISTRY VALUENAME DATA

  !ifndef UMUI_PARAMS_REGISTRY_ROOT & UMUI_PARAMS_REGISTRY_KEY
    !error "The global parameters: UMUI_PARAMS_REGISTRY_ROOT and UMUI_PARAMS_REGISTRY_KEY are not defined."
  !endif

  !define UMUI_UNIQUEID ${__LINE__}

  Push $R0
  Push $R1
  Push $R2

  ClearErrors
  ReadIniStr $R0 "$PLUGINSDIR\Registry.ini" "Settings" "number"
  IfErrors 0 +3
    ClearErrors
    StrCpy $R0 0

  WriteIniStr "$PLUGINSDIR\Registry.ini" "Settings" "REGISTRY_ROOT" "${UMUI_PARAMS_REGISTRY_ROOT}"
  WriteIniStr "$PLUGINSDIR\Registry.ini" "Settings" "REGISTRY_KEY" "${UMUI_PARAMS_REGISTRY_KEY}"

  StrCmp $R0 0 notfound${UMUI_UNIQUEID} 0

  ;search if not already written in the ini file
  StrCpy $R1 0

  loop${UMUI_UNIQUEID}:
    IntOp $R1 $R1 + 1
    IntCmp $R1 $R0 0 0 notfound${UMUI_UNIQUEID}
      ReadIniStr $R2 "$PLUGINSDIR\Registry.ini" "$R1" "Value_Name"
      StrCmp $R2 "${VALUENAME}" found${UMUI_UNIQUEID} loop${UMUI_UNIQUEID}

  notfound${UMUI_UNIQUEID}:
    IntOp $R1 $R0 + 1

    WriteIniStr "$PLUGINSDIR\Registry.ini" "Settings" "number" $R1
    WriteIniStr "$PLUGINSDIR\Registry.ini" "$R1" "Value_Name" "${VALUENAME}"
    WriteIniStr "$PLUGINSDIR\Registry.ini" "$R1" "Data" "${DATA}"

  found${UMUI_UNIQUEID}:
    WriteIniStr "$PLUGINSDIR\Registry.ini" "$R1" "Data" "${DATA}"

  Pop $R2
  Pop $R1
  Pop $R0

  !undef UMUI_UNIQUEID

!macroend

!macro UMUI_ADDPARAMTOSAVETOREGISTRYKEY REGISTRY_ROOT REGISTRY_KEY VALUENAME DATA

  !define UMUI_UNIQUEID ${__LINE__}

  Push $R0
  Push $R1
  Push $R2

  ClearErrors
  ReadIniStr $R0 "$PLUGINSDIR\Registry.ini" "Settings" "number"
  IfErrors 0 noerror${UMUI_UNIQUEID}
    ClearErrors
    StrCpy $R0 0
    Goto notfound${UMUI_UNIQUEID}
  noerror${UMUI_UNIQUEID}:

  ;search if not already written in the ini file
  StrCpy $R1 0

  loop${UMUI_UNIQUEID}:
    IntOp $R1 $R1 + 1
    IntCmp $R1 $R0 0 0 notfound${UMUI_UNIQUEID}
      ReadIniStr $R2 "$PLUGINSDIR\Registry.ini" "$R1" "Value_Name"
      StrCmp $R2 "${VALUENAME}" found${UMUI_UNIQUEID} loop${UMUI_UNIQUEID}

    notfound${UMUI_UNIQUEID}:
      IntOp $R1 $R0 + 1

      WriteIniStr "$PLUGINSDIR\Registry.ini" "Settings" "number" $R1
      WriteIniStr "$PLUGINSDIR\Registry.ini" "$R1" "Value_Name" "${VALUENAME}"

    found${UMUI_UNIQUEID}:
      WriteIniStr "$PLUGINSDIR\Registry.ini" "$R1" "Data" "${DATA}"
      WriteIniStr "$PLUGINSDIR\Registry.ini" "$R1" "REGISTRY_ROOT" "${REGISTRY_ROOT}"
      WriteIniStr "$PLUGINSDIR\Registry.ini" "$R1" "REGISTRY_KEY" "${REGISTRY_KEY}"

  Pop $R2
  Pop $R1
  Pop $R0

  !undef UMUI_UNIQUEID

!macroend


!macro UMUI_ADDSHELLVARCONTEXTTOSAVETOREGISTRY

  !ifdef UMUI_SHELLVARCONTEXT_REGISTRY_VALUENAME
    !ifndef UMUI_SHELLVARCONTEXT_REGISTRY_ROOT
      !ifdef UMUI_PARAMS_REGISTRY_ROOT
        !define UMUI_SHELLVARCONTEXT_REGISTRY_ROOT "${UMUI_PARAMS_REGISTRY_ROOT}"
      !else
        !error "For UMUI_SHELLVARCONTEXT_REGISTRY_VALUENAME, the UMUI_SHELLVARCONTEXT_REGISTRY_ROOT & UMUI_SHELLVARCONTEXT_REGISTRY_KEY parameters or else the UMUI_PARAMS_REGISTRY_ROOT & UMUI_PARAMS_REGISTRY_KEY global parameters must be defined."
      !endif
    !endif
    !ifndef UMUI_SHELLVARCONTEXT_REGISTRY_KEY
      !ifdef UMUI_PARAMS_REGISTRY_KEY
        !define UMUI_SHELLVARCONTEXT_REGISTRY_KEY "${UMUI_PARAMS_REGISTRY_KEY}"
      !else
        !error "For UMUI_SHELLVARCONTEXT_REGISTRY_VALUENAME, the UMUI_SHELLVARCONTEXT_REGISTRY_ROOT & UMUI_SHELLVARCONTEXT_REGISTRY_KEY parameters or else the UMUI_PARAMS_REGISTRY_ROOT & UMUI_PARAMS_REGISTRY_KEY global parameters must be defined."
      !endif
    !endif

    Push $MUI_TEMP1
    Push $MUI_TEMP2

    !insertmacro UMUI_GETSHELLVARCONTEXT
    Pop $MUI_TEMP2

    StrCmp $MUI_TEMP2 "current" 0 +3
      StrCpy $MUI_TEMP1 "current"
    Goto +2
      StrCpy $MUI_TEMP1 "all"

    !insertmacro UMUI_ADDPARAMTOSAVETOREGISTRYKEY ${UMUI_SHELLVARCONTEXT_REGISTRY_ROOT} "${UMUI_SHELLVARCONTEXT_REGISTRY_KEY}" "${UMUI_SHELLVARCONTEXT_REGISTRY_VALUENAME}" $MUI_TEMP1

    Pop $MUI_TEMP2
    Pop $MUI_TEMP1

  !endif

!macroend



!macro UMUI_SAVEPARAMSTOREGISTRY

  !ifndef MUI_PAGE_UNINSTALLER

    IfAbort install_aborted

      Push $MUI_TEMP1
      Push $MUI_TEMP2
      Push $R0
      Push $R1
      Push $R2
      Push $R3

      ClearErrors
      ReadIniStr $R0 "$PLUGINSDIR\Registry.ini" "Settings" "number"
      IfErrors end 0

        StrCpy $R1 "0"
        loop:

          IntOp $R1 $R1 + 1
          IntCmp $R1 $R0 0 0 end

            ReadIniStr $MUI_TEMP1 "$PLUGINSDIR\Registry.ini" "$R1" "REGISTRY_ROOT"
            ReadIniStr $MUI_TEMP2 "$PLUGINSDIR\Registry.ini" "$R1" "REGISTRY_KEY"

            ClearErrors
            StrCmp $MUI_TEMP1 "" 0 +2
              ReadIniStr $MUI_TEMP1 "$PLUGINSDIR\Registry.ini" "Settings" "REGISTRY_ROOT"
            ClearErrors
            StrCmp $MUI_TEMP2 "" 0 +2
              ReadIniStr $MUI_TEMP2 "$PLUGINSDIR\Registry.ini" "Settings" "REGISTRY_KEY"

            ReadIniStr $R2 "$PLUGINSDIR\Registry.ini" "$R1" "Value_Name"
            ReadIniStr $R3 "$PLUGINSDIR\Registry.ini" "$R1" "Data"
            StrCmp $MUI_TEMP1 HKLM 0 +3
              WriteRegStr HKLM "$MUI_TEMP2" "$R2" "$R3"
              Goto loop
            StrCmp $MUI_TEMP1 HKCU 0 +3
              WriteRegStr HKCU "$MUI_TEMP2" "$R2" "$R3"
              Goto loop
            StrCmp $MUI_TEMP1 SHCTX 0 +3
              WriteRegStr SHCTX "$MUI_TEMP2" "$R2" "$R3"
              Goto loop
            StrCmp $MUI_TEMP1 HKU 0 +3
              WriteRegStr HKU "$MUI_TEMP2" "$R2" "$R3"
              Goto loop
            StrCmp $MUI_TEMP1 HKCR 0 +3
              WriteRegStr HKCR "$MUI_TEMP2" "$R2" "$R3"
              Goto loop
            StrCmp $MUI_TEMP1 HKCC 0 +3
              WriteRegStr HKCC "$MUI_TEMP2" "$R2" "$R3"
              Goto loop
            StrCmp $MUI_TEMP1 HKDD 0 +3
              WriteRegStr HKDD "$MUI_TEMP2" "$R2" "$R3"
              Goto loop
            StrCmp $MUI_TEMP1 HKPD 0 +2
              WriteRegStr HKPD "$MUI_TEMP2" "$R2" "$R3"
              Goto loop
            !if ${NSIS_PACKEDVERSION} >= 0x03002000
              StrCmp $MUI_TEMP1 HKCR32 0 +2
                WriteRegStr HKCR32 "$MUI_TEMP2" "$R2" "$R3"
                Goto loop
              StrCmp $MUI_TEMP1 HKCR64 0 +2
                WriteRegStr HKCR64 "$MUI_TEMP2" "$R2" "$R3"
                Goto loop
              StrCmp $MUI_TEMP1 HKCU32 0 +2
                WriteRegStr HKCU32 "$MUI_TEMP2" "$R2" "$R3"
                Goto loop
              StrCmp $MUI_TEMP1 HKCU64 0 +2
                WriteRegStr HKCU64 "$MUI_TEMP2" "$R2" "$R3"
                Goto loop
              StrCmp $MUI_TEMP1 HKLM32 0 +2
                WriteRegStr HKLM32 "$MUI_TEMP2" "$R2" "$R3"
                Goto loop
              StrCmp $MUI_TEMP1 HKLM64 0 +2
                WriteRegStr HKLM64 "$MUI_TEMP2" "$R2" "$R3"
                Goto loop
            !endif
      end:
      ClearErrors

      Pop $R3
      Pop $R2
      Pop $R1
      Pop $R0
      Pop $MUI_TEMP2
      Pop $MUI_TEMP1

    install_aborted:

  !endif

!macroend

!macro UMUI_RESTORESHELLVARCONTEXT

  Push $MUI_TEMP1
  Push $MUI_TEMP2

  !ifdef UMUI_DEFAULT_SHELLVARCONTEXT
    StrCpy $MUI_TEMP1 "${UMUI_DEFAULT_SHELLVARCONTEXT}"
  !else
    !insertmacro UMUI_GETSHELLVARCONTEXT
    Pop $MUI_TEMP1 ;current value
  !endif

  !ifdef UMUI_SHELLVARCONTEXT_REGISTRY_VALUENAME
    !ifndef UMUI_SHELLVARCONTEXT_REGISTRY_ROOT
      !ifdef UMUI_PARAMS_REGISTRY_ROOT
        !define UMUI_SHELLVARCONTEXT_REGISTRY_ROOT "${UMUI_PARAMS_REGISTRY_ROOT}"
      !else
        !error "For UMUI_SHELLVARCONTEXT_REGISTRY_VALUENAME, the UMUI_SHELLVARCONTEXT_REGISTRY_ROOT & UMUI_SHELLVARCONTEXT_REGISTRY_KEY parameters or else the UMUI_PARAMS_REGISTRY_ROOT & UMUI_PARAMS_REGISTRY_KEY global parameters must be defined."
      !endif
    !endif
    !ifndef UMUI_SHELLVARCONTEXT_REGISTRY_KEY
      !ifdef UMUI_PARAMS_REGISTRY_KEY
        !define UMUI_SHELLVARCONTEXT_REGISTRY_KEY "${UMUI_PARAMS_REGISTRY_KEY}"
      !else
        !error "For UMUI_SHELLVARCONTEXT_REGISTRY_VALUENAME, the UMUI_SHELLVARCONTEXT_REGISTRY_ROOT & UMUI_SHELLVARCONTEXT_REGISTRY_KEY parameters or else the UMUI_PARAMS_REGISTRY_ROOT & UMUI_PARAMS_REGISTRY_KEY global parameters must be defined."
      !endif
    !endif

    ClearErrors
    ReadRegStr $MUI_TEMP2 ${UMUI_SHELLVARCONTEXT_REGISTRY_ROOT} "${UMUI_SHELLVARCONTEXT_REGISTRY_KEY}" "${UMUI_SHELLVARCONTEXT_REGISTRY_VALUENAME}"
    IfErrors +2 0
      StrCpy $MUI_TEMP1 $MUI_TEMP2
  !endif

  StrCmp $MUI_TEMP1 all 0 +3
    SetShellVarContext all
  Goto +2
    SetShellVarContext current

  ClearErrors

  Pop $MUI_TEMP2
  Pop $MUI_TEMP1

!macroend


!macro UMUI_GETSHELLVARCONTEXT

  Push $MUI_TEMP1
  Push $MUI_TEMP2

  StrCpy $MUI_TEMP2 "$SMPROGRAMS"
  SetShellVarContext current
  StrCmp $MUI_TEMP2 "$SMPROGRAMS" 0 +3
    StrCpy $MUI_TEMP1 "current"
  Goto +3
    StrCpy $MUI_TEMP1 "all"
    SetShellVarContext all

  Pop $MUI_TEMP2
  Exch $MUI_TEMP1

!macroend


!macro UMUI_RESTOREINSTDIR

  !ifdef UMUI_INSTALLDIR_REGISTRY_VALUENAME
    !ifndef UMUI_INSTALLDIR_REGISTRY_ROOT
      !ifdef UMUI_PARAMS_REGISTRY_ROOT
        !define UMUI_INSTALLDIR_REGISTRY_ROOT "${UMUI_PARAMS_REGISTRY_ROOT}"
      !else
        !error "For UMUI_INSTALLDIR_REGISTRY_VALUENAME, the UMUI_INSTALLDIR_REGISTRY_ROOT & UMUI_INSTALLDIR_REGISTRY_KEY parameters or else the UMUI_PARAMS_REGISTRY_ROOT & UMUI_PARAMS_REGISTRY_KEY global parameters must be defined."
      !endif
    !endif
    !ifndef UMUI_INSTALLDIR_REGISTRY_KEY
      !ifdef UMUI_PARAMS_REGISTRY_KEY
        !define UMUI_INSTALLDIR_REGISTRY_KEY "${UMUI_PARAMS_REGISTRY_KEY}"
      !else
        !error "For UMUI_INSTALLDIR_REGISTRY_VALUENAME, the UMUI_INSTALLDIR_REGISTRY_ROOT & UMUI_INSTALLDIR_REGISTRY_KEY parameters or else the UMUI_PARAMS_REGISTRY_ROOT & UMUI_PARAMS_REGISTRY_KEY global parameters must be defined."
      !endif
    !endif

    Push $R0
    ClearErrors
    ReadRegStr $R0 ${UMUI_INSTALLDIR_REGISTRY_ROOT} "${UMUI_INSTALLDIR_REGISTRY_KEY}" "${UMUI_INSTALLDIR_REGISTRY_VALUENAME}"
    IfErrors +2 0
      StrCpy $INSTDIR $R0
    ClearErrors
    Pop $R0
  !endif

!macroend


;Based on the StrReplace v4 function of Afrow UK
;Usage:
;!insertmacro UMUI_STRREPLACE $Var "replace" "with" "in string"
!macro UMUI_STRREPLACE Var Replace With In

  !define UMUI_UNIQUEIDSTRREPLACE ${__LINE__}

  Push $R0
  Push $R3
  Push $R4
  Push $R5
  Push $R6
  Push $R7
  Push $R8

  StrCpy $R0 "${In}"
  StrCpy $R3 -1
  StrLen $R5 $R0
  StrLen $R6 "${With}"
  StrLen $R7 "${Replace}"
  Loop${UMUI_UNIQUEIDSTRREPLACE}:
    IntOp $R3 $R3 + 1
    StrCpy $R4 $R0 $R7 $R3
    StrCmp $R3 $R5 End${UMUI_UNIQUEIDSTRREPLACE}
      StrCmp $R4 "${Replace}" 0 Loop${UMUI_UNIQUEIDSTRREPLACE}

        StrCpy $R4 $R0 $R3
        IntOp $R8 $R3 + $R7
        StrCpy $R8 $R0 "" $R8
        StrCpy $R0 "$R4${With}$R8"
        IntOp $R3 $R3 + $R6
        IntOp $R3 $R3 - 1
        IntOp $R5 $R5 - $R7
        IntOp $R5 $R5 + $R6

        Goto Loop${UMUI_UNIQUEIDSTRREPLACE}

  End${UMUI_UNIQUEIDSTRREPLACE}:

  Pop $R8
  Pop $R7
  Pop $R6
  Pop $R5
  Pop $R4
  Pop $R3
  Exch $R0 #out
  Pop `${Var}`

  !undef UMUI_UNIQUEIDSTRREPLACE

!macroend



;Usage:
;!insertmacro UMUI_STRCOUNT "string to count" "in string to search"
;Pop $Var ;the return number
; "string to count" and "in string to search" must not be a var betwen $R0 and $R4
!macro UMUI_STRCOUNT COUNT IN

  !define UMUI_UNIQUEIDSTRCOUNT ${__LINE__}

  Push $R0 ; counter
  Push $R1 ; the length of the string to count
  Push $R2 ; the length of the string into search
  Push $R3 ; char index counter
  Push $R4 ; string for comparaison

  StrCpy $R0 0
  StrLen $R1 "${COUNT}"
  StrLen $R2 "${IN}"
  StrCpy $R3 0
  Loop${UMUI_UNIQUEIDSTRCOUNT}:
    StrCpy $R4 "${IN}" $R1 $R3
    StrCmp $R3 $R2 End${UMUI_UNIQUEIDSTRCOUNT}
      IntOp $R3 $R3 + 1 ; incremente counter
      StrCmp $R4 "${COUNT}" 0 Loop${UMUI_UNIQUEIDSTRCOUNT}
        IntOp $R0 $R0 + 1
        Goto Loop${UMUI_UNIQUEIDSTRCOUNT}
  End${UMUI_UNIQUEIDSTRCOUNT}:

  Pop $R4
  Pop $R3
  Pop $R2
  Pop $R1
  Exch $R0

  !undef UMUI_UNIQUEIDSTRCOUNT

!macroend



;Based on the VersionCompare v1.0 of Instructor
;Thanks Afrow UK (Based on his Function "VersionCheckNew2")
;Usage:
;!insertmacro UMUI_VERSIONCOMPARE VER1 VER2
;Pop $Var ;the return   0: the same, 1: VER1 is newer, 2: VRE2 is newer
!macro UMUI_VERSIONCOMPARE VER1 VER2

  !verbose push
  !verbose ${MUI_VERBOSE}

  !define UMUI_UNIQUEIDVER ${__LINE__}

  Push $0
  Push $1
  Push $2
  Push $3
  Push $4
  Push $5
  Push $6
  Push $7

  StrCpy $0 "${VER1}"
  StrCpy $1 "${VER2}"

  begin${UMUI_UNIQUEIDVER}:
    StrCpy $2 -1
    IntOp $2 $2 + 1
    StrCpy $3 $0 1 $2
    StrCmp $3 '' +2
      StrCmp $3 '.' 0 -3
    StrCpy $4 $0 $2
    IntOp $2 $2 + 1
    StrCpy $0 $0 '' $2

    StrCpy $2 -1
    IntOp $2 $2 + 1
    StrCpy $3 $1 1 $2
    StrCmp $3 '' +2
      StrCmp $3 '.' 0 -3
    StrCpy $5 $1 $2
    IntOp $2 $2 + 1
    StrCpy $1 $1 '' $2

    StrCmp $4$5 '' equal${UMUI_UNIQUEIDVER}

      StrCpy $6 -1
      IntOp $6 $6 + 1
      StrCpy $3 $4 1 $6
      StrCmp $3 '0' -2
        StrCmp $3 '' 0 +2
          StrCpy $4 0

        StrCpy $7 -1
        IntOp $7 $7 + 1
        StrCpy $3 $5 1 $7
        StrCmp $3 '0' -2
          StrCmp $3 '' 0 +2
            StrCpy $5 0

            StrCmp $4 0 0 +2
              StrCmp $5 0 begin${UMUI_UNIQUEIDVER} newer2${UMUI_UNIQUEIDVER}
            StrCmp $5 0 newer1${UMUI_UNIQUEIDVER}
              IntCmp $6 $7 0 newer1${UMUI_UNIQUEIDVER} newer2${UMUI_UNIQUEIDVER}

                StrCpy $4 '1$4'
                StrCpy $5 '1$5'
                IntCmp $4 $5 begin${UMUI_UNIQUEIDVER} newer2${UMUI_UNIQUEIDVER} newer1${UMUI_UNIQUEIDVER}

  equal${UMUI_UNIQUEIDVER}:
    StrCpy $0 0
    Goto end${UMUI_UNIQUEIDVER}
  newer1${UMUI_UNIQUEIDVER}:
    StrCpy $0 1
    Goto end${UMUI_UNIQUEIDVER}
  newer2${UMUI_UNIQUEIDVER}:
    StrCpy $0 2

  end${UMUI_UNIQUEIDVER}:

  Pop $7
  Pop $6
  Pop $5
  Pop $4
  Pop $3
  Pop $2
  Pop $1
  Exch $0

  !undef UMUI_UNIQUEIDVER

  !verbose pop

!macroend


;Based on the VersionConvert v1.0 of Instructor
;Thanks Afrow UK (Based on his Function "CharIndexReplace")
;Usage:
;!insertmacro UMUI_VERSIONCONVERT VER
;Pop $Var ;get the coverted version
!macro UMUI_VERSIONCONVERT VER

  !verbose push
  !verbose ${MUI_VERBOSE}

  !define UMUI_UNIQUEIDVER ${__LINE__}

  Push $0    ; Converted string
  Push $1    ; Input version
  Push $2    ; CharactersList
  Push $3    ; Input String Indices
  Push $4    ; Char extracted from input
  Push $5    ; LastCharType
  Push $6
  Push $7

  StrCpy $0 ""

  StrCpy $1 "${VER}"

  StrCpy $2 "abcdefghijklmnopqrstuvwxyz#"

  IntOp $3 0 - 1

  StrCpy $5 "dot"

  loop${UMUI_UNIQUEIDVER}:
    IntOp $3 $3 + 1

    StrCpy $4 $1 1 $3
    StrCmp $4 '' endcheck${UMUI_UNIQUEIDVER}
      StrCmp $4 '.' dot${UMUI_UNIQUEIDVER}
        StrCmp $4 '-' dot${UMUI_UNIQUEIDVER}
          StrCmp $4 '_' dot${UMUI_UNIQUEIDVER}
            StrCmp $4 ' ' dot${UMUI_UNIQUEIDVER}
              StrCmp $4 '0' digit${UMUI_UNIQUEIDVER}
                IntCmp $4 '0' letter${UMUI_UNIQUEIDVER} letter${UMUI_UNIQUEIDVER} digit${UMUI_UNIQUEIDVER}

  dot${UMUI_UNIQUEIDVER}:
    StrCmp $5 "dot" loop${UMUI_UNIQUEIDVER} 0
      StrCpy $0 "$0."
      StrCpy $5 "dot"
      Goto loop${UMUI_UNIQUEIDVER}

  digit${UMUI_UNIQUEIDVER}:
    StrCpy $0 "$0$4"
    StrCpy $5 "digit"
    Goto loop${UMUI_UNIQUEIDVER}

  letter${UMUI_UNIQUEIDVER}:
    StrCmp $5 "digit" 0 +2
      StrCpy $0 "$0."

    StrCpy $5 "letter"

    IntOp $6 0 - 1

    letterloop${UMUI_UNIQUEIDVER}:
      IntOp $6 $6 + 1
      StrCpy $7 $2 1 $6
      StrCmp $7 '#' 0 +3
        StrCpy $0 "$099"
        Goto loop${UMUI_UNIQUEIDVER}

    StrCmp $4 $7 0 letterloop${UMUI_UNIQUEIDVER}
      IntCmp $6 9 0 0 +2
        StrCpy $0 "$00"

      StrCpy $0 "$0$6"

    Goto loop${UMUI_UNIQUEIDVER}

  endcheck${UMUI_UNIQUEIDVER}:
    StrCpy $7 $0 1 -1
    StrCmp $7 '.' 0 end${UMUI_UNIQUEIDVER}
      StrLen $6 $0
      IntOp $6 $6 - 1
      StrCpy $0 $0 $6
      Goto endcheck${UMUI_UNIQUEIDVER}

  end${UMUI_UNIQUEIDVER}:

  Pop $7
  Pop $6
  Pop $5
  Pop $4
  Pop $3
  Pop $2
  Pop $1
  Exch $0

  !undef UMUI_UNIQUEIDVER

  !verbose pop

!macroend



!macro UMUI_GETPARENTFOLDER FULPATH

  !verbose push
  !verbose ${MUI_VERBOSE}

  Push $0
  Push $1

  StrCpy $0 "${FULPATH}"

  StrCpy $1 $0 1 -1
  StrCmp $1 '\' +3
    StrCpy $0 $0 -1
    Goto -3

  StrCpy $1 $0 1 -1

  Pop $1
  Exch $0

  !verbose pop

!macroend


!macro UMUI_WELCOMEFINISHABORTPAGE_INIT UNINSTALLER

  !ifdef MUI_${UNINSTALLER}WELCOMEPAGE | MUI_${UNINSTALLER}FINISHPAGE | UMUI_${UNINSTALLER}ABORTPAGE | UMUI_${UNINSTALLER}MULTILANGUAGEPAGE

    !ifdef UMUI_USE_${UNINSTALLER}ALTERNATE_PAGE
       !insertmacro INSTALLOPTIONS_EXTRACT_AS "${UMUI_${UNINSTALLER}ALTERNATEWELCOMEFINISHABORTPAGE_INI}" "ioSpecial.ini"
    !else
       !insertmacro INSTALLOPTIONS_EXTRACT_AS "${UMUI_${UNINSTALLER}WELCOMEFINISHABORTPAGE_INI}" "ioSpecial.ini"
    !endif

    !ifdef UMUI_WELCOMEFINISHABORTPAGE_USE_IMAGE
      File "/oname=$PLUGINSDIR\modern-wizard.bmp" "${MUI_${UNINSTALLER}WELCOMEFINISHPAGE_BITMAP}"

      !insertmacro INSTALLOPTIONS_WRITE "ioSpecial.ini" "Field 1" "Text" "$PLUGINSDIR\modern-wizard.bmp"

      !ifdef MUI_${UNINSTALLER}WELCOMEFINISHPAGE_BITMAP_NOSTRETCH
        !insertmacro INSTALLOPTIONS_WRITE "ioSpecial.ini" "Field 1" "Flags" ""
      !endif

    !endif

  !endif

!macroend

!macro MUI_HEADERIMAGE_INIT UNINSTALLER

  !ifdef MUI_HEADERIMAGE

    InitPluginsDir

    !ifdef MUI_HEADERIMAGE_${UNINSTALLER}BITMAP_RTL

    StrCmp $(^RTL) 0 mui.headerimageinit_nortl

      File "/oname=$PLUGINSDIR\modern-header.bmp" "${MUI_HEADERIMAGE_${UNINSTALLER}BITMAP_RTL}"

      !ifndef MUI_HEADERIMAGE_${UNINSTALLER}BITMAP_RTL_NOSTRETCH
        SetBrandingImage /IMGID=1046 /RESIZETOFIT "$PLUGINSDIR\modern-header.bmp"
      !else
        SetBrandingImage /IMGID=1046 "$PLUGINSDIR\modern-header.bmp"
      !endif

      Goto mui.headerimageinit_done

      mui.headerimageinit_nortl:

    !endif

      File "/oname=$PLUGINSDIR\modern-header.bmp" "${MUI_HEADERIMAGE_${UNINSTALLER}BITMAP}"

      !ifndef MUI_HEADERIMAGE_${UNINSTALLER}BITMAP_NOSTRETCH
        SetBrandingImage /IMGID=1046 /RESIZETOFIT "$PLUGINSDIR\modern-header.bmp"
      !else
        SetBrandingImage /IMGID=1046 "$PLUGINSDIR\modern-header.bmp"
      !endif

    !ifdef MUI_HEADERIMAGE_${UNINSTALLER}BITMAP_RTL

    mui.headerimageinit_done:

    !endif

  !endif

!macroend

;--------------------------------
;INTERFACE - FUNCTIONS


!macro UMUI_VERSION_SET

  !ifdef UMUI_VERBUILD_REGISTRY_VALUENAME
    !ifndef UMUI_VERBUILD
      !warning "UMUI_VERBUILD need to be defined with UMUI_VERBUILD_REGISTRY_VALUENAME. Ignored"
      !undef UMUI_VERBUILD_REGISTRY_VALUENAME
    !endif
  !endif
  !ifdef UMUI_VERSION_REGISTRY_VALUENAME
    !ifndef UMUI_VERSION
      !warning "UMUI_VERSION need to be defined with UMUI_VERSION_REGISTRY_VALUENAME. Ignored"
      !undef UMUI_VERSION_REGISTRY_VALUENAME
    !endif
  !endif


  !ifdef UMUI_VERBUILD_REGISTRY_VALUENAME

    !ifndef UMUI_VERBUILD_REGISTRY_ROOT
      !ifdef UMUI_PARAMS_REGISTRY_ROOT
        !define UMUI_VERBUILD_REGISTRY_ROOT "${UMUI_PARAMS_REGISTRY_ROOT}"
      !else
        !error "For UMUI_VERBUILD_REGISTRY_VALUENAME, the UMUI_VERBUILD_REGISTRY_ROOT & UMUI_VERBUILD_REGISTRY_KEY parameters or else the UMUI_PARAMS_REGISTRY_ROOT & UMUI_PARAMS_REGISTRY_KEY global parameters must be defined."
      !endif
    !endif
    !ifndef UMUI_VERBUILD_REGISTRY_KEY
      !ifdef UMUI_PARAMS_REGISTRY_KEY
        !define UMUI_VERBUILD_REGISTRY_KEY "${UMUI_PARAMS_REGISTRY_KEY}"
      !else
        !error "For UMUI_VERBUILD_REGISTRY_VALUENAME, the UMUI_VERBUILD_REGISTRY_ROOT & UMUI_VERBUILD_REGISTRY_KEY parameters or else the UMUI_PARAMS_REGISTRY_ROOT & UMUI_PARAMS_REGISTRY_KEY global parameters must be defined."
      !endif
    !endif

    ReadRegStr $MUI_TEMP1 ${UMUI_VERBUILD_REGISTRY_ROOT} "${UMUI_VERBUILD_REGISTRY_KEY}" "${UMUI_VERBUILD_REGISTRY_VALUENAME}"

    StrCmp $MUI_TEMP1 "" endv 0

      ClearErrors

      StrCmp $MUI_TEMP1 "${UMUI_VERBUILD}" 0 diff
        !insertmacro UMUI_SET_INSTALLFLAG ${UMUI_SAMEVERSION}
        !insertmacro UMUI_UNSET_INSTALLFLAG ${UMUI_DIFFVERSION}
        Goto endv
      diff:
        !insertmacro UMUI_SET_INSTALLFLAG ${UMUI_DIFFVERSION}
        !insertmacro UMUI_UNSET_INSTALLFLAG ${UMUI_SAMEVERSION}

    endv:
    ClearErrors

    !insertmacro UMUI_ADDPARAMTOSAVETOREGISTRYKEY ${UMUI_VERBUILD_REGISTRY_ROOT} "${UMUI_VERBUILD_REGISTRY_KEY}" "${UMUI_VERBUILD_REGISTRY_VALUENAME}" "${UMUI_VERBUILD}"

  !endif

  !ifdef UMUI_VERSION_REGISTRY_VALUENAME & UMUI_VERSION

    !ifndef UMUI_VERSION_REGISTRY_ROOT
      !ifdef UMUI_PARAMS_REGISTRY_ROOT
        !define UMUI_VERSION_REGISTRY_ROOT "${UMUI_PARAMS_REGISTRY_ROOT}"
      !else
        !error "For UMUI_VERSION_REGISTRY_VALUENAME, the UMUI_VERSION_REGISTRY_ROOT & UMUI_VERSION_REGISTRY_KEY parameters or else the UMUI_PARAMS_REGISTRY_ROOT & UMUI_PARAMS_REGISTRY_KEY global parameters must be defined."
      !endif
    !endif
    !ifndef UMUI_VERSION_REGISTRY_KEY
      !ifdef UMUI_PARAMS_REGISTRY_KEY
        !define UMUI_VERSION_REGISTRY_KEY "${UMUI_PARAMS_REGISTRY_KEY}"
      !else
        !error "For UMUI_VERSION_REGISTRY_VALUENAME, the UMUI_VERSION_REGISTRY_ROOT & UMUI_VERSION_REGISTRY_KEY parameters or else the UMUI_PARAMS_REGISTRY_ROOT & UMUI_PARAMS_REGISTRY_KEY global parameters must be defined."
      !endif
    !endif

    !insertmacro UMUI_ADDPARAMTOSAVETOREGISTRYKEY ${UMUI_VERSION_REGISTRY_ROOT} "${UMUI_VERSION_REGISTRY_KEY}" "${UMUI_VERSION_REGISTRY_VALUENAME}" "${UMUI_VERSION}"
  !endif

!macroend



!macro UMUI_PATH_SAVE

  !ifdef UMUI_UNINSTALLPATH_REGISTRY_VALUENAME
    !ifndef UMUI_UNINSTALL_FULLPATH
      !warning "UMUI_UNINSTALL_FULLPATH need to be defined with UMUI_UNINSTALLPATH_REGISTRY_VALUENAME. Ignored"
      !undef UMUI_UNINSTALLPATH_REGISTRY_VALUENAME
    !endif

    !ifndef UMUI_UNINSTALLPATH_REGISTRY_ROOT
      !ifdef UMUI_PARAMS_REGISTRY_ROOT
        !define UMUI_UNINSTALLPATH_REGISTRY_ROOT "${UMUI_PARAMS_REGISTRY_ROOT}"
      !else
        !error "For UMUI_UNINSTALLPATH_REGISTRY_VALUENAME, the UMUI_UNINSTALLPATH_REGISTRY_ROOT & UMUI_UNINSTALLPATH_REGISTRY_KEY parameters or else the UMUI_PARAMS_REGISTRY_ROOT & UMUI_PARAMS_REGISTRY_KEY global parameters must be defined."
      !endif
    !endif
    !ifndef UMUI_UNINSTALLPATH_REGISTRY_KEY
      !ifdef UMUI_PARAMS_REGISTRY_KEY
        !define UMUI_UNINSTALLPATH_REGISTRY_KEY "${UMUI_PARAMS_REGISTRY_KEY}"
      !else
        !error "For UMUI_UNINSTALLPATH_REGISTRY_VALUENAME, the UMUI_UNINSTALLPATH_REGISTRY_ROOT & UMUI_UNINSTALLPATH_REGISTRY_KEY parameters or else the UMUI_PARAMS_REGISTRY_ROOT & UMUI_PARAMS_REGISTRY_KEY global parameters must be defined."
      !endif
    !endif

    !ifndef UMUI_INSTALLERFULLPATH_REGISTRY_ROOT
      !ifdef UMUI_PARAMS_REGISTRY_ROOT
        !define UMUI_INSTALLERFULLPATH_REGISTRY_ROOT "${UMUI_PARAMS_REGISTRY_ROOT}"
      !else
        !error "For UMUI_INSTALLERFULLPATH_REGISTRY_VALUENAME, the UMUI_INSTALLERFULLPATH_REGISTRY_ROOT & UMUI_INSTALLERFULLPATH_REGISTRY_KEY parameters or else the UMUI_PARAMS_REGISTRY_ROOT & UMUI_PARAMS_REGISTRY_KEY global parameters must be defined."
      !endif
    !endif
    !ifndef UMUI_INSTALLERFULLPATH_REGISTRY_KEY
      !ifdef UMUI_PARAMS_REGISTRY_KEY
        !define UMUI_INSTALLERFULLPATH_REGISTRY_KEY "${UMUI_PARAMS_REGISTRY_KEY}"
      !else
        !error "For UMUI_INSTALLERFULLPATH_REGISTRY_VALUENAME, the UMUI_INSTALLERFULLPATH_REGISTRY_ROOT & UMUI_INSTALLERFULLPATH_REGISTRY_KEY parameters or else the UMUI_PARAMS_REGISTRY_ROOT & UMUI_PARAMS_REGISTRY_KEY global parameters must be defined."
      !endif
    !endif

  !endif

  !ifdef UMUI_UNINSTALLPATH_REGISTRY_VALUENAME & UMUI_UNINSTALL_FULLPATH
    !insertmacro UMUI_ADDPARAMTOSAVETOREGISTRYKEY ${UMUI_UNINSTALLPATH_REGISTRY_ROOT} "${UMUI_UNINSTALLPATH_REGISTRY_KEY}" "${UMUI_UNINSTALLPATH_REGISTRY_VALUENAME}" "${UMUI_UNINSTALL_FULLPATH}"
  !endif

  !ifdef UMUI_INSTALLERFULLPATH_REGISTRY_VALUENAME
    !ifdef UMUI_INSTALL_FULLPATH
      !insertmacro UMUI_ADDPARAMTOSAVETOREGISTRYKEY ${UMUI_INSTALLERFULLPATH_REGISTRY_ROOT} "${UMUI_INSTALLERFULLPATH_REGISTRY_KEY}" "${UMUI_INSTALLERFULLPATH_REGISTRY_VALUENAME}" "${UMUI_INSTALL_FULLPATH}"
    !else
      !insertmacro UMUI_ADDPARAMTOSAVETOREGISTRYKEY ${UMUI_INSTALLERFULLPATH_REGISTRY_ROOT} "${UMUI_INSTALLERFULLPATH_REGISTRY_KEY}" "${UMUI_INSTALLERFULLPATH_REGISTRY_VALUENAME}" $EXEPATH
    !endif
  !endif

!macroend



!macro UMUI_MAINTENANCE_PARAMETERS_GET

  ClearErrors
  !insertmacro UMUI_PARAMETERISSET "/remove"
  Pop $MUI_TEMP1
  IfErrors noremove 0
    !insertmacro UMUI_SET_INSTALLFLAG ${UMUI_REMOVE}
    !insertmacro UMUI_SET_INSTALLFLAG ${UMUI_ABORTFIRSTTIME}
    !insertmacro UMUI_UNSET_INSTALLFLAG ${UMUI_HIDEBACKBUTTON}
    Goto endsearch

  noremove:
  !insertmacro UMUI_PARAMETERISSET "/modify"
  Pop $MUI_TEMP1
  IfErrors nomodify 0
    !insertmacro UMUI_SET_INSTALLFLAG ${UMUI_MODIFY}
    !insertmacro UMUI_SET_INSTALLFLAG ${UMUI_ABORTFIRSTTIME}
    !insertmacro UMUI_UNSET_INSTALLFLAG ${UMUI_HIDEBACKBUTTON}
    Goto endsearch

  nomodify:
  !insertmacro UMUI_PARAMETERISSET "/repair"
  Pop $MUI_TEMP1
  IfErrors norepair 0
    !insertmacro UMUI_SET_INSTALLFLAG ${UMUI_REPAIR}
    !insertmacro UMUI_SET_INSTALLFLAG ${UMUI_ABORTFIRSTTIME}
    !insertmacro UMUI_UNSET_INSTALLFLAG ${UMUI_HIDEBACKBUTTON}
    Goto endsearch

  norepair:
  !insertmacro UMUI_PARAMETERISSET "/continue"
  Pop $MUI_TEMP1
  IfErrors endsearch 0
    !insertmacro UMUI_SET_INSTALLFLAG ${UMUI_CONTINUE_SETUP}
    !insertmacro UMUI_SET_INSTALLFLAG ${UMUI_ABORTFIRSTTIME}
    !insertmacro UMUI_UNSET_INSTALLFLAG ${UMUI_HIDEBACKBUTTON}

  endsearch:
  ClearErrors

!macroend


!macro MUI_FUNCTION_GUIINIT

  Function .onGUIInit

    !insertmacro MUI_GUIINIT

    !ifdef MUI_CUSTOMFUNCTION_GUIINIT
      Call "${MUI_CUSTOMFUNCTION_GUIINIT}"
    !endif

    !ifdef UMUI_BGSKIN | UMUI_USE_CUSTOMBG
      !insertmacro UMUI_BG
    !endif

    ;Only if not already set in the .onInit function
    StrCmp $UMUI_INSTALLFLAG "" 0 +2
      StrCpy $UMUI_INSTALLFLAG 0

    !insertmacro UMUI_VERSION_SET

    !insertmacro UMUI_SET_INSTALLFLAG ${UMUI_HIDEBACKBUTTON}

    !insertmacro UMUI_MAINTENANCE_PARAMETERS_GET

  FunctionEnd

!ifdef UMUI_CUSTOMFUNCTION_GUIEND | UMUI_BGSKIN | UMUI_USE_CUSTOMBG

  Function .onGUIEnd

    !ifdef UMUI_CUSTOMFUNCTION_GUIEND
      Call "${UMUI_CUSTOMFUNCTION_GUIEND}"
    !endif

    !ifdef UMUI_BGSKIN | UMUI_USE_CUSTOMBG
      !insertmacro UMUI_BG_Destroy
    !endif

    !insertmacro UMUI_DELETE_PLUGINDIR

  FunctionEnd

!endif

!macroend

!macro MUI_FUNCTION_DESCRIPTION_BEGIN

  !verbose push
  !verbose ${MUI_VERBOSE}

  !ifndef MUI_VAR_TEXT
    Var MUI_TEXT
    !define MUI_VAR_TEXT
  !endif

;  !define /redef MUI_PAGE_UNINSTALLER_PREFIX ""
  Function .onMouseOverSection
    !insertmacro MUI_DESCRIPTION_BEGIN

  !verbose pop

!macroend

!macro MUI_FUNCTION_DESCRIPTION_END

  !verbose push
  !verbose ${MUI_VERBOSE}

    !insertmacro MUI_DESCRIPTION_END
    !ifdef MUI_CUSTOMFUNCTION_ONMOUSEOVERSECTION
      Call "${MUI_CUSTOMFUNCTION_ONMOUSEOVERSECTION}"
    !endif
  FunctionEnd
;  !undef MUI_PAGE_UNINSTALLER_PREFIX

  !verbose pop

!macroend

!macro MUI_UNFUNCTION_DESCRIPTION_BEGIN

  !verbose push
  !verbose ${MUI_VERBOSE}

;  !define /redef MUI_PAGE_UNINSTALLER_PREFIX "UN"
  Function un.onMouseOverSection
    !insertmacro MUI_DESCRIPTION_BEGIN

  !verbose pop

!macroend

!macro MUI_UNFUNCTION_DESCRIPTION_END

  !verbose push
  !verbose ${MUI_VERBOSE}

    !insertmacro MUI_DESCRIPTION_END
    !ifdef MUI_CUSTOMFUNCTION_UNONMOUSEOVERSECTION
      Call "${MUI_CUSTOMFUNCTION_UNONMOUSEOVERSECTION}"
    !endif
  FunctionEnd
;  !undef MUI_PAGE_UNINSTALLER_PREFIX

  !verbose pop

!macroend

!macro MUI_FUNCTION_ABORTWARNING

  Function .onUserAbort
    !ifdef MUI_ABORTWARNING
      !insertmacro MUI_ABORTWARNING
    !endif

    !ifdef MUI_CUSTOMFUNCTION_ABORT
      Call "${MUI_CUSTOMFUNCTION_ABORT}"
    !endif

    !ifdef UMUI_ABORTPAGE
      !insertmacro UMUI_SET_INSTALLFLAG ${UMUI_CANCELLED}
      !ifdef UMUI_USE_INSTALLOPTIONSEX
        !insertmacro UMUI_INSTALLOPTIONSEX_SKIPVALIDATION
      !endif
      SendMessage $HWNDPARENT "0x408" "1" ""
      Abort
    !else
      !insertmacro UMUI_DELETE_PLUGINDIR
    !endif
  FunctionEnd

!macroend

!macro MUI_FUNCTION_UNABORTWARNING

  Function un.onUserAbort
    !ifdef MUI_UNABORTWARNING
      !insertmacro MUI_UNABORTWARNING
    !endif

    !ifdef MUI_CUSTOMFUNCTION_UNABORT
      Call "${MUI_CUSTOMFUNCTION_UNABORT}"
    !endif

    !ifdef UMUI_UNABORTPAGE
      !insertmacro UMUI_SET_INSTALLFLAG ${UMUI_CANCELLED}
      !ifdef UMUI_USE_INSTALLOPTIONSEX
        !insertmacro UMUI_INSTALLOPTIONSEX_SKIPVALIDATION
      !endif
      SendMessage $HWNDPARENT "0x408" "1" ""
      Abort
    !else
      !insertmacro UMUI_DELETE_PLUGINDIR
    !endif
  FunctionEnd

!macroend

!macro MUI_UNFUNCTION_GUIINIT

  Function un.onGUIInit

    !insertmacro MUI_UNGUIINIT

    !ifdef MUI_CUSTOMFUNCTION_UNGUIINIT
      Call "${MUI_CUSTOMFUNCTION_UNGUIINIT}"
    !endif

    !ifdef UMUI_BGSKIN | UMUI_USE_CUSTOMBG
      !insertmacro UMUI_BG
    !endif

    ;Only if not already set in the un.onInit function
    StrCmp $UMUI_INSTALLFLAG "" 0 +2
      StrCpy $UMUI_INSTALLFLAG 0

    !insertmacro UMUI_SET_INSTALLFLAG ${UMUI_SAMEVERSION}
    !insertmacro UMUI_UNSET_INSTALLFLAG ${UMUI_DIFFVERSION}
    !insertmacro UMUI_MAINTENANCE_PARAMETERS_GET

    !insertmacro UMUI_SET_INSTALLFLAG ${UMUI_HIDEBACKBUTTON}

  FunctionEnd


  !ifdef UMUI_CUSTOMFUNCTION_UNGUIEND | UMUI_BGSKIN | UMUI_USE_CUSTOMBG

    Function un.onGUIEnd

      !ifdef UMUI_CUSTOMFUNCTION_UNGUIEND
        Call "${UMUI_CUSTOMFUNCTION_UNGUIEND}"
      !endif

      !ifdef UMUI_BGSKIN | UMUI_USE_CUSTOMBG
        !insertmacro UMUI_BG_Destroy
      !endif

      !insertmacro UMUI_DELETE_PLUGINDIR

    FunctionEnd

  !endif

!macroend


!macro UMUI_UNPAGE_LEFTMESSAGEBOX A B C

  !insertmacro UMUI_PAGE_LEFTMESSAGEBOX "${A}" "${B}" "${C}"

!macroend

!macro UMUI_PAGE_LEFTMESSAGEBOX A B C

  !warning "The UMUI_PAGE_LEFTMESSAGEBOX and UMUI_UNPAGE_LEFTMESSAGEBOX macros were removed since Ultra-Modern UI 1.00 beta 2."
  !insertmacro MUI_UNSET UMUI_LEFTMESSAGEBOX_VAR
  !insertmacro MUI_UNSET UMUI_LEFTMESSAGEBOX_LEFTFUNC

!macroend

!macro UMUI_LEFT_TEXTE A B

  !warning "The UMUI_LEFT_TEXTE macro was removed since Ultra-Modern UI 1.00 beta 2."

!macroend

!macro UMUI_LEFT_SETTIME A

  !warning "The UMUI_LEFT_SETTIME macro was removed since Ultra-Modern UI 1.00 beta 2."

!macroend

; Workaround for unkinning button after MessageBox validated
!macro UMUI_FIX_BUTTONS_SKIN

  !ifdef UMUI_${MUI_PAGE_UNINSTALLER_PREFIX}BUTTONIMAGE_BMP
    SendMessage $HWNDPARENT ${WM_MENUDRAG} 0 0 ; Do this to force reskin
  !endif

!macroend

;--------------------------------
;START MENU FOLDER

!macro MUI_STARTMENU_GETFOLDER ID VAR

  !verbose push
  !verbose ${MUI_VERBOSE}

  !ifdef MUI_STARTMENUPAGE_${ID}_REGISTRY_VALUENAME

    ReadRegStr $MUI_TEMP1 "${MUI_STARTMENUPAGE_${ID}_REGISTRY_ROOT}" "${MUI_STARTMENUPAGE_${ID}_REGISTRY_KEY}" "${MUI_STARTMENUPAGE_${ID}_REGISTRY_VALUENAME}"

    StrCmp $MUI_TEMP1 "" +3
      StrCpy "${VAR}" $MUI_TEMP1
      Goto +2

    StrCpy "${VAR}" "${MUI_STARTMENUPAGE_${ID}_DEFAULTFOLDER}"

  !else

    StrCpy "${VAR}" "${MUI_STARTMENUPAGE_${ID}_DEFAULTFOLDER}"

  !endif

  !verbose pop

!macroend

!macro MUI_STARTMENU_WRITE_BEGIN ID

  !verbose push
  !verbose ${MUI_VERBOSE}

  !define MUI_STARTMENUPAGE_CURRENT_ID "${ID}"

  StrCpy $MUI_TEMP1 "${MUI_STARTMENUPAGE_${MUI_STARTMENUPAGE_CURRENT_ID}_VARIABLE}" 1
  StrCmp $MUI_TEMP1 ">" mui.startmenu_write_${MUI_STARTMENUPAGE_CURRENT_ID}_done

    StrCmp "${MUI_STARTMENUPAGE_${MUI_STARTMENUPAGE_CURRENT_ID}_VARIABLE}" "" 0 mui.startmenu_writebegin_${MUI_STARTMENUPAGE_CURRENT_ID}_notempty

      !insertmacro MUI_STARTMENU_GETFOLDER "${MUI_STARTMENUPAGE_CURRENT_ID}" "${MUI_STARTMENUPAGE_${MUI_STARTMENUPAGE_CURRENT_ID}_VARIABLE}"

  mui.startmenu_writebegin_${MUI_STARTMENUPAGE_CURRENT_ID}_notempty:

  !verbose pop

!macroend

!macro MUI_STARTMENU_WRITE_END

  !verbose push
  !verbose ${MUI_VERBOSE}

  mui.startmenu_write_${MUI_STARTMENUPAGE_CURRENT_ID}_done:

  !undef MUI_STARTMENUPAGE_CURRENT_ID

  !verbose pop

!macroend

;--------------------------------
;PAGES

!macro MUI_PAGE_INIT

  !insertmacro MUI_INTERFACE

  !define /IfNDef MUI_PAGE_UNINSTALLER_PREFIX ""
  !define /IfNDef MUI_PAGE_UNINSTALLER_FUNCPREFIX ""

  !insertmacro MUI_UNSET MUI_UNIQUEID

  !define MUI_UNIQUEID ${__LINE__}

!macroend

!macro MUI_UNPAGE_INIT

  !define /IfNDef MUI_UNINSTALLER

  !define MUI_PAGE_UNINSTALLER

  !insertmacro MUI_UNSET MUI_PAGE_UNINSTALLER_PREFIX
  !insertmacro MUI_UNSET MUI_PAGE_UNINSTALLER_FUNCPREFIX

  !define MUI_PAGE_UNINSTALLER_PREFIX "UN"
  !define MUI_PAGE_UNINSTALLER_FUNCPREFIX "un."

!macroend

!macro MUI_UNPAGE_END

  !undef MUI_PAGE_UNINSTALLER
  !undef MUI_PAGE_UNINSTALLER_PREFIX
  !undef MUI_PAGE_UNINSTALLER_FUNCPREFIX

!macroend

!macro MUI_PAGE_WELCOME

  !verbose push
  !verbose ${MUI_VERBOSE}

  !insertmacro MUI_PAGE_INIT

  !define /IfNDef MUI_${MUI_PAGE_UNINSTALLER_PREFIX}WELCOMEPAGE

  !insertmacro MUI_DEFAULT_IOCONVERT MUI_WELCOMEPAGE_TITLE "$(MUI_${MUI_PAGE_UNINSTALLER_PREFIX}TEXT_WELCOME_INFO_TITLE)"

  !ifdef MUI_PAGE_UNINSTALLER
    !insertmacro MUI_DEFAULT_IOCONVERT MUI_WELCOMEPAGE_TEXT "$(MUI_UNTEXT_WELCOME_INFO_TEXT)"
  !else
    !ifdef UMUI_WELCOMEPAGE_ALTERNATIVETEXT
      !insertmacro MUI_DEFAULT_IOCONVERT MUI_WELCOMEPAGE_TEXT "$(UMUI_TEXT_WELCOME_ALTERNATIVEINFO_TEXT)"
    !else
      !insertmacro MUI_DEFAULT_IOCONVERT MUI_WELCOMEPAGE_TEXT "$(MUI_TEXT_WELCOME_INFO_TEXT)"
    !endif
  !endif

  !ifndef MUI_VAR_HWND
    Var MUI_HWND
    !define MUI_VAR_HWND
  !endif

  PageEx ${MUI_PAGE_UNINSTALLER_FUNCPREFIX}custom

    PageCallbacks ${MUI_PAGE_UNINSTALLER_FUNCPREFIX}mui.WelcomePre_${MUI_UNIQUEID} ${MUI_PAGE_UNINSTALLER_FUNCPREFIX}mui.WelcomeLeave_${MUI_UNIQUEID}

  PageExEnd

  !insertmacro MUI_FUNCTION_WELCOMEPAGE ${MUI_PAGE_UNINSTALLER_FUNCPREFIX}mui.WelcomePre_${MUI_UNIQUEID} ${MUI_PAGE_UNINSTALLER_FUNCPREFIX}mui.WelcomeLeave_${MUI_UNIQUEID}

  !insertmacro MUI_UNSET MUI_WELCOMEPAGE_TITLE
  !insertmacro MUI_UNSET MUI_WELCOMEPAGE_TITLE_3LINES
  !insertmacro MUI_UNSET MUI_WELCOMEPAGE_TEXT
  !insertmacro MUI_UNSET UMUI_WELCOMEPAGE_ALTERNATIVETEXT

  !verbose pop

!macroend

!macro MUI_PAGE_LICENSE LICENSEDATA

  !verbose push
  !verbose ${MUI_VERBOSE}

  !insertmacro MUI_PAGE_INIT

  !define /IfNDef MUI_${MUI_PAGE_UNINSTALLER_PREFIX}LICENSEPAGE

  !define /IfNDef MUI_LICENSEPAGE_TEXT_TOP "$(MUI_INNERTEXT_LICENSE_TOP)"
  !define /IfNDef MUI_LICENSEPAGE_BUTTON ""
  !define /IfNDef MUI_LICENSEPAGE_CHECKBOX_TEXT ""
  !define /IfNDef MUI_LICENSEPAGE_RADIOBUTTONS_TEXT_ACCEPT ""
  !define /IfNDef MUI_LICENSEPAGE_RADIOBUTTONS_TEXT_DECLINE ""

  PageEx ${MUI_PAGE_UNINSTALLER_FUNCPREFIX}license

    PageCallbacks ${MUI_PAGE_UNINSTALLER_FUNCPREFIX}mui.LicensePre_${MUI_UNIQUEID} ${MUI_PAGE_UNINSTALLER_FUNCPREFIX}mui.LicenseShow_${MUI_UNIQUEID} ${MUI_PAGE_UNINSTALLER_FUNCPREFIX}mui.LicenseLeave_${MUI_UNIQUEID}

    Caption " "

    LicenseData "${LICENSEDATA}"

    !ifndef MUI_LICENSEPAGE_TEXT_BOTTOM
      !ifndef MUI_LICENSEPAGE_CHECKBOX & MUI_LICENSEPAGE_RADIOBUTTONS
        LicenseText "$(MUI_${MUI_PAGE_UNINSTALLER_PREFIX}INNERTEXT_LICENSE_BOTTOM)" "${MUI_LICENSEPAGE_BUTTON}"
      !else ifdef MUI_LICENSEPAGE_CHECKBOX
        LicenseText "$(MUI_${MUI_PAGE_UNINSTALLER_PREFIX}INNERTEXT_LICENSE_BOTTOM_CHECKBOX)" "${MUI_LICENSEPAGE_BUTTON}"
      !else
        LicenseText "$(MUI_${MUI_PAGE_UNINSTALLER_PREFIX}INNERTEXT_LICENSE_BOTTOM_RADIOBUTTONS)" "${MUI_LICENSEPAGE_BUTTON}"
      !endif
    !else
      LicenseText "${MUI_LICENSEPAGE_TEXT_BOTTOM}" "${MUI_LICENSEPAGE_BUTTON}"
    !endif

    !ifdef MUI_LICENSEPAGE_CHECKBOX
      LicenseForceSelection checkbox "${MUI_LICENSEPAGE_CHECKBOX_TEXT}"
    !else ifdef MUI_LICENSEPAGE_RADIOBUTTONS
      LicenseForceSelection radiobuttons "${MUI_LICENSEPAGE_RADIOBUTTONS_TEXT_ACCEPT}" "${MUI_LICENSEPAGE_RADIOBUTTONS_TEXT_DECLINE}"
    !endif

  PageExEnd

  !insertmacro MUI_FUNCTION_LICENSEPAGE ${MUI_PAGE_UNINSTALLER_FUNCPREFIX}mui.LicensePre_${MUI_UNIQUEID} ${MUI_PAGE_UNINSTALLER_FUNCPREFIX}mui.LicenseShow_${MUI_UNIQUEID} ${MUI_PAGE_UNINSTALLER_FUNCPREFIX}mui.LicenseLeave_${MUI_UNIQUEID}

  !insertmacro MUI_UNSET MUI_LICENSEPAGE_TEXT_TOP
  !insertmacro MUI_UNSET MUI_LICENSEPAGE_TEXT_BOTTOM
  !insertmacro MUI_UNSET MUI_LICENSEPAGE_BUTTON
  !insertmacro MUI_UNSET MUI_LICENSEPAGE_CHECKBOX
    !insertmacro MUI_UNSET MUI_LICENSEPAGE_CHECKBOX_TEXT
  !insertmacro MUI_UNSET MUI_LICENSEPAGE_RADIOBUTTONS
    !insertmacro MUI_UNSET MUI_LICENSEPAGE_CHECKBOX_TEXT_ACCEPT
    !insertmacro MUI_UNSET MUI_LICENSEPAGE_CHECKBOX_TEXT_DECLINE

  !verbose pop

!macroend

!macro MUI_PAGE_COMPONENTS

  !verbose push
  !verbose ${MUI_VERBOSE}

  !insertmacro MUI_PAGE_INIT

  !define /IfNDef MUI_${MUI_PAGE_UNINSTALLER_PREFIX}COMPONENTSPAGE

  !define /IfNDef MUI_COMPONENTSPAGE_TEXT_TOP ""
  !define /IfNDef MUI_COMPONENTSPAGE_TEXT_COMPLIST ""
  !define /IfNDef MUI_COMPONENTSPAGE_TEXT_INSTTYPE ""
  !define /IfNDef MUI_COMPONENTSPAGE_TEXT_DESCRIPTION_TITLE "$(MUI_INNERTEXT_COMPONENTS_DESCRIPTION_TITLE)"
  !define /IfNDef MUI_COMPONENTSPAGE_TEXT_DESCRIPTION_INFO "$(MUI_INNERTEXT_COMPONENTS_DESCRIPTION_INFO)"

  !ifndef MUI_VAR_TEXT
    Var MUI_TEXT
    !define MUI_VAR_TEXT
  !endif

  !ifdef UMUI_COMPONENTSPAGE_REGISTRY_VALUENAME | UMUI_COMPONENTSPAGE_INSTTYPE_REGISTRY_VALUENAME
    !ifndef UMUI_VAR_UMUI_TEMP3
      Var UMUI_TEMP3
      !define UMUI_VAR_UMUI_TEMP3
    !endif
  !endif

  !ifdef UMUI_COMPONENTSPAGE_INSTTYPE_REGISTRY_VALUENAME
    !ifndef UMUI_COMPONENTSPAGE_INSTTYPE_REGISTRY_ROOT
      !ifdef UMUI_PARAMS_REGISTRY_ROOT
        !define UMUI_COMPONENTSPAGE_INSTTYPE_REGISTRY_ROOT "${UMUI_PARAMS_REGISTRY_ROOT}"
      !else
        !error "For UMUI_COMPONENTSPAGE_INSTTYPE_REGISTRY_VALUENAME, the UMUI_COMPONENTSPAGE_INSTTYPE_REGISTRY_ROOT & UMUI_COMPONENTSPAGE_INSTTYPE_REGISTRY_KEY parameters or else the UMUI_PARAMS_REGISTRY_ROOT & UMUI_PARAMS_REGISTRY_KEY global parameters must be defined."
      !endif
    !endif
    !ifndef UMUI_COMPONENTSPAGE_INSTTYPE_REGISTRY_KEY
      !ifdef UMUI_PARAMS_REGISTRY_KEY
        !define UMUI_COMPONENTSPAGE_INSTTYPE_REGISTRY_KEY "${UMUI_PARAMS_REGISTRY_KEY}"
      !else
        !error "For UMUI_COMPONENTSPAGE_INSTTYPE_REGISTRY_VALUENAME, the UMUI_COMPONENTSPAGE_INSTTYPE_REGISTRY_ROOT & UMUI_COMPONENTSPAGE_INSTTYPE_REGISTRY_KEY parameters or else the UMUI_PARAMS_REGISTRY_ROOT & UMUI_PARAMS_REGISTRY_KEY global parameters must be defined."
      !endif
    !endif
  !endif

  !ifdef UMUI_COMPONENTSPAGE_REGISTRY_VALUENAME
    !ifndef UMUI_COMPONENTSPAGE_REGISTRY_ROOT
      !ifdef UMUI_PARAMS_REGISTRY_ROOT
        !define UMUI_COMPONENTSPAGE_REGISTRY_ROOT "${UMUI_PARAMS_REGISTRY_ROOT}"
      !else
        !error "For UMUI_COMPONENTSPAGE_REGISTRY_VALUENAME, the UMUI_COMPONENTSPAGE_REGISTRY_ROOT & UMUI_COMPONENTSPAGE_REGISTRY_KEY parameters or else the UMUI_PARAMS_REGISTRY_ROOT & UMUI_PARAMS_REGISTRY_KEY global parameters must be defined."
      !endif
    !endif
    !ifndef UMUI_COMPONENTSPAGE_REGISTRY_KEY
      !ifdef UMUI_PARAMS_REGISTRY_KEY
        !define UMUI_COMPONENTSPAGE_REGISTRY_KEY "${UMUI_PARAMS_REGISTRY_KEY}"
      !else
        !error "For UMUI_COMPONENTSPAGE_REGISTRY_VALUENAME, the UMUI_COMPONENTSPAGE_REGISTRY_ROOT & UMUI_COMPONENTSPAGE_REGISTRY_KEY parameters or else the UMUI_PARAMS_REGISTRY_ROOT & UMUI_PARAMS_REGISTRY_KEY global parameters must be defined."
      !endif
    !endif
  !endif

  !ifndef MUI_UNINSTALLER
    !ifdef UMUI_MAINTENANCEPAGE
      !ifndef UMUI_COMPONENTSPAGE_REGISTRY_VALUENAME
        !warning "With the maintenance page, you need to set the UMUI_COMPONENTSPAGE_REGISTRY_VALUENAME define with a clean install function."
      !endif
    !endif
  !endif

  PageEx ${MUI_PAGE_UNINSTALLER_FUNCPREFIX}components

    PageCallbacks ${MUI_PAGE_UNINSTALLER_FUNCPREFIX}mui.ComponentsPre_${MUI_UNIQUEID} ${MUI_PAGE_UNINSTALLER_FUNCPREFIX}mui.ComponentsShow_${MUI_UNIQUEID} ${MUI_PAGE_UNINSTALLER_FUNCPREFIX}mui.ComponentsLeave_${MUI_UNIQUEID}

    Caption " "

    ComponentText "${MUI_COMPONENTSPAGE_TEXT_TOP}" "${MUI_COMPONENTSPAGE_TEXT_INSTTYPE}" "${MUI_COMPONENTSPAGE_TEXT_COMPLIST}"

  PageExEnd

  !insertmacro MUI_FUNCTION_COMPONENTSPAGE ${MUI_PAGE_UNINSTALLER_FUNCPREFIX}mui.ComponentsPre_${MUI_UNIQUEID} ${MUI_PAGE_UNINSTALLER_FUNCPREFIX}mui.ComponentsShow_${MUI_UNIQUEID} ${MUI_PAGE_UNINSTALLER_FUNCPREFIX}mui.ComponentsLeave_${MUI_UNIQUEID}

  !undef MUI_COMPONENTSPAGE_TEXT_TOP
  !undef MUI_COMPONENTSPAGE_TEXT_COMPLIST
  !undef MUI_COMPONENTSPAGE_TEXT_INSTTYPE
  !insertmacro MUI_UNSET MUI_COMPONENTSPAGE_TEXT_DESCRIPTION_TITLE
  !insertmacro MUI_UNSET MUI_COMPONENTSPAGE_TEXT_DESCRIPTION_INFO

  !insertmacro MUI_UNSET UMUI_COMPONENTSPAGE_REGISTRY_ROOT
  !insertmacro MUI_UNSET UMUI_COMPONENTSPAGE_REGISTRY_KEY
  !insertmacro MUI_UNSET UMUI_COMPONENTSPAGE_REGISTRY_VALUENAME
  !insertmacro MUI_UNSET UMUI_COMPONENTSPAGE_INSTTYPE_REGISTRY_ROOT
  !insertmacro MUI_UNSET UMUI_COMPONENTSPAGE_INSTTYPE_REGISTRY_KEY
  !insertmacro MUI_UNSET UMUI_COMPONENTSPAGE_INSTTYPE_REGISTRY_VALUENAME

  !verbose pop

!macroend

!macro MUI_PAGE_DIRECTORY

  !verbose push
  !verbose ${MUI_VERBOSE}

  !insertmacro MUI_PAGE_INIT

  !define /IfNDef MUI_${MUI_PAGE_UNINSTALLER_PREFIX}DIRECTORYPAGE

  !define /IfNDef MUI_DIRECTORYPAGE_TEXT_TOP ""
  !define /IfNDef MUI_DIRECTORYPAGE_TEXT_DESTINATION ""

  PageEx ${MUI_PAGE_UNINSTALLER_FUNCPREFIX}directory

    PageCallbacks ${MUI_PAGE_UNINSTALLER_FUNCPREFIX}mui.DirectoryPre_${MUI_UNIQUEID} ${MUI_PAGE_UNINSTALLER_FUNCPREFIX}mui.DirectoryShow_${MUI_UNIQUEID} ${MUI_PAGE_UNINSTALLER_FUNCPREFIX}mui.DirectoryLeave_${MUI_UNIQUEID}

    Caption " "

    DirText "${MUI_DIRECTORYPAGE_TEXT_TOP}" "${MUI_DIRECTORYPAGE_TEXT_DESTINATION}"

    !ifdef MUI_DIRECTORYPAGE_VARIABLE
      DirVar "${MUI_DIRECTORYPAGE_VARIABLE}"
    !endif

    !ifdef MUI_DIRECTORYPAGE_VERIFYONLEAVE
      DirVerify leave
    !endif

  PageExEnd

  !insertmacro MUI_FUNCTION_DIRECTORYPAGE ${MUI_PAGE_UNINSTALLER_FUNCPREFIX}mui.DirectoryPre_${MUI_UNIQUEID} ${MUI_PAGE_UNINSTALLER_FUNCPREFIX}mui.DirectoryShow_${MUI_UNIQUEID} ${MUI_PAGE_UNINSTALLER_FUNCPREFIX}mui.DirectoryLeave_${MUI_UNIQUEID}

  !undef MUI_DIRECTORYPAGE_TEXT_TOP
  !undef MUI_DIRECTORYPAGE_TEXT_DESTINATION
  !insertmacro MUI_UNSET MUI_DIRECTORYPAGE_BGCOLOR
  !insertmacro MUI_UNSET MUI_DIRECTORYPAGE_VARIABLE
  !insertmacro MUI_UNSET MUI_DIRECTORYPAGE_VERIFYONLEAVE

  !verbose pop

!macroend

!macro MUI_PAGE_STARTMENU ID VAR

  !verbose push
  !verbose ${MUI_VERBOSE}

  !insertmacro MUI_PAGE_INIT

  !define /IfNDef MUI_${MUI_PAGE_UNINSTALLER_PREFIX}STARTMENUPAGE

  !define /IfNDef MUI_STARTMENUPAGE_DEFAULTFOLDER "$(^Name)"
  !define /IfNDef MUI_STARTMENUPAGE_TEXT_TOP "$(MUI_${MUI_PAGE_UNINSTALLER_PREFIX}INNERTEXT_STARTMENU_TOP)"
  !define /IfNDef MUI_STARTMENUPAGE_TEXT_CHECKBOX "$(MUI_${MUI_PAGE_UNINSTALLER_PREFIX}INNERTEXT_STARTMENU_CHECKBOX)"

  !define MUI_STARTMENUPAGE_VARIABLE "${VAR}"
  !define "MUI_STARTMENUPAGE_${ID}_VARIABLE" "${MUI_STARTMENUPAGE_VARIABLE}"
  !define "MUI_STARTMENUPAGE_${ID}_DEFAULTFOLDER" "${MUI_STARTMENUPAGE_DEFAULTFOLDER}"
  !ifdef MUI_STARTMENUPAGE_REGISTRY_VALUENAME
    !define "MUI_STARTMENUPAGE_${ID}_REGISTRY_VALUENAME" "${MUI_STARTMENUPAGE_REGISTRY_VALUENAME}"

    !ifndef MUI_STARTMENUPAGE_REGISTRY_ROOT
      !ifdef UMUI_PARAMS_REGISTRY_ROOT
        !define MUI_STARTMENUPAGE_REGISTRY_ROOT "${UMUI_PARAMS_REGISTRY_ROOT}"
      !else
        !error "For MUI_STARTMENUPAGE_REGISTRY_VALUENAME, the MUI_STARTMENUPAGE_REGISTRY_ROOT & MUI_STARTMENUPAGE_REGISTRY_KEY parameters or else the UMUI_PARAMS_REGISTRY_ROOT & UMUI_PARAMS_REGISTRY_KEY global parameters must be defined."
      !endif
    !endif
    !ifndef MUI_STARTMENUPAGE_REGISTRY_KEY
      !ifdef UMUI_PARAMS_REGISTRY_KEY
        !define MUI_STARTMENUPAGE_REGISTRY_KEY "${UMUI_PARAMS_REGISTRY_KEY}"
      !else
        !error "For MUI_STARTMENUPAGE_REGISTRY_VALUENAME, the MUI_STARTMENUPAGE_REGISTRY_ROOT & MUI_STARTMENUPAGE_REGISTRY_KEY parameters or else the UMUI_PARAMS_REGISTRY_ROOT & UMUI_PARAMS_REGISTRY_KEY global parameters must be defined."
      !endif
    !endif

    !define "MUI_STARTMENUPAGE_${ID}_REGISTRY_ROOT" "${MUI_STARTMENUPAGE_REGISTRY_ROOT}"
    !define "MUI_STARTMENUPAGE_${ID}_REGISTRY_KEY" "${MUI_STARTMENUPAGE_REGISTRY_KEY}"

  !endif

  !ifdef UMUI_UNIQUEBGIMAGE | UMUI_PAGEBGIMAGE
    !warning "The MUI_STARTMENU page does not work with the UMUI_UNIQUEBGIMAGE and UMUI_PAGEBGIMAGE defines. Use the UMUI_ALTERNATIVESTARTMENU page instead."
  !endif

  !ifndef MUI_VAR_HWND
    Var MUI_HWND
    !define MUI_VAR_HWND
  !endif

  PageEx ${MUI_PAGE_UNINSTALLER_FUNCPREFIX}custom

    PageCallbacks ${MUI_PAGE_UNINSTALLER_FUNCPREFIX}mui.StartmenuPre_${MUI_UNIQUEID} ${MUI_PAGE_UNINSTALLER_FUNCPREFIX}mui.StartmenuLeave_${MUI_UNIQUEID}

    Caption " "

  PageExEnd

  !insertmacro MUI_FUNCTION_STARTMENUPAGE ${MUI_PAGE_UNINSTALLER_FUNCPREFIX}mui.StartmenuPre_${MUI_UNIQUEID} ${MUI_PAGE_UNINSTALLER_FUNCPREFIX}mui.StartmenuLeave_${MUI_UNIQUEID}

  !undef MUI_STARTMENUPAGE_VARIABLE
  !undef MUI_STARTMENUPAGE_TEXT_TOP
  !undef MUI_STARTMENUPAGE_TEXT_CHECKBOX
  !undef MUI_STARTMENUPAGE_DEFAULTFOLDER
  !insertmacro MUI_UNSET MUI_STARTMENUPAGE_NODISABLE
  !insertmacro MUI_UNSET MUI_STARTMENUPAGE_REGISTRY_ROOT
  !insertmacro MUI_UNSET MUI_STARTMENUPAGE_REGISTRY_KEY
  !insertmacro MUI_UNSET MUI_STARTMENUPAGE_REGISTRY_VALUENAME
  !insertmacro MUI_UNSET MUI_STARTMENUPAGE_BGCOLOR

  !verbose pop

!macroend

!macro MUI_PAGE_INSTFILES

  !verbose push
  !verbose ${MUI_VERBOSE}

  !insertmacro MUI_PAGE_INIT

  !define /IfNDef MUI_${MUI_PAGE_UNINSTALLER_PREFIX}INSTFILESPAGE

  !ifdef UMUI_INSTALLDIR_REGISTRY_VALUENAME
    !ifndef UMUI_INSTALLDIR_REGISTRY_ROOT
      !ifdef UMUI_PARAMS_REGISTRY_ROOT
        !define UMUI_INSTALLDIR_REGISTRY_ROOT "${UMUI_PARAMS_REGISTRY_ROOT}"
      !else
        !error "For UMUI_INSTALLDIR_REGISTRY_VALUENAME, the UMUI_INSTALLDIR_REGISTRY_ROOT & UMUI_INSTALLDIR_REGISTRY_KEY parameters or else the UMUI_PARAMS_REGISTRY_ROOT & UMUI_PARAMS_REGISTRY_KEY global parameters must be defined."
      !endif
    !endif
    !ifndef UMUI_INSTALLDIR_REGISTRY_KEY
      !ifdef UMUI_PARAMS_REGISTRY_KEY
        !define UMUI_INSTALLDIR_REGISTRY_KEY "${UMUI_PARAMS_REGISTRY_KEY}"
      !else
        !error "For UMUI_INSTALLDIR_REGISTRY_VALUENAME, the UMUI_INSTALLDIR_REGISTRY_ROOT & UMUI_INSTALLDIR_REGISTRY_KEY parameters or else the UMUI_PARAMS_REGISTRY_ROOT & UMUI_PARAMS_REGISTRY_KEY global parameters must be defined."
      !endif
    !endif
  !endif

  PageEx ${MUI_PAGE_UNINSTALLER_FUNCPREFIX}instfiles

    PageCallbacks ${MUI_PAGE_UNINSTALLER_FUNCPREFIX}mui.InstFilesPre_${MUI_UNIQUEID} ${MUI_PAGE_UNINSTALLER_FUNCPREFIX}mui.InstFilesShow_${MUI_UNIQUEID} ${MUI_PAGE_UNINSTALLER_FUNCPREFIX}mui.InstFilesLeave_${MUI_UNIQUEID}

    Caption " "

  PageExEnd

  !insertmacro MUI_FUNCTION_INSTFILESPAGE ${MUI_PAGE_UNINSTALLER_FUNCPREFIX}mui.InstFilesPre_${MUI_UNIQUEID} ${MUI_PAGE_UNINSTALLER_FUNCPREFIX}mui.InstFilesShow_${MUI_UNIQUEID} ${MUI_PAGE_UNINSTALLER_FUNCPREFIX}mui.InstFilesLeave_${MUI_UNIQUEID}

  !insertmacro MUI_UNSET MUI_INSTFILESPAGE_FINISHHEADER_TEXT
  !insertmacro MUI_UNSET MUI_INSTFILESPAGE_FINISHHEADER_SUBTEXT
  !insertmacro MUI_UNSET MUI_INSTFILESPAGE_ABORTWARNING_TEXT
  !insertmacro MUI_UNSET MUI_INSTFILESPAGE_ABORTWARNING_SUBTEXT

  !verbose pop

!macroend

!macro MUI_PAGE_FINISH

  !verbose push
  !verbose ${MUI_VERBOSE}

  !insertmacro MUI_PAGE_INIT

  !define /IfNDef MUI_${MUI_PAGE_UNINSTALLER_PREFIX}FINISHPAGE

  !insertmacro MUI_DEFAULT_IOCONVERT MUI_FINISHPAGE_TITLE "$(MUI_${MUI_PAGE_UNINSTALLER_PREFIX}TEXT_FINISH_INFO_TITLE)"
  !insertmacro MUI_DEFAULT_IOCONVERT MUI_FINISHPAGE_TEXT "$(MUI_${MUI_PAGE_UNINSTALLER_PREFIX}TEXT_FINISH_INFO_TEXT)"
  !insertmacro MUI_DEFAULT_IOCONVERT MUI_FINISHPAGE_BUTTON "$(MUI_BUTTONTEXT_FINISH)"
  !insertmacro MUI_DEFAULT_IOCONVERT MUI_FINISHPAGE_TEXT_REBOOT "$(MUI_${MUI_PAGE_UNINSTALLER_PREFIX}TEXT_FINISH_INFO_REBOOT)"
  !insertmacro MUI_DEFAULT_IOCONVERT MUI_FINISHPAGE_TEXT_REBOOTNOW "$(MUI_TEXT_FINISH_REBOOTNOW)"
  !insertmacro MUI_DEFAULT_IOCONVERT MUI_FINISHPAGE_TEXT_REBOOTLATER "$(MUI_TEXT_FINISH_REBOOTLATER)"
  !insertmacro MUI_DEFAULT_IOCONVERT MUI_FINISHPAGE_RUN_TEXT "$(MUI_TEXT_FINISH_RUN)"
  !insertmacro MUI_DEFAULT_IOCONVERT MUI_FINISHPAGE_SHOWREADME_TEXT "$(MUI_TEXT_FINISH_SHOWREADME)"

  !define /IfNDef MUI_FINISHPAGE_LINK_COLOR "${UMUI_TEXT_LIGHTCOLOR}"

  !ifndef MUI_VAR_HWND
    Var MUI_HWND
    !define MUI_VAR_HWND
  !endif

  !ifndef MUI_PAGE_UNINSTALLER
    !ifndef MUI_FINISHPAGE_NOAUTOCLOSE
      AutoCloseWindow true
    !endif
  !endif

  !ifdef MUI_FINISHPAGE_CANCEL_ENABLED
    !ifndef MUI_VAR_NOABORTWARNING
      !define MUI_VAR_NOABORTWARNING
      Var MUI_NOABORTWARNING
    !endif
  !endif

  PageEx ${MUI_PAGE_UNINSTALLER_FUNCPREFIX}custom

    PageCallbacks ${MUI_PAGE_UNINSTALLER_FUNCPREFIX}mui.FinishPre_${MUI_UNIQUEID} ${MUI_PAGE_UNINSTALLER_FUNCPREFIX}mui.FinishLeave_${MUI_UNIQUEID}

    Caption " "

  PageExEnd

  !insertmacro MUI_FUNCTION_FINISHPAGE ${MUI_PAGE_UNINSTALLER_FUNCPREFIX}mui.FinishPre_${MUI_UNIQUEID} ${MUI_PAGE_UNINSTALLER_FUNCPREFIX}mui.FinishLeave_${MUI_UNIQUEID}

  !insertmacro MUI_UNSET MUI_FINISHPAGE_TITLE
  !insertmacro MUI_UNSET MUI_FINISHPAGE_TITLE_3LINES
  !insertmacro MUI_UNSET MUI_FINISHPAGE_TEXT
  !insertmacro MUI_UNSET MUI_FINISHPAGE_TEXT_LARGE
  !insertmacro MUI_UNSET MUI_FINISHPAGE_BUTTON
  !insertmacro MUI_UNSET MUI_FINISHPAGE_CANCEL_ENABLED
  !insertmacro MUI_UNSET MUI_FINISHPAGE_TEXT_REBOOT
  !insertmacro MUI_UNSET MUI_FINISHPAGE_TEXT_REBOOTNOW
  !insertmacro MUI_UNSET MUI_FINISHPAGE_TEXT_REBOOTLATER
  !insertmacro MUI_UNSET MUI_FINISHPAGE_REBOOTLATER_DEFAULT
  !insertmacro MUI_UNSET MUI_FINISHPAGE_RUN
    !insertmacro MUI_UNSET MUI_FINISHPAGE_RUN_TEXT
    !insertmacro MUI_UNSET MUI_FINISHPAGE_RUN_PARAMETERS
    !insertmacro MUI_UNSET MUI_FINISHPAGE_RUN_NOTCHECKED
    !insertmacro MUI_UNSET MUI_FINISHPAGE_RUN_FUNCTION
  !insertmacro MUI_UNSET MUI_FINISHPAGE_SHOWREADME
    !insertmacro MUI_UNSET MUI_FINISHPAGE_SHOWREADME_TEXT
    !insertmacro MUI_UNSET MUI_FINISHPAGE_SHOWREADME_NOTCHECKED
    !insertmacro MUI_UNSET MUI_FINISHPAGE_SHOWREADME_FUNCTION
  !insertmacro MUI_UNSET MUI_FINISHPAGE_LINK
    !insertmacro MUI_UNSET MUI_FINISHPAGE_LINK_LOCATION
    !insertmacro MUI_UNSET MUI_FINISHPAGE_LINK_COLOR
  !insertmacro MUI_UNSET MUI_FINISHPAGE_NOREBOOTSUPPORT

  !insertmacro MUI_UNSET MUI_FINISHPAGE_CURFIELD_TOP
  !insertmacro MUI_UNSET MUI_FINISHPAGE_CURFIELD_BOTTOM

  !verbose pop

!macroend

!macro MUI_UNPAGE_WELCOME

  !verbose push
  !verbose ${MUI_VERBOSE}

  !insertmacro MUI_UNPAGE_INIT

    !insertmacro MUI_PAGE_WELCOME

  !insertmacro MUI_UNPAGE_END

  !verbose pop

!macroend

!macro MUI_UNPAGE_CONFIRM

  !verbose push
  !verbose ${MUI_VERBOSE}

  !define /IfNDef MUI_UNINSTALLER

  !insertmacro MUI_PAGE_INIT

  !define /IfNDef MUI_UNCONFIRMPAGE

  !define /IfNDef MUI_UNCONFIRMPAGE_TEXT_TOP ""
  !define /IfNDef MUI_UNCONFIRMPAGE_TEXT_LOCATION ""

  PageEx un.uninstConfirm

    PageCallbacks un.mui.ConfirmPre_${MUI_UNIQUEID} un.mui.ConfirmShow_${MUI_UNIQUEID} un.mui.ConfirmLeave_${MUI_UNIQUEID}

    Caption " "

    UninstallText "${MUI_UNCONFIRMPAGE_TEXT_TOP}" "${MUI_UNCONFIRMPAGE_TEXT_LOCATION}"

    !ifdef MUI_UNCONFIRMPAGE_VARIABLE
      DirVar "${MUI_UNCONFIRMPAGE_VARIABLE}"
    !endif

  PageExEnd

  !insertmacro MUI_UNFUNCTION_CONFIRMPAGE un.mui.ConfirmPre_${MUI_UNIQUEID} un.mui.ConfirmShow_${MUI_UNIQUEID} un.mui.ConfirmLeave_${MUI_UNIQUEID}

  !insertmacro MUI_UNSET MUI_UNCONFIRMPAGE_TEXT_TOP
  !insertmacro MUI_UNSET MUI_UNCONFIRMPAGE_TEXT_LOCATION

  !verbose pop

!macroend

!macro MUI_UNPAGE_LICENSE LICENSEDATA

  !verbose push
  !verbose ${MUI_VERBOSE}

  !insertmacro MUI_UNPAGE_INIT

    !insertmacro MUI_PAGE_LICENSE "${LICENSEDATA}"

  !insertmacro MUI_UNPAGE_END

  !verbose pop

!macroend

!macro MUI_UNPAGE_COMPONENTS

  !verbose push
  !verbose ${MUI_VERBOSE}

  !insertmacro MUI_UNPAGE_INIT

    !insertmacro MUI_PAGE_COMPONENTS

  !insertmacro MUI_UNPAGE_END

  !verbose pop

!macroend

!macro MUI_UNPAGE_DIRECTORY

  !verbose push
  !verbose ${MUI_VERBOSE}

  !insertmacro MUI_UNPAGE_INIT

    !insertmacro MUI_PAGE_DIRECTORY

  !insertmacro MUI_UNPAGE_END

  !verbose pop

!macroend

!macro MUI_UNPAGE_INSTFILES

  !verbose push
  !verbose ${MUI_VERBOSE}

  !insertmacro MUI_UNPAGE_INIT

    !insertmacro MUI_PAGE_INSTFILES

  !insertmacro MUI_UNPAGE_END

  !verbose pop

!macroend

!macro MUI_UNPAGE_FINISH

  !verbose push
  !verbose ${MUI_VERBOSE}

  !insertmacro MUI_UNPAGE_INIT

    !insertmacro MUI_PAGE_FINISH

  !insertmacro MUI_UNPAGE_END

  !verbose pop

!macroend

;--------------------------------
;PAGE FUNCTIONS


; TODO: Rewrite the INSTALLFLAGS Macros to be able to use conditions like: ~X|Y&~Z|~V&~W|~U meaning (~X)|(Y&~Z)|(~V&~W)|(U)


; Convert a string VALUE1|VALUE2|VALUE4 to a OR bit by bit VALUE7 integer.
; Convert a string VALUE1&VALUE2&VALUE4 to a OR bit by bit VALUE7 integer.
; Usage:
;   !insertmacro UMUI_STR2INT string
;   Pop $VAR <INT Value>
;   IntOp $VAR $VAR ~   only to have a NAND bit by bit VALUE inteder.

!macro UMUI_STR2INT VALUE
  Push $0 ; The source
  Push $1 ; The output
  Push $2 ; Temporary char
  Push $3 ; Temporary integer

  !define UMUI_UNIQUEIDSTR2INT ${__LINE__}

  StrCpy $0 ${VALUE} ; Initialise the source
  StrCpy $1 0        ; Initialise the output
  StrCpy $3 0        ; Initialise the temporary integer

  loop${UMUI_UNIQUEIDSTR2INT}:
    StrCpy $2 $0 1 ; Get the next source char
    StrCmp $2 "" done${UMUI_UNIQUEIDSTR2INT} ; Abort when none left
      StrCpy $0 $0 "" 1 ; Remove it from the source
      StrCmp $2 "|" +2 +1 ; | OR Bit by bit
        StrCmp $2 "&" 0 +4 ; & AND Bit by bit
          IntOp $1 $1 | $3
          StrCpy $3 0
          Goto loop${UMUI_UNIQUEIDSTR2INT}
      IntOp $3 $3 * 10
      IntOp $3 $3 + $2
      Goto loop${UMUI_UNIQUEIDSTR2INT}

  done${UMUI_UNIQUEIDSTR2INT}:
    IntOp $1 $1 | $3

  !undef UMUI_UNIQUEIDSTR2INT

  StrCpy $0 $1
  Pop $3
  Pop $2
  Pop $1
  Exch $0
!macroend




!macro UMUI_ABORT_IF_INSTALLFLAG_IS VALUE
  Push $0

  ; convert INT|INT|INT string into an integer value
  !ifndef UMUI_ABORT_IF_INSTALLFLAG_IS
    !insertmacro UMUI_STR2INT ${VALUE}
  !else
    !insertmacro UMUI_STR2INT ${UMUI_ABORT_IF_INSTALLFLAG_IS}
    !undef UMUI_ABORT_IF_INSTALLFLAG_IS
  !endif

  Pop $0

  StrCmp $0 "none" +5 0
    IntOp $0 $UMUI_INSTALLFLAG & $0
    IntCmp $0 0 +3 0 0
      Pop $0
      Abort

  Pop $0
!macroend

!macro UMUI_ABORT_IF_INSTALLFLAG_ISNOT VALUE
  Push $0
  Push $1

  ; convert INT|INT|INT string into an integer value
  !ifndef UMUI_ABORT_IF_INSTALLFLAG_ISNOT
    !insertmacro UMUI_STR2INT ${VALUE}
  !else
    !insertmacro UMUI_STR2INT ${UMUI_ABORT_IF_INSTALLFLAG_ISNOT}
    !undef UMUI_ABORT_IF_INSTALLFLAG_ISNOT
  !endif

  Pop $0

  StrCmp $0 "none" +5 0

    IntOp $0 $0 ~
    IntOp $1 $UMUI_INSTALLFLAG | $0
    IntCmp $1 $0 0 +4 +4
      Pop $1
      Pop $0
      Abort

  Pop $1
  Pop $0
!macroend



!macro UMUI_IF_INSTALLFLAG_ISNOT VALUE

  Push $0

  !ifndef UMUI_POPVAR1
    Push $1
    !define UMUI_POPVAR1
  !endif

  !ifdef UMUI_UNIQUEIDIS
    !define UMUI_UNIQUEIDISIMB ${__LINE__}
  !else
    !define UMUI_UNIQUEIDIS ${__LINE__}
  !endif

  !insertmacro UMUI_STR2INT ${VALUE}

  Pop $0

  !ifdef UMUI_UNIQUEIDISIMB

    StrCmp $0 "none" endpop${UMUI_UNIQUEIDISIMB}  0

      IntOp $0 $0 ~
      IntOp $1 $UMUI_INSTALLFLAG | $0

      IntCmp $1 $0 0 endpop${UMUI_UNIQUEIDISIMB} endpop${UMUI_UNIQUEIDISIMB}

  !else

    StrCmp $0 "none" endpop${UMUI_UNIQUEIDIS}  0

      IntOp $0 $0 ~
      IntOp $1 $UMUI_INSTALLFLAG | $0

      IntCmp $1 $0 0 endpop${UMUI_UNIQUEIDIS} endpop${UMUI_UNIQUEIDIS}

  !endif

  Pop $1
  Pop $0

!macroend


!macro UMUI_IF_INSTALLFLAG_IS VALUE

  Push $0

  !ifdef UMUI_UNIQUEIDIS
    !define UMUI_UNIQUEIDISIMB ${__LINE__}
  !else
    !define UMUI_UNIQUEIDIS ${__LINE__}
  !endif

  !insertmacro UMUI_STR2INT ${VALUE}

  Pop $0

  !ifdef UMUI_UNIQUEIDISIMB

    StrCmp $0 "none" endpop${UMUI_UNIQUEIDISIMB} 0

      IntOp $0 $UMUI_INSTALLFLAG & $0
      IntCmp $0 0 endpop${UMUI_UNIQUEIDISIMB} 0 0

  !else

    StrCmp $0 "none" endpop${UMUI_UNIQUEIDIS} 0

      IntOp $0 $UMUI_INSTALLFLAG & $0
      IntCmp $0 0 endpop${UMUI_UNIQUEIDIS} 0 0

  !endif

  Pop $0

!macroend


!macro UMUI_ENDIF_INSTALLFLAG

  !ifdef UMUI_UNIQUEIDISIMB

    Goto end${UMUI_UNIQUEIDISIMB}

    endpop${UMUI_UNIQUEIDISIMB}:
      !ifdef UMUI_POPVAR1
        Pop $1
        !undef UMUI_POPVAR1
      !endif
;      Pop $0                  ; Cause an invalide opcode

    end${UMUI_UNIQUEIDISIMB}:

    !undef UMUI_UNIQUEIDISIMB

  !else

    Goto end${UMUI_UNIQUEIDIS}

    endpop${UMUI_UNIQUEIDIS}:
      !ifdef UMUI_POPVAR1
        Pop $1
        !undef UMUI_POPVAR1
      !endif
      Pop $0

    end${UMUI_UNIQUEIDIS}:

    !undef UMUI_UNIQUEIDIS

  !endif

!macroend


!macro UMUI_SET_INSTALLFLAG VALUE
  Push $0

  ; convert INT|INT|INT string into an integer value
  !insertmacro UMUI_STR2INT ${VALUE}
  Pop $0

  IntOp $UMUI_INSTALLFLAG $UMUI_INSTALLFLAG | $0

  Pop $0
!macroend

!macro UMUI_UNSET_INSTALLFLAG VALUE
  Push $0

  ; convert INT|INT|INT string into an integer value
  !insertmacro UMUI_STR2INT ${VALUE}
  Pop $0

  IntOp $0 $0 ~
  IntOp $UMUI_INSTALLFLAG $UMUI_INSTALLFLAG & $0

  Pop $0
!macroend




!macro UMUI_UMUI_HIDEBACKBUTTON

  !ifdef UMUI_HIDEFIRSTBACKBUTTON
    GetDlgItem $MUI_TEMP1 $HWNDPARENT 3
    ShowWindow $MUI_TEMP1 ${SW_HIDE}
  !else
    !insertmacro UMUI_IF_INSTALLFLAG_IS ${UMUI_HIDEBACKBUTTON}
      GetDlgItem $MUI_TEMP1 $HWNDPARENT 3
      ShowWindow $MUI_TEMP1 ${SW_HIDE}
    !insertmacro UMUI_ENDIF_INSTALLFLAG
  !endif

  !insertmacro UMUI_UNSET_INSTALLFLAG ${UMUI_HIDEBACKBUTTON}

  !ifndef UMUI_HIDENEXTBACKBUTTON
    !insertmacro MUI_UNSET UMUI_HIDEFIRSTBACKBUTTON
  !else
    !define /IfNDef UMUI_HIDEFIRSTBACKBUTTON
    !insertmacro UMUI_SET_INSTALLFLAG ${UMUI_HIDEBACKBUTTON}
    !undef UMUI_HIDENEXTBACKBUTTON
  !endif

!macroend


!macro MUI_PAGE_FUNCTION_CUSTOM TYPE

  !ifdef MUI_PAGE_CUSTOMFUNCTION_${TYPE}
    Call "${MUI_PAGE_CUSTOMFUNCTION_${TYPE}}"
    !undef MUI_PAGE_CUSTOMFUNCTION_${TYPE}
  !endif

!macroend

!macro MUI_WELCOMEFINISHPAGE_FUNCTION_CUSTOM

  !ifdef MUI_WELCOMEFINISHPAGE_CUSTOMFUNCTION_INIT
    Call "${MUI_WELCOMEFINISHPAGE_CUSTOMFUNCTION_INIT}"
    !undef MUI_WELCOMEFINISHPAGE_CUSTOMFUNCTION_INIT
  !endif

!macroend



!macro MUI_FUNCTION_WELCOMEPAGE PRE LEAVE

  !ifndef UMUI_WELCOMEFINISHABORTPAGE_USE_IMAGE
    !define UMUI_INTERNAL_WNUMFIELDS 2
    !define UMUI_INTERNAL_WFIELDTITLE 1
    !define UMUI_INTERNAL_WFIELDTEXT 2
    !define UMUI_INTERNAL_WIDTITLE 1200
    !define UMUI_INTERNAL_WIDTEXT 1201
  !else
    !define UMUI_INTERNAL_WNUMFIELDS 3
    !define UMUI_INTERNAL_WFIELDTITLE 2
    !define UMUI_INTERNAL_WFIELDTEXT 3
    !define UMUI_INTERNAL_WIDTITLE 1201
    !define UMUI_INTERNAL_WIDTEXT 1202
  !endif

  Function "${PRE}"

    ; IF setup cancelled
    !insertmacro UMUI_ABORT_IF_INSTALLFLAG_IS ${UMUI_CANCELLED}|${UMUI_MODIFY}|${UMUI_REPAIR}|${UMUI_UPDATE}

    !insertmacro MUI_HEADER_TEXT_PAGE "" ""

    !insertmacro MUI_WELCOMEFINISHPAGE_FUNCTION_CUSTOM

    !insertmacro INSTALLOPTIONS_WRITE "ioSpecial.ini" "Settings" "NumFields" "${UMUI_INTERNAL_WNUMFIELDS}"
    !insertmacro INSTALLOPTIONS_WRITE "ioSpecial.ini" "Settings" "NextButtonText" ""
    !insertmacro INSTALLOPTIONS_WRITE "ioSpecial.ini" "Settings" "CancelEnabled" ""

    !insertmacro MUI_INSTALLOPTIONS_WRITE_DEFAULTCONVERT "ioSpecial.ini" "Field ${UMUI_INTERNAL_WFIELDTITLE}" "Text" "MUI_WELCOMEPAGE_TITLE"

    !ifndef UMUI_USE_${MUI_PAGE_UNINSTALLER_PREFIX}ALTERNATE_PAGE
      !ifndef MUI_WELCOMEPAGE_TITLE_3LINES
        !insertmacro INSTALLOPTIONS_WRITE "ioSpecial.ini" "Field ${UMUI_INTERNAL_WFIELDTITLE}" "Bottom" "55"
        !insertmacro INSTALLOPTIONS_WRITE "ioSpecial.ini" "Field ${UMUI_INTERNAL_WFIELDTEXT}" "Top" "62"
      !else
        !insertmacro INSTALLOPTIONS_WRITE "ioSpecial.ini" "Field ${UMUI_INTERNAL_WFIELDTITLE}" "Bottom" "62"
        !insertmacro INSTALLOPTIONS_WRITE "ioSpecial.ini" "Field ${UMUI_INTERNAL_WFIELDTEXT}" "Top" "69"
      !endif
    !endif

    !insertmacro INSTALLOPTIONS_WRITE "ioSpecial.ini" "Field ${UMUI_INTERNAL_WFIELDTEXT}" "Bottom" "-1"
    !insertmacro MUI_INSTALLOPTIONS_WRITE_DEFAULTCONVERT "ioSpecial.ini" "Field ${UMUI_INTERNAL_WFIELDTEXT}" "Text" "MUI_WELCOMEPAGE_TEXT"

    !insertmacro MUI_PAGE_FUNCTION_CUSTOM PRE

    LockWindow on

!ifdef USE_MUIEx
;-----------------
    GetDlgItem $MUI_TEMP1 $HWNDPARENT 1028
    ShowWindow $MUI_TEMP1 ${SW_HIDE}

    GetDlgItem $MUI_TEMP1 $HWNDPARENT 1256
    ShowWindow $MUI_TEMP1 ${SW_HIDE}

    GetDlgItem $MUI_TEMP1 $HWNDPARENT 1035
    ShowWindow $MUI_TEMP1 ${SW_HIDE}

    GetDlgItem $MUI_TEMP1 $HWNDPARENT 1037
    ShowWindow $MUI_TEMP1 ${SW_HIDE}

    GetDlgItem $MUI_TEMP1 $HWNDPARENT 1038
    ShowWindow $MUI_TEMP1 ${SW_HIDE}

    GetDlgItem $MUI_TEMP1 $HWNDPARENT 1039
    ShowWindow $MUI_TEMP1 ${SW_HIDE}
!endif
;-----------------

    GetDlgItem $MUI_TEMP1 $HWNDPARENT 1045
    ShowWindow $MUI_TEMP1 ${SW_NORMAL}

    LockWindow off


    !insertmacro INSTALLOPTIONS_INITDIALOG "ioSpecial.ini"
    Pop $MUI_HWND

    !insertmacro UMUI_WFAPAGEBGTRANSPARENT_INIT $MUI_HWND

    !ifndef UMUI_USE_${MUI_PAGE_UNINSTALLER_PREFIX}ALTERNATE_PAGE

      GetDlgItem $MUI_TEMP1 $MUI_HWND ${UMUI_INTERNAL_WIDTITLE}
      !insertmacro UMUI_IOPAGECTLTRANSPARENT_INIT $MUI_TEMP1
      CreateFont $MUI_TEMP2 "$(^Font)" "${UMUI_WELCOMEFINISHABORT_TITLE_FONTSIZE}" "700"
      SendMessage $MUI_TEMP1 ${WM_SETFONT} $MUI_TEMP2 0
      GetDlgItem $MUI_TEMP1 $MUI_HWND ${UMUI_INTERNAL_WIDTEXT}
      !insertmacro UMUI_IOPAGECTLTRANSPARENT_INIT $MUI_TEMP1

    !else

      ;alternate page
      GetDlgItem $MUI_TEMP1 $MUI_HWND ${UMUI_INTERNAL_WIDTITLE}
      CreateFont $MUI_TEMP2 "MS Sans Serif" "${UMUI_WELCOMEFINISHABORT_TITLE_FONTSIZE}" "700"
      SendMessage $MUI_TEMP1 ${WM_SETFONT} $MUI_TEMP2 $MUI_TEMP2
      !insertmacro UMUI_IOPAGECTLTRANSPARENT_INIT $MUI_TEMP1
      GetDlgItem $MUI_TEMP1 $MUI_HWND ${UMUI_INTERNAL_WIDTEXT}
      !insertmacro UMUI_IOPAGECTLTRANSPARENT_INIT $MUI_TEMP1

    !endif


    GetDlgItem $MUI_TEMP1 $HWNDPARENT 3
    ShowWindow $MUI_TEMP1 ${SW_HIDE}

    !insertmacro MUI_PAGE_FUNCTION_CUSTOM SHOW

    !insertmacro INSTALLOPTIONS_SHOW

    LockWindow on

!ifdef USE_MUIEx
;-----------------
    GetDlgItem $MUI_TEMP1 $HWNDPARENT 1028
    ShowWindow $MUI_TEMP1 ${SW_NORMAL}

    GetDlgItem $MUI_TEMP1 $HWNDPARENT 1256
    ShowWindow $MUI_TEMP1 ${SW_NORMAL}

    GetDlgItem $MUI_TEMP1 $HWNDPARENT 1035
    ShowWindow $MUI_TEMP1 ${SW_NORMAL}

    GetDlgItem $MUI_TEMP1 $HWNDPARENT 1037
    ShowWindow $MUI_TEMP1 ${SW_NORMAL}

    GetDlgItem $MUI_TEMP1 $HWNDPARENT 1038
    ShowWindow $MUI_TEMP1 ${SW_NORMAL}

    GetDlgItem $MUI_TEMP1 $HWNDPARENT 1039
    ShowWindow $MUI_TEMP1 ${SW_NORMAL}
!endif
;-----------------

    GetDlgItem $MUI_TEMP1 $HWNDPARENT 1045
    ShowWindow $MUI_TEMP1 ${SW_HIDE}

    LockWindow off

    !insertmacro UMUI_FIX_BUTTONS_SKIN

  FunctionEnd

  Function "${LEAVE}"

    !insertmacro MUI_PAGE_FUNCTION_CUSTOM LEAVE

  FunctionEnd

  !undef UMUI_INTERNAL_WNUMFIELDS
  !undef UMUI_INTERNAL_WFIELDTITLE
  !undef UMUI_INTERNAL_WFIELDTEXT
  !undef UMUI_INTERNAL_WIDTITLE
  !undef UMUI_INTERNAL_WIDTEXT

!macroend



!macro MUI_FUNCTION_LICENSEPAGE PRE SHOW LEAVE

  Function "${PRE}"

    ; IF setup cancelled
    !insertmacro UMUI_ABORT_IF_INSTALLFLAG_IS ${UMUI_CANCELLED}|${UMUI_MODIFY}|${UMUI_REPAIR}|${UMUI_UPDATE}

    !insertmacro MUI_PAGE_FUNCTION_CUSTOM PRE

    !insertmacro MUI_HEADER_TEXT_PAGE $(MUI_${MUI_PAGE_UNINSTALLER_PREFIX}TEXT_LICENSE_TITLE) $(MUI_${MUI_PAGE_UNINSTALLER_PREFIX}TEXT_LICENSE_SUBTITLE)

    !insertmacro UMUI_FIX_BUTTONS_SKIN

  FunctionEnd

  Function "${SHOW}"

    !insertmacro UMUI_UMUI_HIDEBACKBUTTON

    !insertmacro UMUI_PAGEBGTRANSPARENT_INIT

    !insertmacro UMUI_PAGECTLTRANSPARENT_INIT 1040
    !insertmacro UMUI_PAGECTLTRANSPARENT_INIT 1036
    !insertmacro UMUI_PAGECTLTRANSPARENT_INIT 1006

    !if "${UMUI_XPSTYLE}" == "On"
      !insertmacro UMUI_PAGECTL_INIT 1034
      !insertmacro UMUI_PAGECTL_INIT 1035
    !else
      !insertmacro UMUI_PAGECTLTRANSPARENT_INIT 1034
      !insertmacro UMUI_PAGECTLTRANSPARENT_INIT 1035
    !endif

    !insertmacro MUI_INNERDIALOG_TEXT 1040 "${MUI_LICENSEPAGE_TEXT_TOP}"

    !insertmacro MUI_PAGE_FUNCTION_CUSTOM SHOW

  FunctionEnd

  Function "${LEAVE}"

    !insertmacro MUI_PAGE_FUNCTION_CUSTOM LEAVE

  FunctionEnd

!macroend


!macro MUI_FUNCTION_COMPONENTSPAGE PRE SHOW LEAVE

  Function "${PRE}"

    !ifdef UMUI_COMPONENTSPAGE_INSTTYPE_REGISTRY_VALUENAME | UMUI_COMPONENTSPAGE_REGISTRY_VALUENAME

      !insertmacro UMUI_IF_INSTALLFLAG_ISNOT ${UMUI_MINIMAL}&${UMUI_STANDARD}&${UMUI_COMPLETE}&${UMUI_COMPONENTSSET}

        !ifdef UMUI_COMPONENTSPAGE_INSTTYPE_REGISTRY_VALUENAME

          ReadRegStr $MUI_TEMP1 ${UMUI_COMPONENTSPAGE_INSTTYPE_REGISTRY_ROOT} "${UMUI_COMPONENTSPAGE_INSTTYPE_REGISTRY_KEY}" "${UMUI_COMPONENTSPAGE_INSTTYPE_REGISTRY_VALUENAME}"
          StrCmp $MUI_TEMP1 "" endis

            ;search the ID of the saved InstType
            ClearErrors
            StrCpy $MUI_TEMP2 0
            loopis:
              InstTypeGetText $MUI_TEMP2 $UMUI_TEMP3
              IfErrors endis
                StrCmp $UMUI_TEMP3 $MUI_TEMP1 foundis
                  IntOp $MUI_TEMP2 $MUI_TEMP2 + 1
                  Goto loopis
            foundis:
              SetCurInstType $MUI_TEMP2
              !insertmacro UMUI_SET_INSTALLFLAG ${UMUI_COMPONENTSSET}
          endis:
          ClearErrors

          ; IF page skipped save
          GetCurInstType $MUI_TEMP1
          InstTypeGetText $MUI_TEMP1 $MUI_TEMP2
          StrCmp $MUI_TEMP1 "32" 0 +2
            StrCpy $MUI_TEMP2 ""
          !insertmacro UMUI_ADDPARAMTOSAVETOREGISTRYKEY ${UMUI_COMPONENTSPAGE_INSTTYPE_REGISTRY_ROOT} "${UMUI_COMPONENTSPAGE_INSTTYPE_REGISTRY_KEY}" "${UMUI_COMPONENTSPAGE_INSTTYPE_REGISTRY_VALUENAME}" $MUI_TEMP2

        !endif

        !ifdef UMUI_COMPONENTSPAGE_REGISTRY_VALUENAME

          !insertmacro UMUI_IF_INSTALLFLAG_ISNOT ${UMUI_COMPONENTSSET}

            ReadRegStr $MUI_TEMP1 ${UMUI_COMPONENTSPAGE_REGISTRY_ROOT} "${UMUI_COMPONENTSPAGE_REGISTRY_KEY}" "${UMUI_COMPONENTSPAGE_REGISTRY_VALUENAME}"
            StrCmp $MUI_TEMP1 "" End
              ClearErrors
              Call "${MUI_PAGE_UNINSTALLER_FUNCPREFIX}umui_components"
              !insertmacro UMUI_SET_INSTALLFLAG ${UMUI_COMPONENTSSET}
            End:
            ClearErrors

          !insertmacro UMUI_ENDIF_INSTALLFLAG

          ; IF page skipped save
          StrCpy $MUI_TEMP1 "save"
          !ifdef UMUI_PREUNINSTALL_FUNCTION
            StrCpy $MUI_TEMP2 ""
          !else
            ReadRegStr $MUI_TEMP2 ${UMUI_PARAMS_REGISTRY_ROOT} "${UMUI_PARAMS_REGISTRY_KEY}" "${UMUI_COMPONENTSPAGE_REGISTRY_VALUENAME}"
            ClearErrors
          !endif
          Call "${MUI_PAGE_UNINSTALLER_FUNCPREFIX}umui_components"
          !insertmacro UMUI_ADDPARAMTOSAVETOREGISTRYKEY ${UMUI_COMPONENTSPAGE_REGISTRY_ROOT} "${UMUI_COMPONENTSPAGE_REGISTRY_KEY}" "${UMUI_COMPONENTSPAGE_REGISTRY_VALUENAME}" $MUI_TEMP2

        !endif

      !insertmacro UMUI_ENDIF_INSTALLFLAG

    !endif

    ; IF setup cancelled or setuptype choosen
    !insertmacro UMUI_ABORT_IF_INSTALLFLAG_IS ${UMUI_CANCELLED}|${UMUI_MINIMAL}|${UMUI_STANDARD}|${UMUI_COMPLETE}|${UMUI_REPAIR}|${UMUI_UPDATE}

    !insertmacro MUI_PAGE_FUNCTION_CUSTOM PRE

    !insertmacro MUI_HEADER_TEXT_PAGE $(MUI_${MUI_PAGE_UNINSTALLER_PREFIX}TEXT_COMPONENTS_TITLE) $(MUI_${MUI_PAGE_UNINSTALLER_PREFIX}TEXT_COMPONENTS_SUBTITLE)

    !insertmacro UMUI_FIX_BUTTONS_SKIN

  FunctionEnd

  Function "${SHOW}"

    !insertmacro UMUI_UMUI_HIDEBACKBUTTON

    !insertmacro UMUI_PAGEBGTRANSPARENT_INIT
    !insertmacro UMUI_PAGEINPUTCTL_INIT 1017
    !insertmacro UMUI_PAGEINPUTCTL_INIT 1032
    !insertmacro UMUI_PAGECTLTRANSPARENT_INIT 1022
    !insertmacro UMUI_PAGECTLTRANSPARENT_INIT 1021
    !insertmacro UMUI_PAGECTL_INIT 1023
    !insertmacro UMUI_PAGECTLTRANSPARENT_INIT 1006
    !insertmacro UMUI_PAGECTL_INIT 1043
;    !insertmacro UMUI_PAGECTLTRANSPARENT_INIT 1043
    !insertmacro UMUI_PAGECTLLIGHT_INIT 1042

    !insertmacro MUI_INNERDIALOG_TEXT 1042 "${MUI_COMPONENTSPAGE_TEXT_DESCRIPTION_TITLE}"

    FindWindow $MUI_TEMP1 "#32770" "" $HWNDPARENT
    GetDlgItem $MUI_TEMP1 $MUI_TEMP1 1043

!ifndef USE_MUIEx
;----------------
    !ifndef UMUI_ENABLE_DESCRIPTION_TEXT
      EnableWindow $MUI_TEMP1 0
    !else
      !insertmacro UMUI_PAGECTLLIGHT_INIT 1043
;      !insertmacro UMUI_PAGECTLLIGHTTRANSPARENT_INIT 1043
      EnableWindow $MUI_TEMP1 1
    !endif
!else
;-----
    EnableWindow $MUI_TEMP1 0
!endif
;-----

    !insertmacro MUI_INNERDIALOG_TEXT 1043 "${MUI_COMPONENTSPAGE_TEXT_DESCRIPTION_INFO}"
    StrCpy $MUI_TEXT "${MUI_COMPONENTSPAGE_TEXT_DESCRIPTION_INFO}"
    !insertmacro MUI_PAGE_FUNCTION_CUSTOM SHOW

  FunctionEnd

  Function "${LEAVE}"

    !ifdef UMUI_COMPONENTSPAGE_INSTTYPE_REGISTRY_VALUENAME

      GetCurInstType $MUI_TEMP1
      InstTypeGetText $MUI_TEMP1 $MUI_TEMP2
      StrCmp $MUI_TEMP1 "32" 0 +2
        StrCpy $MUI_TEMP2 ""
      !insertmacro UMUI_ADDPARAMTOSAVETOREGISTRYKEY ${UMUI_COMPONENTSPAGE_INSTTYPE_REGISTRY_ROOT} "${UMUI_COMPONENTSPAGE_INSTTYPE_REGISTRY_KEY}" "${UMUI_COMPONENTSPAGE_INSTTYPE_REGISTRY_VALUENAME}" $MUI_TEMP2

    !endif

    !ifdef UMUI_COMPONENTSPAGE_REGISTRY_VALUENAME

      StrCpy $MUI_TEMP1 "save"
      !ifdef UMUI_PREUNINSTALL_FUNCTION
        StrCpy $MUI_TEMP2 ""
      !else
        ReadRegStr $MUI_TEMP2 ${UMUI_PARAMS_REGISTRY_ROOT} "${UMUI_PARAMS_REGISTRY_KEY}" "${UMUI_COMPONENTSPAGE_REGISTRY_VALUENAME}"
        ClearErrors
      !endif

      Call "${MUI_PAGE_UNINSTALLER_FUNCPREFIX}umui_components"
      !insertmacro UMUI_ADDPARAMTOSAVETOREGISTRYKEY ${UMUI_COMPONENTSPAGE_REGISTRY_ROOT} "${UMUI_COMPONENTSPAGE_REGISTRY_KEY}" "${UMUI_COMPONENTSPAGE_REGISTRY_VALUENAME}" $MUI_TEMP2

    !endif

    !insertmacro MUI_PAGE_FUNCTION_CUSTOM LEAVE

  FunctionEnd

!macroend

!macro UMUI_DECLARECOMPONENTS_BEGIN
  Function umui_components
!macroend

!macro UMUI_DECLAREUNCOMPONENTS_BEGIN
  Function un.umui_components
!macroend

; TODO: Develop the version number comparison
!macro UMUI_COMPONENT SEC

  Push $0    ; len of "${SEC}="
  Push $1    ; temporary compare string
  Push $2    ; characters to test
  Push $3    ; Len to compare
  Push $4    ; Counter

  StrCmp $MUI_TEMP1 "save" 0 read${SEC}
  ;Save choosen components
    SectionGetFlags "${${SEC}}" $UMUI_TEMP3
    IntOp $UMUI_TEMP3 $UMUI_TEMP3 & 1      ; 1 is ${SF_SELECTED}
    StrCmp $UMUI_TEMP3 1 0 end${SEC}

      ;delete "${SEC}=*|" from $MUI_TEMP2 if already in
      StrLen $0 "${SEC}="
      StrCpy $2 $MUI_TEMP2
      StrCpy $4 0

      loops${SEC}:
        StrCpy $1 $2 $0
        StrLen $3 $2
        IntCmp $3 $0 0 notfounds${SEC} 0
          StrCmp $1 "${SEC}=" founds${SEC}
            StrCpy $2 $2 "" 1
            IntOp $4 $4 + 1
            Goto loops${SEC}
      founds${SEC}:
        ;$0 the temporary new $MUI_TEMP2 string
        StrCpy $0 $MUI_TEMP2 $4
        loopsc${SEC}:
          StrCpy $1 $2 1
          StrCmp $1 "|" foundsc${SEC}
            StrCpy $2 $2 "" 1
            Goto loopsc${SEC}
        foundsc${SEC}:
          StrCpy $2 $2 "" 1
          StrCpy $MUI_TEMP2 "$0$2"
      notfounds${SEC}:
        !ifdef UMUI_COMPONENT_VERSION
          StrCpy $MUI_TEMP2 "$MUI_TEMP2${SEC}=${VER}|"
        !else
          StrCpy $MUI_TEMP2 "$MUI_TEMP2${SEC}=|"
        !endif
        Goto end${SEC}

  ;Read choosen components
  read${SEC}:

    StrLen $0 "${SEC}="
    StrCpy $2 $MUI_TEMP1

    loop${SEC}:
      StrCpy $1 $2 $0
      StrLen $3 $2
      IntCmp $3 $0 0 notfound${SEC} 0
        StrCmp $1 "${SEC}=" found${SEC}
          StrCpy $2 $2 "" 1
          Goto loop${SEC}

    found${SEC}:
      ; select component
      SectionGetFlags "${${SEC}}" $0
      IntOp $0 $0 | 1              ; 0x00000001 is ${SF_SELECTED}
      SectionSetFlags "${${SEC}}" $0

      Goto end${SEC}
    notfound${SEC}:
      ; unselect component
      SectionGetFlags "${${SEC}}" $0
      IntOp $0 $0 & 0xFFFFFFFE    ; 0xFFFFFFFE is ${SECTION_OFF}
      SectionSetFlags "${${SEC}}" $0

  end${SEC}:

  Pop $4
  Pop $3
  Pop $2
  Pop $1
  Pop $0

  !insertmacro MUI_UNSET UMUI_COMPONENT_VERSION

!macroend

!macro UMUI_DECLARECOMPONENTS_END
  FunctionEnd
!macroend

!macro UMUI_DECLAREUNCOMPONENTS_END
  FunctionEnd
!macroend


!macro MUI_FUNCTION_DIRECTORYPAGE PRE SHOW LEAVE

  Function "${PRE}"

    ; IF setup cancelled or setuptype choosen
    !insertmacro UMUI_ABORT_IF_INSTALLFLAG_IS ${UMUI_CANCELLED}|${UMUI_MINIMAL}|${UMUI_STANDARD}|${UMUI_COMPLETE}|${UMUI_MODIFY}|${UMUI_REPAIR}|${UMUI_UPDATE}

    !insertmacro MUI_PAGE_FUNCTION_CUSTOM PRE

    !insertmacro MUI_HEADER_TEXT_PAGE $(MUI_${MUI_PAGE_UNINSTALLER_PREFIX}TEXT_DIRECTORY_TITLE) $(MUI_${MUI_PAGE_UNINSTALLER_PREFIX}TEXT_DIRECTORY_SUBTITLE)

    !insertmacro UMUI_FIX_BUTTONS_SKIN

  FunctionEnd

  Function "${SHOW}"

    !insertmacro UMUI_UMUI_HIDEBACKBUTTON

    !insertmacro UMUI_PAGEBGTRANSPARENT_INIT
    !insertmacro UMUI_PAGECTLTRANSPARENT_INIT 1001
    !insertmacro UMUI_PAGECTLTRANSPARENT_INIT 1008
    !insertmacro UMUI_PAGECTLTRANSPARENT_INIT 1006
    !insertmacro UMUI_PAGECTLTRANSPARENT_INIT 1023
    !insertmacro UMUI_PAGECTL_INIT 1024
    !insertmacro UMUI_PAGECTLLIGHT_INIT 1020

    !ifdef MUI_DIRECTORYPAGE_BGCOLOR
      !insertmacro MUI_DEFAULT MUI_DIRECTORYPAGE_TEXTCOLOR ""
      FindWindow $MUI_TEMP1 "#32770" "" $HWNDPARENT
      GetDlgItem $MUI_TEMP1 $MUI_TEMP1 1019
      SetCtlColors $MUI_TEMP1 "${MUI_DIRECTORYPAGE_TEXTCOLOR}" "${MUI_DIRECTORYPAGE_BGCOLOR}"
    !else
      !insertmacro UMUI_PAGEINPUTCTL_INIT 1019
    !endif

    !insertmacro MUI_PAGE_FUNCTION_CUSTOM SHOW

  FunctionEnd

  Function "${LEAVE}"

    !insertmacro MUI_PAGE_FUNCTION_CUSTOM LEAVE

  FunctionEnd

!macroend

!macro MUI_FUNCTION_STARTMENUPAGE PRE LEAVE

  Function "${PRE}"

    !ifdef MUI_STARTMENUPAGE_REGISTRY_VALUENAME
      StrCmp "${MUI_STARTMENUPAGE_VARIABLE}" "" 0 +4

        ReadRegStr $MUI_TEMP1 ${MUI_STARTMENUPAGE_REGISTRY_ROOT} "${MUI_STARTMENUPAGE_REGISTRY_KEY}" "${MUI_STARTMENUPAGE_REGISTRY_VALUENAME}"

        StrCmp $MUI_TEMP1 "" +2
          StrCpy "${MUI_STARTMENUPAGE_VARIABLE}" $MUI_TEMP1

    !endif

    ; IF setup cancelled or steuptype complete
    !insertmacro UMUI_ABORT_IF_INSTALLFLAG_IS ${UMUI_CANCELLED}|${UMUI_MINIMAL}|${UMUI_STANDARD}|${UMUI_COMPLETE}|${UMUI_MODIFY}|${UMUI_REPAIR}|${UMUI_UPDATE}

    !insertmacro UMUI_UMUI_HIDEBACKBUTTON

    !insertmacro MUI_PAGE_FUNCTION_CUSTOM PRE

    !insertmacro MUI_HEADER_TEXT_PAGE $(MUI_TEXT_STARTMENU_TITLE) $(MUI_TEXT_STARTMENU_SUBTITLE)

    StrCmp $(^RTL) 0 mui.startmenu_nortl
      !ifndef MUI_STARTMENUPAGE_NODISABLE
         StartMenu::Init /rtl /noicon /autoadd /text "${MUI_STARTMENUPAGE_TEXT_TOP}" /lastused "${MUI_STARTMENUPAGE_VARIABLE}" /checknoshortcuts "${MUI_STARTMENUPAGE_TEXT_CHECKBOX}" "${MUI_STARTMENUPAGE_DEFAULTFOLDER}"
      !else
         StartMenu::Init /rtl /noicon /autoadd /text "${MUI_STARTMENUPAGE_TEXT_TOP}" /lastused "${MUI_STARTMENUPAGE_VARIABLE}" "${MUI_STARTMENUPAGE_DEFAULTFOLDER}"
      !endif
      Goto mui.startmenu_initdone
    mui.startmenu_nortl:
       !ifndef MUI_STARTMENUPAGE_NODISABLE
         StartMenu::Init /noicon /autoadd /text "${MUI_STARTMENUPAGE_TEXT_TOP}" /lastused "${MUI_STARTMENUPAGE_VARIABLE}" /checknoshortcuts "${MUI_STARTMENUPAGE_TEXT_CHECKBOX}" "${MUI_STARTMENUPAGE_DEFAULTFOLDER}"
       !else
         StartMenu::Init /noicon /autoadd /text "${MUI_STARTMENUPAGE_TEXT_TOP}" /lastused "${MUI_STARTMENUPAGE_VARIABLE}" "${MUI_STARTMENUPAGE_DEFAULTFOLDER}"
       !endif
    mui.startmenu_initdone:

    Pop $MUI_HWND

    !insertmacro MUI_PAGE_FUNCTION_CUSTOM SHOW

!ifndef USE_MUIEx
;-----------------

    !insertmacro UMUI_IOPAGEBG_INIT $MUI_HWND

    GetDlgItem $MUI_TEMP1 $MUI_HWND 1003
    !insertmacro UMUI_IOPAGECTL_INIT $MUI_TEMP1
    GetDlgItem $MUI_TEMP1 $MUI_HWND 1005
    !insertmacro UMUI_IOPAGECTL_INIT $MUI_TEMP1

!endif
;-----

    !ifdef MUI_STARTMENUPAGE_BGCOLOR
      !insertmacro MUI_DEFAULT MUI_STARTMENUPAGE_TEXTCOLOR ""
      GetDlgItem $MUI_TEMP1 $MUI_HWND 1002
      SetCtlColors $MUI_TEMP1 "${MUI_STARTMENUPAGE_TEXTCOLOR}" "${MUI_STARTMENUPAGE_BGCOLOR}"
      GetDlgItem $MUI_TEMP1 $MUI_HWND 1004
      SetCtlColors $MUI_TEMP1 "${MUI_STARTMENUPAGE_TEXTCOLOR}" "${MUI_STARTMENUPAGE_BGCOLOR}"
    !else
      GetDlgItem $MUI_TEMP1 $MUI_HWND 1002
      !insertmacro UMUI_IOPAGEINPUTCTL_INIT $MUI_TEMP1
      GetDlgItem $MUI_TEMP1 $MUI_HWND 1004
      !insertmacro UMUI_IOPAGEINPUTCTL_INIT $MUI_TEMP1
    !endif

    StartMenu::Show
    !insertmacro MUI_PAGE_FUNCTION_CUSTOM DESTROYED

    Pop $MUI_TEMP1
    StrCmp $MUI_TEMP1 "success" 0 +2
      Pop "${MUI_STARTMENUPAGE_VARIABLE}"

    !insertmacro UMUI_FIX_BUTTONS_SKIN

  FunctionEnd

  Function "${LEAVE}"

    !ifdef MUI_STARTMENUPAGE_REGISTRY_VALUENAME
      !insertmacro UMUI_ADDPARAMTOSAVETOREGISTRYKEY ${MUI_STARTMENUPAGE_REGISTRY_ROOT} "${MUI_STARTMENUPAGE_REGISTRY_KEY}" "${MUI_STARTMENUPAGE_REGISTRY_VALUENAME}" "${MUI_STARTMENUPAGE_VARIABLE}"
    !endif

    !insertmacro MUI_PAGE_FUNCTION_CUSTOM LEAVE

  FunctionEnd

!macroend


!macro MUI_FUNCTION_INSTFILESPAGE PRE SHOW LEAVE

  !ifdef UMUI_INSTFILEPAGE_ENABLE_CANCEL_BUTTON
    !ifndef UMUI_NB_CALL_FUNCTION_CANCEL_DEFINED
      !define UMUI_NB_CALL_FUNCTION_CANCEL_DEFINED
      Var UMUI_NB_CALL_FUNCTION_CANCEL
    !endif
  !endif

  Function "${PRE}"

    ;IF setup is cancelled
    !insertmacro UMUI_IF_INSTALLFLAG_IS ${UMUI_CANCELLED}
      SetAutoClose true
    !insertmacro UMUI_ENDIF_INSTALLFLAG
    !insertmacro UMUI_ABORT_IF_INSTALLFLAG_IS ${UMUI_CANCELLED}

    !insertmacro MUI_PAGE_FUNCTION_CUSTOM PRE

    !insertmacro MUI_HEADER_TEXT_PAGE $(MUI_${MUI_PAGE_UNINSTALLER_PREFIX}TEXT_${MUI_PAGE_UNINSTALLER_PREFIX}INSTALLING_TITLE) $(MUI_${MUI_PAGE_UNINSTALLER_PREFIX}TEXT_${MUI_PAGE_UNINSTALLER_PREFIX}INSTALLING_SUBTITLE)

    !ifdef UMUI_INSTALLDIR_REGISTRY_VALUENAME
      !insertmacro UMUI_ADDPARAMTOSAVETOREGISTRYKEY ${UMUI_INSTALLDIR_REGISTRY_ROOT} "${UMUI_INSTALLDIR_REGISTRY_KEY}" "${UMUI_INSTALLDIR_REGISTRY_VALUENAME}" $INSTDIR
    !endif

    !insertmacro UMUI_FIX_BUTTONS_SKIN

  FunctionEnd

  Function "${SHOW}"

    !insertmacro UMUI_UMUI_HIDEBACKBUTTON

    !insertmacro UMUI_PAGEBGTRANSPARENT_INIT
    !insertmacro UMUI_PAGECTLTRANSPARENT_INIT 1027
    !insertmacro UMUI_PAGECTL_INIT 1006
    !insertmacro UMUI_PAGECTLLIGHT_INIT 1004

    !ifdef UMUI_INSTFILEPAGE_ENABLE_CANCEL_BUTTON
      StrCpy $UMUI_NB_CALL_FUNCTION_CANCEL 0
      GetDlgItem $MUI_TEMP1 $HWNDPARENT 2
      EnableWindow $MUI_TEMP1 1
    !endif

    !insertmacro MUI_PAGE_FUNCTION_CUSTOM SHOW

  FunctionEnd

  Function "${LEAVE}"

    IfAbort 0 noabort
      !insertmacro UMUI_SET_INSTALLFLAG ${UMUI_CANCELLED}
    noabort:

    !ifdef UMUI_INSTFILEPAGE_ENABLE_CANCEL_BUTTON
      !insertmacro UMUI_IF_INSTALLFLAG_IS ${UMUI_CANCELLED}
        StrCmp $UMUI_NB_CALL_FUNCTION_CANCEL 0 0 +3
          StrCpy $UMUI_NB_CALL_FUNCTION_CANCEL 1
          Call ${UMUI_INSTFILEPAGE_ENABLE_CANCEL_BUTTON}
      !insertmacro UMUI_ENDIF_INSTALLFLAG
    !endif

    !insertmacro MUI_UNSET UMUI_INSTFILEPAGE_ENABLE_CANCEL_BUTTON

    !insertmacro MUI_PAGE_FUNCTION_CUSTOM LEAVE

    !insertmacro UMUI_ADDSHELLVARCONTEXTTOSAVETOREGISTRY

    ; Save paths
    !insertmacro UMUI_IF_INSTALLFLAG_ISNOT ${UMUI_CANCELLED}
      StrCmp ${MUI_PAGE_UNINSTALLER_PREFIX} "" 0 endPathSave
        !insertmacro UMUI_PATH_SAVE
      endPathSave:
    !insertmacro UMUI_ENDIF_INSTALLFLAG

    ;Save all parameters
    !insertmacro UMUI_SAVEPARAMSTOREGISTRY

    !ifdef MUI_UNFINISHPAGE_NOAUTOCLOSE
      !insertmacro MUI_ENDHEADER
    !endif

  FunctionEnd

!ifndef USE_MUIEx
;-----------------

  ;This is a workaround for the background of the progress bar that wasn't drawn properly with background image
  !ifdef UMUI_${MUI_PAGE_UNINSTALLER_PREFIX}PAGEBGIMAGE
    !ifndef UMUI_${MUI_PAGE_UNINSTALLER_PREFIX}SECTION_WORKAROUND_INSERTED
      !define UMUI_${MUI_PAGE_UNINSTALLER_PREFIX}SECTION_WORKAROUND_INSERTED

      Section "${MUI_PAGE_UNINSTALLER_FUNCPREFIX}"
        SetDetailsPrint none

        FindWindow $MUI_TEMP1 "#32770" "" $HWNDPARENT
        GetDlgItem $MUI_TEMP1 $MUI_TEMP1 1004

        System::Call "user32::InvalidateRect(i,i,i)i ($MUI_TEMP1, 0, 1)"

        SetDetailsPrint both
      SectionEnd

    !endif
  !endif

!endif
;-----------------

  !ifndef MUI_UNINSTALLER
    !ifdef UMUI_PREUNINSTALL_FUNCTION

      !ifndef UMUI_SECTION_PREUNINSTALL
        !define UMUI_SECTION_PREUNINSTALL

        Section ""
          ClearErrors
          IfFileExists $INSTDIR 0 end

            Call "${UMUI_PREUNINSTALL_FUNCTION}"

          end:
          ClearErrors
        SectionEnd

      !endif

    !endif
  !endif

!macroend

!macro MUI_FUNCTION_FINISHPAGE PRE LEAVE

  !ifndef UMUI_WELCOMEFINISHABORTPAGE_USE_IMAGE
    !define UMUI_INTERNAL_FNUMFIELDS_3ADDITIONALCONTROLS 5
    !define UMUI_INTERNAL_FNUMFIELDS_2ADDITIONALCONTROLS 4
    !define UMUI_INTERNAL_FNUMFIELDS_1ADDITIONALCONTROLS 3
    !define UMUI_INTERNAL_FIELDTITLE 1
    !define UMUI_INTERNAL_FIELDTEXT 2
    !define UMUI_INTERNAL_FIELDTHIRD 3
    !define UMUI_INTERNAL_FIELDFOURTH 4
    !define UMUI_INTERNAL_FIELDFIFTH 5
    !define UMUI_INTERNAL_FIDTITLE 1200
    !define UMUI_INTERNAL_FIDTEXT 1201
    !define UMUI_INTERNAL_FIDTHIRD 1202
    !define UMUI_INTERNAL_FIDFOURTH 1203
    !define UMUI_INTERNAL_FIDFIFTH 1204
    !define UMUI_INTERNAL_FPOSLINKLEFT 22
    !define UMUI_INTERNAL_FOPTIONCHECKLEFT 26
  !else
    !define UMUI_INTERNAL_FNUMFIELDS_3ADDITIONALCONTROLS 6
    !define UMUI_INTERNAL_FNUMFIELDS_2ADDITIONALCONTROLS 5
    !define UMUI_INTERNAL_FNUMFIELDS_1ADDITIONALCONTROLS 4
    !define UMUI_INTERNAL_FIELDTITLE 2
    !define UMUI_INTERNAL_FIELDTEXT 3
    !define UMUI_INTERNAL_FIELDTHIRD 4
    !define UMUI_INTERNAL_FIELDFOURTH 5
    !define UMUI_INTERNAL_FIELDFIFTH 6
    !define UMUI_INTERNAL_FIDTITLE 1201
    !define UMUI_INTERNAL_FIDTEXT 1202
    !define UMUI_INTERNAL_FIDTHIRD 1203
    !define UMUI_INTERNAL_FIDFOURTH 1204
    !define UMUI_INTERNAL_FIDFIFTH 1205
    !define UMUI_INTERNAL_FPOSLINKLEFT 130
    !define UMUI_INTERNAL_FOPTIONCHECKLEFT 134
  !endif

  Function "${PRE}"

    ; IF setup cancelled
    !insertmacro UMUI_ABORT_IF_INSTALLFLAG_IS ${UMUI_CANCELLED}

    !insertmacro MUI_HEADER_TEXT_PAGE "" ""

    !insertmacro MUI_WELCOMEFINISHPAGE_FUNCTION_CUSTOM


    !insertmacro INSTALLOPTIONS_WRITE "ioSpecial.ini" "Settings" "NextButtonText" "${MUI_FINISHPAGE_BUTTON}"

    !ifdef MUI_FINISHPAGE_CANCEL_ENABLED
      !insertmacro INSTALLOPTIONS_WRITE "ioSpecial.ini" "Settings" "CancelEnabled" "1"
    !endif


    !insertmacro MUI_INSTALLOPTIONS_WRITE_DEFAULTCONVERT "ioSpecial.ini" "Field ${UMUI_INTERNAL_FIELDTITLE}" "Text" "MUI_FINISHPAGE_TITLE"

    !ifndef UMUI_USE_${MUI_PAGE_UNINSTALLER_PREFIX}ALTERNATE_PAGE
      !ifndef MUI_FINISHPAGE_TITLE_3LINES
        !insertmacro INSTALLOPTIONS_WRITE "ioSpecial.ini" "Field ${UMUI_INTERNAL_FIELDTITLE}" "Bottom" "38"
        !insertmacro INSTALLOPTIONS_WRITE "ioSpecial.ini" "Field ${UMUI_INTERNAL_FIELDTEXT}" "Top" "45"
      !else
        !insertmacro INSTALLOPTIONS_WRITE "ioSpecial.ini" "Field ${UMUI_INTERNAL_FIELDTITLE}" "Bottom" "48"
        !insertmacro INSTALLOPTIONS_WRITE "ioSpecial.ini" "Field ${UMUI_INTERNAL_FIELDTEXT}" "Top" "55"
      !endif
    !endif

    !ifdef MUI_FINISHPAGE_RUN | MUI_FINISHPAGE_SHOWREADME
      !ifndef UMUI_USE_${MUI_PAGE_UNINSTALLER_PREFIX}ALTERNATE_PAGE
        !ifndef MUI_FINISHPAGE_TITLE_3LINES
          !ifndef MUI_FINISHPAGE_TEXT_LARGE
            !insertmacro INSTALLOPTIONS_WRITE "ioSpecial.ini" "Field ${UMUI_INTERNAL_FIELDTEXT}" "Bottom" "85"
          !else
            !insertmacro INSTALLOPTIONS_WRITE "ioSpecial.ini" "Field ${UMUI_INTERNAL_FIELDTEXT}" "Bottom" "115"
          !endif
        !else
          !ifndef MUI_FINISHPAGE_TEXT_LARGE
            !insertmacro INSTALLOPTIONS_WRITE "ioSpecial.ini" "Field ${UMUI_INTERNAL_FIELDTEXT}" "Bottom" "95"
          !else
            !insertmacro INSTALLOPTIONS_WRITE "ioSpecial.ini" "Field ${UMUI_INTERNAL_FIELDTEXT}" "Bottom" "125"
          !endif
        !endif
      !else
        !ifndef MUI_FINISHPAGE_TEXT_LARGE
          !insertmacro INSTALLOPTIONS_WRITE "ioSpecial.ini" "Field ${UMUI_INTERNAL_FIELDTEXT}" "Bottom" "124"
        !else
          !insertmacro INSTALLOPTIONS_WRITE "ioSpecial.ini" "Field ${UMUI_INTERNAL_FIELDTEXT}" "Bottom" "139"
        !endif
      !endif
    !else
      !ifndef MUI_FINISHPAGE_LINK
        !insertmacro INSTALLOPTIONS_WRITE "ioSpecial.ini" "Field ${UMUI_INTERNAL_FIELDTEXT}" "Bottom" "-1"
      !else
        !insertmacro INSTALLOPTIONS_WRITE "ioSpecial.ini" "Field ${UMUI_INTERNAL_FIELDTEXT}" "Bottom" "-15"
      !endif
    !endif

    !ifndef MUI_FINISHPAGE_NOREBOOTSUPPORT

      IfRebootFlag 0 mui.finish_noreboot_init

      !ifndef UMUI_USE_${MUI_PAGE_UNINSTALLER_PREFIX}ALTERNATE_PAGE
        !ifndef MUI_FINISHPAGE_TITLE_3LINES
          !ifndef MUI_FINISHPAGE_TEXT_LARGE
            !insertmacro INSTALLOPTIONS_WRITE "ioSpecial.ini" "Field ${UMUI_INTERNAL_FIELDTEXT}" "Bottom" "85"
          !else
            !insertmacro INSTALLOPTIONS_WRITE "ioSpecial.ini" "Field ${UMUI_INTERNAL_FIELDTEXT}" "Bottom" "115"
          !endif
        !else
          !ifndef MUI_FINISHPAGE_TEXT_LARGE
            !insertmacro INSTALLOPTIONS_WRITE "ioSpecial.ini" "Field ${UMUI_INTERNAL_FIELDTEXT}" "Bottom" "95"
          !else
            !insertmacro INSTALLOPTIONS_WRITE "ioSpecial.ini" "Field ${UMUI_INTERNAL_FIELDTEXT}" "Bottom" "125"
          !endif
        !endif
      !else
        !ifndef MUI_FINISHPAGE_TEXT_LARGE
          !insertmacro INSTALLOPTIONS_WRITE "ioSpecial.ini" "Field ${UMUI_INTERNAL_FIELDTEXT}" "Bottom" "124"
        !else
          !insertmacro INSTALLOPTIONS_WRITE "ioSpecial.ini" "Field ${UMUI_INTERNAL_FIELDTEXT}" "Bottom" "151"
        !endif
      !endif

      !insertmacro MUI_INSTALLOPTIONS_WRITE_DEFAULTCONVERT "ioSpecial.ini" "Field ${UMUI_INTERNAL_FIELDTEXT}" "Text" "MUI_FINISHPAGE_TEXT_REBOOT"

      !insertmacro INSTALLOPTIONS_WRITE "ioSpecial.ini" "Settings" "Numfields" "${UMUI_INTERNAL_FNUMFIELDS_2ADDITIONALCONTROLS}"

      !insertmacro INSTALLOPTIONS_WRITE "ioSpecial.ini" "Field ${UMUI_INTERNAL_FIELDTHIRD}" "Type" "RadioButton"
      !insertmacro MUI_INSTALLOPTIONS_WRITE_DEFAULTCONVERT "ioSpecial.ini" "Field ${UMUI_INTERNAL_FIELDTHIRD}" "Text" "MUI_FINISHPAGE_TEXT_REBOOTNOW"
      !insertmacro INSTALLOPTIONS_WRITE "ioSpecial.ini" "Field ${UMUI_INTERNAL_FIELDTHIRD}" "Left" "${UMUI_INTERNAL_FOPTIONCHECKLEFT}"
      !insertmacro INSTALLOPTIONS_WRITE "ioSpecial.ini" "Field ${UMUI_INTERNAL_FIELDTHIRD}" "Right" "-15"

      !ifndef UMUI_USE_${MUI_PAGE_UNINSTALLER_PREFIX}ALTERNATE_PAGE
        !ifndef MUI_FINISHPAGE_TITLE_3LINES
          !ifndef MUI_FINISHPAGE_TEXT_LARGE
            !insertmacro INSTALLOPTIONS_WRITE "ioSpecial.ini" "Field ${UMUI_INTERNAL_FIELDTHIRD}" "Top" "90"
            !insertmacro INSTALLOPTIONS_WRITE "ioSpecial.ini" "Field ${UMUI_INTERNAL_FIELDTHIRD}" "Bottom" "100"
          !else
            !insertmacro INSTALLOPTIONS_WRITE "ioSpecial.ini" "Field ${UMUI_INTERNAL_FIELDTHIRD}" "Top" "120"
            !insertmacro INSTALLOPTIONS_WRITE "ioSpecial.ini" "Field ${UMUI_INTERNAL_FIELDTHIRD}" "Bottom" "130"
          !endif
        !else
          !ifndef MUI_FINISHPAGE_TEXT_LARGE
            !insertmacro INSTALLOPTIONS_WRITE "ioSpecial.ini" "Field ${UMUI_INTERNAL_FIELDTHIRD}" "Top" "100"
            !insertmacro INSTALLOPTIONS_WRITE "ioSpecial.ini" "Field ${UMUI_INTERNAL_FIELDTHIRD}" "Bottom" "110"
          !else
            !insertmacro INSTALLOPTIONS_WRITE "ioSpecial.ini" "Field ${UMUI_INTERNAL_FIELDTHIRD}" "Top" "130"
            !insertmacro INSTALLOPTIONS_WRITE "ioSpecial.ini" "Field ${UMUI_INTERNAL_FIELDTHIRD}" "Bottom" "140"
          !endif
        !endif
      !else
        !ifndef MUI_FINISHPAGE_TEXT_LARGE
          !insertmacro INSTALLOPTIONS_WRITE "ioSpecial.ini" "Field ${UMUI_INTERNAL_FIELDTHIRD}" "Top" "129"
          !insertmacro INSTALLOPTIONS_WRITE "ioSpecial.ini" "Field ${UMUI_INTERNAL_FIELDTHIRD}" "Bottom" "139"
        !else
          !insertmacro INSTALLOPTIONS_WRITE "ioSpecial.ini" "Field ${UMUI_INTERNAL_FIELDTHIRD}" "Top" "159"
          !insertmacro INSTALLOPTIONS_WRITE "ioSpecial.ini" "Field ${UMUI_INTERNAL_FIELDTHIRD}" "Bottom" "169"
        !endif
      !endif

      !insertmacro INSTALLOPTIONS_WRITE "ioSpecial.ini" "Field ${UMUI_INTERNAL_FIELDFOURTH}" "Type" "RadioButton"
      !insertmacro MUI_INSTALLOPTIONS_WRITE_DEFAULTCONVERT "ioSpecial.ini" "Field ${UMUI_INTERNAL_FIELDFOURTH}" "Text" "MUI_FINISHPAGE_TEXT_REBOOTLATER"
      !insertmacro INSTALLOPTIONS_WRITE "ioSpecial.ini" "Field ${UMUI_INTERNAL_FIELDFOURTH}" "Left" "${UMUI_INTERNAL_FOPTIONCHECKLEFT}"
      !insertmacro INSTALLOPTIONS_WRITE "ioSpecial.ini" "Field ${UMUI_INTERNAL_FIELDFOURTH}" "Right" "-15"

      !ifdef MUI_FINISHPAGE_REBOOTLATER_DEFAULT
        !insertmacro INSTALLOPTIONS_WRITE "ioSpecial.ini" "Field ${UMUI_INTERNAL_FIELDTHIRD}" "State" "0"
        !insertmacro INSTALLOPTIONS_WRITE "ioSpecial.ini" "Field ${UMUI_INTERNAL_FIELDFOURTH}" "State" "1"
      !else
        !insertmacro INSTALLOPTIONS_WRITE "ioSpecial.ini" "Field ${UMUI_INTERNAL_FIELDTHIRD}" "State" "1"
        !insertmacro INSTALLOPTIONS_WRITE "ioSpecial.ini" "Field ${UMUI_INTERNAL_FIELDFOURTH}" "State" "0"
      !endif

      !ifndef UMUI_USE_${MUI_PAGE_UNINSTALLER_PREFIX}ALTERNATE_PAGE
        !ifndef MUI_FINISHPAGE_TITLE_3LINES
          !insertmacro INSTALLOPTIONS_WRITE "ioSpecial.ini" "Field ${UMUI_INTERNAL_FIELDFOURTH}" "Top" "110"
          !insertmacro INSTALLOPTIONS_WRITE "ioSpecial.ini" "Field ${UMUI_INTERNAL_FIELDFOURTH}" "Bottom" "120"
        !else
          !insertmacro INSTALLOPTIONS_WRITE "ioSpecial.ini" "Field ${UMUI_INTERNAL_FIELDFOURTH}" "Top" "110"
          !insertmacro INSTALLOPTIONS_WRITE "ioSpecial.ini" "Field ${UMUI_INTERNAL_FIELDFOURTH}" "Bottom" "120"
        !endif
      !else
        !insertmacro INSTALLOPTIONS_WRITE "ioSpecial.ini" "Field ${UMUI_INTERNAL_FIELDFOURTH}" "Top" "149"
        !insertmacro INSTALLOPTIONS_WRITE "ioSpecial.ini" "Field ${UMUI_INTERNAL_FIELDFOURTH}" "Bottom" "159"
      !endif

        Goto mui.finish_load

      mui.finish_noreboot_init:

    !endif

    !insertmacro MUI_INSTALLOPTIONS_WRITE_DEFAULTCONVERT "ioSpecial.ini" "Field ${UMUI_INTERNAL_FIELDTEXT}" "Text" "MUI_FINISHPAGE_TEXT"

    !ifdef MUI_FINISHPAGE_RUN

      !insertmacro INSTALLOPTIONS_WRITE "ioSpecial.ini" "Field ${UMUI_INTERNAL_FIELDTHIRD}" "Type" "CheckBox"
      !insertmacro MUI_INSTALLOPTIONS_WRITE_DEFAULTCONVERT "ioSpecial.ini" "Field ${UMUI_INTERNAL_FIELDTHIRD}" "Text" "MUI_FINISHPAGE_RUN_TEXT"
      !insertmacro INSTALLOPTIONS_WRITE "ioSpecial.ini" "Field ${UMUI_INTERNAL_FIELDTHIRD}" "Left" "${UMUI_INTERNAL_FOPTIONCHECKLEFT}"
      !insertmacro INSTALLOPTIONS_WRITE "ioSpecial.ini" "Field ${UMUI_INTERNAL_FIELDTHIRD}" "Right" "-15"

      !ifndef UMUI_USE_${MUI_PAGE_UNINSTALLER_PREFIX}ALTERNATE_PAGE
        !ifndef MUI_FINISHPAGE_TITLE_3LINES
          !ifndef MUI_FINISHPAGE_TEXT_LARGE
            !insertmacro INSTALLOPTIONS_WRITE "ioSpecial.ini" "Field ${UMUI_INTERNAL_FIELDTHIRD}" "Top" "90"
            !insertmacro INSTALLOPTIONS_WRITE "ioSpecial.ini" "Field ${UMUI_INTERNAL_FIELDTHIRD}" "Bottom" "100"
          !else
            !insertmacro INSTALLOPTIONS_WRITE "ioSpecial.ini" "Field ${UMUI_INTERNAL_FIELDTHIRD}" "Top" "120"
            !insertmacro INSTALLOPTIONS_WRITE "ioSpecial.ini" "Field ${UMUI_INTERNAL_FIELDTHIRD}" "Bottom" "130"
          !endif
        !else
          !ifndef MUI_FINISHPAGE_TEXT_LARGE
            !insertmacro INSTALLOPTIONS_WRITE "ioSpecial.ini" "Field ${UMUI_INTERNAL_FIELDTHIRD}" "Top" "100"
            !insertmacro INSTALLOPTIONS_WRITE "ioSpecial.ini" "Field ${UMUI_INTERNAL_FIELDTHIRD}" "Bottom" "110"
          !else
            !insertmacro INSTALLOPTIONS_WRITE "ioSpecial.ini" "Field ${UMUI_INTERNAL_FIELDTHIRD}" "Top" "130"
            !insertmacro INSTALLOPTIONS_WRITE "ioSpecial.ini" "Field ${UMUI_INTERNAL_FIELDTHIRD}" "Bottom" "140"
          !endif
        !endif
      !else
        !ifndef MUI_FINISHPAGE_TEXT_LARGE
          !insertmacro INSTALLOPTIONS_WRITE "ioSpecial.ini" "Field ${UMUI_INTERNAL_FIELDTHIRD}" "Top" "129"
          !insertmacro INSTALLOPTIONS_WRITE "ioSpecial.ini" "Field ${UMUI_INTERNAL_FIELDTHIRD}" "Bottom" "139"
        !else
          !insertmacro INSTALLOPTIONS_WRITE "ioSpecial.ini" "Field ${UMUI_INTERNAL_FIELDTHIRD}" "Top" "139"
          !insertmacro INSTALLOPTIONS_WRITE "ioSpecial.ini" "Field ${UMUI_INTERNAL_FIELDTHIRD}" "Bottom" "149"
        !endif
      !endif

      !ifndef MUI_FINISHPAGE_RUN_NOTCHECKED
        !insertmacro INSTALLOPTIONS_WRITE "ioSpecial.ini" "Field ${UMUI_INTERNAL_FIELDTHIRD}" "State" "1"
      !endif

    !endif


    !ifdef MUI_FINISHPAGE_SHOWREADME

      !ifdef MUI_FINISHPAGE_CURFIELD_NO
        !undef MUI_FINISHPAGE_CURFIELD_NO
      !endif

      !ifndef MUI_FINISHPAGE_RUN
        !define MUI_FINISHPAGE_CURFIELD_NO ${UMUI_INTERNAL_FIELDTHIRD}

        !ifndef UMUI_USE_${MUI_PAGE_UNINSTALLER_PREFIX}ALTERNATE_PAGE
          !ifndef MUI_FINISHPAGE_TITLE_3LINES
            !ifndef MUI_FINISHPAGE_TEXT_LARGE
              !define MUI_FINISHPAGE_CURFIELD_TOP 90
              !define MUI_FINISHPAGE_CURFIELD_BOTTOM 100
            !else
              !define MUI_FINISHPAGE_CURFIELD_TOP 120
              !define MUI_FINISHPAGE_CURFIELD_BOTTOM 130
            !endif
          !else
            !ifndef MUI_FINISHPAGE_TEXT_LARGE
              !define MUI_FINISHPAGE_CURFIELD_TOP 100
              !define MUI_FINISHPAGE_CURFIELD_BOTTOM 110
            !else
              !define MUI_FINISHPAGE_CURFIELD_TOP 130
              !define MUI_FINISHPAGE_CURFIELD_BOTTOM 140
            !endif
          !endif
        !else
          !ifndef MUI_FINISHPAGE_TEXT_LARGE
            !define MUI_FINISHPAGE_CURFIELD_TOP 144
            !define MUI_FINISHPAGE_CURFIELD_BOTTOM 159
          !else
            !define MUI_FINISHPAGE_CURFIELD_TOP 174
            !define MUI_FINISHPAGE_CURFIELD_BOTTOM 189
          !endif
        !endif
      ; finishpagerun
      !else
        !define MUI_FINISHPAGE_CURFIELD_NO ${UMUI_INTERNAL_FIELDFOURTH}

        !ifndef UMUI_USE_${MUI_PAGE_UNINSTALLER_PREFIX}ALTERNATE_PAGE
          !ifndef MUI_FINISHPAGE_TITLE_3LINES
            !ifndef MUI_FINISHPAGE_TEXT_LARGE
              !define MUI_FINISHPAGE_CURFIELD_TOP 110
              !define MUI_FINISHPAGE_CURFIELD_BOTTOM 120
            !else
              !define MUI_FINISHPAGE_CURFIELD_TOP 140
              !define MUI_FINISHPAGE_CURFIELD_BOTTOM 150
            !endif
          !else
            !ifndef MUI_FINISHPAGE_TEXT_LARGE
              !define MUI_FINISHPAGE_CURFIELD_TOP 120
              !define MUI_FINISHPAGE_CURFIELD_BOTTOM 130
            !else
              !define MUI_FINISHPAGE_CURFIELD_TOP 150
              !define MUI_FINISHPAGE_CURFIELD_BOTTOM 160
            !endif
          !endif
        !else
          !ifndef MUI_FINISHPAGE_TEXT_LARGE
            !define MUI_FINISHPAGE_CURFIELD_TOP 150
            !define MUI_FINISHPAGE_CURFIELD_BOTTOM 160
          !else
            !define MUI_FINISHPAGE_CURFIELD_TOP 160
            !define MUI_FINISHPAGE_CURFIELD_BOTTOM 170
          !endif
        !endif
      !endif


      !insertmacro INSTALLOPTIONS_WRITE "ioSpecial.ini" "Field ${MUI_FINISHPAGE_CURFIELD_NO}" "Type" "CheckBox"
      !insertmacro MUI_INSTALLOPTIONS_WRITE_DEFAULTCONVERT "ioSpecial.ini" "Field ${MUI_FINISHPAGE_CURFIELD_NO}" "Text" "MUI_FINISHPAGE_SHOWREADME_TEXT"
      !insertmacro INSTALLOPTIONS_WRITE "ioSpecial.ini" "Field ${MUI_FINISHPAGE_CURFIELD_NO}" "Left" "${UMUI_INTERNAL_FOPTIONCHECKLEFT}"
      !insertmacro INSTALLOPTIONS_WRITE "ioSpecial.ini" "Field ${MUI_FINISHPAGE_CURFIELD_NO}" "Right" "-15"
      !insertmacro INSTALLOPTIONS_WRITE "ioSpecial.ini" "Field ${MUI_FINISHPAGE_CURFIELD_NO}" "Top" "${MUI_FINISHPAGE_CURFIELD_TOP}"
      !insertmacro INSTALLOPTIONS_WRITE "ioSpecial.ini" "Field ${MUI_FINISHPAGE_CURFIELD_NO}" "Bottom" "${MUI_FINISHPAGE_CURFIELD_BOTTOM}"
      !ifndef MUI_FINISHPAGE_SHOWREADME_NOTCHECKED
         !insertmacro INSTALLOPTIONS_WRITE "ioSpecial.ini" "Field ${MUI_FINISHPAGE_CURFIELD_NO}" "State" "1"
      !endif

    !endif

    !ifdef MUI_FINISHPAGE_LINK

      !ifdef MUI_FINISHPAGE_CURFIELD_NO
        !undef MUI_FINISHPAGE_CURFIELD_NO
      !endif

      !ifdef MUI_FINISHPAGE_RUN & MUI_FINISHPAGE_SHOWREADME
        !define MUI_FINISHPAGE_CURFIELD_NO ${UMUI_INTERNAL_FIELDFIFTH}
      !else ifdef MUI_FINISHPAGE_RUN | MUI_FINISHPAGE_SHOWREADME
        !define MUI_FINISHPAGE_CURFIELD_NO ${UMUI_INTERNAL_FIELDFOURTH}
      !else
        !define MUI_FINISHPAGE_CURFIELD_NO ${UMUI_INTERNAL_FIELDTHIRD}
      !endif

      !insertmacro INSTALLOPTIONS_WRITE "ioSpecial.ini" "Field ${MUI_FINISHPAGE_CURFIELD_NO}" "Type" "Link"
      !insertmacro MUI_INSTALLOPTIONS_WRITE_DEFAULTCONVERT "ioSpecial.ini" "Field ${MUI_FINISHPAGE_CURFIELD_NO}" "Text" "MUI_FINISHPAGE_LINK"
      !insertmacro INSTALLOPTIONS_WRITE "ioSpecial.ini" "Field ${MUI_FINISHPAGE_CURFIELD_NO}" "Left" "${UMUI_INTERNAL_FPOSLINKLEFT}"
      !insertmacro INSTALLOPTIONS_WRITE "ioSpecial.ini" "Field ${MUI_FINISHPAGE_CURFIELD_NO}" "Right" "-15"
      !insertmacro INSTALLOPTIONS_WRITE "ioSpecial.ini" "Field ${MUI_FINISHPAGE_CURFIELD_NO}" "Top" "-14"
      !insertmacro INSTALLOPTIONS_WRITE "ioSpecial.ini" "Field ${MUI_FINISHPAGE_CURFIELD_NO}" "Bottom" "-5"
      !insertmacro MUI_INSTALLOPTIONS_WRITE_DEFAULTCONVERT "ioSpecial.ini" "Field ${MUI_FINISHPAGE_CURFIELD_NO}" "State" "MUI_FINISHPAGE_LINK_LOCATION"

    !endif


    !ifdef MUI_FINISHPAGE_RUN & MUI_FINISHPAGE_SHOWREADME & MUI_FINISHPAGE_LINK
      !insertmacro INSTALLOPTIONS_WRITE "ioSpecial.ini" "Settings" "Numfields" "${UMUI_INTERNAL_FNUMFIELDS_3ADDITIONALCONTROLS}"
    !else ifdef MUI_FINISHPAGE_RUN & MUI_FINISHPAGE_SHOWREADME
      !insertmacro INSTALLOPTIONS_WRITE "ioSpecial.ini" "Settings" "Numfields" "${UMUI_INTERNAL_FNUMFIELDS_2ADDITIONALCONTROLS}"
    !else ifdef MUI_FINISHPAGE_RUN & MUI_FINISHPAGE_LINK
      !insertmacro INSTALLOPTIONS_WRITE "ioSpecial.ini" "Settings" "Numfields" "${UMUI_INTERNAL_FNUMFIELDS_2ADDITIONALCONTROLS}"
    !else ifdef MUI_FINISHPAGE_SHOWREADME & MUI_FINISHPAGE_LINK
      !insertmacro INSTALLOPTIONS_WRITE "ioSpecial.ini" "Settings" "Numfields" "${UMUI_INTERNAL_FNUMFIELDS_2ADDITIONALCONTROLS}"
    !else ifdef MUI_FINISHPAGE_RUN | MUI_FINISHPAGE_SHOWREADME | MUI_FINISHPAGE_LINK
      !insertmacro INSTALLOPTIONS_WRITE "ioSpecial.ini" "Settings" "Numfields" "${UMUI_INTERNAL_FNUMFIELDS_1ADDITIONALCONTROLS}"
    !endif


    !ifndef MUI_FINISHPAGE_NOREBOOTSUPPORT
       mui.finish_load:
    !endif

    !insertmacro MUI_PAGE_FUNCTION_CUSTOM PRE

    LockWindow on

!ifdef USE_MUIEx
;-----------------
    GetDlgItem $MUI_TEMP1 $HWNDPARENT 1028
    ShowWindow $MUI_TEMP1 ${SW_HIDE}

    GetDlgItem $MUI_TEMP1 $HWNDPARENT 1256
    ShowWindow $MUI_TEMP1 ${SW_HIDE}

    GetDlgItem $MUI_TEMP1 $HWNDPARENT 1035
    ShowWindow $MUI_TEMP1 ${SW_HIDE}

    GetDlgItem $MUI_TEMP1 $HWNDPARENT 1037
    ShowWindow $MUI_TEMP1 ${SW_HIDE}

    GetDlgItem $MUI_TEMP1 $HWNDPARENT 1038
    ShowWindow $MUI_TEMP1 ${SW_HIDE}

    GetDlgItem $MUI_TEMP1 $HWNDPARENT 1039
    ShowWindow $MUI_TEMP1 ${SW_HIDE}
!endif
;-----------------

    GetDlgItem $MUI_TEMP1 $HWNDPARENT 1045
    ShowWindow $MUI_TEMP1 ${SW_NORMAL}

    LockWindow off


    !insertmacro INSTALLOPTIONS_INITDIALOG "ioSpecial.ini"
    Pop $MUI_HWND

    !insertmacro UMUI_WFAPAGEBGTRANSPARENT_INIT $MUI_HWND

    !ifndef UMUI_USE_${MUI_PAGE_UNINSTALLER_PREFIX}ALTERNATE_PAGE

      GetDlgItem $MUI_TEMP1 $MUI_HWND ${UMUI_INTERNAL_FIDTITLE}
      !insertmacro UMUI_IOPAGECTLTRANSPARENT_INIT $MUI_TEMP1
      CreateFont $MUI_TEMP2 "$(^Font)" "${UMUI_WELCOMEFINISHABORT_TITLE_FONTSIZE}" "700"
      SendMessage $MUI_TEMP1 ${WM_SETFONT} $MUI_TEMP2 0
      GetDlgItem $MUI_TEMP1 $MUI_HWND ${UMUI_INTERNAL_FIDTEXT}
      !insertmacro UMUI_IOPAGECTLTRANSPARENT_INIT $MUI_TEMP1

    !else

      ;alternate page
      GetDlgItem $MUI_TEMP1 $MUI_HWND ${UMUI_INTERNAL_FIDTITLE}
      CreateFont $MUI_TEMP2 "MS Sans Serif" "${UMUI_WELCOMEFINISHABORT_TITLE_FONTSIZE}" "700"
      SendMessage $MUI_TEMP1 ${WM_SETFONT} $MUI_TEMP2 $MUI_TEMP2
      !insertmacro UMUI_IOPAGECTLTRANSPARENT_INIT $MUI_TEMP1
      GetDlgItem $MUI_TEMP1 $MUI_HWND ${UMUI_INTERNAL_FIDTEXT}
      !insertmacro UMUI_IOPAGECTLTRANSPARENT_INIT $MUI_TEMP1

    !endif


    !ifndef MUI_FINISHPAGE_NOREBOOTSUPPORT

      IfRebootFlag 0 mui.finish_noreboot_show

        GetDlgItem $MUI_TEMP1 $MUI_HWND ${UMUI_INTERNAL_FIDTHIRD}
        !insertmacro UMUI_IOPAGECTLTRANSPARENT_INIT $MUI_TEMP1

        GetDlgItem $MUI_TEMP1 $MUI_HWND ${UMUI_INTERNAL_FIDFOURTH}
        !insertmacro UMUI_IOPAGECTLTRANSPARENT_INIT $MUI_TEMP1

        Goto mui.finish_show

      mui.finish_noreboot_show:

    !endif

    !ifdef MUI_FINISHPAGE_RUN
      GetDlgItem $MUI_TEMP1 $MUI_HWND ${UMUI_INTERNAL_FIDTHIRD}
      !insertmacro UMUI_IOPAGECTLTRANSPARENT_INIT $MUI_TEMP1
    !endif

    !ifdef MUI_FINISHPAGE_SHOWREADME
      !ifndef MUI_FINISHPAGE_RUN
        GetDlgItem $MUI_TEMP1 $MUI_HWND ${UMUI_INTERNAL_FIDTHIRD}
      !else
        GetDlgItem $MUI_TEMP1 $MUI_HWND ${UMUI_INTERNAL_FIDFOURTH}
      !endif
      !insertmacro UMUI_IOPAGECTLTRANSPARENT_INIT $MUI_TEMP1
    !endif

    !ifdef MUI_FINISHPAGE_LINK
      !ifdef MUI_FINISHPAGE_RUN & MUI_FINISHPAGE_SHOWREADME
        GetDlgItem $MUI_TEMP1 $MUI_HWND ${UMUI_INTERNAL_FIDFIFTH}
      !else ifdef MUI_FINISHPAGE_RUN | MUI_FINISHPAGE_SHOWREADME
        GetDlgItem $MUI_TEMP1 $MUI_HWND ${UMUI_INTERNAL_FIDFOURTH}
      !else
        GetDlgItem $MUI_TEMP1 $MUI_HWND ${UMUI_INTERNAL_FIDTHIRD}
      !endif

      !ifdef UMUI_${MUI_PAGE_UNINSTALLER_PREFIX}PAGEBGIMAGE
        SetCtlColors $MUI_TEMP1 "${MUI_FINISHPAGE_LINK_COLOR}" "transparent"
      !else
        SetCtlColors $MUI_TEMP1 "${MUI_FINISHPAGE_LINK_COLOR}" "${MUI_BGCOLOR}"
      !endif

    !endif


    !ifndef MUI_FINISHPAGE_NOREBOOTSUPPORT
      mui.finish_show:
    !endif

    !if "${UMUI_XPSTYLE}" == "On"
      !ifndef MUI_FORCECLASSICCONTROLS
        ${If} ${IsHighContrastModeActive}
      !endif
        ; SetCtlColors does not change the check/radio text color (bug #443)
        !ifndef MUI_FINISHPAGE_NOREBOOTSUPPORT
          GetDlgItem $MUI_TEMP1 $MUI_HWND ${UMUI_INTERNAL_FIDTHIRD}
          System::Call 'UXTHEME::SetWindowTheme(p$MUI_TEMP1,w" ",w" ")'
          GetDlgItem $MUI_TEMP1 $MUI_HWND ${UMUI_INTERNAL_FIDFOURTH}
          System::Call 'UXTHEME::SetWindowTheme(p$MUI_TEMP1,w" ",w" ")'
        !else ifdef MUI_FINISHPAGE_RUN | MUI_FINISHPAGE_SHOWREADME
          GetDlgItem $MUI_TEMP1 $MUI_HWND ${UMUI_INTERNAL_FIDTHIRD}
          System::Call 'UXTHEME::SetWindowTheme(p$MUI_TEMP1,w" ",w" ")'
          !ifdef MUI_FINISHPAGE_RUN & MUI_FINISHPAGE_SHOWREADME
            GetDlgItem $MUI_TEMP1 $MUI_HWND ${UMUI_INTERNAL_FIDFOURTH}
            System::Call 'UXTHEME::SetWindowTheme(p$MUI_TEMP1,w" ",w" ")'
          !endif
        !endif
      !ifndef MUI_FORCECLASSICCONTROLS
        ${EndIf}
      !endif
    !endif

    GetDlgItem $MUI_TEMP1 $HWNDPARENT 3
    ShowWindow $MUI_TEMP1 ${SW_HIDE}
    GetDlgItem $MUI_TEMP1 $HWNDPARENT 2
    EnableWindow $MUI_TEMP1 0

    !insertmacro MUI_PAGE_FUNCTION_CUSTOM SHOW

    !ifdef MUI_FINISHPAGE_CANCEL_ENABLED
      StrCpy $MUI_NOABORTWARNING "1"
    !endif

    !insertmacro INSTALLOPTIONS_SHOW

    !ifdef MUI_FINISHPAGE_CANCEL_ENABLED
      StrCpy $MUI_NOABORTWARNING ""
    !endif

    LockWindow on

!ifdef USE_MUIEx
;-----------------
    GetDlgItem $MUI_TEMP1 $HWNDPARENT 1028
    ShowWindow $MUI_TEMP1 ${SW_NORMAL}

    GetDlgItem $MUI_TEMP1 $HWNDPARENT 1256
    ShowWindow $MUI_TEMP1 ${SW_NORMAL}

    GetDlgItem $MUI_TEMP1 $HWNDPARENT 1035
    ShowWindow $MUI_TEMP1 ${SW_NORMAL}

    GetDlgItem $MUI_TEMP1 $HWNDPARENT 1037
    ShowWindow $MUI_TEMP1 ${SW_NORMAL}

    GetDlgItem $MUI_TEMP1 $HWNDPARENT 1038
    ShowWindow $MUI_TEMP1 ${SW_NORMAL}

    GetDlgItem $MUI_TEMP1 $HWNDPARENT 1039
    ShowWindow $MUI_TEMP1 ${SW_NORMAL}
!endif
;-----------------

    GetDlgItem $MUI_TEMP1 $HWNDPARENT 1045
    ShowWindow $MUI_TEMP1 ${SW_HIDE}

    LockWindow off

    !insertmacro UMUI_FIX_BUTTONS_SKIN

  FunctionEnd

  Function "${LEAVE}"

    !insertmacro MUI_PAGE_FUNCTION_CUSTOM LEAVE

    !ifndef MUI_FINISHPAGE_NOREBOOTSUPPORT

      IfRebootFlag "" mui.finish_noreboot_end

        !insertmacro INSTALLOPTIONS_READ $MUI_TEMP1 "ioSpecial.ini" "Field ${UMUI_INTERNAL_FIELDTHIRD}" "State"

          StrCmp $MUI_TEMP1 "1" 0 +2
            Reboot

          Return

      mui.finish_noreboot_end:

    !endif

    !ifdef MUI_FINISHPAGE_RUN

      !insertmacro INSTALLOPTIONS_READ $MUI_TEMP1 "ioSpecial.ini" "Field ${UMUI_INTERNAL_FIELDTHIRD}" "State"

      StrCmp $MUI_TEMP1 "1" 0 mui.finish_norun
        !ifndef MUI_FINISHPAGE_RUN_FUNCTION
          !ifndef MUI_FINISHPAGE_RUN_PARAMETERS
            StrCpy $MUI_TEMP1 "$\"${MUI_FINISHPAGE_RUN}$\""
          !else
            StrCpy $MUI_TEMP1 "$\"${MUI_FINISHPAGE_RUN}$\" ${MUI_FINISHPAGE_RUN_PARAMETERS}"
          !endif
          Exec "$MUI_TEMP1"
        !else
          Call "${MUI_FINISHPAGE_RUN_FUNCTION}"
        !endif

        mui.finish_norun:

    !endif

    !ifdef MUI_FINISHPAGE_SHOWREADME

      !ifndef MUI_FINISHPAGE_RUN
        !insertmacro INSTALLOPTIONS_READ $MUI_TEMP1 "ioSpecial.ini" "Field ${UMUI_INTERNAL_FIELDTHIRD}" "State"
      !else
        !insertmacro INSTALLOPTIONS_READ $MUI_TEMP1 "ioSpecial.ini" "Field ${UMUI_INTERNAL_FIELDFOURTH}" "State"
      !endif

      StrCmp $MUI_TEMP1 "1" 0 mui.finish_noshowreadme
        !ifndef MUI_FINISHPAGE_SHOWREADME_FUNCTION
           ExecShell "open" "${MUI_FINISHPAGE_SHOWREADME}"
        !else
          Call "${MUI_FINISHPAGE_SHOWREADME_FUNCTION}"
        !endif

        mui.finish_noshowreadme:

    !endif

  FunctionEnd

  !undef UMUI_INTERNAL_FNUMFIELDS_3ADDITIONALCONTROLS
  !undef UMUI_INTERNAL_FNUMFIELDS_2ADDITIONALCONTROLS
  !undef UMUI_INTERNAL_FNUMFIELDS_1ADDITIONALCONTROLS
  !undef UMUI_INTERNAL_FIELDTITLE
  !undef UMUI_INTERNAL_FIELDTEXT
  !undef UMUI_INTERNAL_FIELDTHIRD
  !undef UMUI_INTERNAL_FIELDFOURTH
  !undef UMUI_INTERNAL_FIELDFIFTH
  !undef UMUI_INTERNAL_FIDTITLE
  !undef UMUI_INTERNAL_FIDTEXT
  !undef UMUI_INTERNAL_FIDTHIRD
  !undef UMUI_INTERNAL_FIDFOURTH
  !undef UMUI_INTERNAL_FIDFIFTH
  !undef UMUI_INTERNAL_FPOSLINKLEFT
  !undef UMUI_INTERNAL_FOPTIONCHECKLEFT

!macroend

!macro MUI_UNFUNCTION_CONFIRMPAGE PRE SHOW LEAVE

  Function "${PRE}"

    !insertmacro UMUI_ABORT_IF_INSTALLFLAG_IS ${UMUI_CANCELLED}

    !insertmacro MUI_PAGE_FUNCTION_CUSTOM PRE

    !insertmacro MUI_HEADER_TEXT_PAGE $(MUI_UNTEXT_CONFIRM_TITLE) $(MUI_UNTEXT_CONFIRM_SUBTITLE)

    !insertmacro UMUI_FIX_BUTTONS_SKIN

  FunctionEnd

  Function "${SHOW}"

    !insertmacro UMUI_PAGEBGTRANSPARENT_INIT
    !insertmacro UMUI_PAGECTLTRANSPARENT_INIT 1029
    !insertmacro UMUI_PAGECTLLIGHT_INIT 1000
    !insertmacro UMUI_PAGECTLTRANSPARENT_INIT 1006

    !insertmacro MUI_PAGE_FUNCTION_CUSTOM SHOW

  FunctionEnd

  Function "${LEAVE}"

    !insertmacro MUI_PAGE_FUNCTION_CUSTOM LEAVE

  FunctionEnd

!macroend




; ========================
;   New UltraModern page
; ========================



!macro UMUI_PAGE_MULTILANGUAGE

  !verbose push
  !verbose ${MUI_VERBOSE}

  !insertmacro MUI_PAGE_INIT

  !define /IfNDef UMUI_${MUI_PAGE_UNINSTALLER_PREFIX}MULTILANGUAGEPAGE

  !insertmacro MUI_DEFAULT_IOCONVERT UMUI_MULTILANGUAGEPAGE_TITLE "$(UMUI_${MUI_PAGE_UNINSTALLER_PREFIX}TEXT_MULTILANGUAGE_TITLE)"
  !insertmacro MUI_DEFAULT_IOCONVERT UMUI_MULTILANGUAGEPAGE_TEXT "$(UMUI_${MUI_PAGE_UNINSTALLER_PREFIX}TEXT_MULTILANGUAGE_TEXT)"
  !insertmacro MUI_DEFAULT_IOCONVERT UMUI_MULTILANGUAGEPAGE_LANGUAGE "$(UMUI_TEXT_MULTILANGUAGE_LANGUAGE)"

  !ifndef MUI_VAR_HWND
    Var MUI_HWND
    !define MUI_VAR_HWND
  !endif

  !ifndef UMUI_VAR_LANGLIST
    Var UMUI_LANGLIST
    !define UMUI_VAR_LANGLIST
  !endif

  !ifndef UMUI_VAR_UMUI_TEMP3
    Var UMUI_TEMP3
    !define UMUI_VAR_UMUI_TEMP3
  !endif

  PageEx ${MUI_PAGE_UNINSTALLER_FUNCPREFIX}custom

    PageCallbacks ${MUI_PAGE_UNINSTALLER_FUNCPREFIX}mui.MultiLanguagePre_${MUI_UNIQUEID} ${MUI_PAGE_UNINSTALLER_FUNCPREFIX}mui.MultiLanguageLeave_${MUI_UNIQUEID}

    Caption " "

  PageExEnd

  !insertmacro UMUI_FUNCTION_MULTILANGUAGEPAGE ${MUI_PAGE_UNINSTALLER_FUNCPREFIX}mui.MultiLanguagePre_${MUI_UNIQUEID} ${MUI_PAGE_UNINSTALLER_FUNCPREFIX}mui.MultiLanguageLeave_${MUI_UNIQUEID}

  !insertmacro MUI_UNSET UMUI_MULTILANGUAGEPAGE_TITLE
  !insertmacro MUI_UNSET UMUI_MULTILANGUAGEPAGE_TEXT
  !insertmacro MUI_UNSET UMUI_MULTILANGUAGEPAGE_LANGUAGE
  !insertmacro MUI_UNSET UMUI_MULTILANGUAGEPAGE_TITLE_3LINES

  !verbose pop

!macroend


!macro UMUI_UNPAGE_MULTILANGUAGE

  !verbose push
  !verbose ${MUI_VERBOSE}

  !insertmacro MUI_UNPAGE_INIT

    !insertmacro UMUI_PAGE_MULTILANGUAGE

  !insertmacro MUI_UNPAGE_END

  !verbose pop

!macroend


!macro UMUI_FUNCTION_MULTILANGUAGEPAGE PRE LEAVE

  !ifndef UMUI_WELCOMEFINISHABORTPAGE_USE_IMAGE
    !define UMUI_INTERNAL_MNUMFIELDS 4
    !define UMUI_INTERNAL_MFIELDTITLE 1
    !define UMUI_INTERNAL_MFIELDTEXT 2
    !define UMUI_INTERNAL_MFIELDGROUPBOX 3
    !define UMUI_INTERNAL_MFIELDDROPDOWN 4
    !define UMUI_INTERNAL_MIDTITLE 1200
    !define UMUI_INTERNAL_MIDTEXT 1201
    !define UMUI_INTERNAL_MIDGROUPBOX 1202
    !define UMUI_INTERNAL_MIDDROPDOWN 1203
    !define UMUI_INTERNAL_MPOSGROUPBOXLEFT 75
    !define UMUI_INTERNAL_MPOSGROUPBOXRIGHT -75
    !define UMUI_INTERNAL_MPOSDROPDOWNLEFT 105
    !define UMUI_INTERNAL_MPOSDROPDOWNRIGHT -105
  !else
    !define UMUI_INTERNAL_MNUMFIELDS 5
    !define UMUI_INTERNAL_MFIELDTITLE 2
    !define UMUI_INTERNAL_MFIELDTEXT 3
    !define UMUI_INTERNAL_MFIELDGROUPBOX 4
    !define UMUI_INTERNAL_MFIELDDROPDOWN 5
    !define UMUI_INTERNAL_MIDTITLE 1201
    !define UMUI_INTERNAL_MIDTEXT 1202
    !define UMUI_INTERNAL_MIDGROUPBOX 1203
    !define UMUI_INTERNAL_MIDDROPDOWN 1204
    !define UMUI_INTERNAL_MPOSGROUPBOXLEFT 140
    !define UMUI_INTERNAL_MPOSGROUPBOXRIGHT -30
    !define UMUI_INTERNAL_MPOSDROPDOWNLEFT 170
    !define UMUI_INTERNAL_MPOSDROPDOWNRIGHT -60
  !endif

  !define /IfNDef UMUI_HIDENEXTBACKBUTTON

  Function "${PRE}"

    ; IF setup cancelled
    !insertmacro UMUI_ABORT_IF_INSTALLFLAG_IS ${UMUI_CANCELLED}|${UMUI_LANGISSET}

    !insertmacro MUI_HEADER_TEXT_PAGE "" ""

    ; save the old language id
    StrCpy $UMUI_TEMP3 $LANGUAGE

    StrCmp $UMUI_LANGLIST "" 0 +2
      MessageBox MB_OK|MB_ICONSTOP "Ultra-Modern UI error: You have forgotten to insert the UMUI_MULTILANG_GET macro in your ${MUI_PAGE_UNINSTALLER_FUNCPREFIX}.oninit function."

    ClearErrors
    ; Get the current language id
    nsArray::Get LangMap $LANGUAGE
    Pop $MUI_TEMP1

    ;if don't exist
    IfErrors 0 foundLang

      ;search for english
      nsArray::Get LangMap "1033"
      Pop $MUI_TEMP1

      ;if don't exist
      IfErrors 0 foundLang

        ;english an system language was not been inserted
        StrCpy $MUI_TEMP1 ""

    foundLang:

    CopyFiles /SILENT "$PLUGINSDIR\ioSpecial.ini" "$PLUGINSDIR\MultiLanguage.ini"


    !insertmacro INSTALLOPTIONS_WRITE "MultiLanguage.ini" "Settings" "NumFields" "${UMUI_INTERNAL_MNUMFIELDS}"
    !insertmacro INSTALLOPTIONS_WRITE "MultiLanguage.ini" "Settings" "NextButtonText" ""
    !insertmacro INSTALLOPTIONS_WRITE "MultiLanguage.ini" "Settings" "CancelEnabled" ""

    !insertmacro MUI_INSTALLOPTIONS_WRITE_DEFAULTCONVERT "MultiLanguage.ini" "Field ${UMUI_INTERNAL_MFIELDTITLE}" "Text" "UMUI_MULTILANGUAGEPAGE_TITLE"

    !ifndef UMUI_USE_${MUI_PAGE_UNINSTALLER_PREFIX}ALTERNATE_PAGE
      !ifndef UMUI_MULTILANGUAGEPAGE_TITLE_3LINES
        !insertmacro INSTALLOPTIONS_WRITE "MultiLanguage.ini" "Field ${UMUI_INTERNAL_MFIELDTITLE}" "Bottom" "55"
        !insertmacro INSTALLOPTIONS_WRITE "MultiLanguage.ini" "Field ${UMUI_INTERNAL_MFIELDTEXT}" "Top" "62"
      !else
        !insertmacro INSTALLOPTIONS_WRITE "MultiLanguage.ini" "Field ${UMUI_INTERNAL_MFIELDTITLE}" "Bottom" "62"
        !insertmacro INSTALLOPTIONS_WRITE "MultiLanguage.ini" "Field ${UMUI_INTERNAL_MFIELDTEXT}" "Top" "69"
      !endif
    !endif

    !insertmacro MUI_INSTALLOPTIONS_WRITE_DEFAULTCONVERT "MultiLanguage.ini" "Field ${UMUI_INTERNAL_MFIELDTEXT}" "Text" "UMUI_MULTILANGUAGEPAGE_TEXT"
    !insertmacro INSTALLOPTIONS_WRITE "MultiLanguage.ini" "Field ${UMUI_INTERNAL_MFIELDTEXT}" "Bottom" "120"

    !insertmacro INSTALLOPTIONS_WRITE "MultiLanguage.ini" "Field ${UMUI_INTERNAL_MFIELDGROUPBOX}" "Type" "GroupBox"
    !insertmacro MUI_INSTALLOPTIONS_WRITE_DEFAULTCONVERT "MultiLanguage.ini" "Field ${UMUI_INTERNAL_MFIELDGROUPBOX}" "Text" "UMUI_MULTILANGUAGEPAGE_LANGUAGE"
    !insertmacro INSTALLOPTIONS_WRITE "MultiLanguage.ini" "Field ${UMUI_INTERNAL_MFIELDGROUPBOX}" "Left" "${UMUI_INTERNAL_MPOSGROUPBOXLEFT}"
    !insertmacro INSTALLOPTIONS_WRITE "MultiLanguage.ini" "Field ${UMUI_INTERNAL_MFIELDGROUPBOX}" "Right" "${UMUI_INTERNAL_MPOSGROUPBOXRIGHT}"
    !insertmacro INSTALLOPTIONS_WRITE "MultiLanguage.ini" "Field ${UMUI_INTERNAL_MFIELDGROUPBOX}" "Top" "120"
    !insertmacro INSTALLOPTIONS_WRITE "MultiLanguage.ini" "Field ${UMUI_INTERNAL_MFIELDGROUPBOX}" "Bottom" "160"

    !insertmacro INSTALLOPTIONS_WRITE "MultiLanguage.ini" "Field ${UMUI_INTERNAL_MFIELDDROPDOWN}" "Type" "DropList"
    !insertmacro INSTALLOPTIONS_WRITE "MultiLanguage.ini" "Field ${UMUI_INTERNAL_MFIELDDROPDOWN}" "ListItems" "$UMUI_LANGLIST"
    !insertmacro INSTALLOPTIONS_WRITE "MultiLanguage.ini" "Field ${UMUI_INTERNAL_MFIELDDROPDOWN}" "State" $MUI_TEMP1

    !insertmacro INSTALLOPTIONS_WRITE "MultiLanguage.ini" "Field ${UMUI_INTERNAL_MFIELDDROPDOWN}" "Left" "${UMUI_INTERNAL_MPOSDROPDOWNLEFT}"
    !insertmacro INSTALLOPTIONS_WRITE "MultiLanguage.ini" "Field ${UMUI_INTERNAL_MFIELDDROPDOWN}" "Right" "${UMUI_INTERNAL_MPOSDROPDOWNRIGHT}"
    !insertmacro INSTALLOPTIONS_WRITE "MultiLanguage.ini" "Field ${UMUI_INTERNAL_MFIELDDROPDOWN}" "Top" "135"
    !insertmacro INSTALLOPTIONS_WRITE "MultiLanguage.ini" "Field ${UMUI_INTERNAL_MFIELDDROPDOWN}" "Bottom" "-1"

    !insertmacro MUI_PAGE_FUNCTION_CUSTOM PRE

    LockWindow on

!ifdef USE_MUIEx
;-----------------
    GetDlgItem $MUI_TEMP1 $HWNDPARENT 1028
    ShowWindow $MUI_TEMP1 ${SW_HIDE}

    GetDlgItem $MUI_TEMP1 $HWNDPARENT 1256
    ShowWindow $MUI_TEMP1 ${SW_HIDE}

    GetDlgItem $MUI_TEMP1 $HWNDPARENT 1035
    ShowWindow $MUI_TEMP1 ${SW_HIDE}

    GetDlgItem $MUI_TEMP1 $HWNDPARENT 1037
    ShowWindow $MUI_TEMP1 ${SW_HIDE}

    GetDlgItem $MUI_TEMP1 $HWNDPARENT 1038
    ShowWindow $MUI_TEMP1 ${SW_HIDE}

    GetDlgItem $MUI_TEMP1 $HWNDPARENT 1039
    ShowWindow $MUI_TEMP1 ${SW_HIDE}
!endif
;-----------------

    GetDlgItem $MUI_TEMP1 $HWNDPARENT 1045
    ShowWindow $MUI_TEMP1 ${SW_NORMAL}

    LockWindow off


    !insertmacro INSTALLOPTIONS_INITDIALOG "MultiLanguage.ini"
    Pop $MUI_HWND

    !insertmacro UMUI_WFAPAGEBGTRANSPARENT_INIT $MUI_HWND

    !ifndef UMUI_USE_${MUI_PAGE_UNINSTALLER_PREFIX}ALTERNATE_PAGE

      GetDlgItem $MUI_TEMP1 $MUI_HWND ${UMUI_INTERNAL_MIDTITLE}
      !insertmacro UMUI_IOPAGECTLTRANSPARENT_INIT $MUI_TEMP1
      CreateFont $MUI_TEMP2 "$(^Font)" "${UMUI_WELCOMEFINISHABORT_TITLE_FONTSIZE}" "700"
      SendMessage $MUI_TEMP1 ${WM_SETFONT} $MUI_TEMP2 0
      GetDlgItem $MUI_TEMP1 $MUI_HWND ${UMUI_INTERNAL_MIDTEXT}
      !insertmacro UMUI_IOPAGECTLTRANSPARENT_INIT $MUI_TEMP1

    !else

      ;alternate page
      GetDlgItem $MUI_TEMP1 $MUI_HWND ${UMUI_INTERNAL_MIDTITLE}
      CreateFont $MUI_TEMP2 "MS Sans Serif" "${UMUI_WELCOMEFINISHABORT_TITLE_FONTSIZE}" "700"
      SendMessage $MUI_TEMP1 ${WM_SETFONT} $MUI_TEMP2 $MUI_TEMP2
      !insertmacro UMUI_IOPAGECTLTRANSPARENT_INIT $MUI_TEMP1
      GetDlgItem $MUI_TEMP1 $MUI_HWND ${UMUI_INTERNAL_MIDTEXT}
      !insertmacro UMUI_IOPAGECTLTRANSPARENT_INIT $MUI_TEMP1

    !endif


    GetDlgItem $MUI_TEMP1 $MUI_HWND ${UMUI_INTERNAL_MIDGROUPBOX}
    !insertmacro UMUI_IOPAGECTLLIGHT_INIT $MUI_TEMP1
    GetDlgItem $MUI_TEMP1 $MUI_HWND ${UMUI_INTERNAL_MIDDROPDOWN}
    !insertmacro UMUI_IOPAGEINPUTCTL_INIT $MUI_TEMP1

    !insertmacro MUI_PAGE_FUNCTION_CUSTOM SHOW

    !insertmacro INSTALLOPTIONS_SHOW

    LockWindow on

!ifdef USE_MUIEx
;-----------------
    GetDlgItem $MUI_TEMP1 $HWNDPARENT 1028
    ShowWindow $MUI_TEMP1 ${SW_NORMAL}

    GetDlgItem $MUI_TEMP1 $HWNDPARENT 1256
    ShowWindow $MUI_TEMP1 ${SW_NORMAL}

    GetDlgItem $MUI_TEMP1 $HWNDPARENT 1035
    ShowWindow $MUI_TEMP1 ${SW_NORMAL}

    GetDlgItem $MUI_TEMP1 $HWNDPARENT 1037
    ShowWindow $MUI_TEMP1 ${SW_NORMAL}

    GetDlgItem $MUI_TEMP1 $HWNDPARENT 1038
    ShowWindow $MUI_TEMP1 ${SW_NORMAL}

    GetDlgItem $MUI_TEMP1 $HWNDPARENT 1039
    ShowWindow $MUI_TEMP1 ${SW_NORMAL}
!endif
;-----------------

    GetDlgItem $MUI_TEMP1 $HWNDPARENT 1045
    ShowWindow $MUI_TEMP1 ${SW_HIDE}

    LockWindow off

    !insertmacro UMUI_FIX_BUTTONS_SKIN

  FunctionEnd

  Function "${LEAVE}"

    !insertmacro UMUI_IF_INSTALLFLAG_ISNOT ${UMUI_CANCELLED}

      !insertmacro MUI_PAGE_FUNCTION_CUSTOM LEAVE

      ; Get the choosed language name
      !insertmacro INSTALLOPTIONS_READ $MUI_TEMP1 "MultiLanguage.ini" "Field ${UMUI_INTERNAL_MFIELDDROPDOWN}" "State"

      ;Search key of selcted value
      ClearErrors
      langLoop:
        nsArray::Iterate LangMap
        Pop $LANGUAGE
        Pop $MUI_TEMP2
         StrCmp $MUI_TEMP1 $MUI_TEMP2 +2 0
          IfErrors 0 langLoop

      nsArray::Clear LangMap

      ; if we choose the same language
      StrCmp $UMUI_TEMP3 $LANGUAGE 0 reloadinstall

        !insertmacro UMUI_SET_INSTALLFLAG ${UMUI_LANGISSET}

        !ifdef UMUI_LANGUAGE_REGISTRY_VALUENAME
          !insertmacro UMUI_ADDPARAMTOSAVETOREGISTRYKEY ${UMUI_LANGUAGE_REGISTRY_ROOT} "${UMUI_LANGUAGE_REGISTRY_KEY}" "${UMUI_LANGUAGE_REGISTRY_VALUENAME}" "$LANGUAGE"
        !endif

        Goto end
      reloadinstall:

        ;Recall this programm and quit
        !insertmacro UMUI_GET_PARAMETERS
        Pop $MUI_TEMP2

        !insertmacro UMUI_DELETE_PLUGINDIR
        HideWindow

        !ifndef MUI_UNINSTALLER
          ExecWait "$EXEPATH $MUI_TEMP2 /L=$LANGUAGE /NCRC"
        !else
          ExecWait "$EXEPATH $MUI_TEMP2 /L=$LANGUAGE _?=$INSTDIR"
        !endif
        Quit

      end:


    !insertmacro UMUI_ENDIF_INSTALLFLAG

  FunctionEnd

  !undef UMUI_INTERNAL_MNUMFIELDS
  !undef UMUI_INTERNAL_MFIELDTITLE
  !undef UMUI_INTERNAL_MFIELDTEXT
  !undef UMUI_INTERNAL_MFIELDGROUPBOX
  !undef UMUI_INTERNAL_MFIELDDROPDOWN
  !undef UMUI_INTERNAL_MIDTITLE
  !undef UMUI_INTERNAL_MIDTEXT
  !undef UMUI_INTERNAL_MIDGROUPBOX
  !undef UMUI_INTERNAL_MIDDROPDOWN
  !undef UMUI_INTERNAL_MPOSGROUPBOXLEFT
  !undef UMUI_INTERNAL_MPOSGROUPBOXRIGHT
  !undef UMUI_INTERNAL_MPOSDROPDOWNLEFT
  !undef UMUI_INTERNAL_MPOSDROPDOWNRIGHT

!macroend


!macro UMUI_PAGE_CONFIRM

  !verbose push
  !verbose ${MUI_VERBOSE}

  !insertmacro MUI_PAGE_INIT

  !define /IfNDef UMUI_${MUI_PAGE_UNINSTALLER_PREFIX}CONFIRMPAGE

  !insertmacro MUI_DEFAULT_IOCONVERT UMUI_CONFIRMPAGE_TEXT_TOP "$(UMUI_${MUI_PAGE_UNINSTALLER_PREFIX}TEXT_INSTCONFIRM_TEXT_TOP)"
  !insertmacro MUI_DEFAULT_IOCONVERT UMUI_CONFIRMPAGE_TEXT_BOTTOM "$(UMUI_TEXT_INSTCONFIRM_TEXTBOX_TITLE)"

  !ifdef UMUI_CONFIRMPAGE_TEXTBOX
    !ifndef UMUI_VAR_UMUI_TEMP3
      Var UMUI_TEMP3
      !define UMUI_VAR_UMUI_TEMP3
    !endif
  !endif

  PageEx ${MUI_PAGE_UNINSTALLER_FUNCPREFIX}custom

    PageCallbacks ${MUI_PAGE_UNINSTALLER_FUNCPREFIX}mui.ConfirmPre_${MUI_UNIQUEID} ${MUI_PAGE_UNINSTALLER_FUNCPREFIX}mui.ConfirmLeave_${MUI_UNIQUEID}

    Caption " "

  PageExEnd

  !insertmacro UMUI_FUNCTION_CONFIRMPAGE ${MUI_PAGE_UNINSTALLER_FUNCPREFIX}mui.ConfirmPre_${MUI_UNIQUEID} ${MUI_PAGE_UNINSTALLER_FUNCPREFIX}mui.ConfirmLeave_${MUI_UNIQUEID}

  !undef UMUI_CONFIRMPAGE_TEXT_TOP
  !undef UMUI_CONFIRMPAGE_TEXT_BOTTOM

  !insertmacro MUI_UNSET UMUI_CONFIRMPAGE_TEXTBOX

  !verbose pop

!macroend

!macro UMUI_UNPAGE_CONFIRM

  !verbose push
  !verbose ${MUI_VERBOSE}

  !insertmacro MUI_UNPAGE_INIT

    !insertmacro UMUI_PAGE_CONFIRM

  !insertmacro MUI_UNPAGE_END

  !verbose pop

!macroend

!macro UMUI_FUNCTION_CONFIRMPAGE PRE LEAVE

  Function "${PRE}"

    ; IF setup cancelled
    !insertmacro UMUI_ABORT_IF_INSTALLFLAG_IS ${UMUI_CANCELLED}

    !insertmacro INSTALLOPTIONS_EXTRACT_AS "${UMUI_CONFIRMPAGE_INI}" "Confirm.ini"

    ; Bodenseematze-2016-09-15: missing PRE-Function support added:
    !insertmacro MUI_PAGE_FUNCTION_CUSTOM PRE

    !insertmacro MUI_HEADER_TEXT_PAGE "$(UMUI_${MUI_PAGE_UNINSTALLER_PREFIX}TEXT_INSTCONFIRM_TITLE)" "$(UMUI_${MUI_PAGE_UNINSTALLER_PREFIX}TEXT_INSTCONFIRM_SUBTITLE)"

    !ifdef UMUI_CONFIRMPAGE_TEXTBOX
      FlushINI "$PLUGINSDIR\Confirm.ini"

      FileOpen $MUI_TEMP2 "$PLUGINSDIR\Confirm.ini" a
      !ifdef NSIS_UNICODE
        FileSeek $MUI_TEMP2 -4 END
      !else
        FileSeek $MUI_TEMP2 -2 END
      !endif

      Call "${UMUI_CONFIRMPAGE_TEXTBOX}"

      FileClose $MUI_TEMP2

      !insertmacro INSTALLOPTIONS_WRITE "Confirm.ini" "Settings" NumFields "3"

    !endif

    !insertmacro MUI_INSTALLOPTIONS_WRITE_DEFAULTCONVERT "Confirm.ini" "Field 1" "Text" "UMUI_CONFIRMPAGE_TEXT_TOP"
    !insertmacro MUI_INSTALLOPTIONS_WRITE_DEFAULTCONVERT "Confirm.ini" "Field 2" "Text" "UMUI_CONFIRMPAGE_TEXT_BOTTOM"

    !insertmacro MUI_PAGE_FUNCTION_CUSTOM SHOW

    !insertmacro INSTALLOPTIONS_DISPLAY "Confirm.ini"

    !insertmacro UMUI_FIX_BUTTONS_SKIN

  FunctionEnd

  Function "${LEAVE}"

    !insertmacro MUI_PAGE_FUNCTION_CUSTOM LEAVE

  FunctionEnd

!macroend

!macro UMUI_CONFIRMPAGE_TEXTBOX_ADDLINE STR

  StrCpy $UMUI_TEMP3 "${STR}"

  !insertmacro UMUI_STRREPLACE $UMUI_TEMP3 "\" "\\" $UMUI_TEMP3

  !ifdef NSIS_UNICODE
    FileWriteUTF16LE $MUI_TEMP2 "$UMUI_TEMP3\r\n"
  !else
    FileWrite $MUI_TEMP2 "$UMUI_TEMP3\r\n"
  !endif

  ClearErrors

!macroend







!macro UMUI_PAGE_ABORT

  !verbose push
  !verbose ${MUI_VERBOSE}

  !insertmacro MUI_PAGE_INIT

  !define /IfNDef UMUI_${MUI_PAGE_UNINSTALLER_PREFIX}ABORTPAGE

  !insertmacro MUI_DEFAULT_IOCONVERT UMUI_ABORTPAGE_TITLE "$(UMUI_${MUI_PAGE_UNINSTALLER_PREFIX}TEXT_ABORT_INFO_TITLE)"
  !insertmacro MUI_DEFAULT_IOCONVERT UMUI_ABORTPAGE_TEXT "$(UMUI_${MUI_PAGE_UNINSTALLER_PREFIX}TEXT_ABORT_INFO_TEXT)"

  !define /IfNDef UMUI_ABORTPAGE_LINK_COLOR "${UMUI_TEXT_LIGHTCOLOR}"

  !ifndef MUI_VAR_HWND
    Var MUI_HWND
    !define MUI_VAR_HWND
  !endif

  PageEx ${MUI_PAGE_UNINSTALLER_FUNCPREFIX}custom

    PageCallbacks ${MUI_PAGE_UNINSTALLER_FUNCPREFIX}mui.ABORTPre_${MUI_UNIQUEID} ${MUI_PAGE_UNINSTALLER_FUNCPREFIX}mui.ABORTLeave_${MUI_UNIQUEID}

    Caption " "

  PageExEnd

  !insertmacro UMUI_FUNCTION_ABORTPAGE ${MUI_PAGE_UNINSTALLER_FUNCPREFIX}mui.ABORTPre_${MUI_UNIQUEID} ${MUI_PAGE_UNINSTALLER_FUNCPREFIX}mui.ABORTLeave_${MUI_UNIQUEID}

  !insertmacro MUI_UNSET UMUI_ABORTPAGE_TITLE
  !insertmacro MUI_UNSET UMUI_ABORTPAGE_TITLE_3LINES
  !insertmacro MUI_UNSET UMUI_ABORTPAGE_TEXT
  !insertmacro MUI_UNSET UMUI_ABORTPAGE_LINK
  !insertmacro MUI_UNSET UMUI_ABORTPAGE_LINK_LOCATION
  !insertmacro MUI_UNSET UMUI_ABORTPAGE_LINK_COLOR

  !verbose pop

!macroend


!macro UMUI_UNPAGE_ABORT

  !verbose push
  !verbose ${MUI_VERBOSE}

  !insertmacro MUI_UNPAGE_INIT

    !insertmacro UMUI_PAGE_ABORT

  !insertmacro MUI_UNPAGE_END

  !verbose pop

!macroend


!macro UMUI_FUNCTION_ABORTPAGE PRE LEAVE

  !ifndef UMUI_WELCOMEFINISHABORTPAGE_USE_IMAGE
    !define UMUI_INTERNAL_ANUMFIELDS 2
    !define UMUI_INTERNAL_ANUMFIELDSLINK 3
    !define UMUI_INTERNAL_AFIELDTITLE 1
    !define UMUI_INTERNAL_AFIELDTEXT 2
    !define UMUI_INTERNAL_AFIELDLINK 3
    !define UMUI_INTERNAL_AIDTITLE 1200
    !define UMUI_INTERNAL_AIDTEXT 1201
    !define UMUI_INTERNAL_AIDLINK 1202
    !define UMUI_INTERNAL_APOSLINKLEFT 22
  !else
    !define UMUI_INTERNAL_ANUMFIELDS 3
    !define UMUI_INTERNAL_ANUMFIELDSLINK 4
    !define UMUI_INTERNAL_AFIELDTITLE 2
    !define UMUI_INTERNAL_AFIELDTEXT 3
    !define UMUI_INTERNAL_AFIELDLINK 4
    !define UMUI_INTERNAL_AIDTITLE 1201
    !define UMUI_INTERNAL_AIDTEXT 1202
    !define UMUI_INTERNAL_AIDLINK 1203
    !define UMUI_INTERNAL_APOSLINKLEFT 130
  !endif

  Function "${PRE}"

    ;If setup is not cancelled
    !insertmacro UMUI_ABORT_IF_INSTALLFLAG_ISNOT ${UMUI_CANCELLED}

    !insertmacro MUI_HEADER_TEXT_PAGE "" ""

    !insertmacro MUI_WELCOMEFINISHPAGE_FUNCTION_CUSTOM

    !insertmacro INSTALLOPTIONS_WRITE "ioSpecial.ini"  "Settings" NextButtonText "$(^CloseBtn)"

    !insertmacro INSTALLOPTIONS_WRITE "ioSpecial.ini" "Settings" "NumFields" "${UMUI_INTERNAL_ANUMFIELDS}"
    !insertmacro MUI_INSTALLOPTIONS_WRITE_DEFAULTCONVERT "ioSpecial.ini"  "Field ${UMUI_INTERNAL_AFIELDTITLE}" "Text" "UMUI_ABORTPAGE_TITLE"

    !ifndef UMUI_USE_${MUI_PAGE_UNINSTALLER_PREFIX}ALTERNATE_PAGE
      !ifndef UMUI_ABORTPAGE_TITLE_3LINES
        !insertmacro INSTALLOPTIONS_WRITE "ioSpecial.ini" "Field ${UMUI_INTERNAL_AFIELDTITLE}" "Bottom" "55"
        !insertmacro INSTALLOPTIONS_WRITE "ioSpecial.ini" "Field ${UMUI_INTERNAL_AFIELDTEXT}" "Top" "62"
      !else
        !insertmacro INSTALLOPTIONS_WRITE "ioSpecial.ini" "Field ${UMUI_INTERNAL_AFIELDTITLE}" "Bottom" "62"
        !insertmacro INSTALLOPTIONS_WRITE "ioSpecial.ini" "Field ${UMUI_INTERNAL_AFIELDTEXT}" "Top" "69"
      !endif
    !endif

    !insertmacro INSTALLOPTIONS_WRITE "ioSpecial.ini" "Field ${UMUI_INTERNAL_AFIELDTEXT}" "Bottom" "-15"
    !insertmacro MUI_INSTALLOPTIONS_WRITE_DEFAULTCONVERT "ioSpecial.ini" "Field ${UMUI_INTERNAL_AFIELDTEXT}" "Text" "UMUI_ABORTPAGE_TEXT"

    !ifdef UMUI_ABORTPAGE_LINK

      !insertmacro INSTALLOPTIONS_WRITE "ioSpecial.ini"  "Settings" NumFields "${UMUI_INTERNAL_ANUMFIELDSLINK}"

      !insertmacro INSTALLOPTIONS_WRITE "ioSpecial.ini" "Field ${UMUI_INTERNAL_AFIELDLINK}" "Type" "Link"
      !insertmacro MUI_INSTALLOPTIONS_WRITE_DEFAULTCONVERT "ioSpecial.ini" "Field ${UMUI_INTERNAL_AFIELDLINK}" "Text" "UMUI_ABORTPAGE_LINK"
      !insertmacro INSTALLOPTIONS_WRITE "ioSpecial.ini" "Field ${UMUI_INTERNAL_AFIELDLINK}" "Left" "${UMUI_INTERNAL_APOSLINKLEFT}"
      !insertmacro INSTALLOPTIONS_WRITE "ioSpecial.ini" "Field ${UMUI_INTERNAL_AFIELDLINK}" "Right" "-15"
      !insertmacro INSTALLOPTIONS_WRITE "ioSpecial.ini" "Field ${UMUI_INTERNAL_AFIELDLINK}" "Top" "-14"
      !insertmacro INSTALLOPTIONS_WRITE "ioSpecial.ini" "Field ${UMUI_INTERNAL_AFIELDLINK}" "Bottom" "-5"
      !insertmacro MUI_INSTALLOPTIONS_WRITE_DEFAULTCONVERT "ioSpecial.ini" "Field ${UMUI_INTERNAL_AFIELDLINK}" "State" "UMUI_ABORTPAGE_LINK_LOCATION"

    !endif

    !insertmacro MUI_PAGE_FUNCTION_CUSTOM PRE

    LockWindow on

!ifdef USE_MUIEx
;-----------------
    GetDlgItem $MUI_TEMP1 $HWNDPARENT 1028
    ShowWindow $MUI_TEMP1 ${SW_HIDE}

    GetDlgItem $MUI_TEMP1 $HWNDPARENT 1256
    ShowWindow $MUI_TEMP1 ${SW_HIDE}

    GetDlgItem $MUI_TEMP1 $HWNDPARENT 1035
    ShowWindow $MUI_TEMP1 ${SW_HIDE}

    GetDlgItem $MUI_TEMP1 $HWNDPARENT 1037
    ShowWindow $MUI_TEMP1 ${SW_HIDE}

    GetDlgItem $MUI_TEMP1 $HWNDPARENT 1038
    ShowWindow $MUI_TEMP1 ${SW_HIDE}

    GetDlgItem $MUI_TEMP1 $HWNDPARENT 1039
    ShowWindow $MUI_TEMP1 ${SW_HIDE}
!endif
;-----------------

    GetDlgItem $MUI_TEMP1 $HWNDPARENT 1045
    ShowWindow $MUI_TEMP1 ${SW_NORMAL}

    LockWindow off


    !insertmacro INSTALLOPTIONS_INITDIALOG "ioSpecial.ini"
    Pop $MUI_HWND

    !insertmacro UMUI_WFAPAGEBGTRANSPARENT_INIT $MUI_HWND

    !ifndef UMUI_USE_${MUI_PAGE_UNINSTALLER_PREFIX}ALTERNATE_PAGE

      GetDlgItem $MUI_TEMP1 $MUI_HWND ${UMUI_INTERNAL_AIDTITLE}
      !insertmacro UMUI_IOPAGECTLTRANSPARENT_INIT $MUI_TEMP1
      CreateFont $MUI_TEMP2 "$(^Font)" "${UMUI_WELCOMEFINISHABORT_TITLE_FONTSIZE}" "700"
      SendMessage $MUI_TEMP1 ${WM_SETFONT} $MUI_TEMP2 0
      GetDlgItem $MUI_TEMP1 $MUI_HWND ${UMUI_INTERNAL_AIDTEXT}
      !insertmacro UMUI_IOPAGECTLTRANSPARENT_INIT $MUI_TEMP1

    !else

      ;alternate page
      GetDlgItem $MUI_TEMP1 $MUI_HWND ${UMUI_INTERNAL_AIDTITLE}
      CreateFont $MUI_TEMP2 "MS Sans Serif" "${UMUI_WELCOMEFINISHABORT_TITLE_FONTSIZE}" "700"
      SendMessage $MUI_TEMP1 ${WM_SETFONT} $MUI_TEMP2 $MUI_TEMP2
      !insertmacro UMUI_IOPAGECTLTRANSPARENT_INIT $MUI_TEMP1
      GetDlgItem $MUI_TEMP1 $MUI_HWND ${UMUI_INTERNAL_AIDTEXT}
      !insertmacro UMUI_IOPAGECTLTRANSPARENT_INIT $MUI_TEMP1

    !endif


    !ifdef UMUI_ABORTPAGE_LINK
      GetDlgItem $MUI_TEMP1 $MUI_HWND ${UMUI_INTERNAL_AIDLINK}
      !ifdef UMUI_${MUI_PAGE_UNINSTALLER_PREFIX}PAGEBGIMAGE
        SetCtlColors $MUI_TEMP1 "${UMUI_ABORTPAGE_LINK_COLOR}" "transparent"
      !else
        SetCtlColors $MUI_TEMP1 "${UMUI_ABORTPAGE_LINK_COLOR}" "${MUI_BGCOLOR}"
      !endif
    !endif

    GetDlgItem $MUI_TEMP1 $HWNDPARENT 3
    EnableWindow $MUI_TEMP1 0

    !insertmacro MUI_PAGE_FUNCTION_CUSTOM SHOW

    !insertmacro INSTALLOPTIONS_SHOW

    LockWindow on

!ifdef USE_MUIEx
;-----------------
    GetDlgItem $MUI_TEMP1 $HWNDPARENT 1028
    ShowWindow $MUI_TEMP1 ${SW_NORMAL}

    GetDlgItem $MUI_TEMP1 $HWNDPARENT 1256
    ShowWindow $MUI_TEMP1 ${SW_NORMAL}

    GetDlgItem $MUI_TEMP1 $HWNDPARENT 1035
    ShowWindow $MUI_TEMP1 ${SW_NORMAL}

    GetDlgItem $MUI_TEMP1 $HWNDPARENT 1037
    ShowWindow $MUI_TEMP1 ${SW_NORMAL}

    GetDlgItem $MUI_TEMP1 $HWNDPARENT 1038
    ShowWindow $MUI_TEMP1 ${SW_NORMAL}

    GetDlgItem $MUI_TEMP1 $HWNDPARENT 1039
    ShowWindow $MUI_TEMP1 ${SW_NORMAL}
!endif
;-----------------

    GetDlgItem $MUI_TEMP1 $HWNDPARENT 1045
    ShowWindow $MUI_TEMP1 ${SW_HIDE}

    LockWindow off

    !insertmacro UMUI_FIX_BUTTONS_SKIN

  FunctionEnd

  Function "${LEAVE}"

    !insertmacro MUI_PAGE_FUNCTION_CUSTOM LEAVE

    !insertmacro UMUI_DELETE_PLUGINDIR

  FunctionEnd

  !undef UMUI_INTERNAL_ANUMFIELDS
  !undef UMUI_INTERNAL_ANUMFIELDSLINK
  !undef UMUI_INTERNAL_AFIELDTITLE
  !undef UMUI_INTERNAL_AFIELDTEXT
  !undef UMUI_INTERNAL_AFIELDLINK
  !undef UMUI_INTERNAL_AIDTITLE
  !undef UMUI_INTERNAL_AIDTEXT
  !undef UMUI_INTERNAL_AIDLINK
  !undef UMUI_INTERNAL_APOSLINKLEFT

!macroend





!macro UMUI_PAGE_INFORMATION FILE

  !verbose push
  !verbose ${MUI_VERBOSE}

  !insertmacro MUI_PAGE_INIT

  !define /IfNDef UMUI_${MUI_PAGE_UNINSTALLER_PREFIX}INFORMATIONPAGE

  !insertmacro MUI_DEFAULT_IOCONVERT UMUI_INFORMATIONPAGE_TEXT "$(UMUI_TEXT_INFORMATION_INFO_TEXT)"

  PageEx ${MUI_PAGE_UNINSTALLER_FUNCPREFIX}custom

    PageCallbacks ${MUI_PAGE_UNINSTALLER_FUNCPREFIX}mui.InformationPre_${MUI_UNIQUEID} ${MUI_PAGE_UNINSTALLER_FUNCPREFIX}mui.InformationLeave_${MUI_UNIQUEID}

    Caption " "

  PageExEnd

  !insertmacro UMUI_FUNCTION_INFORMATIONPAGE ${MUI_PAGE_UNINSTALLER_FUNCPREFIX}mui.InformationPre_${MUI_UNIQUEID} ${MUI_PAGE_UNINSTALLER_FUNCPREFIX}mui.InformationLeave_${MUI_UNIQUEID}

  !insertmacro MUI_UNSET UMUI_INFORMATIONPAGE_TEXT
  !insertmacro MUI_UNSET UMUI_INFORMATIONPAGE_USE_RICHTEXTFORMAT

  !verbose pop

!macroend


!macro UMUI_UNPAGE_INFORMATION FILE

  !verbose push
  !verbose ${MUI_VERBOSE}

  !insertmacro MUI_UNPAGE_INIT

    !insertmacro UMUI_PAGE_INFORMATION "${FILE}"

  !insertmacro MUI_UNPAGE_END

  !verbose pop

!macroend


!macro UMUI_FUNCTION_INFORMATIONPAGE PRE LEAVE

  Function "${PRE}"

    ; IF setup cancelled
    !insertmacro UMUI_ABORT_IF_INSTALLFLAG_IS ${UMUI_CANCELLED}|${UMUI_MODIFY}|${UMUI_REPAIR}|${UMUI_UPDATE}

    !insertmacro MUI_HEADER_TEXT_PAGE "$(UMUI_TEXT_INFORMATION_TITLE)" "$(UMUI_${MUI_PAGE_UNINSTALLER_PREFIX}TEXT_INFORMATION_SUBTITLE)"

    !insertmacro INSTALLOPTIONS_EXTRACT_AS "${UMUI_INFORMATIONPAGE_INI}" "Information.ini"

    SetOutPath $PLUGINSDIR
    File "${FILE}"

    ; search file names by removing characters before back-slash
    ; $MUI_TEMP1 : file name
    ; $R0 : character to read
    ; $0 : seek
    Push $R0
    Push $0

    StrLen $0 "${FILE}"

    loopfile:
      IntOp $0 $0 - 1
      StrCmp $0 '0' endfile
        StrCpy $R0 "${FILE}" 1 $0
        StrCmp $R0 '\' endfile
          Goto loopfile
    endfile:
    StrCpy $MUI_TEMP1 "${FILE}" "" $0

    StrCpy $R0 $MUI_TEMP1 1
    StrCmp $R0 '\' 0 +2
      StrCpy $MUI_TEMP1 $MUI_TEMP1 "" 1

    Pop $0
    Pop $R0

    ; Determine the file name based on the current language
    ; if '*' was used in the file name, it will be replaced by the $LANGUAGE
    !insertmacro UMUI_STRREPLACE $MUI_TEMP2 "*" "$LANGUAGE" $MUI_TEMP1
    IfFileExists '$PLUGINSDIR\$MUI_TEMP2' fileFound
      ClearErrors
      !insertmacro UMUI_STRREPLACE $MUI_TEMP2 "*" "" $MUI_TEMP1
      IfFileExists '$PLUGINSDIR\$MUI_TEMP2' fileFound
        StrCpy $MUI_TEMP2 ""
    fileFound:
    StrCpy $MUI_TEMP1 $MUI_TEMP2

    !insertmacro MUI_PAGE_FUNCTION_CUSTOM PRE

    !ifdef UMUI_INFORMATIONPAGE_USE_RICHTEXTFORMAT

      !ifndef UMUI_USE_INSTALLOPTIONSEX
        !error "The Rich Text Control that you want to use with the UMUI_USE_INSTALLOPTIONSEX define work only with InstallOptionEx but it seen that you don't use it. Use the define UMUI_USE_INSTALLOPTIONSEX"
      !endif

      !insertmacro INSTALLOPTIONS_WRITE "Information.ini" "Field 2" Type "RichText"

      StrCmp $MUI_TEMP1 "" fileNotFound
      !insertmacro INSTALLOPTIONS_WRITE "Information.ini" "Field 2" State '$PLUGINSDIR\$MUI_TEMP1'

      !insertmacro INSTALLOPTIONS_WRITE "Information.ini" "Field 2" Notify ONCLICK

    !else

      StrCmp $MUI_TEMP1 "" fileNotFound

      ; $MUI_TEMP1 : txt file
      ; $MUI_TEMP2 : ini file
      ; $R0 : text read on one line
      ; $R1 : test if the end of line is $\r$\n
      ; $0 : 1 if UTF16LE, 0 if ANSI

      Push $R1
      Push $R0
      Push $0

      FlushINI "$PLUGINSDIR\Information.ini"

      ClearErrors
      !ifdef NSIS_UNICODE
        !insertmacro UMUI_FILE_IS_UTF16LE "$PLUGINSDIR\$MUI_TEMP1" $0
      !endif
      IfErrors doneWrite

      FileOpen $MUI_TEMP1 "$PLUGINSDIR\$MUI_TEMP1" r
      IfErrors 0 +2
        Abort
      FileOpen $MUI_TEMP2 "$PLUGINSDIR\Information.ini" a
      IfErrors 0 +2
        Abort
      !ifdef NSIS_UNICODE
        FileSeek $MUI_TEMP2 -4 END
        FileWriteUTF16LE $MUI_TEMP2 "$\""
      !else
        FileSeek $MUI_TEMP2 -2 END
        FileWrite $MUI_TEMP2 "$\""
      !endif
      IfErrors doneWrite

      loopWrite:
        !ifdef NSIS_UNICODE
          StrCmp $0 1 0 +3 ; if UTF16LE
            FileReadUTF16LE $MUI_TEMP1 $R0
            Goto +2
        !endif
        FileRead $MUI_TEMP1 $R0
        IfErrors doneWrite ; if End Of File

        StrCpy $R1 "$R0" "" -1
        StrCmp $R1 $\n 0 write
          StrCpy $R0 "$R0" -1
          StrCpy $R1 "$R0" "" -1
          StrCmp $R1 $\r 0 +2
            StrCpy $R0 "$R0" -1
          StrCpy $R0 "$R0\r\n"

        write:
        !ifdef NSIS_UNICODE
          FileWriteUTF16LE $MUI_TEMP2 "$R0"
        !else
          FileWrite $MUI_TEMP2 "$R0"
        !endif
        Goto loopWrite
      doneWrite:
      !ifdef NSIS_UNICODE
        FileWriteUTF16LE $MUI_TEMP2 "$\""
      !else
        FileWrite $MUI_TEMP2 "$\""
      !endif

      FileClose $MUI_TEMP1
      FileClose $MUI_TEMP2
      ClearErrors

      Pop $0
      Pop $R0
      Pop $R1

    !endif

    fileNotFound:

    !insertmacro MUI_INSTALLOPTIONS_WRITE_DEFAULTCONVERT "Information.ini" "Field 1" "Text" "UMUI_INFORMATIONPAGE_TEXT"

    !insertmacro MUI_PAGE_FUNCTION_CUSTOM SHOW

    !insertmacro INSTALLOPTIONS_DISPLAY "Information.ini"

    !insertmacro UMUI_FIX_BUTTONS_SKIN

  FunctionEnd

  Function "${LEAVE}"

    !insertmacro MUI_PAGE_FUNCTION_CUSTOM LEAVE

    !ifdef UMUI_INFORMATIONPAGE_USE_RICHTEXTFORMAT

      !insertmacro INSTALLOPTIONS_READ $MUI_TEMP1 "Information.ini" "Settings" Notify
      StrCmp $MUI_TEMP1 "ONNEXT" +2 0
        Abort

    !endif

  FunctionEnd

!macroend

!macro UMUI_FILE_IS_UTF16LE FILE RESULT_VAR
  Push $2
  Push $1

  StrCpy ${RESULT_VAR} 0  ; is not UFT16LE
  FileOpen $2 "${FILE}" r
  FileReadByte $2 $1
  IntCmpU $1 0xFF "" doneUTF16LE doneUTF16LE
  FileReadByte $2 $1
  IntCmpU $1 0xFE "" doneUTF16LE doneUTF16LE
  StrCpy ${RESULT_VAR} 1  ; is UFT16LE
  doneUTF16LE:
    FileClose $2

  Pop $1
  Pop $2
!macroend



!macro UMUI_PAGE_ADDITIONALTASKS ADDTASKS_FUNC

  !verbose push
  !verbose ${MUI_VERBOSE}

  !insertmacro MUI_PAGE_INIT

  !define /IfNDef UMUI_${MUI_PAGE_UNINSTALLER_PREFIX}ADDITIONALTASKSPAGE

  !insertmacro MUI_DEFAULT_IOCONVERT UMUI_ADDITIONALTASKSPAGE_TEXT_TOP "$(UMUI_${MUI_PAGE_UNINSTALLER_PREFIX}TEXT_ADDITIONALTASKS_INFO_TEXT)"

  !ifndef UMUI_VAR_UMUI_TEMP3
    Var UMUI_TEMP3
    !define UMUI_VAR_UMUI_TEMP3
  !endif

  !ifndef UMUI_VAR_UMUI_TEMP4
    Var UMUI_TEMP4
    !define UMUI_VAR_UMUI_TEMP4
  !endif

  !ifdef UMUI_ADDITIONALTASKS_REGISTRY_VALUENAME
    !ifndef UMUI_ADDITIONALTASKS_REGISTRY_ROOT
      !ifdef UMUI_PARAMS_REGISTRY_ROOT
        !define UMUI_ADDITIONALTASKS_REGISTRY_ROOT "${UMUI_PARAMS_REGISTRY_ROOT}"
      !else
        !error "For UMUI_ADDITIONALTASKS_REGISTRY_VALUENAME, the UMUI_ADDITIONALTASKS_REGISTRY_ROOT & UMUI_ADDITIONALTASKS_REGISTRY_KEY parameters or else the UMUI_PARAMS_REGISTRY_ROOT & UMUI_PARAMS_REGISTRY_KEY global parameters must be defined."
      !endif
    !endif
    !ifndef UMUI_ADDITIONALTASKS_REGISTRY_KEY
      !ifdef UMUI_PARAMS_REGISTRY_KEY
        !define UMUI_ADDITIONALTASKS_REGISTRY_KEY "${UMUI_PARAMS_REGISTRY_KEY}"
      !else
        !error "For UMUI_ADDITIONALTASKS_REGISTRY_VALUENAME, the UMUI_ADDITIONALTASKS_REGISTRY_ROOT & UMUI_ADDITIONALTASKS_REGISTRY_KEY parameters or else the UMUI_PARAMS_REGISTRY_ROOT & UMUI_PARAMS_REGISTRY_KEY global parameters must be defined."
      !endif
    !endif
  !endif

  PageEx ${MUI_PAGE_UNINSTALLER_FUNCPREFIX}custom

    PageCallbacks ${MUI_PAGE_UNINSTALLER_FUNCPREFIX}mui.AdditionalTasksPre_${MUI_UNIQUEID} ${MUI_PAGE_UNINSTALLER_FUNCPREFIX}mui.AdditionalTasksLeave_${MUI_UNIQUEID}

    Caption " "

  PageExEnd

  !insertmacro UMUI_FUNCTION_ADDITIONALTASKSPAGE ${MUI_PAGE_UNINSTALLER_FUNCPREFIX}mui.AdditionalTasksPre_${MUI_UNIQUEID} ${MUI_PAGE_UNINSTALLER_FUNCPREFIX}mui.AdditionalTasksLeave_${MUI_UNIQUEID}

  !undef UMUI_ADDITIONALTASKSPAGE_TEXT_TOP

  !verbose pop

!macroend

!macro UMUI_UNPAGE_ADDITIONALTASKS ADDTASKS_FUNC

  !verbose push
  !verbose ${MUI_VERBOSE}

  !insertmacro MUI_UNPAGE_INIT

    !insertmacro UMUI_PAGE_ADDITIONALTASKS ${ADDTASKS_FUNC}

  !insertmacro MUI_UNPAGE_END

  !verbose pop

!macroend

!macro UMUI_FUNCTION_ADDITIONALTASKSPAGE PRE LEAVE

  Function "${PRE}"

    ; Bodenseematze-2016-09-15: missing PRE-Function support added:
    !insertmacro MUI_PAGE_FUNCTION_CUSTOM PRE

    !insertmacro MUI_HEADER_TEXT_PAGE "$(UMUI_TEXT_ADDITIONALTASKS_TITLE)" "$(UMUI_TEXT_ADDITIONALTASKS_SUBTITLE)"

    IfFileExists "$PLUGINSDIR\AdditionalTasks${ADDTASKS_FUNC}.ini" alreadyExists

      !insertmacro INSTALLOPTIONS_EXTRACT_AS "${UMUI_ADDITIONALTASKSPAGE_INI}" "AdditionalTasks${ADDTASKS_FUNC}.ini"

      !insertmacro MUI_INSTALLOPTIONS_WRITE_DEFAULTCONVERT "AdditionalTasks${ADDTASKS_FUNC}.ini" "Field 1" "Text" "UMUI_ADDITIONALTASKSPAGE_TEXT_TOP"

      StrCpy $UMUI_TEMP3 1   ; number of field
      StrCpy $UMUI_TEMP4 24  ; height of all fields

      StrCpy $MUI_TEMP1 "AdditionalTasks${ADDTASKS_FUNC}.ini"  ; name of the ini file
      Push $MUI_TEMP1

      Call "${ADDTASKS_FUNC}"

      ; IF page skipped save
      !ifdef UMUI_ADDITIONALTASKS_REGISTRY_VALUENAME
        !insertmacro UMUI_INTERNAL_ADDITIONALTASKSPAGE_ADDPARAMTOSAVETOREGISTRY
      !endif

    alreadyExists:

    ; IF setup cancelled or setuptype choosen
    !insertmacro UMUI_ABORT_IF_INSTALLFLAG_IS ${UMUI_CANCELLED}|${UMUI_MINIMAL}|${UMUI_STANDARD}|${UMUI_COMPLETE}|${UMUI_MODIFY}|${UMUI_REPAIR}|${UMUI_UPDATE}

    !insertmacro MUI_PAGE_FUNCTION_CUSTOM SHOW

    !insertmacro INSTALLOPTIONS_DISPLAY "AdditionalTasks${ADDTASKS_FUNC}.ini"

    !insertmacro UMUI_FIX_BUTTONS_SKIN

  FunctionEnd

  Function "${LEAVE}"

    !insertmacro INSTALLOPTIONS_READ $UMUI_TEMP3 "AdditionalTasks${ADDTASKS_FUNC}.ini" "Settings" NumFields
    StrCpy $UMUI_TEMP4 1 ;init at 1 because of the label text top

    ;do
    loop:

      IntOp $UMUI_TEMP4 $UMUI_TEMP4 + 1

      ;get task ID
      !insertmacro INSTALLOPTIONS_READ $MUI_TEMP1 "AdditionalTasks${ADDTASKS_FUNC}.ini" "Field $UMUI_TEMP4" TaskID
      ;if field is not a CheckBox or a RadioButton break
      StrCmp $MUI_TEMP1 "" endloop 0

        ;get task State
        !insertmacro INSTALLOPTIONS_READ $MUI_TEMP2 "AdditionalTasks${ADDTASKS_FUNC}.ini" "Field $UMUI_TEMP4" State
        ;save task State
        !insertmacro INSTALLOPTIONS_WRITE "AdditionalTasksList.ini" "Task $MUI_TEMP1" State "$MUI_TEMP2"

    endloop:
    ;while $UMUI_TEMP4 < $UMUI_TEMP3
    IntCmp $UMUI_TEMP4 $UMUI_TEMP3 0 loop 0

    ClearErrors

    ;save into the registery
    !ifdef UMUI_ADDITIONALTASKS_REGISTRY_VALUENAME
      !insertmacro UMUI_INTERNAL_ADDITIONALTASKSPAGE_ADDPARAMTOSAVETOREGISTRY
    !endif


    !insertmacro MUI_PAGE_FUNCTION_CUSTOM LEAVE

  FunctionEnd

!macroend

!macro UMUI_INTERNAL_ADDITIONALTASKSPAGE_ADDPARAMTOSAVETOREGISTRY

  Push $R9

  !insertmacro INSTALLOPTIONS_READ $UMUI_TEMP3 "AdditionalTasksList.ini" "Settings" NumTasks
  StrCpy $UMUI_TEMP4 0 ;init at 1 because the label text top
  StrCpy $R9 ""

  ;do
  loops:

    ;get task ID
    !insertmacro INSTALLOPTIONS_READ $MUI_TEMP1 "AdditionalTasksList.ini" "$UMUI_TEMP4" TaskID
    !insertmacro INSTALLOPTIONS_READ $MUI_TEMP2 "AdditionalTasksList.ini" "Task $MUI_TEMP1" State

    StrCpy $R9 "$R9|$MUI_TEMP1=$MUI_TEMP2"

    IntOp $UMUI_TEMP4 $UMUI_TEMP4 + 1

  ;while $UMUI_TEMP4 < $UMUI_TEMP3
  IntCmp $UMUI_TEMP4 $UMUI_TEMP3 0 loops 0

  !insertmacro UMUI_ADDPARAMTOSAVETOREGISTRYKEY ${UMUI_ADDITIONALTASKS_REGISTRY_ROOT} "${UMUI_ADDITIONALTASKS_REGISTRY_KEY}" "${UMUI_ADDITIONALTASKS_REGISTRY_VALUENAME}" "$R9"

  Pop $R9

  ClearErrors

!macroend

!macro UMUI_INTERNAL_ADDITIONALTASKSPAGE_REGISTRY_SET_STATE ID DEFSTATE

  !verbose push
  !verbose ${MUI_VERBOSE}

  !ifdef UMUI_UNIQUEID
    !undef UMUI_UNIQUEID
  !endif

  !define UMUI_UNIQUEID ${__LINE__}

  ;Search in the registery
  !ifdef UMUI_ADDITIONALTASKS_REGISTRY_VALUENAME
    Push $0
    Push $1
    Push $2
    Push $3
    Push $4

    ReadRegStr $0 ${UMUI_ADDITIONALTASKS_REGISTRY_ROOT} "${UMUI_ADDITIONALTASKS_REGISTRY_KEY}" "${UMUI_ADDITIONALTASKS_REGISTRY_VALUENAME}"
    StrCmp $0 "" end${UMUI_UNIQUEID}

      ;search the state of the ID
      ClearErrors

      StrCpy $4 "|${ID}="  ; string to search
      StrLen $3 $4          ; len of the task to found

      loop${UMUI_UNIQUEID}:
        StrCpy $2 $0 $3

        StrCmp $2 $4 found${UMUI_UNIQUEID} 0
          StrLen $5 $0
          IntCmp $5 $3 end${UMUI_UNIQUEID} end${UMUI_UNIQUEID} 0  ;if there is not suffitiently char end
            StrCpy $0 $0 "" 1
            Goto loop${UMUI_UNIQUEID}

        found${UMUI_UNIQUEID}:
          StrCpy $2 $0 1 $3

          !insertmacro INSTALLOPTIONS_WRITE "$MUI_TEMP1" "Field $UMUI_TEMP3" State "0"
          StrCmp $2 1 0 end${UMUI_UNIQUEID}
            !insertmacro INSTALLOPTIONS_WRITE "$MUI_TEMP1" "Field $UMUI_TEMP3" State "1"

    end${UMUI_UNIQUEID}:
    ClearErrors

    Pop $4
    Pop $3
    Pop $2
    Pop $1
    Pop $0
  !endif

  !undef UMUI_UNIQUEID

  !verbose pop

!macroend





!macro UMUI_ADDITIONALTASKSPAGE_ADD_LABEL STR

  !verbose push
  !verbose ${MUI_VERBOSE}

  Pop $MUI_TEMP1
  Pop $MUI_TEMP2

  IntOp $UMUI_TEMP3 $UMUI_TEMP3 + 1
  !insertmacro INSTALLOPTIONS_WRITE "$MUI_TEMP1" "Settings" NumFields "$UMUI_TEMP3"

  !insertmacro INSTALLOPTIONS_WRITE "$MUI_TEMP1" "Field $UMUI_TEMP3" Type "Label"
  !insertmacro INSTALLOPTIONS_WRITE "$MUI_TEMP1" "Field $UMUI_TEMP3" Text "${STR}"

  !insertmacro INSTALLOPTIONS_WRITE "$MUI_TEMP1" "Field $UMUI_TEMP3" Left "5"
  !insertmacro INSTALLOPTIONS_WRITE "$MUI_TEMP1" "Field $UMUI_TEMP3" Right "-5"

  IntOp $UMUI_TEMP4 $UMUI_TEMP4 + 6
  !insertmacro INSTALLOPTIONS_WRITE "$MUI_TEMP1" "Field $UMUI_TEMP3" Top "$UMUI_TEMP4"

  Push $0
  Push $1
  Push $2
  Push $3

  !ifdef UMUI_UNIQUEID
    !undef UMUI_UNIQUEID
  !endif

  !define UMUI_UNIQUEID ${__LINE__}

  StrCpy $0 "${STR}"
  StrCpy $2 0
  StrCpy $3 0

  loop${UMUI_UNIQUEID}:
    StrCpy $1 $0 4
    IntOp $2 $2 + 1

    StrCmp $1 "" end${UMUI_UNIQUEID} 0

      StrCmp $1 "\r\n" 0 +3  ; a new line if \n\r appear
        IntOp $3 $3 + 1
        StrCpy $2 0

      StrCmp $2 75 0 +3      ; a new line if character number on this line is > 75
        IntOp $3 $3 + 1
        StrCpy $2 0

      StrCpy $0 $0 "" 1
      Goto loop${UMUI_UNIQUEID}
  end${UMUI_UNIQUEID}:

  !undef UMUI_UNIQUEID

  IntOp $MUI_TEMP2 $3 * 8

  Pop $3
  Pop $2
  Pop $1
  Pop $0

  IntOp $UMUI_TEMP4 $UMUI_TEMP4 + 12
  IntOp $UMUI_TEMP4 $UMUI_TEMP4 + $MUI_TEMP2
  !insertmacro INSTALLOPTIONS_WRITE "$MUI_TEMP1" "Field $UMUI_TEMP3" Bottom "$UMUI_TEMP4"

  !ifndef UMUI_NEWGROUP
    !define UMUI_NEWGROUP
  !endif

  ClearErrors

  Push $MUI_TEMP2
  Push $MUI_TEMP1

  !verbose pop

!macroend

!macro UMUI_ADDITIONALTASKSPAGE_ADD_TASK ID DEFSTATE STR

  !verbose push
  !verbose ${MUI_VERBOSE}

  Pop $MUI_TEMP1
  Pop $MUI_TEMP2

  IntOp $UMUI_TEMP3 $UMUI_TEMP3 + 1
  !insertmacro INSTALLOPTIONS_WRITE "$MUI_TEMP1" "Settings" NumFields "$UMUI_TEMP3"

  !insertmacro INSTALLOPTIONS_WRITE "$MUI_TEMP1" "Field $UMUI_TEMP3" Type "CheckBox"
  !insertmacro INSTALLOPTIONS_WRITE "$MUI_TEMP1" "Field $UMUI_TEMP3" Text "${STR}"

  !insertmacro INSTALLOPTIONS_WRITE "$MUI_TEMP1" "Field $UMUI_TEMP3" State "${DEFSTATE}"
  !insertmacro UMUI_INTERNAL_ADDITIONALTASKSPAGE_REGISTRY_SET_STATE "${ID}" "${DEFSTATE}"

  !insertmacro INSTALLOPTIONS_WRITE "$MUI_TEMP1" "Field $UMUI_TEMP3" TaskID "${ID}"

  !insertmacro INSTALLOPTIONS_WRITE "$MUI_TEMP1" "Field $UMUI_TEMP3" Left "10"
  !insertmacro INSTALLOPTIONS_WRITE "$MUI_TEMP1" "Field $UMUI_TEMP3" Right "-10"
  !insertmacro INSTALLOPTIONS_WRITE "$MUI_TEMP1" "Field $UMUI_TEMP3" Top "$UMUI_TEMP4"

  IntOp $UMUI_TEMP4 $UMUI_TEMP4 + 12
  !insertmacro INSTALLOPTIONS_WRITE "$MUI_TEMP1" "Field $UMUI_TEMP3" Bottom "$UMUI_TEMP4"

  !insertmacro INSTALLOPTIONS_READ $MUI_TEMP2 "$MUI_TEMP1" "Field $UMUI_TEMP3" State
  !insertmacro INSTALLOPTIONS_WRITE "AdditionalTasksList.ini" "Task ${ID}" State "$MUI_TEMP2"

  !insertmacro INSTALLOPTIONS_READ $MUI_TEMP2 "AdditionalTasksList.ini" "Settings" NumTasks
  StrCmp $MUI_TEMP2 "" 0 +2
    StrCpy $MUI_TEMP2 0
  !insertmacro INSTALLOPTIONS_WRITE "AdditionalTasksList.ini" "$MUI_TEMP2" TaskID "${ID}"
  IntOp $MUI_TEMP2 $MUI_TEMP2 + 1
  !insertmacro INSTALLOPTIONS_WRITE "AdditionalTasksList.ini" "Settings" NumTasks "$MUI_TEMP2"

  ClearErrors

  Push $MUI_TEMP2
  Push $MUI_TEMP1

  !verbose pop

!macroend

!macro UMUI_ADDITIONALTASKSPAGE_ADD_TASK_RADIO ID DEFSTATE STR

  !verbose push
  !verbose ${MUI_VERBOSE}

  Pop $MUI_TEMP1
  Pop $MUI_TEMP2

  IntOp $UMUI_TEMP3 $UMUI_TEMP3 + 1
  !insertmacro INSTALLOPTIONS_WRITE "$MUI_TEMP1" "Settings" NumFields "$UMUI_TEMP3"

  !insertmacro INSTALLOPTIONS_WRITE "$MUI_TEMP1" "Field $UMUI_TEMP3" Type "RadioButton"
  !insertmacro INSTALLOPTIONS_WRITE "$MUI_TEMP1" "Field $UMUI_TEMP3" Text "${STR}"

  !insertmacro INSTALLOPTIONS_WRITE "$MUI_TEMP1" "Field $UMUI_TEMP3" State "${DEFSTATE}"
  !insertmacro UMUI_INTERNAL_ADDITIONALTASKSPAGE_REGISTRY_SET_STATE "${ID}" "${DEFSTATE}"

  !insertmacro INSTALLOPTIONS_WRITE "$MUI_TEMP1" "Field $UMUI_TEMP3" TaskID "${ID}"

  !insertmacro INSTALLOPTIONS_WRITE "$MUI_TEMP1" "Field $UMUI_TEMP3" Left "10"
  !insertmacro INSTALLOPTIONS_WRITE "$MUI_TEMP1" "Field $UMUI_TEMP3" Right "-10"
  !insertmacro INSTALLOPTIONS_WRITE "$MUI_TEMP1" "Field $UMUI_TEMP3" Top "$UMUI_TEMP4"

  IntOp $UMUI_TEMP4 $UMUI_TEMP4 + 12
  !insertmacro INSTALLOPTIONS_WRITE "$MUI_TEMP1" "Field $UMUI_TEMP3" Bottom "$UMUI_TEMP4"

  !ifdef UMUI_NEWGROUP
    !insertmacro INSTALLOPTIONS_WRITE "$MUI_TEMP1" "Field $UMUI_TEMP3" Flags "GROUP"
    !undef UMUI_NEWGROUP
  !endif

  !insertmacro INSTALLOPTIONS_READ $MUI_TEMP2 "$MUI_TEMP1" "Field $UMUI_TEMP3" State
  !insertmacro INSTALLOPTIONS_WRITE "AdditionalTasksList.ini" "Task ${ID}" State "$MUI_TEMP2"

  !insertmacro INSTALLOPTIONS_READ $MUI_TEMP2 "AdditionalTasksList.ini" "Settings" NumTasks
  StrCmp $MUI_TEMP2 "" 0 +2
    StrCpy $MUI_TEMP2 0
  !insertmacro INSTALLOPTIONS_WRITE "AdditionalTasksList.ini" "$MUI_TEMP2" TaskID "${ID}"
  IntOp $MUI_TEMP2 $MUI_TEMP2 + 1
  !insertmacro INSTALLOPTIONS_WRITE "AdditionalTasksList.ini" "Settings" NumTasks "$MUI_TEMP2"

  ClearErrors

  Push $MUI_TEMP2
  Push $MUI_TEMP1

  !verbose pop

!macroend

!macro UMUI_ADDITIONALTASKSPAGE_ADD_EMPTYLINE

  !verbose push
  !verbose ${MUI_VERBOSE}

  IntOp $UMUI_TEMP4 $UMUI_TEMP4 + 6

  !verbose pop

!macroend

!macro UMUI_ADDITIONALTASKSPAGE_ADD_LINE

  !verbose push
  !verbose ${MUI_VERBOSE}

  Pop $MUI_TEMP1

  IntOp $UMUI_TEMP3 $UMUI_TEMP3 + 1
  !insertmacro INSTALLOPTIONS_WRITE "$MUI_TEMP1" "Settings" NumFields "$UMUI_TEMP3"

  !insertmacro INSTALLOPTIONS_WRITE "$MUI_TEMP1" "Field $UMUI_TEMP3" Type "HLine"
  !insertmacro INSTALLOPTIONS_WRITE "$MUI_TEMP1" "Field $UMUI_TEMP3" Left "5"
  !insertmacro INSTALLOPTIONS_WRITE "$MUI_TEMP1" "Field $UMUI_TEMP3" Right "-5"

  IntOp $UMUI_TEMP4 $UMUI_TEMP4 + 3
  !insertmacro INSTALLOPTIONS_WRITE "$MUI_TEMP1" "Field $UMUI_TEMP3" Top "$UMUI_TEMP4"
  IntOp $UMUI_TEMP4 $UMUI_TEMP4 + 1
  !insertmacro INSTALLOPTIONS_WRITE "$MUI_TEMP1" "Field $UMUI_TEMP3" Bottom "$UMUI_TEMP4"

  Push $MUI_TEMP1

  !verbose pop

!macroend

; listid can be a string containing ID1|ID2|ID3
!macro UMUI_ADDITIONALTASKS_IF_CKECKED LISTID

  !verbose push
  !verbose ${MUI_VERBOSE}

  !ifdef UMUI_UNIQUEID
    !undef UMUI_UNIQUEID
  !endif

  !define UMUI_UNIQUEID ${__LINE__}

  Push $0
  Push $1
  Push $2

  StrCpy $0 "${LISTID}"  ;the sources
  StrCpy $1 ""            ;an id
  StrCpy $MUI_TEMP1 0    ; 0 = false , 1 = true

  loop${UMUI_UNIQUEID}:
    ;copy one id
    loopid${UMUI_UNIQUEID}:
      StrCpy $2 $0 1
      StrCmp $2 "" check${UMUI_UNIQUEID} 0
        StrCpy $0 $0 "" 1
        StrCmp $2 "|" check${UMUI_UNIQUEID} 0
          StrCpy $1 "$1$2"
          Goto loopid${UMUI_UNIQUEID}
    check${UMUI_UNIQUEID}:
      !insertmacro INSTALLOPTIONS_READ $MUI_TEMP1 "AdditionalTasksList.ini" "Task $1" State
      StrCpy $1 ""
      StrCmp $MUI_TEMP1 1 endloop${UMUI_UNIQUEID}
        StrCpy $MUI_TEMP1 0
        StrCmp $2 "" endloop${UMUI_UNIQUEID} loop${UMUI_UNIQUEID}
  endloop${UMUI_UNIQUEID}:

  ClearErrors

  Pop $2
  Pop $1
  Pop $0

  ; if any of VALS is checked goto done
  StrCmp $MUI_TEMP1 1 0 done_${UMUI_UNIQUEID}

  !verbose pop

!macroend

; listid can be a string containing ID1&ID2&ID3
!macro UMUI_ADDITIONALTASKS_IF_NOT_CKECKED LISTID

  !verbose push
  !verbose ${MUI_VERBOSE}

  !ifdef UMUI_UNIQUEID
    !undef UMUI_UNIQUEID
  !endif

  !define UMUI_UNIQUEID ${__LINE__}

  Push $0
  Push $1
  Push $2

  StrCpy $0 "${LISTID}"  ;the sources
  StrCpy $1 ""            ;an id
  StrCpy $MUI_TEMP1 1    ; 0 = false , 1 = true

  loop${UMUI_UNIQUEID}:
    ;copy one id
    loopid${UMUI_UNIQUEID}:
      StrCpy $2 $0 1
      StrCmp $2 "" check${UMUI_UNIQUEID} 0
        StrCpy $0 $0 "" 1
        StrCmp $2 "&" check${UMUI_UNIQUEID} 0
          StrCpy $1 "$1$2"
          Goto loopid${UMUI_UNIQUEID}
    check${UMUI_UNIQUEID}:
      !insertmacro INSTALLOPTIONS_READ $MUI_TEMP1 "AdditionalTasksList.ini" "Task $1" State
      StrCpy $1 ""
      StrCmp $MUI_TEMP1 0 endloop${UMUI_UNIQUEID}
        StrCpy $MUI_TEMP1 1
        StrCmp $2 "" endloop${UMUI_UNIQUEID} loop${UMUI_UNIQUEID}
  endloop${UMUI_UNIQUEID}:

  ClearErrors

  Pop $2
  Pop $1
  Pop $0

  ; if any of VALS is checked goto done
  StrCmp $MUI_TEMP1 0 0 done_${UMUI_UNIQUEID}

  !verbose pop

!macroend

!macro UMUI_ADDITIONALTASKS_ENDIF

  !verbose push
  !verbose ${MUI_VERBOSE}

  done_${UMUI_UNIQUEID}:

  !undef UMUI_UNIQUEID

  !verbose pop

!macroend




!macro UMUI_PAGE_SERIALNUMBER SERIAL_FUNC

  !verbose push
  !verbose ${MUI_VERBOSE}

  !insertmacro MUI_PAGE_INIT

  !define /IfNDef UMUI_${MUI_PAGE_UNINSTALLER_PREFIX}SERIALNUMBERPAGE

  !insertmacro MUI_DEFAULT_IOCONVERT UMUI_SERIALNUMBERPAGE_TEXT_TOP "$(UMUI_TEXT_SERIALNUMBER_INFO_TEXT)"
  !insertmacro MUI_DEFAULT_IOCONVERT UMUI_SERIALNUMBERPAGE_INVALIDATE_TEXT "$(UMUI_TEXT_SERIALNUMBER_INVALIDATE_TEXT)"

  !ifndef UMUI_VAR_UMUI_TEMP3
    Var UMUI_TEMP3
    !define UMUI_VAR_UMUI_TEMP3
  !endif

  !ifndef UMUI_VAR_UMUI_TEMP4
    Var UMUI_TEMP4
    !define UMUI_VAR_UMUI_TEMP4
  !endif

  !ifndef UMUI_VAR_UMUI_SNTEXT
    Var UMUI_SNTEXT
    !define UMUI_VAR_UMUI_SNTEXT
  !endif

  PageEx ${MUI_PAGE_UNINSTALLER_FUNCPREFIX}custom

    PageCallbacks ${MUI_PAGE_UNINSTALLER_FUNCPREFIX}mui.serialnumberPre_${MUI_UNIQUEID} ${MUI_PAGE_UNINSTALLER_FUNCPREFIX}mui.serialnumberLeave_${MUI_UNIQUEID}

    Caption " "

  PageExEnd

  !insertmacro UMUI_FUNCTION_SERIALNUMBERPAGE ${MUI_PAGE_UNINSTALLER_FUNCPREFIX}mui.serialnumberPre_${MUI_UNIQUEID} ${MUI_PAGE_UNINSTALLER_FUNCPREFIX}mui.serialnumberLeave_${MUI_UNIQUEID}

  !undef UMUI_SERIALNUMBERPAGE_TEXT_TOP

  !verbose pop

!macroend

!macro UMUI_UNPAGE_SERIALNUMBER SERIAL_FUNC

  !verbose push
  !verbose ${MUI_VERBOSE}

  !insertmacro MUI_UNPAGE_INIT

    !insertmacro UMUI_PAGE_SERIALNUMBER ${SERIAL_FUNC}

  !insertmacro MUI_UNPAGE_END

  !verbose pop

!macroend

!macro UMUI_FUNCTION_SERIALNUMBERPAGE PRE LEAVE

  Function "${PRE}"

    ; IF setup cancelled or setuptype choosen
    !insertmacro UMUI_ABORT_IF_INSTALLFLAG_IS ${UMUI_CANCELLED}|${UMUI_MODIFY}|${UMUI_REPAIR}|${UMUI_UPDATE}

    ; Bodenseematze-2016-09-15: missing PRE-Function support added:
    !insertmacro MUI_PAGE_FUNCTION_CUSTOM PRE

    !insertmacro MUI_HEADER_TEXT_PAGE "$(UMUI_TEXT_SERIALNUMBER_TITLE)" "$(UMUI_TEXT_SERIALNUMBER_SUBTITLE)"

    IfFileExists "$PLUGINSDIR\SerialNumber_${SERIAL_FUNC}.ini" alreadyExists

      !insertmacro INSTALLOPTIONS_EXTRACT_AS "${UMUI_SERIALNUMBERPAGE_INI}" "SerialNumber_${SERIAL_FUNC}.ini"

      !insertmacro MUI_INSTALLOPTIONS_WRITE_DEFAULTCONVERT "SerialNumber_${SERIAL_FUNC}.ini" "Field 1" "Text" "UMUI_SERIALNUMBERPAGE_TEXT_TOP"

      StrCpy $MUI_TEMP1 "SerialNumber_${SERIAL_FUNC}.ini"  ; name of the ini file
      StrCpy $MUI_TEMP2 0      ; serials counter
      StrCpy $UMUI_TEMP3 1     ; field counter
      StrCpy $UMUI_TEMP4 30    ; height of all fields

      Call "${SERIAL_FUNC}"

      !insertmacro UMUI_SERIALNUMBERPAGE_APPLYFLAGS "SerialNumber_${SERIAL_FUNC}.ini"

      !insertmacro UMUI_SERIALNUMBERPAGE_SAVE "SerialNumber_${SERIAL_FUNC}.ini"

    alreadyExists:

    !insertmacro MUI_PAGE_FUNCTION_CUSTOM SHOW

    !insertmacro INSTALLOPTIONS_DISPLAY "SerialNumber_${SERIAL_FUNC}.ini"

    !insertmacro UMUI_FIX_BUTTONS_SKIN

  FunctionEnd

  Function "${LEAVE}"

    !insertmacro UMUI_IF_INSTALLFLAG_ISNOT ${UMUI_CANCELLED}

    !ifdef UMUI_USE_INSTALLOPTIONSEX

      Push $0
      Push $1
      Push $2
      Push $3
      Push $4

      ; $MUI_TEMP1    : Current field number
      ; $0            : max lenght
      ; $1            : state of the current field
      ; $2            : lenght of the state
      ; $3            : back/next field number
      ; $4            : HWND of the back/next field

      ClearErrors
      !insertmacro INSTALLOPTIONS_READ $MUI_TEMP1 "SerialNumber_${SERIAL_FUNC}.ini" "Settings" State
      StrCmp $MUI_TEMP1 "0" ok 0

        !insertmacro INSTALLOPTIONS_READ $1 "SerialNumber_${SERIAL_FUNC}.ini" "Field $MUI_TEMP1" State

        StrCmp $1 "" 0 next

          !insertmacro INSTALLOPTIONS_READ $3 "SerialNumber_${SERIAL_FUNC}.ini" "Field $MUI_TEMP1" BackField
          IfErrors abort

          !insertmacro INSTALLOPTIONS_READ $4 "SerialNumber_${SERIAL_FUNC}.ini" "Field $3" HWND
          IfErrors abort

            !insertmacro UMUI_INSTALLOPTIONSEX_SETFOCUS $4

        next:

        !insertmacro INSTALLOPTIONS_READ $0 "SerialNumber_${SERIAL_FUNC}.ini" "Field $MUI_TEMP1" MaxLen
        IfErrors abort

          StrLen $2 $1
          StrCmp $2 $0 0 abort

            !insertmacro INSTALLOPTIONS_READ $3 "SerialNumber_${SERIAL_FUNC}.ini" "Field $MUI_TEMP1" NextField
            IfErrors abort

              !insertmacro INSTALLOPTIONS_READ $4 "SerialNumber_${SERIAL_FUNC}.ini" "Field $3" HWND
              IfErrors abort

                !insertmacro UMUI_INSTALLOPTIONSEX_SETFOCUS $4

        abort:

        ClearErrors

        Pop $4
        Pop $3
        Pop $2
        Pop $1
        Pop $0

        Abort

      ok:

      Pop $4
      Pop $3
      Pop $2
      Pop $1
      Pop $0

    !endif

    !insertmacro UMUI_SERIALNUMBERPAGE_APPLYFLAGS "SerialNumber_${SERIAL_FUNC}.ini"

    !insertmacro UMUI_SERIALNUMBERPAGE_SAVE "SerialNumber_${SERIAL_FUNC}.ini"

    !insertmacro MUI_PAGE_FUNCTION_CUSTOM LEAVE

    !insertmacro UMUI_ENDIF_INSTALLFLAG

  FunctionEnd

!macroend


!macro UMUI_SERIALNUMBERPAGE_GET_WINDOWS_REGISTRED_OWNER VAR
    ClearErrors
    ; Windows NT
    ReadRegStr $${VAR} HKLM "SOFTWARE\Microsoft\Windows NT\CurrentVersion" "RegisteredOwner"
    IfErrors 0 +2
        ; Windows 9x
        ReadRegStr $${VAR} HKLM "SOFTWARE\Microsoft\Windows\CurrentVersion" "RegisteredOwner"
    ClearErrors
!macroend

!macro UMUI_SERIALNUMBERPAGE_GET_WINDOWS_REGISTRED_ORGANIZATION VAR
    ClearErrors
    ; Windows NT
    ReadRegStr $${VAR} HKLM "SOFTWARE\Microsoft\Windows NT\CurrentVersion" "RegisteredOrganization"
    IfErrors 0 +2
        ; Windows 9x
        ReadRegStr $${VAR} HKLM "SOFTWARE\Microsoft\Windows\CurrentVersion" "RegisteredOrganization"
    ClearErrors
!macroend



!macro UMUI_SERIALNUMBERPAGE_APPLYFLAGS FILE

  Push $0
  Push $1
  Push $2
  Push $4
  Push $6
  Push $7
  Push $8
  Push $9

  ; $MUI_TEMP2  : serials line number
  ; $0          : System::Call return success if ok
  ; $1          : curent ID
  ; $2          : curent FLAGS
  ; $4          : the curent serial number
  ; $6          : one portion of the $5 serial number
  ; $7          : Is FLAGS == "TOLOWER"
  ; $8          : Is FLAGS == "TOUPPER"
  ; $9          : current field

  !insertmacro INSTALLOPTIONS_READ $MUI_TEMP2 "${FILE}" Settings NumTasks

  StrCpy $4 0

  loopApplyFlags:

    ClearErrors

    IntOp $4 $4 + 1
    IntCmp $4 $MUI_TEMP2 0 0 endApplyFlags

      !insertmacro INSTALLOPTIONS_READ $1 "${FILE}" $4 SerialID
      !insertmacro INSTALLOPTIONS_READ $9 "${FILE}" $4 FirstField
      !insertmacro INSTALLOPTIONS_READ $2 "${FILE}" $4 FLAGS

      !insertmacro UMUI_STRCOUNT "NUMBERS" "$2"
      Pop $7
      IntCmp $7 0 0 loopApplyFlags loopApplyFlags

      !insertmacro UMUI_STRCOUNT "TOLOWER" "$2"
      Pop $7
      !insertmacro UMUI_STRCOUNT "TOUPPER" "$2"
      Pop $8

      ;if $7 = $8 = 0 goto end
      IntCmp $7 0 0 +2 +2
        IntCmp $8 0 loopApplyFlags 0 0

      ;if $7 != 0 && $8 != 0 goto end
      IntCmp $7 0 +2 0 0
        IntCmp $8 0 0 loopApplyFlags loopApplyFlags

      loopSerialApplyFlags:
        !insertmacro INSTALLOPTIONS_READ $6 "${FILE}" "Field $9" State

        ;if flag is lower
        IntCmp $7 0 +2 0 0
        ;then
          System::Call "User32::CharLower(t r6 r6)i"
        ;endif

        ;if flag is upper
        IntCmp $8 0 +2 0 0
        ;then
          System::Call "User32::CharUpper(t r6 r6)i"
        ;endif

        !insertmacro INSTALLOPTIONS_WRITE "${FILE}" "Field $9" State $6

        !insertmacro INSTALLOPTIONS_READ $0 "${FILE}" "Field $9" HWND
        IfErrors +2 0
          SendMessage $0 ${WM_SETTEXT} 0 "STR:$6"
        ClearErrors

        !insertmacro INSTALLOPTIONS_READ $9 "${FILE}" "Field $9" NextField
        IfErrors 0 loopSerialApplyFlags

    Goto loopApplyFlags
  endApplyFlags:

  Pop $9
  Pop $8
  Pop $7
  Pop $6
  Pop $4
  Pop $2
  Pop $1
  Pop $0

!macroend



!macro UMUI_SERIALNUMBERPAGE_SAVE FILE

  Push $0
  Push $1
  Push $2
  Push $3
  Push $4
  Push $5
  Push $6
  Push $7
  Push $8
  Push $9

  ; $MUI_TEMP2  : serials line number
  ; $0          : temp var
  ; $1          : curent ID
  ; $2          : curent FLAGS
  ; $3          : temp var
  ; $4          : the curent serial number
  ; $5          : full serial number
  ; $6          : one portion of the $5 serial number
  ; $7          : temp var
  ; $8          : Is FLAGS == "NODASHS"
  ; $9          : current field

  !insertmacro INSTALLOPTIONS_READ $MUI_TEMP2 "${FILE}" Settings NumTasks

  StrCpy $4 0

  loopSave:

    ClearErrors
    StrCpy $5 ""

    IntOp $4 $4 + 1
    IntCmp $4 $MUI_TEMP2 0 0 endSave

      !insertmacro INSTALLOPTIONS_READ $1 "${FILE}" $4 SerialID
      !insertmacro INSTALLOPTIONS_READ $9 "${FILE}" $4 FirstField
      !insertmacro INSTALLOPTIONS_READ $2 "${FILE}" $4 FLAGS

      !insertmacro UMUI_STRCOUNT "NODASHS" "$2"
      Pop $8

      loopSerial:

        !insertmacro INSTALLOPTIONS_READ $6 "${FILE}" "Field $9" State

        ;if $8 != 0
        IntCmp $8 0 +3 0 0
        ;then
          StrCpy $5 "$5$6"
          Goto +2
        ;else
          StrCpy $5 "$5-$6"
        ;endif

        !insertmacro INSTALLOPTIONS_READ $9 "${FILE}" "Field $9" NextField
        StrCmp $9 "" 0 loopSerial
          ClearErrors

          StrCpy $0 $5 1  ; get first char
          StrCmp $0 "-" 0 +2
            StrCpy $5 $5 "" 1

          !insertmacro INSTALLOPTIONS_WRITE "SerialNumberList.ini" "Serial $1" SN "$5"

          !insertmacro INSTALLOPTIONS_READ $3 "SerialNumberList.ini" "Serial $1" REGISTRY_VALUENAME
          IfErrors loopSave 0

            !insertmacro INSTALLOPTIONS_READ $0 "SerialNumberList.ini" "Serial $1" REGISTRY_ROOT
            !insertmacro INSTALLOPTIONS_READ $7 "SerialNumberList.ini" "Serial $1" REGISTRY_KEY

            !insertmacro UMUI_ADDPARAMTOSAVETOREGISTRYKEY "$0" "$7" "$3" "$5"

    Goto loopSave
  endSave:

  Pop $9
  Pop $8
  Pop $7
  Pop $6
  Pop $5
  Pop $4
  Pop $3
  Pop $2
  Pop $1
  Pop $0

!macroend


!macro UMUI_SERIALNUMBERPAGE_ADD_LINE

  !verbose push
  !verbose ${MUI_VERBOSE}

  IntOp $UMUI_TEMP4 $UMUI_TEMP4 + 6

  !verbose pop

!macroend

!macro UMUI_SERIALNUMBERPAGE_ADD_HLINE

  !verbose push
  !verbose ${MUI_VERBOSE}

  IntOp $UMUI_TEMP3 $UMUI_TEMP3 + 1
  !insertmacro INSTALLOPTIONS_WRITE "$MUI_TEMP1" "Settings" NumFields "$UMUI_TEMP3"

  !insertmacro INSTALLOPTIONS_WRITE "$MUI_TEMP1" "Field $UMUI_TEMP3" Type "HLine"
  !insertmacro INSTALLOPTIONS_WRITE "$MUI_TEMP1" "Field $UMUI_TEMP3" Left "5"
  !insertmacro INSTALLOPTIONS_WRITE "$MUI_TEMP1" "Field $UMUI_TEMP3" Right "-1"

  IntOp $UMUI_TEMP4 $UMUI_TEMP4 + 3
  !insertmacro INSTALLOPTIONS_WRITE "$MUI_TEMP1" "Field $UMUI_TEMP3" Top "$UMUI_TEMP4"
  IntOp $UMUI_TEMP4 $UMUI_TEMP4 + 1
  !insertmacro INSTALLOPTIONS_WRITE "$MUI_TEMP1" "Field $UMUI_TEMP3" Bottom "$UMUI_TEMP4"

  IntOp $UMUI_TEMP4 $UMUI_TEMP4 + 4

  !verbose pop

!macroend

!macro UMUI_SERIALNUMBERPAGE_ADD_LABEL TEXT

  !verbose push
  !verbose ${MUI_VERBOSE}

  IntOp $UMUI_TEMP3 $UMUI_TEMP3 + 1
  !insertmacro INSTALLOPTIONS_WRITE "$MUI_TEMP1" "Settings" NumFields "$UMUI_TEMP3"

  !insertmacro INSTALLOPTIONS_WRITE "$MUI_TEMP1" "Field $UMUI_TEMP3" Type "Label"
  !insertmacro INSTALLOPTIONS_WRITE "$MUI_TEMP1" "Field $UMUI_TEMP3" Text "${TEXT}"
  !insertmacro INSTALLOPTIONS_WRITE "$MUI_TEMP1" "Field $UMUI_TEMP3" Left "5"
  !insertmacro INSTALLOPTIONS_WRITE "$MUI_TEMP1" "Field $UMUI_TEMP3" Right "-5"

  !insertmacro INSTALLOPTIONS_WRITE "$MUI_TEMP1" "Field $UMUI_TEMP3" Top "$UMUI_TEMP4"
  IntOp $UMUI_TEMP4 $UMUI_TEMP4 + 10
  !insertmacro INSTALLOPTIONS_WRITE "$MUI_TEMP1" "Field $UMUI_TEMP3" Bottom "$UMUI_TEMP4"

  !verbose pop

!macroend

; ID:        A unique identifiant for this serial number
; STR:       555 for 3 inputs of 5 characters each
; FLAGS: "", NODASHS, TOUPPER, TOLOWER, NUMBERS, CANBEEMPTY
; DEFAULT:   XXXXX-XXXXX-XXXXX OR XXXXXXXXXXXXXXX
; WIDTH:     The initial width
!macro UMUI_SERIALNUMBERPAGE_CREATE ID STR FLAGS DEFAULT TEXT WIDTH

  !define UMUI_UNIQUEIDSN ${__LINE__}

  Push $0
  Push $1
  Push $2
  Push $3
  Push $4
  Push $5
  Push $6
  Push $7
  Push $8
  Push $9
  Push $R0

  ; $MUI_TEMP1  : name of the ini file
  ; $MUI_TEMP2  : serials line counter
  ; $UMUI_TEMP3 : field counter for all the page
  ; $UMUI_TEMP4 : current height of all fields
  ; $0          : source str (555 for 3 inputs of 5 characters each)
  ; $1          : temp var
  ; $2          : one of the $0 numbers
  ; $3          : the current width
  ; $4          : the curent serial value
  ; $5          : the next chars of the curent serial value
  ; $6          : one portion of the $5 serial number
  ; $7          : temp var
  ; $8          : Is FLAGS == "NUMBERS"
  ; $9          : first field
  ; $R0         : Is FLAGS == "CANBEEMPTY"

  StrCpy $0 "${STR}"
  StrCpy $7 0
  StrCpy $3 "${WIDTH}"

  !ifdef UMUI_SERIALNUMBERPAGE_SERIAL_REGISTRY_VALUENAME
    !ifndef UMUI_SERIALNUMBERPAGE_SERIAL_REGISTRY_ROOT
      !ifdef UMUI_PARAMS_REGISTRY_ROOT
        !define UMUI_SERIALNUMBERPAGE_SERIAL_REGISTRY_ROOT "${UMUI_PARAMS_REGISTRY_ROOT}"
      !else
        !error "For UMUI_SERIALNUMBERPAGE_SERIAL_REGISTRY_VALUENAME, the UMUI_SERIALNUMBERPAGE_SERIAL_REGISTRY_ROOT & UMUI_SERIALNUMBERPAGE_SERIAL_REGISTRY_KEY parameters or else the UMUI_PARAMS_REGISTRY_ROOT & UMUI_PARAMS_REGISTRY_KEY global parameters must be defined."
      !endif
    !endif
    !ifndef UMUI_SERIALNUMBERPAGE_SERIAL_REGISTRY_KEY
      !ifdef UMUI_PARAMS_REGISTRY_KEY
        !define UMUI_SERIALNUMBERPAGE_SERIAL_REGISTRY_KEY "${UMUI_PARAMS_REGISTRY_KEY}"
      !else
        !error "For UMUI_SERIALNUMBERPAGE_SERIAL_REGISTRY_VALUENAME, the UMUI_SERIALNUMBERPAGE_SERIAL_REGISTRY_ROOT & UMUI_SERIALNUMBERPAGE_SERIAL_REGISTRY_KEY parameters or else the UMUI_PARAMS_REGISTRY_ROOT & UMUI_PARAMS_REGISTRY_KEY global parameters must be defined."
      !endif
    !endif

    ClearErrors
    ReadRegStr $5 "${UMUI_SERIALNUMBERPAGE_SERIAL_REGISTRY_ROOT}" "${UMUI_SERIALNUMBERPAGE_SERIAL_REGISTRY_KEY}" "${UMUI_SERIALNUMBERPAGE_SERIAL_REGISTRY_VALUENAME}"
    IfErrors 0 +2
      StrCpy $5 "${DEFAULT}"
    ClearErrors
  !else
    StrCpy $5 "${DEFAULT}"
  !endif

  StrCpy $4 $5

  !insertmacro UMUI_STRCOUNT "NUMBERS" "${FLAGS}"
  Pop $8
  !insertmacro UMUI_STRCOUNT "CANBEEMPTY" "${FLAGS}"
  Pop $R0

  ;foreach number of $0 AS $2
  loop1${UMUI_UNIQUEIDSN}:
    StrCpy $2 $0 1 ; Get the next source char

    StrCmp $2 "" done1${UMUI_UNIQUEIDSN} ; Abort when none left
      StrCpy $0 $0 "" 1 ; Remove it from the source

      IntOp $UMUI_TEMP3 $UMUI_TEMP3 + 1

      ; add the on text change notify if installoptionsex
      !ifdef UMUI_USE_INSTALLOPTIONSEX
        StrLen $1 "${STR}"
        StrCmp $1 1 endTextChange${UMUI_UNIQUEIDSN} 0
          !insertmacro INSTALLOPTIONS_WRITE "$MUI_TEMP1" "Field $UMUI_TEMP3" Notify ONTEXTCHANGE
        endTextChange${UMUI_UNIQUEIDSN}:
      !endif

      !insertmacro INSTALLOPTIONS_WRITE "$MUI_TEMP1" "Field $UMUI_TEMP3" Type "text"

      changeLine${UMUI_UNIQUEIDSN}:
        !insertmacro INSTALLOPTIONS_WRITE "$MUI_TEMP1" "Field $UMUI_TEMP3" Left "$3"

        ;if $2 = 0
        IntCmp $2 0 0 +3 +3
        ;then
          StrCpy $3 -1
          Goto +3
        ;else
          IntOp $1 $2 * 7
          IntOp $3 $1 + $3
        ;endif

!ifdef USE_MUIEx | UMUI_ULTRAMODERN_SMALL
;----------------
        IntCmp $3 300 +4 +4 0
!else
;----------------
        IntCmp $3 315 +4 +4 0
!endif
;----------------
        StrCpy $3 ${WIDTH}
        IntOp $UMUI_TEMP4 $UMUI_TEMP4 + 14
      Goto changeLine${UMUI_UNIQUEIDSN}

      !insertmacro INSTALLOPTIONS_WRITE "$MUI_TEMP1" "Field $UMUI_TEMP3" Right "$3"
      !insertmacro INSTALLOPTIONS_WRITE "$MUI_TEMP1" "Field $UMUI_TEMP3" Top "$UMUI_TEMP4"
      IntOp $UMUI_TEMP4 $UMUI_TEMP4 + 12
      !insertmacro INSTALLOPTIONS_WRITE "$MUI_TEMP1" "Field $UMUI_TEMP3" Bottom "$UMUI_TEMP4"
      IntOp $UMUI_TEMP4 $UMUI_TEMP4 - 12

      ;if $2 = 0       ; no limit
      IntCmp $2 0 0 notnull${UMUI_UNIQUEIDSN} notnull${UMUI_UNIQUEIDSN}
      ;then
        !insertmacro INSTALLOPTIONS_WRITE "$MUI_TEMP1" "Field $UMUI_TEMP3" State "$5"
        Goto done2${UMUI_UNIQUEIDSN}
      ;else
      notnull${UMUI_UNIQUEIDSN}:
        StrCpy $6 $5 $2 ; Get $2 next source char
        !insertmacro INSTALLOPTIONS_WRITE "$MUI_TEMP1" "Field $UMUI_TEMP3" State "$6"

        StrCpy $5 $5 "" $2 ; Remove it from the source

        ;if $5 next char is "-" remove
        StrCpy $6 $5 1 ; Get the next source char
        StrCmp $6 "-" 0 +2
          StrCpy $5 $5 "" 1 ; Remove it from the source
        ;endif
      ;endif
      done2${UMUI_UNIQUEIDSN}:

      ;if $2 != 0
      IntCmp $2 0 null${UMUI_UNIQUEIDSN} 0 0
      ;then

        !insertmacro INSTALLOPTIONS_WRITE "$MUI_TEMP1" "Field $UMUI_TEMP3" MaxLen "$2"

        ;if $R0 == 0
        IntCmp $R0 0 0 endCanBeEmpty${UMUI_UNIQUEIDSN} endCanBeEmpty${UMUI_UNIQUEIDSN}
        ;then
          !insertmacro INSTALLOPTIONS_WRITE "$MUI_TEMP1" "Field $UMUI_TEMP3" MinLen "$2"
        ;end
        endCanBeEmpty${UMUI_UNIQUEIDSN}:

        StrCpy $UMUI_SNTEXT "${TEXT}"
        !insertmacro INSTALLOPTIONS_WRITE "$MUI_TEMP1" "Field $UMUI_TEMP3" ValidateText "${UMUI_SERIALNUMBERPAGE_INVALIDATE_TEXT}"
        Goto endnull${UMUI_UNIQUEIDSN}

      ;else
      null${UMUI_UNIQUEIDSN}:

        ;if $R0 == 0
        IntCmp $R0 0 0 endCanBeEmpty2${UMUI_UNIQUEIDSN} endCanBeEmpty2${UMUI_UNIQUEIDSN}
        ;then
          !insertmacro INSTALLOPTIONS_WRITE "$MUI_TEMP1" "Field $UMUI_TEMP3" MinLen "1"
          StrCpy $UMUI_SNTEXT "${TEXT}"
          !insertmacro INSTALLOPTIONS_WRITE "$MUI_TEMP1" "Field $UMUI_TEMP3" ValidateText "${UMUI_SERIALNUMBERPAGE_INVALIDATE_TEXT}"
        ;end
        endCanBeEmpty2${UMUI_UNIQUEIDSN}:

      ;endif
      endnull${UMUI_UNIQUEIDSN}:

      ;if $8 != 0
      IntCmp $8 0 flagNoNumbers${UMUI_UNIQUEIDSN} 0 0
      ;then
        !insertmacro INSTALLOPTIONS_WRITE "$MUI_TEMP1" "Field $UMUI_TEMP3" Flags "ONLY_NUMBERS"
      ;endif
      flagNoNumbers${UMUI_UNIQUEIDSN}:

      ;if $7 != 0
      IntCmp $7 0 isfirst${UMUI_UNIQUEIDSN}
      ;then
        IntOp $1 $UMUI_TEMP3 - 2
        !insertmacro INSTALLOPTIONS_WRITE "$MUI_TEMP1" "Field $UMUI_TEMP3" BackField "$1"
        Goto endfirst${UMUI_UNIQUEIDSN}
      ;else
      isfirst${UMUI_UNIQUEIDSN}:
        StrCpy $9 $UMUI_TEMP3
      ;endif
      endfirst${UMUI_UNIQUEIDSN}:

      IntOp $7 $7 + 1

      ;if $2 == 0 done1
      IntCmp $2 0 done1${UMUI_UNIQUEIDSN} 0 0

        ; draw "_"
        StrCpy $2 $0 1 ; Get the next source char
        StrCmp $2 "" done1${UMUI_UNIQUEIDSN} ; Abort when none left

          IntOp $1 $UMUI_TEMP3 + 2
          !insertmacro INSTALLOPTIONS_WRITE "$MUI_TEMP1" "Field $UMUI_TEMP3" NextField "$1"

          IntOp $UMUI_TEMP3 $UMUI_TEMP3 + 1
          !insertmacro INSTALLOPTIONS_WRITE "$MUI_TEMP1" "Field $UMUI_TEMP3" Type "label"
          !insertmacro INSTALLOPTIONS_WRITE "$MUI_TEMP1" "Field $UMUI_TEMP3" Text "_"
          IntOp $UMUI_TEMP4 $UMUI_TEMP4 - 1
          !insertmacro INSTALLOPTIONS_WRITE "$MUI_TEMP1" "Field $UMUI_TEMP3" Top "$UMUI_TEMP4"
          IntOp $UMUI_TEMP4 $UMUI_TEMP4 + 10
          !insertmacro INSTALLOPTIONS_WRITE "$MUI_TEMP1" "Field $UMUI_TEMP3" Bottom "$UMUI_TEMP4"
          IntOp $UMUI_TEMP4 $UMUI_TEMP4 - 9
          IntOp $3 $3 + 3
          !insertmacro INSTALLOPTIONS_WRITE "$MUI_TEMP1" "Field $UMUI_TEMP3" Left "$3"
          IntOp $3 $3 + 7
          !insertmacro INSTALLOPTIONS_WRITE "$MUI_TEMP1" "Field $UMUI_TEMP3" Right "$3"

          Goto loop1${UMUI_UNIQUEIDSN}

  done1${UMUI_UNIQUEIDSN}:
  ;endforeach

  !insertmacro INSTALLOPTIONS_WRITE "$MUI_TEMP1" "Settings" NumFields "$UMUI_TEMP3"

  IntOp $UMUI_TEMP4 $UMUI_TEMP4 + 15

  ;save to list serial ini
  !insertmacro INSTALLOPTIONS_READ $MUI_TEMP2 "$MUI_TEMP1" "Settings" NumTasks

  IntOp $MUI_TEMP2 $MUI_TEMP2 + 1
  !insertmacro INSTALLOPTIONS_WRITE "$MUI_TEMP1" "Settings" NumTasks "$MUI_TEMP2"

  !insertmacro INSTALLOPTIONS_WRITE "$MUI_TEMP1" "$MUI_TEMP2" SerialID "${ID}"
  !insertmacro INSTALLOPTIONS_WRITE "$MUI_TEMP1" "$MUI_TEMP2" FirstField "$9"
  !insertmacro INSTALLOPTIONS_WRITE "$MUI_TEMP1" "$MUI_TEMP2" FLAGS "${FLAGS}"

  !ifdef UMUI_SERIALNUMBERPAGE_SERIAL_REGISTRY_VALUENAME
    !insertmacro INSTALLOPTIONS_WRITE "SerialNumberList.ini" "Serial ${ID}" REGISTRY_ROOT "${UMUI_SERIALNUMBERPAGE_SERIAL_REGISTRY_ROOT}"
    !insertmacro INSTALLOPTIONS_WRITE "SerialNumberList.ini" "Serial ${ID}" REGISTRY_KEY "${UMUI_SERIALNUMBERPAGE_SERIAL_REGISTRY_KEY}"
    !insertmacro INSTALLOPTIONS_WRITE "SerialNumberList.ini" "Serial ${ID}" REGISTRY_VALUENAME "${UMUI_SERIALNUMBERPAGE_SERIAL_REGISTRY_VALUENAME}"
  !endif

  ClearErrors

  !insertmacro MUI_UNSET UMUI_SERIALNUMBERPAGE_SERIAL_REGISTRY_VALUENAME

  !undef UMUI_UNIQUEIDSN

  Pop $R0
  Pop $9
  Pop $8
  Pop $7
  Pop $6
  Pop $5
  Pop $4
  Pop $3
  Pop $2
  Pop $1
  Pop $0

!macroend



!macro UMUI_SERIALNUMBERPAGE_ADD_SERIAL ID STR FLAGS DEFAULT

  !verbose push
  !verbose ${MUI_VERBOSE}

  !insertmacro UMUI_SERIALNUMBERPAGE_CREATE "${ID}" "${STR}" "${FLAGS}" "${DEFAULT}" "${ID}" "5"

  !verbose pop

!macroend


!macro UMUI_SERIALNUMBERPAGE_ADD_LABELEDSERIAL ID STR FLAGS DEFAULT TEXT

  !verbose push
  !verbose ${MUI_VERBOSE}

  ;label
  IntOp $UMUI_TEMP3 $UMUI_TEMP3 + 1

  !insertmacro INSTALLOPTIONS_WRITE "$MUI_TEMP1" "Field $UMUI_TEMP3" Type "Label"
  !insertmacro INSTALLOPTIONS_WRITE "$MUI_TEMP1" "Field $UMUI_TEMP3" Text "${TEXT}:"
  !insertmacro INSTALLOPTIONS_WRITE "$MUI_TEMP1" "Field $UMUI_TEMP3" Left "5"
  !insertmacro INSTALLOPTIONS_WRITE "$MUI_TEMP1" "Field $UMUI_TEMP3" Right "78"

  IntOp $UMUI_TEMP4 $UMUI_TEMP4 + 2
  !insertmacro INSTALLOPTIONS_WRITE "$MUI_TEMP1" "Field $UMUI_TEMP3" Top "$UMUI_TEMP4"
  IntOp $UMUI_TEMP4 $UMUI_TEMP4 + 10
  !insertmacro INSTALLOPTIONS_WRITE "$MUI_TEMP1" "Field $UMUI_TEMP3" Bottom "$UMUI_TEMP4"
  IntOp $UMUI_TEMP4 $UMUI_TEMP4 - 12

  ;inputs
  !insertmacro UMUI_SERIALNUMBERPAGE_CREATE "${ID}" "${STR}" "${FLAGS}" "${DEFAULT}" "${TEXT}" "79"

  !verbose pop

!macroend


!macro UMUI_SERIALNUMBER_GET ID VAR

  !insertmacro INSTALLOPTIONS_READ $${VAR} "SerialNumberList.ini" "Serial ${ID}" SN
  ClearErrors

!macroend







!macro UMUI_PAGE_ALTERNATIVESTARTMENU ID VAR

  !verbose push
  !verbose ${MUI_VERBOSE}

  !insertmacro MUI_PAGE_INIT

  !define /IfNDef MUI_${MUI_PAGE_UNINSTALLER_PREFIX}STARTMENUPAGE
  !define /IfNDef UMUI_${MUI_PAGE_UNINSTALLER_PREFIX}ALTERNATIVESTARTMENUPAGE

  !define /IfNDef MUI_STARTMENUPAGE_DEFAULTFOLDER "$(^Name)"
  !insertmacro MUI_DEFAULT_IOCONVERT MUI_STARTMENUPAGE_TEXT_TOP "$(MUI_${MUI_PAGE_UNINSTALLER_PREFIX}INNERTEXT_STARTMENU_TOP)"
  !insertmacro MUI_DEFAULT_IOCONVERT MUI_STARTMENUPAGE_TEXT_CHECKBOX "$(MUI_${MUI_PAGE_UNINSTALLER_PREFIX}INNERTEXT_STARTMENU_CHECKBOX)"

  !insertmacro MUI_DEFAULT_IOCONVERT UMUI_STARTMENUPAGE_SHELL_VAR_CONTEXT_TITLE "$(UMUI_TEXT_SHELL_VAR_CONTEXT)"
  !insertmacro MUI_DEFAULT_IOCONVERT UMUI_STARTMENUPAGE_TEXT_FOR_ALL_USERS "$(UMUI_TEXT_SHELL_VAR_CONTEXT_FOR_ALL_USERS)"
  !insertmacro MUI_DEFAULT_IOCONVERT UMUI_STARTMENUPAGE_TEXT_FOR_THE_CURRENT_USER "$(UMUI_TEXT_SHELL_VAR_CONTEXT_ONLY_FOR_CURRENT_USER)"

  !define MUI_STARTMENUPAGE_VARIABLE "${VAR}"
  !define "MUI_STARTMENUPAGE_${ID}_VARIABLE" "${MUI_STARTMENUPAGE_VARIABLE}"
  !define "MUI_STARTMENUPAGE_${ID}_DEFAULTFOLDER" "${MUI_STARTMENUPAGE_DEFAULTFOLDER}"
  !ifdef MUI_STARTMENUPAGE_REGISTRY_VALUENAME
    !define "MUI_STARTMENUPAGE_${ID}_REGISTRY_VALUENAME" "${MUI_STARTMENUPAGE_REGISTRY_VALUENAME}"

    !ifndef MUI_STARTMENUPAGE_REGISTRY_ROOT
      !ifdef UMUI_PARAMS_REGISTRY_ROOT
        !define MUI_STARTMENUPAGE_REGISTRY_ROOT "${UMUI_PARAMS_REGISTRY_ROOT}"
      !else
        !error "For MUI_STARTMENUPAGE_REGISTRY_VALUENAME, the MUI_STARTMENUPAGE_REGISTRY_ROOT & MUI_STARTMENUPAGE_REGISTRY_KEY parameters or else the UMUI_PARAMS_REGISTRY_ROOT & UMUI_PARAMS_REGISTRY_KEY global parameters must be defined."
      !endif
    !endif
    !ifndef MUI_STARTMENUPAGE_REGISTRY_KEY
      !ifdef UMUI_PARAMS_REGISTRY_KEY
        !define MUI_STARTMENUPAGE_REGISTRY_KEY "${UMUI_PARAMS_REGISTRY_KEY}"
      !else
        !error "For MUI_STARTMENUPAGE_REGISTRY_VALUENAME, the MUI_STARTMENUPAGE_REGISTRY_ROOT & MUI_STARTMENUPAGE_REGISTRY_KEY parameters or else the UMUI_PARAMS_REGISTRY_ROOT & UMUI_PARAMS_REGISTRY_KEY global parameters must be defined."
      !endif
    !endif

    !define "MUI_STARTMENUPAGE_${ID}_REGISTRY_ROOT" "${MUI_STARTMENUPAGE_REGISTRY_ROOT}"
    !define "MUI_STARTMENUPAGE_${ID}_REGISTRY_KEY" "${MUI_STARTMENUPAGE_REGISTRY_KEY}"

  !endif

  !ifdef UMUI_ALTERNATIVESTARTMENUPAGE_USE_TREEVIEW
    !ifndef UMUI_USE_INSTALLOPTIONSEX
      !error "You want to use a TreeView in the ALTERNATIVESTARTMENU page but you don't use InstallOptionEx. This page won't work without the UMUI_USE_INSTALLOPTIONSEX define."
    !endif
  !endif

  !ifndef MUI_VAR_HWND
    Var MUI_HWND
    !define MUI_VAR_HWND
  !endif

  !ifndef UMUI_VAR_UMUI_TEMP3
    Var UMUI_TEMP3
    !define UMUI_VAR_UMUI_TEMP3
  !endif

  !ifndef UMUI_VAR_UMUI_TEMP4
    Var UMUI_TEMP4
    !define UMUI_VAR_UMUI_TEMP4
  !endif

  !ifdef UMUI_ALTERNATIVESTARTMENUPAGE_SETSHELLVARCONTEXT
    !ifndef UMUI_VAR_UMUI_TEMP5
      Var UMUI_TEMP5
      !define UMUI_VAR_UMUI_TEMP5
    !endif
  !endif

  PageEx ${MUI_PAGE_UNINSTALLER_FUNCPREFIX}custom

    PageCallbacks ${MUI_PAGE_UNINSTALLER_FUNCPREFIX}mui.AlternativeStartmenuPre_${MUI_UNIQUEID} ${MUI_PAGE_UNINSTALLER_FUNCPREFIX}mui.AlternativeStartmenuLeave_${MUI_UNIQUEID}

    Caption " "

  PageExEnd

  !insertmacro UMUI_FUNCTION_ALTERNATIVESTARTMENUPAGE ${MUI_PAGE_UNINSTALLER_FUNCPREFIX}mui.AlternativeStartmenuPre_${MUI_UNIQUEID} ${MUI_PAGE_UNINSTALLER_FUNCPREFIX}mui.AlternativeStartmenuLeave_${MUI_UNIQUEID} ${MUI_PAGE_UNINSTALLER_FUNCPREFIX}mui.AlternativeStartmenuCreateList_${MUI_UNIQUEID}

  !undef MUI_STARTMENUPAGE_VARIABLE
  !undef MUI_STARTMENUPAGE_TEXT_TOP
  !undef MUI_STARTMENUPAGE_TEXT_CHECKBOX
  !undef MUI_STARTMENUPAGE_DEFAULTFOLDER

  !undef UMUI_STARTMENUPAGE_SHELL_VAR_CONTEXT_TITLE
  !undef UMUI_STARTMENUPAGE_TEXT_FOR_ALL_USERS
  !undef UMUI_STARTMENUPAGE_TEXT_FOR_THE_CURRENT_USER

  !insertmacro MUI_UNSET MUI_STARTMENUPAGE_NODISABLE
  !insertmacro MUI_UNSET MUI_STARTMENUPAGE_REGISTRY_ROOT
  !insertmacro MUI_UNSET MUI_STARTMENUPAGE_REGISTRY_KEY
  !insertmacro MUI_UNSET MUI_STARTMENUPAGE_REGISTRY_VALUENAME

  !insertmacro MUI_UNSET UMUI_ALTERNATIVESTARTMENUPAGE_SETSHELLVARCONTEXT
  !insertmacro MUI_UNSET UMUI_ALTERNATIVESTARTMENUPAGE_USE_TREEVIEW

  !verbose pop

!macroend


!macro UMUI_FUNCTION_ALTERNATIVESTARTMENUPAGE PRE LEAVE CREATELIST

  !ifdef MUI_STARTMENUPAGE_NODISABLE
    !define UMUI_INTERNAL_ASMGOUPBOXFIELD 4
    !define UMUI_INTERNAL_ASMALLOPTFIELD 5
    !define UMUI_INTERNAL_ASMCURRENTOPTFIELD 6
  !else
    !define UMUI_INTERNAL_ASMGOUPBOXFIELD 5
    !define UMUI_INTERNAL_ASMALLOPTFIELD 6
    !define UMUI_INTERNAL_ASMCURRENTOPTFIELD 7
  !endif

  Function "${PRE}"

    StrCpy $UMUI_TEMP4 ""

    !ifdef MUI_STARTMENUPAGE_REGISTRY_VALUENAME

      Push $R0
      Push $R1
      Push $R2

      ClearErrors

      StrCmp "${MUI_STARTMENUPAGE_VARIABLE}" "" 0 endreg

        ReadRegStr $MUI_TEMP1 ${MUI_STARTMENUPAGE_REGISTRY_ROOT} "${MUI_STARTMENUPAGE_REGISTRY_KEY}" "${MUI_STARTMENUPAGE_REGISTRY_VALUENAME}"

        StrCmp $MUI_TEMP1 "" endreg
          StrCpy "${MUI_STARTMENUPAGE_VARIABLE}" $MUI_TEMP1
          StrLen $R0 $MUI_TEMP1
          StrLen $R1 "${MUI_STARTMENUPAGE_DEFAULTFOLDER}"

          IntCmp $R0 $R1 endreg endreg 0
            ;delete de default folder from the path if it is in.
            IntOp $R0 $R0 - $R1
            IntOp $R0 $R0 - 1

            StrCpy $UMUI_TEMP4 $MUI_TEMP1 $R0

            ;Convert this Folder path into a IOEx string
            !ifdef UMUI_ALTERNATIVESTARTMENUPAGE_USE_TREEVIEW
              !insertmacro UMUI_STRREPLACE $UMUI_TEMP4 "\" "{" $UMUI_TEMP4
              !insertmacro UMUI_STRCOUNT "{" $UMUI_TEMP4
              Pop $R0

              loopadd:
                StrCmp $R0 "0" endreg
                  StrCpy $UMUI_TEMP4 "$UMUI_TEMP4}"

                IntOp $R0 $R0 - 1
              Goto loopadd
            !endif

      endreg:

      Pop $R2
      Pop $R1
      Pop $R0

    !endif

    StrCmp "${MUI_STARTMENUPAGE_VARIABLE}" "" 0 +2
      StrCpy "${MUI_STARTMENUPAGE_VARIABLE}" "${MUI_STARTMENUPAGE_DEFAULTFOLDER}"

    !ifdef MUI_STARTMENUPAGE_REGISTRY_VALUENAME ; IF page skipped save
      !insertmacro UMUI_ADDPARAMTOSAVETOREGISTRYKEY ${MUI_STARTMENUPAGE_REGISTRY_ROOT} "${MUI_STARTMENUPAGE_REGISTRY_KEY}" "${MUI_STARTMENUPAGE_REGISTRY_VALUENAME}" "${MUI_STARTMENUPAGE_VARIABLE}"
    !endif

    ; IF setup cancelled or steuptype complete
    !insertmacro UMUI_ABORT_IF_INSTALLFLAG_IS ${UMUI_CANCELLED}|${UMUI_MINIMAL}|${UMUI_STANDARD}|${UMUI_COMPLETE}|${UMUI_MODIFY}|${UMUI_REPAIR}|${UMUI_UPDATE}

    !insertmacro MUI_PAGE_FUNCTION_CUSTOM PRE

    !insertmacro MUI_HEADER_TEXT_PAGE $(MUI_TEXT_STARTMENU_TITLE) $(MUI_TEXT_STARTMENU_SUBTITLE)

    ; disable sellvarcontext radio buttons if no admin rights
    !ifdef UMUI_ALTERNATIVESTARTMENUPAGE_SETSHELLVARCONTEXT
      UserInfo::GetAccountType
      Pop $UMUI_TEMP5
      StrCmp $UMUI_TEMP5 "Admin" endcheck
      StrCmp $UMUI_TEMP5 "User" endcheck
      StrCmp $UMUI_TEMP5 "Power" 0 +3
        StrCpy $UMUI_TEMP5 "Admin"
        Goto endcheck
      StrCmp $UMUI_TEMP5 "Guest" 0 +3
        StrCpy $UMUI_TEMP5 "User"
        Goto endcheck
      ;if error or win 95
      StrCpy $UMUI_TEMP5 "Admin"

      endcheck:
    !endif

    IfFileExists "$PLUGINSDIR\AlternativeStartMenu${ID}.ini" alreadyExists
      !insertmacro INSTALLOPTIONS_EXTRACT_AS "${UMUI_ALTERNATIVESTARTMENUPAGE_INI}" "AlternativeStartMenu${ID}.ini"

      ; serach all directory and add it in the listbox/treeview

      ;Save the current ShellVarContext
      !insertmacro UMUI_GETSHELLVARCONTEXT
      Pop $MUI_TEMP2

      ; In treeview mod, the create list function directly write into the ini because of the string lengh limit to 1024 characters
      !ifdef UMUI_ALTERNATIVESTARTMENUPAGE_USE_TREEVIEW

        FlushINI "$PLUGINSDIR\AlternativeStartMenu${ID}.ini"

        FileOpen $MUI_TEMP1 "$PLUGINSDIR\AlternativeStartMenu${ID}.ini" a

        ;search the last "ListItems=" in the ini and seek just after
        Push $R0

        StrCpy $UMUI_TEMP3 0
        seekloop:
          IntOp $UMUI_TEMP3 $UMUI_TEMP3 - 1
          FileSeek $MUI_TEMP1 $UMUI_TEMP3 END
          !ifdef NSIS_UNICODE
            FileReadUTF16LE $MUI_TEMP1 $R0 10
          !else
            FileRead $MUI_TEMP1 $R0 10
          !endif
          StrCmp $R0 "ListItems=" 0 seekloop
            !ifdef NSIS_UNICODE
              IntOp $UMUI_TEMP3 $UMUI_TEMP3 + 20
            !else
              IntOp $UMUI_TEMP3 $UMUI_TEMP3 + 10
            !endif
            FileSeek $MUI_TEMP1 $UMUI_TEMP3 END

        Pop $R0

        Push 0
        Push ""

        Call ${CREATELIST}

        FileClose $MUI_TEMP1

      !else

        Call ${CREATELIST}

        Pop $MUI_TEMP1

      !endif

      ;Save the saved ShellVarContext
      StrCmp $MUI_TEMP2 "current" 0 +3
        SetShellVarContext current
      Goto +2
        SetShellVarContext all

      ClearErrors


      ;end search all directory and add it in the listbox/treeview
      !insertmacro MUI_INSTALLOPTIONS_WRITE_DEFAULTCONVERT "AlternativeStartMenu${ID}.ini" "Field 1" "Text" "MUI_STARTMENUPAGE_TEXT_TOP"

      ;if in the old install the startmenu folder was disabled
      StrCmp "${MUI_STARTMENUPAGE_VARIABLE}" ">" 0 +5
        !insertmacro INSTALLOPTIONS_WRITE "AlternativeStartMenu${ID}.ini" "Field 2" State "${MUI_STARTMENUPAGE_DEFAULTFOLDER}"
        !insertmacro INSTALLOPTIONS_WRITE "AlternativeStartMenu${ID}.ini" "Field 2" Flags "DISABLED"
        !insertmacro INSTALLOPTIONS_WRITE "AlternativeStartMenu${ID}.ini" "Field 3" Flags "NOTIFY|DISABLED"
        Goto +3
        !insertmacro INSTALLOPTIONS_WRITE "AlternativeStartMenu${ID}.ini" "Field 2" State "${MUI_STARTMENUPAGE_VARIABLE}"
        !insertmacro INSTALLOPTIONS_WRITE "AlternativeStartMenu${ID}.ini" "Field 3" State "$UMUI_TEMP4"

      !ifdef UMUI_ALTERNATIVESTARTMENUPAGE_USE_TREEVIEW
        !insertmacro INSTALLOPTIONS_WRITE "AlternativeStartMenu${ID}.ini" "Field 3" Type "TreeView"
      !endif

      ; we write only if it was not already doing by the createlist function (in case of the list lenght is > to 1024 character)
      !ifndef UMUI_ALTERNATIVESTARTMENUPAGE_USE_TREEVIEW
        !insertmacro INSTALLOPTIONS_WRITE "AlternativeStartMenu${ID}.ini" "Field 3" ListItems "$MUI_TEMP1"
      !endif

      !ifndef MUI_STARTMENUPAGE_NODISABLE
        !insertmacro INSTALLOPTIONS_WRITE "AlternativeStartMenu${ID}.ini" "Field 3" Bottom -12

        !insertmacro INSTALLOPTIONS_WRITE "AlternativeStartMenu${ID}.ini" "Field 4" Type "CheckBox"
        !insertmacro MUI_INSTALLOPTIONS_WRITE_DEFAULTCONVERT  "AlternativeStartMenu${ID}.ini" "Field 4" "Text" "MUI_STARTMENUPAGE_TEXT_CHECKBOX"
        !insertmacro INSTALLOPTIONS_WRITE "AlternativeStartMenu${ID}.ini" "Field 4" Left 0
        !insertmacro INSTALLOPTIONS_WRITE "AlternativeStartMenu${ID}.ini" "Field 4" Right -1
        !insertmacro INSTALLOPTIONS_WRITE "AlternativeStartMenu${ID}.ini" "Field 4" Top -12
        !insertmacro INSTALLOPTIONS_WRITE "AlternativeStartMenu${ID}.ini" "Field 4" Bottom -1

        !insertmacro INSTALLOPTIONS_WRITE "AlternativeStartMenu${ID}.ini" "Field 4" State 0

        StrCmp "${MUI_STARTMENUPAGE_VARIABLE}" ">" 0 +2
          !insertmacro INSTALLOPTIONS_WRITE "AlternativeStartMenu${ID}.ini" "Field 4" State 1

        !insertmacro INSTALLOPTIONS_WRITE "AlternativeStartMenu${ID}.ini" "Field 4" Flags NOTIFY
        !insertmacro INSTALLOPTIONS_WRITE "AlternativeStartMenu${ID}.ini" "Field 4" Notify ONCLICK

        !insertmacro INSTALLOPTIONS_WRITE "AlternativeStartMenu${ID}.ini" "Settings" NumFields 4
      !endif

      !ifdef UMUI_ALTERNATIVESTARTMENUPAGE_SETSHELLVARCONTEXT

        !ifdef MUI_STARTMENUPAGE_NODISABLE
          !insertmacro INSTALLOPTIONS_WRITE "AlternativeStartMenu${ID}.ini" "Field 3" "Bottom" "-40"
        !else
          !insertmacro INSTALLOPTIONS_WRITE "AlternativeStartMenu${ID}.ini" "Field 4" "Top" "-52"
          !insertmacro INSTALLOPTIONS_WRITE "AlternativeStartMenu${ID}.ini" "Field 4" "Bottom" "-40"
          !insertmacro INSTALLOPTIONS_WRITE "AlternativeStartMenu${ID}.ini" "Field 3" "Bottom" "-53"
        !endif

        !insertmacro INSTALLOPTIONS_WRITE "AlternativeStartMenu${ID}.ini" "Field ${UMUI_INTERNAL_ASMGOUPBOXFIELD}" "Type" "GroupBox"
        !insertmacro MUI_INSTALLOPTIONS_WRITE_DEFAULTCONVERT "AlternativeStartMenu${ID}.ini" "Field ${UMUI_INTERNAL_ASMGOUPBOXFIELD}" "Text" "UMUI_STARTMENUPAGE_SHELL_VAR_CONTEXT_TITLE"
        !insertmacro INSTALLOPTIONS_WRITE "AlternativeStartMenu${ID}.ini" "Field ${UMUI_INTERNAL_ASMGOUPBOXFIELD}" "Left" "70"
        !insertmacro INSTALLOPTIONS_WRITE "AlternativeStartMenu${ID}.ini" "Field ${UMUI_INTERNAL_ASMGOUPBOXFIELD}" "Right" "-70"
        !insertmacro INSTALLOPTIONS_WRITE "AlternativeStartMenu${ID}.ini" "Field ${UMUI_INTERNAL_ASMGOUPBOXFIELD}" "Top" "-40"
        !insertmacro INSTALLOPTIONS_WRITE "AlternativeStartMenu${ID}.ini" "Field ${UMUI_INTERNAL_ASMGOUPBOXFIELD}" "Bottom" "-1"

        !insertmacro INSTALLOPTIONS_WRITE "AlternativeStartMenu${ID}.ini" "Field ${UMUI_INTERNAL_ASMALLOPTFIELD}" "Type" "RadioButton"
        !insertmacro MUI_INSTALLOPTIONS_WRITE_DEFAULTCONVERT "AlternativeStartMenu${ID}.ini" "Field ${UMUI_INTERNAL_ASMALLOPTFIELD}" "Text" "UMUI_STARTMENUPAGE_TEXT_FOR_ALL_USERS"
        !insertmacro INSTALLOPTIONS_WRITE "AlternativeStartMenu${ID}.ini" "Field ${UMUI_INTERNAL_ASMALLOPTFIELD}" "Left" "80"
        !insertmacro INSTALLOPTIONS_WRITE "AlternativeStartMenu${ID}.ini" "Field ${UMUI_INTERNAL_ASMALLOPTFIELD}" "Right" "-80"
        !insertmacro INSTALLOPTIONS_WRITE "AlternativeStartMenu${ID}.ini" "Field ${UMUI_INTERNAL_ASMALLOPTFIELD}" "Top" "-29"
        !insertmacro INSTALLOPTIONS_WRITE "AlternativeStartMenu${ID}.ini" "Field ${UMUI_INTERNAL_ASMALLOPTFIELD}" "Bottom" "-19"
        !insertmacro INSTALLOPTIONS_WRITE "AlternativeStartMenu${ID}.ini" "Field ${UMUI_INTERNAL_ASMALLOPTFIELD}" "Flag" "GROUP"

        !insertmacro INSTALLOPTIONS_WRITE "AlternativeStartMenu${ID}.ini" "Field ${UMUI_INTERNAL_ASMCURRENTOPTFIELD}" "Type" "RadioButton"
        !insertmacro MUI_INSTALLOPTIONS_WRITE_DEFAULTCONVERT "AlternativeStartMenu${ID}.ini" "Field ${UMUI_INTERNAL_ASMCURRENTOPTFIELD}" "Text" "UMUI_STARTMENUPAGE_TEXT_FOR_THE_CURRENT_USER"
        !insertmacro INSTALLOPTIONS_WRITE "AlternativeStartMenu${ID}.ini" "Field ${UMUI_INTERNAL_ASMCURRENTOPTFIELD}" "Left" "80"
        !insertmacro INSTALLOPTIONS_WRITE "AlternativeStartMenu${ID}.ini" "Field ${UMUI_INTERNAL_ASMCURRENTOPTFIELD}" "Right" "-80"
        !insertmacro INSTALLOPTIONS_WRITE "AlternativeStartMenu${ID}.ini" "Field ${UMUI_INTERNAL_ASMCURRENTOPTFIELD}" "Top" "-17"
        !insertmacro INSTALLOPTIONS_WRITE "AlternativeStartMenu${ID}.ini" "Field ${UMUI_INTERNAL_ASMCURRENTOPTFIELD}" "Bottom" "-7"

        StrCmp $UMUI_TEMP5 "User" 0 admin
          !insertmacro INSTALLOPTIONS_WRITE "AlternativeStartMenu${ID}.ini" "Field ${UMUI_INTERNAL_ASMALLOPTFIELD}" Flags "DISABLED"
          !insertmacro INSTALLOPTIONS_WRITE "AlternativeStartMenu${ID}.ini" "Field ${UMUI_INTERNAL_ASMCURRENTOPTFIELD}" Flags "DISABLED"

          !insertmacro INSTALLOPTIONS_WRITE "AlternativeStartMenu${ID}.ini" "Field ${UMUI_INTERNAL_ASMCURRENTOPTFIELD}" "State" "1"
          !insertmacro INSTALLOPTIONS_WRITE "AlternativeStartMenu${ID}.ini" "Field ${UMUI_INTERNAL_ASMALLOPTFIELD}" "State" "0"
          Goto endcontext
        admin:
          StrCmp $MUI_TEMP2 "current" 0 +4
            !insertmacro INSTALLOPTIONS_WRITE "AlternativeStartMenu${ID}.ini" "Field ${UMUI_INTERNAL_ASMCURRENTOPTFIELD}" "State" "1"
            !insertmacro INSTALLOPTIONS_WRITE "AlternativeStartMenu${ID}.ini" "Field ${UMUI_INTERNAL_ASMALLOPTFIELD}" "State" "0"
          Goto +3
            !insertmacro INSTALLOPTIONS_WRITE "AlternativeStartMenu${ID}.ini" "Field ${UMUI_INTERNAL_ASMALLOPTFIELD}" "State" "1"
            !insertmacro INSTALLOPTIONS_WRITE "AlternativeStartMenu${ID}.ini" "Field ${UMUI_INTERNAL_ASMCURRENTOPTFIELD}" "State" "0"
        endcontext:

          !insertmacro INSTALLOPTIONS_WRITE "AlternativeStartMenu${ID}.ini" "Settings" NumFields "${UMUI_INTERNAL_ASMCURRENTOPTFIELD}"
      !endif

    alreadyExists:

    StrCpy $UMUI_TEMP3 ">"

    !ifndef MUI_STARTMENUPAGE_NODISABLE

      !insertmacro INSTALLOPTIONS_READ $MUI_TEMP1 "AlternativeStartMenu${ID}.ini" "Field 4" State

      StrCmp $MUI_TEMP1 "1" 0 nodisable
        !insertmacro INSTALLOPTIONS_WRITE "AlternativeStartMenu${ID}.ini" "Field 2" Flags "DISABLED"
        !insertmacro INSTALLOPTIONS_WRITE "AlternativeStartMenu${ID}.ini" "Field 3" Flags "NOTIFY|DISABLED"
        !ifdef UMUI_ALTERNATIVESTARTMENUPAGE_SETSHELLVARCONTEXT
          !insertmacro INSTALLOPTIONS_WRITE "AlternativeStartMenu${ID}.ini" "Field ${UMUI_INTERNAL_ASMALLOPTFIELD}" Flags "DISABLED"
          !insertmacro INSTALLOPTIONS_WRITE "AlternativeStartMenu${ID}.ini" "Field ${UMUI_INTERNAL_ASMCURRENTOPTFIELD}" Flags "DISABLED"
        !endif
        Goto endnodisable
      nodisable:
        !insertmacro INSTALLOPTIONS_READ $MUI_TEMP2 "AlternativeStartMenu${ID}.ini" "Field 2" "State"
        StrCmp $MUI_TEMP2 "" 0 +3
          GetDlgItem $MUI_HWND $HWNDPARENT 1 ;next
          EnableWindow $MUI_HWND 0

      endnodisable:

    !else
      !insertmacro INSTALLOPTIONS_WRITE "AlternativeStartMenu${ID}.ini" "Settings" NumFields "3"

      !insertmacro INSTALLOPTIONS_READ $MUI_TEMP2 "AlternativeStartMenu${ID}.ini" "Field 2" "State"
      StrCmp $MUI_TEMP2 "" 0 +3
        GetDlgItem $MUI_HWND $HWNDPARENT 1 ;next
        EnableWindow $MUI_HWND 0

    !endif

    StrCmp $MUI_TEMP1 "0" 0 noenable
      !insertmacro INSTALLOPTIONS_WRITE "AlternativeStartMenu${ID}.ini" "Field 2" Flags ""
      !insertmacro INSTALLOPTIONS_WRITE "AlternativeStartMenu${ID}.ini" "Field 3" Flags "NOTIFY"
      !ifdef UMUI_ALTERNATIVESTARTMENUPAGE_SETSHELLVARCONTEXT
        StrCmp $UMUI_TEMP5 "Admin" 0 noenable
          !insertmacro INSTALLOPTIONS_WRITE "AlternativeStartMenu${ID}.ini" "Field ${UMUI_INTERNAL_ASMALLOPTFIELD}" Flags ""
          !insertmacro INSTALLOPTIONS_WRITE "AlternativeStartMenu${ID}.ini" "Field ${UMUI_INTERNAL_ASMCURRENTOPTFIELD}" Flags ""
      !endif
    noenable:

    !insertmacro MUI_PAGE_FUNCTION_CUSTOM SHOW

    !insertmacro INSTALLOPTIONS_DISPLAY_RETURN "AlternativeStartMenu${ID}.ini"

    !insertmacro UMUI_FIX_BUTTONS_SKIN

  FunctionEnd

  Function "${LEAVE}"

    ;only the first time, get the HWND
    StrCmp $UMUI_TEMP3 ">" 0 +2
      Pop $UMUI_TEMP3

    GetDlgItem $MUI_HWND $HWNDPARENT 1 ;next
    EnableWindow $MUI_HWND 1

    !insertmacro INSTALLOPTIONS_READ $MUI_TEMP1 "AlternativeStartMenu${ID}.ini" "Settings" State

    ; if not next, back or cancel
    StrCmp $MUI_TEMP1 "0" ok 0

      ; if inputtext
      StrCmp $MUI_TEMP1 "2" 0 noinputtext

        !insertmacro INSTALLOPTIONS_READ $MUI_TEMP2 "AlternativeStartMenu${ID}.ini" "Field 2" "State"
        StrCmp $MUI_TEMP2 "" 0 +2
          EnableWindow $MUI_HWND 0

        ClearErrors
        Abort

      noinputtext:
      ; if listbox or treeview
      StrCmp $MUI_TEMP1 "3" 0 checkbox

        !insertmacro INSTALLOPTIONS_READ $MUI_TEMP2 "AlternativeStartMenu${ID}.ini" "Field 3" "State"

        ;Conversion IOEx State string into Folder string
        !ifdef UMUI_ALTERNATIVESTARTMENUPAGE_USE_TREEVIEW
          !insertmacro UMUI_STRREPLACE $MUI_TEMP2 "{" "\" $MUI_TEMP2
          !insertmacro UMUI_STRREPLACE $MUI_TEMP2 "}" "" $MUI_TEMP2
        !endif

        GetDlgItem $MUI_HWND $UMUI_TEMP3 1201 ;"Field 2" "HWND"
        SendMessage $MUI_HWND ${WM_SETTEXT} 0 "STR:$MUI_TEMP2\${MUI_STARTMENUPAGE_DEFAULTFOLDER}"

        ClearErrors
        Abort

      checkbox:
        !ifndef MUI_STARTMENUPAGE_NODISABLE

          !insertmacro INSTALLOPTIONS_READ $MUI_TEMP2 "AlternativeStartMenu${ID}.ini" "Field 4" "State"
          StrCmp $MUI_TEMP2 "0" 0 +3
            StrCpy $MUI_TEMP2 1
          Goto +2
            StrCpy $MUI_TEMP2 0

          GetDlgItem $MUI_HWND $UMUI_TEMP3 1201 ;"Field 2" "HWND"
          EnableWindow $MUI_HWND $MUI_TEMP2
          GetDlgItem $MUI_HWND $UMUI_TEMP3 1202 ;"Field 3" "HWND"
          EnableWindow $MUI_HWND $MUI_TEMP2

          !ifdef UMUI_ALTERNATIVESTARTMENUPAGE_SETSHELLVARCONTEXT

            ; enable only if admin rights
            StrCmp $UMUI_TEMP5 "Admin" 0 +5

              GetDlgItem $MUI_HWND $UMUI_TEMP3 1205 ;"Field 6" "HWND"
              EnableWindow $MUI_HWND $MUI_TEMP2
              GetDlgItem $MUI_HWND $UMUI_TEMP3 1206 ;"Field 7" "HWND"
              EnableWindow $MUI_HWND $MUI_TEMP2

          !endif

          StrCmp $MUI_TEMP2 "1" 0 endcheckbox

            GetDlgItem $MUI_HWND $HWNDPARENT 1 ;next

            !insertmacro INSTALLOPTIONS_READ $MUI_TEMP2 "AlternativeStartMenu${ID}.ini" "Field 2" "State"
            StrCmp $MUI_TEMP2 "" 0 +2
              EnableWindow $MUI_HWND 0

          endcheckbox:

          Abort

        !endif

      Goto end
    ok:

    !ifdef UMUI_ALTERNATIVESTARTMENUPAGE_SETSHELLVARCONTEXT

      !ifdef UMUI_SHELLVARCONTEXT_REGISTRY_VALUENAME
        !ifndef UMUI_SHELLVARCONTEXT_REGISTRY_ROOT
          !ifdef UMUI_PARAMS_REGISTRY_ROOT
            !define UMUI_SHELLVARCONTEXT_REGISTRY_ROOT "${UMUI_PARAMS_REGISTRY_ROOT}"
          !else
            !error "For UMUI_SHELLVARCONTEXT_REGISTRY_VALUENAME, the UMUI_SHELLVARCONTEXT_REGISTRY_ROOT & UMUI_SHELLVARCONTEXT_REGISTRY_KEY parameters or else the UMUI_PARAMS_REGISTRY_ROOT & UMUI_PARAMS_REGISTRY_KEY global parameters must be defined."
          !endif
        !endif
        !ifndef UMUI_SHELLVARCONTEXT_REGISTRY_KEY
          !ifdef UMUI_PARAMS_REGISTRY_KEY
            !define UMUI_SHELLVARCONTEXT_REGISTRY_KEY "${UMUI_PARAMS_REGISTRY_KEY}"
          !else
            !error "For UMUI_SHELLVARCONTEXT_REGISTRY_VALUENAME, the UMUI_SHELLVARCONTEXT_REGISTRY_ROOT & UMUI_SHELLVARCONTEXT_REGISTRY_KEY parameters or else the UMUI_PARAMS_REGISTRY_ROOT & UMUI_PARAMS_REGISTRY_KEY global parameters must be defined."
          !endif
        !endif
      !endif

      !insertmacro INSTALLOPTIONS_READ $MUI_TEMP1 "AlternativeStartMenu${ID}.ini" "Field ${UMUI_INTERNAL_ASMALLOPTFIELD}" State
        StrCmp $MUI_TEMP1 "1" 0 current
          SetShellVarContext all
          !ifdef UMUI_SHELLVARCONTEXT_REGISTRY_VALUENAME
            !insertmacro UMUI_ADDPARAMTOSAVETOREGISTRYKEY ${UMUI_SHELLVARCONTEXT_REGISTRY_ROOT} "${UMUI_SHELLVARCONTEXT_REGISTRY_KEY}"  "${UMUI_SHELLVARCONTEXT_REGISTRY_VALUENAME}" "all"
          !endif
          Goto endcontext

        current:
        SetShellVarContext current
        !ifdef UMUI_SHELLVARCONTEXT_REGISTRY_VALUENAME
          !insertmacro UMUI_ADDPARAMTOSAVETOREGISTRYKEY ${UMUI_SHELLVARCONTEXT_REGISTRY_ROOT} "${UMUI_SHELLVARCONTEXT_REGISTRY_KEY}" "${UMUI_SHELLVARCONTEXT_REGISTRY_VALUENAME}" "current"
        !endif
      endcontext:

    !endif

    ClearErrors

    !ifndef MUI_STARTMENUPAGE_NODISABLE
      !insertmacro INSTALLOPTIONS_READ $MUI_TEMP1 "AlternativeStartMenu${ID}.ini" "Field 4" State
      StrCmp $MUI_TEMP1 "1" 0 +3
        StrCpy "${MUI_STARTMENUPAGE_VARIABLE}" ">"
        Goto +2
    !endif

    !insertmacro INSTALLOPTIONS_READ "${MUI_STARTMENUPAGE_VARIABLE}" "AlternativeStartMenu${ID}.ini" "Field 2" State

    !ifdef MUI_STARTMENUPAGE_REGISTRY_VALUENAME
      !insertmacro UMUI_ADDPARAMTOSAVETOREGISTRYKEY ${MUI_STARTMENUPAGE_REGISTRY_ROOT} "${MUI_STARTMENUPAGE_REGISTRY_KEY}" "${MUI_STARTMENUPAGE_REGISTRY_VALUENAME}" "${MUI_STARTMENUPAGE_VARIABLE}"
    !endif

    !insertmacro MUI_PAGE_FUNCTION_CUSTOM LEAVE

    end:

  FunctionEnd

  Function "${CREATELIST}"

    !ifdef UMUI_ALTERNATIVESTARTMENUPAGE_USE_TREEVIEW
      !insertmacro UMUI_INTERNAL_CREATE_SMTREELIST
    !else
      !insertmacro UMUI_INTERNAL_CREATE_SMLIST
    !endif

  FunctionEnd

  !undef UMUI_INTERNAL_ASMGOUPBOXFIELD
  !undef UMUI_INTERNAL_ASMALLOPTFIELD
  !undef UMUI_INTERNAL_ASMCURRENTOPTFIELD

!macroend


!macro UMUI_INTERNAL_CREATE_SMLIST_LOOP SHELLVARCONTEXT

  SetShellVarContext ${SHELLVARCONTEXT}

  FindFirst $R3 $R1 "$SMPROGRAMS\$R4\*"
  FindNext $R3 $R1

  loop${SHELLVARCONTEXT}:
    FindNext $R3 $R1

    StrCmp $R1 "" exit${SHELLVARCONTEXT}
      IfFileExists "$SMPROGRAMS\$R4\$R1\*" 0 loop${SHELLVARCONTEXT}
        nsArray::Set "SMProgList$R2" /key='$R1' '$R1'
        Goto loop${SHELLVARCONTEXT}

  exit${SHELLVARCONTEXT}:
    FindClose $R3

!macroend

; Generate the folder list for a listview
!macro UMUI_INTERNAL_CREATE_SMLIST

  Push $R4  ; directory to explore and the returned item list
  Push $R1  ; current folder to look
  Push $R3  ; the folder handle
  Push $R2  ; Array name level (empty in this macro)

  StrCpy $R4 ""
  StrCpy $R2 ""

  !insertmacro UMUI_INTERNAL_CREATE_SMLIST_LOOP all
  !insertmacro UMUI_INTERNAL_CREATE_SMLIST_LOOP current

  nsArray::Sort "SMProgList$R2" 4

  nsArray::Join "SMProgList$R2" "|"
  Pop $R4

  nsArray::Clear "SMProgList$R2"

  Pop $R2
  Pop $R3
  Pop $R1

  Exch $R4  ; return the item list

!macroend


; Generate the folder list for a treeview
!macro UMUI_INTERNAL_CREATE_SMTREELIST

  Exch $R4  ; directory to explore
  Exch      ; $R4 under $R2
  Exch $R2  ; Array name level number

  Push $R0  ; counter of the number of items added in this subdirectory
  Push $R1  ; current folder to look and treeview: pop the return of the recursive function
  Push $R3  ; the folder handle
  Push $R5  ; the number of the level
  Push $R6  ; the current item returned by the Read function

  !insertmacro UMUI_INTERNAL_CREATE_SMLIST_LOOP all
  !insertmacro UMUI_INTERNAL_CREATE_SMLIST_LOOP current

  nsArray::Sort "SMProgList$R2" 4

  IntOp $R5 $R2 + 1
  StrCpy $R1 0
  StrCpy $R0 0

  ;for each item of the $R2 level, begin with the end
  loop:
    ClearErrors
    nsArray::Get "SMProgList$R2" /at=$R0
    IfErrors end 0
      Pop $R6 ; key
      Pop $R6 ; value

      StrCmp $R2 "0" endfirstleveltest 0
        StrCmp $R0 "0" 0 +3
          !ifdef NSIS_UNICODE
            FileWriteUTF16LE $MUI_TEMP1 "{"
          !else
            FileWrite $MUI_TEMP1 "{"
          !endif
          Goto endfirstleveltest
        StrCmp $R1 "}" +2 0
          !ifdef NSIS_UNICODE
            FileWriteUTF16LE $MUI_TEMP1 "|"
          !else
            FileWrite $MUI_TEMP1 "|"
          !endif
      endfirstleveltest:
        StrCmp $R2 "0" 0 +4
          StrCmp $R0 "0" +3 0
            StrCmp $R1 "}" +2 0
            !ifdef NSIS_UNICODE
              FileWriteUTF16LE $MUI_TEMP1 "|"
            !else
              FileWrite $MUI_TEMP1 "|"
            !endif

      !ifdef NSIS_UNICODE
        FileWriteUTF16LE $MUI_TEMP1 "$R6"
      !else
        FileWrite $MUI_TEMP1 "$R6"
      !endif

      Push $R5
      Push "$R4\$R6"
      Call ${CREATELIST}
      Pop $R1

      IntOp $R0 $R0 + 1

      Goto loop
    end:

    StrCpy $R4 "0"

    StrCmp $R2 "0" +4 0
      StrCmp $R0 "0" +3 0
        !ifdef NSIS_UNICODE
          FileWriteUTF16LE $MUI_TEMP1 "}"
        !else
          FileWrite $MUI_TEMP1 "}"
        !endif
        StrCpy $R4 "}"

  nsArray::Clear "SMProgList$R2"

  Pop $R6
  Pop $R5
  Pop $R3
  Pop $R1
  Pop $R0

  StrCmp $R2 "0" 0 nolevel0
    Pop $R2
    Pop $R4
    Goto +3
  nolevel0:
    Pop $R2
    Exch $R4  ; return "}" if it is the last character writed in the ini file, "0" otherwise and nothing if root directory

!macroend




!macro UMUI_INTERNAL_PAGES_SETUPTYPE_MAINTENANCE_INI_4OPTIONS FILE

  !ifdef UMUI_USE_SMALL_PAGES
    !insertmacro INSTALLOPTIONS_WRITE "${FILE}" "Field 1" Bottom 17
    !insertmacro INSTALLOPTIONS_WRITE "${FILE}" "Field 2" Top 17
    !insertmacro INSTALLOPTIONS_WRITE "${FILE}" "Field 2" Bottom 27
    !insertmacro INSTALLOPTIONS_WRITE "${FILE}" "Field 3" Top 27
    !insertmacro INSTALLOPTIONS_WRITE "${FILE}" "Field 3" Bottom 47
    !insertmacro INSTALLOPTIONS_WRITE "${FILE}" "Field 4" Top 27
    !insertmacro INSTALLOPTIONS_WRITE "${FILE}" "Field 4" Bottom 48
    !insertmacro INSTALLOPTIONS_WRITE "${FILE}" "Field 5" Top 48
    !insertmacro INSTALLOPTIONS_WRITE "${FILE}" "Field 5" Bottom 58
    !insertmacro INSTALLOPTIONS_WRITE "${FILE}" "Field 6" Top 58
    !insertmacro INSTALLOPTIONS_WRITE "${FILE}" "Field 6" Bottom 78
    !insertmacro INSTALLOPTIONS_WRITE "${FILE}" "Field 7" Top 58
    !insertmacro INSTALLOPTIONS_WRITE "${FILE}" "Field 7" Bottom 79
    !insertmacro INSTALLOPTIONS_WRITE "${FILE}" "Field 8" Top 79
    !insertmacro INSTALLOPTIONS_WRITE "${FILE}" "Field 8" Bottom 89
    !insertmacro INSTALLOPTIONS_WRITE "${FILE}" "Field 9" Top 89
    !insertmacro INSTALLOPTIONS_WRITE "${FILE}" "Field 9" Bottom 109
    !insertmacro INSTALLOPTIONS_WRITE "${FILE}" "Field 10" Top 89
    !insertmacro INSTALLOPTIONS_WRITE "${FILE}" "Field 10" Bottom 110
    !insertmacro INSTALLOPTIONS_WRITE "${FILE}" "Field 11" Top 110
    !insertmacro INSTALLOPTIONS_WRITE "${FILE}" "Field 11" Bottom 120
    !insertmacro INSTALLOPTIONS_WRITE "${FILE}" "Field 12" Top 120
    !insertmacro INSTALLOPTIONS_WRITE "${FILE}" "Field 12" Bottom 140
    !insertmacro INSTALLOPTIONS_WRITE "${FILE}" "Field 13" Top 120
    !insertmacro INSTALLOPTIONS_WRITE "${FILE}" "Field 13" Bottom 140
  !endif

!macroend



!macro UMUI_PAGE_SETUPTYPE

  !verbose push
  !verbose ${MUI_VERBOSE}

  !insertmacro MUI_PAGE_INIT

  !define /IfNDef UMUI_${MUI_PAGE_UNINSTALLER_PREFIX}SETUPTYPEPAGE

  !insertmacro MUI_DEFAULT_IOCONVERT UMUI_SETUPTYPEPAGE_TEXT "$(UMUI_${MUI_PAGE_UNINSTALLER_PREFIX}TEXT_SETUPTYPE_INFO_TEXT)"
  !insertmacro MUI_DEFAULT_IOCONVERT UMUI_SETUPTYPEPAGE_MINIMAL_TITLE "$(UMUI_TEXT_SETUPTYPE_MINIMAL_TITLE)"
  !insertmacro MUI_DEFAULT_IOCONVERT UMUI_SETUPTYPEPAGE_MINIMAL_TEXT "$(UMUI_${MUI_PAGE_UNINSTALLER_PREFIX}TEXT_SETUPTYPE_MINIMAL_TEXT)"
  !insertmacro MUI_DEFAULT_IOCONVERT UMUI_SETUPTYPEPAGE_STANDARD_TITLE "$(UMUI_TEXT_SETUPTYPE_STANDARD_TITLE)"
  !insertmacro MUI_DEFAULT_IOCONVERT UMUI_SETUPTYPEPAGE_STANDARD_TEXT "$(UMUI_${MUI_PAGE_UNINSTALLER_PREFIX}TEXT_SETUPTYPE_STANDARD_TEXT)"
  !insertmacro MUI_DEFAULT_IOCONVERT UMUI_SETUPTYPEPAGE_COMPLETE_TITLE "$(UMUI_TEXT_SETUPTYPE_COMPLETE_TITLE)"
  !insertmacro MUI_DEFAULT_IOCONVERT UMUI_SETUPTYPEPAGE_COMPLETE_TEXT "$(UMUI_${MUI_PAGE_UNINSTALLER_PREFIX}TEXT_SETUPTYPE_COMPLETE_TEXT)"
  !insertmacro MUI_DEFAULT_IOCONVERT UMUI_SETUPTYPEPAGE_CUSTOM_TITLE "$(UMUI_TEXT_SETUPTYPE_CUSTOM_TITLE)"
  !insertmacro MUI_DEFAULT_IOCONVERT UMUI_SETUPTYPEPAGE_CUSTOM_TEXT "$(UMUI_${MUI_PAGE_UNINSTALLER_PREFIX}TEXT_SETUPTYPE_CUSTOM_TEXT)"

!ifndef USE_MUIEx
;-----------------
  !define /IfNDef UMUI_SETUPTYPEPAGE_MINIMALBITMAP "${NSISDIR}\Contrib\Graphics\UltraModernUI\Minimal.bmp"
  !define /IfNDef UMUI_SETUPTYPEPAGE_STANDARDBITMAP "${NSISDIR}\Contrib\Graphics\UltraModernUI\Standard.bmp"
  !define /IfNDef UMUI_SETUPTYPEPAGE_COMPLETEBITMAP "${NSISDIR}\Contrib\Graphics\UltraModernUI\Complete.bmp"
  !define /IfNDef UMUI_SETUPTYPEPAGE_CUSTOMBITMAP "${NSISDIR}\Contrib\Graphics\UltraModernUI\Custom.bmp"
!else
;-----
  !define /IfNDef UMUI_SETUPTYPEPAGE_MINIMALBITMAP "${NSISDIR}\Contrib\Graphics\UltraModernUI\MinimalEx.bmp"
  !define /IfNDef UMUI_SETUPTYPEPAGE_STANDARDBITMAP "${NSISDIR}\Contrib\Graphics\UltraModernUI\StandardEx.bmp"
  !define /IfNDef UMUI_SETUPTYPEPAGE_COMPLETEBITMAP "${NSISDIR}\Contrib\Graphics\UltraModernUI\CompleteEx.bmp"
  !define /IfNDef UMUI_SETUPTYPEPAGE_CUSTOMBITMAP "${NSISDIR}\Contrib\Graphics\UltraModernUI\CustomEx.bmp"
!endif
;------

  !define /IfNDef UMUI_SETUPTYPEPAGE_DEFAULTCHOICE ${UMUI_CUSTOM}

  !ifdef UMUI_SETUPTYPEPAGE_REGISTRY_VALUENAME
    !ifndef UMUI_SETUPTYPEPAGE_REGISTRY_ROOT
      !ifdef UMUI_PARAMS_REGISTRY_ROOT
        !define UMUI_SETUPTYPEPAGE_REGISTRY_ROOT "${UMUI_PARAMS_REGISTRY_ROOT}"
      !else
        !error "For UMUI_SETUPTYPEPAGE_REGISTRY_VALUENAME, the UMUI_SETUPTYPEPAGE_REGISTRY_ROOT & UMUI_SETUPTYPEPAGE_REGISTRY_KEY parameters or else the UMUI_PARAMS_REGISTRY_ROOT & UMUI_PARAMS_REGISTRY_KEY global parameters must be defined."
      !endif
    !endif
    !ifndef UMUI_SETUPTYPEPAGE_REGISTRY_KEY
      !ifdef UMUI_PARAMS_REGISTRY_KEY
        !define UMUI_SETUPTYPEPAGE_REGISTRY_KEY "${UMUI_PARAMS_REGISTRY_KEY}"
      !else
        !error "For UMUI_SETUPTYPEPAGE_REGISTRY_VALUENAME, the UMUI_SETUPTYPEPAGE_REGISTRY_ROOT & UMUI_SETUPTYPEPAGE_REGISTRY_KEY parameters or else the UMUI_PARAMS_REGISTRY_ROOT & UMUI_PARAMS_REGISTRY_KEY global parameters must be defined."
      !endif
    !endif
  !endif

  !ifndef UMUI_VAR_UMUI_TEMP3
    Var UMUI_TEMP3
    !define UMUI_VAR_UMUI_TEMP3
  !endif

  !ifndef UMUI_VAR_UMUI_TEMP4
    Var UMUI_TEMP4
    !define UMUI_VAR_UMUI_TEMP4
  !endif

  PageEx ${MUI_PAGE_UNINSTALLER_FUNCPREFIX}custom

    PageCallbacks ${MUI_PAGE_UNINSTALLER_FUNCPREFIX}mui.setuptypePre_${MUI_UNIQUEID} ${MUI_PAGE_UNINSTALLER_FUNCPREFIX}mui.setuptypeLeave_${MUI_UNIQUEID}

    Caption " "

  PageExEnd

  !insertmacro UMUI_FUNCTION_SETUPTYPEPAGE ${MUI_PAGE_UNINSTALLER_FUNCPREFIX}mui.setuptypePre_${MUI_UNIQUEID} ${MUI_PAGE_UNINSTALLER_FUNCPREFIX}mui.setuptypeLeave_${MUI_UNIQUEID}

  !insertmacro MUI_UNSET UMUI_SETUPTYPEPAGE_TEXT
  !insertmacro MUI_UNSET UMUI_SETUPTYPEPAGE_MINIMAL_TITLE
  !insertmacro MUI_UNSET UMUI_SETUPTYPEPAGE_MINIMAL_TEXT
  !insertmacro MUI_UNSET UMUI_SETUPTYPEPAGE_STANDARD_TITLE
  !insertmacro MUI_UNSET UMUI_SETUPTYPEPAGE_STANDARD_TEXT
  !insertmacro MUI_UNSET UMUI_SETUPTYPEPAGE_COMPLETE_TITLE
  !insertmacro MUI_UNSET UMUI_SETUPTYPEPAGE_COMPLETE_TEXT
  !insertmacro MUI_UNSET UMUI_SETUPTYPEPAGE_CUSTOM_TITLE
  !insertmacro MUI_UNSET UMUI_SETUPTYPEPAGE_CUSTOM_TEXT

  !insertmacro MUI_UNSET UMUI_SETUPTYPEPAGE_MINIMALBITMAP
  !insertmacro MUI_UNSET UMUI_SETUPTYPEPAGE_STANDARDBITMAP
  !insertmacro MUI_UNSET UMUI_SETUPTYPEPAGE_COMPLETEBITMAP
  !insertmacro MUI_UNSET UMUI_SETUPTYPEPAGE_CUSTOMBITMAP

  !insertmacro MUI_UNSET UMUI_SETUPTYPEPAGE_MINIMAL
  !insertmacro MUI_UNSET UMUI_SETUPTYPEPAGE_STANDARD
  !insertmacro MUI_UNSET UMUI_SETUPTYPEPAGE_COMPLETE

  !insertmacro MUI_UNSET UMUI_SETUPTYPEPAGE_DEFAULTCHOICE
  !insertmacro MUI_UNSET UMUI_SETUPTYPEPAGE_REGISTRY_ROOT
  !insertmacro MUI_UNSET UMUI_SETUPTYPEPAGE_REGISTRY_KEY
  !insertmacro MUI_UNSET UMUI_SETUPTYPEPAGE_REGISTRY_VALUENAME

  !verbose pop

!macroend


!macro UMUI_UNPAGE_SETUPTYPE

  !verbose push
  !verbose ${MUI_VERBOSE}

  !insertmacro MUI_UNPAGE_INIT

    !insertmacro UMUI_PAGE_SETUPTYPE

  !insertmacro MUI_UNPAGE_END

  !verbose pop

!macroend


!macro UMUI_FUNCTION_SETUPTYPEPAGE PRE LEAVE

  Function "${PRE}"

    IfFileExists "$PLUGINSDIR\SetupType.ini" alreadyExists

      !insertmacro INSTALLOPTIONS_EXTRACT_AS "${UMUI_MAINTENANCEUPDATESETUPTYPEPAGE_INI}" "SetupType.ini"

      ;reduce the size of the page win 4 options and a small installer
      !ifdef UMUI_SETUPTYPEPAGE_MINIMAL & UMUI_SETUPTYPEPAGE_STANDARD & UMUI_SETUPTYPEPAGE_COMPLETE
        !insertmacro UMUI_INTERNAL_PAGES_SETUPTYPE_MAINTENANCE_INI_4OPTIONS "SetupType.ini"
      !endif

      !insertmacro MUI_INSTALLOPTIONS_WRITE_DEFAULTCONVERT "SetupType.ini" "Field 1" "Text" "UMUI_SETUPTYPEPAGE_TEXT"

      ;Get registry and set the insttype
      StrCpy $UMUI_TEMP4 ${UMUI_SETUPTYPEPAGE_DEFAULTCHOICE}

      !ifdef UMUI_SETUPTYPEPAGE_REGISTRY_VALUENAME

        ReadRegStr $MUI_TEMP1 ${UMUI_SETUPTYPEPAGE_REGISTRY_ROOT} "${UMUI_SETUPTYPEPAGE_REGISTRY_KEY}" "${UMUI_SETUPTYPEPAGE_REGISTRY_VALUENAME}"

        StrCmp $MUI_TEMP1 "MINIMAL" 0 nominimal
          StrCpy $UMUI_TEMP4 ${UMUI_MINIMAL}
          Goto endreg
        nominimal:
        StrCmp $MUI_TEMP1 "STANDARD" 0 nostandard
          StrCpy $UMUI_TEMP4 ${UMUI_STANDARD}
          Goto endreg
        nostandard:
        StrCmp $MUI_TEMP1 "COMPLETE" 0 nocomplete
          StrCpy $UMUI_TEMP4 ${UMUI_COMPLETE}
          Goto endreg
        nocomplete:
        StrCmp $MUI_TEMP1 "CUSTOM" 0 endreg
          StrCpy $UMUI_TEMP4 ${UMUI_CUSTOM}
        endreg:

        ClearErrors

        ; IF page skipped save
        !insertmacro UMUI_ADDPARAMTOSAVETOREGISTRYKEY ${UMUI_SETUPTYPEPAGE_REGISTRY_ROOT} "${UMUI_SETUPTYPEPAGE_REGISTRY_KEY}" "${UMUI_SETUPTYPEPAGE_REGISTRY_VALUENAME}" $MUI_TEMP1

      !endif

      !define UMUI_INTERNAL_PAGE_SETUPTYPE_COUNTER 1

      !insertmacro UMUI_INTERNAL_PAGE_SETUPTYPE_ADDOPTION MINIMAL
      !insertmacro UMUI_INTERNAL_PAGE_SETUPTYPE_ADDOPTION STANDARD
      !insertmacro UMUI_INTERNAL_PAGE_SETUPTYPE_ADDOPTION COMPLETE

      File "/oname=$PLUGINSDIR\Custom.bmp" "${UMUI_SETUPTYPEPAGE_CUSTOMBITMAP}"
      !define /redef /math UMUI_INTERNAL_PAGE_SETUPTYPE_COUNTER ${UMUI_INTERNAL_PAGE_SETUPTYPE_COUNTER} + 1

      StrCmp $UMUI_TEMP4 ${UMUI_CUSTOM} 0 +3
        !insertmacro INSTALLOPTIONS_WRITE "SetupType.ini" "Field ${UMUI_INTERNAL_PAGE_SETUPTYPE_COUNTER}" State "1"
      Goto +2
        !insertmacro INSTALLOPTIONS_WRITE "SetupType.ini" "Field ${UMUI_INTERNAL_PAGE_SETUPTYPE_COUNTER}" State "0"

      !insertmacro INSTALLOPTIONS_WRITE "SetupType.ini" "Field ${UMUI_INTERNAL_PAGE_SETUPTYPE_COUNTER}" InstTypeID "-1"
      !insertmacro INSTALLOPTIONS_WRITE "SetupType.ini" "Field ${UMUI_INTERNAL_PAGE_SETUPTYPE_COUNTER}" InstTypeOption "${UMUI_CUSTOM}"
      !insertmacro INSTALLOPTIONS_WRITE "SetupType.ini" "Field ${UMUI_INTERNAL_PAGE_SETUPTYPE_COUNTER}" InstTypeOptionName "CUSTOM"

      !insertmacro MUI_INSTALLOPTIONS_WRITE_DEFAULTCONVERT  "SetupType.ini" "Field ${UMUI_INTERNAL_PAGE_SETUPTYPE_COUNTER}" "Text" "UMUI_SETUPTYPEPAGE_CUSTOM_TITLE"
      !define /redef /math UMUI_INTERNAL_PAGE_SETUPTYPE_COUNTER ${UMUI_INTERNAL_PAGE_SETUPTYPE_COUNTER} + 1
      !insertmacro INSTALLOPTIONS_WRITE "SetupType.ini" "Field ${UMUI_INTERNAL_PAGE_SETUPTYPE_COUNTER}" "Text" "$PLUGINSDIR\Custom.bmp"
      !define /redef /math UMUI_INTERNAL_PAGE_SETUPTYPE_COUNTER ${UMUI_INTERNAL_PAGE_SETUPTYPE_COUNTER} + 1
      !insertmacro MUI_INSTALLOPTIONS_WRITE_DEFAULTCONVERT  "SetupType.ini" "Field ${UMUI_INTERNAL_PAGE_SETUPTYPE_COUNTER}" "Text" "UMUI_SETUPTYPEPAGE_CUSTOM_TEXT"

      !insertmacro INSTALLOPTIONS_WRITE "SetupType.ini" "Settings" "NumFields" "${UMUI_INTERNAL_PAGE_SETUPTYPE_COUNTER}"

      !undef UMUI_INTERNAL_PAGE_SETUPTYPE_COUNTER

    alreadyExists:

    ; IF setup cancelled
    !insertmacro UMUI_ABORT_IF_INSTALLFLAG_IS ${UMUI_CANCELLED}|${UMUI_REPAIR}|${UMUI_UPDATE}

    ; Bodenseematze-2016-09-15: missing PRE-Function support added:
    !insertmacro MUI_PAGE_FUNCTION_CUSTOM PRE

    !insertmacro MUI_HEADER_TEXT_PAGE "$(UMUI_${MUI_PAGE_UNINSTALLER_PREFIX}TEXT_SETUPTYPE_TITLE)" "$(UMUI_${MUI_PAGE_UNINSTALLER_PREFIX}TEXT_SETUPTYPE_SUBTITLE)"

    !insertmacro MUI_PAGE_FUNCTION_CUSTOM SHOW

    !insertmacro INSTALLOPTIONS_DISPLAY "SetupType.ini"

    !insertmacro UMUI_FIX_BUTTONS_SKIN

  FunctionEnd

  Function "${LEAVE}"

    !insertmacro UMUI_INTERNAL_PAGE_SETUPTYPE_GETOPTION 2
    !insertmacro UMUI_INTERNAL_PAGE_SETUPTYPE_GETOPTION 5
    !insertmacro UMUI_INTERNAL_PAGE_SETUPTYPE_GETOPTION 8
    !insertmacro UMUI_INTERNAL_PAGE_SETUPTYPE_GETOPTION 11

    !insertmacro MUI_PAGE_FUNCTION_CUSTOM LEAVE

  FunctionEnd

!macroend

!macro UMUI_INTERNAL_PAGE_SETUPTYPE_ADDOPTION OPTION

  !ifdef UMUI_SETUPTYPEPAGE_${OPTION}
    File "/oname=$PLUGINSDIR\${OPTION}.bmp" "${UMUI_SETUPTYPEPAGE_${OPTION}BITMAP}"
    !define /redef /math UMUI_INTERNAL_PAGE_SETUPTYPE_COUNTER ${UMUI_INTERNAL_PAGE_SETUPTYPE_COUNTER} + 1

    ;search the ID of the InstType Associated to this option
    ClearErrors
    StrCpy $MUI_TEMP2 0
    loop${OPTION}:
      InstTypeGetText $MUI_TEMP2 $UMUI_TEMP3
      IfErrors notfound${OPTION}
      StrCmp $UMUI_TEMP3 "${UMUI_SETUPTYPEPAGE_${OPTION}}" found${OPTION} 0
        IntOp $MUI_TEMP2 $MUI_TEMP2 + 1
        Goto loop${OPTION}
    found${OPTION}:
      !insertmacro INSTALLOPTIONS_WRITE "SetupType.ini" "Field ${UMUI_INTERNAL_PAGE_SETUPTYPE_COUNTER}" InstTypeID "$MUI_TEMP2"
      Goto end${OPTION}
    notfound${OPTION}:
      ClearErrors
      MessageBox MB_OK "Error: ${UMUI_SETUPTYPEPAGE_${OPTION}} is not an defined InstType...$\nThis option will not work."
    end${OPTION}:

    StrCmp $UMUI_TEMP4 ${UMUI_${OPTION}} 0 +4
      !insertmacro INSTALLOPTIONS_WRITE "SetupType.ini" "Field ${UMUI_INTERNAL_PAGE_SETUPTYPE_COUNTER}" State "1"
      SetCurInstType $MUI_TEMP2
    Goto +2
      !insertmacro INSTALLOPTIONS_WRITE "SetupType.ini" "Field ${UMUI_INTERNAL_PAGE_SETUPTYPE_COUNTER}" State "0"

    !insertmacro INSTALLOPTIONS_WRITE "SetupType.ini" "Field ${UMUI_INTERNAL_PAGE_SETUPTYPE_COUNTER}" InstTypeOption "${UMUI_${OPTION}}"
    !insertmacro INSTALLOPTIONS_WRITE "SetupType.ini" "Field ${UMUI_INTERNAL_PAGE_SETUPTYPE_COUNTER}" InstTypeOptionName "${OPTION}"

    !insertmacro MUI_INSTALLOPTIONS_WRITE_DEFAULTCONVERT "SetupType.ini" "Field ${UMUI_INTERNAL_PAGE_SETUPTYPE_COUNTER}" "Text" "UMUI_SETUPTYPEPAGE_${OPTION}_TITLE"
    !define /redef /math UMUI_INTERNAL_PAGE_SETUPTYPE_COUNTER ${UMUI_INTERNAL_PAGE_SETUPTYPE_COUNTER} + 1
    !insertmacro INSTALLOPTIONS_WRITE "SetupType.ini" "Field ${UMUI_INTERNAL_PAGE_SETUPTYPE_COUNTER}" "Text" "$PLUGINSDIR\${OPTION}.bmp"
    !define /redef /math UMUI_INTERNAL_PAGE_SETUPTYPE_COUNTER ${UMUI_INTERNAL_PAGE_SETUPTYPE_COUNTER} + 1
    !insertmacro MUI_INSTALLOPTIONS_WRITE_DEFAULTCONVERT "SetupType.ini" "Field ${UMUI_INTERNAL_PAGE_SETUPTYPE_COUNTER}" "Text" "UMUI_SETUPTYPEPAGE_${OPTION}_TEXT"
  !endif

!macroend

!macro UMUI_INTERNAL_PAGE_SETUPTYPE_GETOPTION FIELDNUMBER

  !insertmacro INSTALLOPTIONS_READ $UMUI_TEMP3 "SetupType.ini" "Field ${FIELDNUMBER}" "InstTypeOption"
  !insertmacro INSTALLOPTIONS_READ $MUI_TEMP1 "SetupType.ini" "Field ${FIELDNUMBER}" "State"
  StrCmp $MUI_TEMP1 "1" 0 no${FIELDNUMBER}

    !insertmacro INSTALLOPTIONS_READ $MUI_TEMP2 "SetupType.ini" "Field ${FIELDNUMBER}" "InstTypeID"
    StrCmp $MUI_TEMP2 "-1" +2 0
      SetCurInstType $MUI_TEMP2

      !insertmacro UMUI_SET_INSTALLFLAG $UMUI_TEMP3

      !ifdef UMUI_SETUPTYPEPAGE_REGISTRY_VALUENAME
        !insertmacro INSTALLOPTIONS_READ $MUI_TEMP1 "SetupType.ini" "Field ${FIELDNUMBER}" "InstTypeOptionName"
        !insertmacro UMUI_ADDPARAMTOSAVETOREGISTRYKEY ${UMUI_SETUPTYPEPAGE_REGISTRY_ROOT} "${UMUI_SETUPTYPEPAGE_REGISTRY_KEY}" "${UMUI_SETUPTYPEPAGE_REGISTRY_VALUENAME}" $MUI_TEMP1
      !endif

    Goto end${FIELDNUMBER}
  no${FIELDNUMBER}:
    !insertmacro UMUI_UNSET_INSTALLFLAG $UMUI_TEMP3
  end${FIELDNUMBER}:

!macroend

!macro UMUI_GET_CHOOSEN_SETUP_TYPE_TEXT

  Push $R0
  Push $R1

  !insertmacro INSTALLOPTIONS_READ $R1 "SetupType.ini" "Field 2" "State"
  StrCmp $R1 "1" 0 +3
    !insertmacro INSTALLOPTIONS_READ $R0 "SetupType.ini" "Field 2" "Text"
    Goto end

  !insertmacro INSTALLOPTIONS_READ $R1 "SetupType.ini" "Field 5" "State"
  StrCmp $R1 "1" 0 +3
    !insertmacro INSTALLOPTIONS_READ $R0 "SetupType.ini" "Field 5" "Text"
    Goto end

  !insertmacro INSTALLOPTIONS_READ $R1 "SetupType.ini" "Field 8" "State"
  StrCmp $R1 "1" 0 +3
    !insertmacro INSTALLOPTIONS_READ $R0 "SetupType.ini" "Field 8" "Text"
    Goto end

  !insertmacro INSTALLOPTIONS_READ $R0 "SetupType.ini" "Field 11" "Text"

  end:

  Push $R1
  Exch $R0

!macroend



!macro UMUI_PAGE_MAINTENANCE

  !verbose push
  !verbose ${MUI_VERBOSE}

  !insertmacro MUI_PAGE_INIT

  !define /IfNDef UMUI_${MUI_PAGE_UNINSTALLER_PREFIX}MAINTENANCEPAGE

  !insertmacro MUI_DEFAULT_IOCONVERT UMUI_MAINTENANCEPAGE_TEXT "$(UMUI_TEXT_MAINTENANCE_INFO_TEXT)"
  !insertmacro MUI_DEFAULT_IOCONVERT UMUI_MAINTENANCEPAGE_MODIFY_TITLE "$(UMUI_TEXT_MAINTENANCE_MODIFY_TITLE)"
  !insertmacro MUI_DEFAULT_IOCONVERT UMUI_MAINTENANCEPAGE_MODIFY_TEXT "$(UMUI_TEXT_MAINTENANCE_MODIFY_TEXT)"
  !insertmacro MUI_DEFAULT_IOCONVERT UMUI_MAINTENANCEPAGE_REPAIR_TITLE "$(UMUI_TEXT_MAINTENANCE_REPAIR_TITLE)"
  !insertmacro MUI_DEFAULT_IOCONVERT UMUI_MAINTENANCEPAGE_REPAIR_TEXT "$(UMUI_TEXT_MAINTENANCE_REPAIR_TEXT)"
  !insertmacro MUI_DEFAULT_IOCONVERT UMUI_MAINTENANCEPAGE_REMOVE_TITLE "$(UMUI_TEXT_MAINTENANCE_REMOVE_TITLE)"
  !insertmacro MUI_DEFAULT_IOCONVERT UMUI_MAINTENANCEPAGE_REMOVE_TEXT "$(UMUI_TEXT_MAINTENANCE_REMOVE_TEXT)"
  !insertmacro MUI_DEFAULT_IOCONVERT UMUI_MAINTENANCEPAGE_CONTINUE_SETUP_TITLE "$(UMUI_TEXT_MAINTENANCE_CONTINUE_TITLE)"
  !insertmacro MUI_DEFAULT_IOCONVERT UMUI_MAINTENANCEPAGE_CONTINUE_SETUP_TEXT "$(UMUI_TEXT_MAINTENANCE_CONTINUE_TEXT)"

!ifndef USE_MUIEx
;-----------------
  !define /IfNDef UMUI_MAINTENANCEPAGE_MODIFYBITMAP "${NSISDIR}\Contrib\Graphics\UltraModernUI\Modify.bmp"
  !define /IfNDef UMUI_MAINTENANCEPAGE_REPAIRBITMAP "${NSISDIR}\Contrib\Graphics\UltraModernUI\Repair.bmp"
  !define /IfNDef UMUI_MAINTENANCEPAGE_REMOVEBITMAP "${NSISDIR}\Contrib\Graphics\UltraModernUI\Remove.bmp"
  !define /IfNDef UMUI_MAINTENANCEPAGE_CONTINUE_SETUPBITMAP "${NSISDIR}\Contrib\Graphics\UltraModernUI\Continue.bmp"
!else
;-----
  !define /IfNDef UMUI_MAINTENANCEPAGE_MODIFYBITMAP "${NSISDIR}\Contrib\Graphics\UltraModernUI\ModifyEx.bmp"
  !define /IfNDef UMUI_MAINTENANCEPAGE_REPAIRBITMAP "${NSISDIR}\Contrib\Graphics\UltraModernUI\RepairEx.bmp"
  !define /IfNDef UMUI_MAINTENANCEPAGE_REMOVEBITMAP "${NSISDIR}\Contrib\Graphics\UltraModernUI\RemoveEx.bmp"
  !define /IfNDef UMUI_MAINTENANCEPAGE_CONTINUE_SETUPBITMAP "${NSISDIR}\Contrib\Graphics\UltraModernUI\ContinueEx.bmp"
!endif
;------

  !ifdef UMUI_MAINTENANCEPAGE_MODIFY
    !define /IfNDef UMUI_MAINTENANCEPAGE_DEFAULTCHOICE ${UMUI_MODIFY}
  !else ifdef UMUI_MAINTENANCEPAGE_REPAIR
    !define /IfNDef UMUI_MAINTENANCEPAGE_DEFAULTCHOICE ${UMUI_REPAIR}
  !endif

  !ifndef UMUI_MAINTENANCEPAGE_MODIFY & UMUI_MAINTENANCEPAGE_REPAIR
    !error "Maintenance page: You need to define at least one of these options: UMUI_MAINTENANCEPAGE_MODIFY or UMUI_MAINTENANCEPAGE_REPAIR."
  !endif

  !ifdef UMUI_MAINTENANCEPAGE_REMOVE
    !ifndef UMUI_UNINSTALL_FULLPATH | UMUI_UNINSTALLPATH_REGISTRY_VALUENAME
      !error "Maintenance page: You need to set the UMUI_UNINSTALL_FULLPATH and UMUI_UNINSTALLPATH_REGISTRY_VALUENAME defines with the UMUI_MAINTENANCEPAGE_REMOVE option."
    !endif
  !endif

  !ifndef UMUI_PREUNINSTALL_FUNCTION
    !warning "Maintenance page: You need to set the UMUI_PREUNINSTALL_FUNCTION define with a clean install function."
  !endif

  !ifndef UMUI_VERBUILD_REGISTRY_VALUENAME | UMUI_VERBUILD
    !error "Maintenance page: You need to set the UMUI_VERBUILD_REGISTRY_VALUENAME and UMUI_VERBUILD defines with this page."
  !endif

  !ifndef UMUI_VAR_UMUI_TEMP3
    Var UMUI_TEMP3
    !define UMUI_VAR_UMUI_TEMP3
  !endif

  PageEx ${MUI_PAGE_UNINSTALLER_FUNCPREFIX}custom

    PageCallbacks ${MUI_PAGE_UNINSTALLER_FUNCPREFIX}mui.setuptypePre_${MUI_UNIQUEID} ${MUI_PAGE_UNINSTALLER_FUNCPREFIX}mui.setuptypeLeave_${MUI_UNIQUEID}

    Caption " "

  PageExEnd

  !insertmacro UMUI_FUNCTION_MAINTENANCEPAGE ${MUI_PAGE_UNINSTALLER_FUNCPREFIX}mui.setuptypePre_${MUI_UNIQUEID} ${MUI_PAGE_UNINSTALLER_FUNCPREFIX}mui.setuptypeLeave_${MUI_UNIQUEID}

  !insertmacro MUI_UNSET UMUI_MAINTENANCEPAGE_TEXT
  !insertmacro MUI_UNSET UMUI_MAINTENANCEPAGE_MODIFY_TITLE
  !insertmacro MUI_UNSET UMUI_MAINTENANCEPAGE_MODIFY_TEXT
  !insertmacro MUI_UNSET UMUI_MAINTENANCEPAGE_REPAIR_TITLE
  !insertmacro MUI_UNSET UMUI_MAINTENANCEPAGE_REPAIR_TEXT
  !insertmacro MUI_UNSET UMUI_MAINTENANCEPAGE_REMOVE_TITLE
  !insertmacro MUI_UNSET UMUI_MAINTENANCEPAGE_REMOVE_TEXT
  !insertmacro MUI_UNSET UMUI_MAINTENANCEPAGE_CONTINUE_SETUP_TITLE
  !insertmacro MUI_UNSET UMUI_MAINTENANCEPAGE_CONTINUE_SETUP_TEXT

  !insertmacro MUI_UNSET UMUI_MAINTENANCEPAGE_MODIFYBITMAP
  !insertmacro MUI_UNSET UMUI_MAINTENANCEPAGE_REPAIRBITMAP
  !insertmacro MUI_UNSET UMUI_MAINTENANCEPAGE_REMOVEBITMAP
  !insertmacro MUI_UNSET UMUI_MAINTENANCEPAGE_CONTINUE_SETUPBITMAP

  !insertmacro MUI_UNSET UMUI_MAINTENANCEPAGE_DEFAULTCHOICE

  !insertmacro MUI_UNSET UMUI_MAINTENANCEPAGE_MODIFY
  !insertmacro MUI_UNSET UMUI_MAINTENANCEPAGE_REPAIR
  !insertmacro MUI_UNSET UMUI_MAINTENANCEPAGE_REMOVE
  !insertmacro MUI_UNSET UMUI_MAINTENANCEPAGE_CONTINUE_SETUP

  !verbose pop

!macroend


!macro UMUI_UNPAGE_MAINTENANCE

  !verbose push
  !verbose ${MUI_VERBOSE}

  !insertmacro MUI_UNPAGE_INIT

    !ifndef UMUI_INSTALLERFULLPATH_REGISTRY_VALUENAME
      !warning "The MAINTENANCE unpage need the UMUI_INSTALLERFULLPATH_REGISTRY_VALUENAME define"
    !endif

    !ifndef UMUI_VAR_UMUI_TEMP4
      Var UMUI_TEMP4
      !define UMUI_VAR_UMUI_TEMP4
    !endif

    !insertmacro UMUI_PAGE_MAINTENANCE

    ; IF installer can't be found
    !define /redef UMUI_ABORT_IF_INSTALLFLAG_IS ${UMUI_CANCELLED}|${UMUI_REMOVE}
    !define MUI_PAGE_CUSTOMFUNCTION_LEAVE un.umui.fileRequestLeave

    !define UMUI_FILEDISKREQUESTPAGE_VARIABLE UMUI_TEMP4
    !define UMUI_FILEDISKREQUESTPAGE_FILE_NAME $MUI_TEMP2
    !define MUI_PAGE_HEADER_TEXT "$(UMUI_TEXT_MAINTENANCE_TITLE)"

    Function un.umui.fileRequestLeave

      ;Save the new installer file location
      !ifdef UMUI_INSTALLERFULLPATH_REGISTRY_VALUENAME

        !ifndef UMUI_INSTALLERFULLPATH_REGISTRY_ROOT
          !ifdef UMUI_PARAMS_REGISTRY_ROOT
            !define UMUI_INSTALLERFULLPATH_REGISTRY_ROOT "${UMUI_PARAMS_REGISTRY_ROOT}"
          !else
            !error "For UMUI_INSTALLERFULLPATH_REGISTRY_VALUENAME, the UMUI_INSTALLERFULLPATH_REGISTRY_ROOT & UMUI_INSTALLERFULLPATH_REGISTRY_KEY parameters or else the UMUI_PARAMS_REGISTRY_ROOT & UMUI_PARAMS_REGISTRY_KEY global parameters must be defined."
          !endif
        !endif
        !ifndef UMUI_INSTALLERFULLPATH_REGISTRY_KEY
          !ifdef UMUI_PARAMS_REGISTRY_KEY
            !define UMUI_INSTALLERFULLPATH_REGISTRY_KEY "${UMUI_PARAMS_REGISTRY_KEY}"
          !else
            !error "For UMUI_INSTALLERFULLPATH_REGISTRY_VALUENAME, the UMUI_INSTALLERFULLPATH_REGISTRY_ROOT & UMUI_INSTALLERFULLPATH_REGISTRY_KEY parameters or else the UMUI_PARAMS_REGISTRY_ROOT & UMUI_PARAMS_REGISTRY_KEY global parameters must be defined."
          !endif
        !endif

        !insertmacro UMUI_ADDPARAMTOSAVETOREGISTRYKEY ${UMUI_INSTALLERFULLPATH_REGISTRY_ROOT} "${UMUI_INSTALLERFULLPATH_REGISTRY_KEY}" "${UMUI_INSTALLERFULLPATH_REGISTRY_VALUENAME}" "$${UMUI_FILEDISKREQUESTPAGE_VARIABLE}\${UMUI_FILEDISKREQUESTPAGE_FILE_NAME}"
      !endif

      !insertmacro UMUI_IF_INSTALLFLAG_IS ${UMUI_MODIFY}
        ;Recall this programm and quit
        !insertmacro UMUI_GET_PARAMETERS
        Pop $MUI_TEMP2

        !insertmacro UMUI_DELETE_PLUGINDIR
        HideWindow

        ExecWait '"$${UMUI_FILEDISKREQUESTPAGE_VARIABLE}\${UMUI_FILEDISKREQUESTPAGE_FILE_NAME}" $MUI_TEMP2 /modify /L=$LANGUAGE'
        Quit
      !insertmacro UMUI_ENDIF_INSTALLFLAG

      !insertmacro UMUI_IF_INSTALLFLAG_IS ${UMUI_REPAIR}
        ;Recall this programm and quit
        !insertmacro UMUI_GET_PARAMETERS
        Pop $MUI_TEMP2

        !insertmacro UMUI_DELETE_PLUGINDIR
        HideWindow

        ExecWait '"$${UMUI_FILEDISKREQUESTPAGE_VARIABLE}\${UMUI_FILEDISKREQUESTPAGE_FILE_NAME}" $MUI_TEMP2 /repair /L=$LANGUAGE'
        Quit
      !insertmacro UMUI_ENDIF_INSTALLFLAG

    FunctionEnd

    !insertmacro UMUI_PAGE_FILEDISKREQUEST

  !insertmacro MUI_UNPAGE_END

  !verbose pop

!macroend


!macro UMUI_FUNCTION_MAINTENANCEPAGE PRE LEAVE

  Function "${PRE}"

    ; IF setup cancelled
    !insertmacro UMUI_ABORT_IF_INSTALLFLAG_IS ${UMUI_CANCELLED}|${UMUI_UPDATE}
    !insertmacro UMUI_ABORT_IF_INSTALLFLAG_ISNOT ${UMUI_SAMEVERSION}

    !insertmacro UMUI_IF_INSTALLFLAG_IS ${UMUI_ABORTFIRSTTIME}

      ; call uninstaller if the /remove command line argument is set
      !ifndef MUI_UNINSTALLER

        !insertmacro UMUI_IF_INSTALLFLAG_IS ${UMUI_REMOVE}

          IfFileExists "${UMUI_UNINSTALL_FULLPATH}" 0 uninstaller_not_found
            ;Recall this programm and quit
            !insertmacro UMUI_GET_PARAMETERS
            Pop $MUI_TEMP2

            !insertmacro UMUI_DELETE_PLUGINDIR
            HideWindow

            ExecWait '"${UMUI_UNINSTALL_FULLPATH}" $MUI_TEMP2 /remove /L=$LANGUAGE'
            Quit
          uninstaller_not_found:
          ClearErrors

        !insertmacro UMUI_ENDIF_INSTALLFLAG
        ;else continue

      ; call installer if the /modify, /repair or /continue command line argument is set
      !else

        ReadRegStr $MUI_TEMP1 ${UMUI_PARAMS_REGISTRY_ROOT} "${UMUI_PARAMS_REGISTRY_KEY}" "${UMUI_INSTALLERFULLPATH_REGISTRY_VALUENAME}"
        IfFileExists "$MUI_TEMP1" 0 installer_not_found

          !insertmacro UMUI_IF_INSTALLFLAG_IS ${UMUI_MODIFY}|${UMUI_REPAIR}|${UMUI_CONTINUE_SETUP}
            ;Recall this programm and quit
            !insertmacro UMUI_GET_PARAMETERS
            Pop $MUI_TEMP2

            !insertmacro UMUI_DELETE_PLUGINDIR
            HideWindow
          !insertmacro UMUI_ENDIF_INSTALLFLAG

          !insertmacro UMUI_IF_INSTALLFLAG_IS ${UMUI_MODIFY}
            ExecWait '"$MUI_TEMP1" $MUI_TEMP2 /modify /L=$LANGUAGE'
            Quit
          !insertmacro UMUI_ENDIF_INSTALLFLAG

          !insertmacro UMUI_IF_INSTALLFLAG_IS ${UMUI_REPAIR}
            ExecWait '"$MUI_TEMP1" $MUI_TEMP2 /repair /L=$LANGUAGE'
            Quit
          !insertmacro UMUI_ENDIF_INSTALLFLAG

          !insertmacro UMUI_IF_INSTALLFLAG_IS ${UMUI_CONTINUE_SETUP}
            ExecWait '"$MUI_TEMP1" $MUI_TEMP2 /continue /L=$LANGUAGE'
            Quit
          !insertmacro UMUI_ENDIF_INSTALLFLAG

        installer_not_found:
        ClearErrors

        ; continue to the next page for the File Request, Set the variable
        !insertmacro UMUI_GETPARENTFOLDER $MUI_TEMP1
        Pop $UMUI_TEMP4

        StrLen $UMUI_TEMP3 $UMUI_TEMP4
        StrCpy $MUI_TEMP2 $MUI_TEMP1 "" $UMUI_TEMP3

      !endif


      !insertmacro UMUI_UNSET_INSTALLFLAG ${UMUI_ABORTFIRSTTIME}
      Abort
    !insertmacro UMUI_ENDIF_INSTALLFLAG

    ; Bodenseematze-2016-09-15: missing PRE-Function support added:
    !insertmacro MUI_PAGE_FUNCTION_CUSTOM PRE

    !insertmacro MUI_HEADER_TEXT_PAGE "$(UMUI_TEXT_MAINTENANCE_TITLE)" "$(UMUI_TEXT_MAINTENANCE_SUBTITLE)"

    IfFileExists "$PLUGINSDIR\Maintenance.ini" alreadyExists

      !insertmacro INSTALLOPTIONS_EXTRACT_AS "${UMUI_MAINTENANCEUPDATESETUPTYPEPAGE_INI}" "Maintenance.ini"

      ;reduce the size of the page win 4 options and a small installer
      !ifdef UMUI_MAINTENANCEPAGE_MODIFY & UMUI_MAINTENANCEPAGE_REPAIR & UMUI_MAINTENANCEPAGE_REMOVE & UMUI_MAINTENANCEPAGE_CONTINUE_SETUP
        !insertmacro UMUI_INTERNAL_PAGES_SETUPTYPE_MAINTENANCE_INI_4OPTIONS "Maintenance.ini"
      !endif

      !insertmacro MUI_INSTALLOPTIONS_WRITE_DEFAULTCONVERT "Maintenance.ini" "Field 1" "Text" "UMUI_MAINTENANCEPAGE_TEXT"

      StrCpy $UMUI_TEMP3 ${UMUI_MAINTENANCEPAGE_DEFAULTCHOICE}
      !insertmacro UMUI_IF_INSTALLFLAG_IS ${UMUI_MODIFY}
        StrCpy $UMUI_TEMP3 ${UMUI_MODIFY}
      !insertmacro UMUI_ENDIF_INSTALLFLAG
      !insertmacro UMUI_IF_INSTALLFLAG_IS ${UMUI_REPAIR}
        StrCpy $UMUI_TEMP3 ${UMUI_REPAIR}
      !insertmacro UMUI_ENDIF_INSTALLFLAG
      !insertmacro UMUI_IF_INSTALLFLAG_IS ${UMUI_REMOVE}
        StrCpy $UMUI_TEMP3 ${UMUI_REMOVE}
      !insertmacro UMUI_ENDIF_INSTALLFLAG

      !define UMUI_INTERNAL_PAGE_MAINTENANCE_COUNTER 1

      !insertmacro UMUI_INTERNAL_PAGE_MAINTENANCE_ADDOPTION MODIFY
      !insertmacro UMUI_INTERNAL_PAGE_MAINTENANCE_ADDOPTION REPAIR
      !insertmacro UMUI_INTERNAL_PAGE_MAINTENANCE_ADDOPTION REMOVE
      !insertmacro UMUI_INTERNAL_PAGE_MAINTENANCE_ADDOPTION CONTINUE_SETUP

      !insertmacro INSTALLOPTIONS_WRITE "Maintenance.ini" "Settings" "NumFields" "${UMUI_INTERNAL_PAGE_MAINTENANCE_COUNTER}"

      !undef UMUI_INTERNAL_PAGE_MAINTENANCE_COUNTER

    alreadyExists:

    !insertmacro MUI_PAGE_FUNCTION_CUSTOM SHOW

    !insertmacro INSTALLOPTIONS_DISPLAY "Maintenance.ini"

    !insertmacro UMUI_FIX_BUTTONS_SKIN

  FunctionEnd

  Function "${LEAVE}"

    !insertmacro UMUI_INTERNAL_PAGE_MAINTENANCE_GETOPTION 2
    !insertmacro UMUI_INTERNAL_PAGE_MAINTENANCE_GETOPTION 5
    !insertmacro UMUI_INTERNAL_PAGE_MAINTENANCE_GETOPTION 8
    !insertmacro UMUI_INTERNAL_PAGE_MAINTENANCE_GETOPTION 11

    !insertmacro MUI_PAGE_FUNCTION_CUSTOM LEAVE

    !ifndef MUI_UNINSTALLER

      !insertmacro UMUI_IF_INSTALLFLAG_ISNOT ${UMUI_CANCELLED}

        !insertmacro UMUI_IF_INSTALLFLAG_IS ${UMUI_REMOVE}
          ;Recall this programm and quit
          !insertmacro UMUI_GET_PARAMETERS
          Pop $MUI_TEMP2

          !insertmacro UMUI_DELETE_PLUGINDIR
          HideWindow

          ExecWait '"${UMUI_UNINSTALL_FULLPATH}" $MUI_TEMP2 /remove /L=$LANGUAGE'
          Quit
        !insertmacro UMUI_ENDIF_INSTALLFLAG
        ;else continue

      !insertmacro UMUI_ENDIF_INSTALLFLAG

    !else

      ;Remove?
      !insertmacro UMUI_IF_INSTALLFLAG_ISNOT ${UMUI_REMOVE}&${UMUI_CANCELLED}

        ReadRegStr $MUI_TEMP1 ${UMUI_PARAMS_REGISTRY_ROOT} "${UMUI_PARAMS_REGISTRY_KEY}" "${UMUI_INSTALLERFULLPATH_REGISTRY_VALUENAME}"
        IfFileExists "$MUI_TEMP1" 0 installer_not_found

          !insertmacro UMUI_IF_INSTALLFLAG_IS ${UMUI_MODIFY}|${UMUI_REPAIR}|${UMUI_CONTINUE_SETUP}
            ;Recall this programm and quit
            !insertmacro UMUI_GET_PARAMETERS
            Pop $MUI_TEMP2

            !insertmacro UMUI_DELETE_PLUGINDIR
            HideWindow
          !insertmacro UMUI_ENDIF_INSTALLFLAG

          !insertmacro UMUI_IF_INSTALLFLAG_IS ${UMUI_MODIFY}
            ExecWait '"$MUI_TEMP1" $MUI_TEMP2 /modify /L=$LANGUAGE'
            Quit
          !insertmacro UMUI_ENDIF_INSTALLFLAG

          !insertmacro UMUI_IF_INSTALLFLAG_IS ${UMUI_REPAIR}
            ExecWait '"$MUI_TEMP1" $MUI_TEMP2 /repair /L=$LANGUAGE'
            Quit
          !insertmacro UMUI_ENDIF_INSTALLFLAG

          !insertmacro UMUI_IF_INSTALLFLAG_IS ${UMUI_CONTINUE_SETUP}
            ExecWait '"$MUI_TEMP1" $MUI_TEMP2 /continue /L=$LANGUAGE'
            Quit
          !insertmacro UMUI_ENDIF_INSTALLFLAG

        installer_not_found:
        ClearErrors

        !insertmacro UMUI_GETPARENTFOLDER $MUI_TEMP1
        Pop $UMUI_TEMP4

        StrLen $UMUI_TEMP3 $UMUI_TEMP4
        StrCpy $MUI_TEMP2 $MUI_TEMP1 "" $UMUI_TEMP3

      !insertmacro UMUI_ENDIF_INSTALLFLAG

      ;if installer file not found: continue (the next page will request the install exedir folder)

    !endif

  FunctionEnd

!macroend


!macro UMUI_INTERNAL_PAGE_MAINTENANCE_ADDOPTION OPTION

  !ifdef UMUI_MAINTENANCEPAGE_${OPTION}
    File "/oname=$PLUGINSDIR\${OPTION}.bmp" "${UMUI_MAINTENANCEPAGE_${OPTION}BITMAP}"
    !define /redef /math UMUI_INTERNAL_PAGE_MAINTENANCE_COUNTER ${UMUI_INTERNAL_PAGE_MAINTENANCE_COUNTER} + 1

    StrCmp $UMUI_TEMP3 ${UMUI_${OPTION}} 0 +4
      !insertmacro INSTALLOPTIONS_WRITE "Maintenance.ini" "Field ${UMUI_INTERNAL_PAGE_MAINTENANCE_COUNTER}" State "1"
      SetCurInstType $MUI_TEMP2
    Goto +2
      !insertmacro INSTALLOPTIONS_WRITE "Maintenance.ini" "Field ${UMUI_INTERNAL_PAGE_MAINTENANCE_COUNTER}" State "0"

    !ifdef UMUI_MAINTENANCEPAGE_REMOVE
      StrCmp ${OPTION} "REMOVE" 0 no${OPTION}
        IfFileExists "${UMUI_UNINSTALL_FULLPATH}" no${OPTION} 0
          ClearErrors
          !insertmacro INSTALLOPTIONS_WRITE "Maintenance.ini" "Field ${UMUI_INTERNAL_PAGE_MAINTENANCE_COUNTER}" State "0"
          !insertmacro INSTALLOPTIONS_WRITE "Maintenance.ini" "Field ${UMUI_INTERNAL_PAGE_MAINTENANCE_COUNTER}" Flags DISABLED
      no${OPTION}:
    !endif

    !insertmacro INSTALLOPTIONS_WRITE "Maintenance.ini" "Field ${UMUI_INTERNAL_PAGE_MAINTENANCE_COUNTER}" Maintenance "${UMUI_${OPTION}}"
    !insertmacro INSTALLOPTIONS_WRITE "Maintenance.ini" "Field ${UMUI_INTERNAL_PAGE_MAINTENANCE_COUNTER}" MaintenanceName "${OPTION}"

    !insertmacro MUI_INSTALLOPTIONS_WRITE_DEFAULTCONVERT "Maintenance.ini" "Field ${UMUI_INTERNAL_PAGE_MAINTENANCE_COUNTER}" "Text" "UMUI_MAINTENANCEPAGE_${OPTION}_TITLE"
    !define /redef /math UMUI_INTERNAL_PAGE_MAINTENANCE_COUNTER ${UMUI_INTERNAL_PAGE_MAINTENANCE_COUNTER} + 1
    !insertmacro INSTALLOPTIONS_WRITE "Maintenance.ini" "Field ${UMUI_INTERNAL_PAGE_MAINTENANCE_COUNTER}" Text "$PLUGINSDIR\${OPTION}.bmp"
    !define /redef /math UMUI_INTERNAL_PAGE_MAINTENANCE_COUNTER ${UMUI_INTERNAL_PAGE_MAINTENANCE_COUNTER} + 1
    !insertmacro MUI_INSTALLOPTIONS_WRITE_DEFAULTCONVERT "Maintenance.ini" "Field ${UMUI_INTERNAL_PAGE_MAINTENANCE_COUNTER}" "Text" "UMUI_MAINTENANCEPAGE_${OPTION}_TEXT"
  !endif

!macroend

!macro UMUI_INTERNAL_PAGE_MAINTENANCE_GETOPTION FIELDNUMBER

  !insertmacro INSTALLOPTIONS_READ $UMUI_TEMP3 "Maintenance.ini" "Field ${FIELDNUMBER}" "Maintenance"
  !insertmacro INSTALLOPTIONS_READ $MUI_TEMP1 "Maintenance.ini" "Field ${FIELDNUMBER}" "State"
  StrCmp $MUI_TEMP1 "1" 0 no${FIELDNUMBER}

    !insertmacro UMUI_SET_INSTALLFLAG $UMUI_TEMP3
    Goto end${FIELDNUMBER}

  no${FIELDNUMBER}:
    !insertmacro UMUI_UNSET_INSTALLFLAG $UMUI_TEMP3

  end${FIELDNUMBER}:

!macroend





!macro UMUI_PAGE_UPDATE

  !verbose push
  !verbose ${MUI_VERBOSE}

  !insertmacro MUI_PAGE_INIT

  !define /IfNDef UMUI_UPDATEPAGE

  !insertmacro MUI_DEFAULT_IOCONVERT UMUI_UPDATEPAGE_TEXT "$(UMUI_TEXT_UPDATE_INFO_TEXT)"
  !insertmacro MUI_DEFAULT_IOCONVERT UMUI_UPDATEPAGE_UPDATE_TITLE "$(UMUI_TEXT_UPDATE_UPDATE_TITLE)"
  !insertmacro MUI_DEFAULT_IOCONVERT UMUI_UPDATEPAGE_UPDATE_TEXT "$(UMUI_TEXT_UPDATE_UPDATE_TEXT)"
  !insertmacro MUI_DEFAULT_IOCONVERT UMUI_UPDATEPAGE_REMOVE_TITLE "$(UMUI_TEXT_UPDATE_REMOVE_TITLE)"
  !insertmacro MUI_DEFAULT_IOCONVERT UMUI_UPDATEPAGE_REMOVE_TEXT "$(UMUI_TEXT_UPDATE_REMOVE_TEXT)"
  !insertmacro MUI_DEFAULT_IOCONVERT UMUI_UPDATEPAGE_CONTINUE_SETUP_TITLE "$(UMUI_TEXT_UPDATE_CONTINUE_TITLE)"
  !insertmacro MUI_DEFAULT_IOCONVERT UMUI_UPDATEPAGE_CONTINUE_SETUP_TEXT "$(UMUI_TEXT_UPDATE_CONTINUE_TEXT)"

!ifndef USE_MUIEx
;-----------------
  !define /IfNDef UMUI_UPDATEPAGE_UPDATEBITMAP "${NSISDIR}\Contrib\Graphics\UltraModernUI\Modify.bmp"
  !define /IfNDef UMUI_UPDATEPAGE_REMOVEBITMAP "${NSISDIR}\Contrib\Graphics\UltraModernUI\Remove.bmp"
  !define /IfNDef UMUI_UPDATEPAGE_CONTINUE_SETUPBITMAP "${NSISDIR}\Contrib\Graphics\UltraModernUI\Continue.bmp"
!else
;-----
  !define /IfNDef UMUI_UPDATEPAGE_UPDATEBITMAP "${NSISDIR}\Contrib\Graphics\UltraModernUI\ModifyEx.bmp"
  !define /IfNDef UMUI_UPDATEPAGE_REMOVEBITMAP "${NSISDIR}\Contrib\Graphics\UltraModernUI\RemoveEx.bmp"
  !define /IfNDef UMUI_UPDATEPAGE_CONTINUE_SETUPBITMAP "${NSISDIR}\Contrib\Graphics\UltraModernUI\ContinueEx.bmp"
!endif
;------

  !define /IfNDef UMUI_UPDATEPAGE_UPDATE
  !define /IfNDef UMUI_UPDATEPAGE_DEFAULTCHOICE ${UMUI_UPDATE}

  !ifndef UMUI_VERBUILD_REGISTRY_VALUENAME | UMUI_VERBUILD
    !error "Update page: You need to set the UMUI_VERBUILD_REGISTRY_VALUENAME and UMUI_VERBUILD defines with this page."
  !endif

  !ifndef UMUI_VAR_OLDVERSION
    Var OLDVERSION
    !define UMUI_VAR_OLDVERSION
  !endif

  !ifndef UMUI_VAR_NEWVERSION
    Var NEWVERSION
    !define UMUI_VAR_NEWVERSION
  !endif

  PageEx ${MUI_PAGE_UNINSTALLER_FUNCPREFIX}custom

    PageCallbacks ${MUI_PAGE_UNINSTALLER_FUNCPREFIX}mui.updatePre_${MUI_UNIQUEID} ${MUI_PAGE_UNINSTALLER_FUNCPREFIX}mui.updateLeave_${MUI_UNIQUEID}

    Caption " "

  PageExEnd

  !insertmacro UMUI_FUNCTION_UPDATEPAGE ${MUI_PAGE_UNINSTALLER_FUNCPREFIX}mui.updatePre_${MUI_UNIQUEID} ${MUI_PAGE_UNINSTALLER_FUNCPREFIX}mui.updateLeave_${MUI_UNIQUEID}

  !insertmacro MUI_UNSET UMUI_UPDATEPAGE_TEXT
  !insertmacro MUI_UNSET UMUI_UPDATEPAGE_UPDATE_TITLE
  !insertmacro MUI_UNSET UMUI_UPDATEPAGE_UPDATE_TEXT
  !insertmacro MUI_UNSET UMUI_UPDATEPAGE_REMOVE_TITLE
  !insertmacro MUI_UNSET UMUI_UPDATEPAGE_REMOVE_TEXT
  !insertmacro MUI_UNSET UMUI_UPDATEPAGE_CONTINUE_SETUP_TITLE
  !insertmacro MUI_UNSET UMUI_UPDATEPAGE_CONTINUE_SETUP_TEXT

  !insertmacro MUI_UNSET UMUI_UPDATEPAGE_UPDATEBITMAP
  !insertmacro MUI_UNSET UMUI_UPDATEPAGE_REMOVEBITMAP
  !insertmacro MUI_UNSET UMUI_UPDATEPAGE_CONTINUE_SETUPBITMAP

  !insertmacro MUI_UNSET UMUI_UPDATEPAGE_UPDATE
  !insertmacro MUI_UNSET UMUI_UPDATEPAGE_REMOVE
  !insertmacro MUI_UNSET UMUI_UPDATEPAGE_CONTINUE_SETUP

  !insertmacro MUI_UNSET UMUI_UPDATEPAGE_DEFAULTCHOICE

  !verbose pop

!macroend


!macro UMUI_FUNCTION_UPDATEPAGE PRE LEAVE

  Function "${PRE}"

    ; IF setup cancelled
    !insertmacro UMUI_ABORT_IF_INSTALLFLAG_IS ${UMUI_CANCELLED}|${UMUI_MODIFY}|${UMUI_REPAIR}

    ; call uninstaller if the /remove command line argument is set
    !insertmacro UMUI_IF_INSTALLFLAG_IS ${UMUI_REMOVE}

      IfFileExists "${UMUI_UNINSTALL_FULLPATH}" 0 uninstaller_not_found
        ;Recall this programm and quit
        !insertmacro UMUI_GET_PARAMETERS
        Pop $MUI_TEMP2

        !insertmacro UMUI_DELETE_PLUGINDIR
        HideWindow

        ExecWait '"${UMUI_UNINSTALL_FULLPATH}" $MUI_TEMP2 /remove /L=$LANGUAGE'
        Quit
      uninstaller_not_found:
      ClearErrors

    !insertmacro UMUI_ENDIF_INSTALLFLAG
    ;else continue

    !insertmacro UMUI_ABORT_IF_INSTALLFLAG_ISNOT ${UMUI_DIFFVERSION}

    ; Bodenseematze-2016-09-15: missing PRE-Function support added:
    !insertmacro MUI_PAGE_FUNCTION_CUSTOM PRE

    !insertmacro MUI_HEADER_TEXT_PAGE "$(UMUI_TEXT_UPDATE_TITLE)" "$(UMUI_TEXT_UPDATE_SUBTITLE)"

    IfFileExists "$PLUGINSDIR\Update.ini" alreadyExists
      !insertmacro INSTALLOPTIONS_EXTRACT_AS "${UMUI_MAINTENANCEUPDATESETUPTYPEPAGE_INI}" "Update.ini"

      !ifdef UMUI_VERSION
        StrCpy $NEWVERSION "${UMUI_VERSION}"
      !else
        StrCpy $NEWVERSION "${UMUI_VERBUILD}"
      !endif

      !ifdef UMUI_VERSION_REGISTRY_VALUENAME
        ReadRegStr $OLDVERSION ${UMUI_PARAMS_REGISTRY_ROOT} "${UMUI_PARAMS_REGISTRY_KEY}" "${UMUI_VERSION_REGISTRY_VALUENAME}"
        StrCmp $OLDVERSION "" 0 +2
          ReadRegStr $OLDVERSION ${UMUI_PARAMS_REGISTRY_ROOT} "${UMUI_PARAMS_REGISTRY_KEY}" "${UMUI_VERBUILD_REGISTRY_VALUENAME}"
      !else
        ReadRegStr $OLDVERSION ${UMUI_PARAMS_REGISTRY_ROOT} "${UMUI_PARAMS_REGISTRY_KEY}" "${UMUI_VERBUILD_REGISTRY_VALUENAME}"
      !endif

      !insertmacro MUI_INSTALLOPTIONS_WRITE_DEFAULTCONVERT "Update.ini" "Field 1" "Text" "UMUI_UPDATEPAGE_TEXT"

      !define UMUI_INTERNAL_PAGE_UPDATE_COUNTER 1

      !insertmacro UMUI_INTERNAL_PAGE_UPDATE_ADDOPTION UPDATE
      !insertmacro UMUI_INTERNAL_PAGE_UPDATE_ADDOPTION REMOVE
      !insertmacro UMUI_INTERNAL_PAGE_UPDATE_ADDOPTION CONTINUE_SETUP

      !insertmacro INSTALLOPTIONS_WRITE "Update.ini" "Settings" "NumFields" "${UMUI_INTERNAL_PAGE_UPDATE_COUNTER}"

      !undef UMUI_INTERNAL_PAGE_UPDATE_COUNTER

      !insertmacro UMUI_VERSIONCONVERT "${UMUI_VERBUILD}"
      Pop $MUI_TEMP1
      ReadRegStr $MUI_TEMP2 ${UMUI_PARAMS_REGISTRY_ROOT} "${UMUI_PARAMS_REGISTRY_KEY}" "${UMUI_VERBUILD_REGISTRY_VALUENAME}"
      !insertmacro UMUI_VERSIONCONVERT $MUI_TEMP2
      Pop $MUI_TEMP2
      !insertmacro UMUI_VERSIONCOMPARE $MUI_TEMP1 $MUI_TEMP2
      Pop $MUI_TEMP1

      StrCmp $MUI_TEMP1 1 alreadyExists 0
        ;disable the update option
        !insertmacro INSTALLOPTIONS_WRITE "Update.ini" "Field 2" State "0"
        !insertmacro INSTALLOPTIONS_WRITE "Update.ini" "Field 2" Flags DISABLED

        StrCmp ${UMUI_UPDATEPAGE_DEFAULTCHOICE} ${UMUI_UPDATE} 0 +2
        !insertmacro INSTALLOPTIONS_WRITE "Update.ini" "Field 5" State "1"

    alreadyExists:

    !insertmacro MUI_PAGE_FUNCTION_CUSTOM SHOW

    !insertmacro INSTALLOPTIONS_DISPLAY "Update.ini"

    !insertmacro UMUI_FIX_BUTTONS_SKIN

  FunctionEnd

  Function "${LEAVE}"

    !insertmacro UMUI_INTERNAL_PAGE_UPDATE_GETOPTION 2
    !insertmacro UMUI_INTERNAL_PAGE_UPDATE_GETOPTION 5
    !insertmacro UMUI_INTERNAL_PAGE_UPDATE_GETOPTION 8

    !insertmacro MUI_PAGE_FUNCTION_CUSTOM LEAVE

    !insertmacro UMUI_IF_INSTALLFLAG_ISNOT ${UMUI_CANCELLED}

      !insertmacro UMUI_IF_INSTALLFLAG_IS ${UMUI_REMOVE}
        ;Recall this programm and quit
        !insertmacro UMUI_GET_PARAMETERS
        Pop $MUI_TEMP2

        !insertmacro UMUI_DELETE_PLUGINDIR
        HideWindow

        ExecWait '"${UMUI_UNINSTALL_FULLPATH}" $MUI_TEMP2 /remove /L=$LANGUAGE'
        Quit
      !insertmacro UMUI_ENDIF_INSTALLFLAG
      ;else continue
    !insertmacro UMUI_ENDIF_INSTALLFLAG

  FunctionEnd

!macroend


!macro UMUI_INTERNAL_PAGE_UPDATE_ADDOPTION OPTION

  !ifdef UMUI_UPDATEPAGE_${OPTION}
    File "/oname=$PLUGINSDIR\${OPTION}.bmp" "${UMUI_UPDATEPAGE_${OPTION}BITMAP}"
    !define /redef /math UMUI_INTERNAL_PAGE_UPDATE_COUNTER ${UMUI_INTERNAL_PAGE_UPDATE_COUNTER} + 1

    StrCmp ${UMUI_UPDATEPAGE_DEFAULTCHOICE} ${UMUI_${OPTION}} 0 +4
      !insertmacro INSTALLOPTIONS_WRITE "Update.ini" "Field ${UMUI_INTERNAL_PAGE_UPDATE_COUNTER}" State "1"
    Goto +2
      !insertmacro INSTALLOPTIONS_WRITE "Update.ini" "Field ${UMUI_INTERNAL_PAGE_UPDATE_COUNTER}" State "0"

    !ifdef UMUI_UPDATEPAGE_REMOVE
      StrCmp ${OPTION} "REMOVE" 0 no${OPTION}
        IfFileExists "${UMUI_UNINSTALL_FULLPATH}" no${OPTION} 0
          ClearErrors
          !insertmacro INSTALLOPTIONS_WRITE "Update.ini" "Field ${UMUI_INTERNAL_PAGE_UPDATE_COUNTER}" State "0"
          !insertmacro INSTALLOPTIONS_WRITE "Update.ini" "Field ${UMUI_INTERNAL_PAGE_UPDATE_COUNTER}" Flags DISABLED
      no${OPTION}:
    !endif

    !insertmacro INSTALLOPTIONS_WRITE "Update.ini" "Field ${UMUI_INTERNAL_PAGE_UPDATE_COUNTER}" Update "${UMUI_${OPTION}}"
    !insertmacro INSTALLOPTIONS_WRITE "Update.ini" "Field ${UMUI_INTERNAL_PAGE_UPDATE_COUNTER}" UpdateName "${OPTION}"

    !insertmacro MUI_INSTALLOPTIONS_WRITE_DEFAULTCONVERT "Update.ini" "Field ${UMUI_INTERNAL_PAGE_UPDATE_COUNTER}" "Text" "UMUI_UPDATEPAGE_${OPTION}_TITLE"
    !define /redef /math UMUI_INTERNAL_PAGE_UPDATE_COUNTER ${UMUI_INTERNAL_PAGE_UPDATE_COUNTER} + 1
    !insertmacro INSTALLOPTIONS_WRITE "Update.ini" "Field ${UMUI_INTERNAL_PAGE_UPDATE_COUNTER}" "Text" "$PLUGINSDIR\${OPTION}.bmp"
    !define /redef /math UMUI_INTERNAL_PAGE_UPDATE_COUNTER ${UMUI_INTERNAL_PAGE_UPDATE_COUNTER} + 1
    !insertmacro MUI_INSTALLOPTIONS_WRITE_DEFAULTCONVERT "Update.ini" "Field ${UMUI_INTERNAL_PAGE_UPDATE_COUNTER}" "Text" "UMUI_UPDATEPAGE_${OPTION}_TEXT"
  !endif

!macroend

!macro UMUI_INTERNAL_PAGE_UPDATE_GETOPTION FIELDNUMBER

  !insertmacro INSTALLOPTIONS_READ $MUI_TEMP2 "Update.ini" "Field ${FIELDNUMBER}" "Update"
  !insertmacro INSTALLOPTIONS_READ $MUI_TEMP1 "Update.ini" "Field ${FIELDNUMBER}" "State"
  StrCmp $MUI_TEMP1 "1" 0 no${FIELDNUMBER}
    !insertmacro UMUI_SET_INSTALLFLAG $MUI_TEMP2
    Goto end${FIELDNUMBER}
  no${FIELDNUMBER}:
    !insertmacro UMUI_UNSET_INSTALLFLAG $MUI_TEMP2
  end${FIELDNUMBER}:

!macroend


!macro UMUI_PAGE_FILEDISKREQUEST

  !verbose push
  !verbose ${MUI_VERBOSE}

  !insertmacro MUI_PAGE_INIT

  !define /IfNDef UMUI_${MUI_PAGE_UNINSTALLER_PREFIX}FILEDISKREQUESTPAGE

  !ifdef UMUI_FILEDISKREQUESTPAGE_FILE_TO_FOUND
    !warning "The UMUI_FILEDISKREQUESTPAGE_FILE_TO_FOUND define was renamed UMUI_FILEDISKREQUESTPAGE_FILE_NAME"
    !define /IfNDef UMUI_FILEDISKREQUESTPAGE_FILE_NAME "{UMUI_FILEDISKREQUESTPAGE_FILE_TO_FOUND}"
    !undef UMUI_FILEDISKREQUESTPAGE_FILE_TO_FOUND
  !endif

  !ifndef UMUI_FILEDISKREQUESTPAGE_FILE_NAME || UMUI_FILEDISKREQUESTPAGE_VARIABLE
    !error "For the FILEDISKREQUEST page, you need to define UMUI_FILEDISKREQUESTPAGE_FILE_NAME and UMUI_FILEDISKREQUESTPAGE_VARIABLE."
  !endif

  !ifdef UMUI_FILEDISKREQUESTPAGE_DISK_NAME
    !define /IfNDef UMUI_FILEDISKREQUESTPAGE_TEXT_TOP "$(UMUI_TEXT_FILEDISKREQUEST_DISK) ${UMUI_FILEDISKREQUESTPAGE_DISK_NAME}."
  !else
    !define /IfNDef UMUI_FILEDISKREQUESTPAGE_TEXT_TOP "$(UMUI_TEXT_FILEDISKREQUEST_FILE_BEGIN) ${UMUI_FILEDISKREQUESTPAGE_FILE_NAME} $(UMUI_TEXT_FILEDISKREQUEST_FILE_END)"
  !endif

  !define /IfNDef UMUI_FILEDISKREQUESTPAGE_TEXT_PATH "$(UMUI_TEXT_FILEDISKREQUEST_PATH)"

  !ifndef MUI_VAR_HWND
    Var MUI_HWND
    !define MUI_VAR_HWND
  !endif

  PageEx ${MUI_PAGE_UNINSTALLER_FUNCPREFIX}directory

    PageCallbacks ${MUI_PAGE_UNINSTALLER_FUNCPREFIX}mui.filediskrequestPre_${MUI_UNIQUEID} ${MUI_PAGE_UNINSTALLER_FUNCPREFIX}mui.filediskrequestShow_${MUI_UNIQUEID} ${MUI_PAGE_UNINSTALLER_FUNCPREFIX}mui.filediskrequestLeave_${MUI_UNIQUEID}

    Caption " "

    DirText "${UMUI_FILEDISKREQUESTPAGE_TEXT_TOP}" "${UMUI_FILEDISKREQUESTPAGE_TEXT_PATH}" "$(^BrowseBtn)" "${UMUI_FILEDISKREQUESTPAGE_TEXT_TOP}"

    DirVar "$${UMUI_FILEDISKREQUESTPAGE_VARIABLE}"

    DirVerify leave

  PageExEnd

  !insertmacro UMUI_FUNCTION_FILEDISKREQUESTPAGE ${MUI_PAGE_UNINSTALLER_FUNCPREFIX}mui.filediskrequestPre_${MUI_UNIQUEID} ${MUI_PAGE_UNINSTALLER_FUNCPREFIX}mui.filediskrequestShow_${MUI_UNIQUEID} ${MUI_PAGE_UNINSTALLER_FUNCPREFIX}mui.filediskrequestLeave_${MUI_UNIQUEID}

  !undef UMUI_FILEDISKREQUESTPAGE_TEXT_TOP
  !undef UMUI_FILEDISKREQUESTPAGE_TEXT_PATH
  !undef UMUI_FILEDISKREQUESTPAGE_VARIABLE
  !undef UMUI_FILEDISKREQUESTPAGE_FILE_NAME

  !insertmacro MUI_UNSET UMUI_FILEDISKREQUESTPAGE_DISK_NAME

  !verbose pop

!macroend

!macro UMUI_UNPAGE_FILEDISKREQUEST

  !verbose push
  !verbose ${MUI_VERBOSE}

  !insertmacro MUI_UNPAGE_INIT

    !insertmacro UMUI_PAGE_FILEDISKREQUEST

  !insertmacro MUI_UNPAGE_END

  !verbose pop

!macroend

!macro UMUI_FUNCTION_FILEDISKREQUESTPAGE PRE SHOW LEAVE

  Function "${PRE}"

    ;if it's the installer page that call it and if remove : abort
    !insertmacro UMUI_ABORT_IF_INSTALLFLAG_IS ${UMUI_CANCELLED}

    !insertmacro MUI_PAGE_FUNCTION_CUSTOM PRE

    !ifdef UMUI_FILEDISKREQUESTPAGE_FILE_NAME
      !insertmacro MUI_HEADER_TEXT_PAGE "$(MUI_${MUI_PAGE_UNINSTALLER_PREFIX}TEXT_${MUI_PAGE_UNINSTALLER_PREFIX}INSTALLING_TITLE)" "$(UMUI_TEXT_FILEDISKREQUEST_FILE_SUBTITLE_BEGIN) ${UMUI_FILEDISKREQUESTPAGE_FILE_NAME} $(UMUI_TEXT_FILEDISKREQUEST_FILE_SUBTITLE_END)"
    !else
      !insertmacro MUI_HEADER_TEXT_PAGE "$(MUI_${MUI_PAGE_UNINSTALLER_PREFIX}TEXT_${MUI_PAGE_UNINSTALLER_PREFIX}INSTALLING_TITLE)" "$(UMUI_TEXT_FILEDISKREQUEST_DISK_SUBTITLE)"
    !endif

    !insertmacro UMUI_FIX_BUTTONS_SKIN

  FunctionEnd

  Function "${SHOW}"

    !insertmacro UMUI_UMUI_HIDEBACKBUTTON

    !insertmacro UMUI_PAGEBGTRANSPARENT_INIT
    !insertmacro UMUI_PAGECTLTRANSPARENT_INIT 1001
    !insertmacro UMUI_PAGECTLTRANSPARENT_INIT 1008
    !insertmacro UMUI_PAGECTLTRANSPARENT_INIT 1006
    !insertmacro UMUI_PAGECTLLIGHT_INIT 1020

    FindWindow $MUI_HWND "#32770" "" $HWNDPARENT
    GetDlgItem $MUI_TEMP1 $MUI_HWND 1023
    ShowWindow $MUI_TEMP1 ${SW_HIDE}
    GetDlgItem $MUI_TEMP1 $MUI_HWND 1024
    ShowWindow $MUI_TEMP1 ${SW_HIDE}

    !insertmacro MUI_PAGE_FUNCTION_CUSTOM SHOW

  FunctionEnd

  Function "${LEAVE}"

    !insertmacro UMUI_IF_INSTALLFLAG_ISNOT ${UMUI_CANCELLED}

      ClearErrors
      IfFileExists "$${UMUI_FILEDISKREQUESTPAGE_VARIABLE}\${UMUI_FILEDISKREQUESTPAGE_FILE_NAME}" file_found 0
        ClearErrors

        ;Repost this page
        Abort

      file_found:

      !insertmacro MUI_PAGE_FUNCTION_CUSTOM LEAVE

    !insertmacro UMUI_ENDIF_INSTALLFLAG

  FunctionEnd

!macroend



;--------------------------------
;INSTALL OPTIONS (CUSTOM PAGES)

!macro MUI_INSTALLOPTIONS_EXTRACT FILE

  !verbose push
  !verbose ${MUI_VERBOSE}

  !insertmacro INSTALLOPTIONS_EXTRACT "${FILE}"

  !verbose pop

!macroend

!macro MUI_INSTALLOPTIONS_EXTRACT_AS FILE FILENAME

  !verbose push
  !verbose ${MUI_VERBOSE}

  !insertmacro INSTALLOPTIONS_EXTRACT_AS "${FILE}" "${FILENAME}"

  !verbose pop

!macroend

!macro MUI_INSTALLOPTIONS_DISPLAY FILE

  !verbose push
  !verbose ${MUI_VERBOSE}

  !insertmacro INSTALLOPTIONS_DISPLAY "${FILE}"

  !verbose pop

!macroend

!macro MUI_INSTALLOPTIONS_DISPLAY_RETURN FILE

  !verbose push
  !verbose ${MUI_VERBOSE}

  !insertmacro INSTALLOPTIONS_DISPLAY_RETURN "${FILE}"

  !verbose pop

!macroend

!macro MUI_INSTALLOPTIONS_INITDIALOG FILE

  !verbose push
  !verbose ${MUI_VERBOSE}

  !insertmacro INSTALLOPTIONS_INITDIALOG "${FILE}"

  !verbose pop

!macroend

!macro MUI_INSTALLOPTIONS_SHOW

  !verbose push
  !verbose ${MUI_VERBOSE}

  !insertmacro INSTALLOPTIONS_SHOW

  !verbose pop

!macroend

!macro MUI_INSTALLOPTIONS_SHOW_RETURN

  !verbose push
  !verbose ${MUI_VERBOSE}

  !insertmacro INSTALLOPTIONS_SHOW_RETURN

  !verbose pop

!macroend

!macro MUI_INSTALLOPTIONS_READ VAR FILE SECTION KEY

  !verbose push
  !verbose ${MUI_VERBOSE}

  !insertmacro INSTALLOPTIONS_READ "${VAR}" "${FILE}" "${SECTION}" "${KEY}"

  !verbose pop

!macroend

!macro MUI_INSTALLOPTIONS_WRITE FILE SECTION KEY VALUE

  !verbose push
  !verbose ${MUI_VERBOSE}

  !insertmacro INSTALLOPTIONS_WRITE "${FILE}" "${SECTION}" "${KEY}" "${VALUE}"

  !verbose pop

!macroend

!macro MUI_INSTALLOPTIONS_WRITE_DEFAULTCONVERT FILE SECTION KEY SYMBOL

  ;Converts default strings from language files to InstallOptions format
  ;Only for use inside MUI

  !verbose push
  !verbose ${MUI_VERBOSE}

  Push $R9

  !ifndef "${SYMBOL}_DEFAULTSET"
    !insertmacro INSTALLOPTIONS_WRITE "${FILE}" "${SECTION}" "${KEY}" "${${SYMBOL}}"
  !else
    Push "${${SYMBOL}}"
    Call ${MUI_PAGE_UNINSTALLER_FUNCPREFIX}Nsis2Io
    Pop $R9
    !insertmacro INSTALLOPTIONS_WRITE "${FILE}" "${SECTION}" "${KEY}" $R9
  !endif

  Pop $R9

  !verbose pop

!macroend


; Additional Installoptions functions
; ------------------------------------

!macro UMUI_INSTALLOPTIONSEX_SETFOCUS HWND

  !verbose push
  !verbose ${MUI_VERBOSE}

  !ifdef UMUI_USE_INSTALLOPTIONSEX
    InstallOptionsEx::setFocus ${HWND}
  !else
    !warning "setFocus is not available with InstallOptions, use InstallOptionsEx instead."
  !endif

  !verbose pop

!macroend

!macro UMUI_INSTALLOPTIONSEX_SKIPVALIDATION

  !verbose push
  !verbose ${MUI_VERBOSE}

  !ifdef UMUI_USE_INSTALLOPTIONSEX
    InstallOptionsEx::skipValidation
  !else
    !warning "skipValidation is not available with InstallOptions, use InstallOptionsEx instead."
  !endif

  !verbose pop

!macroend


; Convert an IO ini into a compatible IOEx ini
!macro UMUI_INSTALLOPTIONSEX_CONVERT FILE

  !ifdef UMUI_USE_INSTALLOPTIONSEX
    !ifndef UMUI_DONT_USE_IOEX_CONVERTER

      !verbose push
      !verbose ${MUI_VERBOSE}

      Push $R0
      Push $0
      Push $1
      Push $8
      Push $R1
      Push $R8

      !insertmacro MUI_INSTALLOPTIONS_READ $R0 "${FILE}" "Settings" "NumFields"

      ;$R0 NumField
      ;$1 NewNumField
      ;$R1 type
      ;$0  counter
      ;$R8 temp string
      ;$8 temp var

      StrCpy $0 0
      StrCpy $1 $R0

      ;do
      loopConvert:
        IntOp $0 $0 + 1

        !insertmacro MUI_INSTALLOPTIONS_READ $R1 "${FILE}" "Field $0" "Type"

        ;if Button
        StrCmp $R1 "Button" isButtonType 0
        ;else if Link
        StrCmp $R1 "Link" isButtonType 0
        ;else if CheckBox
        StrCmp $R1 "CheckBox" isButtonType 0
        ;else if RadioButton
        StrCmp $R1 "RadioButton" 0 isNotButtonType
        isButtonType:
          !insertmacro UMUI_INSTALLOPTIONSEX_CONVERT_NOTIFY "${FILE}" "$0" ONCLICK
          Goto testConvert
        isNotButtonType:

        ;else if ListBox
        StrCmp $R1 "ListBox" +2 0
        ;else if DropList
        StrCmp $R1 "DropList" 0 isNotListType
          !insertmacro UMUI_INSTALLOPTIONSEX_CONVERT_NOTIFY "${FILE}" "$0" ONSELCHANGE
          Goto testConvert
        isNotListType:

        ;else if FileRequest
        StrCmp $R1 "FileRequest" 0 isNotFileRequest
          !insertmacro MUI_INSTALLOPTIONS_WRITE "${FILE}" "Field $0" "Type" "Text"
          IntOp $1 $1 + 1
          !insertmacro MUI_INSTALLOPTIONS_WRITE "${FILE}" "Settings" "NumFields" "$1"

          !insertmacro MUI_INSTALLOPTIONS_WRITE "${FILE}" "Field $1" "Type" "Button"
          !insertmacro MUI_INSTALLOPTIONS_WRITE "${FILE}" "Field $1" "Text" "..."
          !insertmacro MUI_INSTALLOPTIONS_WRITE "${FILE}" "Field $1" "RefFields" "$0"

          !insertmacro MUI_INSTALLOPTIONS_READ $R8 "${FILE}" "Field $0" "Top"
          !insertmacro MUI_INSTALLOPTIONS_WRITE "${FILE}" "Field $1" "Top" "$R8"
          !insertmacro MUI_INSTALLOPTIONS_READ $R8 "${FILE}" "Field $0" "Bottom"
          !insertmacro MUI_INSTALLOPTIONS_WRITE "${FILE}" "Field $1" "Bottom" "$R8"

          !insertmacro MUI_INSTALLOPTIONS_READ $R8 "${FILE}" "Field $0" "Right"
          !insertmacro MUI_INSTALLOPTIONS_WRITE "${FILE}" "Field $1" "Right" "$R8"
          IntOp $R8 $R8 - 19
          !insertmacro MUI_INSTALLOPTIONS_WRITE "${FILE}" "Field $0" "Right" "$R8"
          IntOp $R8 $R8 + 3
          !insertmacro MUI_INSTALLOPTIONS_WRITE "${FILE}" "Field $1" "Left" "$R8"

          !insertmacro MUI_INSTALLOPTIONS_READ $R8 "${FILE}" "Field $0" "Filter"
          !insertmacro MUI_INSTALLOPTIONS_WRITE "${FILE}" "Field $1" "Filter" "$R8"
          !insertmacro MUI_INSTALLOPTIONS_WRITE "${FILE}" "Field $0" "Filter" ""

          !insertmacro MUI_INSTALLOPTIONS_READ $R8 "${FILE}" "Field $0" "Flags"
          !insertmacro UMUI_STRCOUNT "REQ_SAVE" "$R8"
          Pop $8 ;the return number
          !insertmacro MUI_INSTALLOPTIONS_READ $R8 "${FILE}" "Field $0" "Flags"
          StrCmp $8 0 0 save
            !insertmacro MUI_INSTALLOPTIONS_WRITE "${FILE}" "Field $1" "Flags" "OPEN_FILEREQUEST|$R8"
            Goto end
          save:
            !insertmacro MUI_INSTALLOPTIONS_WRITE "${FILE}" "Field $1" "Flags" "SAVE_FILEREQUEST|$R8"
          end:
          !insertmacro MUI_INSTALLOPTIONS_WRITE "${FILE}" "Field $0" "Flags" ""

          Goto testConvert
        isNotFileRequest:

        ;else if DirRequest
        StrCmp $R1 "DirRequest" 0 isNotDirRequest
          !insertmacro MUI_INSTALLOPTIONS_WRITE "${FILE}" "Field $0" "Type" "Text"
          IntOp $1 $1 + 1
          !insertmacro MUI_INSTALLOPTIONS_WRITE "${FILE}" "Settings" "NumFields" "$1"

          !insertmacro MUI_INSTALLOPTIONS_WRITE "${FILE}" "Field $1" "Type" "Button"
          !insertmacro MUI_INSTALLOPTIONS_WRITE "${FILE}" "Field $1" "Text" "..."
          !insertmacro MUI_INSTALLOPTIONS_WRITE "${FILE}" "Field $1" "RefFields" "$0"

          !insertmacro MUI_INSTALLOPTIONS_READ $R8 "${FILE}" "Field $0" "Text"
          !insertmacro MUI_INSTALLOPTIONS_WRITE "${FILE}" "Field $1" "ListItems" "$R8"
          !insertmacro MUI_INSTALLOPTIONS_WRITE "${FILE}" "Field $0" "Text" ""

          !insertmacro MUI_INSTALLOPTIONS_READ $R8 "${FILE}" "Field $0" "Top"
          !insertmacro MUI_INSTALLOPTIONS_WRITE "${FILE}" "Field $1" "Top" "$R8"
          !insertmacro MUI_INSTALLOPTIONS_READ $R8 "${FILE}" "Field $0" "Bottom"
          !insertmacro MUI_INSTALLOPTIONS_WRITE "${FILE}" "Field $1" "Bottom" "$R8"

          !insertmacro MUI_INSTALLOPTIONS_READ $R8 "${FILE}" "Field $0" "Right"
          !insertmacro MUI_INSTALLOPTIONS_WRITE "${FILE}" "Field $1" "Right" "$R8"
          IntOp $R8 $R8 - 19
          !insertmacro MUI_INSTALLOPTIONS_WRITE "${FILE}" "Field $0" "Right" "$R8"
          IntOp $R8 $R8 + 3
          !insertmacro MUI_INSTALLOPTIONS_WRITE "${FILE}" "Field $1" "Left" "$R8"

          !insertmacro MUI_INSTALLOPTIONS_READ $R8 "${FILE}" "Field $0" "Root"
          !insertmacro MUI_INSTALLOPTIONS_WRITE "${FILE}" "Field $1" "Root" "$R8"

          !insertmacro MUI_INSTALLOPTIONS_WRITE "${FILE}" "Field $1" "Flags" "DIRREQUEST"

          Goto testConvert
        isNotDirRequest:

        ;endif

      testConvert:
      ;while $0 <= $R0
      IntCmp $0 $R0 0 loopConvert 0

      Pop $R8
      Pop $R1
      Pop $8
      Pop $1
      Pop $0
      Pop $R0

      !verbose pop

    !endif
  !endif

!macroend


; Convert an IO ini into a compatible IOEx ini next and finish
!macro UMUI_INSTALLOPTIONSEX_CONVERT_NEXT FILE

  !ifdef UMUI_USE_INSTALLOPTIONSEX
    !ifndef UMUI_DONT_USE_IOEX_CONVERTER

      !verbose push
      !verbose ${MUI_VERBOSE}

      Push $R0
      Push $0
      Push $8
      Push $R1
      Push $R8

      !insertmacro MUI_INSTALLOPTIONS_READ $R0 "${FILE}" "Settings" "NumFields"

      ;$R0 NumField
      ;$R1 type
      ;$0  counter
      ;$R8 temp string
      ;$8 temp var

      StrCpy $0 0

      ;do
      loopConvertNext:
        IntOp $0 $0 + 1

        !insertmacro MUI_INSTALLOPTIONS_READ $R1 "${FILE}" "Field $0" "Type"
        ;if Button
        StrCmp $R1 "Button" 0 testConvertNext

          !insertmacro MUI_INSTALLOPTIONS_READ $8 "${FILE}" "Field $0" "RefFields"
          StrCmp $8 "" testConvertNext 0
            !insertmacro MUI_INSTALLOPTIONS_READ $R8 "${FILE}" "Field $0" "HWND"
            !insertmacro MUI_INSTALLOPTIONS_WRITE "${FILE}" "Field $8" "HWND2" "$R8"

      testConvertNext:
      ;while $0 <= $R0
      IntCmp $0 $R0 0 loopConvertNext 0

      Pop $R8
      Pop $R1
      Pop $8
      Pop $0
      Pop $R0

      !verbose pop

    !endif
  !endif

!macroend

; Convert an IO NOTIFY flag into a Notify key compatible with IOEx
!macro UMUI_INSTALLOPTIONSEX_CONVERT_NOTIFY FILE FIELD NOTIFY

  Push $R9
  Push $9

  !define UMUI_UNIQUEID_CONVERTNOTIFY ${__LINE__}

  !insertmacro MUI_INSTALLOPTIONS_READ $R9 "${FILE}" "Field ${FIELD}" "Notify"
  StrCmp $R9 "" 0 end${UMUI_UNIQUEID_CONVERTNOTIFY}

    !insertmacro MUI_INSTALLOPTIONS_READ $R9 "${FILE}" "Field ${FIELD}" "Flags"
    StrCmp $R9 "" end${UMUI_UNIQUEID_CONVERTNOTIFY} 0
      !insertmacro UMUI_STRCOUNT "NOTIFY" "$R9"
      Pop $9 ;the return number
      StrCmp $9 0 end${UMUI_UNIQUEID_CONVERTNOTIFY} 0

        !insertmacro MUI_INSTALLOPTIONS_WRITE "${FILE}" "Field ${FIELD}" "Notify" "${NOTIFY}"

  end${UMUI_UNIQUEID_CONVERTNOTIFY}:

  !undef UMUI_UNIQUEID_CONVERTNOTIFY

  Pop $9
  Pop $R9

!macroend



;--------------------------------
;RESERVE FILES

!macro MUI_RESERVEFILE_INSTALLOPTIONS

  !verbose push
  !verbose ${MUI_VERBOSE}

  !ifdef UMUI_USE_INSTALLOPTIONSEX
    ReserveFile /plugin InstallOptionsEx.dll
  !else
    ReserveFile /plugin InstallOptions.dll
  !endif

  !verbose pop

!macroend

!macro UMUI_RESERVEFILE_SKINNEDCONTROLS

  !verbose push
  !verbose ${MUI_VERBOSE}

  ReserveFile /plugin SkinnedControls.dll

  !verbose pop

!macroend

!macro MUI_RESERVEFILE_LANGDLL

  !verbose push
  !verbose ${MUI_VERBOSE}

  !ifdef UMUI_MULTILANGUAGEPAGE | UMUI_UNMULTILANGUAGEPAGE
    !warning "You tried to reserve the file LangDLL.dll whereas you have also inserted the UNMULTILANGUAGE page. You can remove the MUI_RESERVEFILE_LANGDLL macro insertion."
  !endif

  ReserveFile /plugin LangDLL.dll

  !verbose pop

!macroend



;--------------------------------
;LANGUAGES

!macro MUI_LANGUAGE NLFID

  ;Include a language

  !verbose push
  !verbose ${MUI_VERBOSE}

  ; MUI_PAGE_UNINSTALLER_PREFIX is undefined by uninstaller pages so we check MUI_UNINSTALLER as well
  !ifndef MUI_PAGE_UNINSTALLER_PREFIX && MUI_UNINSTALLER
    !ifndef MUI_DISABLE_INSERT_LANGUAGE_AFTER_PAGES_WARNING ; Define this to avoid the warning if you only have custom pages
      !warning "MUI_LANGUAGE should be inserted after the MUI_[UN]PAGE_* macros"
    !endif
  !endif

  !insertmacro MUI_INSERT

  LoadLanguageFile "${NSISDIR}\Contrib\Language files\${NLFID}.nlf"

  ;Include language file
  !insertmacro LANGFILE_INCLUDE_WITHDEFAULT \
    "${NSISDIR}\Contrib\Language files\${NLFID}.nsh" "${NSISDIR}\Contrib\Language files\English.nsh" "${NSISDIR}\Contrib\UltraModernUI\Language files\${NLFID}.nsh" "${NSISDIR}\Contrib\UltraModernUI\Language files\English.nsh"

  ;Add language to list of languages for selection dialog
  !define /ifndef MUI_LANGDLL_LANGUAGES ""
  !define /redef MUI_LANGDLL_LANGUAGES \
    `"${LANGFILE_${NLFID}_LANGDLL}" "${LANG_${NLFID}}" ${MUI_LANGDLL_LANGUAGES}`
  !define /ifndef MUI_LANGDLL_LANGUAGES_CP ""
  !define /redef MUI_LANGDLL_LANGUAGES_CP \
    `"${LANGFILE_${NLFID}_LANGDLL}" "${LANG_${NLFID}}" "${LANG_${NLFID}_CP}" ${MUI_LANGDLL_LANGUAGES_CP}`

  !define /ifndef UMUI_MULTILANG_LANGMAP ""
  !define /redef UMUI_MULTILANG_LANGMAP "${UMUI_MULTILANG_LANGMAP} /key=${LANG_${NLFID}} `${LANGFILE_${NLFID}_NAME}`"

  !verbose pop

!macroend

!macro UMUI_MULTILANG_GET

  !verbose push
  !verbose ${MUI_VERBOSE}

  ;Usually, this is done only later, but we need us now
  InitPluginsDir

  ;get parameters in a ini file
  !insertmacro UMUI_PARAMETERS_TO_INI
  StrCpy $UMUI_INSTALLFLAG 0

  ;bu default, $LANGUAGE contain the ID of the language of the system

  ; get the choosen langid if it is passed in the commandline
  !insertmacro UMUI_GETPARAMETERVALUE "/L" "error"
  Pop $MUI_TEMP1

  StrCmp $MUI_TEMP1 "error" checkRegistery 0
    !insertmacro UMUI_SET_INSTALLFLAG ${UMUI_LANGISSET}
    Goto setlang

  checkRegistery:

    !ifdef UMUI_LANGUAGE_REGISTRY_VALUENAME
      ReadRegStr $MUI_TEMP1 ${UMUI_LANGUAGE_REGISTRY_ROOT} "${UMUI_LANGUAGE_REGISTRY_KEY}" "${UMUI_LANGUAGE_REGISTRY_VALUENAME}"
      StrCmp $MUI_TEMP1 "" 0 setlang
    !endif
    Goto endlang

  setlang:

    StrCpy $LANGUAGE $MUI_TEMP1

    !ifndef UMUI_LANGUAGE_ALWAYSSHOW
        !insertmacro UMUI_SET_INSTALLFLAG ${UMUI_LANGISSET}
    !endif

  endlang:

  !ifdef UMUI_LANGUAGE_REGISTRY_VALUENAME
    !insertmacro UMUI_ADDPARAMTOSAVETOREGISTRYKEY ${UMUI_LANGUAGE_REGISTRY_ROOT} "${UMUI_LANGUAGE_REGISTRY_KEY}" "${UMUI_LANGUAGE_REGISTRY_VALUENAME}" "$LANGUAGE"
  !endif

  !ifndef UMUI_VAR_LANGLIST
    !error "It seem that you don't have inserted the MULTILANGUAGE page."
  !endif

  !ifndef UMUI_MULTILANG_LANGMAP
    !error "MUI_LANGUAGE must be inserted before UMUI_MULTILANG_GET"
  !endif

  ClearErrors

  ; create a map that contain the langid => langstring
  nsArray::SetList LangMap ${UMUI_MULTILANG_LANGMAP} /end

  nsArray::Sort LangMap 4

  nsArray::Join LangMap "|"
  Pop $UMUI_LANGLIST

  ClearErrors

  !verbose pop

!macroend


;--------------------------------
;LANGUAGE SELECTION DIALOG

!macro MUI_LANGDLL_DISPLAY

  !verbose push
  !verbose ${MUI_VERBOSE}

  !ifdef UMUI_MULTILANGUAGEPAGE | UMUI_UNMULTILANGUAGEPAGE
    !warning "You have used the MUI_LANGDLL_DISPLAY in your .onInit function whereas you have also inserted the MULTILANGUAGE page. Replace the MUI_LANGDLL_DISPLAY and the MUI_UNGETLANGUAGE macros by the UMUI_MULTILANG_GET macro in your .onInit and un.onInit functions otherwise, the MULTILANGUAGE page will not work."
  !endif

  !ifdef MUI_LANGDLL_REGISTRY_ROOT | MUI_LANGDLL_REGISTRY_KEY | MUI_LANGDLL_REGISTRY_VALUENAME
    !warning "Deprecated: The MUI_LANGDLL_REGISTRY_ROOT, MUI_LANGDLL_REGISTRY_KEY and MUI_LANGDLL_REGISTRY_VALUENAME defines were replaced by UMUI_LANGUAGE_REGISTRY_VALUENAME, UMUI_LANGUAGE_REGISTRY_ROOT, UMUI_LANGUAGE_REGISTRY_KEY or you can use also the UMUI_PARAMS_REGISTRY_ROOT & UMUI_PARAMS_REGISTRY_KEY globals parameters."
  !endif

  !ifndef UMUI_LANGUAGE_REGISTRY_VALUENAME
    !ifdef MUI_LANGDLL_REGISTRY_VALUENAME
      !define UMUI_LANGUAGE_REGISTRY_VALUENAME "${MUI_LANGDLL_REGISTRY_VALUENAME}"
    !endif
  !endif

  !ifdef UMUI_LANGUAGE_REGISTRY_VALUENAME

    !ifndef UMUI_LANGUAGE_REGISTRY_ROOT
      !ifdef UMUI_PARAMS_REGISTRY_ROOT
        !define UMUI_LANGUAGE_REGISTRY_ROOT "${UMUI_PARAMS_REGISTRY_ROOT}"
      !else ifdef MUI_LANGDLL_REGISTRY_ROOT
        !define UMUI_LANGUAGE_REGISTRY_ROOT "${MUI_LANGDLL_REGISTRY_ROOT}"
      !else
        !error "For UMUI_LANGUAGE_REGISTRY_VALUENAME, the UMUI_LANGUAGE_REGISTRY_ROOT & UMUI_LANGUAGE_REGISTRY_KEY parameters or else the UMUI_PARAMS_REGISTRY_ROOT & UMUI_PARAMS_REGISTRY_KEY global parameters must be defined."
      !endif
    !endif
    !ifndef UMUI_LANGUAGE_REGISTRY_KEY
      !ifdef UMUI_PARAMS_REGISTRY_KEY
        !define UMUI_LANGUAGE_REGISTRY_KEY "${UMUI_PARAMS_REGISTRY_KEY}"
      !else ifdef MUI_LANGDLL_REGISTRY_KEY
        !define UMUI_LANGUAGE_REGISTRY_KEY "${MUI_LANGDLL_REGISTRY_KEY}"
      !else
        !error "For UMUI_LANGUAGE_REGISTRY_VALUENAME, the UMUI_LANGUAGE_REGISTRY_ROOT & UMUI_LANGUAGE_REGISTRY_KEY parameters or else the UMUI_PARAMS_REGISTRY_ROOT & UMUI_PARAMS_REGISTRY_KEY global parameters must be defined."
      !endif
    !endif

  !endif

  !define /IfNDef MUI_LANGDLL_WINDOWTITLE "Installer Language"
  !define /IfNDef MUI_LANGDLL_INFO "Please select a language."

  !ifdef UMUI_LANGUAGE_REGISTRY_VALUENAME

    ReadRegStr $MUI_TEMP1 ${UMUI_LANGUAGE_REGISTRY_ROOT} "${UMUI_LANGUAGE_REGISTRY_KEY}" "${UMUI_LANGUAGE_REGISTRY_VALUENAME}"
    StrCmp $MUI_TEMP1 "" mui.langdll_show
      StrCpy $LANGUAGE $MUI_TEMP1
      !ifndef UMUI_LANGUAGE_ALWAYSSHOW
        Goto mui.langdll_done
      !endif
    mui.langdll_show:

  !endif

  !ifdef NSIS_CONFIG_SILENT_SUPPORT
    IfSilent mui.langdll_done
  !endif

  !ifdef MUI_LANGDLL_ALLLANGUAGES | UMUI_MULTILANGUAGEPAGE | UMUI_UNMULTILANGUAGEPAGE
    LangDLL::LangDialog "${MUI_LANGDLL_WINDOWTITLE}" "${MUI_LANGDLL_INFO}" A ${MUI_LANGDLL_LANGUAGES} ""
  !else
    LangDLL::LangDialog "${MUI_LANGDLL_WINDOWTITLE}" "${MUI_LANGDLL_INFO}" AC ${MUI_LANGDLL_LANGUAGES_CP} ""
  !endif

  Pop $LANGUAGE
  StrCmp $LANGUAGE "cancel" 0 +2
    Abort

  !ifdef UMUI_LANGUAGE_REGISTRY_VALUENAME
    !insertmacro UMUI_ADDPARAMTOSAVETOREGISTRYKEY ${UMUI_LANGUAGE_REGISTRY_ROOT} "${UMUI_LANGUAGE_REGISTRY_KEY}" "${UMUI_LANGUAGE_REGISTRY_VALUENAME}" "$LANGUAGE"
  !endif

  !ifdef NSIS_CONFIG_SILENT_SUPPORT | UMUI_LANGUAGE_REGISTRY_VALUENAME
    mui.langdll_done:
  !endif

  !verbose pop

!macroend

!macro MUI_UNGETLANGUAGE

  !verbose push
  !verbose ${MUI_VERBOSE}

  !ifdef UMUI_UNMULTILANGUAGEPAGE
    !warning "You have used the MUI_UNGETLANGUAGE in your un.onInit function whereas you have also inserted the UNMULTILANGUAGE page. Replace the MUI_LANGDLL_DISPLAY and the MUI_UNGETLANGUAGE macros by the UMUI_MULTILANG_GET macro in your .onInit and un.onInit functions otherwise, the MULTILANGUAGE page will not work."
  !endif

  !ifdef MUI_LANGDLL_REGISTRY_ROOT | MUI_LANGDLL_REGISTRY_KEY | MUI_LANGDLL_REGISTRY_VALUENAME
    !warning "Deprecated: The MUI_LANGDLL_REGISTRY_ROOT, MUI_LANGDLL_REGISTRY_KEY and MUI_LANGDLL_REGISTRY_VALUENAME defines were replaced by UMUI_LANGUAGE_REGISTRY_ROOT, UMUI_LANGUAGE_REGISTRY_KEY and UMUI_LANGUAGE_REGISTRY_VALUENAME or you can use also the UMUI_PARAMS_REGISTRY_ROOT and UMUI_PARAMS_REGISTRY_KEY globals parameters."
  !endif

  !ifndef UMUI_LANGUAGE_REGISTRY_VALUENAME
    !ifdef MUI_LANGDLL_REGISTRY_VALUENAME
      !define UMUI_LANGUAGE_REGISTRY_VALUENAME "${MUI_LANGDLL_REGISTRY_VALUENAME}"
    !endif
  !endif

  !ifdef UMUI_LANGUAGE_REGISTRY_VALUENAME

    !ifndef UMUI_LANGUAGE_REGISTRY_ROOT
      !ifdef UMUI_PARAMS_REGISTRY_ROOT
        !define UMUI_LANGUAGE_REGISTRY_ROOT "${UMUI_PARAMS_REGISTRY_ROOT}"
      !else ifdef MUI_LANGDLL_REGISTRY_ROOT
        !define UMUI_LANGUAGE_REGISTRY_ROOT "${MUI_LANGDLL_REGISTRY_ROOT}"
      !else
        !error "For UMUI_LANGUAGE_REGISTRY_VALUENAME, the UMUI_LANGUAGE_REGISTRY_ROOT & UMUI_LANGUAGE_REGISTRY_KEY parameters or else the UMUI_PARAMS_REGISTRY_ROOT & UMUI_PARAMS_REGISTRY_KEY global parameters must be defined."
      !endif
    !endif
    !ifndef UMUI_LANGUAGE_REGISTRY_KEY
      !ifdef UMUI_PARAMS_REGISTRY_KEY
        !define UMUI_LANGUAGE_REGISTRY_KEY "${UMUI_PARAMS_REGISTRY_KEY}"
      !else ifdef MUI_LANGDLL_REGISTRY_KEY
        !define UMUI_LANGUAGE_REGISTRY_KEY "${MUI_LANGDLL_REGISTRY_KEY}"
      !else
        !error "For UMUI_LANGUAGE_REGISTRY_VALUENAME, the UMUI_LANGUAGE_REGISTRY_ROOT & UMUI_LANGUAGE_REGISTRY_KEY parameters or else the UMUI_PARAMS_REGISTRY_ROOT & UMUI_PARAMS_REGISTRY_KEY global parameters must be defined."
      !endif
    !endif

    ReadRegStr $MUI_TEMP1 ${UMUI_LANGUAGE_REGISTRY_ROOT} "${UMUI_LANGUAGE_REGISTRY_KEY}" "${UMUI_LANGUAGE_REGISTRY_VALUENAME}"
    StrCmp $MUI_TEMP1 "" 0 mui.ungetlanguage_setlang

  !endif

  !insertmacro MUI_LANGDLL_DISPLAY

  !ifdef UMUI_LANGUAGE_REGISTRY_VALUENAME

    Goto mui.ungetlanguage_done

    mui.ungetlanguage_setlang:
      StrCpy $LANGUAGE $MUI_TEMP1

    mui.ungetlanguage_done:

  !endif

  !verbose pop

!macroend

;--------------------------------

/*

LangFile.nsh

Header file to create language files that can be
included with a single command.

Copyright 2008-2016 Joost Verburg, Anders Kjersem

* Either LANGFILE_INCLUDE or LANGFILE_INCLUDE_WITHDEFAULT
  can be called from the script to include a language file.

  - LANGFILE_INCLUDE takes the language file name as parameter.
  - LANGFILE_INCLUDE_WITHDEFAULT takes as additional second
    parameter, the default language file to load missing strings from.

* Language strings in the language file have the format:
  ${LangFileString} LANGSTRING_NAME "Text"

* There are two types of language header files:

  - NSIS multi-lang support; these must start with the LANGFILE macro and
    provide strings for features like MUI and MultiUser. If you are adding
    support for a new language to NSIS you should make a copy of English.nsh
    and translate this .nsh along with the .nlf.
  - Custom installer strings; these must start with the LANGFILE_EXT macro and
    contain translated versions of
    custom strings used in a particular installer.
    This is useful if you want to put the translations for each language in
    their own separate file.

* Example:

  ; Setup.nsi
  !include "MUI.nsh"
  !insertmacro MUI_PAGE_INSTFILES
  !insertmacro MUI_LANGUAGE "Danish"
  !insertmacro LANGFILE_INCLUDE "DanishExtra.nsh"
  !insertmacro MUI_LANGUAGE "Swedish"
  !insertmacro LANGFILE_INCLUDE "SwedishExtra.nsh"
  Section
  MessageBox MB_OK "$(myCustomString)"
  SectionEnd

  ; SwedishExtra.nsh
  !insertmacro LANGFILE_EXT Swedish
  ${LangFileString} myCustomString "Bork bork"

*/

!ifndef LANGFILE_INCLUDED
!define LANGFILE_INCLUDED

!macro LANGFILE_INCLUDE FILENAME UMUI_FILENAME

  ;Called from script: include a langauge file

  !define /redef LangFileString "!insertmacro LANGFILE_SETSTRING"

  !define LANGFILE_SETNAMES
  !include "${FILENAME}"
  !include "${UMUI_FILENAME}"
  !undef LANGFILE_SETNAMES

  ;Create language strings
  !define /redef LangFileString "!insertmacro LANGFILE_LANGSTRING"
  !include "${FILENAME}"
  !include "${UMUI_FILENAME}"

!macroend

!macro LANGFILE_INCLUDE_WITHDEFAULT FILENAME FILENAME_DEFAULT UMUI_FILENAME UMUI_FILENAME_DEFAULT

  ;Called from script: include a langauge file
  ;Obtains missing strings from a default file

  !define /redef LangFileString "!insertmacro LANGFILE_SETSTRING"

  !define LANGFILE_SETNAMES
  !include "${FILENAME}"
  !include "${UMUI_FILENAME}"
  !undef LANGFILE_SETNAMES

  ;Include default language for missing strings
  !define LANGFILE_PRIV_INCLUDEISFALLBACK "${FILENAME_DEFAULT}"
  !include "${FILENAME_DEFAULT}"
  !undef LANGFILE_PRIV_INCLUDEISFALLBACK
  !include "${UMUI_FILENAME_DEFAULT}"

  ;Create language strings
  !define /redef LangFileString "!insertmacro LANGFILE_LANGSTRING"
  !include "${FILENAME_DEFAULT}"
  !include "${UMUI_FILENAME_DEFAULT}"

!macroend

!macro LANGFILE NLFID ENGNAME NATIVENAME NATIVEASCIINAME

  ;Start of standard NSIS language file

  ; NLFID: Must match the name of the .nlf file
  ; ENGNAME: English name of language, "=" if it is the same as NLFID
  ; NATIVENAME: Native name of language. (In Unicode)
  ; NATIVEASCIINAME: Native name of language using only ASCII, "=" if it is the same as NATIVENAME

  ; Example: LANGFILE "Swedish" = "Svenska" =
  ; For more examples, see French.nsh, Greek.nsh and PortugueseBR.nsh

  !ifdef LANGFILE_SETNAMES

    !ifdef LANGFILE_IDNAME
      !undef LANGFILE_IDNAME
    !endif

    !define LANGFILE_IDNAME "${NLFID}"

    ; ModernUI or the .nsi can change LANGFILE_LANGDLL_FMT if desired
    !ifndef LANGFILE_LANGDLL_FMT
      !ifndef NSIS_UNICODE
        !define LANGFILE_LANGDLL_FMT "%ENGNAME% / %NATIVEASCIINAME%"
      !endif
      !define /ifndef LANGFILE_LANGDLL_FMT "%NATIVENAME%"
    !endif

    !ifndef "LANGFILE_${NLFID}_NAME"
      !if "${ENGNAME}" == "="
        !define /redef ENGNAME "${NLFID}"
      !endif
      !if "${NATIVEASCIINAME}" == "="
        !define /redef NATIVEASCIINAME "${NATIVENAME}"
      !endif

      !define "LANGFILE_${NLFID}_ENGLISHNAME" "${ENGNAME}"
      !ifdef NSIS_UNICODE
        !define "LANGFILE_${NLFID}_NAME" "${NATIVENAME}"
      !else
        !define "LANGFILE_${NLFID}_NAME" "${NATIVEASCIINAME}"
      !endif

      !searchreplace LANGFILE_${NLFID}_LANGDLL "${LANGFILE_LANGDLL_FMT}" %NATIVEASCIINAME% "${NATIVEASCIINAME}"
      !searchreplace LANGFILE_${NLFID}_LANGDLL "${LANGFILE_${NLFID}_LANGDLL}" %NATIVENAME% "${NATIVENAME}"
      !searchreplace LANGFILE_${NLFID}_LANGDLL "${LANGFILE_${NLFID}_LANGDLL}" %ENGNAME% "${ENGNAME}"

    !endif

  !endif

!macroend

!macro LANGFILE_EXT IDNAME

  ;Start of installer language file

  !ifdef LANGFILE_SETNAMES

    !define /redef LANGFILE_IDNAME "${IDNAME}"

  !endif

!macroend

!macro LANGFILE_SETSTRING NAME VALUE

  ;Set define with translated string

  !ifndef ${NAME}
    !define "${NAME}" "${VALUE}"
    !ifdef LANGFILE_PRIV_INCLUDEISFALLBACK
      !warning 'LangString "${NAME}" for language ${LANGFILE_IDNAME} is missing, using fallback from "${LANGFILE_PRIV_INCLUDEISFALLBACK}"'
    !endif
  !endif

!macroend

!macro LANGFILE_LANGSTRING NAME DUMMY

  ;Create a language string from a define and undefine

  LangString "${NAME}" "${LANG_${LANGFILE_IDNAME}}" "${${NAME}}"
  !undef "${NAME}"

!macroend

!endif

;--------------------------------

/*

InstallOptions.nsh
Macros and conversion functions for InstallOptions

*/

!ifndef ___NSIS__INSTALL_OPTIONS__NSH___
!define ___NSIS__INSTALL_OPTIONS__NSH___

!macro INSTALLOPTIONS_FUNCTION_READ_CONVERT
  !insertmacro INSTALLOPTIONS_FUNCTION_IO2NSIS ""
!macroend

!macro INSTALLOPTIONS_UNFUNCTION_READ_CONVERT
  !insertmacro INSTALLOPTIONS_FUNCTION_IO2NSIS un.
!macroend

!macro INSTALLOPTIONS_FUNCTION_WRITE_CONVERT
  !insertmacro INSTALLOPTIONS_FUNCTION_NSIS2IO ""
!macroend

!macro INSTALLOPTIONS_UNFUNCTION_WRITE_CONVERT
  !insertmacro INSTALLOPTIONS_FUNCTION_NSIS2IO un.
!macroend

!macro INSTALLOPTIONS_FUNCTION_NSIS2IO UNINSTALLER_FUNCPREFIX

  ; Convert an NSIS string to a form suitable for use by InstallOptions
  ; Usage:
  ;   Push <NSIS-string>
  ;   Call Nsis2Io
  ;   Pop <IO-string>

  Function ${UNINSTALLER_FUNCPREFIX}Nsis2Io

    Exch $0 ; The source
    Push $1 ; The output
    Push $2 ; Temporary char
    StrCpy $1 "" ; Initialise the output

  loop:
    StrCpy $2 $0 1 ; Get the next source char
    StrCmp $2 "" done ; Abort when none left
      StrCpy $0 $0 "" 1 ; Remove it from the source
      StrCmp $2 "\" "" +3 ; Back-slash?
        StrCpy $1 "$1\\"
        Goto loop
      StrCmp $2 "$\r" "" +3 ; Carriage return?
        StrCpy $1 "$1\r"
        Goto loop
      StrCmp $2 "$\n" "" +3 ; Line feed?
        StrCpy $1 "$1\n"
        Goto loop
      StrCmp $2 "$\t" "" +3 ; Tab?
        StrCpy $1 "$1\t"
        Goto loop
      StrCpy $1 "$1$2" ; Anything else
      Goto loop

  done:
    StrCpy $0 $1
    Pop $2
    Pop $1
    Exch $0

  FunctionEnd

!macroend

!macro INSTALLOPTIONS_FUNCTION_IO2NSIS UNINSTALLER_FUNCPREFIX

  ; Convert an InstallOptions string to a form suitable for use by NSIS
  ; Usage:
  ;   Push <IO-string>
  ;   Call Io2Nsis
  ;   Pop <NSIS-string>

  Function ${UNINSTALLER_FUNCPREFIX}Io2Nsis

    Exch $0 ; The source
    Push $1 ; The output
    Push $2 ; Temporary char
    StrCpy $1 "" ; Initialise the output

  loop:
    StrCpy $2 $0 1 ; Get the next source char
    StrCmp $2 "" done ; Abort when none left
      StrCpy $0 $0 "" 1 ; Remove it from the source
      StrCmp $2 "\" +3 ; Escape character?
        StrCpy $1 "$1$2" ; If not just output
        Goto loop
      StrCpy $2 $0 1 ; Get the next source char
      StrCpy $0 $0 "" 1 ; Remove it from the source
      StrCmp $2 "\" "" +3 ; Back-slash?
        StrCpy $1 "$1\"
        Goto loop
      StrCmp $2 "r" "" +3 ; Carriage return?
        StrCpy $1 "$1$\r"
        Goto loop
      StrCmp $2 "n" "" +3 ; Line feed?
        StrCpy $1 "$1$\n"
        Goto loop
      StrCmp $2 "t" "" +3 ; Tab?
        StrCpy $1 "$1$\t"
        Goto loop
      StrCpy $1 "$1$2" ; Anything else (should never get here)
      Goto loop

  done:
    StrCpy $0 $1
    Pop $2
    Pop $1
    Exch $0

FunctionEnd

!macroend

!macro INSTALLOPTIONS_EXTRACT FILE

  InitPluginsDir
  File "/oname=$PLUGINSDIR\${FILE}" "${FILE}"
  !ifdef NSIS_UNICODE
    !ifdef UMUI_USE_INSTALLOPTIONSEX
      InstallOptionsEx::make_unicode "$PLUGINSDIR\${FILE}"
    !else
      InstallOptions::make_unicode "$PLUGINSDIR\${FILE}"
    !endif
  !endif
  !insertmacro INSTALLOPTIONS_WRITE "${FILE}" "Settings" "RTL" "$(^RTL)"

!macroend

!macro INSTALLOPTIONS_EXTRACT_AS FILE FILENAME

  InitPluginsDir
  File "/oname=$PLUGINSDIR\${FILENAME}" "${FILE}"
  !ifdef NSIS_UNICODE
    !ifdef UMUI_USE_INSTALLOPTIONSEX
      InstallOptionsEx::make_unicode "$PLUGINSDIR\${FILENAME}"
    !else
      InstallOptions::make_unicode "$PLUGINSDIR\${FILENAME}"
    !endif
  !endif
  !insertmacro INSTALLOPTIONS_WRITE "${FILENAME}" "Settings" "RTL" "$(^RTL)"

!macroend

!macro INSTALLOPTIONS_DISPLAY FILE

  !insertmacro MUI_INSTALLOPTIONS_DISPLAY_RETURN ${FILE}
  Exch

!macroend

!macro INSTALLOPTIONS_DISPLAY_RETURN FILE

  ; IF setup cancelled
  !insertmacro UMUI_ABORT_IF_INSTALLFLAG_IS ${UMUI_CANCELLED}

  !define /IfNDef MUI_PAGE_UNINSTALLER_PREFIX ""

  ; we can't use InstallOptions::dialog function with UMUI because the background can not be initialised
  Push $MUI_TEMP1
  Push $MUI_TEMP2
  Push $R0
  Push $0
  Push $1
  Push $R1

  !insertmacro INSTALLOPTIONS_INITDIALOG "${FILE}"
  Pop $MUI_TEMP1

  !insertmacro UMUI_IOPAGEBGTRANSPARENT_INIT $MUI_TEMP1

  !insertmacro INSTALLOPTIONS_READ $R0 "${FILE}" "Settings" "NumFields"

  ;$R0 NumField
  ;$R1 type
  ;$0  counter
  ;$1  counter + 1200

  StrCpy $1 1200
  StrCpy $0 0

  ;do
  loop:
    IntOp $0 $0 + 1

    GetDlgItem $MUI_TEMP2 $MUI_TEMP1 $1

    !insertmacro INSTALLOPTIONS_READ $R1 "${FILE}" "Field $0" "Type"
    ;if text
    StrCmp $R1 "Text" input 0
    ;else if password
    StrCmp $R1 "Password" input 0
    ;else if listbox
    StrCmp $R1 "ListBox" input 0
    ;else if DropList
    StrCmp $R1 "DropList" input 0
    ;else if DateTime
    StrCmp $R1 "DateTime" input 0
    ;else if  ComboBox
    StrCmp $R1 "ComboBox" input 0
    ;else if TreeView
    StrCmp $R1 "TreeView" input 0
    ;else if IPAddress
    StrCmp $R1 "IPAddress" input 0
    ;else if FileRequest
    StrCmp $R1 "FileRequest" +2 0
    ;else if DirRequest
    StrCmp $R1 "DirRequest" 0 notInput
      IntOp $1 $1 + 1

    input:
      !insertmacro UMUI_IOPAGEINPUTCTL_INIT $MUI_TEMP2
      Goto test
    notInput:

!ifndef USE_MUIEx
;----------------
    ;if GroupBox
    StrCmp $R1 "GroupBox" 0 notGroupBox
      !insertmacro UMUI_IOPAGECTLLIGHT_INIT $MUI_TEMP2
      Goto test
    notGroupBox:
    ;else if link
    StrCmp $R1 "Link" 0 notLink
      !insertmacro UMUI_IOPAGECTLLIGHTTRANSPARENT_INIT $MUI_TEMP2
      Goto test
    notLink:

    !if "${UMUI_XPSTYLE}" == "On"
      ;else if CheckBox
      StrCmp $R1 "CheckBox" +2 0
      ;else if RadioButton
      StrCmp $R1 "RadioButton" 0 notCheckBoxRadio
        !insertmacro UMUI_IOPAGECTL_INIT $MUI_TEMP2
        Goto test
      notCheckBoxRadio:
    !endif

    ;else if not Button (label, checkbox, radiobutton...)
    StrCmp $R1 "Button" test 0
      !insertmacro UMUI_IOPAGECTLTRANSPARENT_INIT $MUI_TEMP2

!endif
;-----

  test:
    IntOp $1 $1 + 1
    ;while $0 <= $R0
    IntCmp $0 $R0 0 loop 0

  Pop $R1
  Pop $1
  Pop $0
  Pop $R0
  Pop $MUI_TEMP2
  Exch $MUI_TEMP1

  !insertmacro INSTALLOPTIONS_SHOW_RETURN

!macroend

!macro INSTALLOPTIONS_INITDIALOG FILE

  !ifdef UMUI_USE_INSTALLOPTIONSEX
    !insertmacro UMUI_INSTALLOPTIONSEX_CONVERT "${FILE}"
    InstallOptionsEx::initDialog "$PLUGINSDIR\${FILE}"
    !insertmacro UMUI_INSTALLOPTIONSEX_CONVERT_NEXT "${FILE}"
  !else
    InstallOptions::initDialog "$PLUGINSDIR\${FILE}"
  !endif

  !insertmacro UMUI_UMUI_HIDEBACKBUTTON

!macroend

!macro INSTALLOPTIONS_SHOW

  Push $0

  !ifdef UMUI_USE_INSTALLOPTIONSEX
    InstallOptionsEx::show
  !else
    InstallOptions::show
  !endif
  Pop $0

  Pop $0

!macroend

!macro INSTALLOPTIONS_SHOW_RETURN

  !ifdef UMUI_USE_INSTALLOPTIONSEX
    InstallOptionsEx::show
  !else
    InstallOptions::show
  !endif

!macroend

!macro INSTALLOPTIONS_READ VAR FILE SECTION KEY

  ReadIniStr ${VAR} "$PLUGINSDIR\${FILE}" "${SECTION}" "${KEY}"

!macroend

!macro INSTALLOPTIONS_WRITE FILE SECTION KEY VALUE

  WriteIniStr "$PLUGINSDIR\${FILE}" "${SECTION}" "${KEY}" "${VALUE}"

!macroend

!macro INSTALLOPTIONS_READ_CONVERT VAR FILE SECTION KEY

  ReadIniStr ${VAR} "$PLUGINSDIR\${FILE}" "${SECTION}" "${KEY}"
  Push ${VAR}
  Call Io2Nsis
  Pop ${VAR}

!macroend

!macro INSTALLOPTIONS_READ_UNCONVERT VAR FILE SECTION KEY

  ReadIniStr ${VAR} "$PLUGINSDIR\${FILE}" "${SECTION}" "${KEY}"
  Push ${VAR}
  Call un.Io2Nsis
  Pop ${VAR}

!macroend

!macro INSTALLOPTIONS_WRITE_CONVERT FILE SECTION KEY VALUE

  Push $0
  StrCpy $0 "${VALUE}"
  Push $0
  Call Nsis2Io
  Pop $0

  WriteIniStr "$PLUGINSDIR\${FILE}" "${SECTION}" "${KEY}" $0

  Pop $0

!macroend

!macro INSTALLOPTIONS_WRITE_UNCONVERT FILE SECTION KEY VALUE

  Push $0
  StrCpy $0 "${VALUE}"
  Push $0
  Call un.Nsis2Io
  Pop $0

  WriteIniStr "$PLUGINSDIR\${FILE}" "${SECTION}" "${KEY}" $0

  Pop $0

!macroend

!endif # ___NSIS__INSTALL_OPTIONS__NSH___


;--------------------------------
;END

!verbose pop
!endif