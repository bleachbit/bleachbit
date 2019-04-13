;NSIS Modern User Interface - Language File
;Compatible with UltraModernUI 2.0 beta 1

;Language: German (1031)
;By Tobias <tm2006@users.sourceforge.net>
;Changes by Matthias <bodenseematze@users.sourceforge.net>
;--------------------------------

!ifdef UMUI_MULTILANGUAGEPAGE
  ${LangFileString} UMUI_TEXT_MULTILANGUAGE_TITLE "Willkommen zur Installation von $(^NameDA)"
  ${LangFileString} UMUI_TEXT_MULTILANGUAGE_TEXT "Wählen Sie bitte eine Sprache für die Installation von $(^NameDA) aus:$\r$\n$\r$\n$_CLICK"
!endif

!ifdef UMUI_UNMULTILANGUAGEPAGE
  ${LangFileString} UMUI_UNTEXT_MULTILANGUAGE_TITLE "Willkommen zur Deinstallation von $(^NameDA)"
  ${LangFileString} UMUI_UNTEXT_MULTILANGUAGE_TEXT "Wählen Sie bitte eine Sprache für die Deinstallation von $(^NameDA) aus:$\r$\n$\r$\n$_CLICK"
!endif

!ifdef UMUI_MULTILANGUAGEPAGE | UMUI_UNMULTILANGUAGEPAGE
  ${LangFileString} UMUI_TEXT_MULTILANGUAGE_LANGUAGE "Sprache:"
!endif


!ifdef MUI_WELCOMEPAGE
  ${LangFileString} UMUI_TEXT_WELCOME_ALTERNATIVEINFO_TEXT "Dieser Assistent führt durch die Installation von $(^NameDA).$\r$\n$\r$\n$\r$\n$_CLICK"
!endif


!ifdef UMUI_SERIALNUMBERPAGE | UMUI_UNSERIALNUMBERPAGE
  ${LangFileString} UMUI_TEXT_SERIALNUMBER_TITLE "Geben Sie bitte die Seriennummer zu $(^NameDA) ein"
  ${LangFileString} UMUI_TEXT_SERIALNUMBER_SUBTITLE "Bitte füllen Sie die verschiedenen Felder aus."
  ${LangFileString} UMUI_TEXT_SERIALNUMBER_INFO_TEXT "Bitte füllen Sie die verschiedenen Felder aus. $_CLICK"
  ${LangFileString} UMUI_TEXT_SERIALNUMBER_INVALIDATE_TEXT "$UMUI_SNTEXT ist ungültig. Bitte überprüfen Sie die eingegebenen Informationen."
  ${LangFileString} UMUI_TEXT_SERIALNUMBER_NAME "Name"
  ${LangFileString} UMUI_TEXT_SERIALNUMBER_ORGANIZATION "Organisation"
  ${LangFileString} UMUI_TEXT_SERIALNUMBER_SERIALNUMBER "Seriennummer"
  ${LangFileString} UMUI_TEXT_SERIALNUMBER_ACTIVATIONCODE "Aktivierungscode"
  ${LangFileString} UMUI_TEXT_SERIALNUMBER_PASSWORD "Passwort"
!endif


!ifdef UMUI_CONFIRMPAGE
  ${LangFileString} UMUI_TEXT_INSTCONFIRM_SUBTITLE "Die benötigten Informationen wurden gesammelt um $(^NameDA) zu installieren."
  ${LangFileString} UMUI_TEXT_INSTCONFIRM_TITLE "Installation bestätigen"
  ${LangFileString} UMUI_TEXT_INSTCONFIRM_TEXT_TOP "Der Assistent ist bereit, $(^NameDA) auf den Computer zu installieren.$\r$\nFalls die Installationseinstellungen noch überprüft oder geändert werden sollen, klicken Sie auf $(^BackBtn). $_CLICK"
!endif

!ifdef UMUI_UNCONFIRMPAGE
  ${LangFileString} UMUI_UNTEXT_INSTCONFIRM_SUBTITLE "Die benötigten Informationen wurden gesammelt um $(^NameDA) zu deinstallieren."
  ${LangFileString} UMUI_UNTEXT_INSTCONFIRM_TITLE "Deinstallation bestätigen"
  ${LangFileString} UMUI_UNTEXT_INSTCONFIRM_TEXT_TOP "Der Assistent ist bereit, $(^NameDA) vom Computer zu entfernen.$\r$\nFalls die Deinstallationseinstellungen noch überprüft oder geändert werden sollen, klicken Sie auf $(^BackBtn). Klicken Sie auf $(^NextBtn), um die Deinstallation zu beginnen."
