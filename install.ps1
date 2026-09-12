# rnpkill installer for Windows
# Usage: powershell -c "irm https://raw.githubusercontent.com/noldee/rnpkill/main/install.ps1 | iex"

$ErrorActionPreference = "Stop"

$Repo    = "noldee/rnpkill"
$BinName = "rnpkill.exe"

function Info($msg) { Write-Host "==> $msg" -ForegroundColor Cyan }
function Warn($msg) { Write-Host "Warn: $msg" -ForegroundColor Yellow }
function Fail($msg) { Write-Host "Error: $msg" -ForegroundColor Red; exit 1 }

# ---- 0. Force TLS 1.2 (fixes PowerShell 5.1 on old Windows) ----------------
try {
    [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
} catch {
    Warn "Could not force TLS 1.2. Continuing anyway..."
}

# ---- 1. Check execution policy ---------------------------------------------
$policy = Get-ExecutionPolicy -Scope CurrentUser
if ($policy -eq "Restricted" -or $policy -eq "Undefined") {
    Warn "ExecutionPolicy is '$policy'. If the script fails, run:"
    Warn "  Set-ExecutionPolicy -Scope CurrentUser RemoteSigned"
}

# ---- 2. Resolve version -----------------------------------------------------
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

# ---- 3. Pick install directory ---------------------------------------------
$InstallDir = if ($env:RNPKILL_INSTALL_DIR) { $env:RNPKILL_INSTALL_DIR } else { "$env:LOCALAPPDATA\rnpkill\bin" }
New-Item -ItemType Directory -Force -Path $InstallDir | Out-Null
$DestPath = Join-Path $InstallDir $BinName

# ---- 4. Download -------------------------------------------------------------
try {
    Invoke-WebRequest -Uri $Url -OutFile $DestPath -UseBasicParsing
} catch {
    Fail "Failed to download $Url`nError: $_"
}

# ---- 5. Verify the binary exists and is not quarantined --------------------
Start-Sleep -Milliseconds 500  # give Defender a moment
if (-not (Test-Path $DestPath)) {
    Fail @"
The binary was downloaded but disappeared — Windows Defender may have
quarantined it (false positive from PyInstaller).

To fix:
  1. Open Windows Security → Protection History
  2. Find the recent block for 'rnpkill.exe'
  3. Click 'Allow on device'
  4. Re-run the installer

Alternative: use the Python installation method instead:
  pipx install git+https://github.com/noldee/rnpkill.git
"@
}

$fileSize = (Get-Item $DestPath).Length
if ($fileSize -lt 1MB) {
    Fail "Downloaded file is too small ($fileSize bytes) — download may have failed."
}
Info "Downloaded $([math]::Round($fileSize / 1MB, 1)) MB to $DestPath"

# ---- 6. Add to PATH (current user) ------------------------------------------
$UserPath = [Environment]::GetEnvironmentVariable("Path", "User")
if ($UserPath -notlike "*$InstallDir*") {
    [Environment]::SetEnvironmentVariable("Path", "$UserPath;$InstallDir", "User")
    $env:Path += ";$InstallDir"
    Info "Added $InstallDir to your user PATH."
    Info "Restart your terminal (or open a new one) for it to take effect everywhere."
} else {
    Info "$InstallDir is already in PATH."
}

Info "Done! Run 'rnpkill --help' to get started."
Info "If 'rnpkill' is not found, open a new terminal or run: `$env:Path += ';$InstallDir'"