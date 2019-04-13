;NSIS Modern User Interface - Language File
;Compatible with UltraModernUI 2.0 beta 1

;Language: Lithuanian (1063)
;By Matthias <bodenseematze@users.sourceforge.net> (copied from English and translated)
;--------------------------------

!ifdef UMUI_MULTILANGUAGEPAGE
  ${LangFileString} UMUI_TEXT_MULTILANGUAGE_TITLE "Sveiki, čia diegimo programos pagelbiklis $(^NameDA)."
  ${LangFileString} UMUI_TEXT_MULTILANGUAGE_TEXT "Prieš diegdami $(^NameDA), pasirinkite kalbą:$\r$\n$\r$\n$_CLICK"
!endif

!ifdef UMUI_UNMULTILANGUAGEPAGE
  ${LangFileString} UMUI_UNTEXT_MULTILANGUAGE_TITLE "Sveiki, čia šalinimo programos pagelbiklis $(^NameDA)."
  ${LangFileString} UMUI_UNTEXT_MULTILANGUAGE_TEXT "Prieš šalindami $(^NameDA), pasirinkite kalbą:$\r$\n$\r$\n$_CLICK"
!endif

!ifdef UMUI_MULTILANGUAGEPAGE | UMUI_UNMULTILANGUAGEPAGE
  ${LangFileString} UMUI_TEXT_MULTILANGUAGE_LANGUAGE "Kalba:"
!endif


!ifdef MUI_WELCOMEPAGE
  ${LangFileString} UMUI_TEXT_WELCOME_ALTERNATIVEINFO_TEXT "Šis pagelbiklis padės Jums įdiegti $(^NameDA).$\r$\n$\r$\n$\r$\n$_CLICK"
!endif


!ifdef UMUI_SERIALNUMBERPAGE | UMUI_UNSERIALNUMBERPAGE
  ${LangFileString} UMUI_TEXT_SERIALNUMBER_TITLE "Prašome įvesti $(^NameDA) serijos numerį"
  ${LangFileString} UMUI_TEXT_SERIALNUMBER_SUBTITLE "Prašome užpildyti įvairius laukelius."
  ${LangFileString} UMUI_TEXT_SERIALNUMBER_INFO_TEXT "Prašome užpildyti įvairius laukelius. $_CLICK"
  ${LangFileString} UMUI_TEXT_SERIALNUMBER_INVALIDATE_TEXT "$UMUI_SNTEXT netinka. Patikrinkite įvestą informaciją."
  ${LangFileString} UMUI_TEXT_SERIALNUMBER_NAME "Pavadinimas"
  ${LangFileString} UMUI_TEXT_SERIALNUMBER_ORGANIZATION "Organizacija"
  ${LangFileString} UMUI_TEXT_SERIALNUMBER_SERIALNUMBER "Serijos numeris"
  ${LangFileString} UMUI_TEXT_SERIALNUMBER_ACTIVATIONCODE "Aktyvinimo kodas"
  ${LangFileString} UMUI_TEXT_SERIALNUMBER_PASSWORD "Slaptažodis"
!endif 


!ifdef UMUI_CONFIRMPAGE
  ${LangFileString} UMUI_TEXT_INSTCONFIRM_SUBTITLE "Diegimo programa surinko reikiamą informaciją ir yra pasirengusi įdiegti $(^NameDA)."
  ${LangFileString} UMUI_TEXT_INSTCONFIRM_TITLE "Diegimo patvirtinimas"
  ${LangFileString} UMUI_TEXT_INSTCONFIRM_TEXT_TOP "Diegimo programa pasirengusi $(^NameDA) įdiegti Jūsų kompiuteryje.$\r$\nJei dar norėtumėte patikrinti arba pakeisti diegimo nustatymus, spustelėkite $(^BackBtn). $_CLICK"
!endif 

!ifdef UMUI_UNCONFIRMPAGE
  ${LangFileString} UMUI_UNTEXT_INSTCONFIRM_SUBTITLE "Diegimo programa surinko reikiamą informaciją ir yra pasirengusi pašalinti $(^NameDA)."
  ${LangFileString} UMUI_UNTEXT_INSTCONFIRM_TITLE "Šalinimo patvirtinimas"
  ${LangFileString} UMUI_UNTEXT_INSTCONFIRM_TEXT_TOP "Diegimo programa pasirengusi pašalinti $(^NameDA) iš Jūsų kompiuterio.$\r$\nJei dar norėtumėte patikrinti arba pakeisti diegimo nustatymus, spustelėkite $(^BackBtn). Spustelėkite $(^NextBtn), jei norite pradėti šalinimo procesą."
