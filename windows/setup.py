"""
BleachBit
Copyright (C) 2008-2025 Andrew Ziem
https://www.bleachbit.org
This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.
This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.
You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.


Example invocation (from parent directory):
python3 -m windows.setup
"""

from __future__ import absolute_import, print_function

# standard library
import fnmatch
import glob
import importlib.util
import logging
import os
import re
import shutil
import struct
import subprocess
import sys
import tempfile
import time

# third party
import certifi
from py2exe import freeze

# local import
import bleachbit
from bleachbit.CleanerML import CleanerML
from bleachbit.SystemInformation import get_version
from windows.NsisUtilities import write_nsis_expressions_to_files

SetupEncoding = sys.stdout.encoding
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
formatter = logging.Formatter(
    "%(asctime)s - %(levelname)s - %(message)s", "%Y-%m-%d %H:%M:%S")
ch.setFormatter(formatter)
logger.addHandler(ch)

# Prevent propagation to root logger to avoid duplicate messages
logger.propagate = False

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
logger.info('ROOT_DIR %s', ROOT_DIR)
sys.path.append(ROOT_DIR)

GTK_DIR = sys.exec_prefix + '\\Lib\\site-packages\\gnome\\'
if os.path.exists(GTK_DIR):
    GTK_LIBDIR = GTK_DIR
else:
    GTK_LIBDIR = sys.exec_prefix
    GTK_DIR = os.path.join(GTK_LIBDIR, '..', '..')
NSIS_EXE = 'C:\\Program Files (x86)\\NSIS\\makensis.exe'
NSIS_ALT_EXE = 'C:\\Program Files\\NSIS\\makensis.exe'
SHRED_REGEX_KEY = 'AllFilesystemObjects\\shell\\shred.bleachbit'
if not os.path.exists(NSIS_EXE) and os.path.exists(NSIS_ALT_EXE):
    logger.info('NSIS found in alternate location: %s', NSIS_ALT_EXE)
    NSIS_EXE = NSIS_ALT_EXE
SZ_EXE = 'C:\\Program Files\\7-Zip\\7z.exe'
UPX_EXE = ROOT_DIR + '\\upx\\upx.exe'
UPX_OPTS = '--best --nrv2e'


def archive(infile, outfile, fast_build):
    """Create an archive from a file"""
    assert_exist(infile)
    if os.path.exists(outfile):
        logger.warning(
            'Deleting output archive that already exists: %s', outfile)
        os.remove(outfile)
    # maximum compression with maximum compatibility
    # mm=deflate method because deflate64 not widely supported
    # mpass=passes for deflate encoder
    # mfb=number of fast bytes
    # bso0 bsp0 quiet output
    # 7-Zip Command Line Reverence Wizard: https://axelstudios.github.io/7z/#!/
    sz_opts = '-tzip -mm=Deflate -mfb=258 -mpass=7 -bso0 -bsp0'  # best compression
    if fast_build:
        # fast compression
        sz_opts = '-tzip -mx=1 -bso0 -bsp0'
    cmd = f'{SZ_EXE} a {sz_opts} {outfile} {infile}'
    run_cmd(cmd)
    assert_exist(outfile)


def recursive_glob(rootdir, patterns):
    """Recursively search for files matching the given patterns"""
    return [os.path.join(looproot, filename)
            for looproot, _, filenames in os.walk(rootdir)
            for filename in filenames
            if any(fnmatch.fnmatch(filename, pattern) for pattern in patterns)]


def assert_exist(path, msg=None):
    """Check if a path exists

    If not, log an error and exit."""
    if not os.path.exists(path):
        logger.error('%s not found', path)
        if msg:
            logger.error(msg)
        sys.exit(1)


def check_exist(path, msg=None):
    """Check if a path exists

    If not, log a warning and sleep for 5 seconds."""
    if not os.path.exists(path):
        logger.warning('%s not found', path)
        if msg:
            logger.warning(msg)
        time.sleep(5)


def assert_module(module):
    """Check if a module is available"""
    try:
        importlib.util.find_spec(module)
    except ImportError:
        logger.error('Failed to import %s', module)
        logger.error('Process aborted because of error!')
        sys.exit(1)


def assert_execute(args, expected_output):
    """Run a command and check it returns the expected output"""
    actual_output = subprocess.check_output(args).decode(SetupEncoding)
    if -1 == actual_output.find(expected_output):
        raise RuntimeError(
            f'When running command {args} expected output {expected_output} but got {actual_output}')