!endif

!ifdef UMUI_CONFIRMPAGE | UMUI_UNCONFIRMPAGE
  ${LangFileString} UMUI_TEXT_INSTCONFIRM_TEXTBOX_TITLE "Derzeitige Konfiguration:"
  ${LangFileString} UMUI_TEXT_INSTCONFIRM_TEXTBOX_DESTINATION_LOCATION "Zielort:"
  ${LangFileString} UMUI_TEXT_INSTCONFIRM_TEXTBOX_START_MENU_FOLDER "Startmenüordner:"
  ${LangFileString} UMUI_TEXT_INSTCONFIRM_TEXTBOX_COMPNENTS "Die folgenden Komponenten werden installiert:"
!endif


!ifdef UMUI_ABORTPAGE
  ${LangFileString} UMUI_TEXT_ABORT_INFO_TITLE "Beenden des $(^NameDA) Installationsassistenten"
  ${LangFileString} UMUI_TEXT_ABORT_INFO_TEXT "Der Assistent wurde unterbrochen, bevor $(^NameDA) komplett installiert werden konnte.$\r$\n$\r$\nUm das Programm zu einem späteren Zeitpunkt zu installieren, führen Sie diese Installation bitte erneut aus.$\r$\n$\r$\n$\r$\n$\r$\nKlicken Sie auf $(^CloseBtn), um den Installationsassistenten zu schließen."
!endif

!ifdef UMUI_UNABORTPAGE
  ${LangFileString} UMUI_UNTEXT_ABORT_INFO_TITLE "Beenden des Deinstallationsassistenten für $(^NameDA)"
  ${LangFileString} UMUI_UNTEXT_ABORT_INFO_TEXT "Der Assistent wurde unterbrochen, bevor $(^NameDA) komplett deinstalliert werden konnte.$\r$\n$\r$\nUm das Programm zu einem späteren Zeitpunkt zu deinstallieren, führen Sie diese Installation bitte erneut aus.$\r$\n$\r$\n$\r$\n$\r$\nKlicken Sie auf $(^CloseBtn), um den Deinstallationsassistenten zu schließen."
!endif


!ifdef UMUI_SETUPTYPEPAGE
  ${LangFileString} UMUI_TEXT_SETUPTYPE_TITLE "Installationsart"
  ${LangFileString} UMUI_TEXT_SETUPTYPE_SUBTITLE "Auswahl der passenden Installationsart"
  ${LangFileString} UMUI_TEXT_SETUPTYPE_INFO_TEXT "Wählen Sie bitte eine Installationsart aus."
  ${LangFileString} UMUI_TEXT_SETUPTYPE_MINIMAL_TEXT "Nur die benötigten Funktionen werden installiert. (Benötigt den geringsten Speicherplatz)"
  ${LangFileString} UMUI_TEXT_SETUPTYPE_STANDARD_TEXT "Alle Hauptfunktionen werden installiert. Empfohlen für die meisten Anwender."
  ${LangFileString} UMUI_TEXT_SETUPTYPE_COMPLETE_TEXT "Alle Programmfunktionen werden installiert. (Benötigt den meisten Speicherplatz)"
  ${LangFileString} UMUI_TEXT_SETUPTYPE_CUSTOM_TEXT "Wählen Sie aus, welche Programmfunktionalität wohin installiert werden soll. Empfohlen für fortgeschrittene Anwender."
!endif

!ifdef UMUI_UNSETUPTYPEPAGE
  ${LangFileString} UMUI_UNTEXT_SETUPTYPE_TITLE "Deinstallationsart"
  ${LangFileString} UMUI_UNTEXT_SETUPTYPE_SUBTITLE "Auswahl der passenden Deinstallationsart"
  ${LangFileString} UMUI_UNTEXT_SETUPTYPE_INFO_TEXT "Wählen Sie bitte eine Deinstallationsart aus."
  ${LangFileString} UMUI_UNTEXT_SETUPTYPE_MINIMAL_TEXT "Nur die Hauptfunktionen werden beibehalten."
  ${LangFileString} UMUI_UNTEXT_SETUPTYPE_STANDARD_TEXT "Nur die wichtigsten Funktionen werden beibehalten."
  ${LangFileString} UMUI_UNTEXT_SETUPTYPE_COMPLETE_TEXT "Das gesamte Programm wird beibehalten."
  ${LangFileString} UMUI_UNTEXT_SETUPTYPE_CUSTOM_TEXT "Wählen Sie aus, welche Programmfunktionalität deinstalliert werden soll."
