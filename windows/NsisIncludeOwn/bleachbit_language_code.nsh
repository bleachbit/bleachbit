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

;  @app BleachBit NSIS Installer Script - Language Code File
;  @url https://nsis.sourceforge.io/Main_Page
;  @os Windows
;  @scriptversion v2.3.0.1059
;  @scriptdate 2019-04-18
;  @scriptby Tobias B. Besemer (2019-04-07 - 2019-04-18)
;  @tested ok v2.3.0.1059, Windows 7
;  @testeddate 2019-04-18
;  @testedby https://github.com/Tobias-B-Besemer
;  @note 

; MUI_LANGUAGE[EX] should be inserted after the MUI_[UN]PAGE_* macros!
; Languages additionaly available in bleachbit_lang.nsh and NsisMultiUserLang.nsh are in comments
!insertmacro MUI_LANGUAGE "English"
!ifndef NoTranslations
  !insertmacro MUI_LANGUAGE "Afrikaans"
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
  !insertmacro MUI_LANGUAGE "Esperanto"
  !insertmacro MUI_LANGUAGE "Estonian"
  !insertmacro MUI_LANGUAGE "Farsi"
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
  !insertmacro MUI_LANGUAGE "SerbianLatin"
  !insertmacro MUI_LANGUAGE "SimpChinese"
  !insertmacro MUI_LANGUAGE "Slovak"
  !insertmacro MUI_LANGUAGE "Slovenian"
  !insertmacro MUI_LANGUAGE "Spanish"
  !insertmacro MUI_LANGUAGE "SpanishInternational"
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

; License used in MUI_PAGE_LICENSE
; http://www.gnu.org/licenses/translations#GPL
; http://www.lingoes.net/en/translator/langcode.htm
; MUI_LICENSE should be inserted after the MUI_[UN]PAGE_* macros!
; Languages additionaly available in bleachbit_lang.nsh and NsisMultiUserLang.nsh are in comments
!ifdef NoTranslations
  LicenseLangString MUI_LICENSE ${LANG_ENGLISH} "..\COPYING"
!endif
!ifndef NoTranslations
  LicenseLangString MUI_LICENSE ${LANG_ENGLISH} "..\license\GPLv3_en.txt"
  LicenseLangString MUI_LICENSE ${LANG_Afrikaans} "..\COPYING"
  LicenseLangString MUI_LICENSE ${LANG_Albanian} "..\COPYING"
  LicenseLangString MUI_LICENSE ${LANG_Arabic} "..\license\GPLv3_ar.txt"
  LicenseLangString MUI_LICENSE ${LANG_Armenian} "..\COPYING"
  LicenseLangString MUI_LICENSE ${LANG_Asturian} "..\COPYING"
  LicenseLangString MUI_LICENSE ${LANG_Basque} "..\COPYING"
  LicenseLangString MUI_LICENSE ${LANG_Belarusian} "..\COPYING"
  LicenseLangString MUI_LICENSE ${LANG_Bosnian} "..\COPYING"
; LicenseLangString MUI_LICENSE ${LANG_BRETON} "..\COPYING"
  LicenseLangString MUI_LICENSE ${LANG_Bulgarian} "..\COPYING"
  LicenseLangString MUI_LICENSE ${LANG_Catalan} "..\COPYING"
; LicenseLangString MUI_LICENSE ${LANG_CORSICAN} "..\COPYING"
  LicenseLangString MUI_LICENSE ${LANG_Croatian} "..\COPYING"
  LicenseLangString MUI_LICENSE ${LANG_Czech} "..\license\GPLv3_cs.txt"
  LicenseLangString MUI_LICENSE ${LANG_Danish} "..\COPYING"
  LicenseLangString MUI_LICENSE ${LANG_Dutch} "..\COPYING"
  LicenseLangString MUI_LICENSE ${LANG_Esperanto} "..\COPYING"
  LicenseLangString MUI_LICENSE ${LANG_Estonian} "..\COPYING"
  LicenseLangString MUI_LICENSE ${LANG_Farsi} "..\COPYING"
  LicenseLangString MUI_LICENSE ${LANG_Finnish} "..\COPYING"
  LicenseLangString MUI_LICENSE ${LANG_French} "..\license\GPLv3_fr.txt"
  LicenseLangString MUI_LICENSE ${LANG_Galician} "..\COPYING"
; LicenseLangString MUI_LICENSE ${LANG_GEORGIAN} "..\COPYING"
  LicenseLangString MUI_LICENSE ${LANG_GERMAN} "..\license\GPLv3_de.txt"
  LicenseLangString MUI_LICENSE ${LANG_Greek} "..\COPYING"
  LicenseLangString MUI_LICENSE ${LANG_Hebrew} "..\COPYING"
  LicenseLangString MUI_LICENSE ${LANG_Hungarian} "..\license\GPLv3_hu.txt"
; LicenseLangString MUI_LICENSE ${LANG_ICELANDIC} "..\COPYING"
  LicenseLangString MUI_LICENSE ${LANG_Indonesian} "..\COPYING"
; LicenseLangString MUI_LICENSE ${LANG_IRISH} "..\COPYING"
  LicenseLangString MUI_LICENSE ${LANG_Italian} "..\license\GPLv3_it.txt"
  LicenseLangString MUI_LICENSE ${LANG_Japanese} "..\COPYING"
  LicenseLangString MUI_LICENSE ${LANG_Korean} "..\COPYING"
  LicenseLangString MUI_LICENSE ${LANG_Kurdish} "..\COPYING"
  LicenseLangString MUI_LICENSE ${LANG_Latvian} "..\COPYING"
  LicenseLangString MUI_LICENSE ${LANG_Lithuanian} "..\COPYING"
; LicenseLangString MUI_LICENSE ${LANG_LUXEMBOURGISH} "..\COPYING"
; LicenseLangString MUI_LICENSE ${LANG_MACEDONIAN} "..\COPYING"
  LicenseLangString MUI_LICENSE ${LANG_Malay} "..\COPYING"
; LicenseLangString MUI_LICENSE ${LANG_MONGOLIAN} "..\COPYING"
  LicenseLangString MUI_LICENSE ${LANG_Norwegian} "..\COPYING"
  LicenseLangString MUI_LICENSE ${LANG_NorwegianNynorsk} "..\COPYING"
; LicenseLangString MUI_LICENSE ${LANG_PASHTO} "..\COPYING"
  LicenseLangString MUI_LICENSE ${LANG_Polish} "..\COPYING"
  LicenseLangString MUI_LICENSE ${LANG_Portuguese} "..\COPYING"
  LicenseLangString MUI_LICENSE ${LANG_PortugueseBR} "..\license\GPLv3_pt-BR.txt"
  LicenseLangString MUI_LICENSE ${LANG_Romanian} "..\COPYING"
  LicenseLangString MUI_LICENSE ${LANG_Russian} "..\license\GPLv3_ru.txt"
