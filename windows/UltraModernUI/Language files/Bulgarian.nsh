;NSIS Modern User Interface - Language File
;Compatible with UltraModernUI 2.0 beta 1

;Language: Bulgarian (1026)
;By Angel <laterist@gmail.com> (copied from English and translated)
;--------------------------------

!ifdef UMUI_MULTILANGUAGEPAGE
  ${LangFileString} UMUI_TEXT_MULTILANGUAGE_TITLE "Добре дошли в съветника за инсталация на $(^NameDA)"
  ${LangFileString} UMUI_TEXT_MULTILANGUAGE_TEXT "Моля изберете език преди да започнете инсталацията на $(^NameDA):$\r$\n$\r$\n$_CLICK"
!endif

!ifdef UMUI_UNMULTILANGUAGEPAGE
  ${LangFileString} UMUI_UNTEXT_MULTILANGUAGE_TITLE "Добре дошли в съветника за премахване на $(^NameDA)"
  ${LangFileString} UMUI_UNTEXT_MULTILANGUAGE_TEXT "Моля изберете език преди да започнете премахването на $(^NameDA):$\r$\n$\r$\n$_CLICK"
!endif

!ifdef UMUI_MULTILANGUAGEPAGE | UMUI_UNMULTILANGUAGEPAGE
  ${LangFileString} UMUI_TEXT_MULTILANGUAGE_LANGUAGE "Език:"
!endif


!ifdef MUI_WELCOMEPAGE
  ${LangFileString} UMUI_TEXT_WELCOME_ALTERNATIVEINFO_TEXT "Този съветник ще ви преведе през стъпките необходими за инсталация на $(^NameDA).$\r$\n$\r$\n$\r$\n$_CLICK"
!endif


!ifdef UMUI_SERIALNUMBERPAGE | UMUI_UNSERIALNUMBERPAGE
  ${LangFileString} UMUI_TEXT_SERIALNUMBER_TITLE "Въведете Вашия сериен номер за $(^NameDA)"
  ${LangFileString} UMUI_TEXT_SERIALNUMBER_SUBTITLE "Моля попълнете полетата по-долу."
  ${LangFileString} UMUI_TEXT_SERIALNUMBER_INFO_TEXT "Моля попълнете различните полета по-долу. $_CLICK"
  ${LangFileString} UMUI_TEXT_SERIALNUMBER_INVALIDATE_TEXT "$UMUI_SNTEXT е неправилен. Моля потвъредете информацията, която въведохте."
  ${LangFileString} UMUI_TEXT_SERIALNUMBER_NAME "Име"
  ${LangFileString} UMUI_TEXT_SERIALNUMBER_ORGANIZATION "Организация"
  ${LangFileString} UMUI_TEXT_SERIALNUMBER_SERIALNUMBER "Сериен номер"
  ${LangFileString} UMUI_TEXT_SERIALNUMBER_ACTIVATIONCODE "Код за активация"
  ${LangFileString} UMUI_TEXT_SERIALNUMBER_PASSWORD "Парола"
!endif


!ifdef UMUI_CONFIRMPAGE
  ${LangFileString} UMUI_TEXT_INSTCONFIRM_SUBTITLE "Съветникът събра необходимата информация и е готов за инсталация на $(^NameDA)."
  ${LangFileString} UMUI_TEXT_INSTCONFIRM_TITLE "Потвърдете инсталацията"
  ${LangFileString} UMUI_TEXT_INSTCONFIRM_TEXT_TOP "Съветникът е готова да установи $(^NameDA) на Вашия комоютър.$\r$\nАко желаете да проверите или промените някоя от настройките за инсталация, моля натиснете $(^BackBtn). $_CLICK"
!endif

!ifdef UMUI_UNCONFIRMPAGE
  ${LangFileString} UMUI_UNTEXT_INSTCONFIRM_SUBTITLE "Съветникът събра необходимата информация и е готов за премахване на $(^NameDA)."
  ${LangFileString} UMUI_UNTEXT_INSTCONFIRM_TITLE "Потвърдете премахването"
  ${LangFileString} UMUI_UNTEXT_INSTCONFIRM_TEXT_TOP "Съветникът е готова да премахне $(^NameDA) от Вашия комоютър.$\r$\nАко желаете да проверите или промените някоя от настройките за премахване, моля натиснете $(^BackBtn). Натиснете $(^NextBtn) за да започнете премахването."
