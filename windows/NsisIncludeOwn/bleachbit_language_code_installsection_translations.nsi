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

;  @app BleachBit NSIS Installer Script - Language Code File InstallerSectionsTranslations
;  @url https://nsis.sourceforge.io/Main_Page
;  @os Windows
;  @scriptversion v2.3.0.1050
;  @scriptdate 2019-04-12
;  @scriptby Tobias B. Besemer (2019-04-07 - 2019-04-12)
;  @tested ok v2.3.0.1050, Windows 7
;  @testeddate 2019-04-12
;  @testedby https://github.com/Tobias-B-Besemer
;  @note 

Section SectionTranslationEnglishUSA "Translation English (USA)"
  ; "SectionIn RO" means: Section defined mandatory, so that the user can not unselect them!
  SectionIn RO
SectionEnd
!ifndef NoTranslations
  ; http://www.lingoes.net/en/translator/langcode.htm
  ; https://translations.launchpad.net/bleachbit
  Section SectionTranslationAfrikaans "Translation Afrikaans"
    CreateDirectory "$INSTDIR\share\locale\af\"
    SetOutPath "$INSTDIR\share\locale\af\"
    File /r "..\dist\share\locale\af\*.*"
  SectionEnd
  !macro "Remove_${Translation Afrikaans}"
    ;Removes component
    RMDir /r "$INSTDIR\share\locale\af"
  !macroend
  Section SectionTranslationAlbanian "Translation Albanian"
    CreateDirectory "$INSTDIR\share\locale\sq\"
    SetOutPath "$INSTDIR\share\locale\sq\"
    File /r "..\dist\share\locale\sq\*.*"
  SectionEnd
  !macro "Remove_${Translation Albanian}"
    ;Removes component
    RMDir /r "$INSTDIR\share\locale\sq"
  !macroend
  Section SectionTranslationArabic "Translation Arabic"
    CreateDirectory "$INSTDIR\share\locale\ar\"
    SetOutPath "$INSTDIR\share\locale\ar\"
    File /r "..\dist\share\locale\ar\*.*"
  SectionEnd
  !macro "Remove_${Translation Arabic}"
    ;Removes component
    RMDir /r "$INSTDIR\share\locale\ar"
  !macroend
  Section SectionTranslationArmenian "Translation Armenian"
    CreateDirectory "$INSTDIR\share\locale\hy\"
    SetOutPath "$INSTDIR\share\locale\hy\"
    File /r "..\dist\share\locale\hy\*.*"
  SectionEnd
  !macro "Remove_${Translation Armenian}"
    ;Removes component
    RMDir /r "$INSTDIR\share\locale\hy"
  !macroend
  Section SectionTranslationAsturian "Translation Asturian"
    CreateDirectory "$INSTDIR\share\locale\ast\"
    SetOutPath "$INSTDIR\share\locale\ast\"
    File /r "..\dist\share\locale\ast\*.*"
  SectionEnd
  !macro "Remove_${Translation Asturian}"
    ;Removes component
    RMDir /r "$INSTDIR\share\locale\ast"
  !macroend
  Section SectionTranslationBasque "Translation Basque"
    CreateDirectory "$INSTDIR\share\locale\eu\"
    SetOutPath "$INSTDIR\share\locale\eu\"
    File /r "..\dist\share\locale\eu\*.*"
  SectionEnd
  !macro "Remove_${Translation Basque}"
    ;Removes component
    RMDir /r "$INSTDIR\share\locale\eu"
  !macroend
  Section SectionTranslationBelarusian "Translation Belarusian"
    CreateDirectory "$INSTDIR\share\locale\be\"
    SetOutPath "$INSTDIR\share\locale\be\"
    File /r "..\dist\share\locale\be\*.*"
  SectionEnd
  !macro "Remove_${Translation Belarusian}"
    ;Removes component
    RMDir /r "$INSTDIR\share\locale\be"
  !macroend
  Section SectionTranslationBengali "Translation Bengali"
    CreateDirectory "$INSTDIR\share\locale\bn\"
    SetOutPath "$INSTDIR\share\locale\bn\"
    File /r "..\dist\share\locale\bn\*.*"
  SectionEnd
  !macro "Remove_${Translation Bengali}"
    ;Removes component
    RMDir /r "$INSTDIR\share\locale\bn"
  !macroend
  Section SectionTranslationBosnian "Translation Bosnian"
    CreateDirectory "$INSTDIR\share\locale\bs\"
    SetOutPath "$INSTDIR\share\locale\bs\"
    File /r "..\dist\share\locale\bs\*.*"
  SectionEnd
  !macro "Remove_${Translation Bosnian}"
    ;Removes component
    RMDir /r "$INSTDIR\share\locale\bs"
  !macroend
  Section SectionTranslationBulgarian "Translation Bulgarian"
    CreateDirectory "$INSTDIR\share\locale\bg\"
    SetOutPath "$INSTDIR\share\locale\bg\"
    File /r "..\dist\share\locale\bg\*.*"
  SectionEnd
  !macro "Remove_${Translation Bulgarian}"
    ;Removes component
    RMDir /r "$INSTDIR\share\locale\bg"
  !macroend
  Section SectionTranslationBurmese "Translation Burmese"
    CreateDirectory "$INSTDIR\share\locale\my\"
    SetOutPath "$INSTDIR\share\locale\my\"
    File /r "..\dist\share\locale\my\*.*"
  SectionEnd
  !macro "Remove_${Translation Burmese}"
    ;Removes component
    RMDir /r "$INSTDIR\share\locale\my"
  !macroend
  Section SectionTranslationCatalan "Translation Catalan"
    CreateDirectory "$INSTDIR\share\locale\ca\"
    SetOutPath "$INSTDIR\share\locale\ca\"
    File /r "..\dist\share\locale\ca\*.*"
  SectionEnd
  !macro "Remove_${Translation Catalan}"
    ;Removes component
    RMDir /r "$INSTDIR\share\locale\ca"
  !macroend
  Section SectionTranslationChineseSimplified "Translation Chinese (Simplified)"
    CreateDirectory "$INSTDIR\share\locale\zh_CN\"
    SetOutPath "$INSTDIR\share\locale\zh_CN\"
    File /r "..\dist\share\locale\zh_CN\*.*"
  SectionEnd
  !macro "Remove_${Translation Chinese (Simplified)}"
    ;Removes component
    RMDir /r "$INSTDIR\share\locale\zh_CN"
  !macroend
  Section SectionTranslationChineseTraditional "Translation Chinese (Traditional)"
    CreateDirectory "$INSTDIR\share\locale\zh_TW\"
    SetOutPath "$INSTDIR\share\locale\zh_TW\"
    File /r "..\dist\share\locale\zh_TW\*.*"
  SectionEnd
  !macro "Remove_${Translation Chinese (Traditional)}"
    ;Removes component
    RMDir /r "$INSTDIR\share\locale\zh_TW"
  !macroend
  Section SectionTranslationCroatian "Translation Croatian"
    CreateDirectory "$INSTDIR\share\locale\hr\"
    SetOutPath "$INSTDIR\share\locale\hr\"
    File /r "..\dist\share\locale\hr\*.*"
  SectionEnd
  !macro "Remove_${Translation Croatian}"
    ;Removes component
    RMDir /r "$INSTDIR\share\locale\hr"
  !macroend
  Section SectionTranslationCzech "Translation Czech"
    CreateDirectory "$INSTDIR\share\locale\cs\"
    SetOutPath "$INSTDIR\share\locale\cs\"
    File /r "..\dist\share\locale\cs\*.*"
  SectionEnd
  !macro "Remove_${Translation Czech}"
    ;Removes component
    RMDir /r "$INSTDIR\share\locale\cs"
  !macroend
  Section SectionTranslationDanish "Translation Danish"
    CreateDirectory "$INSTDIR\share\locale\da\"
    SetOutPath "$INSTDIR\share\locale\da\"
    File /r "..\dist\share\locale\da\*.*"
  SectionEnd
  !macro "Remove_${Translation Danish}"
    ;Removes component
    RMDir /r "$INSTDIR\share\locale\da"
  !macroend
  Section SectionTranslationDutch "Translation Dutch"
    CreateDirectory "$INSTDIR\share\locale\nl\"
    SetOutPath "$INSTDIR\share\locale\nl\"
    File /r "..\dist\share\locale\nl\*.*"
  SectionEnd
  !macro "Remove_${Translation Dutch}"
    ;Removes component
    RMDir /r "$INSTDIR\share\locale\nl"
  !macroend
  Section SectionTranslationEnglishAustralia "Translation English (Australia)"
    CreateDirectory "$INSTDIR\share\locale\en_AU\"
    SetOutPath "$INSTDIR\share\locale\en_AU\"
    File /r "..\dist\share\locale\en_AU\*.*"
  SectionEnd
  !macro "Remove_${Translation English (Australia)}"
    ;Removes component
    RMDir /r "$INSTDIR\share\locale\en_AU"
  !macroend
  Section SectionTranslationEnglishCanada "Translation English (Canada)"
    CreateDirectory "$INSTDIR\share\locale\en_CA\"
    SetOutPath "$INSTDIR\share\locale\en_CA\"
    File /r "..\dist\share\locale\en_CA\*.*"
  SectionEnd
  !macro "Remove_${Translation English (Canada)}"
    ;Removes component
    RMDir /r "$INSTDIR\share\locale\en_CA"
  !macroend
  Section SectionTranslationEnglishUnitedKingdom "Translation English (United Kingdom)"
  CreateDirectory "$INSTDIR\share\locale\en_GB\"
    SetOutPath "$INSTDIR\share\locale\en_GB\"
    File /r "..\dist\share\locale\en_GB\*.*"
  SectionEnd
  !macro "Remove_${Translation English (United Kingdom)}"
    ;Removes component
    RMDir /r "$INSTDIR\share\locale\en_GB"
  !macroend
  Section SectionTranslationEsperanto "Translation Esperanto"
    CreateDirectory "$INSTDIR\share\locale\eo\"
    SetOutPath "$INSTDIR\share\locale\eo\"
    File /r "..\dist\share\locale\eo\*.*"
  SectionEnd
  !macro "Remove_${Translation Esperanto}"
    ;Removes component
    RMDir /r "$INSTDIR\share\locale\eo"
  !macroend
  Section SectionTranslationEstonian "Translation Estonian"
    CreateDirectory "$INSTDIR\share\locale\et\"
    SetOutPath "$INSTDIR\share\locale\et\"
    File /r "..\dist\share\locale\et\*.*"
  SectionEnd
  !macro "Remove_${Translation Estonian}"
    ;Removes component
    RMDir /r "$INSTDIR\share\locale\et"
  !macroend
  Section SectionTranslationFaroese "Translation Faroese"
    CreateDirectory "$INSTDIR\share\locale\fo\"
    SetOutPath "$INSTDIR\share\locale\fo\"
    File /r "..\dist\share\locale\fo\*.*"
  SectionEnd
  !macro "Remove_${Translation Faroese}"
    ;Removes component
    RMDir /r "$INSTDIR\share\locale\fo"
  !macroend
  Section SectionTranslationFinnish "Translation Finnish"
    CreateDirectory "$INSTDIR\share\locale\fi\"
    SetOutPath "$INSTDIR\share\locale\fi\"
    File /r "..\dist\share\locale\fi\*.*"
  SectionEnd
  !macro "Remove_${Translation Finnish}"
    ;Removes component
    RMDir /r "$INSTDIR\share\locale\fi"
  !macroend
  Section SectionTranslationFrench "Translation French"
    CreateDirectory "$INSTDIR\share\locale\fr\"
    SetOutPath "$INSTDIR\share\locale\fr\"
    File /r "..\dist\share\locale\fr\*.*"
  SectionEnd
  !macro "Remove_${Translation French}"
    ;Removes component
    RMDir /r "$INSTDIR\share\locale\fr"
  !macroend
  Section SectionTranslationGalician "Translation Galician"
    CreateDirectory "$INSTDIR\share\locale\gl\"
    SetOutPath "$INSTDIR\share\locale\gl\"
    File /r "..\dist\share\locale\gl\*.*"
  SectionEnd
  !macro "Remove_${Translation Galician}"
    ;Removes component
    RMDir /r "$INSTDIR\share\locale\gl"
  !macroend
  Section SectionTranslationGerman "Translation German"
    CreateDirectory "$INSTDIR\share\locale\de\"
    SetOutPath "$INSTDIR\share\locale\de\"
    File /r "..\dist\share\locale\de\*.*"
  SectionEnd
  !macro "Remove_${Translation German}"
    ;Removes component
    RMDir /r "$INSTDIR\share\locale\de"
  !macroend
  Section SectionTranslationGreek "Translation Greek"
    CreateDirectory "$INSTDIR\share\locale\el\"
    SetOutPath "$INSTDIR\share\locale\el\"
    File /r "..\dist\share\locale\el\*.*"
  SectionEnd
  !macro "Remove_${Translation Greek}"
    ;Removes component
    RMDir /r "$INSTDIR\share\locale\el"
  !macroend
  Section SectionTranslationHebrew "Translation Hebrew"
    CreateDirectory "$INSTDIR\share\locale\he\"
    SetOutPath "$INSTDIR\share\locale\he\"
    File /r "..\dist\share\locale\he\*.*"
  SectionEnd
  !macro "Remove_${Translation Hebrew}"
    ;Removes component
    RMDir /r "$INSTDIR\share\locale\he"
  !macroend
  Section SectionTranslationHindi "Translation Hindi"
    CreateDirectory "$INSTDIR\share\locale\hi\"
    SetOutPath "$INSTDIR\share\locale\hi\"
    File /r "..\dist\share\locale\hi\*.*"
  SectionEnd
  !macro "Remove_${Translation Hindi}"
    ;Removes component
    RMDir /r "$INSTDIR\share\locale\hi"
  !macroend
  Section SectionTranslationHungarian "Translation Hungarian"
    CreateDirectory "$INSTDIR\share\locale\hu\"
    SetOutPath "$INSTDIR\share\locale\hu\"
    File /r "..\dist\share\locale\hu\*.*"
  SectionEnd
  !macro "Remove_${Translation Hungarian}"
    ;Removes component
    RMDir /r "$INSTDIR\share\locale\hu"
  !macroend
  Section SectionTranslationIndonesian "Translation Indonesian"
    CreateDirectory "$INSTDIR\share\locale\id\"
    SetOutPath "$INSTDIR\share\locale\id\"
    File /r "..\dist\share\locale\id\*.*"
  SectionEnd
  !macro "Remove_${Translation Indonesian}"
    ;Removes component
    RMDir /r "$INSTDIR\share\locale\id"
  !macroend
  Section SectionTranslationInterlingua "Translation Interlingua"
    CreateDirectory "$INSTDIR\share\locale\ia\"
    SetOutPath "$INSTDIR\share\locale\ia\"
    File /r "..\dist\share\locale\ia\*.*"
  SectionEnd
  !macro "Remove_${Translation Interlingua}"
    ;Removes component
    RMDir /r "$INSTDIR\share\locale\ia"
  !macroend
  Section SectionTranslationItalian "Translation Italian"
    CreateDirectory "$INSTDIR\share\locale\it\"
    SetOutPath "$INSTDIR\share\locale\it\"
    File /r "..\dist\share\locale\it\*.*"
  SectionEnd
  !macro "Remove_${Translation Italian}"
    ;Removes component
    RMDir /r "$INSTDIR\share\locale\it"
  !macroend
  Section SectionTranslationJapanese "Translation Japanese"
    CreateDirectory "$INSTDIR\share\locale\ja\"
    SetOutPath "$INSTDIR\share\locale\ja\"
    File /r "..\dist\share\locale\ja\*.*"
  SectionEnd
  !macro "Remove_${Translation Japanese}"
    ;Removes component
    RMDir /r "$INSTDIR\share\locale\ja"
  !macroend
  Section SectionTranslationKirghiz "Translation Kirghiz"
    CreateDirectory "$INSTDIR\share\locale\ky\"
    SetOutPath "$INSTDIR\share\locale\ky\"
    File /r "..\dist\share\locale\ky\*.*"
  SectionEnd
  !macro "Remove_${Translation Kirghiz}"
    ;Removes component
    RMDir /r "$INSTDIR\share\locale\ky"
  !macroend
  Section SectionTranslationKorean "Translation Korean"
    CreateDirectory "$INSTDIR\share\locale\ko\"
    SetOutPath "$INSTDIR\share\locale\ko\"
    File /r "..\dist\share\locale\ko\*.*"
  SectionEnd
  !macro "Remove_${Translation Korean}"
    ;Removes component
    RMDir /r "$INSTDIR\share\locale\ko"
  !macroend
  Section SectionTranslationKurdish "Translation Kurdish"
    CreateDirectory "$INSTDIR\share\locale\ku\"
    SetOutPath "$INSTDIR\share\locale\ku\"
    File /r "..\dist\share\locale\ku\*.*"
  SectionEnd
  !macro "Remove_${Translation Kurdish}"
    ;Removes component
    RMDir /r "$INSTDIR\share\locale\ku"
  !macroend
  Section SectionTranslationLatvian "Translation Latvian"
    CreateDirectory "$INSTDIR\share\locale\lv\"
    SetOutPath "$INSTDIR\share\locale\lv\"
    File /r "..\dist\share\locale\lv\*.*"
  SectionEnd
  !macro "Remove_${Translation Latvian}"
    ;Removes component
    RMDir /r "$INSTDIR\share\locale\lv"
  !macroend
  Section SectionTranslationLithuanian "Translation Lithuanian"
    CreateDirectory "$INSTDIR\share\locale\lt\"
    SetOutPath "$INSTDIR\share\locale\lt\"
    File /r "..\dist\share\locale\lt\*.*"
  SectionEnd
  !macro "Remove_${Translation Lithuanian}"
    ;Removes component
    RMDir /r "$INSTDIR\share\locale\lt"
  !macroend
  Section SectionTranslationLowGerman "Translation Low German"
    CreateDirectory "$INSTDIR\share\locale\nds\"
    SetOutPath "$INSTDIR\share\locale\nds\"
    File /r "..\dist\share\locale\nds\*.*"
  SectionEnd
  !macro "Remove_${Translation Low German}"
    ;Removes component
    RMDir /r "$INSTDIR\share\locale\nds"
  !macroend
  Section SectionTranslationMalay "Translation Malay"
    CreateDirectory "$INSTDIR\share\locale\ms\"
    SetOutPath "$INSTDIR\share\locale\ms\"
    File /r "..\dist\share\locale\ms\*.*"
  SectionEnd
  !macro "Remove_${Translation Malay}"
    ;Removes component
    RMDir /r "$INSTDIR\share\locale\ms"
  !macroend
  Section SectionTranslationNorthernSami "Translation Northern Sami"
    CreateDirectory "$INSTDIR\share\locale\se\"
    SetOutPath "$INSTDIR\share\locale\se\"
    File /r "..\dist\share\locale\se\*.*"
  SectionEnd
  !macro "Remove_${Translation Northern Sami}"
    ;Removes component
    RMDir /r "$INSTDIR\share\locale\se"
  !macroend
  Section SectionTranslationNorwegianBokmal "Translation Norwegian Bokmal"
    CreateDirectory "$INSTDIR\share\locale\nb\"
    SetOutPath "$INSTDIR\share\locale\nb\"
    File /r "..\dist\share\locale\nb\*.*"
  SectionEnd
  !macro "Remove_${Translation Norwegian Bokmal}"
    ;Removes component
    RMDir /r "$INSTDIR\share\locale\nb"
  !macroend
  Section SectionTranslationNorwegianNynorsk "Translation Norwegian Nynorsk"
    CreateDirectory "$INSTDIR\share\locale\nn\"
    SetOutPath "$INSTDIR\share\locale\nn\"
    File /r "..\dist\share\locale\nn\*.*"
  SectionEnd
  !macro "Remove_${Translation Norwegian Nynorsk}"
    ;Removes component
    RMDir /r "$INSTDIR\share\locale\nn"
  !macroend
  Section SectionTranslationPersian "Translation Persian"
    CreateDirectory "$INSTDIR\share\locale\fa\"
    SetOutPath "$INSTDIR\share\locale\fa\"
    File /r "..\dist\share\locale\fa\*.*"
  SectionEnd
  !macro "Remove_${Translation Persian}"
    ;Removes component
    RMDir /r "$INSTDIR\share\locale\fa"
  !macroend
  Section SectionTranslationPolish "Translation Polish"
    CreateDirectory "$INSTDIR\share\locale\pl\"
    SetOutPath "$INSTDIR\share\locale\pl\"
    File /r "..\dist\share\locale\pl\*.*"
  SectionEnd
  !macro "Remove_${Translation Polish}"
    ;Removes component
    RMDir /r "$INSTDIR\share\locale\pl"
  !macroend
  Section SectionTranslationPortuguese "Translation Portuguese"
    CreateDirectory "$INSTDIR\share\locale\pt\"
    SetOutPath "$INSTDIR\share\locale\pt\"
    File /r "..\dist\share\locale\pt\*.*"
  SectionEnd
  !macro "Remove_${Translation Portuguese}"
    ;Removes component
    RMDir /r "$INSTDIR\share\locale\pt"
  !macroend
  Section SectionTranslationPortugueseBrazilian "Translation Portuguese (Brazilian)"
    CreateDirectory "$INSTDIR\share\locale\pt_BR\"
    SetOutPath "$INSTDIR\share\locale\pt_BR\"
    File /r "..\dist\share\locale\pt_BR\*.*"
  SectionEnd
  !macro "Remove_${Translation Portuguese (Brazilian)}"
    ;Removes component
    RMDir /r "$INSTDIR\share\locale\pt_BR"
  !macroend
  Section SectionTranslationRomanian "Translation Romanian"
    CreateDirectory "$INSTDIR\share\locale\ro\"
    SetOutPath "$INSTDIR\share\locale\ro\"
    File /r "..\dist\share\locale\ro\*.*"
  SectionEnd
  !macro "Remove_${Translation Romanian}"
    ;Removes component
    RMDir /r "$INSTDIR\share\locale\ro"
  !macroend
  Section SectionTranslationRussian "Translation Russian"
    CreateDirectory "$INSTDIR\share\locale\ru\"
    SetOutPath "$INSTDIR\share\locale\ru\"
    File /r "..\dist\share\locale\ru\*.*"
  SectionEnd
  !macro "Remove_${Translation Russian}"
    ;Removes component
    RMDir /r "$INSTDIR\share\locale\ru"
  !macroend
  Section SectionTranslationSerbian "Translation Serbian"
    CreateDirectory "$INSTDIR\share\locale\sr\"
    SetOutPath "$INSTDIR\share\locale\sr\"
    File /r "..\dist\share\locale\sr\*.*"
  SectionEnd
  !macro "Remove_${Translation Serbian}"
    ;Removes component
    RMDir /r "$INSTDIR\share\locale\sr"
  !macroend
  Section SectionTranslationSinhalese "Translation Sinhalese"
    CreateDirectory "$INSTDIR\share\locale\si\"
    SetOutPath "$INSTDIR\share\locale\si\"
    File /r "..\dist\share\locale\si\*.*"
  SectionEnd
  !macro "Remove_${Translation Sinhalese}"
    ;Removes component
    RMDir /r "$INSTDIR\share\locale\si"
  !macroend
  Section SectionTranslationSlovak "Translation Slovak"
    CreateDirectory "$INSTDIR\share\locale\sk\"
    SetOutPath "$INSTDIR\share\locale\sk\"
    File /r "..\dist\share\locale\sk\*.*"
  SectionEnd
  !macro "Remove_${Translation Slovak}"
    ;Removes component
    RMDir /r "$INSTDIR\share\locale\sk"
  !macroend
  Section SectionTranslationSlovenian "Translation Slovenian"
    CreateDirectory "$INSTDIR\share\locale\sl\"
    SetOutPath "$INSTDIR\share\locale\sl\"
    File /r "..\dist\share\locale\sl\*.*"
  SectionEnd
  !macro "Remove_${Translation Slovenian}"
    ;Removes component
    RMDir /r "$INSTDIR\share\locale\sl"
  !macroend
  Section SectionTranslationSpanish "Translation Spanish"
    CreateDirectory "$INSTDIR\share\locale\es\"
    SetOutPath "$INSTDIR\share\locale\es\"
    File /r "..\dist\share\locale\es\*.*"
  SectionEnd
  !macro "Remove_${Translation Spanish}"
    ;Removes component
    RMDir /r "$INSTDIR\share\locale\es"
  !macroend
  Section SectionTranslationSwedish "Translation Swedish"
    CreateDirectory "$INSTDIR\share\locale\sv\"
    SetOutPath "$INSTDIR\share\locale\sv\"
    File /r "..\dist\share\locale\sv\*.*"
  SectionEnd
  !macro "Remove_${Translation Swedish}"
    ;Removes component
    RMDir /r "$INSTDIR\share\locale\sv"
  !macroend
  Section SectionTranslationTamil "Translation Tamil"
    CreateDirectory "$INSTDIR\share\locale\ta\"
    SetOutPath "$INSTDIR\share\locale\ta\"
    File /r "..\dist\share\locale\ta\*.*"
  SectionEnd
  !macro "Remove_${Translation Tamil}"
    ;Removes component
    RMDir /r "$INSTDIR\share\locale\ta"
  !macroend
  Section SectionTranslationTelugu "Translation Telugu"
    CreateDirectory "$INSTDIR\share\locale\te\"
    SetOutPath "$INSTDIR\share\locale\te\"
    File /r "..\dist\share\locale\te\*.*"
  SectionEnd
  !macro "Remove_${Translation Telugu}"
    ;Removes component
    RMDir /r "$INSTDIR\share\locale\te"
  !macroend
  Section SectionTranslationThai "Translation Thai"
    CreateDirectory "$INSTDIR\share\locale\th\"
    SetOutPath "$INSTDIR\share\locale\th\"
    File /r "..\dist\share\locale\th\*.*"
  SectionEnd
  !macro "Remove_${Translation Thai}"
    ;Removes component
    RMDir /r "$INSTDIR\share\locale\th"
  !macroend
  Section SectionTranslationTurkish "Translation Turkish"
    CreateDirectory "$INSTDIR\share\locale\tr\"
    SetOutPath "$INSTDIR\share\locale\tr\"
    File /r "..\dist\share\locale\tr\*.*"
  SectionEnd
  !macro "Remove_${Translation Turkish}"
    ;Removes component
    RMDir /r "$INSTDIR\share\locale\tr"
  !macroend
  Section SectionTranslationUkrainian "Translation Ukrainian"
    CreateDirectory "$INSTDIR\share\locale\uk\"
    SetOutPath "$INSTDIR\share\locale\uk\"
    File /r "..\dist\share\locale\uk\*.*"
  SectionEnd
  !macro "Remove_${Translation Ukrainian}"
    ;Removes component
    RMDir /r "$INSTDIR\share\locale\uk"
  !macroend
  Section SectionTranslationUyghur "Translation Uyghur"
    CreateDirectory "$INSTDIR\share\locale\ug\"
    SetOutPath "$INSTDIR\share\locale\ug\"
    File /r "..\dist\share\locale\ug\*.*"
  SectionEnd
  !macro "Remove_${Translation Uyghur}"
    ;Removes component
    RMDir /r "$INSTDIR\share\locale\ug"
  !macroend
  Section SectionTranslationUzbek "Translation Uzbek"
    CreateDirectory "$INSTDIR\share\locale\uz\"
    SetOutPath "$INSTDIR\share\locale\uz\"
    File /r "..\dist\share\locale\uz\*.*"
  SectionEnd
  !macro "Remove_${Translation Uzbek}"
    ;Removes component
    RMDir /r "$INSTDIR\share\locale\uz"
  !macroend
  Section SectionTranslationVietnamese "Translation Vietnamese"
    CreateDirectory "$INSTDIR\share\locale\vi\"
    SetOutPath "$INSTDIR\share\locale\vi\"
    File /r "..\dist\share\locale\vi\*.*"
  SectionEnd
  !macro "Remove_${Translation Vietnamese}"
    ;Removes component
    RMDir /r "$INSTDIR\share\locale\vi"
  !macroend
!endif