def assert_execute_console():
    """Check the application starts"""
    logger.info('Checking bleachbit_console.exe starts')
    assert_execute([r'dist\bleachbit_console.exe', '--gui', '--exit', '--no-uac'],
                   'Success')


def run_cmd(cmd):
    """Run a command and log the output"""
    logger.info(cmd)
    with subprocess.Popen(cmd, stdin=subprocess.PIPE,
                          stdout=subprocess.PIPE, stderr=subprocess.PIPE) as p:
        stdout, stderr = p.communicate()
        logger.info(stdout.decode(SetupEncoding))
        if stderr:
            logger.error(stderr.decode(SetupEncoding))


def sign_files(filenames):
    """Add a digital signature

    Passing multiple filenames in one function call can be faster than
    two calls.
    """
    filenames_str = ' '.join(filenames)
    if os.path.exists('CodeSign.bat'):
        logger.info('Signing code: %s', filenames_str)
        cmd = f'CodeSign.bat {filenames_str}'
        run_cmd(cmd)
    else:
        logger.warning('CodeSign.bat not available for %s', filenames_str)


def get_dir_size(start_path='.'):
    """Get the size of a directory"""
    # http://stackoverflow.com/questions/1392413/calculating-a-directory-size-using-python
    total_size = 0
    for dirpath, _dirnames, filenames in os.walk(start_path):
        for f in filenames:
            fp = os.path.join(dirpath, f)
            total_size += os.path.getsize(fp)
    return total_size


def copy_file(src, dst):
    """Copy a file

    The dst must be a full path.
    """
    if not os.path.exists(src):
        logger.warning('copy_file: %s does not exist', src)
        return
    dst_dirname = os.path.dirname(dst)
    # If the destination directory is current directory, do not create it.
    if dst_dirname and not os.path.exists(dst_dirname):
        os.makedirs(dst_dirname)
    # shutil.copy() and .copyfile() do not preserve file date.
    # Check if target file exists and compare content
    if os.path.exists(dst):
        if os.path.getsize(src) == os.path.getsize(dst):
            with open(src, 'rb') as f1, open(dst, 'rb') as f2:
                if f1.read() == f2.read():
                    logger.debug(
                        'files identical, skipping copy: %s to %s', src, dst)
                    return
        logger.warning('target file exists with different content: %s', dst)
        os.remove(dst)

    shutil.copy2(src, dst)


def copy_tree(src, dst):
    """Copy a directory tree"""
    src = os.path.abspath(src)
    if not os.path.exists(src):
        logger.warning('copytree: %s does not exist', src)
        return
    logger.info('copying %s to %s', src, dst)
    # copytree() preserves file date
    shutil.copytree(src, dst, dirs_exist_ok=True)


def count_size_improvement(func):
    """Decorator to count the size improvement of a function"""
    def wrapper(*args, **kwargs):
        t0 = time.time()
        size0 = get_dir_size('dist')
        func(*args, **kwargs)
        size1 = get_dir_size('dist')
        t1 = time.time()
        logger.info('Reduced size of the dist directory by %s B from %s B to %s B in %.1f s',
                    f'{size0 - size1:,}', f'{size0:,}', f'{size1:,}', t1 - t0)
    return wrapper


def environment_check():
    """Check the build environment"""
    logger.info('Checking for 32-bit Python')
    bits = 8 * struct.calcsize('P')
    assert 32 == bits

    logger.info('Checking for translations')
    assert_exist('locale', 'run "make -C po local" to build translations')

    logger.info('Checking PyGI library')
    assert_module('gi')

    logger.info('Checking Python win32 library')
    assert_module('win32file')

    logger.info('Checking Python py2exe library')
    assert_module('py2exe')

    logger.info('Checking for CodeSign.bat')
    check_exist('CodeSign.bat', 'Code signing is not available')

    logger.info('Checking for NSIS')
    check_exist(
        NSIS_EXE, 'NSIS executable not found: will try to build portable BleachBit')

    logger.info('Checking for 7-Zip')
    check_exist(SZ_EXE, '7-Zip executable not found')


