;NSIS Modern User Interface - Language File
;Compatible with UltraModernUI 2.0 beta 1

;Language: Italiano (1040)
;By Matthias <bodenseematze@users.sourceforge.net> (copied from English and translated)
;--------------------------------

!ifdef UMUI_MULTILANGUAGEPAGE
  ${LangFileString} UMUI_TEXT_MULTILANGUAGE_TITLE "Benvenuti all'assistente d'installatione di $(^NameDA)"
  ${LangFileString} UMUI_TEXT_MULTILANGUAGE_TEXT "Selezionate prima di installare $(^NameDA) una lingua:$\r$\n$\r$\n$_CLICK"
!endif

!ifdef UMUI_UNMULTILANGUAGEPAGE
  ${LangFileString} UMUI_UNTEXT_MULTILANGUAGE_TITLE "Benvenuti all'assistente di disinstallazione di $(^NameDA)"
  ${LangFileString} UMUI_UNTEXT_MULTILANGUAGE_TEXT "Selezionate prima di rimuovere $(^NameDA) una lingua:$\r$\n$\r$\n$_CLICK"
!endif

!ifdef UMUI_MULTILANGUAGEPAGE | UMUI_UNMULTILANGUAGEPAGE
  ${LangFileString} UMUI_TEXT_MULTILANGUAGE_LANGUAGE "Lingua:"
!endif


!ifdef MUI_WELCOMEPAGE
  ${LangFileString} UMUI_TEXT_WELCOME_ALTERNATIVEINFO_TEXT "Questo assistente la guiderà durante l'installazione di $(^NameDA) .$\r$\n$\r$\n$\r$\n$_CLICK"
!endif


!ifdef UMUI_SERIALNUMBERPAGE | UMUI_UNSERIALNUMBERPAGE
  ${LangFileString} UMUI_TEXT_SERIALNUMBER_TITLE "Inserite il codice di serie del $(^NameDA)"
  ${LangFileString} UMUI_TEXT_SERIALNUMBER_SUBTITLE "Si prega di compilare le diverse caselle."
  ${LangFileString} UMUI_TEXT_SERIALNUMBER_INFO_TEXT "Si prega di compilare le diverse caselle. $_CLICK"
  ${LangFileString} UMUI_TEXT_SERIALNUMBER_INVALIDATE_TEXT "$UMUI_SNTEXT non è valido. Si prega di verificare le notificazioni immesse."
  ${LangFileString} UMUI_TEXT_SERIALNUMBER_NAME "Nome"
  ${LangFileString} UMUI_TEXT_SERIALNUMBER_ORGANIZATION "Organizzazione"
  ${LangFileString} UMUI_TEXT_SERIALNUMBER_SERIALNUMBER "N° di Serie"
  ${LangFileString} UMUI_TEXT_SERIALNUMBER_ACTIVATIONCODE "Codice di attivazione"
  ${LangFileString} UMUI_TEXT_SERIALNUMBER_PASSWORD "Password"
!endif


!ifdef UMUI_CONFIRMPAGE
  ${LangFileString} UMUI_TEXT_INSTCONFIRM_SUBTITLE "L'assistente ha raccolto tutte le informazioni dovute ed è pronto per istallare $(^NameDA) ."
  ${LangFileString} UMUI_TEXT_INSTCONFIRM_TITLE "Confermare l'installazione"
  ${LangFileString} UMUI_TEXT_INSTCONFIRM_TEXT_TOP "L'assistente è pronto, ad installare $(^NameDA) sul Vs. Computer.$\r$\nSe volete verificare o modificare i parametri d'installazione, Cliccare su $(^BackBtn). $_CLICK"
!endif

!ifdef UMUI_UNCONFIRMPAGE
  ${LangFileString} UMUI_UNTEXT_INSTCONFIRM_SUBTITLE "L'assistente è pronto, a rimuovere $(^NameDA) ."
  ${LangFileString} UMUI_UNTEXT_INSTCONFIRM_TITLE "Confermare la disinstallazione"
  ${LangFileString} UMUI_UNTEXT_INSTCONFIRM_TEXT_TOP "L'assistente è pronto, a rimuovere $(^NameDA)  dal Vs. Computer.$\r$\nSe volete verificare o modificare i parametri di disinstallazione, Cliccare su $(^BackBtn), Cliccare su $(^NextBtn), se volete dare il via alla disinstallazione."
!endif

