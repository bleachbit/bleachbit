"""
BleachBit
Copyright (C) 2008-2016 Andrew Ziem
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
    "%(asctime)s - %(name)s - %(levelname)s - %(message)s")
ch.setFormatter(formatter)
logger.addHandler(ch)


fast = False

if len(sys.argv) > 1 and sys.argv[1] == 'fast':
    logger.info('Fast buid')
    fast = True


ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
logger.info('ROOT_DIR ' + ROOT_DIR)
sys.path.append(ROOT_DIR)


GTK_DIR = 'C:\\Python27\\Lib\\site-packages\\gtk-2.0\\runtime'
NSIS_EXE = 'C:\\Program Files (x86)\\NSIS\\makensis.exe'
NSIS_ALT_EXE = 'C:\\Program Files\\NSIS\\makensis.exe'
if not os.path.exists(NSIS_EXE) and os.path.exists(NSIS_ALT_EXE):
    logger.info('NSIS found in alternate location:' + NSIS_ALT_EXE)
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
UPX_EXE = ROOT_DIR + '\\upx392w\\upx.exe'
UPX_OPTS = '--best --crp-ms=999999 --nrv2e'


def compress(UPX_EXE, UPX_OPTS, file):
    cmd = UPX_EXE + ' ' + UPX_OPTS + ' ' + file
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE,
                         stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = p.communicate()
    logger.info(stdout)
    if stderr:
        logger.error(stderr)


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


def run_cmd(cmd):
    logger.info(cmd)
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE,
                         stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = p.communicate()
    logger.info(stdout)
    if stderr:
        logger.error(stderr)


def check_file_for_string(filename, string):
    with open(filename) as fin:
        return string in fin.read()


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

logger.info('Getting BleachBit version')
import bleachbit.Common
BB_VER = bleachbit.Common.APP_VERSION
logger.info('BleachBit version ' + BB_VER)


logger.info('Checking for translations')
assert_exist('locale', 'run "make -C po local" to build translations')

logger.info('Checking for GTK')
assert_exist(GTK_DIR)

logger.info('Checking PyGTK+ library')
assert_module('pygtk')

logger.info('Checking Python win32 library')
assert_module('win32file')

logger.info('Checking for UPX')
assert_exist(
    UPX_EXE, 'Download UPX executable from http://upx.sourceforge.net/')

logger.info('Checking for CodeSign.bat')
check_exist('CodeSign.bat', 'Code signing is not available')

logger.info('Checking for NSIS')
check_exist(
    NSIS_EXE, 'NSIS executable not found: will try to build portable BleachBit')


logger.info('Deleting directories build and dist')
shutil.rmtree('build', ignore_errors=True)
shutil.rmtree('dist', ignore_errors=True)
shutil.rmtree('BleachBit-portable', ignore_errors=True)


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

shutil.copytree(GTK_DIR + '\\etc', 'dist\\etc')
shutil.copytree(GTK_DIR + '\\lib', 'dist\\lib')
shutil.copytree(GTK_DIR + '\\share', 'dist\\share')
shutil.copyfile('bleachbit.png',  'dist\\share\\bleachbit.png')


logger.info('Deleting unnecessary files')
old_dir_size = get_dir_size('dist')
# Remove SVG to reduce space and avoid this error
# Error loading theme icon 'dialog-warning' for stock: Unable to load image-loading module: C:/Python27/Lib/site-packages/gtk-2.0/runtime/lib/gdk-pixbuf-2.0/2.10.0/loaders/libpixbufloader-svg.dll: `C:/Python27/Lib/site-packages/gtk-2.0/runtime/lib/gdk-pixbuf-2.0/2.10.0/loaders/libpixbufloader-svg.dll': The specified module could not be found.
# https://bugs.launchpad.net/bleachbit/+bug/1650907
delete_dirs = [
    r'dist\lib\gdk-pixbuf-2.0',
    r'dist\lib\glib-2.0',
    r'dist\lib\pkgconfig',
    r'dist\share\doc',
    r'dist\share\gtk-doc',
    r'dist\share\icons\Tango\scalable',
    r'dist\share\man',
]
for delete_dir in delete_dirs:
    if not os.path.exists(delete_dir):
        logger.warning('Directory does not exist: ' + delete_dir)
        continue
    this_dir_size = get_dir_size(delete_dir)
    shutil.rmtree(delete_dir, ignore_errors=True)
    logger.info('Deleting directory {} saved {:,}B'.format(
        delete_dir, this_dir_size))
delete_globs = [
    '*.a',
    '*.def',
    '*.lib'
]
for glob in delete_globs:
    total_size = 0
    for f in recursive_glob('dist', [glob]):
        total_size += os.path.getsize(f)
        os.remove(f)
    logger.info('Deleting glob {} saved {:,}B'.format(glob, total_size))
# unsupported translations
os.remove(r'dist\share\locale\locale.alias')
pygtk_translations = os.listdir('dist/share/locale')
supported_translations = [f[3:-3] for f in glob.glob('po/*.po')]
translations_size = 0
for pt in pygtk_translations:
    if pt not in supported_translations:
        path = 'dist/share/locale/'+pt
        translations_size += get_dir_size(path)
        shutil.rmtree(path)
logger.info('Deleting unsupported translations saved {:,}B'.format(translations_size))
new_dir_size = get_dir_size('dist')
dir_size_diff = old_dir_size - new_dir_size
logger.info('Reduced size of the dist directory by {:,} from {:,} to {:,}'.format(
    dir_size_diff, old_dir_size, new_dir_size))

logger.info('Compressing executables')
files = recursive_glob('dist', ['*.exe'])
for file in files:
    compress(UPX_EXE, UPX_OPTS, file)

#logger.info('Stripping executables')
#files = recursive_glob('dist', ['*.dll', '*.exe'])
# for file in files:
#    cmd = 'strip --strip-all ' + file
#    run_cmd(cmd)


logger.info('Purging unnecessary GTK+ files')
cmd = sys.executable + ' setup.py clean-dist'
run_cmd(cmd)


logger.info('Copying BleachBit localizations')
shutil.rmtree('dist\\share\\locale', ignore_errors=True)
shutil.copytree('locale', 'dist\\share\\locale')
assert_exist('dist\\share\\locale\\es\\LC_MESSAGES\\bleachbit.mo')

logger.info('Copying BleachBit cleaners')
if not os.path.exists('dist\\share\\cleaners'):
    os.makedirs('dist\\share\\cleaners')
cleaners_files = recursive_glob('cleaners', ['*.xml'])
for file in cleaners_files:
    shutil.copy(file,  'dist\\share\\cleaners')


logger.info('Checking for CleanerML')
assert_exist('dist\\share\\cleaners\\internet_explorer.xml')


logger.info('Checking for Linux-only cleaners')
if os.path.exists('dist\\share\\cleaners\\wine.xml'):
    files = recursive_glob('dist/share/cleaners/', ['*.xml'])
    for file in files:
        if check_file_for_string(file, 'os="linux"'):
            logger.warning('delete ' + file)
            os.remove(file)


sign_code('dist\\bleachbit.exe')
sign_code('dist\\bleachbit_console.exe')

logger.info('Building portable')
shutil.copytree('dist', 'BleachBit-portable')
with open("BleachBit-Portable\\BleachBit.ini", "w") as text_file:
    text_file.write("[Portable]")

archive('BleachBit-portable', 'BleachBit-{}-portable.zip'.format(BB_VER))

if not fast:
    logger.info('Recompressing library.zip with 7-Zip')
    if not os.path.exists(SZ_EXE):
        logger.warning(SZ_EXE + ' does not exist')
    else:
        # extract library.zip
        if not os.path.exists('dist\\library'):
            os.makedirs('dist\\library')
        cmd = SZ_EXE + ' x  dist\\library.zip' + ' -odist\\library  -y'
        run_cmd(cmd)
        file_size_old = os.path.getsize('dist\\library.zip')
        os.remove('dist\\library.zip')

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
else:
    logger.warning('Skipped recompression library.zip with 7-Zip')


# NSIS
def nsis(opts, exe_name):
    if os.path.exists(exe_name):
        logger.info('Deleting old file: ' + exe_name)
        os.remove(exe_name)
    cmd = NSIS_EXE + \
        ' {} /DVERSION={} windows\\bleachbit.nsi'.format(opts, BB_VER)
    run_cmd(cmd)
    assert_exist(exe_name)
    sign_code(exe_name)

if not os.path.exists(NSIS_EXE):
    logger.warning('NSIS not found, so not building installer')
else:
    logger.info('Building installer')
    exe_name = 'windows\\BleachBit-{0}-setup.exe'.format(BB_VER)
    opts = '' if fast else '/X"SetCompressor /FINAL zlib"'
    nsis(opts, exe_name)

    if not fast:
        nsis('/DNoTranslations',
             'windows\\BleachBit-{0}-setup-English.exe'.format(BB_VER))

    if os.path.exists(SZ_EXE):
        logger.info('Zipping installer')
        # Please note that the archive does not have the folder name
        outfile = ROOT_DIR + \
            '\\windows\\BleachBit-{0}-setup.zip'.format(BB_VER)
        infile = ROOT_DIR + '\\windows\\BleachBit-{0}-setup.exe'.format(BB_VER)
        archive(infile, outfile)
    else:
        logger.warning(SZ_EXE + ' does not exist')

logger.info('Success!')