def build_py2exe():
    """Build executables using py2exe's freeze API"""
    # See multiple issues about overly description such as:
    # https://github.com/bleachbit/bleachbit/issues/1000
    app_description = 'Delete unwanted data'

    # Common version info for both GUI and console executables
    formatted_version = get_version(four_parts=True)
    version_info = {
        'version': formatted_version,
        'product_version': formatted_version,
        'product_name': bleachbit.APP_NAME,
        'description': app_description,
        'company_name': bleachbit.APP_NAME,
        'internal_name': f'{bleachbit.APP_NAME} GUI',
        'copyright': bleachbit.APP_COPYRIGHT,
    }

    # GUI bleachbit.exe
    gui_target = {
        'script': 'bleachbit.py',
        'icon_resources': [(1, 'windows/bleachbit.ico')],
        'version_info': version_info
    }

    # Console bleachbit_console.exe
    console_target = gui_target.copy()
    console_target['script'] = 'bleachbit_console.py'
    console_target['internal_name'] = f'{bleachbit.APP_NAME} Console'

    options = {
        'bundle_files': 3,  # All files copied to dist directory
        'compressed': 1,     # Create compressed archive
        'optimize': 2,       # Extra optimization (like python -OO)
        'includes': ['gi'],
        'packages': ['encodings', 'gi', 'gi.overrides', 'plyer'],
        'excludes': ['pyreadline', 'difflib', 'doctest',
                     'pickle', 'ftplib', 'bleachbit.Unix'],
        'dll_excludes': [
            'libgstreamer-1.0-0.dll',
            'CRYPT32.DLL',  # required by ssl
            'DNSAPI.DLL',
            'IPHLPAPI.DLL',  # psutil
            'MPR.dll',
            'MSIMG32.DLL',
            'MSWSOCK.dll',
            'NSI.dll',  # psutil
            'PDH.DLL',  # psutil
            'PSAPI.DLL',
            'POWRPROF.dll',
            'USP10.DLL',
            'WINNSI.DLL',  # psutil
            'WTSAPI32.DLL',  # psutil
            'api-ms-win-core-apiquery-l1-1-0.dll',
            'api-ms-win-core-crt-l1-1-0.dll',
            'api-ms-win-core-crt-l2-1-0.dll',
            'api-ms-win-core-debug-l1-1-1.dll',
            'api-ms-win-core-delayload-l1-1-1.dll',
            'api-ms-win-core-errorhandling-l1-1-0.dll',
            'api-ms-win-core-errorhandling-l1-1-1.dll',
            'api-ms-win-core-file-l1-1-0.dll',
            'api-ms-win-core-file-l1-2-1.dll',
            'api-ms-win-core-handle-l1-1-0.dll',
            'api-ms-win-core-heap-l1-1-0.dll',
            'api-ms-win-core-heap-l1-2-0.dll',
            'api-ms-win-core-heap-obsolete-l1-1-0.dll',
            'api-ms-win-core-io-l1-1-1.dll',
            'api-ms-win-core-kernel32-legacy-l1-1-0.dll',
            'api-ms-win-core-kernel32-legacy-l1-1-1.dll',
            'api-ms-win-core-libraryloader-l1-2-0.dll',
            'api-ms-win-core-libraryloader-l1-2-1.dll',
            'api-ms-win-core-localization-l1-2-1.dll',
            'api-ms-win-core-localization-obsolete-l1-2-0.dll',
            'api-ms-win-core-memory-l1-1-0.dll',
            'api-ms-win-core-memory-l1-1-2.dll',
            'api-ms-win-core-perfstm-l1-1-0.dll',
            'api-ms-win-core-processenvironment-l1-2-0.dll',
            'api-ms-win-core-processthreads-l1-1-0.dll',
            'api-ms-win-core-processthreads-l1-1-2.dll',
            'api-ms-win-core-profile-l1-1-0.dll',
            'api-ms-win-core-registry-l1-1-0.dll',
            'api-ms-win-core-registry-l2-1-0.dll',
            'api-ms-win-core-string-l1-1-0.dll',
            'api-ms-win-core-string-obsolete-l1-1-0.dll',
            'api-ms-win-core-synch-l1-1-0.dll',
            'api-ms-win-core-synch-l1-2-0.dll',
            'api-ms-win-core-sysinfo-l1-1-0.dll',
            'api-ms-win-core-sysinfo-l1-2-1.dll',
            'api-ms-win-core-threadpool-l1-2-0.dll',
            'api-ms-win-core-timezone-l1-1-0.dll',
            'api-ms-win-core-util-l1-1-0.dll',
            'api-ms-win-eventing-classicprovider-l1-1-0.dll',
            'api-ms-win-eventing-consumer-l1-1-0.dll',
            'api-ms-win-eventing-controller-l1-1-0.dll',
            'api-ms-win-eventlog-legacy-l1-1-0.dll',
            'api-ms-win-perf-legacy-l1-1-0.dll',
            'api-ms-win-security-base-l1-2-0.dll',
            'w9xpopen.exe',  # not needed after Windows 9x
        ],
    }

    freeze(
        windows=[gui_target],
        console=[console_target],
        zipfile='library.zip',
        options=options,
        version_info=version_info
    )


