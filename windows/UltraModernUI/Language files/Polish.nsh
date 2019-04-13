;NSIS Modern User Interface - Language File
;Compatible with UltraModernUI 2.0 beta 1

;Language: Polish (1045)
;By forge
;--------------------------------

!ifdef UMUI_MULTILANGUAGEPAGE
  ${LangFileString} UMUI_TEXT_MULTILANGUAGE_TITLE "Witamy w instalatorze $(^NameDA)"
  ${LangFileString} UMUI_TEXT_MULTILANGUAGE_TEXT "Przed rozpoczêciem instalacji $(^NameDA), proszê wybraæ jêzyk:$\r$\n$\r$\n$_CLICK"
!endif

!ifdef UMUI_UNMULTILANGUAGEPAGE
  ${LangFileString} UMUI_UNTEXT_MULTILANGUAGE_TITLE "Witamy w deinstalatorze $(^NameDA)"
  ${LangFileString} UMUI_UNTEXT_MULTILANGUAGE_TEXT "Przed rozpoczêciem deinstalacji $(^NameDA), proszê wybraæ jêzyk:$\r$\n$\r$\n$_CLICK"
!endif

!ifdef UMUI_MULTILANGUAGEPAGE | UMUI_UNMULTILANGUAGEPAGE
  ${LangFileString} UMUI_TEXT_MULTILANGUAGE_LANGUAGE "Jêzyk:"
!endif


!ifdef MUI_WELCOMEPAGE
  ${LangFileString} UMUI_TEXT_WELCOME_ALTERNATIVEINFO_TEXT "Ten przewodnik przeprowadzi Ciê przez proces instalacji $(^NameDA).$\r$\n$\r$\n$\r$\n$_CLICK"
!endif


!ifdef UMUI_SERIALNUMBERPAGE | UMUI_UNSERIALNUMBERPAGE
  ${LangFileString} UMUI_TEXT_SERIALNUMBER_TITLE "WprowadŸ numer seryjny dla $(^NameDA)"
  ${LangFileString} UMUI_TEXT_SERIALNUMBER_SUBTITLE "Proszê wype³nij pola poni¿ej."
  ${LangFileString} UMUI_TEXT_SERIALNUMBER_INFO_TEXT "Proszê wype³nij pola poni¿ej. $_CLICK"
  ${LangFileString} UMUI_TEXT_SERIALNUMBER_INVALIDATE_TEXT "$UMUI_SNTEXT jest nieprawid³owy. Proszê sprawdŸ wprowadzone informacje."
  ${LangFileString} UMUI_TEXT_SERIALNUMBER_NAME "Nazwa"
  ${LangFileString} UMUI_TEXT_SERIALNUMBER_ORGANIZATION "Organizacja"
  ${LangFileString} UMUI_TEXT_SERIALNUMBER_SERIALNUMBER "Numer Seryjny"
  ${LangFileString} UMUI_TEXT_SERIALNUMBER_ACTIVATIONCODE "Kod Aktywacyjny"
  ${LangFileString} UMUI_TEXT_SERIALNUMBER_PASSWORD "Has³o"
!endif


!ifdef UMUI_CONFIRMPAGE
  ${LangFileString} UMUI_TEXT_INSTCONFIRM_SUBTITLE "Instalator zakoñczy³ zbieranie informacji i jest gotowy do instalacji $(^NameDA)."
  ${LangFileString} UMUI_TEXT_INSTCONFIRM_TITLE "PotwierdŸ chêæ instalacji"
  ${LangFileString} UMUI_TEXT_INSTCONFIRM_TEXT_TOP "Instalator jest gotowy do instalacji $(^NameDA) na Twoim komputerze.$\r$\nJeœli chcesz sprawdziæ lub zmieniæ ustawienia instalatora, kliknij Wstecz. $_CLICK"
!endif

!ifdef UMUI_UNCONFIRMPAGE
  ${LangFileString} UMUI_UNTEXT_INSTCONFIRM_SUBTITLE "Instalator zakoñczy³ zbieranie informacji i jest gotowy do deinstalacji $(^NameDA)."
  ${LangFileString} UMUI_UNTEXT_INSTCONFIRM_TITLE "PotwierdŸ chêæ Deinstalacji"
  ${LangFileString} UMUI_UNTEXT_INSTCONFIRM_TEXT_TOP "Instalator jest gotowy do deinstalacji $(^NameDA) z Twojego komputera.$\r$\nJeœli chcesz sprawdziæ lub zmieniæ ustawienia deinstalatora, kliknij Wstecz. Kliknij Dalej aby rozpocz¹æ deinstalacjê."
!endif

