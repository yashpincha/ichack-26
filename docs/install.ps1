#Requires -Version 5.1
<#
.SYNOPSIS
    Autocomplete.ps1 Installer for Windows PowerShell
.DESCRIPTION
    Downloads and installs autocomplete.ps1 for LLM-powered PowerShell completion.
    Run with: irm https://autocomplete.sh/install.ps1 | iex
.NOTES
    MIT License - ClosedLoop Technologies, Inc.
#>

param(
    [string]$Version = "v0.5.0",
    [switch]$Dev
)

$ErrorActionPreference = "Stop"

Write-Host "Autocomplete.ps1 Installer" -ForegroundColor Green
Write-Host "==========================" -ForegroundColor Green
Write-Host ""

# Configuration
$ScriptName = "autocomplete.ps1"
$ConfigDir = Join-Path $env:USERPROFILE ".autocomplete"
$InstallDir = $ConfigDir
$InstallPath = Join-Path $InstallDir $ScriptName
$GitHubUrl = "https://raw.githubusercontent.com/closedloop-technologies/autocomplete-sh/$Version/$ScriptName"

# Create installation directory
if (-not (Test-Path $InstallDir)) {
    Write-Host "Creating installation directory: $InstallDir"
    New-Item -ItemType Directory -Path $InstallDir -Force | Out-Null
}

# Download or copy the script
if ($Dev) {
    # Use local development version
    $LocalScript = Join-Path $PWD $ScriptName
    if (Test-Path $LocalScript) {
        Write-Host "Installing local development version..."
        Copy-Item $LocalScript -Destination $InstallPath -Force
    } else {
        Write-Host "ERROR: Local $ScriptName not found in current directory." -ForegroundColor Red
        exit 1
    }
} else {
    # Download from GitHub
    Write-Host "Downloading from: $GitHubUrl"
    try {
        Invoke-WebRequest -Uri $GitHubUrl -OutFile $InstallPath -UseBasicParsing
        Write-Host "Downloaded successfully to: $InstallPath" -ForegroundColor Green
    } catch {
        Write-Host "ERROR: Failed to download $ScriptName" -ForegroundColor Red
        Write-Host $_.Exception.Message -ForegroundColor Red
        exit 1
    }
}

# Get PowerShell profile path
$ProfilePath = $PROFILE.CurrentUserCurrentHost
$ProfileDir = Split-Path $ProfilePath -Parent

# Create profile directory if it doesn't exist
if (-not (Test-Path $ProfileDir)) {
    Write-Host "Creating PowerShell profile directory: $ProfileDir"
    New-Item -ItemType Directory -Path $ProfileDir -Force | Out-Null
}

# Create profile file if it doesn't exist
if (-not (Test-Path $ProfilePath)) {
    Write-Host "Creating PowerShell profile: $ProfilePath"
    New-Item -ItemType File -Path $ProfilePath -Force | Out-Null
}

# Add to PowerShell profile
$SourceLine = ". '$InstallPath'"
$EnableLine = "Enable-AutocompletePS"
$ProfileContent = Get-Content $ProfilePath -Raw -ErrorAction SilentlyContinue

if ($ProfileContent -notmatch [regex]::Escape($InstallPath)) {
    Write-Host "Adding autocomplete.ps1 to PowerShell profile..."
    
    $profileAddition = @"

# Autocomplete.ps1 - LLM Powered PowerShell Completion
$SourceLine
$EnableLine
"@
    
    Add-Content -Path $ProfilePath -Value $profileAddition -Encoding UTF8
    Write-Host "Added to: $ProfilePath" -ForegroundColor Green
} else {
    Write-Host "Autocomplete.ps1 is already in your PowerShell profile." -ForegroundColor Yellow
}

# Create cache directory
$CacheDir = Join-Path $ConfigDir "cache"
if (-not (Test-Path $CacheDir)) {
    New-Item -ItemType Directory -Path $CacheDir -Force | Out-Null
}

# Create default config file
$ConfigFile = Join-Path $ConfigDir "config"
if (-not (Test-Path $ConfigFile)) {
    Write-Host "Creating default configuration file..."
    
    $defaultConfig = @"
# ~/.autocomplete/config
# Autocomplete.ps1 Configuration

# OpenAI API Key
openai_api_key: $($env:OPENAI_API_KEY)

# Anthropic API Key
anthropic_api_key: $($env:ANTHROPIC_API_KEY)

# Groq API Key
groq_api_key: $($env:GROQ_API_KEY)

# Custom API Key for Ollama
custom_api_key: $($env:LLM_API_KEY)

# Model configuration
provider: openai
model: gpt-4o
temperature: 0.0
endpoint: https://api.openai.com/v1/chat/completions
api_prompt_cost: 0.000005
api_completion_cost: 0.000015

# Max history and recent files
max_history_commands: 20
max_recent_files: 20

# Cache settings
cache_dir: $CacheDir
cache_size: 10

# Logging settings
log_file: $(Join-Path $ConfigDir "autocomplete.log")
"@
    
    Set-Content -Path $ConfigFile -Value $defaultConfig -Encoding UTF8
}

Write-Host ""
Write-Host "============================================" -ForegroundColor Green
Write-Host "Installation Complete!" -ForegroundColor Green
Write-Host "============================================" -ForegroundColor Green
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Cyan
Write-Host "  1. Restart PowerShell or run: . `$PROFILE" -ForegroundColor White
Write-Host "  2. Run: autocomplete model" -ForegroundColor White
Write-Host "     to select a language model and configure your API key" -ForegroundColor Gray
Write-Host ""
Write-Host "Usage:" -ForegroundColor Cyan
Write-Host "  - Press Ctrl+Space for interactive LLM suggestions" -ForegroundColor White
Write-Host "  - Run 'autocomplete --help' for all commands" -ForegroundColor White
Write-Host ""
Write-Host "Configuration file: $ConfigFile" -ForegroundColor Gray
Write-Host "Script location: $InstallPath" -ForegroundColor Gray
Write-Host ""

# Check if PSReadLine is available
$psReadLine = Get-Module -Name PSReadLine -ListAvailable
if (-not $psReadLine) {
    Write-Host "WARNING: PSReadLine module not found." -ForegroundColor Yellow
    Write-Host "Some features (like Ctrl+Space) may not work." -ForegroundColor Yellow
    Write-Host "Install with: Install-Module PSReadLine -Force" -ForegroundColor Yellow
    Write-Host ""
}

# Check for API key
if (-not $env:OPENAI_API_KEY -and -not $env:ANTHROPIC_API_KEY -and -not $env:GROQ_API_KEY) {
    Write-Host "NOTE: No API key found in environment variables." -ForegroundColor Yellow
    Write-Host "You'll need to configure one by running: autocomplete model" -ForegroundColor Yellow
    Write-Host ""
}

Write-Host "For issues or feedback: https://github.com/closedloop-technologies/autocomplete-sh/issues" -ForegroundColor Gray
