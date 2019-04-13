;NSIS Modern User Interface - Language File
;Compatible with UltraModernUI 2.0 beta 1

;Language: French (1036)
;By SuperPat
;--------------------------------

!ifdef UMUI_MULTILANGUAGEPAGE
  ${LangFileString} UMUI_TEXT_MULTILANGUAGE_TITLE "Bienvenue dans le programme d'installation de $(^NameDA)"
  ${LangFileString} UMUI_TEXT_MULTILANGUAGE_TEXT "Avant de commencer l'installation de $(^NameDA), veuillez choisir un langage:$\r$\n$\r$\n$_CLICK"
!endif

!ifdef UMUI_UNMULTILANGUAGEPAGE
  ${LangFileString} UMUI_UNTEXT_MULTILANGUAGE_TITLE "Bienvenue dans le programme de désinstallation de $(^NameDA)"
  ${LangFileString} UMUI_UNTEXT_MULTILANGUAGE_TEXT "Avant de commencer la désinstallation de $(^NameDA), veuillez choisir un langage:$\r$\n$\r$\n$_CLICK"
!endif

!ifdef UMUI_MULTILANGUAGEPAGE | UMUI_UNMULTILANGUAGEPAGE
  ${LangFileString} UMUI_TEXT_MULTILANGUAGE_LANGUAGE "Langage:"
!endif


!ifdef MUI_WELCOMEPAGE
  ${LangFileString} UMUI_TEXT_WELCOME_ALTERNATIVEINFO_TEXT "Vous êtes sur le point d'installer $(^NameDA) sur votre ordinateur.$\r$\n$\r$\n$_CLICK"
!endif


!ifdef UMUI_SERIALNUMBERPAGE | UMUI_UNSERIALNUMBERPAGE
  ${LangFileString} UMUI_TEXT_SERIALNUMBER_TITLE "Entrer votre numéro de série de $(^NameDA)"
  ${LangFileString} UMUI_TEXT_SERIALNUMBER_SUBTITLE "Veuillez renseigner les différents champs ci-dessous."
  ${LangFileString} UMUI_TEXT_SERIALNUMBER_INFO_TEXT "Veuillez renseigner les différents champs ci-dessous. $_CLICK"
  ${LangFileString} UMUI_TEXT_SERIALNUMBER_INVALIDATE_TEXT "$UMUI_SNTEXT invalide. Veuillez revérifier les informations que vous venez d'entrer."
  ${LangFileString} UMUI_TEXT_SERIALNUMBER_NAME "Nom"
  ${LangFileString} UMUI_TEXT_SERIALNUMBER_ORGANIZATION "Société"
  ${LangFileString} UMUI_TEXT_SERIALNUMBER_SERIALNUMBER "Numéro de série"
  ${LangFileString} UMUI_TEXT_SERIALNUMBER_ACTIVATIONCODE "Code d'activation"
  ${LangFileString} UMUI_TEXT_SERIALNUMBER_PASSWORD "Mot de passe"
!endif


!ifdef UMUI_CONFIRMPAGE
  ${LangFileString} UMUI_TEXT_INSTCONFIRM_SUBTITLE "Le programme a finit de rassembler les informations et est prêt à installer $(^NameDA)."
  ${LangFileString} UMUI_TEXT_INSTCONFIRM_TITLE "Confirmation de l'installation"
  ${LangFileString} UMUI_TEXT_INSTCONFIRM_TEXT_TOP "Le programme est prêt à installer $(^NameDA) sur votre ordinateur.$\r$\nSi vous vouler revoir ou changer n'importe lequel de vos paramètres d'installation, cliquez sur $(^BackBtn). $_CLICK"
!endif

!ifdef UMUI_UNCONFIRMPAGE
  ${LangFileString} UMUI_UNTEXT_INSTCONFIRM_SUBTITLE "Le programme a finit de rassembler les informations et est prêt à désinstaller $(^NameDA)."
  ${LangFileString} UMUI_UNTEXT_INSTCONFIRM_TITLE "Confirmation de la désinstallation"
  ${LangFileString} UMUI_UNTEXT_INSTCONFIRM_TEXT_TOP "Le programme est prêt à désinstaller $(^NameDA) sur votre ordinateur.$\r$\nSi vous vouler revoir ou changer n'importe lequel de vos paramètres de désinstallation, cliquez sur $(^BackBtn). Sinon cliquez sur $(^NextBtn) pour commencer l'installation."