!endif 

!ifdef UMUI_CONFIRMPAGE | UMUI_UNCONFIRMPAGE
  ${LangFileString} UMUI_TEXT_INSTCONFIRM_TEXTBOX_TITLE "Dabartinė konfigūracija:"
  ${LangFileString} UMUI_TEXT_INSTCONFIRM_TEXTBOX_DESTINATION_LOCATION "Paskirties vieta:"
  ${LangFileString} UMUI_TEXT_INSTCONFIRM_TEXTBOX_START_MENU_FOLDER "Pradžios meniu aplankas:"
  ${LangFileString} UMUI_TEXT_INSTCONFIRM_TEXTBOX_COMPNENTS "Bus įdiegti toliau nurodyti komponentai:"
!endif 


!ifdef UMUI_ABORTPAGE
  ${LangFileString} UMUI_TEXT_ABORT_INFO_TITLE "Diegimo programos pagelbiklio $(^NameDA) išjungimas"
  ${LangFileString} UMUI_TEXT_ABORT_INFO_TEXT "Pagelbiklis buvo išjungtas nebaigus iki galo įdiegti $(^NameDA).$\r$\n$\r$\nJei norėsite programą diegti vėliau, turėsite pagelbiklį įjungti iš naujo.$\r$\n$\r$\n$\r$\n$\r$\nNorėdami uždaryti diegimo programos pagelbiklį, spustelėkite $(^CloseBtn)."
!endif 

!ifdef UMUI_UNABORTPAGE
  ${LangFileString} UMUI_UNTEXT_ABORT_INFO_TITLE "Programos šalinimo pagelbiklio $(^NameDA) išjungimas"
  ${LangFileString} UMUI_UNTEXT_ABORT_INFO_TEXT "Pagelbiklis buvo išjungtas nebaigus iki galo pašalinti $(^NameDA).$\r$\n$\r$\nJei norėsite programą šalinti vėliau, turėsite pagelbiklį įjungti iš naujo.$\r$\n$\r$\n$\r$\n$\r$\nNorėdami uždaryti šalinimo programos pagelbiklį, spustelėkite $(^CloseBtn)."
!endif


!ifdef UMUI_SETUPTYPEPAGE
  ${LangFileString} UMUI_TEXT_SETUPTYPE_TITLE "Diegimo programos tipas"
  ${LangFileString} UMUI_TEXT_SETUPTYPE_SUBTITLE "Pasirinkite Jums labiausiai tinkamą diegimo programos tipą."
  ${LangFileString} UMUI_TEXT_SETUPTYPE_INFO_TEXT "Pasirinkite diegimo programos tipą."
  ${LangFileString} UMUI_TEXT_SETUPTYPE_MINIMAL_TEXT "Bus įdiegtos tik reikiamos funkcijos. (Joms reikia mažiausiai atminties vietos)"
  ${LangFileString} UMUI_TEXT_SETUPTYPE_STANDARD_TEXT "Bus įdiegtos visos pagrindinės funkcijos. Dažniausiai rekomenduojama naudotojams."
  ${LangFileString} UMUI_TEXT_SETUPTYPE_COMPLETE_TEXT "Bus įdiegtos visos programos funkcijos. (Joms reikia daugiausiai atminties vietos)"
  ${LangFileString} UMUI_TEXT_SETUPTYPE_CUSTOM_TEXT "Prašome pasirinkti norimas programų funkcijų diegimo vietas. Rekomenduojama pažengusiems naudotojams."
!endif 

!ifdef UMUI_UNSETUPTYPEPAGE
  ${LangFileString} UMUI_UNTEXT_SETUPTYPE_TITLE "Programos šalinimo tipas"
  ${LangFileString} UMUI_UNTEXT_SETUPTYPE_SUBTITLE "Pasirinkite Jums labiausiai tinkamą programos šalinimo tipą."
  ${LangFileString} UMUI_UNTEXT_SETUPTYPE_INFO_TEXT "Pasirinkite programos šalinimo tipą."
  ${LangFileString} UMUI_UNTEXT_SETUPTYPE_MINIMAL_TEXT "Nebus pašalintos tik pagrindinės funkcijos."
  ${LangFileString} UMUI_UNTEXT_SETUPTYPE_STANDARD_TEXT "Nebus pašalintos tik svarbiausios funkcijos."
  ${LangFileString} UMUI_UNTEXT_SETUPTYPE_COMPLETE_TEXT "Bus išsaugota visa programa."
  ${LangFileString} UMUI_UNTEXT_SETUPTYPE_CUSTOM_TEXT "Pasirinkite, kurias programos funkcijas norite pašalinti."