; LicenseLangString MUI_LICENSE ${LANG_SCOTSGAELIC} "..\COPYING"
  LicenseLangString MUI_LICENSE ${LANG_Serbian} "..\license\GPLv3_sr.rtf"
  LicenseLangString MUI_LICENSE ${LANG_SerbianLatin} "..\COPYING"
  LicenseLangString MUI_LICENSE ${LANG_SimpChinese} "..\license\GPLv3_zh-cn.txt"
  LicenseLangString MUI_LICENSE ${LANG_Slovak} "..\license\GPLv3_sk.txt"
  LicenseLangString MUI_LICENSE ${LANG_Slovenian} "..\COPYING"
  LicenseLangString MUI_LICENSE ${LANG_Spanish} "..\COPYING"
  LicenseLangString MUI_LICENSE ${LANG_SpanishInternational} "..\COPYING"
  LicenseLangString MUI_LICENSE ${LANG_Swedish} "..\COPYING"
; LicenseLangString MUI_LICENSE ${LANG_TATAR} "..\COPYING"
  LicenseLangString MUI_LICENSE ${LANG_Thai} "..\COPYING"
  LicenseLangString MUI_LICENSE ${LANG_TradChinese} "..\license\GPLv3_zh-tw.txt"
  LicenseLangString MUI_LICENSE ${LANG_Turkish} "..\COPYING"
  LicenseLangString MUI_LICENSE ${LANG_Ukrainian} "..\COPYING"
  LicenseLangString MUI_LICENSE ${LANG_Uzbek} "..\COPYING"
  LicenseLangString MUI_LICENSE ${LANG_Vietnamese} "..\COPYING"
; LicenseLangString MUI_LICENSE ${LANG_WELSH} "..\COPYING"
!endif

!macro BB_Language_Installer_MUI_Description_Text_Translations
; https://www.omniglot.com/language/names.htm
  !insertmacro MUI_DESCRIPTION_TEXT "${Translation English (USA)}" "English (USA)"
  !ifndef NoTranslations
    !insertmacro MUI_DESCRIPTION_TEXT "${Translation Afrikaans}" "Afrikaans"
    !insertmacro MUI_DESCRIPTION_TEXT "${Translation Albanian}" "gjuha shqipe" ; Albanian
    !insertmacro MUI_DESCRIPTION_TEXT "${Translation Arabic}" "al-ʻArabīyah" ; Arabic
    !insertmacro MUI_DESCRIPTION_TEXT "${Translation Armenian}" "Hayeren lezou" ; Armenian
    !insertmacro MUI_DESCRIPTION_TEXT "${Translation Asturian}" "Asturianu" ; Asturian
    !insertmacro MUI_DESCRIPTION_TEXT "${Translation Basque}" "euskara" ; Basque
    !insertmacro MUI_DESCRIPTION_TEXT "${Translation Belarusian}" "Bielaruskaja mova" ; Belarusian
    !insertmacro MUI_DESCRIPTION_TEXT "${Translation Bengali}" "baɛṅlā" ; Bengali
    !insertmacro MUI_DESCRIPTION_TEXT "${Translation Bosnian}" "bosanski" ; Bosnian
    !insertmacro MUI_DESCRIPTION_TEXT "${Translation Bulgarian}" "bãlgarski" ; Bulgarian
    !insertmacro MUI_DESCRIPTION_TEXT "${Translation Burmese}" "bama saka" ; Burmese
    !insertmacro MUI_DESCRIPTION_TEXT "${Translation Catalan}" "català" ; Catalan
    !insertmacro MUI_DESCRIPTION_TEXT "${Translation Chinese (Simplified)}" "zhōngwén (Simplified)" ; Chinese (Simplified)
    !insertmacro MUI_DESCRIPTION_TEXT "${Translation Chinese (Traditional)}" "zhōngwén (Traditional)" ; Chinese (Traditional)
    !insertmacro MUI_DESCRIPTION_TEXT "${Translation Croatian}" "Hrvatski" ; Croatian
    !insertmacro MUI_DESCRIPTION_TEXT "${Translation Czech}" "čeština" ; Czech
    !insertmacro MUI_DESCRIPTION_TEXT "${Translation Danish}" "dansk" ; Danish
    !insertmacro MUI_DESCRIPTION_TEXT "${Translation Dutch}" "Nederlands" ; Dutch
    !insertmacro MUI_DESCRIPTION_TEXT "${Translation English (Australia)}" "English (Australia)"
    !insertmacro MUI_DESCRIPTION_TEXT "${Translation English (Canada)}" "English (Canada)"
    !insertmacro MUI_DESCRIPTION_TEXT "${Translation English (United Kingdom)}" "English (United Kingdom)"
    !insertmacro MUI_DESCRIPTION_TEXT "${Translation Esperanto}" "Esperanto"
    !insertmacro MUI_DESCRIPTION_TEXT "${Translation Estonian}" "eesti keel" ; Estonian
    !insertmacro MUI_DESCRIPTION_TEXT "${Translation Faroese}" "Føroyskt" ; Faroese
    !insertmacro MUI_DESCRIPTION_TEXT "${Translation Finnish}" "suomen kieli" ; Finnish
    !insertmacro MUI_DESCRIPTION_TEXT "${Translation French}" "français" ; French
    !insertmacro MUI_DESCRIPTION_TEXT "${Translation Galician}" "Galego" ; Galician
    !insertmacro MUI_DESCRIPTION_TEXT "${Translation German}" "Deutsch" ; German
    !insertmacro MUI_DESCRIPTION_TEXT "${Translation Greek}" "ellēniká" ; Greek
    !insertmacro MUI_DESCRIPTION_TEXT "${Translation Hebrew}" "ivrit" ; Hebrew
    !insertmacro MUI_DESCRIPTION_TEXT "${Translation Hindi}" "hindī" ; Hindi
    !insertmacro MUI_DESCRIPTION_TEXT "${Translation Hungarian}" "magyar nyelv" ; Hungarian
    !insertmacro MUI_DESCRIPTION_TEXT "${Translation Indonesian}" "Bahasa Indonesia" ; Indonesian
    !insertmacro MUI_DESCRIPTION_TEXT "${Translation Interlingua}" "Interlingua"
    !insertmacro MUI_DESCRIPTION_TEXT "${Translation Italian}" "italiano" ; Italian
    !insertmacro MUI_DESCRIPTION_TEXT "${Translation Japanese}" "nihongo" ; Japanese
    !insertmacro MUI_DESCRIPTION_TEXT "${Translation Kirghiz}" "Kirghiz"
    !insertmacro MUI_DESCRIPTION_TEXT "${Translation Korean}" "han-guk-eo" ; Korean
    !insertmacro MUI_DESCRIPTION_TEXT "${Translation Kurdish}" "Kurdí" ; Kurdish
    !insertmacro MUI_DESCRIPTION_TEXT "${Translation Latvian}" "latviešu valoda" ; Latvian
    !insertmacro MUI_DESCRIPTION_TEXT "${Translation Lithuanian}" "lietuvių kalba"; Lithuanian
    !insertmacro MUI_DESCRIPTION_TEXT "${Translation Low German}" "Plattdeutsch" ; Low German
    !insertmacro MUI_DESCRIPTION_TEXT "${Translation Malay}" "Bahasa melayu" ; Malay
    !insertmacro MUI_DESCRIPTION_TEXT "${Translation Northern Sami}" "davvisámegiella" ; Northern Sami
    !insertmacro MUI_DESCRIPTION_TEXT "${Translation Norwegian Bokmal}" "norsk Bokmal" ; Norwegian Bokmal
    !insertmacro MUI_DESCRIPTION_TEXT "${Translation Norwegian Nynorsk}" "norsk Nynorsk" ; Norwegian Nynorsk
    !insertmacro MUI_DESCRIPTION_TEXT "${Translation Persian}" "fārsī" ; Persian/Farsi
    !insertmacro MUI_DESCRIPTION_TEXT "${Translation Polish}" "polski" ; Polish
    !insertmacro MUI_DESCRIPTION_TEXT "${Translation Portuguese}" "português" ; Portuguese
    !insertmacro MUI_DESCRIPTION_TEXT "${Translation Portuguese (Brazilian)}" "português (Brazilian)" ; Portuguese (Brazilian)
    !insertmacro MUI_DESCRIPTION_TEXT "${Translation Romanian}" "român" ; Romanian
    !insertmacro MUI_DESCRIPTION_TEXT "${Translation Russian}" "Russkij jazyk" ; Russian
    !insertmacro MUI_DESCRIPTION_TEXT "${Translation Serbian}" "srpski" ; Serbian
    !insertmacro MUI_DESCRIPTION_TEXT "${Translation Sinhalese}" "Sinhalese"
    !insertmacro MUI_DESCRIPTION_TEXT "${Translation Slovak}" "slovenčina" ; Slovak
    !insertmacro MUI_DESCRIPTION_TEXT "${Translation Slovenian}" "slovenščina" ; Slovenian
    !insertmacro MUI_DESCRIPTION_TEXT "${Translation Spanish}" "español" ; Spanish
    !insertmacro MUI_DESCRIPTION_TEXT "${Translation Swedish}" "svenska" ; Swedish
    !insertmacro MUI_DESCRIPTION_TEXT "${Translation Tamil}" "tamiḻ" ; Tamil
    !insertmacro MUI_DESCRIPTION_TEXT "${Translation Telugu}" "telugu" ; Telugu
    !insertmacro MUI_DESCRIPTION_TEXT "${Translation Thai}" "paasaa-tai" ; Thai
    !insertmacro MUI_DESCRIPTION_TEXT "${Translation Turkish}" "Türkçe" ; Turkish
    !insertmacro MUI_DESCRIPTION_TEXT "${Translation Ukrainian}" "Ukrajins'ka" ; Ukrainian
    !insertmacro MUI_DESCRIPTION_TEXT "${Translation Uyghur}" "Uyghurche" ; Uyghur
    !insertmacro MUI_DESCRIPTION_TEXT "${Translation Uzbek}" "o‘zbek tili" ; Uzbek
    !insertmacro MUI_DESCRIPTION_TEXT "${Translation Vietnamese}" "tiếng việt" ; Vietnamese