!ifdef UMUI_CONFIRMPAGE | UMUI_UNCONFIRMPAGE
  ${LangFileString} UMUI_TEXT_INSTCONFIRM_TEXTBOX_TITLE "Obecna konfiguracja:"
  ${LangFileString} UMUI_TEXT_INSTCONFIRM_TEXTBOX_DESTINATION_LOCATION "Lokalizacja docelowa:"
  ${LangFileString} UMUI_TEXT_INSTCONFIRM_TEXTBOX_START_MENU_FOLDER "Katalog w Menu Start:"
  ${LangFileString} UMUI_TEXT_INSTCONFIRM_TEXTBOX_COMPNENTS "Natêpuj¹ce sk³¹dniki zostan¹ zainstalowane:"
!endif


!ifdef UMUI_ABORTPAGE
  ${LangFileString} UMUI_TEXT_ABORT_INFO_TITLE "Koñczenie instalacji $(^NameDA)"
!endif
  ${LangFileString} UMUI_TEXT_ABORT_INFO_TEXT "Praca instalatora $(^NameDA) zosta³a przerwana przed zakoñczeniem instalcji.$\r$\n$\r$\nAby póŸnije zainstalowaæ program, proszê uruchomiæ instalator ponownie.$\r$\n$\r$\n$\r$\n$\r$\nKliknij $(^CloseBtn) aby opuœciæ instalator."

!ifdef UMUI_UNABORTPAGE
  ${LangFileString} UMUI_UNTEXT_ABORT_INFO_TITLE "Koñczenie deinstalacji $(^NameDA)"
  ${LangFileString} UMUI_UNTEXT_ABORT_INFO_TEXT "Praca deinstalatora $(^NameDA) zosta³a przerwana przed zakoñczeniem deinstalcji.$\r$\n$\r$\nAby póŸniej odinstalowaæ program, proszê uruchomiæ deinstaltor ponownie.$\r$\n$\r$\n$\r$\n$\r$\nKliknij $(^CloseBtn) aby opuœciæ deinstalator."
!endif


!ifdef UMUI_SETUPTYPEPAGE
  ${LangFileString} UMUI_TEXT_SETUPTYPE_TITLE "Typ instalacji"
  ${LangFileString} UMUI_TEXT_SETUPTYPE_SUBTITLE "Wybierz typ instalacji, który najbardziej odpowiada Twoim potrzebom."
  ${LangFileString} UMUI_TEXT_SETUPTYPE_INFO_TEXT "Proszê wybraæ typ instalacji."
  ${LangFileString} UMUI_TEXT_SETUPTYPE_MINIMAL_TEXT "Tylko niezbêdne sk³adniki programu zostan¹ zainstalowane. (Wymaga najmniej miejsca na dysku)"
  ${LangFileString} UMUI_TEXT_SETUPTYPE_STANDARD_TEXT "Najwa¿niejsze sk³adniki programu zostanê zainstalowane. Sugerowana dla wiekszoœci u¿ytkowników."
  ${LangFileString} UMUI_TEXT_SETUPTYPE_COMPLETE_TEXT "Wszystkie sk³adniki programu zostan¹ zainstalowane. (Wymaga najwiecej miejsca na dysku)"
  ${LangFileString} UMUI_TEXT_SETUPTYPE_CUSTOM_TEXT "Wybierz które sk³¹dniki programu chcesz zainstalowaæ i gdzie maj¹ byæ zainstalowane. Zalecane dla u¿ytkowników zaawansowanych."
!endif

!ifdef UMUI_UNSETUPTYPEPAGE
  ${LangFileString} UMUI_UNTEXT_SETUPTYPE_TITLE "Typ deinstalacji"
  ${LangFileString} UMUI_UNTEXT_SETUPTYPE_SUBTITLE "Wybierz typ deinstalacji, który najbardziej odpowiada Twoim potrzebom."
  ${LangFileString} UMUI_UNTEXT_SETUPTYPE_INFO_TEXT "Proszê wybraæ typ deinstalacji."
  ${LangFileString} UMUI_UNTEXT_SETUPTYPE_MINIMAL_TEXT "Najwa¿niejsze sk³adniki programu zostan¹ zachowane."
  ${LangFileString} UMUI_UNTEXT_SETUPTYPE_STANDARD_TEXT "Tylko niezbêdne sk³adniki programu zostan¹ zachowane."
  ${LangFileString} UMUI_UNTEXT_SETUPTYPE_COMPLETE_TEXT "Wszystkie sk³adniki programu zostan¹ odinstalowane."
  ${LangFileString} UMUI_UNTEXT_SETUPTYPE_CUSTOM_TEXT "Wybierz które sk³adniki programu chcesz odinstalowaæ."
