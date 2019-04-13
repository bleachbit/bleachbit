;NSIS Modern User Interface - Language File
;Compatible with UltraModernUI 2.0 beta 1

;Language: English (1033)
;By SuperPat
;Changes by Matthias <bodenseematze@users.sourceforge.net>
;--------------------------------

!ifdef UMUI_MULTILANGUAGEPAGE
  ${LangFileString} UMUI_TEXT_MULTILANGUAGE_TITLE "Welcome to the $(^NameDA) Setup Wizard"
  ${LangFileString} UMUI_TEXT_MULTILANGUAGE_TEXT "Before beginning the installation of $(^NameDA), please choose a language:$\r$\n$\r$\n$_CLICK"
!endif

!ifdef UMUI_UNMULTILANGUAGEPAGE
  ${LangFileString} UMUI_UNTEXT_MULTILANGUAGE_TITLE "Welcome to the $(^NameDA) Uninstall Wizard"
  ${LangFileString} UMUI_UNTEXT_MULTILANGUAGE_TEXT "Before beginning the uninstallation of $(^NameDA), please choose a language:$\r$\n$\r$\n$_CLICK"
!endif

!ifdef UMUI_MULTILANGUAGEPAGE | UMUI_UNMULTILANGUAGEPAGE
  ${LangFileString} UMUI_TEXT_MULTILANGUAGE_LANGUAGE "Language:"
!endif


!ifdef MUI_WELCOMEPAGE
  ${LangFileString} UMUI_TEXT_WELCOME_ALTERNATIVEINFO_TEXT "This wizard will guide you through the installation of $(^NameDA).$\r$\n$\r$\n$\r$\n$_CLICK"
!endif


!ifdef UMUI_SERIALNUMBERPAGE | UMUI_UNSERIALNUMBERPAGE
  ${LangFileString} UMUI_TEXT_SERIALNUMBER_TITLE "Enter your serial number of $(^NameDA)"
  ${LangFileString} UMUI_TEXT_SERIALNUMBER_SUBTITLE "Please inform the various fields below."
  ${LangFileString} UMUI_TEXT_SERIALNUMBER_INFO_TEXT "Please inform the various fields below. $_CLICK"
  ${LangFileString} UMUI_TEXT_SERIALNUMBER_INVALIDATE_TEXT "$UMUI_SNTEXT is invalid. Please reverify information that you have just entered."
  ${LangFileString} UMUI_TEXT_SERIALNUMBER_NAME "Name"
  ${LangFileString} UMUI_TEXT_SERIALNUMBER_ORGANIZATION "Organization"
  ${LangFileString} UMUI_TEXT_SERIALNUMBER_SERIALNUMBER "Serial Number"
  ${LangFileString} UMUI_TEXT_SERIALNUMBER_ACTIVATIONCODE "Activation code"
  ${LangFileString} UMUI_TEXT_SERIALNUMBER_PASSWORD "Password"
!endif


!ifdef UMUI_CONFIRMPAGE
  ${LangFileString} UMUI_TEXT_INSTCONFIRM_SUBTITLE "Setup has finished gathering information and is ready to install $(^NameDA)."
  ${LangFileString} UMUI_TEXT_INSTCONFIRM_TITLE "Confirm Installation"
  ${LangFileString} UMUI_TEXT_INSTCONFIRM_TEXT_TOP "Setup is ready to install $(^NameDA) on your computer.$\r$\nIf you want to review or change any of your installation settings, click $(^BackBtn). $_CLICK"
!endif

!ifdef UMUI_UNCONFIRMPAGE
  ${LangFileString} UMUI_UNTEXT_INSTCONFIRM_SUBTITLE "Setup has finished gathering information and is ready to uninstall $(^NameDA)."
  ${LangFileString} UMUI_UNTEXT_INSTCONFIRM_TITLE "Confirm Uninstallation"
  ${LangFileString} UMUI_UNTEXT_INSTCONFIRM_TEXT_TOP "Setup is ready to uninstall $(^NameDA) on your computer.$\r$\nIf you want to review or change any of your uninstallation settings, click $(^BackBtn). Click $(^NextBtn) to begin the uninstall."