def recompile_mo(langdir, app, langid, dst):
    """Recompile gettext .mo file to shrink file size."""
    mo_pathname = os.path.normpath(f'{langdir}/LC_MESSAGES/{app}.mo')
    if not os.path.exists(mo_pathname):
        logger.info('does not exist: %s', mo_pathname)
        return

    # decompile .mo to .po
    po = os.path.join(dst, langid + '.po')
    __args = ['msgunfmt', '-o', po,
              mo_pathname]
    ret = bleachbit.General.run_external(__args)
    if ret[0] != 0:
        raise RuntimeError(ret[2])

    # shrink .po
    po2 = os.path.join(dst, langid + '.po2')
    __args = ['msgmerge', '--no-fuzzy-matching', po,
              os.path.normpath(f'windows/{app}.pot'),
              '-o', po2]
    ret = bleachbit.General.run_external(__args)
    if ret[0] != 0:
        raise RuntimeError(ret[2])

    # compile smaller .po to smaller .mo
    __args = ['msgfmt', po2, '-o', mo_pathname]
    ret = bleachbit.General.run_external(__args)
    if ret[0] != 0:
        raise RuntimeError(ret[2])

    # clean up
    os.remove(po)
    os.remove(po2)


def supported_languages():
    """Return list of supported languages by scanning ./po/"""
    langs = []
    for pathname in glob.glob('po/*.po'):
        basename = os.path.basename(pathname)
        langs.append(os.path.splitext(basename)[0])
    return sorted(langs)


def clean_dist_locale():
    """Clean dist/share/locale"""
    tmpd = tempfile.mkdtemp('gtk_locale')
    supported_langs = supported_languages()
    basedir = os.path.normpath('dist/share/locale')
    have_msgunfmt = bleachbit.FileUtilities.exe_exists('msgunfmt.exe')
    recompile_langs = []  # supported languages to recompile
    remove_langs = []  # unsupported languages to remove
    for langid in sorted(os.listdir(basedir)):
        if langid in supported_langs:
            recompile_langs.append(langid)
        else:
            remove_langs.append(langid)
    if recompile_langs:
        if have_msgunfmt:
            logger.info('recompiling supported GTK languages: %s',
                        recompile_langs)
            for lang_id in recompile_langs:
                recompile_mo(basedir, 'gtk30', lang_id, tmpd)
        else:
            logger.warning('msgunfmt missing: skipping recompile')
    if remove_langs:
        logger.info('removing unsupported GTK languages: %s', remove_langs)
        for langid in remove_langs:
            langdir = os.path.join(basedir, langid)
            if os.path.exists(langdir):
                logger.info('Removing directory: %s', langdir)
                shutil.rmtree(langdir)
    else:
        logger.info('no unsupported GTK languages found')
    os.rmdir(tmpd)


