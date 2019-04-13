;NSIS Modern User Interface - Language File
;Compatible with UltraModernUI 2.0 beta 1

;Language: Spanish (1034)
;By Matthias <bodenseematze@users.sourceforge.net> (copied from English and translated)
;--------------------------------

!ifdef UMUI_MULTILANGUAGEPAGE
  ${LangFileString} UMUI_TEXT_MULTILANGUAGE_TITLE "Bienvenido al asistente de Setup de $(^NameDA)"
  ${LangFileString} UMUI_TEXT_MULTILANGUAGE_TEXT "Por favor, seleccione antes de la instalación de $(^NameDA) un idioma:$\r$\n$\r$\n$_CLICK"
!endif

!ifdef UMUI_UNMULTILANGUAGEPAGE
  ${LangFileString} UMUI_UNTEXT_MULTILANGUAGE_TITLE "Bienvenido al asistente de desinstalación de $(^NameDA)"
  ${LangFileString} UMUI_UNTEXT_MULTILANGUAGE_TEXT "Por favor, seleccione antes de la desinstalación de $(^NameDA) un idioma:$\r$\n$\r$\n$_CLICK"
!endif

!ifdef UMUI_MULTILANGUAGEPAGE | UMUI_UNMULTILANGUAGEPAGE
  ${LangFileString} UMUI_TEXT_MULTILANGUAGE_LANGUAGE "Idioma:"
!endif


!ifdef MUI_WELCOMEPAGE
  ${LangFileString} UMUI_TEXT_WELCOME_ALTERNATIVEINFO_TEXT "Este asistente lo guiará a través de la instalación de $(^NameDA).$\r$\n$\r$\n$\r$\n$_CLICK"
!endif


!ifdef UMUI_SERIALNUMBERPAGE | UMUI_UNSERIALNUMBERPAGE
  ${LangFileString} UMUI_TEXT_SERIALNUMBER_TITLE "Por favor, introduzca el número de serie para $(^NameDA)"
  ${LangFileString} UMUI_TEXT_SERIALNUMBER_SUBTITLE "Por favor, complete los diferentes campos."
  ${LangFileString} UMUI_TEXT_SERIALNUMBER_INFO_TEXT "Por favor, complete los diferentes campos. $_CLICK"
  ${LangFileString} UMUI_TEXT_SERIALNUMBER_INVALIDATE_TEXT "$UMUI_SNTEXT es inválido. Por favor, compruebe su información introducida."
  ${LangFileString} UMUI_TEXT_SERIALNUMBER_NAME "Nombre"
  ${LangFileString} UMUI_TEXT_SERIALNUMBER_ORGANIZATION "Organización"
  ${LangFileString} UMUI_TEXT_SERIALNUMBER_SERIALNUMBER "Número de serie"
  ${LangFileString} UMUI_TEXT_SERIALNUMBER_ACTIVATIONCODE "Código de activación"
  ${LangFileString} UMUI_TEXT_SERIALNUMBER_PASSWORD "Contraseña"
!endif 


!ifdef UMUI_CONFIRMPAGE
  ${LangFileString} UMUI_TEXT_INSTCONFIRM_SUBTITLE "Setup ha reunido la información necesaria y está dispuesto a instalar $(^NameDA)."
  ${LangFileString} UMUI_TEXT_INSTCONFIRM_TITLE "Confirmar instalación"
  ${LangFileString} UMUI_TEXT_INSTCONFIRM_TEXT_TOP "Setup está dispuesto a instalar $(^NameDA) en su ordenador. $\r$\nEn caso de que aún desee comprobar o modificar las configuraciones de su instalación haga clic en $(^BackBtn). $_CLICK"
!endif 

!ifdef UMUI_UNCONFIRMPAGE
  ${LangFileString} UMUI_UNTEXT_INSTCONFIRM_SUBTITLE "Setup ha reunido la información necesaria y está dispuesto a desinstalar $(^NameDA)."
  ${LangFileString} UMUI_UNTEXT_INSTCONFIRM_TITLE "Confirmar desinstalación"
  ${LangFileString} UMUI_UNTEXT_INSTCONFIRM_TEXT_TOP "Setup está dispuesto a desinstalar $(^NameDA) de su ordenador. $\r$\nEn caso de que aún desee comprobar o modificar las configuraciones de su desinstalación haga clic en $(^BackBtn). Haga clic en $(^NextBtn) para comenzar con la desinstalación."