!endif

!ifdef UMUI_SETUPTYPEPAGE | UMUI_UNSETUPTYPEPAGE
  ${LangFileString} UMUI_TEXT_SETUPTYPE_MINIMAL_TITLE "Minimalna"
  ${LangFileString} UMUI_TEXT_SETUPTYPE_STANDARD_TITLE "Standardowa"
  ${LangFileString} UMUI_TEXT_SETUPTYPE_COMPLETE_TITLE "Kompletna"
  ${LangFileString} UMUI_TEXT_SETUPTYPE_CUSTOM_TITLE "U¿ytkownika"
!endif


!ifdef UMUI_INFORMATIONPAGE
  ${LangFileString} UMUI_TEXT_INFORMATION_SUBTITLE "SprawdŸ informacje dotycz¹ce instalacji programu $(^NameDA)."
!endif

!ifdef UMUI_UNINFORMATIONPAGE
  ${LangFileString} UMUI_UNTEXT_INFORMATION_SUBTITLE "SprawdŸ informacje dotycz¹ce deinstalacji programu $(^NameDA)."
!endif

!ifdef UMUI_INFORMATIONPAGE | UMUI_UNINFORMATIONPAGE
  ${LangFileString} UMUI_TEXT_INFORMATION_TITLE "Informacje"
  ${LangFileString} UMUI_TEXT_INFORMATION_INFO_TEXT "Informacje dotycz¹ce $(^NameDA)."
!endif


!ifdef UMUI_ADDITIONALTASKSPAGE
  ${LangFileString} UMUI_TEXT_ADDITIONALTASKS_INFO_TEXT "Wybierz dodatkowe zadania, które powinny byæ wykonane podczas procesu instalcji $(^NameDA). $_CLICK"
!endif

!ifdef UMUI_UNADDITIONALTASKSPAGE
  ${LangFileString} UMUI_UNTEXT_ADDITIONALTASKS_INFO_TEXT "Wybierz dodatkowe zadania, które powinny byæ wykonane podczas procesu deinstalcji $(^NameDA). $_CLICK"
!endif

!ifdef UMUI_ADDITIONALTASKSPAGE | UMUI_UNADDITIONALTASKSPAGE
  ${LangFileString} UMUI_TEXT_ADDITIONALTASKS_TITLE "Dodatkowe Zadania"
  ${LangFileString} UMUI_TEXT_ADDITIONALTASKS_SUBTITLE "Które z dodatkowych czynnoœci chcesz wykonaæ?"
  ${LangFileString} UMUI_TEXT_ADDITIONALTASKS_ADDITIONAL_ICONS "Dodatkowe ikony:"
  ${LangFileString} UMUI_TEXT_ADDITIONALTASKS_CREATE_DESKTOP_ICON "Utwórz ikone na pulpicie"
  ${LangFileString} UMUI_TEXT_ADDITIONALTASKS_CREATE_QUICK_LAUNCH_ICON "Utwórz ikone w pasku szybkiego uruchamiania"
  ${LangFileString} UMUI_TEXT_ADDITIONALTASKS_ADVANCED_PARAMETERS "Zaawansowane ustawienia:"
  ${LangFileString} UMUI_TEXT_ADDITIONALTASKS_LAUNCH_PROGRAM_AT_WINDOWS_STARTUP "Uruchom $(^NameDA) przy starcie systemu windows"
  ${LangFileString} UMUI_TEXT_ADDITIONALTASKS_FILE_ASSOCIATION "Skojarzenia plików:"
  ${LangFileString} UMUI_TEXT_ADDITIONALTASKS_ASSOCIATE_WITH "Skojarz $(^NameDA) z "
  ${LangFileString} UMUI_TEXT_ADDITIONALTASKS_ASSOCIATE_WITH_END " typem pliku"
!endif
  
  
!ifdef UMUI_CONFIRMPAGE | UMUI_UNCONFIRMPAGE | UMUI_ALTERNATIVESTARTMENUPAGE | UMUI_UNALTERNATIVESTARTMENUPAGE
  ${LangFileString} UMUI_TEXT_SHELL_VAR_CONTEXT "Jak utworzyæ skróty:"
  ${LangFileString} UMUI_TEXT_SHELL_VAR_CONTEXT_FOR_ALL_USERS "Dla wszystkich u¿ytkowników"
  ${LangFileString} UMUI_TEXT_SHELL_VAR_CONTEXT_ONLY_FOR_CURRENT_USER "Tylko dla obecnego u¿ytkownika"
!endif


