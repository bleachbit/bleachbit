<#
Install Python and GTK development and build environment for BleachBit on Windows.
This is a special version built for BleachBit.
It installs in a portable style.
This script may be run in an empty directory like `c:\projects`.

Pass `-Arch x64` for the 64-bit environment; the default is x86.

Afterwards, launch the application like this:
  c:\projects\vcpkg_installed\x86-windows\tools\python3\python.exe c:\projects\bleachbit\bleachbit.py

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
along with this program.  If not, see <https://www.gnu.org/licenses/>.
#>

param(
    [ValidateSet('x86', 'x64')]
    [string]$Arch = 'x86'
)

# CI's pwsh wrapper already does this, but `powershell -File` does not
$ErrorActionPreference = 'Stop'

$root_dir = Join-Path (Get-Location).Path "vcpkg_installed\$Arch-windows"
$python_home = Join-Path $root_dir "tools\python3"
$themes_dir = Join-Path $python_home "share\themes"
# When the tree is restored from cache python.exe already exists, so the pip
# bootstrap and installs below can be skipped. A dependency change busts the
# cache key, forcing a fresh unpack where this is false.
$python_exists = Test-Path "$python_home\python.exe"
# location of this .ps1 script
$script_dir = Split-Path -Parent $MyInvocation.MyCommand.Path
$base_download_url = "https://github.com/bleachbit/pygtkwin/releases/download/v2026-10-13/"
$arch_info = @{
    x86 = @{
        Bits = '32'
        Wheel = 'win32'
        Crt = "$env:SystemRoot\SysWOW64\vcruntime140.dll"
        GtkSha256 = 'd3fd28959ab69ceb185a3f22cfe03bd6f00ab4f7e896621b850e377913a992f3'
        PyGObjectSha256 = 'a51a6fa9b1cbe55485d63c08e953538c72007a3798fc2285ca369625a0265f29'
    }
    x64 = @{
        Bits = '64'
        Wheel = 'win_amd64'
        # Only the x64 redistributable has this DLL
        Crt = "$env:SystemRoot\System32\vcruntime140_1.dll"
        GtkSha256 = '008e2a1f7f8d68766ba18f2c0ca22d7009c71e45046b5149bce17a5b6d3cf820'
        PyGObjectSha256 = 'a1deef789661f36ea3dbb4768c3b87466f2cb962cbe5b08e17d9799793bc88f3'
    }
}[$Arch]
$themes_sha256 = '0a48c03a468a8809fe0379102a9d987721dd2840d426b789596994ec0182572d'

function Assert-FileHash($Path, $Expected) {
    $actual = (Get-FileHash -Path $Path -Algorithm SHA256).Hash
    if ($actual -ine $Expected) {
        throw "SHA256 mismatch for ${Path}: expected $Expected, got $actual"
    }
}

function Expand-7z($Path) {
    $seven_zip = (Get-Command 7z.exe -ErrorAction SilentlyContinue).Source
    if (-not $seven_zip) {
        $seven_zip = Join-Path $env:ProgramFiles "7-Zip\7z.exe"
    }
    if (-not (Test-Path $seven_zip)) {
        Write-Error "7-Zip is needed to unpack $Path"
        exit 1
    }
    & $seven_zip x -bso0 -bsp0 -y $Path
    if ($LASTEXITCODE -ne 0) {
        Write-Error "7-Zip failed to unpack ${Path}: exit code $LASTEXITCODE"
        exit $LASTEXITCODE
    }
}

# Visual C++ Redistributable 2015
$VC_REDIST_FN = "VC_redist.$Arch.exe"
$VC_REDIST_URL = "https://aka.ms/vs/17/release/vc_redist.$Arch.exe"
if (-not $env:GITHUB_ACTIONS) {
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
    if (-not (Test-Path $arch_info.Crt)) {
        Write-Host "Installing Visual C++ Redistributable..."
        Write-Host "Tip: If this step seems to freeze, press ALT+TAB to check for the UAC dialog."
        Start-Process -FilePath $VC_REDIST_FN -ArgumentList "/install", "/quiet", "/norestart" -Wait
    } else {
        Write-Host "Visual C++ Redistributable is already installed."
    }
} else {
    Write-Host "Skipping Visual C++ Redistributable installation in CI."
}

