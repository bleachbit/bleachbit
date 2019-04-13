;NSIS Modern User Interface - Language File
;Compatible with UltraModernUI 2.0 beta 1

;Language: Hungarian (1038) - Based on NSIS Official Hungarian Language
;By Tom Evin (evin@mailbox.hu)
;--------------------------------

!ifdef UMUI_MULTILANGUAGEPAGE
  ${LangFileString} UMUI_TEXT_MULTILANGUAGE_TITLE "Üdvözli a(z) $(^NameDA) Telepítõ Varázsló"
  ${LangFileString} UMUI_TEXT_MULTILANGUAGE_TEXT "A(z) $(^NameDA) telepítése elõtt, válasszon nyelvet:$\r$\n$\r$\n$_CLICK"
!endif

!ifdef UMUI_UNMULTILANGUAGEPAGE
  ${LangFileString} UMUI_UNTEXT_MULTILANGUAGE_TITLE "Üdvözli a(z) $(^NameDA) Eltávolító Varázsló"
  ${LangFileString} UMUI_UNTEXT_MULTILANGUAGE_TEXT "A(z) $(^NameDA) eltávolítása elõtt, válasszon nyelvet:$\r$\n$\r$\n$_CLICK"
!endif

!ifdef UMUI_MULTILANGUAGEPAGE | UMUI_UNMULTILANGUAGEPAGE
  ${LangFileString} UMUI_TEXT_MULTILANGUAGE_LANGUAGE "Nyelv:"
!endif


!ifdef MUI_WELCOMEPAGE
  ${LangFileString} UMUI_TEXT_WELCOME_ALTERNATIVEINFO_TEXT "A varázsló végigvezeti a(z) $(^NameDA) telepítési folyamatán.$\r$\n$\r$\n$\r$\n$_CLICK"
!endif


!ifdef UMUI_SERIALNUMBERPAGE | UMUI_UNSERIALNUMBERPAGE
  ${LangFileString} UMUI_TEXT_SERIALNUMBER_TITLE "Adja meg a(z) $(^NameDA) sorozatszámát"
  ${LangFileString} UMUI_TEXT_SERIALNUMBER_SUBTITLE "Kérem töltse ki a következõ mezõket."
  ${LangFileString} UMUI_TEXT_SERIALNUMBER_INFO_TEXT "Kérem töltse ki a következõ mezõket. $_CLICK"
  ${LangFileString} UMUI_TEXT_SERIALNUMBER_INVALIDATE_TEXT "A(z) $UMUI_SNTEXT érvénytelen. Ellenõrizze újra a megadott információt."
  ${LangFileString} UMUI_TEXT_SERIALNUMBER_NAME "Név"
  ${LangFileString} UMUI_TEXT_SERIALNUMBER_ORGANIZATION "Szervezet"
  ${LangFileString} UMUI_TEXT_SERIALNUMBER_SERIALNUMBER "Sorozatszám"
  ${LangFileString} UMUI_TEXT_SERIALNUMBER_ACTIVATIONCODE "Aktivációs kód"
  ${LangFileString} UMUI_TEXT_SERIALNUMBER_PASSWORD "Jelszó"
!endif


!ifdef UMUI_CONFIRMPAGE
  ${LangFileString} UMUI_TEXT_INSTCONFIRM_SUBTITLE "A telepítõ begyûjtötte az információkat és készen áll a(z) $(^NameDA) telepítésére."
  ${LangFileString} UMUI_TEXT_INSTCONFIRM_TITLE "Telepítés megerõsítése"
  ${LangFileString} UMUI_TEXT_INSTCONFIRM_TEXT_TOP "A telepítõ készen áll a(z) $(^NameDA) telepítésére.$\r$\nHa át akarja nézni vagy módosítani a telepítési beállításokat, kattintson a Vissza gombra. $_CLICK"
!endif

!ifdef UMUI_UNCONFIRMPAGE
  ${LangFileString} UMUI_UNTEXT_INSTCONFIRM_SUBTITLE "A telepítõ begyûjtötte az információkat és készen áll a(z) $(^NameDA) eltávolítására."
  ${LangFileString} UMUI_UNTEXT_INSTCONFIRM_TITLE "Eltávolítás megerõsítése"
  ${LangFileString} UMUI_UNTEXT_INSTCONFIRM_TEXT_TOP "A telepítõ készen áll a(z) $(^NameDA) eltávolítására.$\r$\nHa át akarja nézni vagy módosítani az eltávolítási beállításokat, kattintson a Vissza gombra. A Tovább gombbal elkezdõdik az eltávolítás."
