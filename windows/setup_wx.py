"""
BleachBit wxWidgets Windows build script
Copyright (C) 2008-2025 Andrew Ziem
https://www.bleachbit.org

Example invocation (from parent directory):
    python3 -m windows.setup_wx
"""

from __future__ import absolute_import, print_function

import fnmatch
import glob
import importlib.util
import logging
import os
import shutil
import struct
import subprocess
import sys
import time

import certifi

import bleachbit
from bleachbit.CleanerML import CleanerML
from bleachbit.SystemInformation import get_version
from windows.NsisUtilities import write_nsis_expressions_to_files

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
formatter = logging.Formatter(
    "%(asctime)s - %(levelname)s - %(message)s", "%Y-%m-%d %H:%M:%S")
ch.setFormatter(formatter)
logger.addHandler(ch)
logger.propagate = False

SetupEncoding = sys.stdout.encoding or 'utf-8'

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
logger.info('ROOT_DIR %s', ROOT_DIR)
sys.path.append(ROOT_DIR)

NSIS_EXE = 'C:\\Program Files (x86)\\NSIS\\makensis.exe'
NSIS_ALT_EXE = 'C:\\Program Files\\NSIS\\makensis.exe'
if not os.path.exists(NSIS_EXE) and os.path.exists(NSIS_ALT_EXE):
    logger.info('NSIS found in alternate location: %s', NSIS_ALT_EXE)
    NSIS_EXE = NSIS_ALT_EXE
SZ_EXE = 'C:\\Program Files\\7-Zip\\7z.exe'


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
    run_7z(cmd)
    assert_exist(outfile)


def recursive_glob(rootdir, patterns):
    """Recursively search for files matching the given patterns"""
    return [os.path.join(looproot, filename)
            for looproot, _, filenames in os.walk(rootdir)
            for filename in filenames
            if any(fnmatch.fnmatch(filename, pattern) for pattern in patterns)]