!ifdef UMUI_CONFIRMPAGE | UMUI_UNCONFIRMPAGE
  ${LangFileString} UMUI_TEXT_INSTCONFIRM_TEXTBOX_TITLE "Configurazione attuale:"
  ${LangFileString} UMUI_TEXT_INSTCONFIRM_TEXTBOX_DESTINATION_LOCATION "luogo di destinazione:"
  ${LangFileString} UMUI_TEXT_INSTCONFIRM_TEXTBOX_START_MENU_FOLDER "Cartella dello Start menu:"
  ${LangFileString} UMUI_TEXT_INSTCONFIRM_TEXTBOX_COMPNENTS "I seguenti componenti vengono installati:"
!endif


!ifdef UMUI_ABORTPAGE
  ${LangFileString} UMUI_TEXT_ABORT_INFO_TITLE "L'assistente d'installazione di $(^NameDA)interrotto !"
  ${LangFileString} UMUI_TEXT_ABORT_INFO_TEXT "L'assistente è stato interrotto, prima di completare l'installazione di $(^NameDA).$\r$\n$\r$\nPer installare questo programma in un secondo tempo, riavviate nuovamente l'assistente d'installazione. $\r$\n$\r$\n$\r$\n$\r$\nCliccare su $(^CloseBtn), per terminare l'assistente d'installazione."
!endif

!ifdef UMUI_UNABORTPAGE
  ${LangFileString} UMUI_UNTEXT_ABORT_INFO_TITLE "L'assistente di disinstallazione di $(^NameDA) interrotto !"
  ${LangFileString} UMUI_UNTEXT_ABORT_INFO_TEXT "L'assistente è stato interrotto, prima di completare la disinstallazione di $(^NameDA).$\r$\n$\r$\nPer disinstallare questo programma in un secondo tempo, riavviate nuovamente l'assistente di disinstallazione.$\r$\n$\r$\n$\r$\n$\r$\nCliccare su $(^CloseBtn), per terminare l'assistente di disinstallazione."
!endif


!ifdef UMUI_SETUPTYPEPAGE
  ${LangFileString} UMUI_TEXT_SETUPTYPE_TITLE "Tipo di Setup"
  ${LangFileString} UMUI_TEXT_SETUPTYPE_SUBTITLE "Selezionate il tipo di Setup per voi più idoneo."
  ${LangFileString} UMUI_TEXT_SETUPTYPE_INFO_TEXT "Selezionate un tipo di Setup."
  ${LangFileString} UMUI_TEXT_SETUPTYPE_MINIMAL_TEXT "Vengono installate solo le applicazioni necessarie (richiedono il minor spazio di memoria)"
  ${LangFileString} UMUI_TEXT_SETUPTYPE_STANDARD_TEXT "Tutte le applicazioni principali vengono installate. Consigliato per la maggior parte degli utenti ."
  ${LangFileString} UMUI_TEXT_SETUPTYPE_COMPLETE_TEXT "Vengono installate tutte le applicazioni del Programma. (richiede il maggior spazio di memoria)"
  ${LangFileString} UMUI_TEXT_SETUPTYPE_CUSTOM_TEXT "Selezionate quali applicazioni di programma, in quali destinazioni devono essere installati. Consigliato solo per utenti esperti ."
!endif

!ifdef UMUI_UNSETUPTYPEPAGE
  ${LangFileString} UMUI_UNTEXT_SETUPTYPE_TITLE "Tipo di disinstallazione"
  ${LangFileString} UMUI_UNTEXT_SETUPTYPE_SUBTITLE "Selezionate il tipo di disinstallazione per voi più idoneo.."
  ${LangFileString} UMUI_UNTEXT_SETUPTYPE_INFO_TEXT "Selezionate un tipo di disinstallazione."
  ${LangFileString} UMUI_UNTEXT_SETUPTYPE_MINIMAL_TEXT "Vengono mantenute solo le applicazioni principali."
  ${LangFileString} UMUI_UNTEXT_SETUPTYPE_STANDARD_TEXT "Vengono mantenute solo le applicazioni più importanti."
  ${LangFileString} UMUI_UNTEXT_SETUPTYPE_COMPLETE_TEXT "viene mantenuto tutto il programma."
  ${LangFileString} UMUI_UNTEXT_SETUPTYPE_CUSTOM_TEXT "Selezionate le applicazioni di programma che volete rimuovere."
!endif

