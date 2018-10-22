"""
BleachBit
Copyright (C) 2008-2018 Andrew Ziem
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
"""

from __future__ import absolute_import, print_function

import fnmatch
import glob
import imp
import logging
import os
import shlex
import shutil
import subprocess
import sys

logger = logging.getLogger('setup_py2exe')
logger.setLevel(logging.INFO)
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
formatter = logging.Formatter(
    "%(asctime)s - %(levelname)s - %(message)s", "%Y-%m-%d %H:%M:%S")
ch.setFormatter(formatter)
logger.addHandler(ch)

fast = False
if len(sys.argv) > 1 and sys.argv[1] == 'fast':
    logger.info('Fast build')
    fast = True


ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
logger.info('ROOT_DIR ' + ROOT_DIR)
sys.path.append(ROOT_DIR)

BB_VER = None
GTK_DIR = 'C:\\Python27\\Lib\\site-packages\\gtk-2.0\\runtime'
NSIS_EXE = 'C:\\Program Files (x86)\\NSIS\\makensis.exe'
NSIS_ALT_EXE = 'C:\\Program Files\\NSIS\\makensis.exe'
if not os.path.exists(NSIS_EXE) and os.path.exists(NSIS_ALT_EXE):
    logger.info('NSIS found in alternate location: ' + NSIS_ALT_EXE)
    NSIS_EXE = NSIS_ALT_EXE
SZ_EXE = 'C:\\Program Files\\7-Zip\\7z.exe'
# maximum compression with maximum compatibility
# mm=deflate method because deflate64 not widely supported
# mpass=passes for deflate encoder
# mfb=number of fast bytes
# bso0 bsp0 quiet output
SZ_OPTS = '-tzip -mm=Deflate -mfb=258 -mpass=7 -bso0 -bsp0'  # best compression
if fast:
    # fast compression
    SZ_OPTS = '-tzip -mx=1 -bso0 -bsp0'
UPX_EXE = ROOT_DIR + '\\upx394w\\upx.exe'
UPX_OPTS = '--best --crp-ms=999999 --nrv2e'


def archive(infile, outfile):
    assert_exist(infile)
    if os.path.exists(outfile):
        logger.warning(
            'Deleting output archive that already exists: ' + outfile)
        os.remove(outfile)
    cmd = '{} a {} {} {}'.format(SZ_EXE, SZ_OPTS, outfile, infile)
    run_cmd(cmd)
    assert_exist(outfile)


def recursive_glob(rootdir, patterns):
    return [os.path.join(looproot, filename)
            for looproot, _, filenames in os.walk(rootdir)
            for filename in filenames
            if any(fnmatch.fnmatch(filename, pattern) for pattern in patterns)]


def assert_exist(path, msg=None):
    if not os.path.exists(path):
        logger.error(path + ' not found')
        if msg:
            logger.error(msg)
        sys.exit(1)


def check_exist(path, msg=None):
    if not os.path.exists(path):
        logger.warning(path + ' not found')
        if msg:
            logger.warning(msg)
        import time
        time.sleep(5)


def assert_module(module):
    try:
        imp.find_module(module)
    except ImportError:
        logger.error('Failed to import ' + module)
        logger.error('Process aborted because of error!')
        sys.exit(1)


def assert_execute(args, expected_output):
    """Run a command and check it returns the expected output"""
    actual_output = subprocess.check_output(args)
    if -1 == actual_output.find(expected_output):
        raise RuntimeError('When running command {} expected output {} but got {}'.format(
            args, expected_output, actual_output))


def assert_execute_console():
    """Check the application starts"""
    logger.info('Checking bleachbit_console.exe starts')
    assert_execute([r'dist\bleachbit_console.exe', '--gui', '--exit', '--no-uac'],
                   'Success')


def run_cmd(cmd):
    logger.info(cmd)
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE,
                         stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = p.communicate()
    logger.info(stdout)
    if stderr:
        logger.error(stderr)


def sign_code(filename):
    if os.path.exists('CodeSign.bat'):
        logger.info('Signing code: %s' % filename)
        cmd = 'CodeSign.bat %s' % filename
        run_cmd(cmd)
    else:
        logger.warning('CodeSign.bat not available for %s' % filename)


