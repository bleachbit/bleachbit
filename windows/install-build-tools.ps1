# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (c) 2008-2026 Andrew Ziem.

# For the CI build, install NSIS and, with -AdvanceComp, unpack AdvanceCOMP
# (advzip). Downloads already present, such as from the cache, are verified
# the same way as fresh ones.

param(
    [switch]$AdvanceComp
)

$ErrorActionPreference = 'Stop'

if (-not (Test-Path nsis-3.13-setup.exe)) {
    Invoke-WebRequest -Uri "https://download.bleachbit.org/dependency/nsis-3.13-setup.exe" -OutFile nsis-3.13-setup.exe
}
$hash = (Get-FileHash nsis-3.13-setup.exe -Algorithm SHA256).Hash
if ($hash -ne 'db9a1038bbc0e53fef24f423fd609979bd578e942f1be1198db186d1c42652a3') {
    throw "SHA256 mismatch=$hash"
}
$proc = Start-Process -FilePath .\nsis-3.13-setup.exe -ArgumentList '/S' -Wait -PassThru
if ($proc.ExitCode -ne 0) { throw "NSIS setup failed with exit code $($proc.ExitCode)" }

if ($AdvanceComp) {
    if (-not (Test-Path advancecomp.zip)) {
        Invoke-WebRequest -Uri "https://github.com/amadvance/advancecomp/releases/download/v2.6/advancecomp-2.6-windows-x64.zip" -OutFile advancecomp.zip
    }
    $hash = (Get-FileHash advancecomp.zip -Algorithm SHA256).Hash
    if ($hash -ne '39478E2810D2E6FECEA321D11A8E8AAD678E9E52F83C684D85DCB70342607704') {
        throw "SHA256 mismatch=$hash"
    }
    7z x advancecomp.zip -oadvancecomp -y
    if ($LASTEXITCODE -ne 0) { throw "7z failed with exit code $LASTEXITCODE" }
    Get-ChildItem .\advancecomp\
}
