<#
Install Python and GTK development and build environment for BleachBit on Windows.
This is a special version built for BleachBit.
It installs in a portable style.
This script may be run in an empty directory like `c:\projects`.

Afterwards, launch the application like this:
  c:\projects\x86-windows\tools\python3\python.exe c:\projects\bleachbit\bleachbit.py

This assumes that the BleachBit source code is in `c:\projects\bleachbit` and PyGTK
is installed in `c:\projects\pygtk`, but either directory can be relocated.

Copyright (C) 2008-2025 Andrew Ziem

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
#>

# Harden PowerShell execution and networking
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
try { [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12 } catch {}

$work_dir = (Get-Location).Path
$root_dir = Join-Path (Get-Location).Path "vcpkg_installed\x86-windows"
$python_home = Join-Path $root_dir "tools\python3"
$themes_dir = Join-Path $python_home "share\themes"
# location of this .ps1 script
$script_dir = Split-Path -Parent $MyInvocation.MyCommand.Path
$base_download_url = "https://github.com/bleachbit/pygtkwin/releases/download/v2025-02-15/"

# Set PATH to a minimal baseline with optional Python entries.
function Set-MinimalPath {
    param([switch]$IncludePython)
    $paths = @()
    if ($env:SystemRoot) {
        $paths += @("$env:SystemRoot", "$env:SystemRoot\System32")
    } else {
        $paths += @('C:\Windows','C:\Windows\System32')
    }
    if ($IncludePython) {
        $paths = @("$python_home","$python_home\Scripts", "$root_dir\tools\gtk3") + $paths
    }
    $env:PATH = ($paths -join ';')
    Write-Host ("PATH set to: {0}" -f $env:PATH)
}

# Start with a minimal PATH for the script, without Python.
Set-MinimalPath

# Visual C++ Redistributable 2015 x86
$VC_REDIST_FN = "VC_redist.x86.exe"
$VC_REDIST_URL = "https://aka.ms/vs/17/release/vc_redist.x86.exe"
# Reminder: Prefer absolute paths.
$VC_REDIST_PATH = Join-Path $work_dir $VC_REDIST_FN
if ($env:APPVEYOR -ne $true) {
    if (-not (Test-Path $VC_REDIST_PATH)) {
        Write-Host "Downloading Visual C++ Redistributable..."
        Invoke-WebRequest -Uri $VC_REDIST_URL -OutFile $VC_REDIST_PATH
        Get-FileHash -Path $VC_REDIST_PATH -Algorithm SHA256 | Format-List
        $fileSizeMB = (Get-Item $VC_REDIST_PATH).Length / 1MB
        if ($fileSizeMB -lt 5) {
            Write-Warning "The downloaded Visual C++ Redistributable file is smaller than expected (< 5MB). Please verify its integrity."
        }
        # Verify Authenticode is signed by Microsoft
        $sig = Get-AuthenticodeSignature -FilePath $VC_REDIST_PATH
        Write-Host ("Authenticode signer: {0}; status: {1}" -f $sig.SignerCertificate.Subject, $sig.Status)
        if ($sig.Status -ne 'Valid' -or $sig.SignerCertificate.Subject -notmatch 'Microsoft') {
            Write-Error "Invalid Authenticode signature on $VC_REDIST_PATH"
            exit 1
        }
    } else {
        Write-Host "Visual C++ Redistributable is already downloaded."
    }
    if (-not (Test-Path "C:\Windows\SysWOW64\vcruntime140.dll")) {
        Write-Host "Installing Visual C++ Redistributable..."
        Write-Host "Tip: If this step seems to freeze, press ALT+TAB to check for the UAC dialog."
        Start-Process -FilePath $VC_REDIST_PATH -ArgumentList "/install", "/quiet", "/norestart" -Wait
    } else {
        Write-Host "Visual C++ Redistributable is already installed."
    }
} else {
    Write-Host "Skipping Visual C++ Redistributable installation in AppVeyor environment."
}

# Python and GTK+
$GTK_ZIP_FN = "gtk3.24-x86-windows.zip"
$GTK_ZIP_PATH = Join-Path $work_dir $GTK_ZIP_FN
if (-not (Test-Path $GTK_ZIP_PATH)) {
    Write-Host "Downloading Python and GTK+..."
    Invoke-WebRequest -Uri "$base_download_url/$GTK_ZIP_FN" -OutFile $GTK_ZIP_PATH
    Get-FileHash -Path $GTK_ZIP_PATH -Algorithm SHA256 | Format-List
} else {
    Write-Host "Python and GTK+ are already downloaded."
}

if (-not (Test-Path $python_home\python.exe)) {
    Write-Host "Unpacking Python and GTK+..."
    $vcpkg_installed = Join-Path $work_dir "vcpkg_installed"
    if (-not (Test-Path $vcpkg_installed)) {
        New-Item -Path $vcpkg_installed -ItemType Directory
    }
    Expand-Archive -Path $GTK_ZIP_PATH -DestinationPath $work_dir
} else {
    Write-Host "Python and GTK+ are already unpacked."
}

if (-not (Test-Path "$root_dir\tools\gtk3\gtk-launch.exe")) {
    Write-Error "GTK+ is not installed correctly."
    exit 1
}

$schema_compiler = Join-Path $root_dir "tools\glib\glib-compile-schemas.exe"
$schema_dir = Join-Path $root_dir "share\glib-2.0\schemas"
if (-not (Test-Path "$schema_dir\gschemas.compiled")) {
    Write-Host "Compiling GLib schemas..."
    & $schema_compiler $schema_dir
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Failed to compile GLib schemas: exit code $LASTEXITCODE"
        exit $LASTEXITCODE
    }
    if (-not (Test-Path "$schema_dir\gschemas.compiled")) {
        Write-Error "Failed to compile GLib schemas: $schema_dir\gschemas.compiled does not exist"
        exit 1
    }
}