def get_dir_size(start_path='.'):
    # http://stackoverflow.com/questions/1392413/calculating-a-directory-size-using-python
    total_size = 0
    for dirpath, dirnames, filenames in os.walk(start_path):
        for f in filenames:
            fp = os.path.join(dirpath, f)
            total_size += os.path.getsize(fp)
    return total_size


def copytree(src, dst):
    # Microsoft xcopy is about twice as fast as shutil.copytree
    logger.info('copying {} to {}'.format(src, dst))
    cmd = 'xcopy {} {} /i /s /q'.format(src, dst)
    os.system(cmd)


def count_size_improvement(func):
    def wrapper():
        import time
        t0 = time.time()
        size0 = get_dir_size('dist')
        func()
        size1 = get_dir_size('dist')
        t1 = time.time()
        logger.info('Reduced size of the dist directory by {:,} B from {:,} B to {:,} B in {:.1f} s'.format(
            size0 - size1, size0, size1, t1 - t0))
    return wrapper


def environment_check():
    """Check the build environment"""
    logger.info('Checking for translations')
    assert_exist('locale', 'run "make -C po local" to build translations')

    logger.info('Checking for GTK')
    assert_exist(GTK_DIR)

    logger.info('Checking PyGTK+ library')
    assert_module('pygtk')

    logger.info('Checking Python win32 library')
    assert_module('win32file')

    logger.info('Checking for CodeSign.bat')
    check_exist('CodeSign.bat', 'Code signing is not available')

    logger.info('Checking for NSIS')
    check_exist(
        NSIS_EXE, 'NSIS executable not found: will try to build portable BleachBit')


def build():
    """Build the application"""
    logger.info('Deleting directories build and dist')
    shutil.rmtree('build', ignore_errors=True)
    shutil.rmtree('dist', ignore_errors=True)
    shutil.rmtree('BleachBit-Portable', ignore_errors=True)

    logger.info('Running py2exe')
    shutil.copyfile('bleachbit.py', 'bleachbit_console.py')
    cmd = sys.executable + ' -OO setup.py py2exe'
    run_cmd(cmd)
    assert_exist('dist\\bleachbit.exe')
    assert_exist('dist\\bleachbit_console.exe')
    os.remove('bleachbit_console.py')

    if not os.path.exists('dist'):
        os.makedirs('dist')

    logger.info('Copying GTK files and icon')
    shutil.copyfile(GTK_DIR + '\\bin\\intl.dll',  'dist\\intl.dll')

    copytree(GTK_DIR + '\\etc', 'dist\\etc')
    copytree(GTK_DIR + '\\lib', 'dist\\lib')
    copytree(GTK_DIR + '\\share', 'dist\\share')
    shutil.copyfile('bleachbit.png',  'dist\\share\\bleachbit.png')

    logger.info('Copying BleachBit localizations')
    shutil.rmtree('dist\\share\\locale', ignore_errors=True)
    copytree('locale', 'dist\\share\\locale')
    assert_exist('dist\\share\\locale\\es\\LC_MESSAGES\\bleachbit.mo')

    logger.info('Copying BleachBit cleaners')
    if not os.path.exists('dist\\share\\cleaners'):
        os.makedirs('dist\\share\\cleaners')
    cleaners_files = recursive_glob('cleaners', ['*.xml'])
    for file in cleaners_files:
        shutil.copy(file,  'dist\\share\\cleaners')

    logger.info('Checking for CleanerML')
    assert_exist('dist\\share\\cleaners\\internet_explorer.xml')

    sign_code('dist\\bleachbit.exe')
    sign_code('dist\\bleachbit_console.exe')

    assert_execute_console()