!endif

!ifdef UMUI_CONFIRMPAGE | UMUI_UNCONFIRMPAGE
  ${LangFileString} UMUI_TEXT_INSTCONFIRM_TEXTBOX_TITLE "Aktuális beállítás:"
  ${LangFileString} UMUI_TEXT_INSTCONFIRM_TEXTBOX_DESTINATION_LOCATION "Telepítési hely:"
  ${LangFileString} UMUI_TEXT_INSTCONFIRM_TEXTBOX_START_MENU_FOLDER "Start menü mappa:"
  ${LangFileString} UMUI_TEXT_INSTCONFIRM_TEXTBOX_COMPNENTS "A következõ összetevõk lesznek telepítve:"
!endif


!ifdef UMUI_ABORTPAGE
  ${LangFileString} UMUI_TEXT_ABORT_INFO_TITLE "A(z) $(^NameDA) Telepítõ Varázsló befejezõdött"
  ${LangFileString} UMUI_TEXT_ABORT_INFO_TEXT "A varázsló megszakadt, mielõtt a(z) $(^NameDA) sikeresen telepítésre került volna.$\r$\n$\r$\nA program késõbbi telepítéséhez, futtassa újra a telepítõt.$\r$\n$\r$\n$\r$\n$\r$\nA $(^CloseBtn) gombbal kiléphet a Telepítõ Varázslóból."
!endif

!ifdef UMUI_UNABORTPAGE
  ${LangFileString} UMUI_UNTEXT_ABORT_INFO_TITLE "A(z) $(^NameDA) Eltávolítás Varázsló befejezõdött"
  ${LangFileString} UMUI_UNTEXT_ABORT_INFO_TEXT "A varázsló megszakadt, mielõtt a(z) $(^NameDA) sikeresen eltávolításra került volna.$\r$\n$\r$\nA program késõbbi eltávolításához, futtassa újra az eltávolítót.$\r$\n$\r$\n$\r$\n$\r$\nA $(^CloseBtn) gombbal kiléphet az Eltávolítás Varázslóból."
!endif


!ifdef UMUI_SETUPTYPEPAGE
  ${LangFileString} UMUI_TEXT_SETUPTYPE_TITLE "Telepítési típus"
  ${LangFileString} UMUI_TEXT_SETUPTYPE_SUBTITLE "Válassza ki a kívánt telepítési típust."
  ${LangFileString} UMUI_TEXT_SETUPTYPE_INFO_TEXT "Válasszon egy telepítési típust."
  ${LangFileString} UMUI_TEXT_SETUPTYPE_MINIMAL_TEXT "Csak a szükséges szolgáltatások lesznek telepítve. (Kevesebb lemezterület szükséges)"
  ${LangFileString} UMUI_TEXT_SETUPTYPE_STANDARD_TEXT "Minden fõ szolgáltatás telepítve lesz. A legtöbb felhasználónak ajánlott."
  ${LangFileString} UMUI_TEXT_SETUPTYPE_COMPLETE_TEXT "Minden szolgáltatás telepítve lesz. (A legtöbb lemezterület szükséges)"
  ${LangFileString} UMUI_TEXT_SETUPTYPE_CUSTOM_TEXT "Kiválasztható mely program szolgáltatások települjenek és hova. Haladó felhasználóknak ajánlott."
!endif

!ifdef UMUI_UNSETUPTYPEPAGE
  ${LangFileString} UMUI_UNTEXT_SETUPTYPE_TITLE "Eltávolítási típus"
  ${LangFileString} UMUI_UNTEXT_SETUPTYPE_SUBTITLE "Válassza ki a kívánt eltávolítási típust."
  ${LangFileString} UMUI_UNTEXT_SETUPTYPE_INFO_TEXT "Válasszon egy eltávolítási típust."
  ${LangFileString} UMUI_UNTEXT_SETUPTYPE_MINIMAL_TEXT "Csak a fõ szolgáltatások maradnak meg."
  ${LangFileString} UMUI_UNTEXT_SETUPTYPE_STANDARD_TEXT "Csak a szükséges szolgáltatások maradnak meg."
  ${LangFileString} UMUI_UNTEXT_SETUPTYPE_COMPLETE_TEXT "Minden program szolgáltatás el lesz távolítva."
  ${LangFileString} UMUI_UNTEXT_SETUPTYPE_CUSTOM_TEXT "Kiválasztható mely program szolgáltatások kerüljenek eltávolításra."
