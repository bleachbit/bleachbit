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

import sys
import os
import logging
import imp
import shutil
import fnmatch

import subprocess
import shlex

logger = logging.getLogger( 'setup_py2exe' )
logger.setLevel(logging.INFO)
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
ch.setFormatter(formatter)
logger.addHandler(ch)



fast = False

if len(sys.argv) > 1 and  sys.argv[1] == 'fast':
    logger.info('Fast buid')
    fast = True


ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
logger.info('ROOT_DIR ' + ROOT_DIR)
sys.path.append( ROOT_DIR )



GTK_DIR  = 'C:\\Python27\\Lib\\site-packages\\gtk-2.0\\runtime'
NSIS_EXE = 'C:\\Program Files (x86)\\NSIS\\makensis.exe'
SZ_EXE   = 'C:\\Program Files\\7-Zip\\7z.exe'
UPX_EXE  = ROOT_DIR + '\\upx392w\\upx.exe'
UPX_OPTS = '--best --crp-ms=999999 --nrv2e'


def compress(UPX_EXE, UPX_OPTS, file):
    cmd= UPX_EXE + ' ' + UPX_OPTS + ' '+ file
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE )
    stdout, stderr = p.communicate()
    logger.info(stdout)
    if stderr :
        logger.error(stderr)


def recursive_glob(rootdir, patterns):
    return [os.path.join(looproot, filename)
            for looproot, _, filenames in os.walk(rootdir)
            for filename in filenames
            if any(fnmatch.fnmatch(filename, pattern) for pattern in patterns) ]


def assert_exist(path, msg=None):
    if not os.path.exists( path ):
        logger.error( path + ' not found')
        if msg:
            logger.error(msg)
        sys.exit(1)


def check_exist(path, msg=None):
    if not os.path.exists( path ):
        logger.warning( path + ' not found')
        if msg:
            logger.warning(msg)
        import time
        time.sleep(5)

def assert_module(module):
    try:
        imp.find_module( module )
    except ImportError:
        logger.error('Failed to import '+ module)
        logger.error('Process aborted because of error!')
        sys.exit(1)

def run_cmd(cmd):
    logger.info(cmd)
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE )
    stdout, stderr = p.communicate()
    logger.info(stdout)
    if stderr :
        logger.error(stderr)

def check_file_for_string(filename, string):
    with open(filename) as fin:
         return string in fin.read()



logger.info('Getting BleachBit version')
import bleachbit.Common
BB_VER = bleachbit.Common.APP_VERSION
logger.info('BleachBit version ' + BB_VER )


logger.info('Checking for translations')
assert_exist('locale', 'run "make -C po local" to build translations')

logger.info('Checking for GTK')
assert_exist(GTK_DIR)

logger.info('Checking PyGTK+ library')
assert_module('pygtk')

logger.info('Checking Python win32 library')
assert_module('win32file')

logger.info('Checking for UPX')
assert_exist(UPX_EXE, 'Download UPX executable from http://upx.sourceforge.net/')

logger.info('Checking for CodeSign.bat')
check_exist('CodeSign.bat', 'Code signing is not available')

logger.info('Checking for NSIS')
check_exist(NSIS_EXE, 'NSIS executable not found: will try to build portable BleachBit')


logger.info('Deleting directories build and dist')
shutil.rmtree( 'build', ignore_errors=True)
shutil.rmtree( 'dist', ignore_errors=True)
shutil.rmtree( 'BleachBit-portable', ignore_errors=True )


logger.info('Running py2exe')
shutil.copyfile('bleachbit.py', 'bleachbit_console.py')
cmd= sys.executable +  ' -OO setup.py py2exe'
run_cmd(cmd)
assert_exist('dist\\bleachbit.exe')
assert_exist('dist\\bleachbit_console.exe')
os.remove('bleachbit_console.py')


if not os.path.exists('dist'):
    os.makedirs('dist')

logger.info('Copying GTK files and icon')
shutil.copyfile( GTK_DIR + '\\bin\\intl.dll',  'dist\\intl.dll')

shutil.copytree(GTK_DIR + '\\etc', 'dist\\etc')
shutil.copytree(GTK_DIR + '\\lib', 'dist\\lib')
shutil.copytree(GTK_DIR + '\\share', 'dist\\share')
shutil.copyfile( 'bleachbit.png',  'dist\\share\\bleachbit.png')


logger.info('Compressing executables')
files = recursive_glob('dist', ['*.exe'])
for file in files:
    compress(UPX_EXE, UPX_OPTS, file)

#logger.info('Stripping executables')
#files = recursive_glob('dist', ['*.dll', '*.exe'])
#for file in files:
#    cmd = 'strip --strip-all ' + file
#    run_cmd(cmd)


logger.info('Purging unnecessary GTK+ files')
cmd= sys.executable +  ' setup.py clean-dist'
run_cmd(cmd)


