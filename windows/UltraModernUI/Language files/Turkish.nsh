;NSIS Modern User Interface - Language File
;Compatible with UltraModernUI 2.0 beta 1

;Language: Turkish (1055)
;By Matthias <bodenseematze@users.sourceforge.net> (copied from English and translated)
;--------------------------------

!ifdef UMUI_MULTILANGUAGEPAGE
  ${LangFileString} UMUI_TEXT_MULTILANGUAGE_TITLE "Kurulum asistanýna $(^NameDA) hoþ geldiniz"
  ${LangFileString} UMUI_TEXT_MULTILANGUAGE_TEXT "Kurulumdan önce lütfen $(^NameDA) içerisinden bir dil seçin:$\r$\n$\r$\n$_CLICK"
!endif

!ifdef UMUI_UNMULTILANGUAGEPAGE
  ${LangFileString} UMUI_UNTEXT_MULTILANGUAGE_TITLE "Program kaldýrma asistanýna $(^NameDA) hoþ geldiniz"
  ${LangFileString} UMUI_UNTEXT_MULTILANGUAGE_TEXT "Programý kaldýrmadan önce lütfen $(^NameDA) içerisinden bir dil seçin:$\r$\n$\r$\n$_CLICK"
!endif

!ifdef UMUI_MULTILANGUAGEPAGE | UMUI_UNMULTILANGUAGEPAGE
  ${LangFileString} UMUI_TEXT_MULTILANGUAGE_LANGUAGE "Dil:"
!endif


!ifdef MUI_WELCOMEPAGE
  ${LangFileString} UMUI_TEXT_WELCOME_ALTERNATIVEINFO_TEXT "Bu asistan sizi $(^NameDA) ait olan kuruluma götürecektir.$\r$\n$\r$\n$\r$\n$_CLICK"
!endif


!ifdef UMUI_SERIALNUMBERPAGE | UMUI_UNSERIALNUMBERPAGE
  ${LangFileString} UMUI_TEXT_SERIALNUMBER_TITLE "Lütfen $(^NameDA) ait olan seri numarasýný girin"
  ${LangFileString} UMUI_TEXT_SERIALNUMBER_SUBTITLE "Lütfen deðiþik alanlarý doldurun."
  ${LangFileString} UMUI_TEXT_SERIALNUMBER_INFO_TEXT "Lütfen deðiþik alanlarý doldurun. $_CLICK"
  ${LangFileString} UMUI_TEXT_SERIALNUMBER_INVALIDATE_TEXT "$UMUI_SNTEXT geçersiz. Lütfen girilen bilgilerinizi kontrol edin."
  ${LangFileString} UMUI_TEXT_SERIALNUMBER_NAME "Ýsim"
  ${LangFileString} UMUI_TEXT_SERIALNUMBER_ORGANIZATION "Organizasyon"
  ${LangFileString} UMUI_TEXT_SERIALNUMBER_SERIALNUMBER "Seri numarasý"
  ${LangFileString} UMUI_TEXT_SERIALNUMBER_ACTIVATIONCODE "Aktifleþtirme kodu"
  ${LangFileString} UMUI_TEXT_SERIALNUMBER_PASSWORD "Þifre"
!endif


!ifdef UMUI_CONFIRMPAGE
  ${LangFileString} UMUI_TEXT_INSTCONFIRM_SUBTITLE "Kurulum gerekli bilgileri topladý ve $(^NameDA) kurulum için hazýr."
  ${LangFileString} UMUI_TEXT_INSTCONFIRM_TITLE "Kurulumu onayla"
  ${LangFileString} UMUI_TEXT_INSTCONFIRM_TEXT_TOP "Kurulum, $(^NameDA) bilgisayarýnýza kurulmak için hazýr.$\r$\nEðer kurulum ayarlarýnýzý kontrol etmek veya deðiþtirmek istiyorsanýz, geriye basýn. Kurulumu baþlatmak için devama basýn. $_CLICK"
!endif 

!ifdef UMUI_UNCONFIRMPAGE
  ${LangFileString} UMUI_UNTEXT_INSTCONFIRM_SUBTITLE "Kurulum gerekli bilgileri topladý ve $(^NameDA) program kaldýrma için hazýr."
  ${LangFileString} UMUI_UNTEXT_INSTCONFIRM_TITLE "Program kaldýrmayý onayla"
  ${LangFileString} UMUI_UNTEXT_INSTCONFIRM_TEXT_TOP "Setup Kurulum, $(^NameDA) bilgisayarýnýzdan programý kaldýrmak için hazýr.$\r$\nEðer program kaldýrma ayarlarýnýzý kontrol etmek veya deðiþtirmek istiyorsanýz, geriye basýn. Program kaldýrma iþlemine baþlamak için devama basýn."