@count_size_improvement
def delete_unnecessary():
    logger.info('Deleting unnecessary files')
    # Remove SVG to reduce space and avoid this error
    # Error loading theme icon 'dialog-warning' for stock: Unable to load image-loading module: C:/Python27/Lib/site-packages/gtk-2.0/runtime/lib/gdk-pixbuf-2.0/2.10.0/loaders/libpixbufloader-svg.dll: `C:/Python27/Lib/site-packages/gtk-2.0/runtime/lib/gdk-pixbuf-2.0/2.10.0/loaders/libpixbufloader-svg.dll': The specified module could not be found.
    # https://bugs.launchpad.net/bleachbit/+bug/1650907
    delete_paths = [
        r'_win32sysloader.pyd',
        r'bz2.pyd',
        r'etc\bash_completion.d',
        r'lib\GNU.Gettext.dll',
        r'lib\gdk-pixbuf-2.0',
        r'lib\glib-2.0',
        r'lib\gtk-2.0\include',
        r'lib\gtk-2.0\2.10.0\engines\libpixmap.dll',
        r'lib\gtk-2.0\2.10.0\engines\libsvg.dll',
        r'lib\gtk-2.0\modules\libgail.dll',
        r'lib\pkgconfig',
        r'perfmon.pyd',
        r'select.pyd',
        r'servicemanager.pyd',
        r'share\aclocal',
        r'share\doc',
        r'share\glib-2.0',
        r'share\gtk-2.0',
        r'share\gtk-doc',
        r'share\icon-naming-utils',
        r'share\icons\Tango\scalable',
        r'share\man',
        r'share\themes\default',
        r'share\themes\emacs',
        r'share\themes\raleigh',
        r'share\xml',
        r'win32evtlog.pyd',
        r'win32pipe.pyd',
        r'win32wnet.pyd',
    ]
    for path in delete_paths:
        path = r'dist\{}'.format(path)
        if not os.path.exists(path):
            logger.warning('Path does not exist: ' + path)
            continue
        if os.path.isdir(path):
            this_dir_size = get_dir_size(path)
            shutil.rmtree(path, ignore_errors=True)
            logger.info('Deleting directory {} saved {:,} B'.format(
                path, this_dir_size))
        else:
            logger.info('Deleting file {} saved {:,} B'.format(
                path, os.path.getsize(path)))
            os.remove(path)
    # by wildcard with recursive search
    delete_wildcards = [
        '*.a',
        '*.def',
        '*.lib',
        'atk10.mo',
        'gdk-pixbuf.mo',
        'gettext-runtime.mo',
        'glib20.mo',
        'gtk20-properties.mo',
        'libgsf.mo',
    ]
    for wc in delete_wildcards:
        total_size = 0
        for f in recursive_glob('dist', [wc]):
            total_size += os.path.getsize(f)
            os.remove(f)
        logger.info('Deleting wildcard {} saved {:,}B'.format(wc, total_size))


@count_size_improvement
def delete_icons():
    logger.info('Deleting unused PNG icons')
    # This whitelist comes from analyze_process_monitor_events.py
    png_whitelist = [
        'dialog-information.png',
        'dialog-warning.png',
        'edit-delete.png',
        'edit-find.png',
        'gtk-preferences.png',
    ]
    strip_list = recursive_glob(r'dist\share\icons', ['*.png'])
    for f in strip_list:
        if os.path.basename(f) not in png_whitelist:
            os.remove(f)


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
    logger.info('Stripping executables')
    strip_list = recursive_glob('dist', ['*.dll', '*.pyd'])
    strip_whitelist = []
    strip_files_str = [f for f in strip_list if os.path.basename(
        f) not in strip_whitelist]
    cmd = 'strip.exe --strip-debug --discard-all --preserve-dates ' + \
        ' '.join(strip_files_str)
    run_cmd(cmd)


@count_size_improvement
def upx():
    if fast:
        logger.warning('Fast mode: Skipped executable with UPX')
        return

    if not os.path.exists(UPX_EXE):
        logger.warning('To compress executables, install UPX to: ' + UPX_EXE)
        return

    logger.info('Compressing executables')
    upx_files = recursive_glob('dist', ['*.exe', '*.dll', '*.pyd'])
    cmd = '{} {} {}'.format(UPX_EXE, UPX_OPTS, ' '.join(upx_files))
    run_cmd(cmd)


@count_size_improvement
def delete_linux_only():
    logger.info('Checking for Linux-only cleaners')
    files = recursive_glob('dist/share/cleaners/', ['*.xml'])
    for fn in files:
        from bleachbit.CleanerML import CleanerML
        cml = CleanerML(fn)
        if not cml.get_cleaner().is_usable():
            logger.warning('Deleting cleaner not usable on this OS: ' + fn)
            os.remove(fn)


