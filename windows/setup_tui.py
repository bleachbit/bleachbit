# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (c) 2008-2026 Andrew Ziem.
#
# This work is licensed under the terms of the GNU GPL, version 3 or
# later.  See the COPYING file in the top-level directory.

"""
BleachBit TUI — Windows build script

Example invocation (from parent directory):
python3 -m windows.setup_tui

Differences from the main (GTK) Windows build:
  - Uses native 64-bit Python (no 32-bit PyGTK constraint)
  - No GTK / PyGObject dependencies
  - Builds a single console executable (bleachbit_tui.exe)

FIXME: stop duplicating code with windows/setup.py
"""

# standard library
import fnmatch
import importlib.util
import logging
import os
import shutil
import struct
import subprocess
import sys
import time

# third party
import certifi

# local import
import bleachbit
from setup import supported_languages
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
logger.propagate = False

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
logger.info('ROOT_DIR %s', ROOT_DIR)
sys.path.append(ROOT_DIR)

NSIS_EXE = 'C:\\Program Files (x86)\\NSIS\\makensis.exe'
NSIS_ALT_EXE = 'C:\\Program Files\\NSIS\\makensis.exe'
if not os.path.exists(NSIS_EXE) and os.path.exists(NSIS_ALT_EXE):
    logger.info('NSIS found in alternate location: %s', NSIS_ALT_EXE)
    NSIS_EXE = NSIS_ALT_EXE
SZ_EXE = 'C:\\Program Files\\7-Zip\\7z.exe'
UPX_EXE = ROOT_DIR + '\\upx\\upx.exe'
UPX_OPTS = '--best --nrv2e'
PORTABLE_DIR = 'BleachBit-Portable'


# ---------------------------------------------------------------------------
# Utility functions
# ---------------------------------------------------------------------------

def archive(infile, outfile, fast_build):
    """Create an archive from a file"""
    assert_exist(infile)
    if os.path.exists(outfile):
        logger.warning('Deleting output archive that already exists: %s', outfile)
        os.remove(outfile)
    sz_opts = '-tzip -mm=Deflate -mfb=258 -mpass=7 -bso0 -bsp0'
    if fast_build:
        sz_opts = '-tzip -mx=1 -bso0 -bsp0'
    cmd = f'{SZ_EXE} a {sz_opts} {outfile} {infile}'
    run_cmd(cmd)
    assert_exist(outfile)
    outfile_abs = os.path.abspath(outfile)
    outfile_size = os.path.getsize(outfile)
    logger.info('Created archive: %s (%s bytes)', outfile_abs, f'{outfile_size:,}')


def recursive_glob(rootdir, patterns):
    """Recursively search for files matching the given patterns"""
    return [os.path.join(looproot, filename)
            for looproot, _, filenames in os.walk(rootdir)
            for filename in filenames
            if any(fnmatch.fnmatch(filename, pattern) for pattern in patterns)]


def assert_exist(path, msg=None):
    """Check if a path exists. If not, log an error and exit."""
    if not os.path.exists(path):
        logger.error('%s not found', path)
        if msg:
            logger.error(msg)
        sys.exit(1)


def check_exist(path, msg=None):
    """Check if a path exists. If not, log a warning and sleep."""
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
    """Add a digital signature"""
    filenames_str = ' '.join(filenames)
    if os.path.exists('CodeSign.bat'):
        logger.info('Signing code: %s', filenames_str)
        cmd = f'CodeSign.bat {filenames_str}'
        run_cmd(cmd)
    else:
        logger.warning('CodeSign.bat not available for %s', filenames_str)


def get_dir_size(start_path='.'):
    """Get the size of a directory"""
    total_size = 0
    for dirpath, _dirnames, filenames in os.walk(start_path):
        for f in filenames:
            fp = os.path.join(dirpath, f)
            total_size += os.path.getsize(fp)
    return total_size


def copy_file(src, dst):
    """Copy a file. dst must be a full path."""
    if not os.path.exists(src):
        logger.warning('copy_file: %s does not exist', src)
        return
    dst_dirname = os.path.dirname(dst)
    if dst_dirname and not os.path.exists(dst_dirname):
        os.makedirs(dst_dirname)
    if os.path.exists(dst):
        if os.path.getsize(src) == os.path.getsize(dst):
            with open(src, 'rb') as f1, open(dst, 'rb') as f2:
                if f1.read() == f2.read():
                    logger.debug('files identical, skipping copy: %s to %s', src, dst)
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
    shutil.copytree(src, dst, dirs_exist_ok=True)


