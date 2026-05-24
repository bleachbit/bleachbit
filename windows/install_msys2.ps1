# installs msys2 needed to run make commands such as
# `make tests` and `make -C po bleachbit.pot`.

$ErrorActionPreference = "Stop"

$msysRoot = "C:\msys64"
$installer = "$env:TEMP\msys2-x86_64.exe"

Write-Host "Downloading MSYS2 installer..."

Invoke-WebRequest `
    -Uri "https://github.com/msys2/msys2-installer/releases/latest/download/msys2-x86_64-latest.exe" `
    -OutFile $installer

Write-Host "Installing MSYS2..."

Start-Process `
    -FilePath $installer `
    -ArgumentList "in","--confirm-command","--accept-messages","--root",$msysRoot `
    -Wait

$bash = "$msysRoot\usr\bin\bash.exe"

Write-Host "Updating package database..."

& $bash -lc "pacman --noconfirm -Sy"

Write-Host "Installing packages..."

& $bash -lc @'
pacman --noconfirm --needed -S \
    make \
    grep \
    sed \
    gettext \
    diffutils \
    findutils \
    gawk \
    libxml2
'@

Write-Host "Adding MSYS2 to PATH..."
# Define the paths to add to the user's PATH environment variable
$pathsToAdd = @(
    "$msysRoot\usr\bin"
)

# Retrieve the current user's PATH environment variable
$currentUserPath = [Environment]::GetEnvironmentVariable(
    "Path",
    "User"
)

# Loop through each path to add
foreach ($p in $pathsToAdd) {
    # Check if the path is not already in the user's PATH
    if ($currentUserPath -notlike "*$p*") {
        # Append the path to the existing PATH string
        $currentUserPath += ";$p"
    }
}

# Set the updated PATH environment variable for the user
[Environment]::SetEnvironmentVariable(
    "Path",
    $currentUserPath,
    "User"
)

Write-Host ""
Write-Host "Done."
Write-Host ""
Write-Host "Open a NEW terminal and test:"
Write-Host "  make --version"
Write-Host "  grep --version"
Write-Host "  sed --version"
Write-Host "  gettext --version"
Write-Host "  xmllint --version"