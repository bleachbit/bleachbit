"""Helper utilities to install optional desktop service menus."""

import logging
import os
from pathlib import Path

from bleachbit.FileUtilities import open_for_overwrite
from bleachbit.Options import options

logger = logging.getLogger(__name__)


def install_kde_service_menu_file():
    """Create or remove the KDE service menu entry for shredding."""
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
            try:
                with open_for_overwrite(str(service_file_path)) as service_file:
                    # fchmod on the fd, not .chmod() on the path, so a
                    # symlink raced in after the exists() check above
                    # can't redirect the permission change to its target.
                    os.fchmod(service_file.fileno(), 0o755)
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
            except OSError as exc:
                logger.warning(
                    'failed to create KDE service menu file %s: %s',
                    service_file_path, exc)
    else:
        service_file_path.unlink(missing_ok=True)