def remove_empty_dirs(root):
    """Remove empty directories"""
    for entry in os.scandir(root):
        if entry.is_dir():
            remove_empty_dirs(entry.path)
            if not os.listdir(entry.path):
                logger.info('Deleting empty directory: %s', entry.path)
                os.rmdir(entry.path)


# ---------------------------------------------------------------------------
# Size optimization decorator
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# Environment check — TUI-specific
# ---------------------------------------------------------------------------

def environment_check():
    """Check the build environment for TUI build"""
    logger.info('Checking for 64-bit Python')
    bits = 8 * struct.calcsize('P')
    assert 64 == bits, f'Expected 64-bit Python, got {bits}-bit'

    logger.info('Checking for translations')
    assert_exist('locale', 'run "make -C po local" to build translations')

    logger.info('Checking Python win32 library')
    assert_module('win32file')

    logger.info('Checking Python py2exe library')
    assert_module('py2exe')

    logger.info('Checking for Textual')
    assert_module('textual')

    logger.info('Checking for CodeSign.bat')
    check_exist('CodeSign.bat', 'Code signing is not available')

    logger.info('Checking for NSIS')
    check_exist(NSIS_EXE, 'NSIS executable not found: will still build portable')

    logger.info('Checking for 7-Zip')
    check_exist(SZ_EXE, '7-Zip executable not found')


# ---------------------------------------------------------------------------
# py2exe build — TUI only, console subsystem
# ---------------------------------------------------------------------------

def build_py2exe():
    """Build the TUI executable using py2exe's freeze API"""
    # pylint: disable=import-outside-toplevel
    from py2exe import freeze

    formatted_version = get_version(four_parts=True)
    app_description = 'Delete unwanted data — Terminal UI'

    version_info = {
        'version': formatted_version,
        'product_version': formatted_version,
        'product_name': f'{bleachbit.APP_NAME} TUI',
        'description': app_description,
        'company_name': bleachbit.APP_NAME,
        'internal_name': f'{bleachbit.APP_NAME} TUI',
        'copyright': bleachbit.APP_COPYRIGHT,
    }

    console_target = {
        'script': 'bleachbit_tui.py',
        'icon_resources': [(1, 'windows/bleachbit.ico')],
        'version_info': version_info,
    }

    options = {
        'bundle_files': 3,
        'compressed': 1,
        'optimize': 2,
        'packages': ['chardet', 'encodings', 'textual', 'rich', 'rich._unicode_data',
                     'markdown_it', 'mdurl', 'linkify_it'],
        'excludes': ['pyreadline', 'doctest', 'ftplib',
                     'charset_normalizer', 'gi', 'cairo', 'Gtk', 'Gdk', 'GLib',
                     'Pango', 'tcl', 'tk', 'tkinter', 'bleachbit.GUI',
                     'bleachbit.GuiApplication', 'bleachbit.GuiBasic',
                     'bleachbit.GuiChaff', 'bleachbit.GuiCookie',
                     'bleachbit.GuiPreferences', 'bleachbit.GuiStartup',
                     'bleachbit.GuiTreeModels', 'bleachbit.GuiUtil',
                     'bleachbit.GuiWindow', 'bleachbit.FontCheckDialog',
                     'bleachbit.Unix'],
        'dll_excludes': [
            'CRYPT32.DLL',
            'DNSAPI.DLL',
            'IPHLPAPI.DLL',
            'MPR.dll',
            'MSIMG32.DLL',
            'MSWSOCK.dll',
            'NSI.dll',
            'PDH.DLL',
            'PSAPI.DLL',
            'POWRPROF.dll',
            'USP10.DLL',
            'WINNSI.DLL',
            'WTSAPI32.DLL',
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
            'w9xpopen.exe',
        ],
    }

    try:
        freeze(
            console=[console_target],
            zipfile='library.zip',
            options=options,
            version_info=version_info,
        )
    except PermissionError as e :
        logger.error("Failed to freeze: %s; check that other process does not have files open", e)
        raise


# ---------------------------------------------------------------------------
# Build — assemble the dist/ directory
# ---------------------------------------------------------------------------