# Python and GTK+
$GTK_ARCHIVE_FN = "gtk3.24-$Arch-windows.7z"
if (-not (Test-Path $GTK_ARCHIVE_FN)) {
    Write-Host "Downloading Python and GTK+..."
    Invoke-WebRequest -Uri "$base_download_url/$GTK_ARCHIVE_FN" -OutFile $GTK_ARCHIVE_FN
} else {
    Write-Host "Python and GTK+ are already downloaded."
}
Assert-FileHash $GTK_ARCHIVE_FN $arch_info.GtkSha256

if (-not (Test-Path $python_home\python.exe)) {
    Write-Host "Unpacking Python and GTK+..."
    Expand-7z $GTK_ARCHIVE_FN
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

if (-not $python_exists) {
    Write-Host "ensurepip"
    & "$python_home\python.exe" -m ensurepip

    Write-Host "Checking pip version"
    & "$python_home\Scripts\pip3.exe" --version  # show pip version

    Write-Host "Updating pip..."
    & "$python_home\python.exe" -m pip install --disable-pip-version-check --upgrade pip
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Failed to update pip: exit code $LASTEXITCODE"
        exit $LASTEXITCODE
    }
} else {
    Write-Host "Python is already unpacked; skipping pip bootstrap."
}

if (-not (Test-Path gtk-themes.7z)) {
    Write-Host "Downloading GTK themes..."
    Invoke-WebRequest -Uri "$base_download_url/gtk-themes.7z" -OutFile "gtk-themes.7z"
} else {
    Write-Host "GTK themes are already downloaded."
}
Assert-FileHash gtk-themes.7z $themes_sha256

if (-not (Test-Path "$themes_dir")) {
    Write-Host "Unpacking GTK themes..."
    Expand-7z gtk-themes.7z
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
if (-not $python_exists) {
    Write-Host "pip install -r requirements.txt..."
    & "$python_home\Scripts\pip3.exe" install --disable-pip-version-check -r "$script_dir\requirements.txt"
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Failed to update pip: exit code $LASTEXITCODE"
        exit $LASTEXITCODE
    }
}

$PYGOBJECT_FN = "pygobject-3.58.0-cp312-cp312-$($arch_info.Wheel).whl"
if (-not (Test-Path $PYGOBJECT_FN)) {
    Write-Host "Downloading PyGObject..."
    Invoke-WebRequest -Uri "$base_download_url/$PYGOBJECT_FN" -OutFile "$PYGOBJECT_FN"
} else {
    Write-Host "PyGObject is already downloaded."
}
Assert-FileHash $PYGOBJECT_FN $arch_info.PyGObjectSha256

if (-not $python_exists) {
    Write-Host "pip install $PYGOBJECT_FN..."
    & "$python_home\Scripts\pip3.exe" install --disable-pip-version-check $PYGOBJECT_FN
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Failed to install PyGObject: exit code $LASTEXITCODE"
        exit $LASTEXITCODE
    }
}

# By default, pygobject installs to `<triplet>\lib\girepository-1.0`.
# Copy it to `<triplet>\tools\python3\lib\girepository-1.0`.
$girepo_dir = "$python_home\lib\girepository-1.0"
if (-not (Test-Path $girepo_dir)) {
    New-Item -Path "$girepo_dir" -ItemType Directory -Force
    Copy-Item -Path "$root_dir\lib\girepository-1.0\*" -Destination "$girepo_dir" -Recurse -Force -ErrorAction Stop
}

# Copy GTK dependencies to Python home.
# {bits} is for GLib's gspawn-win32-* or gspawn-win64-* helpers
Get-Content "$script_dir\python-gtk3-deps.lst" | ForEach-Object {
    $dep = $_.Replace('{bits}', $arch_info.Bits)
    Write-Host "Copying $dep..."
    if (-not (Test-Path "$python_home\$dep")) {
        Copy-Item -Path "$root_dir\$dep" -Destination "$python_home" -Recurse -Force
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
