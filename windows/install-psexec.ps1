# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (c) 2008-2026 Andrew Ziem.

# For the CI tests, put PsExec 2.43 in .\psexec. A copy already there, such
# as from the cache, is kept only if its hash matches.

$ErrorActionPreference = 'Stop'

$dir = 'psexec'
$exe = Join-Path $dir 'PsExec.exe'
$sha256 = '078163D5C16F64CAA5A14784323FD51451B8C831C73396B967B4E35E6879937B'

function Test-PsExec {
    (Test-Path $exe) -and (Get-FileHash $exe -Algorithm SHA256).Hash -eq $sha256
}

if (Test-PsExec) {
    Write-Output "Using cached $exe"
    exit 0
}

# PSTools.zip has no version in its URL and other tools in it change, so
# only PsExec.exe is checked.
$zip = Join-Path ([IO.Path]::GetTempPath()) 'PSTools.zip'
Invoke-WebRequest -Uri 'https://download.sysinternals.com/files/PSTools.zip' -OutFile $zip
7z e $zip "-o$dir" PsExec.exe -y
if ($LASTEXITCODE -ne 0) { throw "7z failed with exit code $LASTEXITCODE" }
if (-not (Test-PsExec)) {
    $hash = if (Test-Path $exe) { (Get-FileHash $exe -Algorithm SHA256).Hash } else { 'missing' }
    Remove-Item -Recurse -Force $dir
    throw "PsExec.exe SHA256 mismatch=$hash"
}