# This fixes the chaff dialog when running on Windows from source.
New-Item -ItemType Directory -Path "$python_home\share\glib-2.0\schemas" -Force
Copy-Item -Path "$schema_dir\gschemas.compiled" -Destination "$python_home\share\glib-2.0\schemas" -Force

Write-Host "Checking Python version"
& "$python_home\python.exe" -V  # show Python version
if ($LASTEXITCODE -ne 0) {
    Write-Error "python.exe -V failed"
    exit $LASTEXITCODE
}

Set-MinimalPath -IncludePython

Write-Host "ensurepip"
& "$python_home\python.exe" -m ensurepip

Write-Host "Checking pip version"
& "$python_home\python.exe" -m pip --version  # show pip version

Write-Host "Updating pip..."
& "$python_home\python.exe" -m pip install --upgrade pip

Set-MinimalPath

$GTK_THEMES_ZIP = Join-Path $work_dir "gtk-themes.zip"
if (-not (Test-Path $GTK_THEMES_ZIP)) {
    Write-Host "Downloading GTK themes..."
    #Invoke-WebRequest -Uri "$base_download_url/gtk-themes.zip" -OutFile $GTK_THEMES_ZIP
    #FIXME: use new themes
    Invoke-WebRequest -Uri "https://github.com/mkhon/vcpkg/releases/download/gtk3-introspection-v1/gtk-themes.zip" -OutFile $GTK_THEMES_ZIP
    Get-FileHash -Path $GTK_THEMES_ZIP -Algorithm SHA256 | Format-List
} else {
    Write-Host "GTK themes are already downloaded."
}

if (-not (Test-Path "$themes_dir")) {
    Write-Host "Unpacking GTK themes..."
    Expand-Archive -Path $GTK_THEMES_ZIP -DestinationPath $work_dir
    Copy-Item -Path (Join-Path $work_dir "gtk-themes\*") -Destination $python_home -Recurse -ErrorAction SilentlyContinue
} else {
    Write-Host "GTK themes are already unpacked."
}

if (-not (Test-Path "$themes_dir\Adwaita\index.theme")) {
    Write-Error "GTK themes are not installed correctly."
    exit 1
}

if (Test-Path "gtk-themes") {
    Write-Host "Removing temporary directory gtk-themes..."
    Remove-Item -Path "gtk-themes" -Recurse
}

# Install pip packages from requirements.txt.
Write-Host "Installing Python packages from requirements.txt..."
Set-MinimalPath -IncludePython
& "$python_home\python.exe" -m pip install -r (Join-Path $script_dir 'requirements.txt')
Set-MinimalPath

$PYGOBJECT_FN = "pygobject-3.51.0-cp311-cp311-win32.whl"
$PYGOBJECT_PATH = Join-Path $work_dir $PYGOBJECT_FN
if (-not (Test-Path $PYGOBJECT_PATH)) {
    Write-Host "Downloading PyGObject..."
    Invoke-WebRequest -Uri "$base_download_url/$PYGOBJECT_FN" -OutFile $PYGOBJECT_PATH
    Get-FileHash -Path $PYGOBJECT_PATH -Algorithm SHA256 | Format-List
} else {
    Write-Host "PyGObject is already downloaded."
}

Write-Host "pip install $PYGOBJECT_FN..."
Set-MinimalPath -IncludePython
& "$python_home\python.exe" -m pip install $PYGOBJECT_PATH
Set-MinimalPath

# By default, pygobject installs to `x86-windows\lib\girepository-1.0`.
# Copy it to `x86-windows\tools\python3\lib\girepository-1.0`.
$girepo_dir = "$python_home\lib\girepository-1.0"
if (-not (Test-Path $girepo_dir)) {
    New-Item -Path "$girepo_dir" -ItemType Directory -Force
    Copy-Item -Path "$root_dir\lib\girepository-1.0\*" -Destination "$girepo_dir" -Recurse -Force -ErrorAction Stop
}

# Copy GTK dependencies to Python home.
Get-Content "$script_dir\python-gtk3-deps.lst" | ForEach-Object {
    Write-Host "Copying $_..."
    if (-not (Test-Path "$python_home\$_")) {
        Copy-Item -Path "$root_dir\$_" -Destination "$python_home" -Recurse -Force
    }
}

$GDK_PIXBUF_DIR = "$python_home\lib\gdk-pixbuf-2.0\2.10.0"
if (-not (Test-Path $GDK_PIXBUF_DIR)) {
    Write-Host "Creating $GDK_PIXBUF_DIR..."
    New-Item -Path $GDK_PIXBUF_DIR -ItemType Directory -Force
}

# Update cache file for GDK pixbuf.
$env:GDK_PIXBUF_MODULEDIR = "$root_dir\lib\gdk-pixbuf-2.0\2.10.0\loaders"
$env:GDK_PIXBUF_MODULE_FILE = "$GDK_PIXBUF_DIR\loaders.cache"
if (-not (Test-Path $env:GDK_PIXBUF_MODULE_FILE)) {
    Write-Host "Creating $env:GDK_PIXBUF_MODULE_FILE..."
    Set-MinimalPath -IncludePython
    & "$root_dir\tools\gdk-pixbuf\gdk-pixbuf-query-loaders.exe" --update-cache "$python_home\pixbufloader-svg.dll"
    if ($LASTEXITCODE -ne 0) {
        Write-Error "gdk-pixbuf-query-loaders.exe failed with exit code $LASTEXITCODE"
        exit $LASTEXITCODE
    }
    Set-MinimalPath
}
