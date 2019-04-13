!macro UMUI_BG
		SetOutPath "$PLUGINSDIR"
		File "${NSISDIR}\Contrib\UltraModernUI\BGSkins\SoftGray\BackGround.bmp"
		BgImage::SetBg /FILLSCREEN "$PLUGINSDIR\BackGround.bmp"
		CreateFont $1 "Verdana" 30 700
		BgImage::AddText "$(^Name)" $1 255 255 255 16 114 -1 -1
		BgImage::AddText "$(^Name)" $1 132 132 132 12 110 -1 -1
		BgImage::Redraw
!macroend
!macro UMUI_BG_Destroy
		BgImage::Destroy
!macroend
