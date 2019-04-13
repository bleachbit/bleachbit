;NSIS Modern User Interface - Language File
;Compatible with UltraModernUI 2.0 beta 1

;Language: Japanese (1041)
;By Logue <http://logue.be/>
;modified 2009/06/23
;--------------------------------

!ifdef UMUI_MULTILANGUAGEPAGE
  ${LangFileString} UMUI_TEXT_MULTILANGUAGE_TITLE "$(^NameDA) のセットアップへようこそ"
  ${LangFileString} UMUI_TEXT_MULTILANGUAGE_TEXT "$(^NameDA) をインストールする前に言語を選択してください：$\r$\n$\r$\n$_CLICK"
!endif

!ifdef UMUI_UNMULTILANGUAGEPAGE
  ${LangFileString} UMUI_UNTEXT_MULTILANGUAGE_TITLE "$(^NameDA) のアンインストールウィザードへようこそ"
  ${LangFileString} UMUI_UNTEXT_MULTILANGUAGE_TEXT "$(^NameDA) をアンインストールする前に言語を選択してください：$\r$\n$\r$\n$_CLICK"
!endif

!ifdef UMUI_MULTILANGUAGEPAGE | UMUI_UNMULTILANGUAGEPAGE
  ${LangFileString} UMUI_TEXT_MULTILANGUAGE_LANGUAGE "言語："
!endif


!ifdef MUI_WELCOMEPAGE
  ${LangFileString} UMUI_TEXT_WELCOME_ALTERNATIVEINFO_TEXT "このウィザードは、 $(^NameDA) をインストールする上でのガイドを行います。$\r$\n$\r$\n$\r$\n$_CLICK"
!endif


!ifdef UMUI_SERIALNUMBERPAGE | UMUI_UNSERIALNUMBERPAGE
  ${LangFileString} UMUI_TEXT_SERIALNUMBER_TITLE "$(^NameDA) のシリアルナンバーを入力してください。"
  ${LangFileString} UMUI_TEXT_SERIALNUMBER_SUBTITLE "以下の項目を入力してください。"
  ${LangFileString} UMUI_TEXT_SERIALNUMBER_INFO_TEXT "以下の項目を入力してください。$_CLICK"
  ${LangFileString} UMUI_TEXT_SERIALNUMBER_INVALIDATE_TEXT "$UMUI_SNTEXTの値が不正です。お手数ですが入力内容をご確認ください。"
  ${LangFileString} UMUI_TEXT_SERIALNUMBER_NAME "名前"
  ${LangFileString} UMUI_TEXT_SERIALNUMBER_ORGANIZATION "所属"
  ${LangFileString} UMUI_TEXT_SERIALNUMBER_SERIALNUMBER "シリアルナンバー"
  ${LangFileString} UMUI_TEXT_SERIALNUMBER_ACTIVATIONCODE "アクティベーションコード"
  ${LangFileString} UMUI_TEXT_SERIALNUMBER_PASSWORD "パスワード"
!endif


!ifdef UMUI_CONFIRMPAGE
  ${LangFileString} UMUI_TEXT_INSTCONFIRM_SUBTITLE "セットアップは、 $(^NameDA) をインストールする上での必要な情報の収集および、準備が完了しました。"
  ${LangFileString} UMUI_TEXT_INSTCONFIRM_TITLE "インストールの確認"
  ${LangFileString} UMUI_TEXT_INSTCONFIRM_TEXT_TOP "セットアップは、あなたのコンピューターへ $(^NameDA) をインストールする準備ができました。$\r$\nもしも、インストール設定を変更する必要がある場合は、「戻る」ボタンを押してください。$_CLICK"
!endif

!ifdef UMUI_UNCONFIRMPAGE
  ${LangFileString} UMUI_UNTEXT_INSTCONFIRM_SUBTITLE "セットアップは、 $(^NameDA) をアンインストールする上での必要な情報の収集および、準備が完了しました。"
  ${LangFileString} UMUI_UNTEXT_INSTCONFIRM_TITLE "アンインストールの確認"
  ${LangFileString} UMUI_UNTEXT_INSTCONFIRM_TEXT_TOP "セットアップは、あなたのコンピューターから $(^NameDA) をアンインストールする準備ができました。$\r$\nもしも、アンインストール設定を変更する必要がある場合は、「戻る」ボタンを押してください。「次へ」ボタンをクリックするとアンインストールを開始します。"
