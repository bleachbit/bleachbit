;NSIS Modern User Interface - Language File
;Compatible with UltraModernUI 2.0 beta 1

;Language: Greek (1032)
;By Matthias <bodenseematze@users.sourceforge.net> (copied from English and translated)
;--------------------------------

!ifdef UMUI_MULTILANGUAGEPAGE
  ${LangFileString} UMUI_TEXT_MULTILANGUAGE_TITLE "Καλωσορίσατε στον οδηγό εγκατάστασης $(^NameDA)"
  ${LangFileString} UMUI_TEXT_MULTILANGUAGE_TEXT "Πριν από την εγκατάσταση του $(^NameDA) επιλέξτε μία γλώσσα:$\r$\n$\r$\n$_CLICK"
!endif

!ifdef UMUI_UNMULTILANGUAGEPAGE
  ${LangFileString} UMUI_UNTEXT_MULTILANGUAGE_TITLE "Καλωσορίσατε στον οδηγό απεγκατάστασης $(^NameDA)"
  ${LangFileString} UMUI_UNTEXT_MULTILANGUAGE_TEXT "Πριν από την απεγκατάσταση του $(^NameDA) επιλέξτε μία γλώσσα:$\r$\n$\r$\n$_CLICK"
!endif

!ifdef UMUI_MULTILANGUAGEPAGE | UMUI_UNMULTILANGUAGEPAGE
  ${LangFileString} UMUI_TEXT_MULTILANGUAGE_LANGUAGE "Γλώσσα:"
!endif


!ifdef MUI_WELCOMEPAGE
  ${LangFileString} UMUI_TEXT_WELCOME_ALTERNATIVEINFO_TEXT "Αυτός ο οδηγός θα σας καθοδηγήσει μέσω της εγκατάστασης του $(^NameDA).$\r$\n$\r$\n$\r$\n$_CLICK"
!endif


!ifdef UMUI_SERIALNUMBERPAGE | UMUI_UNSERIALNUMBERPAGE
  ${LangFileString} UMUI_TEXT_SERIALNUMBER_TITLE "Εισαγάγετε το σειριακό αριθμό για το $(^NameDA)"
  ${LangFileString} UMUI_TEXT_SERIALNUMBER_SUBTITLE "Συμπληρώστε τα διάφορα πεδία."
  ${LangFileString} UMUI_TEXT_SERIALNUMBER_INFO_TEXT "Συμπληρώστε τα διάφορα πεδία. $_CLICK"
  ${LangFileString} UMUI_TEXT_SERIALNUMBER_INVALIDATE_TEXT "Η καταχώρηση $UMUI_SNTEXT δεν είναι έγκυρη. Επαληθεύστε τις πληροφορίες που καταχωρήσατε."
  ${LangFileString} UMUI_TEXT_SERIALNUMBER_NAME "Όνομα"
  ${LangFileString} UMUI_TEXT_SERIALNUMBER_ORGANIZATION "Οργανισμός"
  ${LangFileString} UMUI_TEXT_SERIALNUMBER_SERIALNUMBER "Αριθμός σειράς"
  ${LangFileString} UMUI_TEXT_SERIALNUMBER_ACTIVATIONCODE "Κωδικός ενεργοποίησης"
  ${LangFileString} UMUI_TEXT_SERIALNUMBER_PASSWORD "Κωδικός πρόσβασης"
!endif 


!ifdef UMUI_CONFIRMPAGE
  ${LangFileString} UMUI_TEXT_INSTCONFIRM_SUBTITLE "Το πρόγραμμα έχει ολοκληρώσει τη συλλογή των απαραίτητων πληροφοριών και είναι έτοιμο για την εγκατάσταση του $(^NameDA)."
  ${LangFileString} UMUI_TEXT_INSTCONFIRM_TITLE "Επιβεβαίωση εγκατάστασης"
  ${LangFileString} UMUI_TEXT_INSTCONFIRM_TEXT_TOP "Το πρόγραμμα είναι έτοιμο να εγκαταστήσει το $(^NameDA) στον υπολογιστή σας.$\r$\nΑν θέλετε να ελέγξετε πάλι ή να τροποποιήσετε τις ρυθμίσεις εγκατάστασης πατήστε $(^BackBtn). $_CLICK"
