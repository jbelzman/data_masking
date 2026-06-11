$ErrorActionPreference = "Stop"
$venvPython = Join-Path $PSScriptRoot ".venv\Scripts\python.exe"

if (-not (Test-Path $venvPython)) {
    $launcher = Get-Command py -ErrorAction SilentlyContinue
    $python = Get-Command python -ErrorAction SilentlyContinue
    if ($launcher) {
        & $launcher.Source -3 -m venv (Join-Path $PSScriptRoot ".venv")
    }
    elseif ($python) {
        & $python.Source -m venv (Join-Path $PSScriptRoot ".venv")
    }
    else {
        throw "Python 3.10 or newer was not found. Install it from https://www.python.org/downloads/windows/ and enable 'Add Python to PATH', then run setup.ps1 again."
    }
}

& $venvPython -m pip install --upgrade pip
& $venvPython -m pip install -r (Join-Path $PSScriptRoot "requirements.txt")
Write-Host ""
Write-Host "Setup complete. Double-click run.bat to open the app."
