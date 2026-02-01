# Get script directory and set location
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Push-Location $ScriptDir

try {
    # Load environment variables from .env
    Write-Host "Loading environment variables..." -ForegroundColor Cyan
    Get-Content (Join-Path $ScriptDir ".env") | ForEach-Object {
        if ($_ -match '^([^=]+)=(.*)$') {
            $key = $matches[1]
            $value = $matches[2]
            Set-Item -Path "env:$key" -Value $value
            Write-Host "  Loaded: $key" -ForegroundColor Gray
        }
    }

    # Source the autocomplete script
    Write-Host "`nLoading autocomplete.ps1..." -ForegroundColor Cyan
    . (Join-Path $ScriptDir "autocomplete.ps1")

    # Run a test command
    Write-Host "`nRunning: autocomplete command 'list files'" -ForegroundColor Cyan
    autocomplete command "list files in current directory"
}
finally {
    Pop-Location
}