!endif

!ifdef UMUI_SETUPTYPEPAGE | UMUI_UNSETUPTYPEPAGE
  ${LangFileString} UMUI_TEXT_SETUPTYPE_MINIMAL_TITLE "Minimal"
  ${LangFileString} UMUI_TEXT_SETUPTYPE_STANDARD_TITLE "Standard"
  ${LangFileString} UMUI_TEXT_SETUPTYPE_COMPLETE_TITLE "Komplett"
  ${LangFileString} UMUI_TEXT_SETUPTYPE_CUSTOM_TITLE "Benutzerdefiniert"
!endif


!ifdef UMUI_INFORMATIONPAGE
  ${LangFileString} UMUI_TEXT_INFORMATION_SUBTITLE "Bitte beachten Sie die Informationen über die Installation von $(^NameDA)."
!endif

!ifdef UMUI_UNINFORMATIONPAGE
  ${LangFileString} UMUI_UNTEXT_INFORMATION_SUBTITLE "Bitte beachten Sie die Informationen über die Deinstallation von $(^NameDA)."
!endif

!ifdef UMUI_INFORMATIONPAGE | UMUI_UNINFORMATIONPAGE
  ${LangFileString} UMUI_TEXT_INFORMATION_TITLE "Information"
  ${LangFileString} UMUI_TEXT_INFORMATION_INFO_TEXT "Informationen über $(^NameDA)."
!endif


!ifdef UMUI_ADDITIONALTASKSPAGE
  ${LangFileString} UMUI_TEXT_ADDITIONALTASKS_INFO_TEXT "Wählen Sie zusätzliche Aktionen, die während des Installationsprozesses von $(^NameDA) durchgeführt werden sollen. $_CLICK"
!endif

!ifdef UMUI_UNADDITIONALTASKSPAGE
  ${LangFileString} UMUI_UNTEXT_ADDITIONALTASKS_INFO_TEXT "Wählen Sie zusätzliche Aktionen, die während des Deinstallationsprozesses von $(^NameDA) durchgeführt werden sollen. $_CLICK"
!endif

!ifdef UMUI_ADDITIONALTASKSPAGE | UMUI_UNADDITIONALTASKSPAGE
  ${LangFileString} UMUI_TEXT_ADDITIONALTASKS_TITLE "Zusätzliche Aktionen"
  ${LangFileString} UMUI_TEXT_ADDITIONALTASKS_SUBTITLE "Welche zusätzlichen Aktionen sollen durchgeführt werden?"
  ${LangFileString} UMUI_TEXT_ADDITIONALTASKS_ADDITIONAL_ICONS "Zusätzliche Icons:"
  ${LangFileString} UMUI_TEXT_ADDITIONALTASKS_CREATE_DESKTOP_ICON "Erstelle ein Icon auf dem Desktop"
  ${LangFileString} UMUI_TEXT_ADDITIONALTASKS_CREATE_QUICK_LAUNCH_ICON "Erstelle ein  Icon auf der Schnellstartleiste"
  ${LangFileString} UMUI_TEXT_ADDITIONALTASKS_ADVANCED_PARAMETERS "Fortgeschrittene Parameter:"
  ${LangFileString} UMUI_TEXT_ADDITIONALTASKS_LAUNCH_PROGRAM_AT_WINDOWS_STARTUP "Starte $(^NameDA) nach einem Systemstart"
  ${LangFileString} UMUI_TEXT_ADDITIONALTASKS_FILE_ASSOCIATION "Dateiverknüpfungen:"
  ${LangFileString} UMUI_TEXT_ADDITIONALTASKS_ASSOCIATE_WITH "Verknüpfe $(^NameDA) mit "
  ${LangFileString} UMUI_TEXT_ADDITIONALTASKS_ASSOCIATE_WITH_END " Dateityp"
!endif


!ifdef UMUI_CONFIRMPAGE | UMUI_UNCONFIRMPAGE | UMUI_ALTERNATIVESTARTMENUPAGE | UMUI_UNALTERNATIVESTARTMENUPAGE
  ${LangFileString} UMUI_TEXT_SHELL_VAR_CONTEXT "Für wen sollen die Verknüpfungen erstellt werden:"
  ${LangFileString} UMUI_TEXT_SHELL_VAR_CONTEXT_FOR_ALL_USERS "Für alle Benutzer"
  ${LangFileString} UMUI_TEXT_SHELL_VAR_CONTEXT_ONLY_FOR_CURRENT_USER "Nur für den angemeldeten Benutzer"
!endif


