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
  - Uses vanilla 64-bit Python (no 32-bit PyGTK constraint)
  - No GTK / PyGObject dependencies
  - Builds a single console executable (bleachbit_tui.exe)
  - No option for UPX compression

FIXME: stop duplicating code with windows/setup.py
"""

# Helpers are intentionally copied from windows/setup.py; see FIXME above.
# pylint: disable=duplicate-code

# standard library
import fnmatch
import glob
import importlib.util
import logging
import os
import shutil
import subprocess
import sys
import time

# third party
import certifi

# local import
import bleachbit
from setup import supported_languages
from bleachbit.CleanerML import CleanerML
from bleachbit.FileUtilities import children_in_directory
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
PORTABLE_DIR = 'BleachBit-Portable'


# ---------------------------------------------------------------------------
# Utility functions
# ---------------------------------------------------------------------------

def archive(infile, outfile, fast_build, store=False):
    """Create an archive from a file

    If store is enabled, the files are not compressed.
    """
    assert_exist(infile)
    if os.path.exists(outfile):
        logger.warning(
            'Deleting output archive that already exists: %s', outfile)
        os.remove(outfile)
    sz_opts = '-tzip -mm=Deflate -mfb=258 -mpass=7 -bso0 -bsp0'
    if store:
        sz_opts = '-tzip -mm=Copy -bso0 -bsp0'
    elif fast_build:
        sz_opts = '-tzip -mx=1 -bso0 -bsp0'
    cmd = f'{SZ_EXE} a {sz_opts} {outfile} {infile}'
    run_cmd(cmd)
    assert_exist(outfile)
    outfile_abs = os.path.abspath(outfile)
    outfile_size = os.path.getsize(outfile)
    logger.info('Created archive: %s (%s bytes)',
                outfile_abs, f'{outfile_size:,}')


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
    """Check if a path exists

    If not, log a warning and sleep for 5 seconds, except on CI."""
    if not os.path.exists(path):
        logger.warning('%s not found', path)
        if msg:
            logger.warning(msg)
        if not os.environ.get('GITHUB_ACTIONS'):
            time.sleep(5)


def assert_module(module):
    """Check if a module is available"""
    try:
        spec = importlib.util.find_spec(module)
    except ImportError:
        spec = None
    if spec is None:
        logger.error('Failed to import %s', module)
        logger.error('Process aborted because of error!')
        sys.exit(1)


def assert_execute(args, expected_output, timeout=120):
    """Run a command and check it returns the expected output.

    A timeout guards against hangs. On timeout, the child is killed
    and any captured output is logged to aid troubleshooting.
    """
    try:
        actual_output = subprocess.check_output(
            args, stderr=subprocess.STDOUT, timeout=timeout).decode(SetupEncoding)
    except subprocess.TimeoutExpired as e:
        partial = (e.output or b'').decode(SetupEncoding, errors='replace')
        logger.error('Command %s timed out after %ss. Partial output:\n%s',
                     args, timeout, partial)
        raise RuntimeError(f'Timeout running {args} after {timeout}s') from e
    except subprocess.CalledProcessError as e:
        output = (e.output or b'').decode(SetupEncoding, errors='replace')
        logger.error('Command %s failed with exit code %s. Output:\n%s',
                     args, e.returncode, output)
        raise
    if -1 == actual_output.find(expected_output):
        raise RuntimeError(
            f'When running command {args} expected output {expected_output} but got {actual_output}')


def assert_execute_console():
    """Check the application starts"""
    logger.info('Checking bleachbit_tui.exe starts')
    assert_execute([r'dist\bleachbit_tui.exe', '--sysinfo'],
                   'BleachBit version')


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
    """Get the size of a directory

    FileUtilities.getsizedir() is not used because it prepends the
    extended-length prefix, which Windows rejects on the relative paths
    used here.
    """
    return sum(os.path.getsize(fn) for fn in children_in_directory(start_path))


def copy_file(src, dst):
    """Copy a file. dst must be a full path."""
    assert_exist(src)
    dst_dirname = os.path.dirname(dst)
    if dst_dirname and not os.path.exists(dst_dirname):
        os.makedirs(dst_dirname)
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
    assert_exist(src)
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
    assert 64 == bleachbit.ARCH_BITS, \
        f'Expected 64-bit Python, got {bleachbit.ARCH_BITS}-bit'

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
        'compressed': 0,  # stored, so imports skip inflate
        'optimize': 2,
        'packages': ['charset_normalizer', 'encodings', 'textual', 'rich', 'rich._unicode_data',
                     'markdown_it', 'mdurl', 'linkify_it'],
        'excludes': ['pyreadline', 'difflib', 'doctest', 'pickle', 'ftplib',
                     'unittest', 'test',
                     'multiprocessing',
                     'concurrent.futures.process',
                     'chardet',  # not present now, but defensive
                     'xmlrpc',  # only consumer was multiprocessing.connection
                     # non-Windows platform modules
                     'psutil._psaix', 'psutil._psbsd', 'psutil._pslinux',
                     'psutil._psosx', 'psutil._pssunos',
                     'setuptools', 'tomli', 'wheel', 'backports',
                     'importlib_metadata', 'zipp', 'packaging', 'distutils',
                     'gi', 'cairo', 'Gtk', 'Gdk', 'GLib',
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
    except PermissionError as e:
        logger.error(
            "Failed to freeze: %s; check that other process does not have files open", e)
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
                logger.error(
                    "Failed to delete %s: %s. Check that another process does not have the file locked.", dir_path, e)
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
        logger.error('Unsupported Python version')
        sys.exit(1)
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
            logger.error('%s not found', dll_name)
            sys.exit(1)

    # Protected path XML
    copy_file('share\\protected_path.xml', 'dist\\share\\protected_path.xml')

    sign_files(('dist\\bleachbit_tui.exe',))

    assert_execute_console()


# ---------------------------------------------------------------------------
# Size optimizations
# ---------------------------------------------------------------------------

@count_size_improvement
def delete_unnecessary():
    """Delete unnecessary files from dist/"""
    logger.info('Deleting unnecessary files')
    delete_paths = [
        r'_multiprocessing.pyd',
        r'_queue.pyd',
        r'_win32sysloader.pyd',
        r'perfmon.pyd',
        r'servicemanager.pyd',
        r'win32evtlog.pyd',
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
            logger.info('Deleting directory %s saved %s B',
                        path, f'{this_dir_size:,}')
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
def delete_linux_only():
    """Delete Linux-only cleaners to reduce size"""
    logger.info('Deleting Linux-only cleaners')
    files = recursive_glob('dist/share/cleaners/', ['*.xml'])
    for fn in files:
        cml = CleanerML(fn)
        if not cml.get_cleaner().is_usable():
            logger.info('Deleting cleaner not usable on this OS: %s', fn)
            os.remove(fn)


def repack_library(fast_build):
    """Prune library.zip and repack it stored, so imports skip inflate"""
    if fast_build:
        logger.warning('Fast mode: Skipped repack of library.zip')
        return
    if not os.path.exists(SZ_EXE):
        logger.warning('%s does not exist', SZ_EXE)
        return

    logger.info('Repacking library.zip with 7-Zip')

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
        'requests',
        'textual\\demo',
    ]
    for path in delete_paths:
        full_path = os.path.join('dist\\library', path)
        if os.path.exists(full_path):
            shutil.rmtree(full_path, ignore_errors=True)
    # bleachbit.Memory wipes Linux swap/free memory and is never used on
    # Windows (the 'memory' option is registered only on Linux).  Strip it
    # from the Windows build.  Safe because Cleaner.py imports it lazily.
    delete_files = ['bleachbit\\Memory.pyc']
    for path in delete_files:
        full_path = os.path.join('dist\\library', path)
        if os.path.exists(full_path):
            os.remove(full_path)

    # Prune unneeded codecs from the encodings package.
    encodings_keep_list = (
        '__init__', 'aliases',
        'cp*',  # every Windows ANSI codepage
        'utf_8', 'utf_8_sig',
        'utf_16', 'utf_16_le', 'utf_16_be',
        'utf_32', 'utf_32_le', 'utf_32_be',
        'latin_1', 'ascii', 'mbcs', 'charmap', 'iso8859_1',
        '_win_cp_codecs',  # required by encodings on Python 3.14+
        # Below are codecs used by standard library.
        'punycode', 'idna',
        'unicode_escape', 'raw_unicode_escape', 'unicode_internal',
        'hex_codec', 'base64_codec', 'zlib_codec', 'bz2_codec',
        'qp_codec', 'quopri_codec', 'uu_codec',
        'rot_13', 'palmos', 'oem', 'undefined',
    )
    encodings_files = glob.glob(os.path.join(
        'dist', 'library', 'encodings', '*.pyc'))
    encodings_deleted = 0
    for enc in encodings_files:
        stem = os.path.splitext(os.path.basename(enc))[0]
        if any(fnmatch.fnmatch(stem, pattern)
               for pattern in encodings_keep_list):
            continue
        encodings_deleted += 1
        try:
            os.remove(enc)
        except OSError as e:
            logger.warning('Failed to remove %s: %s', enc, e)
    logger.info('Deleted %d of %d files in dist\\library\\encodings',
                encodings_deleted, len(encodings_files))

    # remove .dist-info metadata directories
    for dist_info_dir in glob.glob(os.path.join('dist', 'library', '*.dist-info')):
        logger.info('Removing .dist-info directory: %s', dist_info_dir)
        shutil.rmtree(dist_info_dir)

    # remove empty directories
    remove_empty_dirs('dist\\library')

    os.chdir('dist\\library')
    archive('.', '..\\library.zip', fast_build, store=True)
    os.chdir('..\\..')
    file_size_new = os.path.getsize('dist\\library.zip')
    logger.info('library.zip changed size by %s from %s to %s',
                f'{file_size_new - file_size_old:+,}', f'{file_size_old:,}', f'{file_size_new:,}')
    shutil.rmtree('dist\\library', ignore_errors=True)
    assert_exist('dist\\library.zip')
    # Nothing else runs the exe after library.zip is rewritten
    assert_execute_console()


def shrink(fast_build):
    """After building, run all applicable size optimizations"""
    delete_unnecessary()
    clean_translations()
    try:
        remove_empty_dirs('dist')
    except PermissionError:
        logger.error(
            'Permission denied removing empty directories in dist: check for files locked by other process')
    delete_linux_only()
    repack_library(fast_build)

    logger.info('Final size of the dist folder: %s',
                f'{get_dir_size("dist"):,}')


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
    # /WX: treat NSIS warnings as errors
    cmd = f'{NSIS_EXE} /WX {opts} /DVERSION={get_version()} {nsi_path}'
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
    opts = '' if fast_build else '/V3 /DCompressor'
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