!endif 

!ifdef UMUI_UNCONFIRMPAGE
  ${LangFileString} UMUI_UNTEXT_INSTCONFIRM_SUBTITLE "Το πρόγραμμα έχει ολοκληρώσει τη συλλογή των απαραίτητων πληροφοριών και είναι έτοιμο για την απεγκατάσταση του $(^NameDA)."
  ${LangFileString} UMUI_UNTEXT_INSTCONFIRM_TITLE "Επιβεβαίωση της απεγκατάστασης"
  ${LangFileString} UMUI_UNTEXT_INSTCONFIRM_TEXT_TOP "Το πρόγραμμα είναι έτοιμο να καταργήσει το $(^NameDA) από τον υπολογιστή σας.$\r$\nΑν θέλετε να ελέγξετε πάλι ή να τροποποιήσετε τις ρυθμίσεις απεγκατάστασης πατήστε $(^BackBtn). Πατήστε $(^BackBtn) για να ξεκινήσετε την απεγκατάσταση."
!endif 

!ifdef UMUI_CONFIRMPAGE | UMUI_UNCONFIRMPAGE
  ${LangFileString} UMUI_TEXT_INSTCONFIRM_TEXTBOX_TITLE "Τρέχουσα διαμόρφωση:"
  ${LangFileString} UMUI_TEXT_INSTCONFIRM_TEXTBOX_DESTINATION_LOCATION "Τοποθεσία προορισμού:"
  ${LangFileString} UMUI_TEXT_INSTCONFIRM_TEXTBOX_START_MENU_FOLDER "Φάκελος μενού έναρξης:"
  ${LangFileString} UMUI_TEXT_INSTCONFIRM_TEXTBOX_COMPNENTS "Θα εγκατασταθούν τα ακόλουθα στοιχεία:"
!endif 


!ifdef UMUI_ABORTPAGE
  ${LangFileString} UMUI_TEXT_ABORT_INFO_TITLE "Τερματισμός του βοηθού εγκατάστασης $(^NameDA)"
  ${LangFileString} UMUI_TEXT_ABORT_INFO_TEXT "Ο βοηθός εγκατάστασης διακόπηκε πριν την ολοκλήρωση της εγκατάστασης του $(^NameDA).$\r$\n$\r$\nΓια να εγκαταστήσετε το πρόγραμμα σε μεταγενέστερο χρόνο, εκτελέστε ξανά τον οδηγό.$\r$\n$\r$\n$\r$\n$\r$\nΚάντε κλικ στο $(^CloseBtn) για να κλείσετε τον βοηθό εγκατάστασης."
!endif 

!ifdef UMUI_UNABORTPAGE
  ${LangFileString} UMUI_UNTEXT_ABORT_INFO_TITLE "Τερματίστε τον οδηγό απεγκατάστασης για το $(^NameDA)"
  ${LangFileString} UMUI_UNTEXT_ABORT_INFO_TEXT "Ο βοηθός απεγκατάστασης διακόπηκε πριν την ολοκλήρωση της κατάργησης του $(^NameDA).$\r$\n$\r$\nΓια να καταργήσετε το πρόγραμμα σε μεταγενέστερο χρόνο, εκτελέστε ξανά τον οδηγό.$\r$\n$\r$\n$\r$\n$\r$\nΚάντε κλικ στο $(^CloseBtn) για να κλείσετε τον βοηθό απεγκατάστασης."
!endif