!endif

!ifdef UMUI_CONFIRMPAGE | UMUI_UNCONFIRMPAGE
  ${LangFileString} UMUI_TEXT_INSTCONFIRM_TEXTBOX_TITLE "Configuration actuelle:"
  ${LangFileString} UMUI_TEXT_INSTCONFIRM_TEXTBOX_DESTINATION_LOCATION "Dossier de destination:"
  ${LangFileString} UMUI_TEXT_INSTCONFIRM_TEXTBOX_START_MENU_FOLDER "Répertoire du menu démarrer:"
  ${LangFileString} UMUI_TEXT_INSTCONFIRM_TEXTBOX_COMPNENTS "Les composants suivants seront installés:"
!endif


!ifdef UMUI_ABORTPAGE
  ${LangFileString} UMUI_TEXT_ABORT_INFO_TITLE "Abandon de l'installation de $(^NameDA)"
  ${LangFileString} UMUI_TEXT_ABORT_INFO_TEXT "L'installation a été interrompue avant que $(^NameDA) n'ait été complètement installé.$\r$\n$\r$\nPour installer ce programme plus tard, redémarrez l'installation une nouvelle fois.$\r$\n$\r$\n$\r$\n$\r$\nCliquez sur $(^CloseBtn) pour quitter le programme d'installation."
!endif

!ifdef UMUI_UNABORTPAGE
  ${LangFileString} UMUI_UNTEXT_ABORT_INFO_TITLE "Abandon de la désinstallation de $(^NameDA)"
  ${LangFileString} UMUI_UNTEXT_ABORT_INFO_TEXT "La désinstallation a été interrompue avant que $(^NameDA) n'ait été complètement désinstallé.$\r$\n$\r$\nPour désinstaller ce programme plus tard, redémarrez la désinstallation une nouvelle fois.$\r$\n$\r$\n$\r$\n$\r$\nCliquez sur $(^CloseBtn) pour quitter le programme de désinstallation."
!endif


!ifdef UMUI_SETUPTYPEPAGE
  ${LangFileString} UMUI_TEXT_SETUPTYPE_TITLE "Type d'installation"
  ${LangFileString} UMUI_TEXT_SETUPTYPE_SUBTITLE "Choisissez le type d'installation qui convient le plus à vos besoins."
  ${LangFileString} UMUI_TEXT_SETUPTYPE_INFO_TEXT "Selectionnez un type d'installation."
  ${LangFileString} UMUI_TEXT_SETUPTYPE_MINIMAL_TEXT "Uniquement les fonctionnalités requise seront installées. (Requiert le moins d'espace disque)"
  ${LangFileString} UMUI_TEXT_SETUPTYPE_STANDARD_TEXT "Toutes les principales fonctionnalités seront installées. Recommandé pour la plupart des utilisateurs."
  ${LangFileString} UMUI_TEXT_SETUPTYPE_COMPLETE_TEXT "Toutes les fonctionnalités seront installées. (Requiert le plus d'espace disque)"
  ${LangFileString} UMUI_TEXT_SETUPTYPE_CUSTOM_TEXT "Choisir quelles fonctionnalitées du programme vous voulez installer et où elles seront installées. Recommandé pour les utilisateurs avancés."
!endif

!ifdef UMUI_UNSETUPTYPEPAGE
  ${LangFileString} UMUI_UNTEXT_SETUPTYPE_TITLE "Type de Désinstallation"
  ${LangFileString} UMUI_UNTEXT_SETUPTYPE_SUBTITLE "Choisissez le type de désinstallation qui convient le plus à vos besoins."
  ${LangFileString} UMUI_UNTEXT_SETUPTYPE_INFO_TEXT "Selectionnez un type de désinstallation."
  ${LangFileString} UMUI_UNTEXT_SETUPTYPE_MINIMAL_TEXT "Uniquement les pincipales fonctionnalités seront gardés."
  ${LangFileString} UMUI_UNTEXT_SETUPTYPE_STANDARD_TEXT "Uniquement les fonctionnalités requises seront gardés."
  ${LangFileString} UMUI_UNTEXT_SETUPTYPE_COMPLETE_TEXT "Tous le programme sera désinstallé."
  ${LangFileString} UMUI_UNTEXT_SETUPTYPE_CUSTOM_TEXT "Choisir quelles fonctionnalitées du programme vous voulez désinstaller."
!endif