!endif 

!ifdef UMUI_SETUPTYPEPAGE | UMUI_UNSETUPTYPEPAGE
  ${LangFileString} UMUI_TEXT_SETUPTYPE_MINIMAL_TITLE "Minimaliai"
  ${LangFileString} UMUI_TEXT_SETUPTYPE_STANDARD_TITLE "Standartiškai"
  ${LangFileString} UMUI_TEXT_SETUPTYPE_COMPLETE_TITLE "Visiškai"
  ${LangFileString} UMUI_TEXT_SETUPTYPE_CUSTOM_TITLE "Nurodo naudotojas"
!endif 


!ifdef UMUI_INFORMATIONPAGE
  ${LangFileString} UMUI_TEXT_INFORMATION_SUBTITLE "Prašome atkreipti dėmesį į informaciją apie $(^NameDA) įdiegimą."
!endif 

!ifdef UMUI_UNINFORMATIONPAGE
  ${LangFileString} UMUI_UNTEXT_INFORMATION_SUBTITLE "Prašome atkreipti dėmesį į informaciją apie $(^NameDA) šalinimą."
!endif 

!ifdef UMUI_INFORMATIONPAGE | UMUI_UNINFORMATIONPAGE
  ${LangFileString} UMUI_TEXT_INFORMATION_TITLE "Informacija"
  ${LangFileString} UMUI_TEXT_INFORMATION_INFO_TEXT "Informacija apie $(^NameDA)."
!endif 


!ifdef UMUI_ADDITIONALTASKSPAGE
  ${LangFileString} UMUI_TEXT_ADDITIONALTASKS_INFO_TEXT "Pasirinkite papildomus veiksmus, kuriuos diegimo programa turi atlikti diegdama $(^NameDA). $_CLICK"
!endif 

!ifdef UMUI_UNADDITIONALTASKSPAGE
  ${LangFileString} UMUI_UNTEXT_ADDITIONALTASKS_INFO_TEXT "Pasirinkite papildomus veiksmus, kuriuos diegimo programa turi atlikti šalindama $(^NameDA). $_CLICK"
!endif 

!ifdef UMUI_ADDITIONALTASKSPAGE | UMUI_UNADDITIONALTASKSPAGE
  ${LangFileString} UMUI_TEXT_ADDITIONALTASKS_TITLE "Papildomi veiksmai"
  ${LangFileString} UMUI_TEXT_ADDITIONALTASKS_SUBTITLE "Kokie papildomi veiksmai turi būti atlikti?"
  ${LangFileString} UMUI_TEXT_ADDITIONALTASKS_ADDITIONAL_ICONS "Papildomos piktogramos:"
  ${LangFileString} UMUI_TEXT_ADDITIONALTASKS_CREATE_DESKTOP_ICON "Sukurti piktogramą darbalaukyje"
  ${LangFileString} UMUI_TEXT_ADDITIONALTASKS_CREATE_QUICK_LAUNCH_ICON "Sukurti piktogramą sparčiosios paleisties juostoje"
  ${LangFileString} UMUI_TEXT_ADDITIONALTASKS_ADVANCED_PARAMETERS "Papildomi parametrai:"
  ${LangFileString} UMUI_TEXT_ADDITIONALTASKS_LAUNCH_PROGRAM_AT_WINDOWS_STARTUP "Paleisti $(^NameDA) įsijungus sistemai"
  ${LangFileString} UMUI_TEXT_ADDITIONALTASKS_FILE_ASSOCIATION "Failų susiejimas:"
  ${LangFileString} UMUI_TEXT_ADDITIONALTASKS_ASSOCIATE_WITH "$(^NameDA) susieti su "
  ${LangFileString} UMUI_TEXT_ADDITIONALTASKS_ASSOCIATE_WITH_END " Failo tipas"
!endif 
  
  
!ifdef UMUI_CONFIRMPAGE | UMUI_UNCONFIRMPAGE | UMUI_ALTERNATIVESTARTMENUPAGE | UMUI_UNALTERNATIVESTARTMENUPAGE
  ${LangFileString} UMUI_TEXT_SHELL_VAR_CONTEXT "Kam turi būti sukurtos sąsajos:"
  ${LangFileString} UMUI_TEXT_SHELL_VAR_CONTEXT_FOR_ALL_USERS "Visiems naudotojams"
  ${LangFileString} UMUI_TEXT_SHELL_VAR_CONTEXT_ONLY_FOR_CURRENT_USER "Tik prisiregistravusiems naudotojams"
!endif