!endif 

!ifdef UMUI_CONFIRMPAGE | UMUI_UNCONFIRMPAGE
  ${LangFileString} UMUI_TEXT_INSTCONFIRM_TEXTBOX_TITLE "Þimdiki konfigürasyon:"
  ${LangFileString} UMUI_TEXT_INSTCONFIRM_TEXTBOX_DESTINATION_LOCATION "Hedef yer:"
  ${LangFileString} UMUI_TEXT_INSTCONFIRM_TEXTBOX_START_MENU_FOLDER "Baþlangýç menüsü düzenleyicisi:"
  ${LangFileString} UMUI_TEXT_INSTCONFIRM_TEXTBOX_COMPNENTS "Takip eden bileþenler kuruluyor:"
!endif 


!ifdef UMUI_ABORTPAGE
  ${LangFileString} UMUI_TEXT_ABORT_INFO_TITLE "Kurulum asistanýnýn $(^NameDA) sonlandýrýlmasý"
  ${LangFileString} UMUI_TEXT_ABORT_INFO_TEXT "Asistan $(^NameDA) komple kurulabilene kadar iptal edildi.$\r$\n$\r$\nProgramý ileriki bir zamanda kurabilmek için bu kurulumu yeniden yürütün.$\r$\n$\r$\n$\r$\n$\r$\nKurulum asistanýný kapatmak için $(^CloseBtn) üzerine basýn."
!endif 

!ifdef UMUI_UNABORTPAGE
  ${LangFileString} UMUI_UNTEXT_ABORT_INFO_TITLE "$(^NameDA) için program kaldýrma asistanýný sonlandýrýn"
  ${LangFileString} UMUI_UNTEXT_ABORT_INFO_TEXT "Asistan $(^NameDA) komple program kaldýrýlana kadar iptal edildi.$\r$\n$\r$\nProgramý ileriki bir zamanda kaldýrabilmek için bu kurulumu yeniden yürütün.$\r$\n$\r$\n$\r$\n$\r$\nProgram kaldýrma asistanýný kapatmak için $(^CloseBtn) üzerine basýn."
!endif 


!ifdef UMUI_SETUPTYPEPAGE
  ${LangFileString} UMUI_TEXT_SETUPTYPE_TITLE "Kurulum tipi"
  ${LangFileString} UMUI_TEXT_SETUPTYPE_SUBTITLE "Sizin için en iyi kurulum tipini seçin."
  ${LangFileString} UMUI_TEXT_SETUPTYPE_INFO_TEXT "Lütfen bir kurulum tipini seçin."
  ${LangFileString} UMUI_TEXT_SETUPTYPE_MINIMAL_TEXT "Sadece gerekli fonksiyonlarýn kurulumu yapýlýr. (en az hafýza yerine ihtiyaç duyar)"
  ${LangFileString} UMUI_TEXT_SETUPTYPE_STANDARD_TEXT "Tüm ana fonksiyonlar kurulur. Çoðu kullanýcý için önerilir."
  ${LangFileString} UMUI_TEXT_SETUPTYPE_COMPLETE_TEXT "Tüm program fonksiyonlarý kurulur. (en çok hafýza yerine ihtiyaç duyar)"
  ${LangFileString} UMUI_TEXT_SETUPTYPE_CUSTOM_TEXT "Lütfen hangi program fonksiyonelliðini nereye kurmak istediðinizi seçin. Ýleri düzeydeki kullanýcýlara önerilir."
!endif 

!ifdef UMUI_UNSETUPTYPEPAGE
  ${LangFileString} UMUI_UNTEXT_SETUPTYPE_TITLE "Program kaldýrma tipi"
  ${LangFileString} UMUI_UNTEXT_SETUPTYPE_SUBTITLE "Sizin için en iyi program kaldýrma tipini seçin."
  ${LangFileString} UMUI_UNTEXT_SETUPTYPE_INFO_TEXT "Lütfen bir program kaldýrma tipini seçin."
  ${LangFileString} UMUI_UNTEXT_SETUPTYPE_MINIMAL_TEXT "Sadece ana fonksiyonlar saklý tutulur."
  ${LangFileString} UMUI_UNTEXT_SETUPTYPE_STANDARD_TEXT "Sadece en önemli fonksiyonlar saklý tutulur."
  ${LangFileString} UMUI_UNTEXT_SETUPTYPE_COMPLETE_TEXT "Tüm program saklý tutulur."
  ${LangFileString} UMUI_UNTEXT_SETUPTYPE_CUSTOM_TEXT "Lütfen hangi program fonksiyonelliðini kaldýrmak istediðinizi seçin."
!endif 

