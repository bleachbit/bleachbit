;NSIS Modern User Interface - Language File
;Compatible with UltraModernUI 2.0 beta 1

;Language: Russian (1049)
;By Matthias <bodenseematze@users.sourceforge.net> (copied from English and translated)
;--------------------------------

!ifdef UMUI_MULTILANGUAGEPAGE
  ${LangFileString} UMUI_TEXT_MULTILANGUAGE_TITLE "Добро пожаловать в установку $(^NameDA)"
  ${LangFileString} UMUI_TEXT_MULTILANGUAGE_TEXT "Выберите, пожалуйста, язык для установки $(^NameDA):$\r$\n$\r$\n$_CLICK"
!endif

!ifdef UMUI_UNMULTILANGUAGEPAGE
  ${LangFileString} UMUI_UNTEXT_MULTILANGUAGE_TITLE "Добро пожаловать в программу деинсталляции $(^NameDA)"
  ${LangFileString} UMUI_UNTEXT_MULTILANGUAGE_TEXT "Выберите, пожалуйста, язык для деинсталляции $(^NameDA):$\r$\n$\r$\n$_CLICK"
!endif

!ifdef UMUI_MULTILANGUAGEPAGE | UMUI_UNMULTILANGUAGEPAGE
  ${LangFileString} UMUI_TEXT_MULTILANGUAGE_LANGUAGE "Язык:"
!endif


!ifdef MUI_WELCOMEPAGE
  ${LangFileString} UMUI_TEXT_WELCOME_ALTERNATIVEINFO_TEXT "Данный ассистент выполнит установку $(^NameDA). $\r$\n$\r$\n$\r$\n$_CLICK"
!endif


!ifdef UMUI_SERIALNUMBERPAGE | UMUI_UNSERIALNUMBERPAGE
  ${LangFileString} UMUI_TEXT_SERIALNUMBER_TITLE "Введите серийный номер $(^NameDA)"
  ${LangFileString} UMUI_TEXT_SERIALNUMBER_SUBTITLE "Заполните различные поля."
  ${LangFileString} UMUI_TEXT_SERIALNUMBER_INFO_TEXT "Заполните различные поля. $_CLICK"
  ${LangFileString} UMUI_TEXT_SERIALNUMBER_INVALIDATE_TEXT "$UMUI_SNTEXT недействительно. Проверьте введенную вами информацию."
  ${LangFileString} UMUI_TEXT_SERIALNUMBER_NAME "Фамилия"
  ${LangFileString} UMUI_TEXT_SERIALNUMBER_ORGANIZATION "Организация"
  ${LangFileString} UMUI_TEXT_SERIALNUMBER_SERIALNUMBER "Серийный номер"
  ${LangFileString} UMUI_TEXT_SERIALNUMBER_ACTIVATIONCODE "Код активации"
  ${LangFileString} UMUI_TEXT_SERIALNUMBER_PASSWORD "Пароль"
!endif


!ifdef UMUI_CONFIRMPAGE
  ${LangFileString} UMUI_TEXT_INSTCONFIRM_SUBTITLE "Необходимая информация для установки $(^NameDA) собрана."
  ${LangFileString} UMUI_TEXT_INSTCONFIRM_TITLE "Подтвердить установку"
  ${LangFileString} UMUI_TEXT_INSTCONFIRM_TEXT_TOP "Программа-ассистент готова к установке $(^NameDA) на ваш компьютер.$\r$\nЕсли требуется проверить или изменить настройки установки, нажмите $(^BackBtn). $_CLICK"
!endif

!ifdef UMUI_UNCONFIRMPAGE
  ${LangFileString} UMUI_UNTEXT_INSTCONFIRM_SUBTITLE "Необходимая информация для деинсталляции $(^NameDA) собрана."
  ${LangFileString} UMUI_UNTEXT_INSTCONFIRM_TITLE "Подтвердить деинсталляцию"
  ${LangFileString} UMUI_UNTEXT_INSTCONFIRM_TEXT_TOP "Программа-ассистент готова к деинсталляции $(^NameDA) с вашего компьютера.$\r$\nЕсли требуется проверить или изменить настройки деинсталляции, нажмите $(^BackBtn). Нажмите $(^NextBtn), чтобы начать  деинсталляцию."