@count_size_improvement
def recompress_library():
    """Recompress library.zip"""
    if fast:
        logger.warning('Fast mode: Skipped recompression of library.zip')
        return

    if not os.path.exists(SZ_EXE):
        logger.warning(SZ_EXE + ' does not exist')
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
    delete_paths = ['distutils', 'email']
    for p in delete_paths:
        shutil.rmtree(os.path.join('dist', 'library', p))

    # recompress library.zip
    cmd = SZ_EXE + ' a {} ..\\library.zip'.format(SZ_OPTS)
    logger.info(cmd)
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE, cwd='dist\\library')
    stdout, stderr = p.communicate()
    logger.info(stdout)
    if stderr:
        logger.error(stderr)

    file_size_new = os.path.getsize('dist\\library.zip')
    file_size_diff = file_size_old - file_size_new
    logger.info('Recompression of library.dll reduced size by {:,} from {:,} to {:,}'.format(
        file_size_diff, file_size_old, file_size_new))
    shutil.rmtree('dist\\library', ignore_errors=True)
    assert_exist('dist\\library.zip')


def shrink():
    """After building, run all the applicable size optimizations"""
    delete_unnecessary()
    delete_icons()
    clean_translations()

    try:
        strip()
    except Exception:
        logger.exception(
            'Error when running strip. Does your PATH have MINGW with binutils?')

    if not fast:
        upx()
        assert_execute_console()

    logger.info('Purging unnecessary GTK+ files')
    # FIXME: move clean-dist into this program
    cmd = sys.executable + ' setup.py clean-dist'
    run_cmd(cmd)

    delete_linux_only()

    recompress_library()

    # so calculate the size of the folder, as it is a goal to shrink it.
    logger.info('Final size of the dist folder: {:,}'.format(
        get_dir_size('dist')))


def package_portable():
    """Package the portable version"""
    logger.info('Building portable')
    copytree('dist', 'BleachBit-Portable')
    with open("BleachBit-Portable\\BleachBit.ini", "w") as text_file:
        text_file.write("[Portable]")

    archive('BleachBit-Portable', 'BleachBit-{}-portable.zip'.format(BB_VER))

# NSIS


def nsis(opts, exe_name, nsi_path):
    """Run NSIS with the options to build exe_name"""
    if os.path.exists(exe_name):
        logger.info('Deleting old file: ' + exe_name)
        os.remove(exe_name)
    cmd = NSIS_EXE + \
        ' {} /DVERSION={} {}'.format(opts, BB_VER, nsi_path)
    run_cmd(cmd)
    assert_exist(exe_name)
    sign_code(exe_name)


def package_installer(nsi_path=r'windows\bleachbit.nsi'):
    """Package the installer"""

    if not os.path.exists(NSIS_EXE):
        logger.warning('NSIS not found, so not building installer')
        return

    logger.info('Building installer')
    exe_name = 'windows\\BleachBit-{0}-setup.exe'.format(BB_VER)
    opts = '' if fast else '/X"SetCompressor /FINAL zlib"'
    nsis(opts, exe_name, nsi_path)

    if not fast:
        nsis('/DNoTranslations',
             'windows\\BleachBit-{0}-setup-English.exe'.format(BB_VER),
             nsi_path)

    if os.path.exists(SZ_EXE):
        logger.info('Zipping installer')
        # Please note that the archive does not have the folder name
        outfile = ROOT_DIR + \
            '\\windows\\BleachBit-{0}-setup.zip'.format(BB_VER)
        infile = ROOT_DIR + '\\windows\\BleachBit-{0}-setup.exe'.format(BB_VER)
        archive(infile, outfile)
    else:
        logger.warning(SZ_EXE + ' does not exist')


if '__main__' == __name__:
    logger.info('Getting BleachBit version')
    import bleachbit
    BB_VER = bleachbit.APP_VERSION
    logger.info('BleachBit version ' + BB_VER)

    environment_check()
    build()
    shrink()
    package_portable()
    package_installer()
    # Clearly show the sizes of the files that end users download because the
    # goal is to minimize them.
    os.system(r'dir *.zip windows\*.exe windows\*.zip')
    logger.info('Success!')