!ifdef UMUI_SETUPTYPEPAGE
  ${LangFileString} UMUI_TEXT_SETUPTYPE_TITLE "Τύπος οδηγού εγκατάστασης"
  ${LangFileString} UMUI_TEXT_SETUPTYPE_SUBTITLE "Επιλέξτε τον τύπο οδηγού εγκατάστασης που σας ταιριάζει."
  ${LangFileString} UMUI_TEXT_SETUPTYPE_INFO_TEXT "Επιλέξτε έναν τύπο οδηγού εγκατάστασης."
  ${LangFileString} UMUI_TEXT_SETUPTYPE_MINIMAL_TEXT "Θα εγκατασταθούν μόνο οι απαραίτητες λειτουργίες. (Απαιτεί τον μικρότερο αποθηκευτικό χώρο στο δίσκο)"
  ${LangFileString} UMUI_TEXT_SETUPTYPE_STANDARD_TEXT "Θα εγκατασταθούν όλες οι κύριες λειτουργίες. Συνιστάται για τους περισσότερους χρήστες."
  ${LangFileString} UMUI_TEXT_SETUPTYPE_COMPLETE_TEXT "Θα εγκατασταθούν όλες οι λειτουργίες του προγράμματος. (Απαιτεί τον μεγαλύτερο αποθηκευτικό χώρο στο δίσκο)"
  ${LangFileString} UMUI_TEXT_SETUPTYPE_CUSTOM_TEXT "Επιλέξτε ποια χαρακτηριστικά του προγράμματος θέλετε να εγκαταστήσετε και τη θέση εγκατάστασης. Συνιστάται για προχωρημένους χρήστες."
!endif 

!ifdef UMUI_UNSETUPTYPEPAGE
  ${LangFileString} UMUI_UNTEXT_SETUPTYPE_TITLE "Τύπος απεγκατάστασης"
  ${LangFileString} UMUI_UNTEXT_SETUPTYPE_SUBTITLE "Επιλέξτε τον τύπο απεγκατάστασης που σας ταιριάζει."
  ${LangFileString} UMUI_UNTEXT_SETUPTYPE_INFO_TEXT "Επιλέξτε έναν τύπο απεγκατάστασης."
  ${LangFileString} UMUI_UNTEXT_SETUPTYPE_MINIMAL_TEXT "Θα διατηρηθούν μόνο οι κύριες λειτουργίες."
  ${LangFileString} UMUI_UNTEXT_SETUPTYPE_STANDARD_TEXT "Θα διατηρηθούν μόνο οι σημαντικότερες λειτουργίες."
  ${LangFileString} UMUI_UNTEXT_SETUPTYPE_COMPLETE_TEXT "Θα διατηρηθεί το σύνολο του προγράμματος."
  ${LangFileString} UMUI_UNTEXT_SETUPTYPE_CUSTOM_TEXT "Επιλέξτε ποια χαρακτηριστικά του προγράμματος θέλετε να καταργήσετε."
!endif 

!ifdef UMUI_SETUPTYPEPAGE | UMUI_UNSETUPTYPEPAGE
  ${LangFileString} UMUI_TEXT_SETUPTYPE_MINIMAL_TITLE "Ελάχιστη"
  ${LangFileString} UMUI_TEXT_SETUPTYPE_STANDARD_TITLE "Τυπική"
  ${LangFileString} UMUI_TEXT_SETUPTYPE_COMPLETE_TITLE "Πλήρης"
  ${LangFileString} UMUI_TEXT_SETUPTYPE_CUSTOM_TITLE "Προσαρμοσμένη από το χρήστη"
!endif 


!ifdef UMUI_INFORMATIONPAGE
  ${LangFileString} UMUI_TEXT_INFORMATION_SUBTITLE "Λάβετε υπόψη τις πληροφορίες για την εγκατάσταση του $(^NameDA)."
!endif 

!ifdef UMUI_UNINFORMATIONPAGE
  ${LangFileString} UMUI_UNTEXT_INFORMATION_SUBTITLE "Λάβετε υπόψη τις πληροφορίες για την απεγκατάσταση του $(^NameDA)."
!endif 

!ifdef UMUI_INFORMATIONPAGE | UMUI_UNINFORMATIONPAGE
  ${LangFileString} UMUI_TEXT_INFORMATION_TITLE "Πληροφορία"
  ${LangFileString} UMUI_TEXT_INFORMATION_INFO_TEXT "Πληροφορίες για το $(^NameDA)."
!endif 


!ifdef UMUI_ADDITIONALTASKSPAGE
  ${LangFileString} UMUI_TEXT_ADDITIONALTASKS_INFO_TEXT "Επιλέξτε πρόσθετες ενέργειες που πρέπει να πραγματοποιήσει ο οδηγός εγκατάστασης κατά τη διάρκεια της εγκατάστασης του $(^NameDA). $_CLICK"
!endif 