!ifdef UMUI_UPDATEPAGE
  ${LangFileString} UMUI_TEXT_UPDATE_TITLE "Aktualisieren"
  ${LangFileString} UMUI_TEXT_UPDATE_SUBTITLE "Aktualisierung einer früheren Version des Programms."
  ${LangFileString} UMUI_TEXT_UPDATE_INFO_TEXT "Willkommen zum $(^NameDA) Installationsassistenten.$\r$\nDieses Programm führt eine Aktualisierung der Version $OLDVERSION durch."
  ${LangFileString} UMUI_TEXT_UPDATE_UPDATE_TITLE "Aktualisierung"
  ${LangFileString} UMUI_TEXT_UPDATE_UPDATE_TEXT "Aktualisierung aller bereits installierten Komponenten auf die Version $NEWVERSION."
  ${LangFileString} UMUI_TEXT_UPDATE_REMOVE_TITLE "Entfernen"
  ${LangFileString} UMUI_TEXT_UPDATE_REMOVE_TEXT "Deinstallation der Version $OLDVERSION  vom Computer."
  ${LangFileString} UMUI_TEXT_UPDATE_CONTINUE_TITLE "Installation fortsetzen"
  ${LangFileString} UMUI_TEXT_UPDATE_CONTINUE_TEXT "Installation wie üblich fortsetzen. Verwenden Sie diese Option, wenn die neue Version in einem anderen Ordner parallel zur bereits bestehenden Version installiert werden soll."
!endif


!ifdef UMUI_MAINTENANCEPAGE | UMUI_UNMAINTENANCEPAGE
  ${LangFileString} UMUI_TEXT_MAINTENANCE_TITLE "Anpassen"
  ${LangFileString} UMUI_TEXT_MAINTENANCE_SUBTITLE "Ändern, Reparieren oder Entfernen des Programms."
  ${LangFileString} UMUI_TEXT_MAINTENANCE_INFO_TEXT "Willkommen zum $(^NameDA) Anpassungsassistenten.$\r$\nMit diesem Programm kann die aktuelle Installation geändert werden."
  ${LangFileString} UMUI_TEXT_MAINTENANCE_MODIFY_TITLE "Ändern"
  ${LangFileString} UMUI_TEXT_MAINTENANCE_MODIFY_TEXT "Wählen Sie neue Komponenten aus, um diese zu installieren oder bereits vorhandene, um diese zu deinstallieren."
  ${LangFileString} UMUI_TEXT_MAINTENANCE_REPAIR_TITLE "Reparieren"
  ${LangFileString} UMUI_TEXT_MAINTENANCE_REPAIR_TEXT "Reinstallation aller bereits installierten $(^NameDA) Komponenten."
  ${LangFileString} UMUI_TEXT_MAINTENANCE_REMOVE_TITLE "Entfernen"
  ${LangFileString} UMUI_TEXT_MAINTENANCE_REMOVE_TEXT "Deinstallation der $(^NameDA) vom Computer."
  ${LangFileString} UMUI_TEXT_MAINTENANCE_CONTINUE_TITLE "Installation fortsetzen"
  ${LangFileString} UMUI_TEXT_MAINTENANCE_CONTINUE_TEXT "Installation wie üblich fortsetzen. Verwenden Sie diese Option, wenn die Neuinstallation eine bereits existierende Installation überschreiben soll oder um eine Neuinstallation in einem anderen Verzeichnis durchzuführen."
!endif


!ifdef UMUI_FILEDISKREQUESTPAGE | UMUI_UNFILEDISKREQUESTPAGE
  ${LangFileString} UMUI_TEXT_FILEDISKREQUEST_FILE_SUBTITLE_BEGIN "Die Installation benötigt"
  ${LangFileString} UMUI_TEXT_FILEDISKREQUEST_FILE_SUBTITLE_END "Datei um fortsetzen zu können."
  ${LangFileString} UMUI_TEXT_FILEDISKREQUEST_DISK_SUBTITLE "Die Installation benötigt den nächsten Datenträger um fortsetzen zu können."
  ${LangFileString} UMUI_TEXT_FILEDISKREQUEST_FILE_BEGIN "Wählen Sie den Speicherort der Datei"
  ${LangFileString} UMUI_TEXT_FILEDISKREQUEST_FILE_END "um fortzusetzen."
  ${LangFileString} UMUI_TEXT_FILEDISKREQUEST_DISK "Bitte legen Sie den Datenträger ein"
  ${LangFileString} UMUI_TEXT_FILEDISKREQUEST_PATH "Pfad:"
!endif