!endif 

!ifdef UMUI_CONFIRMPAGE | UMUI_UNCONFIRMPAGE
  ${LangFileString} UMUI_TEXT_INSTCONFIRM_TEXTBOX_TITLE "Configuración actual:"
  ${LangFileString} UMUI_TEXT_INSTCONFIRM_TEXTBOX_DESTINATION_LOCATION "Localización de destino:"
  ${LangFileString} UMUI_TEXT_INSTCONFIRM_TEXTBOX_START_MENU_FOLDER "Carpeta de menú de inicio:"
  ${LangFileString} UMUI_TEXT_INSTCONFIRM_TEXTBOX_COMPNENTS "Se instalan los siguientes componentes:"
!endif 


!ifdef UMUI_ABORTPAGE
  ${LangFileString} UMUI_TEXT_ABORT_INFO_TITLE "Finalizar al asistente de Setup $(^NameDA)"
  ${LangFileString} UMUI_TEXT_ABORT_INFO_TEXT "El asistente ha sido cancelado antes de que $(^NameDA) haya podido ser instalado completamente.$\r$\n$\r$\nPara instalar el programa en un momento posterior, ejecute por favor nuevamente este Setup.$\r$\n$\r$\n$\r$\n$\r$\nHaga clic en $(^CloseBtn), para cerrar el asistente de instalación."
!endif 

!ifdef UMUI_UNABORTPAGE
  ${LangFileString} UMUI_UNTEXT_ABORT_INFO_TITLE "Finalizar el asistente de desinstalación para $(^NameDA)"
  ${LangFileString} UMUI_UNTEXT_ABORT_INFO_TEXT "El asistente ha sido cancelado antes de que $(^NameDA) haya podido ser desinstalado completamente.$\r$\n$\r$\nPara desinstalar el programa en un momento posterior, ejecute por favor nuevamente este Setup.$\r$\n$\r$\n$\r$\n$\r$\nHaga clic en $(^CloseBtn), para cerrar el asistente de desinstalación."
!endif


!ifdef UMUI_SETUPTYPEPAGE
  ${LangFileString} UMUI_TEXT_SETUPTYPE_TITLE "Tipo de Setup"
  ${LangFileString} UMUI_TEXT_SETUPTYPE_SUBTITLE "Seleccione el mejor tipo de Setup para usted."
  ${LangFileString} UMUI_TEXT_SETUPTYPE_INFO_TEXT "Seleccione por favor un tipo de Setup."
  ${LangFileString} UMUI_TEXT_SETUPTYPE_MINIMAL_TEXT "Solo se instalan las funciones necesarias. (necesita el mínimo espacio de memoria)"
  ${LangFileString} UMUI_TEXT_SETUPTYPE_STANDARD_TEXT "Se instalan todas las funciones principales. Recomendado para la mayoría de usuarios."
  ${LangFileString} UMUI_TEXT_SETUPTYPE_COMPLETE_TEXT "Se instalan todas las funciones del programa. (necesita el máximo espacio de memoria)"
  ${LangFileString} UMUI_TEXT_SETUPTYPE_CUSTOM_TEXT "Por favor seleccione qué funcionalidad de programa y donde quiere que sea instalada. Recomendado para usuarios avanzados."
!endif 

!ifdef UMUI_UNSETUPTYPEPAGE
  ${LangFileString} UMUI_UNTEXT_SETUPTYPE_TITLE "Tipo de desinstalación"
  ${LangFileString} UMUI_UNTEXT_SETUPTYPE_SUBTITLE "Seleccione el mejor tipo de desinstalación para usted."
  ${LangFileString} UMUI_UNTEXT_SETUPTYPE_INFO_TEXT "Seleccione por favor un tipo de desinstalación"
  ${LangFileString} UMUI_UNTEXT_SETUPTYPE_MINIMAL_TEXT "Solo se mantienen las funciones principales."
  ${LangFileString} UMUI_UNTEXT_SETUPTYPE_STANDARD_TEXT "Solo se mantienen las funciones más importantes."
  ${LangFileString} UMUI_UNTEXT_SETUPTYPE_COMPLETE_TEXT "Se mantiene todo el programa."
  ${LangFileString} UMUI_UNTEXT_SETUPTYPE_CUSTOM_TEXT "Seleccione qué funcionalidad de programa quiere desinstalar."
