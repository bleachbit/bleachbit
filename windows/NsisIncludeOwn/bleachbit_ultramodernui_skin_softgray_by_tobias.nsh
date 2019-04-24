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

;  @app BleachBit NSIS Installer Script - bleachbit_ultramodernui_skin_softgray_by_tobias.nsh
;  @url https://nsis.sourceforge.io/Main_Page
;  @os Windows
;  @scriptversion v2.3.0.1059
;  @scriptdate 2019-04-16
;  @scriptby Tobias B. Besemer (2019-04-13 - 2019-04-16)
;  @tested ok v2.3.0.1059, Windows 7
;  @testeddate 2019-04-16
;  @testedby https://github.com/Tobias-B-Besemer
;  @note Based on: ${NSISDIR}\Contrib\UltraModernUI\Skins\SoftGray.nsh


;--------------------------------
!define /IfNDef MUI_TEXTCOLOR 000000
!define /IfNDef MUI_BGCOLOR F9F9F9
!define /IfNDef UMUI_TEXT_LIGHTCOLOR 0000FF
!define /IfNDef UMUI_HEADERTEXT_COLOR 000000
!define /IfNDef UMUI_BRANDINGTEXTFRONTCOLOR 000000
!define /IfNDef UMUI_BRANDINGTEXTBACKCOLOR F9F9F9
!define /IfNDef UMUI_DISABLED_BUTTON_TEXT_COLOR 808080
!define /IfNDef UMUI_SELECTED_BUTTON_TEXT_COLOR 000080
!define /IfNDef UMUI_BUTTON_TEXT_COLOR 000000
!define /IfNDef UMUI_LEFTIMAGE_BMP "picture.UMUI\Left_BleachBit_SoftGray.bmp"
!define /IfNDef UMUI_HEADERBGIMAGE_BMP "${NSISDIR}\Contrib\UltraModernUI\Skins\SoftGray\Header.bmp"
!define /IfNDef UMUI_BOTTOMIMAGE_BMP "${NSISDIR}\Contrib\UltraModernUI\Skins\SoftGray\Bottom.bmp"
!define /IfNDef UMUI_BUTTONIMAGE_BMP "${NSISDIR}\Contrib\UltraModernUI\Skins\SoftGray\Button.bmp"
!define /IfNDef UMUI_SCROLLBARIMAGE_BMP "${NSISDIR}\Contrib\UltraModernUI\Skins\SoftGray\ScrollBar.bmp"
!define /IfNDef UMUI_PAGEBGIMAGE_BMP
!define /IfNDef MUI_WELCOMEFINISHPAGE_BITMAP ; "${NSISDIR}\Contrib\UltraModernUI\Skins\SoftGray\Wizard.bmp"
!define /IfNDef MUI_ICON "${NSISDIR}\Contrib\Graphics\Icons\orange-install-nsis.ico"
!define /IfNDef MUI_UNICON "${NSISDIR}\Contrib\Graphics\Icons\orange-uninstall-nsis.ico"
!define /IfNDef UMUI_XPSTYLE On
