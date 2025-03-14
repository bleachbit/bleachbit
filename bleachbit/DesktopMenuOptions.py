from bleachbit.Options import options

import os
from pathlib import Path


def install_kde_service_menu_file():
    try:
        # Honor the XDG Base Directory Specification first
        # and check if $XDG_DATA_HOME has already been defined.
        # The path default is $HOME/.local/share
        data_home_path = Path(os.environ["XDG_DATA_HOME"])
    except KeyError:
        data_home_path = Path(os.environ["HOME"], ".local", "share")
    service_file_path = data_home_path / "kio" / \
        "servicemenus" / "shred_with_bleachbit.desktop"
    if options.get("kde_shred_menu_option"):
        dir_path = service_file_path.parent
        if not dir_path.exists():
            dir_path.mkdir(parents=True)
        if not service_file_path.exists():
            # Service file has dependency on `kdialog` which KDE installations may not provide by default.
            with service_file_path.open('w') as service_file:
                service_file_path.chmod(0o755)
                service_file.write(r'''
[Desktop Entry]
Type=Service
Name=Shred With Bleachbit
X-KDE-ServiceTypes=KonqPopupMenu/Plugin
MimeType=all/all
Icon=bleachbit
Actions=BleachbitShred
Terminal=true

[Desktop Action BleachbitShred]
Name=Shred With Bleachbit
Icon=bleachbit
Exec=kdialog --yesno "This action will shred the following:\n\n$(echo %F | tr ' ' '\n')\n\nContinue?" && sh -c 'bleachbit --shred "$@"; echo Press enter/return to close; read' sh %F
''')
    else:
        try:
            service_file_path.unlink()
        except FileNotFoundError:
            pass