logger.info('Copying BleachBit localizations')
shutil.rmtree('dist\\share\\locale', ignore_errors=True)
shutil.copytree('locale', 'dist\\share\\locale')
assert_exist( 'dist\\share\\locale\\es\\LC_MESSAGES\\bleachbit.mo' )

logger.info('Copying BleachBit cleaners')
if not os.path.exists( 'dist\\share\\cleaners'):
    os.makedirs( 'dist\\share\\cleaners')
cleaners_files = recursive_glob('cleaners', ['*.xml'])
for file in cleaners_files:
    shutil.copy( file,  'dist\\share\\cleaners')


logger.info('Checking for CleanerML')
assert_exist('dist\\share\\cleaners\\internet_explorer.xml')


logger.info('Checking for Linux-only cleaners')
if os.path.exists( 'dist\\share\\cleaners\\wine.xml'):
    files = recursive_glob('dist/share/cleaners/', ['*.xml'])
    for file in files:
        if check_file_for_string(file, 'os="linux"'):
            logger.warning('delete ' + file)
            os.remove( file )



logger.info('Signing code')
if os.path.exists('CodeSign.bat') :
    cmds = ['CodeSign.bat dist\\bleachbit.exe', 'CodeSign.bat dist\\bleachbit_console.exe']
    for c in cmds:
        run_cmd(c)
else:
    logger.error('CodeSign.bat not found')


logger.info('Building portable')
shutil.copytree('dist', 'BleachBit-portable')
with open("BleachBit-Portable\\BleachBit.ini", "w") as text_file:
    text_file.write( "[Portable]" )

cmd = SZ_EXE + '  a -mx=9  BleachBit-{0}-portable.zip BleachBit-portable'.format(BB_VER)
run_cmd(cmd)


if not fast:
    logger.info('Recompressing library.zip with 7-Zip')
    if not os.path.exists( SZ_EXE ) :
        logger.warning(SZ_EXE + ' does not exist')
    else:
        if not os.path.exists( 'dist\\library' ):
            os.makedirs( 'dist\\library' )
        cmd = SZ_EXE + ' x  dist\\library.zip' + ' -odist\\library  -y'
        logger.info( cmd )
        run_cmd(cmd)
        file_size = os.path.getsize( 'dist\\library.zip' ) / (1024*1024.0)
        logger.info( 'Size before 7zip recompression ' + str( file_size ) + ' Mb')
        shutil.rmtree('dist\\library.zip', ignore_errors=True)

        cmd = SZ_EXE + '  a -tzip -mx=9 -mfb=255 ..\\library.zip'
        logger.info( cmd )
        p = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd='dist\\library')
        stdout, stderr = p.communicate()
        logger.info(stdout)
        if stderr :
            logger.error(stderr)

        file_size = os.path.getsize( 'dist\\library.zip' ) / (1024*1024.0)
        logger.info( 'Size after 7zip recompression ' + str( file_size ) + ' Mb')
        shutil.rmtree( 'dist\\library', ignore_errors=True )
        assert_exist( 'dist\\library.zip')
else:
    logger.warning( 'Skip Recompressing library.zip with 7-Zip' )


# NSIS
logger.info( 'Building installer' )
if not fast:
    cmd = NSIS_EXE + ' /X"SetCompressor /FINAL zlib" /DVERSION={0} windows\\bleachbit.nsi'.format(BB_VER)
    run_cmd(cmd)
else:
    cmd = NSIS_EXE + ' /DVERSION={0} windows\\bleachbit.nsi'.format(BB_VER)
    run_cmd(cmd)

if os.path.exists('CodeSign.bat') :
    logger.info( 'Signing code' )
    cmd = 'CodeSign.bat windows\\BleachBit-{0}-setup.exe'.format(BB_VER)
    run_cmd(cmd)
else:
    logger.error('CodeSign.bat not found')


if not fast:
    cmd = NSIS_EXE + ' /DNoTranslations /DVERSION={0} windows\\bleachbit.nsi'.format(BB_VER)
    run_cmd(cmd)
    if os.path.exists('CodeSign.bat') :
        logger.info( 'Signing code' )
        cmd = 'CodeSign.bat windows\\BleachBit-{0}-setup-English.exe'.format(BB_VER)
        run_cmd(cmd)


if os.path.exists( SZ_EXE ) :
    logger.info( 'Zipping installer' )
    #Please note that the archive does not have the folder name
    outfile = ROOT_DIR +'\\windows\\BleachBit-{0}-setup.zip'.format(BB_VER)
    infile  = ROOT_DIR +'\\windows\\BleachBit-{0}-setup.exe'.format(BB_VER)
    assert_exist(infile)
    cmd = SZ_EXE + ' a -mx=9  ' + outfile + ' ' + infile
    run_cmd(cmd)
else:
    logger.warning(SZ_EXE + ' does not exist')

logger.info( 'Success!' )