!ifdef UMUI_UNADDITIONALTASKSPAGE
  ${LangFileString} UMUI_UNTEXT_ADDITIONALTASKS_INFO_TEXT "Επιλέξτε πρόσθετες ενέργειες που πρέπει να πραγματοποιήσει ο οδηγός απεγκατάστασης κατά τη διάρκεια της κατάργησης του $(^NameDA). $_CLICK"
!endif 

!ifdef UMUI_ADDITIONALTASKSPAGE | UMUI_UNADDITIONALTASKSPAGE
  ${LangFileString} UMUI_TEXT_ADDITIONALTASKS_TITLE "Πρόσθετες ενέργειες"
  ${LangFileString} UMUI_TEXT_ADDITIONALTASKS_SUBTITLE "Ποιες πρόσθετες ενέργειες πρέπει να πραγματοποιηθούν;"
  ${LangFileString} UMUI_TEXT_ADDITIONALTASKS_ADDITIONAL_ICONS "Πρόσθετα εικονίδια:"
  ${LangFileString} UMUI_TEXT_ADDITIONALTASKS_CREATE_DESKTOP_ICON "Δημιουργία εικονιδίου στην επιφάνεια εργασίας"
  ${LangFileString} UMUI_TEXT_ADDITIONALTASKS_CREATE_QUICK_LAUNCH_ICON "Δημιουργία εικονιδίου στη γραμμή γρήγορης εκκίνησης"
  ${LangFileString} UMUI_TEXT_ADDITIONALTASKS_ADVANCED_PARAMETERS "Παράμετροι για προχωρημένους:"
  ${LangFileString} UMUI_TEXT_ADDITIONALTASKS_LAUNCH_PROGRAM_AT_WINDOWS_STARTUP "Εκκίνηση του $(^NameDA) μετά από έναρξη του συστήματος"
  ${LangFileString} UMUI_TEXT_ADDITIONALTASKS_FILE_ASSOCIATION "Συντομεύσεις αρχείων:"
  ${LangFileString} UMUI_TEXT_ADDITIONALTASKS_ASSOCIATE_WITH "Συντόμευση του $(^NameDA) με "
  ${LangFileString} UMUI_TEXT_ADDITIONALTASKS_ASSOCIATE_WITH_END " Τύπος αρχείου"
!endif 
  
  
!ifdef UMUI_CONFIRMPAGE | UMUI_UNCONFIRMPAGE | UMUI_ALTERNATIVESTARTMENUPAGE | UMUI_UNALTERNATIVESTARTMENUPAGE
  ${LangFileString} UMUI_TEXT_SHELL_VAR_CONTEXT "Οι συντομεύσεις πρέπει να δημιουργηθούν για:"
  ${LangFileString} UMUI_TEXT_SHELL_VAR_CONTEXT_FOR_ALL_USERS "Όλους τους χρήστες"
  ${LangFileString} UMUI_TEXT_SHELL_VAR_CONTEXT_ONLY_FOR_CURRENT_USER "Μόνο για τον τρέχοντα χρήστη"
!endif


!ifdef UMUI_UPDATEPAGE
  ${LangFileString} UMUI_TEXT_UPDATE_TITLE "Ενημέρωση"
  ${LangFileString} UMUI_TEXT_UPDATE_SUBTITLE "Ενημέρωση μιας προηγούμενης έκδοσης του προγράμματος."
  ${LangFileString} UMUI_TEXT_UPDATE_INFO_TEXT "Καλωσορίσατε στον βοηθό ενημέρωσης $(^NameDA).$\r$\nΑυτό το πρόγραμμα ενημερώνει την έκδοση $OLDVERSION."
  ${LangFileString} UMUI_TEXT_UPDATE_UPDATE_TITLE "Ενημέρωση"
  ${LangFileString} UMUI_TEXT_UPDATE_UPDATE_TEXT "Ενημέρωση όλων των ήδη εγκατεστημένων στοιχείων του $(^NameDA) με την έκδοση $NEWVERSION."
  ${LangFileString} UMUI_TEXT_UPDATE_REMOVE_TITLE "Αφαίρεση"
  ${LangFileString} UMUI_TEXT_UPDATE_REMOVE_TEXT "Απεγκατάσταση του έκδοση $OLDVERSION από τον υπολογιστή σας."
  ${LangFileString} UMUI_TEXT_UPDATE_CONTINUE_TITLE "Συνέχεια με τον οδηγό εγκατάστασης"
  ${LangFileString} UMUI_TEXT_UPDATE_CONTINUE_TEXT "Συνέχεια με τον οδηγό εγκατάστασης όπως συνήθως. Χρησιμοποιήστε αυτή την επιλογή αν η νέα έκδοση πρέπει να εγκατασταθεί σε ένα νέο φάκελο, παράλληλα με την ήδη υπάρχουσα έκδοση."