!ifdef UMUI_SETUPTYPEPAGE | UMUI_UNSETUPTYPEPAGE
  ${LangFileString} UMUI_TEXT_SETUPTYPE_MINIMAL_TITLE "Minimum"
  ${LangFileString} UMUI_TEXT_SETUPTYPE_STANDARD_TITLE "Standart"
  ${LangFileString} UMUI_TEXT_SETUPTYPE_COMPLETE_TITLE "Komple"
  ${LangFileString} UMUI_TEXT_SETUPTYPE_CUSTOM_TITLE "Kullanýcý tanýmlý"
!endif 


!ifdef UMUI_INFORMATIONPAGE
  ${LangFileString} UMUI_TEXT_INFORMATION_SUBTITLE "Lütfen $(^NameDA) ait olan kurulum hakkýndaki bilgilere dikkat edin."
!endif 

!ifdef UMUI_UNINFORMATIONPAGE
  ${LangFileString} UMUI_UNTEXT_INFORMATION_SUBTITLE "Lütfen $(^NameDA) ait olan program kaldýrma hakkýndaki bilgilere dikkat edin."
!endif 

!ifdef UMUI_INFORMATIONPAGE | UMUI_UNINFORMATIONPAGE
  ${LangFileString} UMUI_TEXT_INFORMATION_TITLE "Bilgi"
  ${LangFileString} UMUI_TEXT_INFORMATION_INFO_TEXT "$(^NameDA) hakkýndaki bilgiler."
!endif 


!ifdef UMUI_ADDITIONALTASKSPAGE
  ${LangFileString} UMUI_TEXT_ADDITIONALTASKS_INFO_TEXT "Kurulumu, $(^NameDA) ait kurulum prosesi sýrasýnda yürütecek olan ilave aksiyonlarý seçin. $_CLICK"
!endif 

!ifdef UMUI_UNADDITIONALTASKSPAGE
  ${LangFileString} UMUI_UNTEXT_ADDITIONALTASKS_INFO_TEXT "Kurulumu, $(^NameDA) ait program kaldýrma prosesi sýrasýnda yürütecek olan ilave aksiyonlarý seçin. $_CLICK"
!endif 

!ifdef UMUI_ADDITIONALTASKSPAGE | UMUI_UNADDITIONALTASKSPAGE
  ${LangFileString} UMUI_TEXT_ADDITIONALTASKS_TITLE "Ýlave aksiyonlar"
  ${LangFileString} UMUI_TEXT_ADDITIONALTASKS_SUBTITLE "Ýlave hangi aksiyonlarýn yürütülmesi gerekiyor?"
  ${LangFileString} UMUI_TEXT_ADDITIONALTASKS_ADDITIONAL_ICONS "Ýlave ikonlar:"
  ${LangFileString} UMUI_TEXT_ADDITIONALTASKS_CREATE_DESKTOP_ICON "Masaüstünde bir ikon oluþtur"
  ${LangFileString} UMUI_TEXT_ADDITIONALTASKS_CREATE_QUICK_LAUNCH_ICON "Hýzlý çalýþtýrma satýrýnda bir ikon oluþtur"
  ${LangFileString} UMUI_TEXT_ADDITIONALTASKS_ADVANCED_PARAMETERS "Ýlerlemiþ parametreler:"
  ${LangFileString} UMUI_TEXT_ADDITIONALTASKS_LAUNCH_PROGRAM_AT_WINDOWS_STARTUP "Bir sistem çalýþtýrmasýndan sonra $(^NameDA) baþlat"
  ${LangFileString} UMUI_TEXT_ADDITIONALTASKS_FILE_ASSOCIATION "Dosya baðlantýlarý:"
  ${LangFileString} UMUI_TEXT_ADDITIONALTASKS_ASSOCIATE_WITH "Dosya tipi ile "
  ${LangFileString} UMUI_TEXT_ADDITIONALTASKS_ASSOCIATE_WITH_END " $(^NameDA) baðlantý yap"
!endif 
  
  
!ifdef UMUI_CONFIRMPAGE | UMUI_UNCONFIRMPAGE | UMUI_ALTERNATIVESTARTMENUPAGE | UMUI_UNALTERNATIVESTARTMENUPAGE
  ${LangFileString} UMUI_TEXT_SHELL_VAR_CONTEXT "Baðlantýlar kimin için oluþturulsun:"
  ${LangFileString} UMUI_TEXT_SHELL_VAR_CONTEXT_FOR_ALL_USERS "Tüm kullanýcýlar için"
  ${LangFileString} UMUI_TEXT_SHELL_VAR_CONTEXT_ONLY_FOR_CURRENT_USER "Sadece kayýtlý kullanýcýlar için"
!endif