def build():
    """Build the application"""
    logger.info('Deleting directories build and dist')
    shutil.rmtree('build', ignore_errors=True)
    shutil.rmtree('dist', ignore_errors=True)
    shutil.rmtree('BleachBit-Portable', ignore_errors=True)

    logger.info('Running py2exe')
    copy_file('bleachbit.py', 'bleachbit_console.py')
    build_py2exe()
    assert_exist('dist\\bleachbit.exe')
    assert_exist('dist\\bleachbit_console.exe')
    os.remove('bleachbit_console.py')

    if not os.path.exists('dist'):
        os.makedirs('dist')

    os.makedirs(os.path.join('dist', 'share'), exist_ok=True)

    logger.info('Copying GTK helpers')
    for exe in glob.glob1(GTK_LIBDIR, 'gspawn-win*-helper*.exe'):
        copy_file(os.path.join(GTK_LIBDIR, exe), os.path.join('dist', exe))
    for exe in ('fc-cache.exe',):
        copy_file(os.path.join(GTK_LIBDIR, exe), os.path.join('dist', exe))

    logger.info('Copying GTK files and icon')
    for d in ('dbus-1', 'fonts', 'gtk-3.0', 'pango'):
        path = os.path.join(GTK_DIR, 'etc', d)
        copy_tree(path, os.path.join('dist', 'etc', d))
    for d in ('gdk-pixbuf-2.0', 'girepository-1.0', 'glade', 'gtk-3.0'):
        path = os.path.join(GTK_DIR, 'lib', d)
        copy_tree(path, os.path.join('dist', 'lib', d))

    gtk_share = os.path.join(GTK_LIBDIR, 'share')
    if os.path.exists(gtk_share):
        for d in ('icons', 'themes'):
            path = os.path.join(gtk_share, d)
            copy_tree(path, os.path.join('dist', 'share', d))

    logger.info('Fixing paths in loaders.cache file')
    loaders_fn = os.path.join(
        'dist', 'lib', 'gdk-pixbuf-2.0', '2.10.0', 'loaders.cache')
    with open(loaders_fn, 'r+', encoding=SetupEncoding) as f:
        data = f.read()
        data = re.sub(r'^".*[/\\](.*\.dll)"$',
                      r'"\1"', data, flags=re.I | re.M)
        f.seek(0)
        f.write(data)
        f.truncate()

    # fonts are not needed https://github.com/bleachbit/bleachbit/issues/863
    for d in ('icons',):
        path = os.path.join(GTK_DIR, 'share', d)
        copy_tree(path, os.path.join('dist', 'share', d))
    schemas_dir = 'share\\glib-2.0\\schemas'
    gschemas_compiled_src = os.path.join(
        GTK_DIR, schemas_dir, 'gschemas.compiled')
    gschemas_compiled_dst = os.path.join(
        'dist', schemas_dir, 'gschemas.compiled')
    copy_file(gschemas_compiled_src, gschemas_compiled_dst)
    copy_file('bleachbit.png', 'dist\\share\\bleachbit.png')
    # bleachbit.ico is used the for pop-up notification.
    copy_file('windows\\bleachbit.ico', 'dist\\share\\bleachbit.ico')
    for dll in glob.glob1(GTK_LIBDIR, '*.dll'):
        copy_file(os.path.join(GTK_LIBDIR, dll), 'dist\\' + dll)

    copy_file('data\\app-menu.ui', 'dist\\data\\app-menu.ui')

    logger.info('Copying themes')
    copy_tree('themes', 'dist\\themes')

    logger.info('Copying CA bundle')
    copy_file(certifi.where(),
              os.path.join('dist', 'cacert.pem'))

    dist_locale_dir = r'dist\share\locale'
    shutil.rmtree(dist_locale_dir, ignore_errors=True)
    os.makedirs(dist_locale_dir)

    logger.info('Copying GTK localizations')
    locale_dir = os.path.join(GTK_DIR, 'share\\locale\\')
    for f in recursive_glob(locale_dir, ['gtk30.mo']):
        if not f.startswith(locale_dir):
            continue
        rel_f = f[len(locale_dir):]
        copy_file(f, os.path.join(dist_locale_dir, rel_f))
    assert_exist(os.path.join(dist_locale_dir, r'es\LC_MESSAGES\gtk30.mo'))

    logger.info('Copying BleachBit localizations')
    copy_tree('locale', dist_locale_dir)
    assert_exist(os.path.join(dist_locale_dir, r'es\LC_MESSAGES\bleachbit.mo'))

    logger.info('Copying BleachBit cleaners')
    if not os.path.exists('dist\\share\\cleaners'):
        os.makedirs('dist\\share\\cleaners')
    cleaners_files = recursive_glob('cleaners', ['*.xml'])
    for file in cleaners_files:
        shutil.copy(file, 'dist\\share\\cleaners')

    logger.info('Checking for CleanerML')
    assert_exist('dist\\share\\cleaners\\internet_explorer.xml')

    logger.info('Copying license')
    copy_file('COPYING', 'dist\\COPYING')

    logger.info('Copying DLL')
    python_version = sys.version_info[:2]
    if python_version == (3, 4):
        # For Python 3.4, copy msvcr100.dll
        dll_name = 'msvcr100.dll'
    elif python_version >= (3, 10):
        # For Python 3.10, copy vcruntime140.dll
        dll_name = 'vcruntime140.dll'
    else:
        logger.error('Unsupported Python version. Skipping DLL copy.')
        return
    dll_dirs = (sys.prefix, r'c:\windows\system32', r'c:\windows\SysWOW64')
    copied_dll = False
    for dll_dir in dll_dirs:
        dll_path = os.path.join(dll_dir, dll_name)
        if os.path.exists(dll_path):
            logger.info('Copying %s from %s', dll_name, dll_path)
            shutil.copy(dll_path, 'dist')
            copied_dll = True
            break
    if not copied_dll:
        logger.warning('%s not found. Skipping copy.', dll_name)

    sign_files(('dist\\bleachbit.exe', 'dist\\bleachbit_console.exe'))

    assert_execute_console()