!endif

!ifdef UMUI_CONFIRMPAGE | UMUI_UNCONFIRMPAGE
  ${LangFileString} UMUI_TEXT_INSTCONFIRM_TEXTBOX_TITLE "Настоящи настройки:"
  ${LangFileString} UMUI_TEXT_INSTCONFIRM_TEXTBOX_DESTINATION_LOCATION "Целева папка:"
  ${LangFileString} UMUI_TEXT_INSTCONFIRM_TEXTBOX_START_MENU_FOLDER "Папка в началното меню:"
  ${LangFileString} UMUI_TEXT_INSTCONFIRM_TEXTBOX_COMPNENTS "Следните части ще бъдат установени:"
!endif


!ifdef UMUI_ABORTPAGE
  ${LangFileString} UMUI_TEXT_ABORT_INFO_TITLE "Завършване на съветника по инсталация на $(^NameDA)"
  ${LangFileString} UMUI_TEXT_ABORT_INFO_TEXT "Съветникът беще прекъснат преди инсталацията на $(^NameDA) да може да бъде напълно завършена.$\r$\n$\r$\nЗа да завършите инсталацията на това приложение на по-късен етап, моля заредете съветника отново.$\r$\n$\r$\n$\r$\n$\r$\nНатиснете $(^CloseBtn) за да излезете от съветника по инсталация."
!endif

!ifdef UMUI_UNABORTPAGE
  ${LangFileString} UMUI_UNTEXT_ABORT_INFO_TITLE "Завършване на съветника по премахване на $(^NameDA)"
  ${LangFileString} UMUI_UNTEXT_ABORT_INFO_TEXT "Съветникът беще прекъснат преди премахването на $(^NameDA) да може да бъде напълно завършено.$\r$\n$\r$\nЗа да завършите премахването на това приложение на по-късен етап, моля заредете съветника отново.$\r$\n$\r$\n$\r$\n$\r$\nНатиснете $(^CloseBtn) за да излезете от съветника по премахване."
!endif


!ifdef UMUI_SETUPTYPEPAGE
  ${LangFileString} UMUI_TEXT_SETUPTYPE_TITLE "Вид на инсталация"
  ${LangFileString} UMUI_TEXT_SETUPTYPE_SUBTITLE "Моля изберете този вид, който най-добре отговаря на изискванията Ви."
  ${LangFileString} UMUI_TEXT_SETUPTYPE_INFO_TEXT "Моля изберете вид на инсталацията."
  ${LangFileString} UMUI_TEXT_SETUPTYPE_MINIMAL_TEXT "Единствено необходимте части ще бъдат установени. (Заема по-малко пространство на диска)"
  ${LangFileString} UMUI_TEXT_SETUPTYPE_STANDARD_TEXT "Всички основни части ще бъдат установени. Препоръчва се за по-голямата част от потребителите."
  ${LangFileString} UMUI_TEXT_SETUPTYPE_COMPLETE_TEXT "Всички програмни части ще бъдат установени. (Отнема най-много пространство на диска)"
  ${LangFileString} UMUI_TEXT_SETUPTYPE_CUSTOM_TEXT "Изберете, коит програмни части искате да бъдат установени, както и къде да бъдат установени. Препоръчва се за напреднали потребители."
!endif

!ifdef UMUI_UNSETUPTYPEPAGE
  ${LangFileString} UMUI_UNTEXT_SETUPTYPE_TITLE "Вид на премахване"
  ${LangFileString} UMUI_UNTEXT_SETUPTYPE_SUBTITLE "Моля изберете този вид, който най-добре отговаря на изискванията Ви."
  ${LangFileString} UMUI_UNTEXT_SETUPTYPE_INFO_TEXT "Моля изберете вид на премахването."
  ${LangFileString} UMUI_UNTEXT_SETUPTYPE_MINIMAL_TEXT "Единствено необходимте части ще бъдат премахнати."
  ${LangFileString} UMUI_UNTEXT_SETUPTYPE_STANDARD_TEXT "Всички основни части ще бъдат премахнати."
  ${LangFileString} UMUI_UNTEXT_SETUPTYPE_COMPLETE_TEXT "Всички части ще бъдат премахнати."
  ${LangFileString} UMUI_UNTEXT_SETUPTYPE_CUSTOM_TEXT "Изберете, кои части от приложението ще бъдат премахнати."
