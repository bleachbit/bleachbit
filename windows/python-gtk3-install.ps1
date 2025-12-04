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

$root_dir = Join-Path (Get-Location).Path "vcpkg_installed\x86-windows"
$python_home = Join-Path $root_dir "tools\python3"
$themes_dir = Join-Path $python_home "share\themes"
# location of this .ps1 script
$script_dir = Split-Path -Parent $MyInvocation.MyCommand.Path
$base_download_url = "https://github.com/bleachbit/pygtkwin/releases/download/v2025-12-03/"

# Visual C++ Redistributable 2015 x86
$VC_REDIST_FN = "VC_redist.x86.exe"
$VC_REDIST_URL = "https://aka.ms/vs/17/release/vc_redist.x86.exe"
if ($env:APPVEYOR -ne $true) {
    if (-not (Test-Path $VC_REDIST_FN)) {
        Write-Host "Downloading Visual C++ Redistributable..."
        Invoke-WebRequest -Uri $VC_REDIST_URL -OutFile $VC_REDIST_FN
        Get-FileHash -Path $VC_REDIST_FN -Algorithm SHA256 | Format-List
        $fileSizeMB = (Get-Item $VC_REDIST_FN).Length / 1MB
        if ($fileSizeMB -lt 5) {
            Write-Warning "The downloaded Visual C++ Redistributable file is smaller than expected (< 5MB). Please verify its integrity."
        }
    } else {
        Write-Host "Visual C++ Redistributable is already downloaded."
    }
    if (-not (Test-Path "C:\Windows\SysWOW64\vcruntime140.dll")) {
        Write-Host "Installing Visual C++ Redistributable..."
        Write-Host "Tip: If this step seems to freeze, press ALT+TAB to check for the UAC dialog."
        Start-Process -FilePath $VC_REDIST_FN -ArgumentList "/install", "/quiet", "/norestart" -Wait
    } else {
        Write-Host "Visual C++ Redistributable is already installed."
    }
} else {
    Write-Host "Skipping Visual C++ Redistributable installation in AppVeyor environment."
}

# Python and GTK+
$GTK_ZIP_FN = "gtk3.24-x86-windows.zip"
if (-not (Test-Path $GTK_ZIP_FN)) {
    Write-Host "Downloading Python and GTK+..."
    Invoke-WebRequest -Uri "$base_download_url/$GTK_ZIP_FN" -OutFile $GTK_ZIP_FN
    Get-FileHash -Path $GTK_ZIP_FN -Algorithm SHA256 | Format-List
} else {
    Write-Host "Python and GTK+ are already downloaded."
}

