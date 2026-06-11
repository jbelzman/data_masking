$ErrorActionPreference = "Stop"
$python = Join-Path $PSScriptRoot ".venv\Scripts\python.exe"

if (-not (Test-Path $python)) {
    Write-Host "The app is not set up yet. Running setup..."
    & (Join-Path $PSScriptRoot "setup.ps1")
}

& $python (Join-Path $PSScriptRoot "app.py")
if ($LASTEXITCODE -ne 0) {
    throw "The app exited with code $LASTEXITCODE. See the message above or startup-error.log for details."
}
