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

;  @app BleachBit NSIS Installer Script - Language Code File AddRemove PerformRemoveOperations
;  @url https://nsis.sourceforge.io/Main_Page
;  @os Windows
;  @scriptversion v2.3.0.1050
;  @scriptdate 2019-04-12
;  @scriptby Tobias B. Besemer (2019-04-08 - 2019-04-12)
;  @tested ok v2.3.0.1050, Windows 7
;  @testeddate 2019-04-12
;  @testedby https://github.com/Tobias-B-Besemer
;  @note 

!insertmacro "${BB_Language_InstallerSections_Translations_PerformRemoveOperations}" "Translation Afrikaans"
!insertmacro "${BB_Language_InstallerSections_Translations_PerformRemoveOperations}" "Translation Albanian"
!insertmacro "${BB_Language_InstallerSections_Translations_PerformRemoveOperations}" "Translation Arabic"
!insertmacro "${BB_Language_InstallerSections_Translations_PerformRemoveOperations}" "Translation Armenian"
!insertmacro "${BB_Language_InstallerSections_Translations_PerformRemoveOperations}" "Translation Asturian"
!insertmacro "${BB_Language_InstallerSections_Translations_PerformRemoveOperations}" "Translation Basque"
!insertmacro "${BB_Language_InstallerSections_Translations_PerformRemoveOperations}" "Translation Belarusian"
!insertmacro "${BB_Language_InstallerSections_Translations_PerformRemoveOperations}" "Translation Bengali"
!insertmacro "${BB_Language_InstallerSections_Translations_PerformRemoveOperations}" "Translation Bosnian"
!insertmacro "${BB_Language_InstallerSections_Translations_PerformRemoveOperations}" "Translation Bulgarian"
!insertmacro "${BB_Language_InstallerSections_Translations_PerformRemoveOperations}" "Translation Burmese"
!insertmacro "${BB_Language_InstallerSections_Translations_PerformRemoveOperations}" "Translation Catalan"
!insertmacro "${BB_Language_InstallerSections_Translations_PerformRemoveOperations}" "Translation Chinese (Simplified)"
!insertmacro "${BB_Language_InstallerSections_Translations_PerformRemoveOperations}" "Translation Chinese (Traditional)"
!insertmacro "${BB_Language_InstallerSections_Translations_PerformRemoveOperations}" "Translation Croatian"
!insertmacro "${BB_Language_InstallerSections_Translations_PerformRemoveOperations}" "Translation Czech"
!insertmacro "${BB_Language_InstallerSections_Translations_PerformRemoveOperations}" "Translation Danish"
!insertmacro "${BB_Language_InstallerSections_Translations_PerformRemoveOperations}" "Translation Dutch"
!insertmacro "${BB_Language_InstallerSections_Translations_PerformRemoveOperations}" "Translation English (Australia)"
!insertmacro "${BB_Language_InstallerSections_Translations_PerformRemoveOperations}" "Translation English (Canada)"
!insertmacro "${BB_Language_InstallerSections_Translations_PerformRemoveOperations}" "Translation English (United Kingdom)"
!insertmacro "${BB_Language_InstallerSections_Translations_PerformRemoveOperations}" "Translation Esperanto"
!insertmacro "${BB_Language_InstallerSections_Translations_PerformRemoveOperations}" "Translation Estonian"
!insertmacro "${BB_Language_InstallerSections_Translations_PerformRemoveOperations}" "Translation Faroese"
!insertmacro "${BB_Language_InstallerSections_Translations_PerformRemoveOperations}" "Translation Finnish"
!insertmacro "${BB_Language_InstallerSections_Translations_PerformRemoveOperations}" "Translation French"
!insertmacro "${BB_Language_InstallerSections_Translations_PerformRemoveOperations}" "Translation Galician"
!insertmacro "${BB_Language_InstallerSections_Translations_PerformRemoveOperations}" "Translation German"
!insertmacro "${BB_Language_InstallerSections_Translations_PerformRemoveOperations}" "Translation Greek"
!insertmacro "${BB_Language_InstallerSections_Translations_PerformRemoveOperations}" "Translation Hebrew"
!insertmacro "${BB_Language_InstallerSections_Translations_PerformRemoveOperations}" "Translation Hindi"
!insertmacro "${BB_Language_InstallerSections_Translations_PerformRemoveOperations}" "Translation Hungarian"
!insertmacro "${BB_Language_InstallerSections_Translations_PerformRemoveOperations}" "Translation Indonesian"
!insertmacro "${BB_Language_InstallerSections_Translations_PerformRemoveOperations}" "Translation Interlingua"
!insertmacro "${BB_Language_InstallerSections_Translations_PerformRemoveOperations}" "Translation Italian"
!insertmacro "${BB_Language_InstallerSections_Translations_PerformRemoveOperations}" "Translation Japanese"
!insertmacro "${BB_Language_InstallerSections_Translations_PerformRemoveOperations}" "Translation Kirghiz"
!insertmacro "${BB_Language_InstallerSections_Translations_PerformRemoveOperations}" "Translation Korean"
!insertmacro "${BB_Language_InstallerSections_Translations_PerformRemoveOperations}" "Translation Kurdish"
!insertmacro "${BB_Language_InstallerSections_Translations_PerformRemoveOperations}" "Translation Latvian"
!insertmacro "${BB_Language_InstallerSections_Translations_PerformRemoveOperations}" "Translation Lithuanian"
!insertmacro "${BB_Language_InstallerSections_Translations_PerformRemoveOperations}" "Translation Low German"
!insertmacro "${BB_Language_InstallerSections_Translations_PerformRemoveOperations}" "Translation Malay"
!insertmacro "${BB_Language_InstallerSections_Translations_PerformRemoveOperations}" "Translation Northern Sami"
!insertmacro "${BB_Language_InstallerSections_Translations_PerformRemoveOperations}" "Translation Norwegian Bokmal"
!insertmacro "${BB_Language_InstallerSections_Translations_PerformRemoveOperations}" "Translation Norwegian Nynorsk"
!insertmacro "${BB_Language_InstallerSections_Translations_PerformRemoveOperations}" "Translation Persian"
!insertmacro "${BB_Language_InstallerSections_Translations_PerformRemoveOperations}" "Translation Polish"
!insertmacro "${BB_Language_InstallerSections_Translations_PerformRemoveOperations}" "Translation Portuguese"
!insertmacro "${BB_Language_InstallerSections_Translations_PerformRemoveOperations}" "Translation Portuguese (Brazilian)"
!insertmacro "${BB_Language_InstallerSections_Translations_PerformRemoveOperations}" "Translation Romanian"
!insertmacro "${BB_Language_InstallerSections_Translations_PerformRemoveOperations}" "Translation Russian"
!insertmacro "${BB_Language_InstallerSections_Translations_PerformRemoveOperations}" "Translation Serbian"
!insertmacro "${BB_Language_InstallerSections_Translations_PerformRemoveOperations}" "Translation Sinhalese"
!insertmacro "${BB_Language_InstallerSections_Translations_PerformRemoveOperations}" "Translation Slovak"
!insertmacro "${BB_Language_InstallerSections_Translations_PerformRemoveOperations}" "Translation Slovenian"
!insertmacro "${BB_Language_InstallerSections_Translations_PerformRemoveOperations}" "Translation Spanish"
!insertmacro "${BB_Language_InstallerSections_Translations_PerformRemoveOperations}" "Translation Swedish"
!insertmacro "${BB_Language_InstallerSections_Translations_PerformRemoveOperations}" "Translation Tamil"
!insertmacro "${BB_Language_InstallerSections_Translations_PerformRemoveOperations}" "Translation Telugu"
!insertmacro "${BB_Language_InstallerSections_Translations_PerformRemoveOperations}" "Translation Thai"
!insertmacro "${BB_Language_InstallerSections_Translations_PerformRemoveOperations}" "Translation Turkish"
!insertmacro "${BB_Language_InstallerSections_Translations_PerformRemoveOperations}" "Translation Ukrainian"
!insertmacro "${BB_Language_InstallerSections_Translations_PerformRemoveOperations}" "Translation Uyghur"
!insertmacro "${BB_Language_InstallerSections_Translations_PerformRemoveOperations}" "Translation Uzbek"
!insertmacro "${BB_Language_InstallerSections_Translations_PerformRemoveOperations}" "Translation Vietnamese"