if (-not (Test-Path $python_home\python.exe)) {
    Write-Host "Unpacking Python and GTK+..."
    $vcpkg_installed = ".\vcpkg_installed"
    if (-not (Test-Path $vcpkg_installed)) {
        New-Item -Path $vcpkg_installed -ItemType Directory
    }
    Expand-Archive -Path $GTK_ZIP_FN -DestinationPath .
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

# Add Python home and scripts to PATH.
if ($env:PATH -notlike "*$python_home*") {
    Write-Host "Adding Python home and scripts to PATH..."
    $env:PATH += ";$python_home;$python_home\Scripts"
    Write-Host "Updated PATH: $env:PATH"
}

Write-Host "ensurepip"
& "$python_home\python.exe" -m ensurepip

Write-Host "Checking pip version"
& "$python_home\Scripts\pip3.exe" --version  # show pip version

Write-Host "Updating pip..."
& "$python_home\python.exe" -m pip install --upgrade pip
if ($LASTEXITCODE -ne 0) {
    Write-Error "Failed to update pip: exit code $LASTEXITCODE"
    exit $LASTEXITCODE
}

if (-not (Test-Path gtk-themes.zip)) {
    Write-Host "Downloading GTK themes..."
    #Invoke-WebRequest -Uri "$base_download_url/gtk-themes.zip" -OutFile "gtk-themes.zip"
    #FIXME: use new themes
    Invoke-WebRequest -Uri "https://github.com/mkhon/vcpkg/releases/download/gtk3-introspection-v1/gtk-themes.zip" -OutFile "gtk-themes.zip"
    Get-FileHash -Path gtk-themes.zip -Algorithm SHA256 | Format-List
} else {
    Write-Host "GTK themes are already downloaded."
}

if (-not (Test-Path "$themes_dir")) {
    Write-Host "Unpacking GTK themes..."
    Expand-Archive -Path gtk-themes.zip -DestinationPath .
    Copy-Item -Path "gtk-themes\*" -Destination $python_home -Recurse -ErrorAction SilentlyContinue
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

# psutil 7.1.2 stopped providing 32-bit wheels.
# It needs MSVC++ with the python3.lib.
Write-Host "Copying python312.lib..."
New-Item -ItemType Directory -Path "$python_home\libs" -Force
$pylibdest = "$python_home\libs\python3.lib"
Copy-Item -Path "$root_dir\lib\python312.lib" -Destination $pylibdest
Get-ChildItem -Path $pylibdest | Format-List -Property Name, Length

# Install pip packages
Write-Host "pip install -r requirements.txt..."
& "$python_home\Scripts\pip3.exe" install -r "$script_dir\requirements.txt"
if ($LASTEXITCODE -ne 0) {
    Write-Error "Failed to update pip: exit code $LASTEXITCODE"
    exit $LASTEXITCODE
}

$PYGOBJECT_FN = "pygobject-3.55.0-cp312-cp312-win32.whl"
if (-not (Test-Path $PYGOBJECT_FN)) {
    Write-Host "Downloading PyGObject..."
    Invoke-WebRequest -Uri "$base_download_url/$PYGOBJECT_FN" -OutFile "$PYGOBJECT_FN"
    Get-FileHash -Path $PYGOBJECT_FN -Algorithm SHA256 | Format-List
} else {
    Write-Host "PyGObject is already downloaded."
}

Write-Host "pip install $PYGOBJECT_FN..."
& "$python_home\Scripts\pip3.exe" install $PYGOBJECT_FN

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

Write-Host "Copying gdk-pixbuf-2.0..."
$GDK_PIXBUF_DIR = "$python_home\lib\gdk-pixbuf-2.0\2.10.0"
if (-not (Test-Path $GDK_PIXBUF_DIR)) {
    Write-Host "Creating $GDK_PIXBUF_DIR..."
    New-Item -Path $GDK_PIXBUF_DIR -ItemType Directory -Force
}

$GDK_PIXBUF_LOADER_DIR = Join-Path $GDK_PIXBUF_DIR "loaders"
if (-not (Test-Path $GDK_PIXBUF_LOADER_DIR)) {
    New-Item -Path $GDK_PIXBUF_LOADER_DIR -ItemType Directory -Force | Out-Null
}
$svg_loader_src = Join-Path $root_dir "lib\gdk-pixbuf-2.0\2.10.0\loaders\pixbufloader-svg.dll"
if (Test-Path $svg_loader_src) {
    Copy-Item -Path $svg_loader_src -Destination $GDK_PIXBUF_LOADER_DIR -Force
}
Get-ChildItem -Path $GDK_PIXBUF_LOADER_DIR | Format-List -Property Name, Length

# Update cache file for GDK pixbuf.
$env:GDK_PIXBUF_MODULE_FILE = "$GDK_PIXBUF_DIR\loaders.cache"
if (-not (Test-Path $env:GDK_PIXBUF_MODULE_FILE)) {
    Write-Host "Creating $env:GDK_PIXBUF_MODULE_FILE..."
    $prevPath = $env:PATH
    try {
        $env:GDK_PIXBUF_MODULEDIR = $GDK_PIXBUF_LOADER_DIR
        $env:PATH = "$python_home\bin;$python_home;$python_home\Scripts;$root_dir\tools\gtk3;$prevPath"
        & "$root_dir\tools\gdk-pixbuf\gdk-pixbuf-query-loaders.exe" --update-cache
        if ($LASTEXITCODE -ne 0) {
            Write-Error "gdk-pixbuf-query-loaders.exe failed with exit code $LASTEXITCODE"
            exit $LASTEXITCODE
        }
    } finally {
        $env:PATH = $prevPath
    }
}