def build():
    """Build the TUI application"""
    logger.info('Deleting directories build and dist')
    for dir_path in ['build', 'dist', PORTABLE_DIR]:
        if os.path.exists(dir_path):
            try:
                shutil.rmtree(dir_path)
            except PermissionError as e:
                logger.error("Failed to delete %s: %s. Check that another process does not have the file locked.", dir_path, e)
        if os.path.exists(dir_path):
            logger.error('failed to delete %s', os.path.abspath(dir_path))

    logger.info('Running py2exe')
    build_py2exe()
    assert_exist('dist\\bleachbit_tui.exe')

    if not os.path.exists('dist'):
        os.makedirs('dist')
    os.makedirs(os.path.join('dist', 'share'), exist_ok=True)

    # Cleaners (XML files)
    logger.info('Copying BleachBit cleaners')
    if not os.path.exists('dist\\share\\cleaners'):
        os.makedirs('dist\\share\\cleaners')
    cleaners_files = recursive_glob('cleaners', ['*.xml'])
    for file in cleaners_files:
        shutil.copy(file, 'dist\\share\\cleaners')
    assert_exist('dist\\share\\cleaners\\internet_explorer.xml')

    # Localizations
    dist_locale_dir = r'dist\share\locale'
    shutil.rmtree(dist_locale_dir, ignore_errors=True)
    os.makedirs(dist_locale_dir)

    logger.info('Copying BleachBit localizations')
    copy_tree('locale', dist_locale_dir)
    assert_exist(os.path.join(dist_locale_dir, r'es\LC_MESSAGES\bleachbit.mo'))

    # License
    logger.info('Copying license')
    copy_file('COPYING', 'dist\\COPYING')

    # CA bundle for SSL
    logger.info('Copying CA bundle')
    copy_file(certifi.where(), os.path.join('dist', 'cacert.pem'))

    # Runtime DLL
    logger.info('Copying DLL')
    python_version = sys.version_info[:2]
    if python_version >= (3, 10):
        dll_names = ['vcruntime140.dll', 'vcruntime140_1.dll']
    else:
        logger.error('Unsupported Python version. Skipping DLL copy.')
        return
    dll_dirs = (sys.prefix, r'c:\windows\system32')
    for dll_name in dll_names:
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

    # Protected path XML
    copy_file('share\\protected_path.xml', 'dist\\share\\protected_path.xml')

    sign_files(('dist\\bleachbit_tui.exe',))


# ---------------------------------------------------------------------------
# Size optimizations
# ---------------------------------------------------------------------------

@count_size_improvement
def delete_unnecessary():
    """Delete unnecessary files from dist/"""
    logger.info('Deleting unnecessary files')
    delete_paths = [
        r'_win32sysloader.pyd',
        r'perfmon.pyd',
        r'servicemanager.pyd',
        r'win32evtlog.pyd',
        r'win32pipe.pyd',
        r'win32wnet.pyd',
        r'libcrypto-3.dll',
        r'libssl-3.dll',
        r'_decimal.pyd',
        r'_ssl.pyd',
        r'_testcapi.pyd',
        r'_testinternalcapi.pyd',
        r'_testlimitedcapi.pyd',
    ]
    for path in delete_paths:
        path = fr'dist\{path}'
        if not os.path.exists(path):
            logger.warning('Path does not exist: %s', path)
            continue
        if os.path.isdir(path):
            this_dir_size = get_dir_size(path)
            shutil.rmtree(path, ignore_errors=True)
            logger.info('Deleting directory %s saved %s B', path, f'{this_dir_size:,}')
        else:
            file_size = os.path.getsize(path)
            logger.info('Deleting file %s saved %s B', path, f'{file_size:,}')
            os.remove(path)


@count_size_improvement
def clean_translations():
    """Remove unsupported translations from dist/"""
    logger.info('Cleaning translations')
    dist_locale = 'dist/share/locale'
    if not os.path.exists(dist_locale):
        return
    supported = supported_languages()
    for langid in os.listdir(dist_locale):
        if langid not in supported:
            path = os.path.join(dist_locale, langid)
            if os.path.isdir(path):
                shutil.rmtree(path)


