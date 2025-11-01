<#
Install MSYS2 32-bit environment for BleachBit on Windows.
It installs in a portable style.
This script may be run in an empty directory like `c:\projects`.

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

$ErrorActionPreference = "Stop"

#$msys_exe_fn = "msys2-x86_64-20241208.exe"
#$msys_exe_url = "https://github.com/msys2/msys2-installer/releases/download/2024-12-08/$msys_exe_fn"
#$msys_root = ".\msys2"
# The .sfx.exe file is a self-extracting archive built using 7-zip.
# The i686 version was last updated 2021.
$msys_exe_fn = "msys2-base-x86_64-20250830.sfx.exe"
$msys_exe_full_path = Join-Path -Path (Get-Location) -ChildPath $msys_exe_fn
$msys_exe_url = "https://github.com/msys2/msys2-installer/releases/download/2025-08-30/$msys_exe_fn"
$msys_root = ".\msys64"
if (-not (Test-Path $msys_exe_full_path)) {
    Write-Host "Downloading MSYS2 from $msys_exe_url..."
    Invoke-WebRequest -Uri $msys_exe_url -OutFile $msys_exe_full_path -ErrorAction Stop
} else {
    Write-Host "MSYS2 is already downloaded."
}
$fileSizeMB = (Get-Item $msys_exe_full_path).Length
Write-Host "File size: $($fileSizeMB.ToString('N0')) bytes"
$fileHash = Get-FileHash -Path $msys_exe_full_path -Algorithm SHA256
Write-Host "File hash: $($fileHash.Hash)"

#$msys_root_install = Join-Path ("$msys_root", "..").Path |  Resolve-Path
$msys_root_install = (Resolve-Path (Split-Path $msys_root -Parent)).Path
Write-Host "MSYS2 will be installed to $msys_root_install"

if (Test-Path "$msys_root\usr\bin\ls.exe")  {
    Write-Host "MSYS2 is already installed."
} else {
    Write-Host "Installing MSYS2..."
    Write-Host "Installer: $msys_exe_full_path"

    try {
        $p = Start-Process -FilePath "$msys_exe_full_path" -ArgumentList "-y -o$msys_root_install" -Wait -NoNewWindow -PassThru
        if ($p.ExitCode -ne 0) {
            Write-Error "Failed to install MSYS2, exit code: $($p.ExitCode)"
            exit $p.ExitCode
        }
    } catch {
        Write-Error "Exception during MSYS2 installation: $_"
        exit 1
    }
}

# Check whether $msys_root\home has any subdirectroes
#if ((Get-ChildItem -Path "$msys_root\home" -Directory).Count -gt 0) {
if (Test-Path "$msys_root\etc\hosts") {
    Write-Host "MSYS2 was already initialized."
} else {
    Start-Process -FilePath "$msys_root\msys2_shell.cmd" -ArgumentList "-defterm", "-here", "-no-start", "-msys", "-c", "exit" -Wait -NoNewWindow
}

$pacman_path = "$msys_root\usr\bin\pacman.exe"
if (-not (Test-Path $pacman_path)) {
    Write-Error "Pacman not found in $pacman_path"
    exit 1
}

# Update pacman without user interaction
function Update-Pacman {
    Write-Host "Updating pacman and packages..."
    $p = Start-Process "$pacman_path" -ArgumentList "-Syu", "--noconfirm" -Wait -NoNewWindow -PassThru
    if ($p.ExitCode -ne 0) {
        Write-Error "Failed to update pacman"
        exit $p.ExitCode
    }
}

Update-Pacman
# Run a second time to update remaining packages
Update-Pacman

$GETTEXT_PKG = "mingw-w64-x86_64-gettext-runtime"
$p = Start-Process "$pacman_path" -ArgumentList "-S", "$GETTEXT_PKG", "--noconfirm" -Wait -NoNewWindow -PassThru
if ($p.ExitCode -ne 0) {
    Write-Error "Failed to install package $GETTEXT_PKG"
    exit $p.ExitCode
}

Write-Host "Checking for msgunfmt.exe..."
Get-ChildItem -Path $msys_root -Filter msgunfmt.exe -Recurse -ErrorAction SilentlyContinue | Select-Object -ExpandProperty FullName

$libintl_path = "$msys_root\mingw64\bin\libintl-8.dll"
if (-not (Test-Path $libintl_path)) {
    Write-Error "libintl-8.dll not found in $libintl_path"
    exit 1
}