!endif 

!ifdef UMUI_SETUPTYPEPAGE | UMUI_UNSETUPTYPEPAGE
  ${LangFileString} UMUI_TEXT_SETUPTYPE_MINIMAL_TITLE "Mínima"
  ${LangFileString} UMUI_TEXT_SETUPTYPE_STANDARD_TITLE "Estándar"
  ${LangFileString} UMUI_TEXT_SETUPTYPE_COMPLETE_TITLE "Completa"
  ${LangFileString} UMUI_TEXT_SETUPTYPE_CUSTOM_TITLE "Definida por el usuario"
!endif 


!ifdef UMUI_INFORMATIONPAGE
  ${LangFileString} UMUI_TEXT_INFORMATION_SUBTITLE "Por favor observe la información sobre la instalación de $(^NameDA)."
!endif 

!ifdef UMUI_UNINFORMATIONPAGE
  ${LangFileString} UMUI_UNTEXT_INFORMATION_SUBTITLE "Por favor observe la información sobre la desinstalación de $(^NameDA)."
!endif 

!ifdef UMUI_INFORMATIONPAGE | UMUI_UNINFORMATIONPAGE
  ${LangFileString} UMUI_TEXT_INFORMATION_TITLE "Información"
  ${LangFileString} UMUI_TEXT_INFORMATION_INFO_TEXT "Información sobre $(^NameDA)."
!endif 


!ifdef UMUI_ADDITIONALTASKSPAGE
  ${LangFileString} UMUI_TEXT_ADDITIONALTASKS_INFO_TEXT "Seleccione acciones adicionales que debe ejecutar el Setup durante el proceso de instalación de $(^NameDA). $_CLICK"
!endif 

!ifdef UMUI_UNADDITIONALTASKSPAGE
  ${LangFileString} UMUI_UNTEXT_ADDITIONALTASKS_INFO_TEXT "Seleccione acciones adicionales que debe ejecutar el Setup durante el proceso de desinstalación de $(^NameDA). $_CLICK"
!endif 

!ifdef UMUI_ADDITIONALTASKSPAGE | UMUI_UNADDITIONALTASKSPAGE
  ${LangFileString} UMUI_TEXT_ADDITIONALTASKS_TITLE "Acciones adicionales"
  ${LangFileString} UMUI_TEXT_ADDITIONALTASKS_SUBTITLE "¿Qué acciones adicionales tienen que ser ejecutadas?"
  ${LangFileString} UMUI_TEXT_ADDITIONALTASKS_ADDITIONAL_ICONS "Iconos adicionales:"
  ${LangFileString} UMUI_TEXT_ADDITIONALTASKS_CREATE_DESKTOP_ICON "Crear un icono en el escritorio"
  ${LangFileString} UMUI_TEXT_ADDITIONALTASKS_CREATE_QUICK_LAUNCH_ICON "Crear un icono en la barra de tareas"
  ${LangFileString} UMUI_TEXT_ADDITIONALTASKS_ADVANCED_PARAMETERS "Parámetros avanzados:"
  ${LangFileString} UMUI_TEXT_ADDITIONALTASKS_LAUNCH_PROGRAM_AT_WINDOWS_STARTUP "Iniciar $(^NameDA) tras un inicio de sistema"
  ${LangFileString} UMUI_TEXT_ADDITIONALTASKS_FILE_ASSOCIATION "Enlace de archivos:"
  ${LangFileString} UMUI_TEXT_ADDITIONALTASKS_ASSOCIATE_WITH "Enlace $(^NameDA) con "
  ${LangFileString} UMUI_TEXT_ADDITIONALTASKS_ASSOCIATE_WITH_END " tipo de archivo"
!endif 
  
  
!ifdef UMUI_CONFIRMPAGE | UMUI_UNCONFIRMPAGE | UMUI_ALTERNATIVESTARTMENUPAGE | UMUI_UNALTERNATIVESTARTMENUPAGE
  ${LangFileString} UMUI_TEXT_SHELL_VAR_CONTEXT "Para quién deben ser creados los enlaces:"
  ${LangFileString} UMUI_TEXT_SHELL_VAR_CONTEXT_FOR_ALL_USERS "Para todos los usuarios"
  ${LangFileString} UMUI_TEXT_SHELL_VAR_CONTEXT_ONLY_FOR_CURRENT_USER "Solo para el usuario registrado"