!endif

!ifdef UMUI_CONFIRMPAGE | UMUI_UNCONFIRMPAGE
  ${LangFileString} UMUI_TEXT_INSTCONFIRM_TEXTBOX_TITLE "Актуальная конфигурация:"
  ${LangFileString} UMUI_TEXT_INSTCONFIRM_TEXTBOX_DESTINATION_LOCATION "Место назначения:"
  ${LangFileString} UMUI_TEXT_INSTCONFIRM_TEXTBOX_START_MENU_FOLDER "Папка начального меню:"
  ${LangFileString} UMUI_TEXT_INSTCONFIRM_TEXTBOX_COMPNENTS "Инсталлируются следующие компоненты:"
!endif


!ifdef UMUI_ABORTPAGE
  ${LangFileString} UMUI_TEXT_ABORT_INFO_TITLE "Завершение программы-ассистента деинсталляции $(^NameDA)"
  ${LangFileString} UMUI_TEXT_ABORT_INFO_TEXT "Программа-ассистент была прервана до полной инсталляции $(^NameDA).$\r$\n$\r$\nЧтобы впоследствии инсталлировать программу, выполните эту программу установки заново.$\r$\n$\r$\n$\r$\n$\r$\nНажмите $(^CloseBtn), чтобы закрыть программу-ассистент инсталляции."
!endif

!ifdef UMUI_UNABORTPAGE
  ${LangFileString} UMUI_UNTEXT_ABORT_INFO_TITLE "Выйти из программ-ассистентов деинсталляции для $(^NameDA)"
  ${LangFileString} UMUI_UNTEXT_ABORT_INFO_TEXT "Программа-ассистент была прервана до полной деинсталляции $(^NameDA).$\r$\n$\r$\nЧтобы впоследствии деинсталлировать программу, выполните эту программу установки заново.$\r$\n$\r$\n$\r$\n$\r$\nНажмите $(^CloseBtn), чтобы закрыть программу-ассистент деинсталляции."
!endif


!ifdef UMUI_SETUPTYPEPAGE
  ${LangFileString} UMUI_TEXT_SETUPTYPE_TITLE "Тип установки"
  ${LangFileString} UMUI_TEXT_SETUPTYPE_SUBTITLE "Выбор подходящего типа установки"
  ${LangFileString} UMUI_TEXT_SETUPTYPE_INFO_TEXT "Выберите тип установки."
  ${LangFileString} UMUI_TEXT_SETUPTYPE_MINIMAL_TEXT "Инсталлируются только необходимые функции. (требует минимального объема памяти)"
  ${LangFileString} UMUI_TEXT_SETUPTYPE_STANDARD_TEXT "Инсталлируются все основные функции. Рекомендуется для большинства пользователей."
  ${LangFileString} UMUI_TEXT_SETUPTYPE_COMPLETE_TEXT "Инсталлируются все программные функции. (требует наибольшего объема памяти)"
  ${LangFileString} UMUI_TEXT_SETUPTYPE_CUSTOM_TEXT "Выберите, куда и какие программные функции необходимо установить. Рекомендуется для продвинутых пользователей."
!endif

!ifdef UMUI_UNSETUPTYPEPAGE
  ${LangFileString} UMUI_UNTEXT_SETUPTYPE_TITLE "Тип деинсталляции"
  ${LangFileString} UMUI_UNTEXT_SETUPTYPE_SUBTITLE "Выбор подходящего типа деинсталляции"
  ${LangFileString} UMUI_UNTEXT_SETUPTYPE_INFO_TEXT "Выберите тип деинсталляции."
  ${LangFileString} UMUI_UNTEXT_SETUPTYPE_MINIMAL_TEXT "Сохраняются только основные функции."
  ${LangFileString} UMUI_UNTEXT_SETUPTYPE_STANDARD_TEXT "Инсталлируются только наиболее важные функции."
  ${LangFileString} UMUI_UNTEXT_SETUPTYPE_COMPLETE_TEXT "Сохраняется вся программа."
  ${LangFileString} UMUI_UNTEXT_SETUPTYPE_CUSTOM_TEXT "Выберите программные функции, которые необходимо деинсталлировать."
!endif