!endif
!macroend

!macro BB_Language_Installer_SectionSetText
  ; To access the section index, curly brackets must be used and the code must be located below the section in the script.
  ; -> Place Functions below the Sections!
  SectionSetText "${Core}" $(BLEACHBIT_COMPONENT_CORE_TITLE)
  SectionSetText "${Group Cleaners}" $(BLEACHBIT_COMPONENTGROUP_CLEANERS_TITLE)
  SectionSetText "${Cleaners Stable}" "Stable"
  !ifdef BetaTester
    SectionSetText "${Cleaners Beta}" "Beta"
    !ifdef AlphaTester
      SectionSetText "${Cleaners Alpha}" "Alpha"
    !endif
  !endif
  SectionSetText "${Installer}" $(BLEACHBIT_COMPONENT_INSTALLER_TITLE)
  SectionSetText "${Group Shortcuts}" $(BLEACHBIT_COMPONENTGROUP_SHORTCUTS_TITLE)
  SectionSetText "${Shortcuts Start Menu}" $(BLEACHBIT_COMPONENT_SHORTCUTS_STARTMENU_TITLE)
  SectionSetText "${Shortcut Desktop}" $(BLEACHBIT_COMPONENT_SHORTCUTS_DESKTOP_TITLE)
  SectionSetText "${Shortcut Quick Launch}" $(BLEACHBIT_COMPONENT_SHORTCUTS_QUICKLAUNCH_TITLE)
  SectionSetText "${Shortcut Autostart}" $(BLEACHBIT_COMPONENT_SHORTCUTS_AUTOSTART_TITLE)
  SectionSetText "${Group Translations}" $(BLEACHBIT_COMPONENTGROUP_TRANSLATIONS_TITLE)
  ; https://www.omniglot.com/language/names.htm
  SectionSetText "${Translation English (USA)}" "English (USA)"
  !ifndef NoTranslations
    SectionSetText "${Translation Afrikaans}" "Afrikaans"
    SectionSetText "${Translation Albanian}" "gjuha shqipe" ; Albanian
    SectionSetText "${Translation Arabic}" "al-ʻArabīyah" ; Arabic
    SectionSetText "${Translation Armenian}" "Hayeren lezou" ; Armenian
    SectionSetText "${Translation Asturian}" "Asturianu" ; Asturian
    SectionSetText "${Translation Basque}" "euskara" ; Basque
    SectionSetText "${Translation Belarusian}" "Bielaruskaja mova" ; Belarusian
    SectionSetText "${Translation Bengali}" "baɛṅlā" ; Bengali
    SectionSetText "${Translation Bosnian}" "bosanski" ; Bosnian
    SectionSetText "${Translation Bulgarian}" "bãlgarski" ; Bulgarian
    SectionSetText "${Translation Burmese}" "bama saka" ; Burmese
    SectionSetText "${Translation Catalan}" "català" ; Catalan
    SectionSetText "${Translation Chinese (Simplified)}" "zhōngwén (Simplified)" ; Chinese (Simplified)
    SectionSetText "${Translation Chinese (Traditional)}" "zhōngwén (Traditional)" ; Chinese (Traditional)
    SectionSetText "${Translation Croatian}" "Hrvatski" ; Croatian
    SectionSetText "${Translation Czech}" "čeština" ; Czech
    SectionSetText "${Translation Danish}" "dansk" ; Danish
    SectionSetText "${Translation Dutch}" "Nederlands" ; Dutch
    SectionSetText "${Translation English (Australia)}" "English (Australia)"
    SectionSetText "${Translation English (Canada)}" "English (Canada)"
    SectionSetText "${Translation English (United Kingdom)}" "English (United Kingdom)"
    SectionSetText "${Translation Esperanto}" "Esperanto"
    SectionSetText "${Translation Estonian}" "eesti keel" ; Estonian
    SectionSetText "${Translation Faroese}" "Føroyskt" ; Faroese
    SectionSetText "${Translation Finnish}" "suomen kieli" ; Finnish
    SectionSetText "${Translation French}" "français" ; French
    SectionSetText "${Translation Galician}" "Galego" ; Galician
    SectionSetText "${Translation German}" "Deutsch" ; German
    SectionSetText "${Translation Greek}" "ellēniká" ; Greek
    SectionSetText "${Translation Hebrew}" "ivrit" ; Hebrew
    SectionSetText "${Translation Hindi}" "hindī" ; Hindi
    SectionSetText "${Translation Hungarian}" "magyar nyelv" ; Hungarian
    SectionSetText "${Translation Indonesian}" "Bahasa Indonesia" ; Indonesian
    SectionSetText "${Translation Interlingua}" "Interlingua"
    SectionSetText "${Translation Italian}" "italiano" ; Italian
    SectionSetText "${Translation Japanese}" "nihongo" ; Japanese
    SectionSetText "${Translation Kirghiz}" "Kirghiz"
    SectionSetText "${Translation Korean}" "han-guk-eo" ; Korean
    SectionSetText "${Translation Kurdish}" "Kurdí" ; Kurdish
    SectionSetText "${Translation Latvian}" "latviešu valoda" ; Latvian
    SectionSetText "${Translation Lithuanian}" "lietuvių kalba"; Lithuanian
    SectionSetText "${Translation Low German}" "Plattdeutsch" ; Low German
    SectionSetText "${Translation Malay}" "Bahasa melayu" ; Malay
    SectionSetText "${Translation Northern Sami}" "davvisámegiella" ; Northern Sami
    SectionSetText "${Translation Norwegian Bokmal}" "norsk Bokmal" ; Norwegian Bokmal
    SectionSetText "${Translation Norwegian Nynorsk}" "norsk Nynorsk" ; Norwegian Nynorsk
    SectionSetText "${Translation Persian}" "fārsī" ; Persian/Farsi
    SectionSetText "${Translation Polish}" "polski" ; Polish
    SectionSetText "${Translation Portuguese}" "português" ; Portuguese
    SectionSetText "${Translation Portuguese (Brazilian)}" "português (Brazilian)" ; Portuguese (Brazilian)
    SectionSetText "${Translation Romanian}" "român" ; Romanian
    SectionSetText "${Translation Russian}" "Russkij jazyk" ; Russian
    SectionSetText "${Translation Serbian}" "srpski" ; Serbian
    SectionSetText "${Translation Sinhalese}" "Sinhalese"
    SectionSetText "${Translation Slovak}" "slovenčina" ; Slovak
    SectionSetText "${Translation Slovenian}" "slovenščina" ; Slovenian
    SectionSetText "${Translation Spanish}" "español" ; Spanish
    SectionSetText "${Translation Swedish}" "svenska" ; Swedish
    SectionSetText "${Translation Tamil}" "tamiḻ" ; Tamil
    SectionSetText "${Translation Telugu}" "telugu" ; Telugu
    SectionSetText "${Translation Thai}" "paasaa-tai" ; Thai
    SectionSetText "${Translation Turkish}" "Türkçe" ; Turkish
    SectionSetText "${Translation Ukrainian}" "Ukrajins'ka" ; Ukrainian
    SectionSetText "${Translation Uyghur}" "Uyghurche" ; Uyghur
    SectionSetText "${Translation Uzbek}" "o‘zbek tili" ; Uzbek
    SectionSetText "${Translation Vietnamese}" "tiếng việt" ; Vietnamese
  !endif
  !ifndef NoSectionShred
    SectionSetText "${Shred for Explorer}" $(BLEACHBIT_COMPONENT_SHREDFOREXPLORER_TITLE)
  !endif