!endif

!ifdef UMUI_CONFIRMPAGE | UMUI_UNCONFIRMPAGE
  ${LangFileString} UMUI_TEXT_INSTCONFIRM_TEXTBOX_TITLE "現在の設定："
  ${LangFileString} UMUI_TEXT_INSTCONFIRM_TEXTBOX_DESTINATION_LOCATION "インストール先："
  ${LangFileString} UMUI_TEXT_INSTCONFIRM_TEXTBOX_START_MENU_FOLDER "スタートメニューフォルダ："
  ${LangFileString} UMUI_TEXT_INSTCONFIRM_TEXTBOX_COMPNENTS "インストールされるコンポーネント："
!endif


!ifdef UMUI_ABORTPAGE
  ${LangFileString} UMUI_TEXT_ABORT_INFO_TITLE "$(^NameDA) セットアップウィザードの中断"
  ${LangFileString} UMUI_TEXT_ABORT_INFO_TEXT "ウィザードは、 $(^NameDA) のインストール作業を中断しました。$\r$\n$\r$\nこのプログラムをインストールするためには、あとでセットアップを再実行する必要があります。$\r$\n$\r$\n$\r$\n$\r$\n「$(^CloseBtn)」ボタンを押すとセットアップウィザードを終了します。"
!endif

!ifdef UMUI_UNABORTPAGE
  ${LangFileString} UMUI_UNTEXT_ABORT_INFO_TITLE "$(^NameDA) アンインストールウィザードの中断"
  ${LangFileString} UMUI_UNTEXT_ABORT_INFO_TEXT "ウィザードは、 $(^NameDA) のアンインストール作業を中断しました。$\r$\n$\r$\nこのプログラムをアンインストールするためには、あとでアンインストールを再実行する必要があります。$\r$\n$\r$\n$\r$\n$\r$\n「$(^CloseBtn)」ボタンを押すとアンインストールウィザードを終了します。"
!endif


!ifdef UMUI_SETUPTYPEPAGE
  ${LangFileString} UMUI_TEXT_SETUPTYPE_TITLE "セットアップタイプ"
  ${LangFileString} UMUI_TEXT_SETUPTYPE_SUBTITLE "必要な項目を選択してください。"
  ${LangFileString} UMUI_TEXT_SETUPTYPE_INFO_TEXT "セットアップタイプを選択してください。"
  ${LangFileString} UMUI_TEXT_SETUPTYPE_MINIMAL_TEXT "最低限必要な機能のみ（ディスク消費量が最小限です）"
  ${LangFileString} UMUI_TEXT_SETUPTYPE_STANDARD_TEXT "メインとなる機能がインストールされます。多くのユーザに推奨されます。"
  ${LangFileString} UMUI_TEXT_SETUPTYPE_COMPLETE_TEXT "すべての機能がインストールされます。（ディスクの消費量が最大です）"
  ${LangFileString} UMUI_TEXT_SETUPTYPE_CUSTOM_TEXT "プログラムに必要な機能を自分で選択できます。上級ユーザ推奨です。"
!endif

!ifdef UMUI_UNSETUPTYPEPAGE
  ${LangFileString} UMUI_UNTEXT_SETUPTYPE_TITLE "アンインストールタイプ"
  ${LangFileString} UMUI_UNTEXT_SETUPTYPE_SUBTITLE "アンインストールしたい項目を選択してください。"
  ${LangFileString} UMUI_UNTEXT_SETUPTYPE_INFO_TEXT "アンインストールタイプを選択してください。"
  ${LangFileString} UMUI_UNTEXT_SETUPTYPE_MINIMAL_TEXT "メインとなる機能は残ります。"
  ${LangFileString} UMUI_UNTEXT_SETUPTYPE_STANDARD_TEXT "必要な機能は残ります。"
  ${LangFileString} UMUI_UNTEXT_SETUPTYPE_COMPLETE_TEXT "すべてのプログラムをアンインストールします。"
  ${LangFileString} UMUI_UNTEXT_SETUPTYPE_CUSTOM_TEXT "アンインストールする機能を自分で選択します。"