!endif

!ifdef UMUI_SETUPTYPEPAGE | UMUI_UNSETUPTYPEPAGE
  ${LangFileString} UMUI_TEXT_SETUPTYPE_MINIMAL_TITLE "Минимално"
  ${LangFileString} UMUI_TEXT_SETUPTYPE_STANDARD_TITLE "Обикновено"
  ${LangFileString} UMUI_TEXT_SETUPTYPE_COMPLETE_TITLE "Пълно"
  ${LangFileString} UMUI_TEXT_SETUPTYPE_CUSTOM_TITLE "Ръчно"
!endif


!ifdef UMUI_INFORMATIONPAGE
  ${LangFileString} UMUI_TEXT_INFORMATION_SUBTITLE "Моля отбележете следното относно инсталацията на $(^NameDA)."
!endif

!ifdef UMUI_UNINFORMATIONPAGE
  ${LangFileString} UMUI_UNTEXT_INFORMATION_SUBTITLE "Моля отбележете следното относно премахването на $(^NameDA)."
!endif

!ifdef UMUI_INFORMATIONPAGE | UMUI_UNINFORMATIONPAGE
  ${LangFileString} UMUI_TEXT_INFORMATION_TITLE "Информация"
  ${LangFileString} UMUI_TEXT_INFORMATION_INFO_TEXT "Информация относно $(^NameDA)."
!endif


!ifdef UMUI_ADDITIONALTASKSPAGE
  ${LangFileString} UMUI_TEXT_ADDITIONALTASKS_INFO_TEXT "Изберете допълнителни задачи, които да бъдат извършени по време на инсталацията на $(^NameDA). $_CLICK"
!endif

!ifdef UMUI_UNADDITIONALTASKSPAGE
  ${LangFileString} UMUI_UNTEXT_ADDITIONALTASKS_INFO_TEXT "Изберете допълнителни задачи, които да бъдат извършени по време на премахването на $(^NameDA). $_CLICK"
!endif

!ifdef UMUI_ADDITIONALTASKSPAGE | UMUI_UNADDITIONALTASKSPAGE
  ${LangFileString} UMUI_TEXT_ADDITIONALTASKS_TITLE "Допълнителни задачи"
  ${LangFileString} UMUI_TEXT_ADDITIONALTASKS_SUBTITLE "Кои са допълнителните задачи, които следва да бъдат извършени?"
  ${LangFileString} UMUI_TEXT_ADDITIONALTASKS_ADDITIONAL_ICONS "Допълнителни икони:"
  ${LangFileString} UMUI_TEXT_ADDITIONALTASKS_CREATE_DESKTOP_ICON "Създаване на икона на Работния плот"
  ${LangFileString} UMUI_TEXT_ADDITIONALTASKS_CREATE_QUICK_LAUNCH_ICON "Създаване на икона за Бързо стартиране"
  ${LangFileString} UMUI_TEXT_ADDITIONALTASKS_ADVANCED_PARAMETERS "Допълнителни параметри:"
  ${LangFileString} UMUI_TEXT_ADDITIONALTASKS_LAUNCH_PROGRAM_AT_WINDOWS_STARTUP "Изпълни $(^NameDA) при стартиране на Windows"
  ${LangFileString} UMUI_TEXT_ADDITIONALTASKS_FILE_ASSOCIATION "Асоцииране на видове файлове:"
  ${LangFileString} UMUI_TEXT_ADDITIONALTASKS_ASSOCIATE_WITH "Асоцииране на $(^NameDA) с "
  ${LangFileString} UMUI_TEXT_ADDITIONALTASKS_ASSOCIATE_WITH_END " вид на файл."
!endif


!ifdef UMUI_CONFIRMPAGE | UMUI_UNCONFIRMPAGE | UMUI_ALTERNATIVESTARTMENUPAGE | UMUI_UNALTERNATIVESTARTMENUPAGE
  ${LangFileString} UMUI_TEXT_SHELL_VAR_CONTEXT "Как ще бъдат създадени иконите:"
  ${LangFileString} UMUI_TEXT_SHELL_VAR_CONTEXT_FOR_ALL_USERS "За всички потребители"
  ${LangFileString} UMUI_TEXT_SHELL_VAR_CONTEXT_ONLY_FOR_CURRENT_USER "Само за текущия потребител"
!endif


