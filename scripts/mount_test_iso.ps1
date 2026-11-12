# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (c) 2008-2026 Andrew Ziem.

# For testing, download and mount an .iso.

param(
    [string]$IsoPath = "$env:TEMP\bleachbit_test.iso",
    [switch]$Dismount
)

$ErrorActionPreference = 'Stop'

Dismount-DiskImage -ImagePath $IsoPath -ErrorAction SilentlyContinue | Out-Null
if ($Dismount) { exit }

$archiveUrl = 'https://download.bleachbit.org/test/test.iso.7z'
$archiveHash = '0d827b61fed9fc5983fe4639e3d383e40b9d5d6c2335ee00ca9b2229280ebb38'
$expectedHash = '71f284d46636bc11d2d02dcf1da4a87003e30056db59cc696f040163bfa28ffb'

$archive = "$env:TEMP\bleachbit_test.iso.7z"
curl.exe -fsSL --retry 3 --retry-connrefused -o $archive $archiveUrl
if ($LASTEXITCODE -ne 0) { throw "download failed with exit code $LASTEXITCODE" }
if ((Get-FileHash -Algorithm SHA256 $archive).Hash -ne $archiveHash) {
    throw "SHA256 mismatch for $archive"
}

tar -xf $archive -C $env:TEMP
if ($LASTEXITCODE -ne 0) { throw "extract failed with exit code $LASTEXITCODE" }
$extracted = "$env:TEMP\bleachbit_test.iso"
if ($extracted -ne $IsoPath) { Move-Item $extracted $IsoPath -Force }

if ((Get-FileHash -Algorithm SHA256 $IsoPath).Hash -ne $expectedHash) {
    throw "SHA256 mismatch for $IsoPath"
}

$vol = Mount-DiskImage -ImagePath $IsoPath -PassThru | Get-Volume
Write-Host "Mounted $IsoPath as drive $($vol.DriveLetter):"
