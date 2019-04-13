;NSIS Modern User Interface - Language File
;Compatible with UltraModernUI 2.0 beta 1

;Language: Brazilian Portuguese (1046)
;By Jenner Modesto <jennermodesto@gmail.com>
;--------------------------------

!ifdef UMUI_CONFIRMPAGE
  ${LangFileString} UMUI_TEXT_INSTCONFIRM_SUBTITLE "O Assistente terminou de reunir informações e está pronto para instalar $(^NameDA)."
  ${LangFileString} UMUI_TEXT_INSTCONFIRM_TITLE "Confirmar a Instalação"
  ${LangFileString} UMUI_TEXT_INSTCONFIRM_TEXT_TOP "O Assistente está pronto para instalar $(^NameDA) em seu computador.$\r$\nSe quiser rever ou mudar quaisquer configurações da instalação, clique em Voltar. $_CLICK"
!endif

!ifdef UMUI_UNCONFIRMPAGE
  ${LangFileString} UMUI_UNTEXT_INSTCONFIRM_SUBTITLE "O Assistente terminou de reunir informações e está pronto para instalar $(^NameDA)."
  ${LangFileString} UMUI_UNTEXT_INSTCONFIRM_TITLE "Confirmar a desinstalação"
  ${LangFileString} UMUI_UNTEXT_INSTCONFIRM_TEXT_TOP "O Assistente está pronto para desinstalar $(^NameDA) em seu computador.$\r$\nSe quiser rever ou mudar quaisquer configurações da desinstalação, clique em Voltar. Clique em Avançar para iniciar a desinstalação."
!endif

!ifdef UMUI_CONFIRMPAGE | UMUI_UNCONFIRMPAGE
  ${LangFileString} UMUI_TEXT_INSTCONFIRM_TEXTBOX_TITLE "Configuração atual:"
  ${LangFileString} UMUI_TEXT_INSTCONFIRM_TEXTBOX_DESTINATION_LOCATION "Diretório de instalação:"
  ${LangFileString} UMUI_TEXT_INSTCONFIRM_TEXTBOX_START_MENU_FOLDER "Menu iniciar:"
!endif


!ifdef UMUI_ABORTPAGE
  ${LangFileString} UMUI_TEXT_ABORT_INFO_TITLE "Terminando o Assistente de Instalação de $(^NameDA)"
  ${LangFileString} UMUI_TEXT_ABORT_INFO_TEXT "O Assistente foi interrompido antes que $(^Name) pudesse ser totalmente instalado.$\r$\n$\r$\nPara instalar esse programa mais tarde, execute o assistente novamente.$\r$\n$\r$\n$\r$\n$\r$\nClique em $(^CloseBtn) para sair do Assistente."
!endif

!ifdef UMUI_UNABORTPAGE
  ${LangFileString} UMUI_UNTEXT_ABORT_INFO_TITLE "Terminando o Assistente de Desinstalação de $(^NameDA)"
  ${LangFileString} UMUI_UNTEXT_ABORT_INFO_TEXT "O Assistente foi interrompido antes que $(^Name) pudesse ser totalmente desinstalado.$\r$\n$\r$\nPara desinstalar esse programa mais tarde, execute o assistente novamente.$\r$\n$\r$\n$\r$\n$\r$\nClique em $(^CloseBtn) para sair do Assistente."
!endif