!ifdef UMUI_UPDATEPAGE
  ${LangFileString} UMUI_TEXT_UPDATE_TITLE "Обновяване"
  ${LangFileString} UMUI_TEXT_UPDATE_SUBTITLE "Обновяване на предна версия на приложението."
  ${LangFileString} UMUI_TEXT_UPDATE_INFO_TEXT "Добре дошли в съветника по обновяване на $(^NameDA).$\r$\nТази програма Ви позволява да обновите версия $OLDVERSION, която бе намерена на Вашия компютър."
  ${LangFileString} UMUI_TEXT_UPDATE_UPDATE_TITLE "Обновяване"
  ${LangFileString} UMUI_TEXT_UPDATE_UPDATE_TEXT "Обновяване на всички части на $(^NameDA), които са вече установени до версия $NEWVERSION."
  ${LangFileString} UMUI_TEXT_UPDATE_REMOVE_TITLE "Премахване"
  ${LangFileString} UMUI_TEXT_UPDATE_REMOVE_TEXT "Премахване на версия $OLDVERSION от Вашия компютър."
  ${LangFileString} UMUI_TEXT_UPDATE_CONTINUE_TITLE "Продължаване на инсталацията"
  ${LangFileString} UMUI_TEXT_UPDATE_CONTINUE_TEXT "Продължаване на обичайната инсталация. Използвайте тази възможност, ако искате да установите новата версия в друга целева папка, заедно с предната инсталация."
!endif


!ifdef UMUI_MAINTENANCEPAGE | UMUI_UNMAINTENANCEPAGE
  ${LangFileString} UMUI_TEXT_MAINTENANCE_TITLE "Поддръжка"
  ${LangFileString} UMUI_TEXT_MAINTENANCE_SUBTITLE "Промяна, поправка или премахване на приложението."
  ${LangFileString} UMUI_TEXT_MAINTENANCE_INFO_TEXT "Добре дошли в съветника по поддръжка на $(^NameDA).$\r$\nТова приложение ще ви позволи да промените настоящото приложение."
  ${LangFileString} UMUI_TEXT_MAINTENANCE_MODIFY_TITLE "Промяна"
  ${LangFileString} UMUI_TEXT_MAINTENANCE_MODIFY_TEXT "Изберете нови части, които да бъдат добавени или съществуващи части, които да бъдат премахнати."
  ${LangFileString} UMUI_TEXT_MAINTENANCE_REPAIR_TITLE "Поправка"
  ${LangFileString} UMUI_TEXT_MAINTENANCE_REPAIR_TEXT "Нова инсталация на всички части на $(^NameDA), които са вече установени."
  ${LangFileString} UMUI_TEXT_MAINTENANCE_REMOVE_TITLE "Премахване"
  ${LangFileString} UMUI_TEXT_MAINTENANCE_REMOVE_TEXT "Премахване на $(^NameDA) от Вашия компютър."
  ${LangFileString} UMUI_TEXT_MAINTENANCE_CONTINUE_TITLE "Продължаване на инсталацията"
  ${LangFileString} UMUI_TEXT_MAINTENANCE_CONTINUE_TEXT "Продължаване на обичайната инсталация. Използвайте тази възможност, ако искате да установите приложението върху вече съществуваща инсталация или да го инсталирате в друга целева папка."
!endif


!ifdef UMUI_FILEDISKREQUESTPAGE | UMUI_UNFILEDISKREQUESTPAGE
  ${LangFileString} UMUI_TEXT_FILEDISKREQUEST_FILE_SUBTITLE_BEGIN "Съветникът има нужда от файл с име"
  ${LangFileString} UMUI_TEXT_FILEDISKREQUEST_FILE_SUBTITLE_END "за да продължи."
  ${LangFileString} UMUI_TEXT_FILEDISKREQUEST_DISK_SUBTITLE "Съветникът има нужда от следващият носител, за да продължи."
  ${LangFileString} UMUI_TEXT_FILEDISKREQUEST_FILE_BEGIN "Укажете местонахождението на файл с име"
  ${LangFileString} UMUI_TEXT_FILEDISKREQUEST_FILE_END "за да продължите."
  ${LangFileString} UMUI_TEXT_FILEDISKREQUEST_DISK "Моля закачете"
  ${LangFileString} UMUI_TEXT_FILEDISKREQUEST_PATH "Пътека:"
!endif