!endif

!ifdef UMUI_SETUPTYPEPAGE | UMUI_UNSETUPTYPEPAGE
  ${LangFileString} UMUI_TEXT_SETUPTYPE_MINIMAL_TITLE "Minimális"
  ${LangFileString} UMUI_TEXT_SETUPTYPE_STANDARD_TITLE "Általános"
  ${LangFileString} UMUI_TEXT_SETUPTYPE_COMPLETE_TITLE "Teljes"
  ${LangFileString} UMUI_TEXT_SETUPTYPE_CUSTOM_TITLE "Egyéni"
!endif


!ifdef UMUI_INFORMATIONPAGE
  ${LangFileString} UMUI_TEXT_INFORMATION_SUBTITLE "Olvassa el a(z) $(^NameDA) telepítésére vonatkozó információkat."
!endif

!ifdef UMUI_UNINFORMATIONPAGE
  ${LangFileString} UMUI_UNTEXT_INFORMATION_SUBTITLE "Olvassa el a(z) $(^NameDA) eltávolítására vonatkozó információkat."
!endif

!ifdef UMUI_INFORMATIONPAGE | UMUI_UNINFORMATIONPAGE
  ${LangFileString} UMUI_TEXT_INFORMATION_TITLE "Információ"
  ${LangFileString} UMUI_TEXT_INFORMATION_INFO_TEXT "A(z) $(^NameDA) kapcsolódó információi."
!endif


!ifdef UMUI_ADDITIONALTASKSPAGE
  ${LangFileString} UMUI_TEXT_ADDITIONALTASKS_INFO_TEXT "Válasszon további feladatot, melyet a telepítõ végrehajt a(z) $(^NameDA) telepítése során. $_CLICK"
!endif

!ifdef UMUI_UNADDITIONALTASKSPAGE
  ${LangFileString} UMUI_UNTEXT_ADDITIONALTASKS_INFO_TEXT "Válasszon további feladatot, melyet a telepítõ végrehajt a(z) $(^NameDA) eltávolítása során. $_CLICK"
!endif

!ifdef UMUI_ADDITIONALTASKSPAGE | UMUI_UNADDITIONALTASKSPAGE
  ${LangFileString} UMUI_TEXT_ADDITIONALTASKS_TITLE "További feladatok"
  ${LangFileString} UMUI_TEXT_ADDITIONALTASKS_SUBTITLE "Mely további feladatot kell végrehajtani?"
  ${LangFileString} UMUI_TEXT_ADDITIONALTASKS_ADDITIONAL_ICONS "További ikonok:"
  ${LangFileString} UMUI_TEXT_ADDITIONALTASKS_CREATE_DESKTOP_ICON "Asztali ikon létrehozása"
  ${LangFileString} UMUI_TEXT_ADDITIONALTASKS_CREATE_QUICK_LAUNCH_ICON "Gyorsindító ikon létrehozása"
  ${LangFileString} UMUI_TEXT_ADDITIONALTASKS_ADVANCED_PARAMETERS "További paraméterek:"
  ${LangFileString} UMUI_TEXT_ADDITIONALTASKS_LAUNCH_PROGRAM_AT_WINDOWS_STARTUP "A(z) $(^NameDA) indítása a Windows-al"
  ${LangFileString} UMUI_TEXT_ADDITIONALTASKS_FILE_ASSOCIATION "Fájl társítása:"
  ${LangFileString} UMUI_TEXT_ADDITIONALTASKS_ASSOCIATE_WITH "$(^NameDA) társítása a(z) "
  ${LangFileString} UMUI_TEXT_ADDITIONALTASKS_ASSOCIATE_WITH_END " fájltípussal"
!endif
  
  
!ifdef UMUI_CONFIRMPAGE | UMUI_UNCONFIRMPAGE | UMUI_ALTERNATIVESTARTMENUPAGE | UMUI_UNALTERNATIVESTARTMENUPAGE
  ${LangFileString} UMUI_TEXT_SHELL_VAR_CONTEXT "Parancsikonok létrehozása:"
  ${LangFileString} UMUI_TEXT_SHELL_VAR_CONTEXT_FOR_ALL_USERS "Minden felhasználónak"
  ${LangFileString} UMUI_TEXT_SHELL_VAR_CONTEXT_ONLY_FOR_CURRENT_USER "Csak az aktuális felhasználónak"
!endif