!ifdef UMUI_SETUPTYPEPAGE | UMUI_UNSETUPTYPEPAGE
  ${LangFileString} UMUI_TEXT_SETUPTYPE_MINIMAL_TITLE "Минимально"
  ${LangFileString} UMUI_TEXT_SETUPTYPE_STANDARD_TITLE "Стандартно"
  ${LangFileString} UMUI_TEXT_SETUPTYPE_COMPLETE_TITLE "Полностью"
  ${LangFileString} UMUI_TEXT_SETUPTYPE_CUSTOM_TITLE "Определено пользователем"
!endif


!ifdef UMUI_INFORMATIONPAGE
  ${LangFileString} UMUI_TEXT_INFORMATION_SUBTITLE "Учтите информацию об установке  $(^NameDA)."
!endif

!ifdef UMUI_UNINFORMATIONPAGE
  ${LangFileString} UMUI_UNTEXT_INFORMATION_SUBTITLE "Учтите информацию о деинсталляции $(^NameDA)."
!endif

!ifdef UMUI_INFORMATIONPAGE | UMUI_UNINFORMATIONPAGE
  ${LangFileString} UMUI_TEXT_INFORMATION_TITLE "Информация"
  ${LangFileString} UMUI_TEXT_INFORMATION_INFO_TEXT "Информация о $(^NameDA)."
!endif


!ifdef UMUI_ADDITIONALTASKSPAGE
  ${LangFileString} UMUI_TEXT_ADDITIONALTASKS_INFO_TEXT "Выберите дополнительные действия, которые программа должна выполнить во время процесса установки  $(^NameDA). $_CLICK"
!endif

!ifdef UMUI_UNADDITIONALTASKSPAGE
  ${LangFileString} UMUI_UNTEXT_ADDITIONALTASKS_INFO_TEXT "Выберите дополнительные действия, которые программа должна выполнить во время процесса деинсталляции $(^NameDA). $_CLICK"
!endif

!ifdef UMUI_ADDITIONALTASKSPAGE | UMUI_UNADDITIONALTASKSPAGE
  ${LangFileString} UMUI_TEXT_ADDITIONALTASKS_TITLE "Дополнительные действия"
  ${LangFileString} UMUI_TEXT_ADDITIONALTASKS_SUBTITLE "Какие дополнительные действия необходимо выполнить?"
  ${LangFileString} UMUI_TEXT_ADDITIONALTASKS_ADDITIONAL_ICONS "Дополнительные пиктограммы:"
  ${LangFileString} UMUI_TEXT_ADDITIONALTASKS_CREATE_DESKTOP_ICON "Создайте пиктограмму на рабочем столе"
  ${LangFileString} UMUI_TEXT_ADDITIONALTASKS_CREATE_QUICK_LAUNCH_ICON "Создайте пиктограмму на панели быстрого запуска"
  ${LangFileString} UMUI_TEXT_ADDITIONALTASKS_ADVANCED_PARAMETERS "Параметры для продвинутого пользователя:"
  ${LangFileString} UMUI_TEXT_ADDITIONALTASKS_LAUNCH_PROGRAM_AT_WINDOWS_STARTUP "Запустите $(^NameDA) после запуска системы"
  ${LangFileString} UMUI_TEXT_ADDITIONALTASKS_FILE_ASSOCIATION "Файловые ссылки:"
  ${LangFileString} UMUI_TEXT_ADDITIONALTASKS_ASSOCIATE_WITH "Свяжите $(^NameDA) с "
  ${LangFileString} UMUI_TEXT_ADDITIONALTASKS_ASSOCIATE_WITH_END " Тип файла"
!endif


!ifdef UMUI_CONFIRMPAGE | UMUI_UNCONFIRMPAGE | UMUI_ALTERNATIVESTARTMENUPAGE | UMUI_UNALTERNATIVESTARTMENUPAGE
  ${LangFileString} UMUI_TEXT_SHELL_VAR_CONTEXT "Для кого необходимо создать ссылки:"
  ${LangFileString} UMUI_TEXT_SHELL_VAR_CONTEXT_FOR_ALL_USERS "Для всех пользователей"
  ${LangFileString} UMUI_TEXT_SHELL_VAR_CONTEXT_ONLY_FOR_CURRENT_USER "Только для зарегистрированных пользователей"
!endif