!ifdef UMUI_SETUPTYPEPAGE | UMUI_UNSETUPTYPEPAGE
  ${LangFileString} UMUI_TEXT_SETUPTYPE_MINIMAL_TITLE "Minimale"
  ${LangFileString} UMUI_TEXT_SETUPTYPE_STANDARD_TITLE "Standard"
  ${LangFileString} UMUI_TEXT_SETUPTYPE_COMPLETE_TITLE "Complète"
  ${LangFileString} UMUI_TEXT_SETUPTYPE_CUSTOM_TITLE "Personnalisée"
!endif


!ifdef UMUI_INFORMATIONPAGE
  ${LangFileString} UMUI_TEXT_INFORMATION_SUBTITLE "Veuillez prendre connaissance des informations concernant l'installation de $(^NameDA)."
!endif

!ifdef UMUI_UNINFORMATIONPAGE
  ${LangFileString} UMUI_UNTEXT_INFORMATION_SUBTITLE "Veuillez prendre connaissance des informations concernant la désinstallation de $(^NameDA)."
!endif

!ifdef UMUI_INFORMATIONPAGE | UMUI_UNINFORMATIONPAGE
  ${LangFileString} UMUI_TEXT_INFORMATION_TITLE "Information"
  ${LangFileString} UMUI_TEXT_INFORMATION_INFO_TEXT "Informations concernant $(^NameDA)."
!endif


!ifdef UMUI_ADDITIONALTASKSPAGE
  ${LangFileString} UMUI_TEXT_ADDITIONALTASKS_INFO_TEXT "Sélectionnez les tâches supplémentaires que l'assistant doit effectuer pendant l'installation de $(^NameDA). $_CLICK"
!endif

!ifdef UMUI_UNADDITIONALTASKSPAGE
  ${LangFileString} UMUI_UNTEXT_ADDITIONALTASKS_INFO_TEXT "Sélectionnez les tâches supplémentaires que l'assistant doit effectuer pendant la désinstallation de $(^NameDA). $_CLICK"
!endif

!ifdef UMUI_ADDITIONALTASKSPAGE | UMUI_UNADDITIONALTASKSPAGE
  ${LangFileString} UMUI_TEXT_ADDITIONALTASKS_TITLE "Tâches supplémentaires"
  ${LangFileString} UMUI_TEXT_ADDITIONALTASKS_SUBTITLE "Quelles sont les tâches supplémentaires qui doivent être effectuées?"
  ${LangFileString} UMUI_TEXT_ADDITIONALTASKS_ADDITIONAL_ICONS "Icônes Additionnelles:"
  ${LangFileString} UMUI_TEXT_ADDITIONALTASKS_CREATE_DESKTOP_ICON "Créer une icône sur le bureau"
  ${LangFileString} UMUI_TEXT_ADDITIONALTASKS_CREATE_QUICK_LAUNCH_ICON "Créer une icône dans la barre de lancement rapide"
  ${LangFileString} UMUI_TEXT_ADDITIONALTASKS_ADVANCED_PARAMETERS "Paramètres avancés:"
  ${LangFileString} UMUI_TEXT_ADDITIONALTASKS_LAUNCH_PROGRAM_AT_WINDOWS_STARTUP "Lancer $(^NameDA) au démarrage de Windows"
  ${LangFileString} UMUI_TEXT_ADDITIONALTASKS_FILE_ASSOCIATION "Association de fichier:"
  ${LangFileString} UMUI_TEXT_ADDITIONALTASKS_ASSOCIATE_WITH "Associer $(^NameDA) avec les fichiers de type "
  ${LangFileString} UMUI_TEXT_ADDITIONALTASKS_ASSOCIATE_WITH_END " "
!endif
  
  
!ifdef UMUI_CONFIRMPAGE | UMUI_UNCONFIRMPAGE | UMUI_ALTERNATIVESTARTMENUPAGE | UMUI_UNALTERNATIVESTARTMENUPAGE
  ${LangFileString} UMUI_TEXT_SHELL_VAR_CONTEXT "Comment les raccourcis seront créés:"
  ${LangFileString} UMUI_TEXT_SHELL_VAR_CONTEXT_FOR_ALL_USERS "Pour tous les utilisateurs"
  ${LangFileString} UMUI_TEXT_SHELL_VAR_CONTEXT_ONLY_FOR_CURRENT_USER "Uniquement pour l'utilisateur courant"
!endif