!macroend

!macro BB_Language_Installer_SetSectionInInstType_Translations
  !insertmacro SetSectionInInstType "${Translation English (USA)}" "${INSTTYPE_1}"
  !insertmacro SetSectionInInstType "${Translation English (USA)}" "${INSTTYPE_2}"
  !insertmacro SetSectionInInstType "${Translation English (USA)}" "${INSTTYPE_3}"
  !ifndef NoTranslations
    ; https://docs.oracle.com/cd/E13214_01/wli/docs92/xref/xqisocodes.html#wp1252447
    !insertmacro SetSectionInInstType "${Translation Afrikaans}" "${INSTTYPE_1}"
    ${If} $Language == ${LANG_Afrikaans}
      !insertmacro SetSectionInInstType "${Translation Afrikaans}" "${INSTTYPE_2}"
    ${EndIf}
    !insertmacro SetSectionInInstType "${Translation Albanian}" "${INSTTYPE_1}"
    ${If} $Language == ${LANG_Albanian}
      !insertmacro SetSectionInInstType "${Translation Albanian}" "${INSTTYPE_2}"
    ${EndIf}
    !insertmacro SetSectionInInstType "${Translation Arabic}" "${INSTTYPE_1}"
    ${If} $Language == ${LANG_Arabic}
      !insertmacro SetSectionInInstType "${Translation Arabic}" "${INSTTYPE_2}"
    ${EndIf}
    !insertmacro SetSectionInInstType "${Translation Armenian}" "${INSTTYPE_1}"
    ${If} $Language == ${LANG_Armenian}
      !insertmacro SetSectionInInstType "${Translation Armenian}" "${INSTTYPE_2}"
    ${EndIf}
    !insertmacro SetSectionInInstType "${Translation Asturian}" "${INSTTYPE_1}"
    ${If} $Language == ${LANG_Asturian}
      !insertmacro SetSectionInInstType "${Translation Asturian}" "${INSTTYPE_2}"
    ${EndIf}
    !insertmacro SetSectionInInstType "${Translation Basque}" "${INSTTYPE_1}"
    ${If} $Language == ${LANG_Basque}
      !insertmacro SetSectionInInstType "${Translation Basque}" "${INSTTYPE_2}"
    ${EndIf}
    !insertmacro SetSectionInInstType "${Translation Belarusian}" "${INSTTYPE_1}"
    ${If} $Language == ${LANG_Belarusian}
      !insertmacro SetSectionInInstType "${Translation Belarusian}" "${INSTTYPE_2}"
    ${EndIf}
    !insertmacro SetSectionInInstType "${Translation Bengali}" "${INSTTYPE_1}"
    !insertmacro SetSectionInInstType "${Translation Bosnian}" "${INSTTYPE_1}"
    ${If} $Language == ${LANG_Bosnian}
      !insertmacro SetSectionInInstType "${Translation Bosnian}" "${INSTTYPE_2}"
    ${EndIf}
    !insertmacro SetSectionInInstType "${Translation Bulgarian}" "${INSTTYPE_1}"
    ${If} $Language == ${LANG_Bulgarian}
      !insertmacro SetSectionInInstType "${Translation Bulgarian}" "${INSTTYPE_2}"
    ${EndIf}
    !insertmacro SetSectionInInstType "${Translation Burmese}" "${INSTTYPE_1}"
    !insertmacro SetSectionInInstType "${Translation Catalan}" "${INSTTYPE_1}"
    ${If} $Language == ${LANG_Catalan}
      !insertmacro SetSectionInInstType "${Translation Catalan}" "${INSTTYPE_2}"
    ${EndIf}
    !insertmacro SetSectionInInstType "${Translation Chinese (Simplified)}" "${INSTTYPE_1}"
    !insertmacro SetSectionInInstType "${Translation Chinese (Traditional)}" "${INSTTYPE_1}"
    !insertmacro SetSectionInInstType "${Translation Croatian}" "${INSTTYPE_1}"
    ${If} $Language == ${LANG_Croatian}
      !insertmacro SetSectionInInstType "${Translation Croatian}" "${INSTTYPE_2}"
    ${EndIf}
    !insertmacro SetSectionInInstType "${Translation Czech}" "${INSTTYPE_1}"
    ${If} $Language == ${LANG_Czech}
      !insertmacro SetSectionInInstType "${Translation Czech}" "${INSTTYPE_2}"
    ${EndIf}
    !insertmacro SetSectionInInstType "${Translation Danish}" "${INSTTYPE_1}"
    ${If} $Language == ${LANG_Danish}
      !insertmacro SetSectionInInstType "${Translation Danish}" "${INSTTYPE_2}"
    ${EndIf}
    !insertmacro SetSectionInInstType "${Translation Dutch}" "${INSTTYPE_1}"
    ${If} $Language == ${LANG_Dutch}
      !insertmacro SetSectionInInstType "${Translation Dutch}" "${INSTTYPE_2}"
    ${EndIf}
    !insertmacro SetSectionInInstType "${Translation English (Australia)}" "${INSTTYPE_1}"
    !insertmacro SetSectionInInstType "${Translation English (Canada)}" "${INSTTYPE_1}"
    !insertmacro SetSectionInInstType "${Translation English (United Kingdom)}" "${INSTTYPE_1}"
    !insertmacro SetSectionInInstType "${Translation Esperanto}" "${INSTTYPE_1}"
    ${If} $Language == ${LANG_ESPERANTO}
      !insertmacro SetSectionInInstType "${Translation Esperanto}" "${INSTTYPE_2}"
    ${EndIf}
    !insertmacro SetSectionInInstType "${Translation Estonian}" "${INSTTYPE_1}"
    ${If} $Language == ${LANG_Estonian}
      !insertmacro SetSectionInInstType "${Translation Estonian}" "${INSTTYPE_2}"
    ${EndIf}
    !insertmacro SetSectionInInstType "${Translation Faroese}" "${INSTTYPE_1}"
    !insertmacro SetSectionInInstType "${Translation Finnish}" "${INSTTYPE_1}"
    ${If} $Language == ${LANG_Finnish}
      !insertmacro SetSectionInInstType "${Translation Finnish}" "${INSTTYPE_2}"
    ${EndIf}
    !insertmacro SetSectionInInstType "${Translation French}" "${INSTTYPE_1}"
    ${If} $Language == ${LANG_FRENCH}
      !insertmacro SetSectionInInstType "${Translation French}" "${INSTTYPE_2}"
    ${EndIf}
    !insertmacro SetSectionInInstType "${Translation Galician}" "${INSTTYPE_1}"
    ${If} $Language == ${LANG_Galician}
      !insertmacro SetSectionInInstType "${Translation Galician}" "${INSTTYPE_2}"
    ${EndIf}
    !insertmacro SetSectionInInstType "${Translation German}" "${INSTTYPE_1}"
    ${If} $Language == ${LANG_German}
      !insertmacro SetSectionInInstType "${Translation German}" "${INSTTYPE_2}"
    ${EndIf}
    !insertmacro SetSectionInInstType "${Translation Greek}" "${INSTTYPE_1}"
    ${If} $Language == ${LANG_Greek}
      !insertmacro SetSectionInInstType "${Translation Greek}" "${INSTTYPE_2}"
    ${EndIf}
    !insertmacro SetSectionInInstType "${Translation Hebrew}" "${INSTTYPE_1}"
    ${If} $Language == ${LANG_Hebrew}
      !insertmacro SetSectionInInstType "${Translation Hebrew}" "${INSTTYPE_2}"
    ${EndIf}
    !insertmacro SetSectionInInstType "${Translation Hindi}" "${INSTTYPE_1}"
    !insertmacro SetSectionInInstType "${Translation Hungarian}" "${INSTTYPE_1}"
    ${If} $Language == ${LANG_Hungarian}
      !insertmacro SetSectionInInstType "${Translation Hungarian}" "${INSTTYPE_2}"
    ${EndIf}
    !insertmacro SetSectionInInstType "${Translation Indonesian}" "${INSTTYPE_1}"
    ${If} $Language == ${LANG_Indonesian}
      !insertmacro SetSectionInInstType "${Translation Indonesian}" "${INSTTYPE_2}"
    ${EndIf}
    !insertmacro SetSectionInInstType "${Translation Interlingua}" "${INSTTYPE_1}"
    !insertmacro SetSectionInInstType "${Translation Italian}" "${INSTTYPE_1}"
    ${If} $Language == ${LANG_Italian}
      !insertmacro SetSectionInInstType "${Translation Italian}" "${INSTTYPE_2}"
    ${EndIf}
    !insertmacro SetSectionInInstType "${Translation Japanese}" "${INSTTYPE_1}"
    ${If} $Language == ${LANG_Japanese}
      !insertmacro SetSectionInInstType "${Translation Japanese}" "${INSTTYPE_2}"
    ${EndIf}
    !insertmacro SetSectionInInstType "${Translation Kirghiz}" "${INSTTYPE_1}"
    !insertmacro SetSectionInInstType "${Translation Korean}" "${INSTTYPE_1}"
    ${If} $Language == ${LANG_Korean}
      !insertmacro SetSectionInInstType "${Translation Korean}" "${INSTTYPE_2}"
    ${EndIf}
    !insertmacro SetSectionInInstType "${Translation Kurdish}" "${INSTTYPE_1}"
    ${If} $Language == ${LANG_Kurdish}
      !insertmacro SetSectionInInstType "${Translation Kurdish}" "${INSTTYPE_2}"
    ${EndIf}
    !insertmacro SetSectionInInstType "${Translation Latvian}" "${INSTTYPE_1}"
    ${If} $Language == ${LANG_Latvian}
      !insertmacro SetSectionInInstType "${Translation Latvian}" "${INSTTYPE_2}"
    ${EndIf}
    !insertmacro SetSectionInInstType "${Translation Lithuanian}" "${INSTTYPE_1}"
    ${If} $Language == ${LANG_Lithuanian}
      !insertmacro SetSectionInInstType "${Translation Lithuanian}" "${INSTTYPE_2}"
    ${EndIf}
    !insertmacro SetSectionInInstType "${Translation Low German}" "${INSTTYPE_1}"
    !insertmacro SetSectionInInstType "${Translation Malay}" "${INSTTYPE_1}"
    ${If} $Language == ${LANG_Malay}
      !insertmacro SetSectionInInstType "${Translation Malay}" "${INSTTYPE_2}"
    ${EndIf}
    !insertmacro SetSectionInInstType "${Translation Northern Sami}" "${INSTTYPE_1}"
    !insertmacro SetSectionInInstType "${Translation Norwegian Bokmal}" "${INSTTYPE_1}"
    ${If} $Language == ${LANG_Norwegian}
      !insertmacro SetSectionInInstType "${Translation Norwegian Bokmal}" "${INSTTYPE_2}"
    ${EndIf}
    !insertmacro SetSectionInInstType "${Translation Norwegian Nynorsk}" "${INSTTYPE_1}"
    ${If} $Language == ${LANG_NorwegianNynorsk}
      !insertmacro SetSectionInInstType "${Translation Norwegian Nynorsk}" "${INSTTYPE_2}"
    ${EndIf}
    !insertmacro SetSectionInInstType "${Translation Persian}" "${INSTTYPE_1}"
    ${If} $Language == ${LANG_Farsi}
      !insertmacro SetSectionInInstType "${Translation Persian}" "${INSTTYPE_2}"
    ${EndIf}
    !insertmacro SetSectionInInstType "${Translation Polish}" "${INSTTYPE_1}"
    ${If} $Language == ${LANG_Polish}
      !insertmacro SetSectionInInstType "${Translation Polish}" "${INSTTYPE_2}"
    ${EndIf}
    !insertmacro SetSectionInInstType "${Translation Portuguese}" "${INSTTYPE_1}"
    ${If} $Language == ${LANG_Portuguese}
      !insertmacro SetSectionInInstType "${Translation Portuguese}" "${INSTTYPE_2}"
    ${EndIf}
    !insertmacro SetSectionInInstType "${Translation Portuguese (Brazilian)}" "${INSTTYPE_1}"
    ${If} $Language == ${LANG_PortugueseBR}
      !insertmacro SetSectionInInstType "${Translation Portuguese (Brazilian)}" "${INSTTYPE_2}"
    ${EndIf}
    !insertmacro SetSectionInInstType "${Translation Romanian}" "${INSTTYPE_1}"
    ${If} $Language == ${LANG_Romanian}
      !insertmacro SetSectionInInstType "${Translation Romanian}" "${INSTTYPE_2}"
    ${EndIf}
    !insertmacro SetSectionInInstType "${Translation Russian}" "${INSTTYPE_1}"
    ${If} $Language == ${LANG_Russian}
      !insertmacro SetSectionInInstType "${Translation Russian}" "${INSTTYPE_2}"
    ${EndIf}
    !insertmacro SetSectionInInstType "${Translation Serbian}" "${INSTTYPE_1}"
    ${If} $Language == ${LANG_Serbian}
      !insertmacro SetSectionInInstType "${Translation Serbian}" "${INSTTYPE_2}"
    ${EndIf}
    !insertmacro SetSectionInInstType "${Translation Sinhalese}" "${INSTTYPE_1}"
    !insertmacro SetSectionInInstType "${Translation Slovak}" "${INSTTYPE_1}"
    ${If} $Language == ${LANG_Slovak}
      !insertmacro SetSectionInInstType "${Translation Slovak}" "${INSTTYPE_2}"
    ${EndIf}
    !insertmacro SetSectionInInstType "${Translation Slovenian}" "${INSTTYPE_1}"
    ${If} $Language == ${LANG_Slovenian}
      !insertmacro SetSectionInInstType "${Translation Slovenian}" "${INSTTYPE_2}"
    ${EndIf}
    !insertmacro SetSectionInInstType "${Translation Spanish}" "${INSTTYPE_1}"
    ${If} $Language == ${LANG_Spanish}
      !insertmacro SetSectionInInstType "${Translation Spanish}" "${INSTTYPE_2}"
    ${EndIf}
    !insertmacro SetSectionInInstType "${Translation Swedish}" "${INSTTYPE_1}"
    ${If} $Language == ${LANG_Swedish}
      !insertmacro SetSectionInInstType "${Translation Swedish}" "${INSTTYPE_2}"
    ${EndIf}
    !insertmacro SetSectionInInstType "${Translation Tamil}" "${INSTTYPE_1}"
    !insertmacro SetSectionInInstType "${Translation Telugu}" "${INSTTYPE_1}"
    !insertmacro SetSectionInInstType "${Translation Thai}" "${INSTTYPE_1}"
    ${If} $Language == ${LANG_Thai}
      !insertmacro SetSectionInInstType "${Translation Thai}" "${INSTTYPE_2}"
    ${EndIf}
    !insertmacro SetSectionInInstType "${Translation Turkish}" "${INSTTYPE_1}"
    ${If} $Language == ${LANG_Turkish}
      !insertmacro SetSectionInInstType "${Translation Turkish}" "${INSTTYPE_2}"
    ${EndIf}
    !insertmacro SetSectionInInstType "${Translation Ukrainian}" "${INSTTYPE_1}"
    ${If} $Language == ${LANG_Ukrainian}
      !insertmacro SetSectionInInstType "${Translation Ukrainian}" "${INSTTYPE_2}"
    ${EndIf}
    !insertmacro SetSectionInInstType "${Translation Uyghur}" "${INSTTYPE_1}"
    !insertmacro SetSectionInInstType "${Translation Uzbek}" "${INSTTYPE_1}"
    ${If} $Language == ${LANG_Uzbek}
      !insertmacro SetSectionInInstType "${Translation Uzbek}" "${INSTTYPE_2}"
    ${EndIf}
    !insertmacro SetSectionInInstType "${Translation Vietnamese}" "${INSTTYPE_1}"
    ${If} $Language == ${LANG_Vietnamese}
      !insertmacro SetSectionInInstType "${Translation Vietnamese}" "${INSTTYPE_2}"
    ${EndIf}