!endif


!ifdef UMUI_MAINTENANCEPAGE | UMUI_UNMAINTENANCEPAGE
  ${LangFileString} UMUI_TEXT_MAINTENANCE_TITLE "Διαχείριση"
  ${LangFileString} UMUI_TEXT_MAINTENANCE_SUBTITLE "Τροποποίηση, επιδιόρθωση ή αφαίρεση του προγράμματος."
  ${LangFileString} UMUI_TEXT_MAINTENANCE_INFO_TEXT "Καλωσορίσατε στο πρόγραμμα διαχείρισης $(^NameDA).$\r$\nΜε αυτό το πρόγραμμα μπορείτε να τροποποιήσετε την τρέχουσα εγκατάσταση."
  ${LangFileString} UMUI_TEXT_MAINTENANCE_MODIFY_TITLE "Τροποποίηση"
  ${LangFileString} UMUI_TEXT_MAINTENANCE_MODIFY_TEXT "Επιλέξτε νέα στοιχεία για να τα εγκαταστήσετε, ή επιλέξτε ήδη υπάρχοντα για να τα καταργήσετε."
  ${LangFileString} UMUI_TEXT_MAINTENANCE_REPAIR_TITLE "Επιδιόρθωση"
  ${LangFileString} UMUI_TEXT_MAINTENANCE_REPAIR_TEXT "Επανεγκατάσταση όλων των ήδη εγκατεστημένων στοιχείων του $(^NameDA)."
  ${LangFileString} UMUI_TEXT_MAINTENANCE_REMOVE_TITLE "Αφαίρεση"
  ${LangFileString} UMUI_TEXT_MAINTENANCE_REMOVE_TEXT "Απεγκατάσταση του $(^NameDA) από τον υπολογιστή σας."
  ${LangFileString} UMUI_TEXT_MAINTENANCE_CONTINUE_TITLE "Συνέχεια με τον οδηγό εγκατάστασης"
  ${LangFileString} UMUI_TEXT_MAINTENANCE_CONTINUE_TEXT "Συνέχεια με τον οδηγό εγκατάστασης όπως συνήθως. Χρησιμοποιήστε αυτή την επιλογή αν θέλετε να εγκαταστήσετε το πρόγραμμα πάνω σε μια ήδη υπάρχουσα εγκατάσταση ή να εκτελέσετε μια νέα εγκατάσταση σε μια νέα διεύθυνση."
!endif


!ifdef UMUI_FILEDISKREQUESTPAGE | UMUI_UNFILEDISKREQUESTPAGE
  ${LangFileString} UMUI_TEXT_FILEDISKREQUEST_FILE_SUBTITLE_BEGIN "Ο οδηγός εγκατάστασης χρειάζεται τον επόμενο δίσκο για να συνεχίσει."
  ${LangFileString} UMUI_TEXT_FILEDISKREQUEST_FILE_SUBTITLE_END "αρχείο για να συνεχίσει."
  ${LangFileString} UMUI_TEXT_FILEDISKREQUEST_DISK_SUBTITLE "Ο οδηγός εγκατάστασης χρειάζεται τον επόμενο δίσκο για να συνεχίσει."
  ${LangFileString} UMUI_TEXT_FILEDISKREQUEST_FILE_BEGIN "Επιλέξτε την τοποθεσία αποθήκευσης του αρχείου"
  ${LangFileString} UMUI_TEXT_FILEDISKREQUEST_FILE_END "για να συνεχίσετε."
  ${LangFileString} UMUI_TEXT_FILEDISKREQUEST_DISK "Εισαγάγετε τη"
  ${LangFileString} UMUI_TEXT_FILEDISKREQUEST_PATH "διαδρομή:"
!endif
