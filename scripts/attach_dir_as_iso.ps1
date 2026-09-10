# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (c) 2008-2026 Andrew Ziem.
#
# This work is licensed under the terms of the GNU GPL, version 3 or
# later.  See the COPYING file in the top-level directory.

<#
.SYNOPSIS
    Build a minimal ISO image from a directory and mount it as an optical
    drive at a given drive letter.

.DESCRIPTION
    Uses the built-in IMAPI2FS.MsftFileSystemImage COM object to create an
    ISO9660 image from the contents of a source directory, then mounts it
    read-only (no drive letter is auto-assigned) and assigns the requested
    drive letter. This is used in CI to provide a CD-ROM-style volume for
    tests that exercise read-only / optical-drive code paths.

.PARAMETER SourceDir
    Directory whose contents are placed at the ISO root. Created if missing.

.PARAMETER IsoPath
    Path of the .iso file to write. Parent directory is created if missing.

.PARAMETER DriveLetter
    Single-letter drive (without colon or backslash) to assign to the
    mounted ISO. Defaults to "O".

.PARAMETER VolumeName
    ISO9660 volume label. Defaults to "MINIMAL_ISO".

.PARAMETER ContentFile
    Optional path of a single file to create inside SourceDir when it does
    not already exist. Defaults to "readme.txt" containing a one-line
    placeholder. Ignored when SourceDir already contains files.

.EXAMPLE
    .\scripts\attach_dir_as_iso.ps1
    .\scripts\attach_dir_as_iso.ps1 -DriveLetter O -SourceDir C:\Temp\IsoSource -IsoPath C:\Temp\Minimal.iso
#>
[CmdletBinding()]
param(
    [string]$SourceDir   = "C:\Temp\IsoSource",
    [string]$IsoPath     = "C:\Temp\Minimal.iso",
    [string]$DriveLetter = "O",
    [string]$VolumeName  = "MINIMAL_ISO",
    [string]$ContentFile = "readme.txt"
)

$ErrorActionPreference = 'Stop'

# Normalize the drive letter: strip any trailing colon/backslash and
# upper-case it so downstream cmdlets accept it consistently.
$DriveLetter = ($DriveLetter -replace '[^A-Za-z]', '').ToUpper()
if ($DriveLetter.Length -ne 1) {
    throw "DriveLetter must be a single letter (got '$DriveLetter')"
}

# 1. If a previous run left an image mounted at this letter, detach it so
#    the new Set-Partition -NewDriveLetter does not collide. Ignore errors
#    when nothing is mounted.
if (Get-PSDrive -Name $DriveLetter -ErrorAction SilentlyContinue) {
    Write-Host "Detaching previously mounted image at ${DriveLetter}:"
    Get-DiskImage -ImagePath $IsoPath -ErrorAction SilentlyContinue |
        Dismount-DiskImage -ErrorAction SilentlyContinue
    # Fall back: detach any disk image backing the volume.
    Get-Volume -DriveLetter $DriveLetter -ErrorAction SilentlyContinue |
        Get-Partition -ErrorAction SilentlyContinue |
        ForEach-Object { $_ | Get-Disk -ErrorAction SilentlyContinue } |
        Where-Object { $_.BusType -eq 'FileBackedVirtual' } |
        ForEach-Object { Dismount-DiskImage -ImagePath $_.Path -ErrorAction SilentlyContinue }
}

# 2. Create the source directory and seed a minimal file when empty.
New-Item -ItemType Directory -Path $SourceDir -Force | Out-Null
$existing = Get-ChildItem -Path $SourceDir -Force -ErrorAction SilentlyContinue
if (-not $existing) {
    Set-Content -Path (Join-Path $SourceDir $ContentFile) `
        -Value "Minimal ISO contents"
}

# 3. Build the ISO image using the built-in IMAPI2 COM object.
Write-Host "Building ISO '$IsoPath' from '$SourceDir' (volume '$VolumeName')"
$Image = New-Object -ComObject IMAPI2FS.MsftFileSystemImage
$Image.ChooseObjectDefaultsForMediaType(12)  # 12 = IMAPI_MEDIA_TYPE_DISK
$Image.VolumeName = $VolumeName
$Image.Root.AddTree($SourceDir, $false)

$Result  = $Image.CreateResultImage()
$Stream  = $Result.ImageStream

$IsoParent = Split-Path -Parent $IsoPath
if ($IsoParent -and -not (Test-Path $IsoParent)) {
    New-Item -ItemType Directory -Path $IsoParent -Force | Out-Null
}
$FileStream = [System.IO.File]::Create($IsoPath)
$Buffer     = New-Object byte[] 2048
while (($Read = $Stream.Read($Buffer, 0, $Buffer.Length)) -gt 0) {
    $FileStream.Write($Buffer, 0, $Read)
}
$FileStream.Close()

# 4. Mount the ISO without an auto-assigned drive letter, then assign ours.
Write-Host "Mounting ISO at ${DriveLetter}:"
$Mounted = Mount-DiskImage -ImagePath $IsoPath -NoDriveLetter -PassThru
Get-Volume -DiskImage $Mounted |
    Get-Partition |
    Set-Partition -NewDriveLetter $DriveLetter

# 5. Verify the mounted drive.
Get-PSDrive -Name $DriveLetter | Format-Table Name, Root, Description, Used, Free
Get-ChildItem -Path "${DriveLetter}:\" | Format-Table Name, Length
Write-Host "ISO mounted successfully at ${DriveLetter}:\"