!ifdef UMUI_UPDATEPAGE
  ${LangFileString} UMUI_TEXT_UPDATE_TITLE "Aktualizacja"
  ${LangFileString} UMUI_TEXT_UPDATE_SUBTITLE "Aktualizuj poprzeni¹ wersjê programu."
  ${LangFileString} UMUI_TEXT_UPDATE_INFO_TEXT "Witaj w przewodniku aktualizacji $(^NameDA).$\r$\nTen program pozwoli Ci zaktualizaowaæ wersjê $OLDVERSION znalezion¹ na Twoim komputerze."
  ${LangFileString} UMUI_TEXT_UPDATE_UPDATE_TITLE "Aktualizuj"
  ${LangFileString} UMUI_TEXT_UPDATE_UPDATE_TEXT "Aktualizuj wszystkie zainstalowne sk³adniki $(^NameDA) do wersji $NEWVERSION.."
  ${LangFileString} UMUI_TEXT_UPDATE_REMOVE_TITLE "Usuñ"
  ${LangFileString} UMUI_TEXT_UPDATE_REMOVE_TEXT "Odinstaluj wersjê $OLDVERSION z Twojego komputera."
  ${LangFileString} UMUI_TEXT_UPDATE_CONTINUE_TITLE "Kontynuowanie instalacji"
  ${LangFileString} UMUI_TEXT_UPDATE_CONTINUE_TEXT "Kontynuuj normaln¹ instalacje. U¿yj tej opcji aby zainstalowaæ nowasz¹ wersjê w innym katalogu ni¿ dotychczasowa instalacja."
!endif


!ifdef UMUI_MAINTENANCEPAGE | UMUI_UNMAINTENANCEPAGE
  ${LangFileString} UMUI_TEXT_MAINTENANCE_TITLE "Konserwacja"
  ${LangFileString} UMUI_TEXT_MAINTENANCE_SUBTITLE "Modyfikuj, napraw, lub usuñ program."
  ${LangFileString} UMUI_TEXT_MAINTENANCE_INFO_TEXT "Witamy w instalatorze programu $(^NameDA).$\r$\nTen program umo¿liwi Ci modyfikacjê obecnej instalacji."
  ${LangFileString} UMUI_TEXT_MAINTENANCE_MODIFY_TITLE "Modyfikuj"
  ${LangFileString} UMUI_TEXT_MAINTENANCE_MODIFY_TEXT "Zaznacz nowe sk³adniki do dodanie lub zaznacz ju¿ zainstalowane aby je usun¹æ."
  ${LangFileString} UMUI_TEXT_MAINTENANCE_REPAIR_TITLE "Napraw"
  ${LangFileString} UMUI_TEXT_MAINTENANCE_REPAIR_TEXT "Reinstaluje wszystkie sk³adniki $(^NameDA), które ju¿ zosta³y zainstalwane."
  ${LangFileString} UMUI_TEXT_MAINTENANCE_REMOVE_TITLE "Usuñ"
  ${LangFileString} UMUI_TEXT_MAINTENANCE_REMOVE_TEXT "Odinstaluj $(^NameDA) z Twojego komputera."
  ${LangFileString} UMUI_TEXT_MAINTENANCE_CONTINUE_TITLE "Kontynuowanie instalacji"
  ${LangFileString} UMUI_TEXT_MAINTENANCE_CONTINUE_TEXT "Kontynuuj normaln¹ instalacje. U¿yj tej opcji aby przeinstalowaæ Use this option if you want to reinstall this program over an existing install or to install it a new time in a different folder."
!endif


!ifdef UMUI_FILEDISKREQUESTPAGE | UMUI_UNFILEDISKREQUESTPAGE
  ${LangFileString} UMUI_TEXT_FILEDISKREQUEST_FILE_SUBTITLE_BEGIN "Instalator potrzebuje"
  ${LangFileString} UMUI_TEXT_FILEDISKREQUEST_FILE_SUBTITLE_END "pliku aby kontynuowaæ."
  ${LangFileString} UMUI_TEXT_FILEDISKREQUEST_DISK_SUBTITLE "Instaltor potrzebuje kolejnego dysku."
  ${LangFileString} UMUI_TEXT_FILEDISKREQUEST_FILE_BEGIN "WprowadŸ lokalizacje pliku"
  ${LangFileString} UMUI_TEXT_FILEDISKREQUEST_FILE_END "aby kontynuowaæ."
  ${LangFileString} UMUI_TEXT_FILEDISKREQUEST_DISK "Proszê w³ó¿"
  ${LangFileString} UMUI_TEXT_FILEDISKREQUEST_PATH "Œcie¿ka:"
!endif