!ifdef UMUI_UPDATEPAGE
  ${LangFileString} UMUI_TEXT_UPDATE_TITLE "Naujinimas"
  ${LangFileString} UMUI_TEXT_UPDATE_SUBTITLE "Ankstesnės programos versijos naujinimas."
  ${LangFileString} UMUI_TEXT_UPDATE_INFO_TEXT "Sveiki, čia $(^NameDA) naujinimo pagelbiklis.$\r$\nŠi programa atnaujins versiją $OLDVERSION."
  ${LangFileString} UMUI_TEXT_UPDATE_UPDATE_TITLE "Naujinimas"
  ${LangFileString} UMUI_TEXT_UPDATE_UPDATE_TEXT "Visų $(^NameDA) jau įdiegtų komponentų atnaujinimas, įdiegiant versiją $NEWVERSION."
  ${LangFileString} UMUI_TEXT_UPDATE_REMOVE_TITLE "Šalinimas"
  ${LangFileString} UMUI_TEXT_UPDATE_REMOVE_TEXT "versiją $OLDVERSION šalinimas iš Jūsų kompiuterio."
  ${LangFileString} UMUI_TEXT_UPDATE_CONTINUE_TITLE "Diegimo programos tęsimas"
  ${LangFileString} UMUI_TEXT_UPDATE_CONTINUE_TEXT "Tęskite diegimo programą įprastai. Naudokite šią parinktį, jei naujoji versija turi būti paraleliai įdiegta kitame aplanke, išsaugant esamą versiją."
!endif


!ifdef UMUI_MAINTENANCEPAGE | UMUI_UNMAINTENANCEPAGE
  ${LangFileString} UMUI_TEXT_MAINTENANCE_TITLE "Tvarkymas"
  ${LangFileString} UMUI_TEXT_MAINTENANCE_SUBTITLE "Programos keitimas, taisymas arba šalinimas."
  ${LangFileString} UMUI_TEXT_MAINTENANCE_INFO_TEXT "Sveiki, čia $(^NameDA) tvarkymo programa.$\r$\nNaudodami šią programą galite pakeisti esamą įdiegtą programą."
  ${LangFileString} UMUI_TEXT_MAINTENANCE_MODIFY_TITLE "Keitimas"
  ${LangFileString} UMUI_TEXT_MAINTENANCE_MODIFY_TEXT "Pasirinkite naujus komponentus, kuriuos norite įdiegti, arba jau esamus komponentus, kuriuos norite pašalinti."
  ${LangFileString} UMUI_TEXT_MAINTENANCE_REPAIR_TITLE "Taisymas"
  ${LangFileString} UMUI_TEXT_MAINTENANCE_REPAIR_TEXT "Iš naujo įdiegiami visi jau įdiegti $(^NameDA) komponentai."
  ${LangFileString} UMUI_TEXT_MAINTENANCE_REMOVE_TITLE "Šalinimas"
  ${LangFileString} UMUI_TEXT_MAINTENANCE_REMOVE_TEXT "$(^NameDA) šalinimas iš Jūsų kompiuterio."
  ${LangFileString} UMUI_TEXT_MAINTENANCE_CONTINUE_TITLE "Diegimo programos tęsimas"
  ${LangFileString} UMUI_TEXT_MAINTENANCE_CONTINUE_TEXT "Tęskite diegimo programą įprastai. Naudokite šią parinktį, jei programą norite diegti vietoje jau įdiegtos programos, arba norite iš naujo įdiegti kitame aplanke."
!endif


!ifdef UMUI_FILEDISKREQUESTPAGE | UMUI_UNFILEDISKREQUESTPAGE
  ${LangFileString} UMUI_TEXT_FILEDISKREQUEST_FILE_SUBTITLE_BEGIN "Diegimo programai reikia toliau nurodytos duomenų laikmenos, kad būtų galima tęsti."
  ${LangFileString} UMUI_TEXT_FILEDISKREQUEST_FILE_SUBTITLE_END "failo, kad būtų galima tęsti."
  ${LangFileString} UMUI_TEXT_FILEDISKREQUEST_DISK_SUBTITLE "Diegimo programai reikia toliau nurodytos duomenų laikmenos, kad būtų galima tęsti."
  ${LangFileString} UMUI_TEXT_FILEDISKREQUEST_FILE_BEGIN "Pasirinkite failo išsaugojimo vietą,"
  ${LangFileString} UMUI_TEXT_FILEDISKREQUEST_FILE_END "kad būtų galima tęsti."
  ${LangFileString} UMUI_TEXT_FILEDISKREQUEST_DISK "Prašome nurodyti"
  ${LangFileString} UMUI_TEXT_FILEDISKREQUEST_PATH "maršrutą:"
!endif