@count_size_improvement
def delete_unnecessary():
    """Delete unnecessary files"""
    logger.info('Deleting unnecessary files')
    # Remove SVG to reduce space and avoid this error
    # Error loading theme icon 'dialog-warning' for stock: Unable to load image-loading module: C:/PythonXY/Lib/site-packages/gtk-2.0/runtime/lib/gdk-pixbuf-2.0/2.10.0/loaders/libpixbufloader-svg.dll: `C:/PythonXY/Lib/site-packages/gtk-2.0/runtime/lib/gdk-pixbuf-2.0/2.10.0/loaders/libpixbufloader-svg.dll': The specified module could not be found.
    # https://bugs.launchpad.net/bleachbit/+bug/1650907
    delete_paths = [
        r'_win32sysloader.pyd',
        r'perfmon.pyd',
        r'servicemanager.pyd',
        r'share\icons\highcontrast',
        r'win32evtlog.pyd',
        r'win32pipe.pyd',
        r'win32wnet.pyd',
    ]
    for path in delete_paths:
        path = fr'dist\{path}'
        if not os.path.exists(path):
            logger.warning('Path does not exist: %s', path)
            continue
        if os.path.isdir(path):
            this_dir_size = get_dir_size(path)
            shutil.rmtree(path, ignore_errors=True)
            logger.info('Deleting directory %s saved %s B',
                        path, f'{this_dir_size:,}')
        else:
            file_size = os.path.getsize(path)
            logger.info('Deleting file %s saved %s B', path, f'{file_size:,}')
            os.remove(path)


@count_size_improvement
def delete_icons():
    """Delete unused PNG/SVG icons to reduce size"""
    logger.info('Deleting unused PNG/SVG icons')
    # This whitelist comes from analyze_process_monitor_events.py
    icon_whitelist = [
        'edit-clear-all.png',
        'edit-delete.png',
        'edit-find.png',
        'list-add-symbolic.svg',  # spin box in chaff dialog
        'list-remove-symbolic.svg',  # spin box in chaff dialog
        'pan-down-symbolic.svg',  # there is no pan-down.png
        'pan-end-symbolic.svg',  # there is no pan-end.png
        'process-stop.png',  # abort on toolbar
        'window-close-symbolic.svg',  # png does not get used
        'window-maximize-symbolic.svg',  # no png
        'window-minimize-symbolic.svg',  # no png
        'window-restore-symbolic.svg'  # no png
    ]
    strip_list = recursive_glob(r'dist\share\icons', ['*.png', '*.svg'])
    for f in strip_list:
        if os.path.basename(f) not in icon_whitelist:
            os.remove(f)
        else:
            logger.info('keeping whitelisted icon: %s', f)


def remove_empty_dirs(root):
    """Remove empty directories"""
    for entry in os.scandir(root):
        if entry.is_dir():
            remove_empty_dirs(entry.path)
            if not os.listdir(entry.path):
                logger.info('Deleting empty directory: %s', entry.path)
                os.rmdir(entry.path)


@count_size_improvement
def clean_translations():
    """Clean translations (localizations)"""
    logger.info('Cleaning translations')
    if os.path.exists(r'dist\share\locale\locale.alias'):
        os.remove(r'dist\share\locale\locale.alias')
    else:
        logger.warning('locale.alias does not exist')
    pygtk_translations = os.listdir('dist/share/locale')
    supported_translations = [f[3:-3] for f in glob.glob('po/*.po')]
    for pt in pygtk_translations:
        if pt not in supported_translations:
            path = 'dist/share/locale/' + pt
            shutil.rmtree(path)