!ifdef UMUI_UPDATEPAGE
  ${LangFileString} UMUI_TEXT_UPDATE_TITLE "Frissítés"
  ${LangFileString} UMUI_TEXT_UPDATE_SUBTITLE "A program korábbi verziójának frissítése."
  ${LangFileString} UMUI_TEXT_UPDATE_INFO_TEXT "Üdvözli a(z) $(^NameDA) frissítõ varázsló.$\r$\nEz a program frissíti a számítógépen található $OLDVERSION verziót."
  ${LangFileString} UMUI_TEXT_UPDATE_UPDATE_TITLE "Frissítés"
  ${LangFileString} UMUI_TEXT_UPDATE_UPDATE_TEXT "A(z) $(^NameDA) minden, már telepített elemének frissítése $NEWVERSION verzióra."
  ${LangFileString} UMUI_TEXT_UPDATE_REMOVE_TITLE "Eltávolítás"
  ${LangFileString} UMUI_TEXT_UPDATE_REMOVE_TEXT "A(z) $OLDVERSION verzióra eltávolítása a számítógéprõl."
  ${LangFileString} UMUI_TEXT_UPDATE_CONTINUE_TITLE "Telepítés folytatása"
  ${LangFileString} UMUI_TEXT_UPDATE_CONTINUE_TEXT "Telepítés folytatása a megszokott módon. Ez az opció akkor ajánlott, ha egy létezõ telepítésre akarja újratelepíteni a programot vagy ezúttal egy másik mappába telepítené."
!endif


!ifdef UMUI_MAINTENANCEPAGE | UMUI_UNMAINTENANCEPAGE
  ${LangFileString} UMUI_TEXT_MAINTENANCE_TITLE "Karbantartás"
  ${LangFileString} UMUI_TEXT_MAINTENANCE_SUBTITLE "A program módosítása, javítása vagy eltávolítása."
  ${LangFileString} UMUI_TEXT_MAINTENANCE_INFO_TEXT "Üdvözli a(z) $(^NameDA) telepítõ karbantartó programja.$\r$\nA programmal módosíthatja az aktuális telepítést."
  ${LangFileString} UMUI_TEXT_MAINTENANCE_MODIFY_TITLE "Módosítás"
  ${LangFileString} UMUI_TEXT_MAINTENANCE_MODIFY_TEXT "Új összetevõk telepíthetõk fel vagy már telepítettek távolíthatók el."
  ${LangFileString} UMUI_TEXT_MAINTENANCE_REPAIR_TITLE "Javítás"
  ${LangFileString} UMUI_TEXT_MAINTENANCE_REPAIR_TEXT "A(z) $(^NameDA) minden telepített összetevõjének újratelepítése."
  ${LangFileString} UMUI_TEXT_MAINTENANCE_REMOVE_TITLE "Eltávolítás"
  ${LangFileString} UMUI_TEXT_MAINTENANCE_REMOVE_TEXT "A(z) $(^NameDA) eltávolítása a számítógéprõl."
  ${LangFileString} UMUI_TEXT_MAINTENANCE_CONTINUE_TITLE "Telepítés folytatása"
  ${LangFileString} UMUI_TEXT_MAINTENANCE_CONTINUE_TEXT "Telepítés folytatása a megszokott módon. Ez az opció akkor ajánlott, ha egy létezõ telepítésre akarja újratelepíteni a programot vagy ezúttal egy másik mappába telepítené."
!endif


!ifdef UMUI_FILEDISKREQUESTPAGE | UMUI_UNFILEDISKREQUESTPAGE
  ${LangFileString} UMUI_TEXT_FILEDISKREQUEST_FILE_SUBTITLE_BEGIN "A telepítéshez szükséges a(z)"
  ${LangFileString} UMUI_TEXT_FILEDISKREQUEST_FILE_SUBTITLE_END "fájl a folytatáshoz."
  ${LangFileString} UMUI_TEXT_FILEDISKREQUEST_DISK_SUBTITLE "A telepítéshez szükséges a következõ lemez a folytatáshoz."
  ${LangFileString} UMUI_TEXT_FILEDISKREQUEST_FILE_BEGIN "Adja meg a fájl elérését"
  ${LangFileString} UMUI_TEXT_FILEDISKREQUEST_FILE_END "a folytatáshoz."
  ${LangFileString} UMUI_TEXT_FILEDISKREQUEST_DISK "Helyezze be:"
  ${LangFileString} UMUI_TEXT_FILEDISKREQUEST_PATH "Elérés:"
!endif