!endif

!ifdef UMUI_CONFIRMPAGE | UMUI_UNCONFIRMPAGE
  ${LangFileString} UMUI_TEXT_INSTCONFIRM_TEXTBOX_TITLE "Current configuration:"
  ${LangFileString} UMUI_TEXT_INSTCONFIRM_TEXTBOX_DESTINATION_LOCATION "Destination location:"
  ${LangFileString} UMUI_TEXT_INSTCONFIRM_TEXTBOX_START_MENU_FOLDER "Start menu folder:"
  ${LangFileString} UMUI_TEXT_INSTCONFIRM_TEXTBOX_COMPNENTS "The following components will be installed:"
!endif


!ifdef UMUI_ABORTPAGE
  ${LangFileString} UMUI_TEXT_ABORT_INFO_TITLE "Completing the $(^NameDA) Setup Wizard"
  ${LangFileString} UMUI_TEXT_ABORT_INFO_TEXT "The wizard was interrupted before $(^NameDA) could be completely installed.$\r$\n$\r$\nTo install this program at a later time, please run the setup again.$\r$\n$\r$\n$\r$\n$\r$\nClick $(^CloseBtn) to exit the Setup wizard."
!endif

!ifdef UMUI_UNABORTPAGE
  ${LangFileString} UMUI_UNTEXT_ABORT_INFO_TITLE "Completing the $(^NameDA) Uninstall Wizard"
  ${LangFileString} UMUI_UNTEXT_ABORT_INFO_TEXT "The wizard was interrupted before $(^NameDA) could be completely uninstalled.$\r$\n$\r$\nTo uninstall this program at a later time, please run the uninstall again.$\r$\n$\r$\n$\r$\n$\r$\nClick $(^CloseBtn) to exit the Uninstall wizard."
!endif


!ifdef UMUI_SETUPTYPEPAGE
  ${LangFileString} UMUI_TEXT_SETUPTYPE_TITLE "Setup Type"
  ${LangFileString} UMUI_TEXT_SETUPTYPE_SUBTITLE "Choose the setup type that best suits your needs."
  ${LangFileString} UMUI_TEXT_SETUPTYPE_INFO_TEXT "Please select a setup type."
  ${LangFileString} UMUI_TEXT_SETUPTYPE_MINIMAL_TEXT "Only the necessary features will be installed. (Requires the less disk space)"
  ${LangFileString} UMUI_TEXT_SETUPTYPE_STANDARD_TEXT "All the main features will be installed. Recommended for the majority of the users."
  ${LangFileString} UMUI_TEXT_SETUPTYPE_COMPLETE_TEXT "All program features will be installed. (Requires the most disk space)"
  ${LangFileString} UMUI_TEXT_SETUPTYPE_CUSTOM_TEXT "Choose which programm features you want installed and where they will be installed. Recommended for advanced users."
!endif

!ifdef UMUI_UNSETUPTYPEPAGE
  ${LangFileString} UMUI_UNTEXT_SETUPTYPE_TITLE "Uninstall Type"
  ${LangFileString} UMUI_UNTEXT_SETUPTYPE_SUBTITLE "Choose the uninstall type that best suits your needs."
  ${LangFileString} UMUI_UNTEXT_SETUPTYPE_INFO_TEXT "Please select an uninstall type."
  ${LangFileString} UMUI_UNTEXT_SETUPTYPE_MINIMAL_TEXT "Only the main features will be kept."
  ${LangFileString} UMUI_UNTEXT_SETUPTYPE_STANDARD_TEXT "Only the necessary features will be kept."
  ${LangFileString} UMUI_UNTEXT_SETUPTYPE_COMPLETE_TEXT "All program will be uninstalled."
  ${LangFileString} UMUI_UNTEXT_SETUPTYPE_CUSTOM_TEXT "Choose which programm features you want uninstall."
!endif