!ifdef UMUI_UPDATEPAGE
  ${LangFileString} UMUI_TEXT_UPDATE_TITLE "Обновить"
  ${LangFileString} UMUI_TEXT_UPDATE_SUBTITLE "Обновление предыдущей версии программы."
  ${LangFileString} UMUI_TEXT_UPDATE_INFO_TEXT "Добро пожаловать в программу-ассистент инсталляции $(^NameDA).Данная$\r$\nДанная программа выполнит обновление версии $OLDVERSION."
  ${LangFileString} UMUI_TEXT_UPDATE_UPDATE_TITLE "Обновление"
  ${LangFileString} UMUI_TEXT_UPDATE_UPDATE_TEXT "обновления всех уже инсталлированных компонентов до версии $NEWVERSION."
  ${LangFileString} UMUI_TEXT_UPDATE_REMOVE_TITLE "Удалить"
  ${LangFileString} UMUI_TEXT_UPDATE_REMOVE_TEXT "Деинсталляция версии $OLDVERSION с компьютера."
  ${LangFileString} UMUI_TEXT_UPDATE_CONTINUE_TITLE "Продолжить установку"
  ${LangFileString} UMUI_TEXT_UPDATE_CONTINUE_TEXT "Продолжить установку как обычно. Используйте эту опцию, если новая версия должна быть установлена в другой папке параллельно с уже существующей версией."
!endif


!ifdef UMUI_MAINTENANCEPAGE | UMUI_UNMAINTENANCEPAGE
  ${LangFileString} UMUI_TEXT_MAINTENANCE_TITLE "Настроить"
  ${LangFileString} UMUI_TEXT_MAINTENANCE_SUBTITLE "Изменить, восстановить или удалить программу."
  ${LangFileString} UMUI_TEXT_MAINTENANCE_INFO_TEXT "Добро пожаловать в программу-ассистент настройки $(^NameDA).$\r$\nПри помощи данной программы можно изменить актуальную установку."
  ${LangFileString} UMUI_TEXT_MAINTENANCE_MODIFY_TITLE "Изменить"
  ${LangFileString} UMUI_TEXT_MAINTENANCE_MODIFY_TEXT "Выберите новые компоненты, чтобы их установить, или уже существующие, чтобы их деинсталлировать."
  ${LangFileString} UMUI_TEXT_MAINTENANCE_REPAIR_TITLE "Восстановить"
  ${LangFileString} UMUI_TEXT_MAINTENANCE_REPAIR_TEXT "Переустановка всех уже существующих компонентов $(^NameDA)."
  ${LangFileString} UMUI_TEXT_MAINTENANCE_REMOVE_TITLE "Удалить"
  ${LangFileString} UMUI_TEXT_MAINTENANCE_REMOVE_TEXT "Деинсталляция $(^NameDA) с компьютера."
  ${LangFileString} UMUI_TEXT_MAINTENANCE_CONTINUE_TITLE "Продолжить установку"
  ${LangFileString} UMUI_TEXT_MAINTENANCE_CONTINUE_TEXT "Продолжить установку как обычно. Используйте эту опцию, если хотите инсталлировать программу поверх уже существующей установки или для повторной установки в новом каталоге."
!endif


!ifdef UMUI_FILEDISKREQUESTPAGE | UMUI_UNFILEDISKREQUESTPAGE
  ${LangFileString} UMUI_TEXT_FILEDISKREQUEST_FILE_SUBTITLE_BEGIN "Для установки требуется"
  ${LangFileString} UMUI_TEXT_FILEDISKREQUEST_FILE_SUBTITLE_END "файлом для продолжения работы."
  ${LangFileString} UMUI_TEXT_FILEDISKREQUEST_DISK_SUBTITLE "Для установки требуется следующий носитель данных для продолжения работы."
  ${LangFileString} UMUI_TEXT_FILEDISKREQUEST_FILE_BEGIN "Выберите место сохранения файла"
  ${LangFileString} UMUI_TEXT_FILEDISKREQUEST_FILE_END "для продолжения работы."
  ${LangFileString} UMUI_TEXT_FILEDISKREQUEST_DISK "Вставьте новый носитель данных"
  ${LangFileString} UMUI_TEXT_FILEDISKREQUEST_PATH "путь:"
!endif