!endif


!ifdef UMUI_UPDATEPAGE
  ${LangFileString} UMUI_TEXT_UPDATE_TITLE "Actualización"
  ${LangFileString} UMUI_TEXT_UPDATE_SUBTITLE "Actualización a una versión anterior del programa."
  ${LangFileString} UMUI_TEXT_UPDATE_INFO_TEXT "Bienvenido al asistente de actualización $(^NameDA).$\r$\nEste programa ejecuta una actualización a la versión $OLDVERSION."
  ${LangFileString} UMUI_TEXT_UPDATE_UPDATE_TITLE "Actualización"
  ${LangFileString} UMUI_TEXT_UPDATE_UPDATE_TEXT "Actualizar todos los componentes ya instalados de $(^NameDA) a la versión $NEWVERSION."
  ${LangFileString} UMUI_TEXT_UPDATE_REMOVE_TITLE "Eliminar"
  ${LangFileString} UMUI_TEXT_UPDATE_REMOVE_TEXT "Desinstalación de la versión $OLDVERSION de su ordenador."
  ${LangFileString} UMUI_TEXT_UPDATE_CONTINUE_TITLE "Continuar Setup"
  ${LangFileString} UMUI_TEXT_UPDATE_CONTINUE_TEXT "Continuar Setup como habitualmente. Utilice esta opción cuando la nueva versión tiene que ser instalada en otro ordenador paralelamente a la versión existente."
!endif


!ifdef UMUI_MAINTENANCEPAGE | UMUI_UNMAINTENANCEPAGE
  ${LangFileString} UMUI_TEXT_MAINTENANCE_TITLE "Administración"
  ${LangFileString} UMUI_TEXT_MAINTENANCE_SUBTITLE "Modificar, reparar o eliminar un programa."
  ${LangFileString} UMUI_TEXT_MAINTENANCE_INFO_TEXT "Bienvenido al programa de administración $(^NameDA).$\r$\nCon este programa puede modificar su instalación actual."
  ${LangFileString} UMUI_TEXT_MAINTENANCE_MODIFY_TITLE "Modificar"
  ${LangFileString} UMUI_TEXT_MAINTENANCE_MODIFY_TEXT "Seleccione componentes nuevos para ser instalados o ya existentes para desinstalarlos."
  ${LangFileString} UMUI_TEXT_MAINTENANCE_REPAIR_TITLE "Reparar"
  ${LangFileString} UMUI_TEXT_MAINTENANCE_REPAIR_TEXT "Reinstalación de todos los componentes $(^NameDA) ya instalados."
  ${LangFileString} UMUI_TEXT_MAINTENANCE_REMOVE_TITLE "Eliminar"
  ${LangFileString} UMUI_TEXT_MAINTENANCE_REMOVE_TEXT "Desinstalación de $(^NameDA) de su ordenador."
  ${LangFileString} UMUI_TEXT_MAINTENANCE_CONTINUE_TITLE "Continuar Setup"
  ${LangFileString} UMUI_TEXT_MAINTENANCE_CONTINUE_TEXT "Continuar Setup como habitualmente. Utilice esta opción si desea instalar el programa sobre una instalación ya existente o ejecutar una nueva instalación en otro directorio."
!endif


!ifdef UMUI_FILEDISKREQUESTPAGE | UMUI_UNFILEDISKREQUESTPAGE
  ${LangFileString} UMUI_TEXT_FILEDISKREQUEST_FILE_SUBTITLE_BEGIN "Setup necesita el siguiente soporte de datos para poder continuar."
  ${LangFileString} UMUI_TEXT_FILEDISKREQUEST_FILE_SUBTITLE_END "archivo para poder continuar."
  ${LangFileString} UMUI_TEXT_FILEDISKREQUEST_DISK_SUBTITLE "Setup necesita el siguiente soporte de datos para poder continuar."
  ${LangFileString} UMUI_TEXT_FILEDISKREQUEST_FILE_BEGIN "Seleccione la localización de guardado del archivo"
  ${LangFileString} UMUI_TEXT_FILEDISKREQUEST_FILE_END "para continuar."
  ${LangFileString} UMUI_TEXT_FILEDISKREQUEST_DISK "Por favor, introduzca la"
  ${LangFileString} UMUI_TEXT_FILEDISKREQUEST_PATH "ruta:"
!endif