!ifdef UMUI_SETUPTYPEPAGE | UMUI_UNSETUPTYPEPAGE
  ${LangFileString} UMUI_TEXT_SETUPTYPE_MINIMAL_TITLE "Minimal"
  ${LangFileString} UMUI_TEXT_SETUPTYPE_STANDARD_TITLE "Standard"
  ${LangFileString} UMUI_TEXT_SETUPTYPE_COMPLETE_TITLE "Complete"
  ${LangFileString} UMUI_TEXT_SETUPTYPE_CUSTOM_TITLE "Custom"
!endif


!ifdef UMUI_INFORMATIONPAGE
  ${LangFileString} UMUI_TEXT_INFORMATION_SUBTITLE "Please take note of informations concerning the installation of $(^NameDA)."
!endif

!ifdef UMUI_UNINFORMATIONPAGE
  ${LangFileString} UMUI_UNTEXT_INFORMATION_SUBTITLE "Please take note of informations concerning the uninstallation of $(^NameDA)."
!endif

!ifdef UMUI_INFORMATIONPAGE | UMUI_UNINFORMATIONPAGE
  ${LangFileString} UMUI_TEXT_INFORMATION_TITLE "Information"
  ${LangFileString} UMUI_TEXT_INFORMATION_INFO_TEXT "Informations concerning $(^NameDA)."
!endif


!ifdef UMUI_ADDITIONALTASKSPAGE
  ${LangFileString} UMUI_TEXT_ADDITIONALTASKS_INFO_TEXT "Select additional tasks that setup must carry out during the setup process of $(^NameDA). $_CLICK"
!endif

!ifdef UMUI_UNADDITIONALTASKSPAGE
  ${LangFileString} UMUI_UNTEXT_ADDITIONALTASKS_INFO_TEXT "Select additional tasks that setup must carry out during the uninstall process of $(^NameDA). $_CLICK"
!endif

!ifdef UMUI_ADDITIONALTASKSPAGE | UMUI_UNADDITIONALTASKSPAGE
  ${LangFileString} UMUI_TEXT_ADDITIONALTASKS_TITLE "Additional Tasks"
  ${LangFileString} UMUI_TEXT_ADDITIONALTASKS_SUBTITLE "Which are the additional tasks which must be carried out?"
  ${LangFileString} UMUI_TEXT_ADDITIONALTASKS_ADDITIONAL_ICONS "Additional Icons:"
  ${LangFileString} UMUI_TEXT_ADDITIONALTASKS_CREATE_DESKTOP_ICON "Create a desktop icon"
  ${LangFileString} UMUI_TEXT_ADDITIONALTASKS_CREATE_QUICK_LAUNCH_ICON "Create a Quick Launch icon"
  ${LangFileString} UMUI_TEXT_ADDITIONALTASKS_ADVANCED_PARAMETERS "Advanced parameters:"
  ${LangFileString} UMUI_TEXT_ADDITIONALTASKS_LAUNCH_PROGRAM_AT_WINDOWS_STARTUP "Launch $(^NameDA) at the windows startup"
  ${LangFileString} UMUI_TEXT_ADDITIONALTASKS_FILE_ASSOCIATION "File Association:"
  ${LangFileString} UMUI_TEXT_ADDITIONALTASKS_ASSOCIATE_WITH "Associate $(^NameDA) with the "
  ${LangFileString} UMUI_TEXT_ADDITIONALTASKS_ASSOCIATE_WITH_END " file type"
!endif


!ifdef UMUI_CONFIRMPAGE | UMUI_UNCONFIRMPAGE | UMUI_ALTERNATIVESTARTMENUPAGE | UMUI_UNALTERNATIVESTARTMENUPAGE
  ${LangFileString} UMUI_TEXT_SHELL_VAR_CONTEXT "How the shortcuts will be created:"
  ${LangFileString} UMUI_TEXT_SHELL_VAR_CONTEXT_FOR_ALL_USERS "For all users"
  ${LangFileString} UMUI_TEXT_SHELL_VAR_CONTEXT_ONLY_FOR_CURRENT_USER "Only for the current user"