def assert_exist(path, msg=None):
    """Check if a path exists"""
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

    A timeout guards against hangs (e.g., a GUI main loop not quitting).
    On timeout, the child is killed and any captured output is logged
    to aid troubleshooting.
    """
    try:
        actual_output = subprocess.check_output(
            args, stderr=subprocess.STDOUT, timeout=timeout).decode(SetupEncoding)
    except subprocess.TimeoutExpired as e:
        partial = (e.output or b'').decode(SetupEncoding, errors='replace')
        logger.error('Command %s timed out after %ss. Partial output:\n%s',
                     args, timeout, partial)
        raise RuntimeError(f'Timeout running {args} after {timeout}s') from e
    if -1 == actual_output.find(expected_output):
        raise RuntimeError(
            f'When running command {args} expected output {expected_output} '
            f'but got {actual_output}')


def assert_execute_console():
    """Check the application starts"""
    logger.info('Checking bleachbit_console_wx.exe starts')
    assert_execute([r'dist\bleachbit_console_wx.exe', '--sysinfo'],
                   'BleachBit version')


def run_cmd(cmd, check=True):
    """Run a command and log the output

    Return the exit code. If check is true, a non-zero exit code aborts.
    """
    logger.info(cmd)
    with subprocess.Popen(cmd, stdin=subprocess.PIPE,
                          stdout=subprocess.PIPE, stderr=subprocess.PIPE) as p:
        stdout, stderr = p.communicate()
        stdout_decoded = stdout.decode(SetupEncoding)
        stderr_decoded = stderr.decode(SetupEncoding)
        logger.info(stdout_decoded)
        if stderr_decoded:
            logger.error(stderr_decoded)
    if p.returncode and check:
        logger.error('Command exited with code %d', p.returncode)
        sys.exit(1)
    return p.returncode


def run_7z(cmd):
    """Run 7-Zip

    Exit code 1 is a warning, such as a locked file. Higher is fatal.
    """
    returncode = run_cmd(cmd, check=False)
    if returncode == 1:
        logger.warning('7-Zip exited with a warning')
    elif returncode:
        logger.error('7-Zip exited with code %d', returncode)
        sys.exit(1)


def get_dir_size(start_path='.'):
    """Get the size of a directory"""
    total_size = 0
    for dirpath, _dirnames, filenames in os.walk(start_path):
        for f in filenames:
            fp = os.path.join(dirpath, f)
            total_size += os.path.getsize(fp)
    return total_size


def copy_file(src, dst):
    """Copy a file"""
    assert_exist(src)
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
    assert_exist(src)
    logger.info('copying %s to %s', src, dst)
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
    logger.info('Checking for 64-bit Python')
    bits = 8 * struct.calcsize('P')
    if bits != 64:
        logger.error('Expected 64-bit Python, found %d-bit', bits)
        sys.exit(1)

    logger.info('Checking for translations')
    assert_exist('locale', 'run "make -C po local" to build translations')

    logger.info('Checking wxPython')
    assert_module('wx')

    logger.info('Checking py2exe')
    assert_module('py2exe')

    logger.info('Checking for 7-Zip')
    check_exist(SZ_EXE, '7-Zip executable not found')

    logger.info('Checking for NSIS')
    check_exist(
        NSIS_EXE, 'NSIS executable not found: will try to build portable BleachBit')


def build_py2exe():
    """Build executables using py2exe's freeze API"""
    from py2exe import freeze
    app_description = 'Delete unwanted data'

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

    gui_version_info = version_info.copy()
    console_version_info = version_info.copy()
    console_version_info['internal_name'] = f'{bleachbit.APP_NAME} Console'

    gui_target = {
        'script': 'bleachbit-wx.py',
        'icon_resources': [(1, 'windows/bleachbit.ico')],
        'version_info': gui_version_info
    }

    console_target = {
        'script': 'bleachbit_console_wx.py',
        'icon_resources': [(1, 'windows/bleachbit.ico')],
        'version_info': console_version_info
    }

    options = {
        'bundle_files': 3,
        'compressed': 0,     # Stored, so imports skip inflate
        'optimize': 2,
        'includes': ['wx', 'win32api', 'win32con'],
        'packages': [
            'wx', 'bleachbit.markovify', 'bleachbit.GUIwx',
            'charset_normalizer', 'encodings', 'requests', 'psutil', 'plyer'
        ],
        'excludes': [
            'pyreadline', 'difflib', 'doctest', 'pickle', 'ftplib',
            'bleachbit.Unix'
        ],
        'dll_excludes': [
            'CRYPT32.DLL', 'DNSAPI.DLL', 'IPHLPAPI.DLL', 'MPR.dll',
            'MSIMG32.DLL', 'MSWSOCK.dll', 'NSI.dll', 'PDH.DLL',
            'PSAPI.DLL', 'POWRPROF.dll', 'USP10.DLL', 'WINNSI.DLL',
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

    freeze(
        windows=[gui_target],
        console=[console_target],
        zipfile='library.zip',
        options=options,
        version_info=version_info
    )


def build():
    """Build the application"""
    logger.info('Deleting directories build and dist')
    shutil.rmtree('build', ignore_errors=True)
    shutil.rmtree('dist', ignore_errors=True)
    shutil.rmtree('BleachBit-Portable', ignore_errors=True)

    logger.info('Running py2exe')
    copy_file('bleachbit-wx.py', 'bleachbit_console_wx.py')
    build_py2exe()
    assert_exist('dist\\bleachbit-wx.exe')
    assert_exist('dist\\bleachbit_console_wx.exe')
    os.remove('bleachbit_console_wx.py')

    if not os.path.exists('dist'):
        os.makedirs('dist')

    os.makedirs(os.path.join('dist', 'share'), exist_ok=True)

    logger.info('Copying BleachBit cleaners')
    os.makedirs('dist\\share\\cleaners', exist_ok=True)
    for file in recursive_glob('cleaners', ['*.xml']):
        shutil.copy(file, 'dist\\share\\cleaners')
    assert_exist('dist\\share\\cleaners\\internet_explorer.xml')

    logger.info('Copying share files')
    copy_file('share\\app-menu.ui', 'dist\\share\\app-menu.ui')
    copy_file('share\\protected_path.xml', 'dist\\share\\protected_path.xml')

    logger.info('Copying license and icons')
    copy_file('COPYING', 'dist\\COPYING')
    copy_file('windows\\bleachbit.ico', 'dist\\share\\bleachbit.ico')
    copy_file('bleachbit.png', 'dist\\share\\bleachbit.png')

    logger.info('Copying CA bundle')
    copy_file(certifi.where(), os.path.join('dist', 'cacert.pem'))

    logger.info('Copying BleachBit localizations')
    dist_locale_dir = r'dist\share\locale'
    os.makedirs(dist_locale_dir, exist_ok=True)
    copy_tree('locale', dist_locale_dir)
    assert_exist(os.path.join(dist_locale_dir, r'es\LC_MESSAGES\bleachbit.mo'))

    logger.info('Copying runtime DLL')
    python_version = sys.version_info[:2]
    if python_version >= (3, 10):
        dll_name = 'vcruntime140.dll'
    else:
        logger.error('Unsupported Python version')
        sys.exit(1)
    dll_dirs = (sys.prefix, r'c:\windows\system32')
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

    assert_execute_console()


@count_size_improvement
def delete_unnecessary():
    """Delete unnecessary files"""
    logger.info('Deleting unnecessary files')
    delete_paths = [
        r'_win32sysloader.pyd',
        r'perfmon.pyd',
        r'servicemanager.pyd',
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
            logger.info('Deleting directory %s saved %s B', path, f'{this_dir_size:,}')
        else:
            file_size = os.path.getsize(path)
            logger.info('Deleting file %s saved %s B', path, f'{file_size:,}')
            os.remove(path)


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
    dist_translations = os.listdir('dist/share/locale')
    supported_translations = [f[3:-3] for f in glob.glob('po/*.po')]
    for pt in dist_translations:
        if pt not in supported_translations:
            path = 'dist/share/locale/' + pt
            if os.path.exists(path):
                logger.info('Removing unsupported translation: %s', path)
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


@count_size_improvement
def repack_library(fast_build):
    """Prune library.zip and repack it stored, so imports skip inflate"""
    if fast_build:
        logger.warning('Fast mode: Skipped repacking of library.zip')
        return
    if not os.path.exists(SZ_EXE):
        logger.warning('%s does not exist', SZ_EXE)
        return
    logger.info('Repacking library.zip with 7-Zip')
    if not os.path.exists('dist\\library'):
        os.makedirs('dist\\library')
    cmd = SZ_EXE + ' x  dist\\library.zip' + ' -odist\\library  -y'
    run_7z(cmd)
    file_size_old = os.path.getsize('dist\\library.zip')
    os.remove('dist\\library.zip')
    delete_paths = ['distutils', 'plyer\\platforms\\android',
                    'plyer\\platforms\\ios', 'plyer\\platforms\\linux', 'plyer\\platforms\\macosx']
    for p in delete_paths:
        path = os.path.join('dist', 'library', p)
        if os.path.exists(path):
            shutil.rmtree(path)
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
    """After building, run all the applicable size optimizations"""
    delete_unnecessary()
    clean_translations()
    remove_empty_dirs('dist')
    delete_linux_only()
    repack_library(fast_build)
    logger.info('Final size of the dist folder: %s',
                f'{get_dir_size("dist"):,}')


def package_portable(fast_build):
    """Package the portable version"""
    logger.info('Building portable')
    copy_tree('dist', 'BleachBit-Portable')
    with open("BleachBit-Portable\\BleachBit.ini", "w", encoding=SetupEncoding) as text_file:
        text_file.write("[Portable]")
    archive('BleachBit-Portable',
            f'BleachBit-wx-{get_version()}-portable.zip', fast_build)


def nsis(opts, exe_name, nsi_path):
    """Run NSIS with the options to build exe_name"""
    if os.path.exists(exe_name):
        logger.info('Deleting old file: %s', exe_name)
        os.remove(exe_name)
    # /WX: treat NSIS warnings as errors
    cmd = f'{NSIS_EXE} /WX {opts} /DVERSION={get_version()} {nsi_path}'
    run_cmd(cmd)
    assert_exist(exe_name)


def package_installer(fast_build, nsi_path=r'windows\bleachbit-wx.nsi'):
    """Package the installer"""
    assert isinstance(fast_build, bool)
    assert isinstance(nsi_path, str)

    if not os.path.exists(NSIS_EXE):
        logger.warning('NSIS not found, so not building installer')
        return

    logger.info('Building installer')
    write_nsis_expressions_to_files()
    exe_name = f'windows\\BleachBit-wx-{get_version()}-setup.exe'
    opts = '' if fast_build else '/V3'
    nsis(opts, exe_name, nsi_path)

    if os.path.exists(SZ_EXE):
        logger.info('Zipping installer')
        outfile = f"{ROOT_DIR}\\windows\\BleachBit-wx-{get_version()}-setup.zip"
        infile = f"{ROOT_DIR}\\windows\\BleachBit-wx-{get_version()}-setup.exe"
        archive(infile, outfile, fast_build)
    else:
        logger.warning('%s does not exist', SZ_EXE)


def main():
    """Main function"""
    start_time = time.time()
    logger.info('BleachBit version %s', get_version())
    environment_check()
    fast_build = len(sys.argv) > 1 and sys.argv[1] == 'fast'
    build()
    shrink(fast_build)
    package_portable(fast_build)
    package_installer(fast_build)
    subprocess.run(
        ['cmd', '/c', 'dir', '*.zip', r'windows\*.exe', r'windows\*.zip'],
        check=False)
    duration = time.time() - start_time
    minutes = int(duration // 60)
    seconds = int(duration % 60)
    logger.info('%s success! Duration: %d minutes, %d seconds',
                __file__, minutes, seconds)


if '__main__' == __name__:
    if len(sys.argv) == 1 or 'py2exe' not in sys.argv:
        sys.argv.append('py2exe')
    main()
