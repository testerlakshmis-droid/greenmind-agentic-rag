$ErrorActionPreference = "Stop"

$targets = Get-CimInstance Win32_Process |
    Where-Object {
        $_.Name -match "^python(\.exe)?$" -and
        $_.CommandLine -match "streamlit\s+run" -and
        $_.CommandLine -match "streamlit_app\.py"
    }

if (-not $targets) {
    Write-Host "No running Streamlit process found for streamlit_app.py"
    exit 0
}

foreach ($proc in $targets) {
    try {
        $null = Invoke-CimMethod -InputObject $proc -MethodName Terminate -ErrorAction Stop
        Write-Host "Stopped PID $($proc.ProcessId)"
    }
    catch {
        # Ignore process-race errors when a target exits between discovery and termination.
        Write-Host "PID $($proc.ProcessId) already exited"
    }
}
