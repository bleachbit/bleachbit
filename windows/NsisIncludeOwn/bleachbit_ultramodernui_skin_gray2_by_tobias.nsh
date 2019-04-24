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

;  @app BleachBit NSIS Installer Script - bleachbit_ultramodernui_skin_gray2_by_tobias.nsh
;  @url https://nsis.sourceforge.io/Main_Page
;  @os Windows
;  @scriptversion v2.3.0.1084
;  @scriptdate 2019-04-24
;  @scriptby Tobias B. Besemer (2019-04-24 - 2019-04-24)
;  @tested ok v2.3.0.1084, Windows 7
;  @testeddate 2019-04-24
;  @testedby https://github.com/Tobias-B-Besemer
;  @note Based on: ${NSISDIR}\Contrib\UltraModernUI\Skins\Gray2.nsh


;--------------------------------
!define /IfNDef MUI_TEXTCOLOR FFFFFF
!define /IfNDef MUI_BGCOLOR 292929
!define /IfNDef UMUI_TEXT_LIGHTCOLOR FFFF00
!define /IfNDef UMUI_HEADERTEXT_COLOR FFFFFF
!define /IfNDef UMUI_BRANDINGTEXTFRONTCOLOR 8e8e8e
!define /IfNDef UMUI_BRANDINGTEXTBACKCOLOR ececec
!define /IfNDef UMUI_DISABLED_BUTTON_TEXT_COLOR 404040
!define /IfNDef UMUI_SELECTED_BUTTON_TEXT_COLOR 808080
!define /IfNDef UMUI_BUTTON_TEXT_COLOR 000000
!define /IfNDef UMUI_LEFTIMAGE_BMP "picture.UMUI\Left_BleachBit_Gray.bmp"
!define /IfNDef UMUI_HEADERBGIMAGE_BMP "picture.UMUI\Header_BleachBit_Gray.bmp"
!define /IfNDef UMUI_BOTTOMIMAGE_BMP "${NSISDIR}\Contrib\UltraModernUI\Skins\gray\Bottom2.bmp"
!define /IfNDef UMUI_BUTTONIMAGE_BMP "${NSISDIR}\Contrib\UltraModernUI\Skins\gray\Button2.bmp"
!define /IfNDef UMUI_PAGEBGIMAGE_BMP ; "${NSISDIR}\Contrib\UltraModernUI\Skins\gray\PageBG2.bmp"
!define /IfNDef UMUI_SCROLLBARIMAGE_BMP "${NSISDIR}\Contrib\UltraModernUI\Skins\gray\ScrollBar.bmp"
!define /IfNDef MUI_WELCOMEFINISHPAGE_BITMAP "${NSISDIR}\Contrib\UltraModernUI\Skins\gray\Wizard.bmp"
!define /IfNDef MUI_ICON "${NSISDIR}\Contrib\Graphics\Icons\orange-install-nsis.ico"
!define /IfNDef MUI_UNICON "${NSISDIR}\Contrib\Graphics\Icons\orange-uninstall-nsis.ico"
!define /IfNDef UMUI_XPSTYLE On