!endif


!ifdef UMUI_UPDATEPAGE
  ${LangFileString} UMUI_TEXT_UPDATE_TITLE "Update"
  ${LangFileString} UMUI_TEXT_UPDATE_SUBTITLE "Update a previous version of the program."
  ${LangFileString} UMUI_TEXT_UPDATE_INFO_TEXT "Welcome to the $(^NameDA) update wizard.$\r$\nThis program lets you update the version $OLDVERSION which was found on your computer."
  ${LangFileString} UMUI_TEXT_UPDATE_UPDATE_TITLE "Update"
  ${LangFileString} UMUI_TEXT_UPDATE_UPDATE_TEXT "Update all $(^NameDA) components already installed to the version $NEWVERSION."
  ${LangFileString} UMUI_TEXT_UPDATE_REMOVE_TITLE "Remove"
  ${LangFileString} UMUI_TEXT_UPDATE_REMOVE_TEXT "Uninstall the version $OLDVERSION from your computer."
  ${LangFileString} UMUI_TEXT_UPDATE_CONTINUE_TITLE "Continue setup"
  ${LangFileString} UMUI_TEXT_UPDATE_CONTINUE_TEXT "Continue the setup as usual. Use this option if you want to install this newer version in an other folder in parallel with the preceding setup."
!endif


!ifdef UMUI_MAINTENANCEPAGE | UMUI_UNMAINTENANCEPAGE
  ${LangFileString} UMUI_TEXT_MAINTENANCE_TITLE "Maintenance"
  ${LangFileString} UMUI_TEXT_MAINTENANCE_SUBTITLE "Modify, repair, or remove the program."
  ${LangFileString} UMUI_TEXT_MAINTENANCE_INFO_TEXT "Welcome to the $(^NameDA) setup maintenance program.$\r$\nThis program lets you modify the current installation."
  ${LangFileString} UMUI_TEXT_MAINTENANCE_MODIFY_TITLE "Modify"
  ${LangFileString} UMUI_TEXT_MAINTENANCE_MODIFY_TEXT "Select new components to add or select already installed components to remove."
  ${LangFileString} UMUI_TEXT_MAINTENANCE_REPAIR_TITLE "Repair"
  ${LangFileString} UMUI_TEXT_MAINTENANCE_REPAIR_TEXT "Reinstall all $(^NameDA) components already installed."
  ${LangFileString} UMUI_TEXT_MAINTENANCE_REMOVE_TITLE "Remove"
  ${LangFileString} UMUI_TEXT_MAINTENANCE_REMOVE_TEXT "Uninstall $(^NameDA) from your computer."
  ${LangFileString} UMUI_TEXT_MAINTENANCE_CONTINUE_TITLE "Continue setup"
  ${LangFileString} UMUI_TEXT_MAINTENANCE_CONTINUE_TEXT "Continue the setup as usual. Use this option if you want to reinstall this program over an existing install or to install it a new time in a different folder."
!endif


!ifdef UMUI_FILEDISKREQUESTPAGE | UMUI_UNFILEDISKREQUESTPAGE
  ${LangFileString} UMUI_TEXT_FILEDISKREQUEST_FILE_SUBTITLE_BEGIN "Setup needs the"
  ${LangFileString} UMUI_TEXT_FILEDISKREQUEST_FILE_SUBTITLE_END "file to continue."
  ${LangFileString} UMUI_TEXT_FILEDISKREQUEST_DISK_SUBTITLE "Setup needs the next disk to continue."
  ${LangFileString} UMUI_TEXT_FILEDISKREQUEST_FILE_BEGIN "Specify the location of the file"
  ${LangFileString} UMUI_TEXT_FILEDISKREQUEST_FILE_END "to continue."
  ${LangFileString} UMUI_TEXT_FILEDISKREQUEST_DISK "Please insert the"
  ${LangFileString} UMUI_TEXT_FILEDISKREQUEST_PATH "Path:"
!endif