!ifdef UMUI_UPDATEPAGE
  ${LangFileString} UMUI_TEXT_UPDATE_TITLE "Güncelle"
  ${LangFileString} UMUI_TEXT_UPDATE_SUBTITLE "Programýn daha önceki bir versiyonu için güncelleme."
  ${LangFileString} UMUI_TEXT_UPDATE_INFO_TEXT "Güncelleme asistanýna $(^NameDA) hoþ geldiniz.$\r$\nBu program, bilgisayarýnýzda bulunan $OLDVERSION versiyonunun güncellemesini yapar."
  ${LangFileString} UMUI_TEXT_UPDATE_UPDATE_TITLE "Güncelle"
  ${LangFileString} UMUI_TEXT_UPDATE_UPDATE_TEXT "$NEWVERSION versiyonundaki önceden kurulmuþ bileþenlerin tüm $(^NameDA) güncellemesi.."
  ${LangFileString} UMUI_TEXT_UPDATE_REMOVE_TITLE "Kaldýr"
  ${LangFileString} UMUI_TEXT_UPDATE_REMOVE_TEXT "Bilgisayarýnýzdan $OLDVERSION versiyonunun program kaldýrma."
  ${LangFileString} UMUI_TEXT_UPDATE_CONTINUE_TITLE "Kuruluma devam et"
  ${LangFileString} UMUI_TEXT_UPDATE_CONTINUE_TEXT "Kuruluma önceki gibi devam edin. Bu opsiyonu, eðer daha yeni bir versiyonu, eski versiyondan farklý bir dizine kurmak istiyorsanýz kullanýn."
!endif


!ifdef UMUI_MAINTENANCEPAGE | UMUI_UNMAINTENANCEPAGE
  ${LangFileString} UMUI_TEXT_MAINTENANCE_TITLE "Yönetim"
  ${LangFileString} UMUI_TEXT_MAINTENANCE_SUBTITLE "Programýn deðiþtirilmesi, onarýlmasý veya kaldýrýlmasý."
  ${LangFileString} UMUI_TEXT_MAINTENANCE_INFO_TEXT "Yönetim programýna $(^NameDA) hoþ geldiniz.$\r$\nBu program ile güncel kurulumunuzu deðiþtirebilirsiniz."
  ${LangFileString} UMUI_TEXT_MAINTENANCE_MODIFY_TITLE "Deðiþtir"
  ${LangFileString} UMUI_TEXT_MAINTENANCE_MODIFY_TEXT "Yeni bileþenleri, bunlarý kurmak veya önceden mevcut olanlarýn programýný kaldýrmak için seçin."
  ${LangFileString} UMUI_TEXT_MAINTENANCE_REPAIR_TITLE "Onar"
  ${LangFileString} UMUI_TEXT_MAINTENANCE_REPAIR_TEXT "Önceden kurulumu yapýlmýþ bileþenlerin $(^NameDA) yeniden kurulumu."
  ${LangFileString} UMUI_TEXT_MAINTENANCE_REMOVE_TITLE "Kaldýr"
  ${LangFileString} UMUI_TEXT_MAINTENANCE_REMOVE_TEXT "Bilgisayarýnýzdan $(^NameDA) program kaldýrma."
  ${LangFileString} UMUI_TEXT_MAINTENANCE_CONTINUE_TITLE "Kuruluma devam et"
  ${LangFileString} UMUI_TEXT_MAINTENANCE_CONTINUE_TEXT "Kuruluma önceki gibi devam edin. Bu opsiyonu, eðer programý mevcut bir kurulum üzerinden kurmak istiyorsanýz veya baþka bir dizinde yeni bir kurulum yürütmek istiyorsanýz kullanýn."
!endif


!ifdef UMUI_FILEDISKREQUESTPAGE | UMUI_UNFILEDISKREQUESTPAGE
  ${LangFileString} UMUI_TEXT_FILEDISKREQUEST_FILE_SUBTITLE_BEGIN "Kurulum devam edebilmek için "
  ${LangFileString} UMUI_TEXT_FILEDISKREQUEST_FILE_SUBTITLE_END "dosyaya ihtiyaç duyuyor."
  ${LangFileString} UMUI_TEXT_FILEDISKREQUEST_DISK_SUBTITLE "Kurulum devam edebilmek için bir sonraki veri taþýyýcýsýna gerek duyuyor."
  ${LangFileString} UMUI_TEXT_FILEDISKREQUEST_FILE_BEGIN "Devam edebilmek için"
  ${LangFileString} UMUI_TEXT_FILEDISKREQUEST_FILE_END "dosyanýn kaydedileceði hafýza yerini seçin."
  ${LangFileString} UMUI_TEXT_FILEDISKREQUEST_DISK "Lütfen"
  ${LangFileString} UMUI_TEXT_FILEDISKREQUEST_PATH "yolu girin:"
!endif
