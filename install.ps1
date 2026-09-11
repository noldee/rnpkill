# rnpkill installer for Windows
# Usage: powershell -c "irm https://raw.githubusercontent.com/noldee/rnpkill/main/install.ps1 | iex"

$ErrorActionPreference = "Stop"

$Repo    = "noldee/rnpkill"
$BinName = "rnpkill.exe"

function Info($msg) { Write-Host "==> $msg" -ForegroundColor Cyan }
function Fail($msg) { Write-Host "Error: $msg" -ForegroundColor Red; exit 1 }

# ---- 1. Resolve version -----------------------------------------------------
if ($env:RNPKILL_VERSION) {
    $Version = $env:RNPKILL_VERSION
} else {
    Info "Looking up latest release..."
    try {
        $release = Invoke-RestMethod -Uri "https://api.github.com/repos/$Repo/releases/latest"
        $Version = $release.tag_name
    } catch {
        Fail "Could not resolve the latest version. Check your connection or set `$env:RNPKILL_VERSION` manually."
    }
}

$Asset = "rnpkill-windows.exe"
$Url   = "https://github.com/$Repo/releases/download/$Version/$Asset"
Info "Installing rnpkill $Version for Windows..."

# ---- 2. Pick install directory ---------------------------------------------
$InstallDir = if ($env:RNPKILL_INSTALL_DIR) { $env:RNPKILL_INSTALL_DIR } else { "$env:LOCALAPPDATA\rnpkill\bin" }
New-Item -ItemType Directory -Force -Path $InstallDir | Out-Null
$DestPath = Join-Path $InstallDir $BinName

# ---- 3. Download -------------------------------------------------------------
try {
    Invoke-WebRequest -Uri $Url -OutFile $DestPath -UseBasicParsing
} catch {
    Fail "Failed to download $Url"
}

Info "Installed to $DestPath"

# ---- 4. Add to PATH (current user) ------------------------------------------
$UserPath = [Environment]::GetEnvironmentVariable("Path", "User")
if ($UserPath -notlike "*$InstallDir*") {
    [Environment]::SetEnvironmentVariable("Path", "$UserPath;$InstallDir", "User")
    $env:Path += ";$InstallDir"
    Info "Added $InstallDir to your user PATH. Restart your terminal for it to take effect everywhere."
} else {
    Info "$InstallDir is already in PATH."
}

Info "Done! Run 'rnpkill --help' to get started."