!endif

!ifdef UMUI_SETUPTYPEPAGE | UMUI_UNSETUPTYPEPAGE
  ${LangFileString} UMUI_TEXT_SETUPTYPE_MINIMAL_TITLE "最小限"
  ${LangFileString} UMUI_TEXT_SETUPTYPE_STANDARD_TITLE "一般"
  ${LangFileString} UMUI_TEXT_SETUPTYPE_COMPLETE_TITLE "完全"
  ${LangFileString} UMUI_TEXT_SETUPTYPE_CUSTOM_TITLE "カスタム"
!endif


!ifdef UMUI_INFORMATIONPAGE
  ${LangFileString} UMUI_TEXT_INFORMATION_SUBTITLE "$(^NameDA) をインストールする上での関連情報をご確認ください。"
!endif

!ifdef UMUI_UNINFORMATIONPAGE
  ${LangFileString} UMUI_UNTEXT_INFORMATION_SUBTITLE "$(^NameDA) をアンインストールする上での関連情報をご確認ください。"
!endif

!ifdef UMUI_INFORMATIONPAGE | UMUI_UNINFORMATIONPAGE
  ${LangFileString} UMUI_TEXT_INFORMATION_TITLE "情報"
  ${LangFileString} UMUI_TEXT_INFORMATION_INFO_TEXT "$(^NameDA) の関連情報です。"
!endif


!ifdef UMUI_ADDITIONALTASKSPAGE
  ${LangFileString} UMUI_TEXT_ADDITIONALTASKS_INFO_TEXT "$(^NameDA) のセットアップ作業時に行いたい追加のタスクを選択してください。$_CLICK"
!endif

!ifdef UMUI_UNADDITIONALTASKSPAGE
  ${LangFileString} UMUI_UNTEXT_ADDITIONALTASKS_INFO_TEXT "$(^NameDA) のアンストール作業時に行いたい追加のタスクを選択してください$_CLICK"
!endif

!ifdef UMUI_ADDITIONALTASKSPAGE | UMUI_UNADDITIONALTASKSPAGE
  ${LangFileString} UMUI_TEXT_ADDITIONALTASKS_TITLE "追加する作業"
  ${LangFileString} UMUI_TEXT_ADDITIONALTASKS_SUBTITLE "追加のタスクを選択してください。"
  ${LangFileString} UMUI_TEXT_ADDITIONALTASKS_ADDITIONAL_ICONS "拡張アイコン："
  ${LangFileString} UMUI_TEXT_ADDITIONALTASKS_CREATE_DESKTOP_ICON "ディスクトップに作成"
  ${LangFileString} UMUI_TEXT_ADDITIONALTASKS_CREATE_QUICK_LAUNCH_ICON "クイック起動に作成"
  ${LangFileString} UMUI_TEXT_ADDITIONALTASKS_ADVANCED_PARAMETERS "拡張パラメーター："
  ${LangFileString} UMUI_TEXT_ADDITIONALTASKS_LAUNCH_PROGRAM_AT_WINDOWS_STARTUP "Windowsのスタートアップ時に実行する $(^NameDA)"
  ${LangFileString} UMUI_TEXT_ADDITIONALTASKS_FILE_ASSOCIATION "ファイルの関連づけ："
  ${LangFileString} UMUI_TEXT_ADDITIONALTASKS_ASSOCIATE_WITH "$(^NameDA) と関連づけるファイルタイプ "
  ${LangFileString} UMUI_TEXT_ADDITIONALTASKS_ASSOCIATE_WITH_END " "
!endif
  
  
!ifdef UMUI_CONFIRMPAGE | UMUI_UNCONFIRMPAGE | UMUI_ALTERNATIVESTARTMENUPAGE | UMUI_UNALTERNATIVESTARTMENUPAGE
  ${LangFileString} UMUI_TEXT_SHELL_VAR_CONTEXT "作成するショートカット："
  ${LangFileString} UMUI_TEXT_SHELL_VAR_CONTEXT_FOR_ALL_USERS "すべてのユーザ"
  ${LangFileString} UMUI_TEXT_SHELL_VAR_CONTEXT_ONLY_FOR_CURRENT_USER "現在のユーザのみ"
!endif