@count_size_improvement
def strip():
    """Strip executables to reduce size"""
    if not bleachbit.FileUtilities.exe_exists('strip.exe'):
        logger.warning('strip.exe does not exist. Skipping strip.')
        return
    logger.info('Stripping executables')
    strip_list = recursive_glob('dist', ['*.dll', '*.pyd'])
    strip_whitelist = ['_sqlite3.dll']
    strip_files_str = [f for f in strip_list if os.path.basename(
        f) not in strip_whitelist]
    # Process each file individually in case it is locked. See
    # https://github.com/bleachbit/bleachbit/issues/690
    for strip_file in strip_files_str:
        if os.path.exists('strip.tmp'):
            os.remove('strip.tmp')
        if not os.path.exists(strip_file):
            logger.error('%s does not exist before stripping', strip_file)
            continue
        cmd = f'strip.exe --strip-debug --discard-all --preserve-dates -o strip.tmp {strip_file}'
        run_cmd(cmd)
        if not os.path.exists(strip_file):
            logger.error('%s does not exist after stripping', strip_file)
            continue
        if not os.path.exists('strip.tmp'):
            logger.warning('strip.tmp missing while processing %s', strip_file)
            continue
        error_counter = 0
        while error_counter < 100:
            try:
                os.remove(strip_file)
            except PermissionError:
                logger.warning(
                    'permissions error while removing %s', strip_file)
                time.sleep(.1)
                error_counter += 1
            else:
                break
        if error_counter > 1:
            logger.warning('error counter %d while removing %s',
                           error_counter, strip_file)
        if not os.path.exists(strip_file):
            os.rename('strip.tmp', strip_file)


@count_size_improvement
def upx(fast_build):
    """Compress executables with UPX to reduce size"""
    logger.warning('UPX causes application to not launch, so UPX is disabled for now')
    return
    if fast_build:
        logger.warning('Fast mode: Skipped executable with UPX')
        return

    if not os.path.exists(UPX_EXE):
        logger.warning(
            'UPX not found. To compress executables, install UPX to: %s', UPX_EXE)
        return

    logger.info('Compressing executables')
    # Do not compress bleachbit.exe and bleachbit_console.exe to avoid false positives
    # with antivirus software. Not much is space with gained with these small files, anyway.
    upx_files = recursive_glob('dist', ['*.dll', '*.pyd'])
    cmd = f'{UPX_EXE} {UPX_OPTS} {" ".join(upx_files)}'
    run_cmd(cmd)
    assert_execute_console()


@count_size_improvement
def delete_linux_only():
    """Delete Linux-only cleaners to reduce size"""
    logger.info('Deleting Linux-only cleaners')
    files = recursive_glob('dist/share/cleaners/', ['*.xml'])
    for fn in files:
        cml = CleanerML(fn)
        if not cml.get_cleaner().is_usable():
            logger.warning('Deleting cleaner not usable on this OS: %s', fn)
            os.remove(fn)


@count_size_improvement
def recompress_library(fast_build):
    """Recompress library.zip to reduce size"""
    if fast_build:
        logger.warning('Fast mode: Skipped recompression of library.zip')
        return

    if not os.path.exists(SZ_EXE):
        logger.warning('%s does not exist', SZ_EXE)
        return

    logger.info('Recompressing library.zip with 7-Zip')

    # extract library.zip
    if not os.path.exists('dist\\library'):
        os.makedirs('dist\\library')
    cmd = SZ_EXE + ' x  dist\\library.zip' + ' -odist\\library  -y'
    run_cmd(cmd)
    file_size_old = os.path.getsize('dist\\library.zip')
    os.remove('dist\\library.zip')

    # clean unused modules from library.zip
    delete_paths = ['distutils', 'plyer\\platforms\\android',
                    'plyer\\platforms\\ios', 'plyer\\platforms\\linux', 'plyer\\platforms\\macosx']
    for p in delete_paths:
        path = os.path.join('dist', 'library', p)
        if os.path.exists(path):
            shutil.rmtree(path)

    # recompress library.zip
    os.chdir('dist\\library')
    archive('.', '..\\library.zip', fast_build)
    os.chdir('..\\..')
    file_size_new = os.path.getsize('dist\\library.zip')
    file_size_diff = file_size_old - file_size_new
    logger.info('Recompression of library.dll reduced size by %s from %s to %s',
                f'{file_size_diff:,}', f'{file_size_old:,}', f'{file_size_new:,}')
    shutil.rmtree('dist\\library', ignore_errors=True)
    assert_exist('dist\\library.zip')


