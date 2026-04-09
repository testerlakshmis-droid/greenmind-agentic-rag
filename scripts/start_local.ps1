param(
    [int]$Port = 8505,
    [switch]$Headless = $true
)

$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $PSScriptRoot
$pythonExe = Join-Path $projectRoot "venv\Scripts\python.exe"
$appFile = Join-Path $projectRoot "streamlit_app.py"

if (-not (Test-Path $pythonExe)) {
    Write-Error "Python executable not found at $pythonExe. Recreate the virtual environment first."
}

if (-not (Test-Path $appFile)) {
    Write-Error "App entry file not found at $appFile."
}

$headlessValue = if ($Headless) { "true" } else { "false" }

Push-Location $projectRoot
try {
    & $pythonExe -m streamlit run $appFile --server.headless $headlessValue --server.port $Port
}
finally {
    Pop-Location
}