!ifdef UMUI_UPDATEPAGE
  ${LangFileString} UMUI_TEXT_UPDATE_TITLE "アップデート"
  ${LangFileString} UMUI_TEXT_UPDATE_SUBTITLE "前のバージョンのプログラムをアップデートします。"
  ${LangFileString} UMUI_TEXT_UPDATE_INFO_TEXT "$(^NameDA) アップデートウィザードへようこそ。$\r$\nこのプログラムは、コンピューターにインストールされている$OLDVERSIONをアップデートします。"
  ${LangFileString} UMUI_TEXT_UPDATE_UPDATE_TITLE "アップデート"
  ${LangFileString} UMUI_TEXT_UPDATE_UPDATE_TEXT "インストールされている全ての $(^NameDA) のコンポーネントを$NEWVERSIONにアップデートしています…"
  ${LangFileString} UMUI_TEXT_UPDATE_REMOVE_TITLE "削除"
  ${LangFileString} UMUI_TEXT_UPDATE_REMOVE_TEXT "$(^NameDA) をあなたのコンピューターからアンインストールします。"
  ${LangFileString} UMUI_TEXT_UPDATE_CONTINUE_TITLE "セットアップ続行"
  ${LangFileString} UMUI_TEXT_UPDATE_CONTINUE_TEXT "通常通りセットアップを続行してください。このオプションは、新しいバージョンのプログラムにアップデートしたり、別のフォルダにインストールしたい場合使用します。"
!endif


!ifdef UMUI_MAINTENANCEPAGE | UMUI_UNMAINTENANCEPAGE
  ${LangFileString} UMUI_TEXT_MAINTENANCE_TITLE "メンテナンス"
  ${LangFileString} UMUI_TEXT_MAINTENANCE_SUBTITLE "プログラムを変更、修正または削除します。"
  ${LangFileString} UMUI_TEXT_MAINTENANCE_INFO_TEXT "$(^NameDA) セットアップメンテナンスプログラムへようこそ。$\r$\nこのプログラムは、現在のインストールを修正することができます。"
  ${LangFileString} UMUI_TEXT_MAINTENANCE_MODIFY_TITLE "変更"
  ${LangFileString} UMUI_TEXT_MAINTENANCE_MODIFY_TEXT "新しいコンポーネントを追加したり、インストールされている項目を削除したりすることができます。"
  ${LangFileString} UMUI_TEXT_MAINTENANCE_REPAIR_TITLE "修復"
  ${LangFileString} UMUI_TEXT_MAINTENANCE_REPAIR_TEXT "$(^NameDA) のコンポーネントを再インストールします。"
  ${LangFileString} UMUI_TEXT_MAINTENANCE_REMOVE_TITLE "削除"
  ${LangFileString} UMUI_TEXT_MAINTENANCE_REMOVE_TEXT "$(^NameDA) をアンインストールします"
  ${LangFileString} UMUI_TEXT_MAINTENANCE_CONTINUE_TITLE "セットアップ続行"
  ${LangFileString} UMUI_TEXT_MAINTENANCE_CONTINUE_TEXT "通常通りセットアップを続行してください。このオプションは、既存のプログラムを再インストールしたり、異なるフォルダにインストールしたい場合使用します。"
!endif


!ifdef UMUI_FILEDISKREQUESTPAGE | UMUI_UNFILEDISKREQUESTPAGE
  ${LangFileString} UMUI_TEXT_FILEDISKREQUEST_FILE_SUBTITLE_BEGIN "セットアップを続行するには、"
  ${LangFileString} UMUI_TEXT_FILEDISKREQUEST_FILE_SUBTITLE_END "ファイルが必要です。"
  ${LangFileString} UMUI_TEXT_FILEDISKREQUEST_DISK_SUBTITLE "セットアップを続行するには、次のディスクを挿入してください。"
  ${LangFileString} UMUI_TEXT_FILEDISKREQUEST_FILE_BEGIN "続けるには、"
  ${LangFileString} UMUI_TEXT_FILEDISKREQUEST_FILE_END "ファイルを指定してください。"
  ${LangFileString} UMUI_TEXT_FILEDISKREQUEST_DISK ""
  ${LangFileString} UMUI_TEXT_FILEDISKREQUEST_PATH "のパスを入力してください："
!endif
