;NSIS Modern User Interface - Language File
;Compatible with UltraModernUI 2.0 beta 1

;Language: Slovenian (1060)
;By Matthias <bodenseematze@users.sourceforge.net> (copied from English and translated)
;--------------------------------

!ifdef UMUI_MULTILANGUAGEPAGE
  ${LangFileString} UMUI_TEXT_MULTILANGUAGE_TITLE "Dobrodošli v namestitvi $(^NameDA)"
  ${LangFileString} UMUI_TEXT_MULTILANGUAGE_TEXT "Izberite jezik za namestitev $(^NameDA):$\r$\n$\r$\n$_CLICK"
!endif

!ifdef UMUI_UNMULTILANGUAGEPAGE
  ${LangFileString} UMUI_UNTEXT_MULTILANGUAGE_TITLE "Dobrodošli v odstranitvi $(^NameDA)"
  ${LangFileString} UMUI_UNTEXT_MULTILANGUAGE_TEXT "Izberite jezik za odstranitev $(^NameDA):$\r$\n$\r$\n$_CLICK"
!endif

!ifdef UMUI_MULTILANGUAGEPAGE | UMUI_UNMULTILANGUAGEPAGE
  ${LangFileString} UMUI_TEXT_MULTILANGUAGE_LANGUAGE "Jezik:"
!endif


!ifdef MUI_WELCOMEPAGE
  ${LangFileString} UMUI_TEXT_WELCOME_ALTERNATIVEINFO_TEXT "Ta asistent vas bo vodil pri namestitvi $(^NameDA).$\r$\n$\r$\n$\r$\n$_CLICK"
!endif


!ifdef UMUI_SERIALNUMBERPAGE | UMUI_UNSERIALNUMBERPAGE
  ${LangFileString} UMUI_TEXT_SERIALNUMBER_TITLE "Vnesite serijsko številko za $(^NameDA)"
  ${LangFileString} UMUI_TEXT_SERIALNUMBER_SUBTITLE "Prosimo da izpolnite polja."
  ${LangFileString} UMUI_TEXT_SERIALNUMBER_INFO_TEXT "Prosimo da izpolnite polja. $_CLICK"
  ${LangFileString} UMUI_TEXT_SERIALNUMBER_INVALIDATE_TEXT "$UMUI_SNTEXT ni veljaven. Prosimo da preverite svoje podatke."
  ${LangFileString} UMUI_TEXT_SERIALNUMBER_NAME "Ime"
  ${LangFileString} UMUI_TEXT_SERIALNUMBER_ORGANIZATION "Organizacija"
  ${LangFileString} UMUI_TEXT_SERIALNUMBER_SERIALNUMBER "Serijska številka"
  ${LangFileString} UMUI_TEXT_SERIALNUMBER_ACTIVATIONCODE "Aktivacijska koda"
  ${LangFileString} UMUI_TEXT_SERIALNUMBER_PASSWORD "Geslo"
!endif


!ifdef UMUI_CONFIRMPAGE
  ${LangFileString} UMUI_TEXT_INSTCONFIRM_SUBTITLE "Za namestitev $(^NameDA) zbiram naslednjo informacijo."
  ${LangFileString} UMUI_TEXT_INSTCONFIRM_TITLE "Potrditev namestitve"
  ${LangFileString} UMUI_TEXT_INSTCONFIRM_TEXT_TOP "Asistent je pripravljen za namestitev $(^NameDA) na računalniku.$\r$\nV primeru, da morate preveriti oz. spremeniti namestitvene nastavitve, pritisnite na $(^BackBtn). $_CLICK"
!endif

!ifdef UMUI_UNCONFIRMPAGE
  ${LangFileString} UMUI_UNTEXT_INSTCONFIRM_SUBTITLE "Za odstranitev $(^NameDA) zbiram naslednjo informacijo."
  ${LangFileString} UMUI_UNTEXT_INSTCONFIRM_TITLE "Potrditev odstranitve"
  ${LangFileString} UMUI_UNTEXT_INSTCONFIRM_TEXT_TOP "Asistent je pripravljen za odstranitev $(^NameDA) iz računalnika.$\r$\nV primeru, da morate preveriti oz. spremeniti namestitvene nastavitve, pritisnite na $(^BackBtn). Kliknite na $(^NextBtn) da začnete odstranitev."
!endif