!endif
!macroend

!macro BB_Language_UnInstaller_MUI_Description_Text_Translations
; https://www.omniglot.com/language/names.htm
  !insertmacro MUI_DESCRIPTION_TEXT "${un.Translation English (USA)}" "English (USA)"
  !ifndef NoTranslations
    ; https://docs.oracle.com/cd/E13214_01/wli/docs92/xref/xqisocodes.html#wp1252447
    !insertmacro MUI_DESCRIPTION_TEXT "${un.Translation Afrikaans}" "Afrikaans"
    !insertmacro MUI_DESCRIPTION_TEXT "${un.Translation Albanian}" "gjuha shqipe" ; Albanian
    !insertmacro MUI_DESCRIPTION_TEXT "${un.Translation Arabic}" "al-ʻArabīyah" ; Arabic
    !insertmacro MUI_DESCRIPTION_TEXT "${un.Translation Armenian}" "Hayeren lezou" ; Armenian
    !insertmacro MUI_DESCRIPTION_TEXT "${un.Translation Asturian}" "Asturianu" ; Asturian
    !insertmacro MUI_DESCRIPTION_TEXT "${un.Translation Basque}" "euskara" ; Basque
    !insertmacro MUI_DESCRIPTION_TEXT "${un.Translation Belarusian}" "Bielaruskaja mova" ; Belarusian
    !insertmacro MUI_DESCRIPTION_TEXT "${un.Translation Bengali}" "baɛṅlā" ; Bengali
    !insertmacro MUI_DESCRIPTION_TEXT "${un.Translation Bosnian}" "bosanski" ; Bosnian
    !insertmacro MUI_DESCRIPTION_TEXT "${un.Translation Bulgarian}" "bãlgarski" ; Bulgarian
    !insertmacro MUI_DESCRIPTION_TEXT "${un.Translation Burmese}" "bama saka" ; Burmese
    !insertmacro MUI_DESCRIPTION_TEXT "${un.Translation Catalan}" "català" ; Catalan
    !insertmacro MUI_DESCRIPTION_TEXT "${un.Translation Chinese (Simplified)}" "zhōngwén (Simplified)" ; Chinese (Simplified)
    !insertmacro MUI_DESCRIPTION_TEXT "${un.Translation Chinese (Traditional)}" "zhōngwén (Traditional)" ; Chinese (Traditional)
    !insertmacro MUI_DESCRIPTION_TEXT "${un.Translation Croatian}" "Hrvatski" ; Croatian
    !insertmacro MUI_DESCRIPTION_TEXT "${un.Translation Czech}" "čeština" ; Czech
    !insertmacro MUI_DESCRIPTION_TEXT "${un.Translation Danish}" "dansk" ; Danish
    !insertmacro MUI_DESCRIPTION_TEXT "${un.Translation Dutch}" "Nederlands" ; Dutch
    !insertmacro MUI_DESCRIPTION_TEXT "${un.Translation English (Australia)}" "English (Australia)"
    !insertmacro MUI_DESCRIPTION_TEXT "${un.Translation English (Canada)}" "English (Canada)"
    !insertmacro MUI_DESCRIPTION_TEXT "${un.Translation English (United Kingdom)}" "English (United Kingdom)"
    !insertmacro MUI_DESCRIPTION_TEXT "${un.Translation Esperanto}" "Esperanto"
    !insertmacro MUI_DESCRIPTION_TEXT "${un.Translation Estonian}" "eesti keel" ; Estonian
    !insertmacro MUI_DESCRIPTION_TEXT "${un.Translation Faroese}" "Føroyskt" ; Faroese
    !insertmacro MUI_DESCRIPTION_TEXT "${un.Translation Finnish}" "suomen kieli" ; Finnish
    !insertmacro MUI_DESCRIPTION_TEXT "${un.Translation French}" "français" ; French
    !insertmacro MUI_DESCRIPTION_TEXT "${un.Translation Galician}" "Galego" ; Galician
    !insertmacro MUI_DESCRIPTION_TEXT "${un.Translation German}" "Deutsch" ; German
    !insertmacro MUI_DESCRIPTION_TEXT "${un.Translation Greek}" "ellēniká" ; Greek
    !insertmacro MUI_DESCRIPTION_TEXT "${un.Translation Hebrew}" "ivrit" ; Hebrew
    !insertmacro MUI_DESCRIPTION_TEXT "${un.Translation Hindi}" "hindī" ; Hindi
    !insertmacro MUI_DESCRIPTION_TEXT "${un.Translation Hungarian}" "magyar nyelv" ; Hungarian
    !insertmacro MUI_DESCRIPTION_TEXT "${un.Translation Indonesian}" "Bahasa Indonesia" ; Indonesian
    !insertmacro MUI_DESCRIPTION_TEXT "${un.Translation Interlingua}" "Interlingua"
    !insertmacro MUI_DESCRIPTION_TEXT "${un.Translation Italian}" "italiano" ; Italian
    !insertmacro MUI_DESCRIPTION_TEXT "${un.Translation Japanese}" "nihongo" ; Japanese
    !insertmacro MUI_DESCRIPTION_TEXT "${un.Translation Kirghiz}" "Kirghiz"
    !insertmacro MUI_DESCRIPTION_TEXT "${un.Translation Korean}" "han-guk-eo" ; Korean
    !insertmacro MUI_DESCRIPTION_TEXT "${un.Translation Kurdish}" "Kurdí" ; Kurdish
    !insertmacro MUI_DESCRIPTION_TEXT "${un.Translation Latvian}" "latviešu valoda" ; Latvian
    !insertmacro MUI_DESCRIPTION_TEXT "${un.Translation Lithuanian}" "lietuvių kalba"; Lithuanian
    !insertmacro MUI_DESCRIPTION_TEXT "${un.Translation Low German}" "Plattdeutsch" ; Low German
    !insertmacro MUI_DESCRIPTION_TEXT "${un.Translation Malay}" "Bahasa melayu" ; Malay
    !insertmacro MUI_DESCRIPTION_TEXT "${un.Translation Northern Sami}" "davvisámegiella" ; Northern Sami
    !insertmacro MUI_DESCRIPTION_TEXT "${un.Translation Norwegian Bokmal}" "norsk Bokmal" ; Norwegian Bokmal
    !insertmacro MUI_DESCRIPTION_TEXT "${un.Translation Norwegian Nynorsk}" "norsk Nynorsk" ; Norwegian Nynorsk
    !insertmacro MUI_DESCRIPTION_TEXT "${un.Translation Persian}" "fārsī" ; Persian/Farsi
    !insertmacro MUI_DESCRIPTION_TEXT "${un.Translation Polish}" "polski" ; Polish
    !insertmacro MUI_DESCRIPTION_TEXT "${un.Translation Portuguese}" "português" ; Portuguese
    !insertmacro MUI_DESCRIPTION_TEXT "${un.Translation Portuguese (Brazilian)}" "português (Brazilian)" ; Portuguese (Brazilian)
    !insertmacro MUI_DESCRIPTION_TEXT "${un.Translation Romanian}" "român" ; Romanian
    !insertmacro MUI_DESCRIPTION_TEXT "${un.Translation Russian}" "Russkij jazyk" ; Russian
    !insertmacro MUI_DESCRIPTION_TEXT "${un.Translation Serbian}" "srpski" ; Serbian
    !insertmacro MUI_DESCRIPTION_TEXT "${un.Translation Sinhalese}" "Sinhalese"
    !insertmacro MUI_DESCRIPTION_TEXT "${un.Translation Slovak}" "slovenčina" ; Slovak
    !insertmacro MUI_DESCRIPTION_TEXT "${un.Translation Slovenian}" "slovenščina" ; Slovenian
    !insertmacro MUI_DESCRIPTION_TEXT "${un.Translation Spanish}" "español" ; Spanish
    !insertmacro MUI_DESCRIPTION_TEXT "${un.Translation Swedish}" "svenska" ; Swedish
    !insertmacro MUI_DESCRIPTION_TEXT "${un.Translation Tamil}" "tamiḻ" ; Tamil
    !insertmacro MUI_DESCRIPTION_TEXT "${un.Translation Telugu}" "telugu" ; Telugu
    !insertmacro MUI_DESCRIPTION_TEXT "${un.Translation Thai}" "paasaa-tai" ; Thai
    !insertmacro MUI_DESCRIPTION_TEXT "${un.Translation Turkish}" "Türkçe" ; Turkish
    !insertmacro MUI_DESCRIPTION_TEXT "${un.Translation Ukrainian}" "Ukrajins'ka" ; Ukrainian
    !insertmacro MUI_DESCRIPTION_TEXT "${un.Translation Uyghur}" "Uyghurche" ; Uyghur
    !insertmacro MUI_DESCRIPTION_TEXT "${un.Translation Uzbek}" "o‘zbek tili" ; Uzbek
    !insertmacro MUI_DESCRIPTION_TEXT "${un.Translation Vietnamese}" "tiếng việt" ; Vietnamese