!ifdef UMUI_SETUPTYPEPAGE | UMUI_UNSETUPTYPEPAGE
  ${LangFileString} UMUI_TEXT_SETUPTYPE_MINIMAL_TITLE "Minima"
  ${LangFileString} UMUI_TEXT_SETUPTYPE_STANDARD_TITLE "Standard"
  ${LangFileString} UMUI_TEXT_SETUPTYPE_COMPLETE_TITLE "Completa"
  ${LangFileString} UMUI_TEXT_SETUPTYPE_CUSTOM_TITLE "Definizione utente"
!endif


!ifdef UMUI_INFORMATIONPAGE
  ${LangFileString} UMUI_TEXT_INFORMATION_SUBTITLE "Si prega di osservare le indicazioni di installazione di(^NameDA)."
!endif

!ifdef UMUI_UNINFORMATIONPAGE
  ${LangFileString} UMUI_UNTEXT_INFORMATION_SUBTITLE "Si prega di osservare le indicazioni di disinstallazione di $(^NameDA)."
!endif

!ifdef UMUI_INFORMATIONPAGE | UMUI_UNINFORMATIONPAGE
  ${LangFileString} UMUI_TEXT_INFORMATION_TITLE "Informazioni"
  ${LangFileString} UMUI_TEXT_INFORMATION_INFO_TEXT "Informazione su $(^NameDA)."
!endif


!ifdef UMUI_ADDITIONALTASKSPAGE
  ${LangFileString} UMUI_TEXT_ADDITIONALTASKS_INFO_TEXT "Selezionate le impostazioni supplementari, che durante il processo d'installazione di $(^NameDA) si dovranno applicare. $_CLICK"
!endif

!ifdef UMUI_UNADDITIONALTASKSPAGE
  ${LangFileString} UMUI_UNTEXT_ADDITIONALTASKS_INFO_TEXT "Selezionate le impostazioni supplementari, che durante il processo di disinstallazione di $(^NameDA) si dovranno rimuovere. $_CLICK"
!endif

!ifdef UMUI_ADDITIONALTASKSPAGE | UMUI_UNADDITIONALTASKSPAGE
  ${LangFileString} UMUI_TEXT_ADDITIONALTASKS_TITLE "Impostazioni supplementari"
  ${LangFileString} UMUI_TEXT_ADDITIONALTASKS_SUBTITLE "Quali impostazioni supplementari devono essere eseguite?"
  ${LangFileString} UMUI_TEXT_ADDITIONALTASKS_ADDITIONAL_ICONS "Icone Supplementari:"
  ${LangFileString} UMUI_TEXT_ADDITIONALTASKS_CREATE_DESKTOP_ICON "Genera un icona su Desktop"
  ${LangFileString} UMUI_TEXT_ADDITIONALTASKS_CREATE_QUICK_LAUNCH_ICON "Genera un icona sulla barra veloce d'avvio"
  ${LangFileString} UMUI_TEXT_ADDITIONALTASKS_ADVANCED_PARAMETERS "Parametri per esperti:"
  ${LangFileString} UMUI_TEXT_ADDITIONALTASKS_LAUNCH_PROGRAM_AT_WINDOWS_STARTUP "Avvia $(^NameDA) dopo l'avvio del sistema operativo"
  ${LangFileString} UMUI_TEXT_ADDITIONALTASKS_FILE_ASSOCIATION "Collegamenti file:"
  ${LangFileString} UMUI_TEXT_ADDITIONALTASKS_ASSOCIATE_WITH "Collega $(^NameDA) con "
  ${LangFileString} UMUI_TEXT_ADDITIONALTASKS_ASSOCIATE_WITH_END " Tipo file"
!endif


!ifdef UMUI_CONFIRMPAGE | UMUI_UNCONFIRMPAGE | UMUI_ALTERNATIVESTARTMENUPAGE | UMUI_UNALTERNATIVESTARTMENUPAGE
  ${LangFileString} UMUI_TEXT_SHELL_VAR_CONTEXT "Per chi devono essere generati i collegamenti :"
  ${LangFileString} UMUI_TEXT_SHELL_VAR_CONTEXT_FOR_ALL_USERS "per tutti gli utenti"
  ${LangFileString} UMUI_TEXT_SHELL_VAR_CONTEXT_ONLY_FOR_CURRENT_USER "Solo per l'utente annunciato"
!endif