!ifdef UMUI_CONFIRMPAGE | UMUI_UNCONFIRMPAGE
  ${LangFileString} UMUI_TEXT_INSTCONFIRM_TEXTBOX_TITLE "Trenutna konfiguracija:"
  ${LangFileString} UMUI_TEXT_INSTCONFIRM_TEXTBOX_DESTINATION_LOCATION "Ciljne mesto:"
  ${LangFileString} UMUI_TEXT_INSTCONFIRM_TEXTBOX_START_MENU_FOLDER "Imenik za začetni meni:"
  ${LangFileString} UMUI_TEXT_INSTCONFIRM_TEXTBOX_COMPNENTS "Nameščene bodo naslednje sestavne dele:"
!endif


!ifdef UMUI_ABORTPAGE
  ${LangFileString} UMUI_TEXT_ABORT_INFO_TITLE "Izhod iz asistenta za odstranitev $(^NameDA)"
  ${LangFileString} UMUI_TEXT_ABORT_INFO_TEXT "Asistent je bil prekinjen, še preden je bil $(^NameDA) v celoti nameščen.$\r$\n$\r$\nDa bi program kasneje namestili, nameščanje ponovite.$\r$\n$\r$\n$\r$\n$\r$\nDa bi asistenta za namestitev lahko zaprli, pritisnite na $(^CloseBtn)."
!endif

!ifdef UMUI_UNABORTPAGE
  ${LangFileString} UMUI_UNTEXT_ABORT_INFO_TITLE "Izhod iz asistenta za odstranitev $(^NameDA)"
  ${LangFileString} UMUI_UNTEXT_ABORT_INFO_TEXT "Asistent je bil prekinjen, še preden je bil $(^NameDA) v celoti odstranjen.$\r$\n$\r$\nDa bi program kasneje odstranili, odstranjevanje ponovite.$\r$\n$\r$\n$\r$\n$\r$\nDa bi asistenta za odstranitev lahko zaprli, pritisnite na $(^CloseBtn)."
!endif


!ifdef UMUI_SETUPTYPEPAGE
  ${LangFileString} UMUI_TEXT_SETUPTYPE_TITLE "Način namestitve"
  ${LangFileString} UMUI_TEXT_SETUPTYPE_SUBTITLE "Izbor ustreznega načina namestitve"
  ${LangFileString} UMUI_TEXT_SETUPTYPE_INFO_TEXT "Izberite način namestitve."
  ${LangFileString} UMUI_TEXT_SETUPTYPE_MINIMAL_TEXT "Nameščene bodo samo potrebne funkcije. (Zahteva najmanjši pomnilnik)"
  ${LangFileString} UMUI_TEXT_SETUPTYPE_STANDARD_TEXT "Nameščene bodo vse glavne funkcije. Priporočeno za večino uporabnikov."
  ${LangFileString} UMUI_TEXT_SETUPTYPE_COMPLETE_TEXT "Nameščene bodo vse programske funkcije. (Zahteva največji pomnilnik)"
  ${LangFileString} UMUI_TEXT_SETUPTYPE_CUSTOM_TEXT "Izberite katero funkcijo programa želite namestiti. Izberite kam naj se katera od funkcij programa namesti."
!endif

!ifdef UMUI_UNSETUPTYPEPAGE
  ${LangFileString} UMUI_UNTEXT_SETUPTYPE_TITLE "Način odstranitve"
  ${LangFileString} UMUI_UNTEXT_SETUPTYPE_SUBTITLE "Izbor ustreznega načina odstranitve"
  ${LangFileString} UMUI_UNTEXT_SETUPTYPE_INFO_TEXT "Izberite način odstranitve."
  ${LangFileString} UMUI_UNTEXT_SETUPTYPE_MINIMAL_TEXT "Se shranijo samo glavne funkcije."
  ${LangFileString} UMUI_UNTEXT_SETUPTYPE_STANDARD_TEXT "Se shranijo samo najpomembnejše funkcije."
  ${LangFileString} UMUI_UNTEXT_SETUPTYPE_COMPLETE_TEXT "Bode shranjen celoten program."
  ${LangFileString} UMUI_UNTEXT_SETUPTYPE_CUSTOM_TEXT "Izberite katero funkcijo programa želite odstraniti."
!endif

