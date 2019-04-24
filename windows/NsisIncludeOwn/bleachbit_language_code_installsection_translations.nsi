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
;  @scriptversion v2.3.0.1059
;  @scriptdate 2019-04-18
;  @scriptby Tobias B. Besemer (2019-04-07 - 2019-04-18)
;  @tested ok v2.3.0.1059, Windows 7
;  @testeddate 2019-04-18
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
  Section SectionTranslationAlbanian "Translation Albanian"
    CreateDirectory "$INSTDIR\share\locale\sq\"
    SetOutPath "$INSTDIR\share\locale\sq\"
    File /r "..\dist\share\locale\sq\*.*"
  SectionEnd
  Section SectionTranslationArabic "Translation Arabic"
    CreateDirectory "$INSTDIR\share\locale\ar\"
    SetOutPath "$INSTDIR\share\locale\ar\"
    File /r "..\dist\share\locale\ar\*.*"
  SectionEnd
  Section SectionTranslationArmenian "Translation Armenian"
    CreateDirectory "$INSTDIR\share\locale\hy\"
    SetOutPath "$INSTDIR\share\locale\hy\"
    File /r "..\dist\share\locale\hy\*.*"
  SectionEnd
  Section SectionTranslationAsturian "Translation Asturian"
    CreateDirectory "$INSTDIR\share\locale\ast\"
    SetOutPath "$INSTDIR\share\locale\ast\"
    File /r "..\dist\share\locale\ast\*.*"
  SectionEnd
  Section SectionTranslationBasque "Translation Basque"
    CreateDirectory "$INSTDIR\share\locale\eu\"
    SetOutPath "$INSTDIR\share\locale\eu\"
    File /r "..\dist\share\locale\eu\*.*"
  SectionEnd
  Section SectionTranslationBelarusian "Translation Belarusian"
    CreateDirectory "$INSTDIR\share\locale\be\"
    SetOutPath "$INSTDIR\share\locale\be\"
    File /r "..\dist\share\locale\be\*.*"
  SectionEnd
  Section SectionTranslationBengali "Translation Bengali"
    CreateDirectory "$INSTDIR\share\locale\bn\"
    SetOutPath "$INSTDIR\share\locale\bn\"
    File /r "..\dist\share\locale\bn\*.*"
  SectionEnd
  Section SectionTranslationBosnian "Translation Bosnian"
    CreateDirectory "$INSTDIR\share\locale\bs\"
    SetOutPath "$INSTDIR\share\locale\bs\"
    File /r "..\dist\share\locale\bs\*.*"
  SectionEnd
  Section SectionTranslationBulgarian "Translation Bulgarian"
    CreateDirectory "$INSTDIR\share\locale\bg\"
    SetOutPath "$INSTDIR\share\locale\bg\"
    File /r "..\dist\share\locale\bg\*.*"
  SectionEnd
  Section SectionTranslationBurmese "Translation Burmese"
    CreateDirectory "$INSTDIR\share\locale\my\"
    SetOutPath "$INSTDIR\share\locale\my\"
    File /r "..\dist\share\locale\my\*.*"
  SectionEnd
  Section SectionTranslationCatalan "Translation Catalan"
    CreateDirectory "$INSTDIR\share\locale\ca\"
    SetOutPath "$INSTDIR\share\locale\ca\"
    File /r "..\dist\share\locale\ca\*.*"
  SectionEnd
  Section SectionTranslationChineseSimplified "Translation Chinese (Simplified)"
    CreateDirectory "$INSTDIR\share\locale\zh_CN\"
    SetOutPath "$INSTDIR\share\locale\zh_CN\"
    File /r "..\dist\share\locale\zh_CN\*.*"
  SectionEnd
  Section SectionTranslationChineseTraditional "Translation Chinese (Traditional)"
    CreateDirectory "$INSTDIR\share\locale\zh_TW\"
    SetOutPath "$INSTDIR\share\locale\zh_TW\"
    File /r "..\dist\share\locale\zh_TW\*.*"
  SectionEnd
  Section SectionTranslationCroatian "Translation Croatian"
    CreateDirectory "$INSTDIR\share\locale\hr\"
    SetOutPath "$INSTDIR\share\locale\hr\"
    File /r "..\dist\share\locale\hr\*.*"
  SectionEnd
  Section SectionTranslationCzech "Translation Czech"
    CreateDirectory "$INSTDIR\share\locale\cs\"
    SetOutPath "$INSTDIR\share\locale\cs\"
    File /r "..\dist\share\locale\cs\*.*"
  SectionEnd
  Section SectionTranslationDanish "Translation Danish"
    CreateDirectory "$INSTDIR\share\locale\da\"
    SetOutPath "$INSTDIR\share\locale\da\"
    File /r "..\dist\share\locale\da\*.*"
  SectionEnd
  Section SectionTranslationDutch "Translation Dutch"
    CreateDirectory "$INSTDIR\share\locale\nl\"
    SetOutPath "$INSTDIR\share\locale\nl\"
    File /r "..\dist\share\locale\nl\*.*"
  SectionEnd
  Section SectionTranslationEnglishAustralia "Translation English (Australia)"
    CreateDirectory "$INSTDIR\share\locale\en_AU\"
    SetOutPath "$INSTDIR\share\locale\en_AU\"
    File /r "..\dist\share\locale\en_AU\*.*"
  SectionEnd
  Section SectionTranslationEnglishCanada "Translation English (Canada)"
    CreateDirectory "$INSTDIR\share\locale\en_CA\"
    SetOutPath "$INSTDIR\share\locale\en_CA\"
    File /r "..\dist\share\locale\en_CA\*.*"
  SectionEnd
  Section SectionTranslationEnglishUnitedKingdom "Translation English (United Kingdom)"
  CreateDirectory "$INSTDIR\share\locale\en_GB\"
    SetOutPath "$INSTDIR\share\locale\en_GB\"
    File /r "..\dist\share\locale\en_GB\*.*"
  SectionEnd
  Section SectionTranslationEsperanto "Translation Esperanto"
    CreateDirectory "$INSTDIR\share\locale\eo\"
    SetOutPath "$INSTDIR\share\locale\eo\"
    File /r "..\dist\share\locale\eo\*.*"
  SectionEnd
  Section SectionTranslationEstonian "Translation Estonian"
    CreateDirectory "$INSTDIR\share\locale\et\"
    SetOutPath "$INSTDIR\share\locale\et\"
    File /r "..\dist\share\locale\et\*.*"
  SectionEnd
  Section SectionTranslationFaroese "Translation Faroese"
    CreateDirectory "$INSTDIR\share\locale\fo\"
    SetOutPath "$INSTDIR\share\locale\fo\"
    File /r "..\dist\share\locale\fo\*.*"
  SectionEnd
  Section SectionTranslationFinnish "Translation Finnish"
    CreateDirectory "$INSTDIR\share\locale\fi\"
    SetOutPath "$INSTDIR\share\locale\fi\"
    File /r "..\dist\share\locale\fi\*.*"
  SectionEnd
  Section SectionTranslationFrench "Translation French"
    CreateDirectory "$INSTDIR\share\locale\fr\"
    SetOutPath "$INSTDIR\share\locale\fr\"
    File /r "..\dist\share\locale\fr\*.*"
  SectionEnd
  Section SectionTranslationGalician "Translation Galician"
    CreateDirectory "$INSTDIR\share\locale\gl\"
    SetOutPath "$INSTDIR\share\locale\gl\"
    File /r "..\dist\share\locale\gl\*.*"
  SectionEnd
  Section SectionTranslationGerman "Translation German"
    CreateDirectory "$INSTDIR\share\locale\de\"
    SetOutPath "$INSTDIR\share\locale\de\"
    File /r "..\dist\share\locale\de\*.*"
  SectionEnd
  Section SectionTranslationGreek "Translation Greek"
    CreateDirectory "$INSTDIR\share\locale\el\"
    SetOutPath "$INSTDIR\share\locale\el\"
    File /r "..\dist\share\locale\el\*.*"
  SectionEnd
  Section SectionTranslationHebrew "Translation Hebrew"
    CreateDirectory "$INSTDIR\share\locale\he\"
    SetOutPath "$INSTDIR\share\locale\he\"
    File /r "..\dist\share\locale\he\*.*"
  SectionEnd
  Section SectionTranslationHindi "Translation Hindi"
    CreateDirectory "$INSTDIR\share\locale\hi\"
    SetOutPath "$INSTDIR\share\locale\hi\"
    File /r "..\dist\share\locale\hi\*.*"
  SectionEnd
  Section SectionTranslationHungarian "Translation Hungarian"
    CreateDirectory "$INSTDIR\share\locale\hu\"
    SetOutPath "$INSTDIR\share\locale\hu\"
    File /r "..\dist\share\locale\hu\*.*"
  SectionEnd
  Section SectionTranslationIndonesian "Translation Indonesian"
    CreateDirectory "$INSTDIR\share\locale\id\"
    SetOutPath "$INSTDIR\share\locale\id\"
    File /r "..\dist\share\locale\id\*.*"
  SectionEnd
  Section SectionTranslationInterlingua "Translation Interlingua"
    CreateDirectory "$INSTDIR\share\locale\ia\"
    SetOutPath "$INSTDIR\share\locale\ia\"
    File /r "..\dist\share\locale\ia\*.*"
  SectionEnd
  Section SectionTranslationItalian "Translation Italian"
    CreateDirectory "$INSTDIR\share\locale\it\"
    SetOutPath "$INSTDIR\share\locale\it\"
    File /r "..\dist\share\locale\it\*.*"
  SectionEnd
  Section SectionTranslationJapanese "Translation Japanese"
    CreateDirectory "$INSTDIR\share\locale\ja\"
    SetOutPath "$INSTDIR\share\locale\ja\"
    File /r "..\dist\share\locale\ja\*.*"
  SectionEnd
  Section SectionTranslationKirghiz "Translation Kirghiz"
    CreateDirectory "$INSTDIR\share\locale\ky\"
    SetOutPath "$INSTDIR\share\locale\ky\"
    File /r "..\dist\share\locale\ky\*.*"
  SectionEnd
  Section SectionTranslationKorean "Translation Korean"
    CreateDirectory "$INSTDIR\share\locale\ko\"
    SetOutPath "$INSTDIR\share\locale\ko\"
    File /r "..\dist\share\locale\ko\*.*"
  SectionEnd
  Section SectionTranslationKurdish "Translation Kurdish"
    CreateDirectory "$INSTDIR\share\locale\ku\"
    SetOutPath "$INSTDIR\share\locale\ku\"
    File /r "..\dist\share\locale\ku\*.*"
  SectionEnd
  Section SectionTranslationLatvian "Translation Latvian"
    CreateDirectory "$INSTDIR\share\locale\lv\"
    SetOutPath "$INSTDIR\share\locale\lv\"
    File /r "..\dist\share\locale\lv\*.*"
  SectionEnd
  Section SectionTranslationLithuanian "Translation Lithuanian"
    CreateDirectory "$INSTDIR\share\locale\lt\"
    SetOutPath "$INSTDIR\share\locale\lt\"
    File /r "..\dist\share\locale\lt\*.*"
  SectionEnd
  Section SectionTranslationLowGerman "Translation Low German"
    CreateDirectory "$INSTDIR\share\locale\nds\"
    SetOutPath "$INSTDIR\share\locale\nds\"
    File /r "..\dist\share\locale\nds\*.*"
  SectionEnd
  Section SectionTranslationMalay "Translation Malay"
    CreateDirectory "$INSTDIR\share\locale\ms\"
    SetOutPath "$INSTDIR\share\locale\ms\"
    File /r "..\dist\share\locale\ms\*.*"
  SectionEnd
  Section SectionTranslationNorthernSami "Translation Northern Sami"
    CreateDirectory "$INSTDIR\share\locale\se\"
    SetOutPath "$INSTDIR\share\locale\se\"
    File /r "..\dist\share\locale\se\*.*"
  SectionEnd
  Section SectionTranslationNorwegianBokmal "Translation Norwegian Bokmal"
    CreateDirectory "$INSTDIR\share\locale\nb\"
    SetOutPath "$INSTDIR\share\locale\nb\"
    File /r "..\dist\share\locale\nb\*.*"
  SectionEnd
  Section SectionTranslationNorwegianNynorsk "Translation Norwegian Nynorsk"
    CreateDirectory "$INSTDIR\share\locale\nn\"
    SetOutPath "$INSTDIR\share\locale\nn\"
    File /r "..\dist\share\locale\nn\*.*"
  SectionEnd
  Section SectionTranslationPersian "Translation Persian"
    CreateDirectory "$INSTDIR\share\locale\fa\"
    SetOutPath "$INSTDIR\share\locale\fa\"
    File /r "..\dist\share\locale\fa\*.*"
  SectionEnd
  Section SectionTranslationPolish "Translation Polish"
    CreateDirectory "$INSTDIR\share\locale\pl\"
    SetOutPath "$INSTDIR\share\locale\pl\"
    File /r "..\dist\share\locale\pl\*.*"
  SectionEnd
  Section SectionTranslationPortuguese "Translation Portuguese"
    CreateDirectory "$INSTDIR\share\locale\pt\"
    SetOutPath "$INSTDIR\share\locale\pt\"
    File /r "..\dist\share\locale\pt\*.*"
  SectionEnd
  Section SectionTranslationPortugueseBrazilian "Translation Portuguese (Brazilian)"
    CreateDirectory "$INSTDIR\share\locale\pt_BR\"
    SetOutPath "$INSTDIR\share\locale\pt_BR\"
    File /r "..\dist\share\locale\pt_BR\*.*"
  SectionEnd
  Section SectionTranslationRomanian "Translation Romanian"
    CreateDirectory "$INSTDIR\share\locale\ro\"
    SetOutPath "$INSTDIR\share\locale\ro\"
    File /r "..\dist\share\locale\ro\*.*"
  SectionEnd
  Section SectionTranslationRussian "Translation Russian"
    CreateDirectory "$INSTDIR\share\locale\ru\"
    SetOutPath "$INSTDIR\share\locale\ru\"
    File /r "..\dist\share\locale\ru\*.*"
  SectionEnd
  Section SectionTranslationSerbian "Translation Serbian"
    CreateDirectory "$INSTDIR\share\locale\sr\"
    SetOutPath "$INSTDIR\share\locale\sr\"
    File /r "..\dist\share\locale\sr\*.*"
  SectionEnd
  Section SectionTranslationSinhalese "Translation Sinhalese"
    CreateDirectory "$INSTDIR\share\locale\si\"
    SetOutPath "$INSTDIR\share\locale\si\"
    File /r "..\dist\share\locale\si\*.*"
  SectionEnd
  Section SectionTranslationSlovak "Translation Slovak"
    CreateDirectory "$INSTDIR\share\locale\sk\"
    SetOutPath "$INSTDIR\share\locale\sk\"
    File /r "..\dist\share\locale\sk\*.*"
  SectionEnd
  Section SectionTranslationSlovenian "Translation Slovenian"
    CreateDirectory "$INSTDIR\share\locale\sl\"
    SetOutPath "$INSTDIR\share\locale\sl\"
    File /r "..\dist\share\locale\sl\*.*"
  SectionEnd
  Section SectionTranslationSpanish "Translation Spanish"
    CreateDirectory "$INSTDIR\share\locale\es\"
    SetOutPath "$INSTDIR\share\locale\es\"
    File /r "..\dist\share\locale\es\*.*"
  SectionEnd
  Section SectionTranslationSwedish "Translation Swedish"
    CreateDirectory "$INSTDIR\share\locale\sv\"
    SetOutPath "$INSTDIR\share\locale\sv\"
    File /r "..\dist\share\locale\sv\*.*"
  SectionEnd
  Section SectionTranslationTamil "Translation Tamil"
    CreateDirectory "$INSTDIR\share\locale\ta\"
    SetOutPath "$INSTDIR\share\locale\ta\"
    File /r "..\dist\share\locale\ta\*.*"
  SectionEnd
  Section SectionTranslationTelugu "Translation Telugu"
    CreateDirectory "$INSTDIR\share\locale\te\"
    SetOutPath "$INSTDIR\share\locale\te\"
    File /r "..\dist\share\locale\te\*.*"
  SectionEnd
  Section SectionTranslationThai "Translation Thai"
    CreateDirectory "$INSTDIR\share\locale\th\"
    SetOutPath "$INSTDIR\share\locale\th\"
    File /r "..\dist\share\locale\th\*.*"
  SectionEnd
  Section SectionTranslationTurkish "Translation Turkish"
    CreateDirectory "$INSTDIR\share\locale\tr\"
    SetOutPath "$INSTDIR\share\locale\tr\"
    File /r "..\dist\share\locale\tr\*.*"
  SectionEnd
  Section SectionTranslationUkrainian "Translation Ukrainian"
    CreateDirectory "$INSTDIR\share\locale\uk\"
    SetOutPath "$INSTDIR\share\locale\uk\"
    File /r "..\dist\share\locale\uk\*.*"
  SectionEnd
  Section SectionTranslationUyghur "Translation Uyghur"
    CreateDirectory "$INSTDIR\share\locale\ug\"
    SetOutPath "$INSTDIR\share\locale\ug\"
    File /r "..\dist\share\locale\ug\*.*"
  SectionEnd
  Section SectionTranslationUzbek "Translation Uzbek"
    CreateDirectory "$INSTDIR\share\locale\uz\"
    SetOutPath "$INSTDIR\share\locale\uz\"
    File /r "..\dist\share\locale\uz\*.*"
  SectionEnd
  Section SectionTranslationVietnamese "Translation Vietnamese"
    CreateDirectory "$INSTDIR\share\locale\vi\"
    SetOutPath "$INSTDIR\share\locale\vi\"
    File /r "..\dist\share\locale\vi\*.*"
  SectionEnd
!endif