def shrink(fast_build):
    """After building, run all the applicable size optimizations"""
    delete_unnecessary()
    delete_icons()
    clean_translations()
    remove_empty_dirs('dist')
    strip()
    upx(fast_build)

    logger.info('Purging unnecessary GTK+ files')
    clean_dist_locale()

    delete_linux_only()

    recompress_library(fast_build)

    # so calculate the size of the folder, as it is a goal to shrink it.
    logger.info('Final size of the dist folder: %s',
                f'{get_dir_size("dist"):,}')


def package_portable(fast_build):
    """Package the portable version"""
    logger.info('Building portable')
    copy_tree('dist', 'BleachBit-Portable')
    with open("BleachBit-Portable\\BleachBit.ini", "w", encoding=SetupEncoding) as text_file:
        text_file.write("[Portable]")

    archive('BleachBit-Portable',
            f'BleachBit-{get_version()}-portable.zip', fast_build)


def nsis(opts, exe_name, nsi_path):
    """Run NSIS with the options to build exe_name"""
    if os.path.exists(exe_name):
        logger.info('Deleting old file: %s', exe_name)
        os.remove(exe_name)
    cmd = f'{NSIS_EXE} {opts} /DVERSION={get_version()} /DSHRED_REGEX_KEY={SHRED_REGEX_KEY} {nsi_path}'
    run_cmd(cmd)
    assert_exist(exe_name)


def package_installer(fast_build, nsi_path=r'windows\bleachbit.nsi'):
    """Package the installer"""

    assert isinstance(fast_build, bool)
    assert isinstance(nsi_path, str)

    if not os.path.exists(NSIS_EXE):
        logger.warning('NSIS not found, so not building installer')
        return

    logger.info('Building installer')

    write_nsis_expressions_to_files()

    exe_name_multilang = f'windows\\BleachBit-{get_version()}-setup.exe'
    exe_name_en = f'windows\\BleachBit-{get_version()}-setup-English.exe'
    # Was:
    # opts = '' if fast else '/X"SetCompressor /FINAL zlib"'
    # Now: Done in NSIS file!
    opts = '' if fast_build else '/V3 /Dpackhdr /DCompressor'
    nsis(opts, exe_name_multilang, nsi_path)

    if fast_build:
        sign_files((exe_name_multilang,))
    else:
        # Was:
        # nsis('/DNoTranslations',
        # Now: Compression gets now done in NSIS file!
        # As of 2022-11-20, there is not a big size difference for
        # the English-only build, and Google Search flags the Python 3.10
        # version as malware.
        nsis(opts + ' /DNoTranslations', exe_name_en, nsi_path)
        sign_files((exe_name_multilang, exe_name_en))

    if os.path.exists(SZ_EXE):
        logger.info('Zipping installer')
        # The archive does not have the folder name.
        outfile = f"{ROOT_DIR}\\windows\\BleachBit-{get_version()}-setup.zip"
        infile = f"{ROOT_DIR}\\windows\\BleachBit-{get_version()}-setup.exe"
        archive(infile, outfile, fast_build)
    else:
        logger.warning('%s does not exist', SZ_EXE)


def main():
    """Main function"""
    logger.info('BleachBit version %s', get_version())
    environment_check()
    fast_build = len(sys.argv) > 1 and sys.argv[1] == 'fast'
    build()
    shrink(fast_build)
    package_portable(fast_build)
    package_installer(fast_build)
    # Clearly show the sizes of the files that end users download because the
    # goal is to minimize them.
    os.system(r'dir *.zip windows\*.exe windows\*.zip')
    logger.info('Success!')


if '__main__' == __name__:
    # Add py2exe to sys.argv if it's not already there
    # This allows running 'python3 -m windows.setup' without explicitly adding py2exe
    if len(sys.argv) == 1 or 'py2exe' not in sys.argv:
        sys.argv.append('py2exe')
    main()