!endif
!macroend

!macro BB_Language_UnInstaller_SectionSetText
  ; To access the section index, curly brackets must be used and the code must be located below the section in the script.
  ; -> Place Functions below the un.Sections!
  SectionSetText "${un.Core}" $(BLEACHBIT_COMPONENT_CORE_TITLE)
  SectionSetText "${un.Group Cleaners}" $(BLEACHBIT_COMPONENTGROUP_CLEANERS_TITLE)
  SectionSetText "${un.Cleaners Stable}" "Stable"
  !ifdef BetaTester
    SectionSetText "${un.Cleaners Beta}" "Beta"
    !ifdef AlphaTester
      SectionSetText "${un.Cleaners Alpha}" "Alpha"
    !endif
  !endif
  SectionSetText "${un.Installer}" $(BLEACHBIT_COMPONENT_INSTALLER_TITLE)
  SectionSetText "${un.Group Shortcuts}" $(BLEACHBIT_COMPONENTGROUP_SHORTCUTS_TITLE)
  SectionSetText "${un.Shortcuts Start Menu}" $(BLEACHBIT_COMPONENT_SHORTCUTS_STARTMENU_TITLE)
  SectionSetText "${un.Shortcut Desktop}" $(BLEACHBIT_COMPONENT_SHORTCUTS_DESKTOP_TITLE)
  SectionSetText "${un.Shortcut Quick Launch}" $(BLEACHBIT_COMPONENT_SHORTCUTS_QUICKLAUNCH_TITLE)
  SectionSetText "${un.Shortcut Autostart}" $(BLEACHBIT_COMPONENT_SHORTCUTS_AUTOSTART_TITLE)
  SectionSetText "${un.Group Translations}" $(BLEACHBIT_COMPONENTGROUP_TRANSLATIONS_TITLE)
  ; https://www.omniglot.com/language/names.htm
  SectionSetText "${un.Translation English (USA)}" "English (USA)"
  !ifndef NoTranslations
    SectionSetText "${un.Translation Afrikaans}" "Afrikaans"
    SectionSetText "${un.Translation Albanian}" "gjuha shqipe" ; Albanian
    SectionSetText "${un.Translation Arabic}" "al-ʻArabīyah" ; Arabic
    SectionSetText "${un.Translation Armenian}" "Hayeren lezou" ; Armenian
    SectionSetText "${un.Translation Asturian}" "Asturianu" ; Asturian
    SectionSetText "${un.Translation Basque}" "euskara" ; Basque
    SectionSetText "${un.Translation Belarusian}" "Bielaruskaja mova" ; Belarusian
    SectionSetText "${un.Translation Bengali}" "baɛṅlā" ; Bengali
    SectionSetText "${un.Translation Bosnian}" "bosanski" ; Bosnian
    SectionSetText "${un.Translation Bulgarian}" "bãlgarski" ; Bulgarian
    SectionSetText "${un.Translation Burmese}" "bama saka" ; Burmese
    SectionSetText "${un.Translation Catalan}" "català" ; Catalan
    SectionSetText "${un.Translation Chinese (Simplified)}" "zhōngwén (Simplified)" ; Chinese (Simplified)
    SectionSetText "${un.Translation Chinese (Traditional)}" "zhōngwén (Traditional)" ; Chinese (Traditional)
    SectionSetText "${un.Translation Croatian}" "Hrvatski" ; Croatian
    SectionSetText "${un.Translation Czech}" "čeština" ; Czech
    SectionSetText "${un.Translation Danish}" "dansk" ; Danish
    SectionSetText "${un.Translation Dutch}" "Nederlands" ; Dutch
    SectionSetText "${un.Translation English (Australia)}" "English (Australia)"
    SectionSetText "${un.Translation English (Canada)}" "English (Canada)"
    SectionSetText "${un.Translation English (United Kingdom)}" "English (United Kingdom)"
    SectionSetText "${un.Translation Esperanto}" "Esperanto"
    SectionSetText "${un.Translation Estonian}" "eesti keel" ; Estonian
    SectionSetText "${un.Translation Faroese}" "Føroyskt" ; Faroese
    SectionSetText "${un.Translation Finnish}" "suomen kieli" ; Finnish
    SectionSetText "${un.Translation French}" "français" ; French
    SectionSetText "${un.Translation Galician}" "Galego" ; Galician
    SectionSetText "${un.Translation German}" "Deutsch" ; German
    SectionSetText "${un.Translation Greek}" "ellēniká" ; Greek
    SectionSetText "${un.Translation Hebrew}" "ivrit" ; Hebrew
    SectionSetText "${un.Translation Hindi}" "hindī" ; Hindi
    SectionSetText "${un.Translation Hungarian}" "magyar nyelv" ; Hungarian
    SectionSetText "${un.Translation Indonesian}" "Bahasa Indonesia" ; Indonesian
    SectionSetText "${un.Translation Interlingua}" "Interlingua"
    SectionSetText "${un.Translation Italian}" "italiano" ; Italian
    SectionSetText "${un.Translation Japanese}" "nihongo" ; Japanese
    SectionSetText "${un.Translation Kirghiz}" "Kirghiz"
    SectionSetText "${un.Translation Korean}" "han-guk-eo" ; Korean
    SectionSetText "${un.Translation Kurdish}" "Kurdí" ; Kurdish
    SectionSetText "${un.Translation Latvian}" "latviešu valoda" ; Latvian
    SectionSetText "${un.Translation Lithuanian}" "lietuvių kalba"; Lithuanian
    SectionSetText "${un.Translation Low German}" "Plattdeutsch" ; Low German
    SectionSetText "${un.Translation Malay}" "Bahasa melayu" ; Malay
    SectionSetText "${un.Translation Northern Sami}" "davvisámegiella" ; Northern Sami
    SectionSetText "${un.Translation Norwegian Bokmal}" "norsk Bokmal" ; Norwegian Bokmal
    SectionSetText "${un.Translation Norwegian Nynorsk}" "norsk Nynorsk" ; Norwegian Nynorsk
    SectionSetText "${un.Translation Persian}" "fārsī" ; Persian/Farsi
    SectionSetText "${un.Translation Polish}" "polski" ; Polish
    SectionSetText "${un.Translation Portuguese}" "português" ; Portuguese
    SectionSetText "${un.Translation Portuguese (Brazilian)}" "português (Brazilian)" ; Portuguese (Brazilian)
    SectionSetText "${un.Translation Romanian}" "român" ; Romanian
    SectionSetText "${un.Translation Russian}" "Russkij jazyk" ; Russian
    SectionSetText "${un.Translation Serbian}" "srpski" ; Serbian
    SectionSetText "${un.Translation Sinhalese}" "Sinhalese"
    SectionSetText "${un.Translation Slovak}" "slovenčina" ; Slovak
    SectionSetText "${un.Translation Slovenian}" "slovenščina" ; Slovenian
    SectionSetText "${un.Translation Spanish}" "español" ; Spanish
    SectionSetText "${un.Translation Swedish}" "svenska" ; Swedish
    SectionSetText "${un.Translation Tamil}" "tamiḻ" ; Tamil
    SectionSetText "${un.Translation Telugu}" "telugu" ; Telugu
    SectionSetText "${un.Translation Thai}" "paasaa-tai" ; Thai
    SectionSetText "${un.Translation Turkish}" "Türkçe" ; Turkish
    SectionSetText "${un.Translation Ukrainian}" "Ukrajins'ka" ; Ukrainian
    SectionSetText "${un.Translation Uyghur}" "Uyghurche" ; Uyghur
    SectionSetText "${un.Translation Uzbek}" "o‘zbek tili" ; Uzbek
    SectionSetText "${un.Translation Vietnamese}" "tiếng việt" ; Vietnamese
  !endif
  !ifndef NoSectionShred
    SectionSetText "${un.Shred for Explorer}" $(BLEACHBIT_COMPONENT_SHREDFOREXPLORER_TITLE)
  !endif
!macroend