!ifdef UMUI_SETUPTYPEPAGE | UMUI_UNSETUPTYPEPAGE
  ${LangFileString} UMUI_TEXT_SETUPTYPE_MINIMAL_TITLE "Minimalno"
  ${LangFileString} UMUI_TEXT_SETUPTYPE_STANDARD_TITLE "Standardno"
  ${LangFileString} UMUI_TEXT_SETUPTYPE_COMPLETE_TITLE "popolna"
  ${LangFileString} UMUI_TEXT_SETUPTYPE_CUSTOM_TITLE "po meri"
!endif


!ifdef UMUI_INFORMATIONPAGE
  ${LangFileString} UMUI_TEXT_INFORMATION_SUBTITLE "Upoštevajte informacije za namestitev $(^NameDA)."
!endif

!ifdef UMUI_UNINFORMATIONPAGE
  ${LangFileString} UMUI_UNTEXT_INFORMATION_SUBTITLE "Upoštevajte informacije za odstranitev $(^NameDA)."
!endif

!ifdef UMUI_INFORMATIONPAGE | UMUI_UNINFORMATIONPAGE
  ${LangFileString} UMUI_TEXT_INFORMATION_TITLE "Informacija"
  ${LangFileString} UMUI_TEXT_INFORMATION_INFO_TEXT "Informacije o $(^NameDA)."
!endif


!ifdef UMUI_ADDITIONALTASKSPAGE
  ${LangFileString} UMUI_TEXT_ADDITIONALTASKS_INFO_TEXT "Izberite dodatne dejavnosti, ki morajo biti izvedene med namestitvijo $(^NameDA). $_CLICK"
!endif

!ifdef UMUI_UNADDITIONALTASKSPAGE
  ${LangFileString} UMUI_UNTEXT_ADDITIONALTASKS_INFO_TEXT "Izberite dodatne dejavnosti, ki morajo biti izvedene med odstranitvijo $(^NameDA). $_CLICK"
!endif

!ifdef UMUI_ADDITIONALTASKSPAGE | UMUI_UNADDITIONALTASKSPAGE
  ${LangFileString} UMUI_TEXT_ADDITIONALTASKS_TITLE "Dodatne ukrepe"
  ${LangFileString} UMUI_TEXT_ADDITIONALTASKS_SUBTITLE "Katere dodatne ukrepe je treba izvesti?"
  ${LangFileString} UMUI_TEXT_ADDITIONALTASKS_ADDITIONAL_ICONS "Dodatne ikone:"
  ${LangFileString} UMUI_TEXT_ADDITIONALTASKS_CREATE_DESKTOP_ICON "Ustvarjanje ikone na namizju"
  ${LangFileString} UMUI_TEXT_ADDITIONALTASKS_CREATE_QUICK_LAUNCH_ICON "Ustvarjanje ikone v orodni vrstici za hitri zagon"
  ${LangFileString} UMUI_TEXT_ADDITIONALTASKS_ADVANCED_PARAMETERS "Nadaljevalne parametre:"
  ${LangFileString} UMUI_TEXT_ADDITIONALTASKS_LAUNCH_PROGRAM_AT_WINDOWS_STARTUP "$(^NameDA) se bo zagnal po zagonu sistema"
  ${LangFileString} UMUI_TEXT_ADDITIONALTASKS_FILE_ASSOCIATION "Povezave datoteke:"
  ${LangFileString} UMUI_TEXT_ADDITIONALTASKS_ASSOCIATE_WITH "Povezava $(^NameDA) z "
  ${LangFileString} UMUI_TEXT_ADDITIONALTASKS_ASSOCIATE_WITH_END " Vrsta datoteke"
!endif


!ifdef UMUI_CONFIRMPAGE | UMUI_UNCONFIRMPAGE | UMUI_ALTERNATIVESTARTMENUPAGE | UMUI_UNALTERNATIVESTARTMENUPAGE
  ${LangFileString} UMUI_TEXT_SHELL_VAR_CONTEXT "Povezave je potrebno ustvariti za:"
  ${LangFileString} UMUI_TEXT_SHELL_VAR_CONTEXT_FOR_ALL_USERS "Za vse uporabnike"
  ${LangFileString} UMUI_TEXT_SHELL_VAR_CONTEXT_ONLY_FOR_CURRENT_USER "Samo za prijavljeni uporabnik"
!endif