@count_size_improvement
def upx(fast_build):
    """Compress executables with UPX to reduce size"""
    if fast_build:
        logger.warning('Fast mode: Skipped executable with UPX')
        return

    if not os.path.exists(UPX_EXE):
        logger.warning(
            'UPX not found. To compress executables, install UPX to: %s', UPX_EXE)
        return

    logger.info('Compressing executables')
    # Do not compress bleachbit_tui.exe to avoid false positives
    # with antivirus software.
    upx_files = recursive_glob('dist', ['*.dll', '*.pyd'])
    cmd = f'{UPX_EXE} {UPX_OPTS} {" ".join(upx_files)}'
    run_cmd(cmd)


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

    if not os.path.exists('dist\\library'):
        os.makedirs('dist\\library')
    cmd = SZ_EXE + ' x  dist\\library.zip' + ' -odist\\library  -y'
    run_cmd(cmd)
    file_size_old = os.path.getsize('dist\\library.zip')
    os.remove('dist\\library.zip')

    # Clean unused modules
    delete_paths = [
        'distutils',
        'setuptools',
        'pydoc_data',
        'urllib3',
        'unittest',
        'packaging',
        'requests'
    ]
    for path in delete_paths:
        full_path = os.path.join('dist\\library', path)
        if os.path.exists(full_path):
            shutil.rmtree(full_path, ignore_errors=True)

    os.chdir('dist\\library')
    cmd = f'{SZ_EXE} a -tzip -mm=Deflate -mfb=258 -mpass=7 -bso0 -bsp0 ..\\library.zip * -r'
    run_cmd(cmd)
    os.chdir('..\\..')
    file_size_new = os.path.getsize('dist\\library.zip')
    file_size_diff = file_size_old - file_size_new
    logger.info('Recompression of library.zip reduced size by %s from %s to %s',
                f'{file_size_diff:,}', f'{file_size_old:,}', f'{file_size_new:,}')
    shutil.rmtree('dist\\library', ignore_errors=True)
    assert_exist('dist\\library.zip')


def shrink(fast_build):
    """After building, run all applicable size optimizations"""
    delete_unnecessary()
    clean_translations()
    try:
        remove_empty_dirs('dist')
    except PermissionError:
        logger.error('Permission denied removing empty directories in dist: check for files locked by other process')
    upx(fast_build)
    delete_linux_only()
    recompress_library(fast_build)

    logger.info('Final size of the dist folder: %s', f'{get_dir_size("dist"):,}')


# ---------------------------------------------------------------------------
# Packaging
# ---------------------------------------------------------------------------

def package_portable(fast_build):
    """Package the portable version"""
    logger.info('Building portable TUI')
    copy_tree('dist', PORTABLE_DIR)
    with open(f"{PORTABLE_DIR}\\BleachBit.ini", "w", encoding=SetupEncoding) as text_file:
        text_file.write("[Portable]")

    archive(PORTABLE_DIR,
            f'BleachBit-TUI-{get_version()}-portable.zip', fast_build)


def nsis(opts, exe_name, nsi_path):
    """Run NSIS with the options to build exe_name"""
    if os.path.exists(exe_name):
        logger.info('Deleting old file: %s', exe_name)
        os.remove(exe_name)
    cmd = f'{NSIS_EXE} {opts} /DVERSION={get_version()} {nsi_path}'
    run_cmd(cmd)
    assert_exist(exe_name)


def package_installer(fast_build, nsi_path=r'windows\bleachbit_tui.nsi'):
    """Package the installer"""

    if not os.path.exists(NSIS_EXE):
        logger.warning('NSIS not found, so not building installer')
        return

    logger.info('Building TUI installer')

    write_nsis_expressions_to_files()

    exe_name = f'windows\\BleachBit-TUI-{get_version()}-setup.exe'
    opts = '' if fast_build else '/V3 /Dpackhdr /DCompressor'
    nsis(opts, exe_name, nsi_path)

    sign_files((exe_name,))


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    """Main function"""
    start_time = time.time()
    logger.info('BleachBit TUI version %s', get_version())
    environment_check()
    fast_build = len(sys.argv) > 1 and sys.argv[1] == 'fast'
    build()
    shrink(fast_build)
    package_portable(fast_build)
    package_installer(fast_build)
    os.system(r'dir *.zip windows\*.exe windows\*.zip')
    duration = time.time() - start_time
    minutes = int(duration // 60)
    seconds = int(duration % 60)
    logger.info('%s success! Duration: %d minutes, %d seconds',
                __file__, minutes, seconds)


if '__main__' == __name__:
    if len(sys.argv) == 1 or 'py2exe' not in sys.argv:
        sys.argv.append('py2exe')
    main()
