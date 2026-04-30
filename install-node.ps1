# install-node.ps1 — Downloads and installs Node.js LTS silently
# Run this script ONCE to install Node.js, then use start-frontend.bat

$nodeVersion = "20.14.0"
$nodeUrl = "https://nodejs.org/dist/v$nodeVersion/node-v$nodeVersion-x64.msi"
$installer = "$env:TEMP\node-v$nodeVersion-x64.msi"

Write-Host ""
Write-Host "  The Automated Outpost — Node.js Installer" -ForegroundColor Cyan
Write-Host "  ==========================================" -ForegroundColor Cyan
Write-Host ""

# Check if already installed
$nodePaths = @("C:\Program Files\nodejs\node.exe", "$env:APPDATA\npm\node.exe")
foreach ($p in $nodePaths) {
    if (Test-Path $p) {
        Write-Host "  ✅ Node.js already installed at: $p" -ForegroundColor Green
        & $p --version
        Write-Host ""
        Write-Host "  You can now run: start-frontend.bat" -ForegroundColor Yellow
        Read-Host "  Press Enter to exit"
        exit 0
    }
}

Write-Host "  Downloading Node.js v$nodeVersion..." -ForegroundColor Yellow
try {
    Invoke-WebRequest -Uri $nodeUrl -OutFile $installer -UseBasicParsing
    Write-Host "  ✅ Download complete" -ForegroundColor Green
} catch {
    Write-Host "  ❌ Download failed: $_" -ForegroundColor Red
    Write-Host "  Please download manually from: https://nodejs.org/" -ForegroundColor Yellow
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host "  Installing Node.js (requires admin — UAC prompt may appear)..." -ForegroundColor Yellow
$result = Start-Process msiexec -ArgumentList "/i `"$installer`" /qn /norestart ADDLOCAL=ALL" -Verb RunAs -Wait -PassThru

if ($result.ExitCode -eq 0) {
    Write-Host "  ✅ Node.js installed successfully!" -ForegroundColor Green
    Write-Host ""
    Write-Host "  Please RESTART your PowerShell/Command Prompt, then run:" -ForegroundColor Cyan
    Write-Host "  start-frontend.bat" -ForegroundColor Yellow
} else {
    Write-Host "  ⚠️  Installation may have been cancelled (code: $($result.ExitCode))" -ForegroundColor Yellow
    Write-Host "  Please install manually from: https://nodejs.org/" -ForegroundColor Yellow
}

Write-Host ""
Read-Host "  Press Enter to exit"