!ifdef UMUI_UPDATEPAGE
  ${LangFileString} UMUI_TEXT_UPDATE_TITLE "Aggiornamento"
  ${LangFileString} UMUI_TEXT_UPDATE_SUBTITLE "Update di un antecedente versione."
  ${LangFileString} UMUI_TEXT_UPDATE_INFO_TEXT "Benvenuti all'assistente d'update di $(^NameDA) .$\r$\nQuesto programma effettuerà un Update della versione $OLDVERSION."
  ${LangFileString} UMUI_TEXT_UPDATE_UPDATE_TITLE "Aggiornamento"
  ${LangFileString} UMUI_TEXT_UPDATE_UPDATE_TEXT "Update di tutti componenti installati di $(^NameDA) sulla Release $NEWVERSION."
  ${LangFileString} UMUI_TEXT_UPDATE_REMOVE_TITLE "Rimuovere"
  ${LangFileString} UMUI_TEXT_UPDATE_REMOVE_TEXT "Disinstallare Release $OLDVERSION dal Vs. Computer."
  ${LangFileString} UMUI_TEXT_UPDATE_CONTINUE_TITLE "Proseguire Setup"
  ${LangFileString} UMUI_TEXT_UPDATE_CONTINUE_TEXT "Proseguire con il Setup come di usuale. Utilizzate questa opzione, se volete installare questa nuova versione su un'altra destinazione alle altre versioni."
!endif


!ifdef UMUI_MAINTENANCEPAGE | UMUI_UNMAINTENANCEPAGE
  ${LangFileString} UMUI_TEXT_MAINTENANCE_TITLE "Amministrazione"
  ${LangFileString} UMUI_TEXT_MAINTENANCE_SUBTITLE "Modificare, riparare o rimuovere il programma."
  ${LangFileString} UMUI_TEXT_MAINTENANCE_INFO_TEXT "Benvenuti al programma d'amministrazione di $(^NameDA) .$\r$\nCon questo programma potete modificare le Vs. attuale installazione."
  ${LangFileString} UMUI_TEXT_MAINTENANCE_MODIFY_TITLE "Modificare"
  ${LangFileString} UMUI_TEXT_MAINTENANCE_MODIFY_TEXT "Selezionate i nuovi componenti, da applicare, o selezionate dei componenti già applicati per poterli rimuovere ."
  ${LangFileString} UMUI_TEXT_MAINTENANCE_REPAIR_TITLE "Riparare"
  ${LangFileString} UMUI_TEXT_MAINTENANCE_REPAIR_TEXT "Reinstallazione di tutti i componenti precedentemente installati di $(^NameDA) ."
  ${LangFileString} UMUI_TEXT_MAINTENANCE_REMOVE_TITLE "Rimuovere"
  ${LangFileString} UMUI_TEXT_MAINTENANCE_REMOVE_TEXT "Disinstalla $(^NameDA) dal Vs. Computer."
  ${LangFileString} UMUI_TEXT_MAINTENANCE_CONTINUE_TITLE "Proseguire Setup"
  ${LangFileString} UMUI_TEXT_MAINTENANCE_CONTINUE_TEXT "Proseguire con il Setup come di usuale. Utilizzate questa opzione, se volete sovrascrivere l'installazione sull'attuale installazione o effettuare una nuova istallazione con altra destinazione."
!endif


!ifdef UMUI_FILEDISKREQUESTPAGE | UMUI_UNFILEDISKREQUESTPAGE
  ${LangFileString} UMUI_TEXT_FILEDISKREQUEST_FILE_SUBTITLE_BEGIN "Il Setup necessita del prossimo supporto dati per poter proseguire."
  ${LangFileString} UMUI_TEXT_FILEDISKREQUEST_FILE_SUBTITLE_END "File per poter proseguire."
  ${LangFileString} UMUI_TEXT_FILEDISKREQUEST_DISK_SUBTITLE "Il Setup necessita del prossimo supporto dati per poter proseguire."
  ${LangFileString} UMUI_TEXT_FILEDISKREQUEST_FILE_BEGIN "Selezionate la locazione memoria dei dati "
  ${LangFileString} UMUI_TEXT_FILEDISKREQUEST_FILE_END "per proseguire."
  ${LangFileString} UMUI_TEXT_FILEDISKREQUEST_DISK "Si prega di inserire il"
  ${LangFileString} UMUI_TEXT_FILEDISKREQUEST_PATH "Percorso:"
!endif