!ifdef UMUI_UPDATEPAGE
  ${LangFileString} UMUI_TEXT_UPDATE_TITLE "Mise à jour"
  ${LangFileString} UMUI_TEXT_UPDATE_SUBTITLE "Mettre à jour une ancienne version du programme."
  ${LangFileString} UMUI_TEXT_UPDATE_INFO_TEXT "Bienvenue dans l'assistant de mise à jour de $(^NameDA).$\n$\rCe programme va vous permettre de mettre à jour la version $OLDVERSION qui a été trouvé sur votre ordinateur."
  ${LangFileString} UMUI_TEXT_UPDATE_UPDATE_TITLE "Mettre à jour"
  ${LangFileString} UMUI_TEXT_UPDATE_UPDATE_TEXT "Mettre à jour tous les composants de $(^NameDA) déjà installés à la version $NEWVERSION."
  ${LangFileString} UMUI_TEXT_UPDATE_REMOVE_TITLE "Supprimer"
  ${LangFileString} UMUI_TEXT_UPDATE_REMOVE_TEXT "Désinstaller la version $OLDVERSION de votre ordinateur."
  ${LangFileString} UMUI_TEXT_UPDATE_CONTINUE_TITLE "Continuer l'installation"
  ${LangFileString} UMUI_TEXT_UPDATE_CONTINUE_TEXT "Continuer l'installation comme d'habitude. Utilisez cette option si vous voulez installer cette nouvelle version dans un autre répertoire en parallèle à la version précédente."
!endif


!ifdef UMUI_MAINTENANCEPAGE | UMUI_UNMAINTENANCEPAGE
  ${LangFileString} UMUI_TEXT_MAINTENANCE_TITLE "Maintenance"
  ${LangFileString} UMUI_TEXT_MAINTENANCE_SUBTITLE "Modifier, réparer, ou supprimer le programme."
  ${LangFileString} UMUI_TEXT_MAINTENANCE_INFO_TEXT "Bienvenue dans l'assistant de maintenance de $(^NameDA).$\r$\nCe programme va vous permettre de modifier l'installation actuelle."
  ${LangFileString} UMUI_TEXT_MAINTENANCE_MODIFY_TITLE "Modifier"
  ${LangFileString} UMUI_TEXT_MAINTENANCE_MODIFY_TEXT "Sélectionner de nouveaux composants à ajouter et sélectionner des composants déjà installés à supprimer."
  ${LangFileString} UMUI_TEXT_MAINTENANCE_REPAIR_TITLE "Réparer"
  ${LangFileString} UMUI_TEXT_MAINTENANCE_REPAIR_TEXT "Réinstaller tous les composants de $(^NameDA) déjà installés."
  ${LangFileString} UMUI_TEXT_MAINTENANCE_REMOVE_TITLE "Supprimer"
  ${LangFileString} UMUI_TEXT_MAINTENANCE_REMOVE_TEXT "Désinstaller $(^NameDA) de votre ordinateur."
  ${LangFileString} UMUI_TEXT_MAINTENANCE_CONTINUE_TITLE "Continuer l'installation"
  ${LangFileString} UMUI_TEXT_MAINTENANCE_CONTINUE_TEXT "Continuer l'installation comme d'habitude. Pour réinstaller ce programme sur une précédente installation ou une nouvelle fois dans un autre répertoire."
!endif


!ifdef UMUI_FILEDISKREQUESTPAGE | UMUI_UNFILEDISKREQUESTPAGE
  ${LangFileString} UMUI_TEXT_FILEDISKREQUEST_FILE_SUBTITLE_BEGIN "L'assistant d'installation à besoin du fichier"
  ${LangFileString} UMUI_TEXT_FILEDISKREQUEST_FILE_SUBTITLE_END "pour continuer."
  ${LangFileString} UMUI_TEXT_FILEDISKREQUEST_DISK_SUBTITLE "L'assistant d'installation à besoin du disque suivant pour continuer."
  ${LangFileString} UMUI_TEXT_FILEDISKREQUEST_FILE_BEGIN "Spécifier la localisation du fichier"
  ${LangFileString} UMUI_TEXT_FILEDISKREQUEST_FILE_END "pour continuer."
  ${LangFileString} UMUI_TEXT_FILEDISKREQUEST_DISK "Veuillez insérer le"
  ${LangFileString} UMUI_TEXT_FILEDISKREQUEST_PATH "Chemin:"
!endif