!ifdef UMUI_UPDATEPAGE
  ${LangFileString} UMUI_TEXT_UPDATE_TITLE "Aktualizacija"
  ${LangFileString} UMUI_TEXT_UPDATE_SUBTITLE "Posodobitev starejše različice programa."
  ${LangFileString} UMUI_TEXT_UPDATE_INFO_TEXT "Dobrodošli v namestitvenem asistentu $(^NameDA).$\r$\nTa program opravlja posodabljanje različice $OLDVERSION."
  ${LangFileString} UMUI_TEXT_UPDATE_UPDATE_TITLE "Posodabljanje"
  ${LangFileString} UMUI_TEXT_UPDATE_UPDATE_TEXT "Posodobitev vseh nameščenih sestavin do različice $NEWVERSION."
  ${LangFileString} UMUI_TEXT_UPDATE_REMOVE_TITLE "Odstranitev"
  ${LangFileString} UMUI_TEXT_UPDATE_REMOVE_TEXT "Odstranitev različice $OLDVERSION iz računalnika."
  ${LangFileString} UMUI_TEXT_UPDATE_CONTINUE_TITLE "Nadaljevanje namestitve"
  ${LangFileString} UMUI_TEXT_UPDATE_CONTINUE_TEXT "Običajno nadaljevanje namestitve Kadar morate novo različico namestiti v drug imenik, ki je vzporeden obstoječemu, priporočamo, da uporabite to možnost."
!endif


!ifdef UMUI_MAINTENANCEPAGE | UMUI_UNMAINTENANCEPAGE
  ${LangFileString} UMUI_TEXT_MAINTENANCE_TITLE "Prilagoditev"
  ${LangFileString} UMUI_TEXT_MAINTENANCE_SUBTITLE "Sprememba, popravilo ali odstranitev programa."
  ${LangFileString} UMUI_TEXT_MAINTENANCE_INFO_TEXT "Dobrodošli v $(^NameDA) prilagoditvenem asistentu.$\r$\nS tem programom se trenutna namestitev lahko spremeni."
  ${LangFileString} UMUI_TEXT_MAINTENANCE_MODIFY_TITLE "Spreminjanje"
  ${LangFileString} UMUI_TEXT_MAINTENANCE_MODIFY_TEXT "Izberite nove komponente za namestitev, oz. izberite nameščene obstoječe komponente za odstranitev."
  ${LangFileString} UMUI_TEXT_MAINTENANCE_REPAIR_TITLE "Popravljanje"
  ${LangFileString} UMUI_TEXT_MAINTENANCE_REPAIR_TEXT "Ponovna namestitev vseh nameščenih $(^NameDA) sestavnih delov."
  ${LangFileString} UMUI_TEXT_MAINTENANCE_REMOVE_TITLE "Odstranitev"
  ${LangFileString} UMUI_TEXT_MAINTENANCE_REMOVE_TEXT "Odstranitev $(^NameDA) iz računalnika."
  ${LangFileString} UMUI_TEXT_MAINTENANCE_CONTINUE_TITLE "Nadaljevanje namestitve"
  ${LangFileString} UMUI_TEXT_MAINTENANCE_CONTINUE_TEXT "Običajno nadaljevanje namestitve Kadar morate novo namestitev shraniti na že obstoječo oz. ko se mora nova namestitev izvesti v drugem imeniku, priporočamo, da uporabite to možnost."
!endif


!ifdef UMUI_FILEDISKREQUESTPAGE | UMUI_UNFILEDISKREQUESTPAGE
  ${LangFileString} UMUI_TEXT_FILEDISKREQUEST_FILE_SUBTITLE_BEGIN "Za namestitev potrebujete"
  ${LangFileString} UMUI_TEXT_FILEDISKREQUEST_FILE_SUBTITLE_END "Za nadaljevanje datoteke."
  ${LangFileString} UMUI_TEXT_FILEDISKREQUEST_DISK_SUBTITLE "Za nadaljevanje namestitve vstavite naslednjo zgoščenko."
  ${LangFileString} UMUI_TEXT_FILEDISKREQUEST_FILE_BEGIN "Izberite lokacijo datoteke."
  ${LangFileString} UMUI_TEXT_FILEDISKREQUEST_FILE_END "za nadaljevanje."
  ${LangFileString} UMUI_TEXT_FILEDISKREQUEST_DISK "Prosimo da vstavite disk"
  ${LangFileString} UMUI_TEXT_FILEDISKREQUEST_PATH "Pot:"
!endif
