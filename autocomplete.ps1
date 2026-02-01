#Requires -Version 5.1
<#
.SYNOPSIS
    Autocomplete.ps1 - LLM Powered PowerShell Completion
.DESCRIPTION
    This script provides PowerShell completion suggestions using an LLM.
.NOTES
    MIT License - ClosedLoop Technologies, Inc.
#>

$script:ACSH_VERSION = "0.5.0"

# Model definitions
$script:AutocompleteModelList = @{
    'openai:gpt-4o' = @{ completion_cost = 0.0000100; prompt_cost = 0.00000250; endpoint = "https://api.openai.com/v1/chat/completions"; model = "gpt-4o"; provider = "openai" }
    'openai:gpt-4o-mini' = @{ completion_cost = 0.0000060; prompt_cost = 0.00000015; endpoint = "https://api.openai.com/v1/chat/completions"; model = "gpt-4o-mini"; provider = "openai" }
    'anthropic:claude-3-5-sonnet-20241022' = @{ completion_cost = 0.0000150; prompt_cost = 0.0000030; endpoint = "https://api.anthropic.com/v1/messages"; model = "claude-3-5-sonnet-20241022"; provider = "anthropic" }
    'groq:llama3-70b-8192' = @{ completion_cost = 0.0; prompt_cost = 0.0; endpoint = "https://api.groq.com/openai/v1/chat/completions"; model = "llama3-70b-8192"; provider = "groq" }
    'ollama:codellama' = @{ completion_cost = 0.0; prompt_cost = 0.0; endpoint = "http://localhost:11434/api/chat"; model = "codellama"; provider = "ollama" }
}

$script:ACSH_CONFIG = @{}

function Write-ErrorMessage { param([string]$Message); Write-Host "Autocomplete.ps1 - $Message" -ForegroundColor Red }
function Write-GreenMessage { param([string]$Message); Write-Host $Message -ForegroundColor Green }

function Get-ConfigDirectory { return Join-Path $env:USERPROFILE ".autocomplete" }
function Get-ConfigFilePath { return Join-Path (Get-ConfigDirectory) "config" }
function Get-CacheDirectory { if ($script:ACSH_CONFIG.CACHE_DIR) { return $script:ACSH_CONFIG.CACHE_DIR }; return Join-Path (Get-ConfigDirectory) "cache" }
function Get-LogFilePath { if ($script:ACSH_CONFIG.LOG_FILE) { return $script:ACSH_CONFIG.LOG_FILE }; return Join-Path (Get-ConfigDirectory) "autocomplete.log" }

function Get-MD5Hash {
    param([string]$InputString)
    $md5 = [System.Security.Cryptography.MD5]::Create()
    $bytes = [System.Text.Encoding]::UTF8.GetBytes($InputString)
    $hash = $md5.ComputeHash($bytes)
    return [BitConverter]::ToString($hash).Replace("-", "").ToLower()
}

function Get-TerminalInfo {
    return @"
 * User: $env:USERNAME
 * Directory: $PWD
 * Computer: $env:COMPUTERNAME
 * OS: $([System.Environment]::OSVersion.VersionString)
 * PowerShell: $($PSVersionTable.PSVersion)
"@
}

function Get-SystemInfo {
    Write-Output "# System Information"
    Write-Output "Computer: $env:COMPUTERNAME"
    Write-Output "OS: $([System.Environment]::OSVersion.VersionString)"
    Write-Output "PowerShell Version: $($PSVersionTable.PSVersion)"
    Write-Output "`n## Terminal Information"
    Get-TerminalInfo
}

function Build-Config {
    $configFile = Get-ConfigFilePath
    $configDir = Get-ConfigDirectory
    if (-not (Test-Path $configDir)) { New-Item -ItemType Directory -Path $configDir -Force | Out-Null }
    if (-not (Test-Path $configFile)) {
        Write-Host "Creating default configuration file at $configFile"
        $defaultConfig = @"
# Autocomplete.ps1 Configuration
openai_api_key: $env:OPENAI_API_KEY
anthropic_api_key: $env:ANTHROPIC_API_KEY
groq_api_key: $env:GROQ_API_KEY
provider: openai
model: gpt-4o
temperature: 0.0
endpoint: https://api.openai.com/v1/chat/completions
cache_dir: $(Join-Path (Get-ConfigDirectory) "cache")
cache_size: 10
log_file: $(Join-Path (Get-ConfigDirectory) "autocomplete.log")
"@
        Set-Content -Path $configFile -Value $defaultConfig -Encoding UTF8
    }
}

function Import-ACSHConfig {
    $configFile = Get-ConfigFilePath
    $script:ACSH_CONFIG = @{}
    if (Test-Path $configFile) {
        Get-Content $configFile -Encoding UTF8 | ForEach-Object {
            if ($_ -notmatch '^\s*#' -and $_ -match '^([^:]+):\s*(.*)$') {
                $key = $Matches[1].Trim().ToUpper() -replace '[^A-Z0-9]', '_'
                $value = $Matches[2].Trim()
                if (-not [string]::IsNullOrEmpty($value)) { $script:ACSH_CONFIG[$key] = $value }
            }
        }
        # Fallback to env vars
        if (-not $script:ACSH_CONFIG.OPENAI_API_KEY -and $env:OPENAI_API_KEY) { $script:ACSH_CONFIG.OPENAI_API_KEY = $env:OPENAI_API_KEY }
        if (-not $script:ACSH_CONFIG.ANTHROPIC_API_KEY -and $env:ANTHROPIC_API_KEY) { $script:ACSH_CONFIG.ANTHROPIC_API_KEY = $env:ANTHROPIC_API_KEY }
        if (-not $script:ACSH_CONFIG.GROQ_API_KEY -and $env:GROQ_API_KEY) { $script:ACSH_CONFIG.GROQ_API_KEY = $env:GROQ_API_KEY }
        
        $provider = if ($script:ACSH_CONFIG.PROVIDER) { $script:ACSH_CONFIG.PROVIDER } else { "openai" }
        switch ($provider.ToLower()) {
            "openai" { $script:ACSH_CONFIG.ACTIVE_API_KEY = $script:ACSH_CONFIG.OPENAI_API_KEY }
            "anthropic" { $script:ACSH_CONFIG.ACTIVE_API_KEY = $script:ACSH_CONFIG.ANTHROPIC_API_KEY }
            "groq" { $script:ACSH_CONFIG.ACTIVE_API_KEY = $script:ACSH_CONFIG.GROQ_API_KEY }
        }
    }
}

function Show-Config {
    Write-GreenMessage "Autocomplete.ps1 - Configuration - Version $script:ACSH_VERSION"
    Import-ACSHConfig
    foreach ($key in $script:ACSH_CONFIG.Keys | Sort-Object) {
        if ($key -match 'API_KEY') { continue }
        Write-Host "  ACSH_$key`: $($script:ACSH_CONFIG[$key])" -ForegroundColor Gray
    }
}

function Build-Prompt {
    param([string]$UserInput)
    $terminalContext = Get-TerminalInfo
    $history = (Get-History -Count 10 -ErrorAction SilentlyContinue | ForEach-Object { $_.CommandLine }) -join "`n"
    return @"
User command: $UserInput

# Terminal Context
$terminalContext

# Recent History
$history

# Instructions
Provide 2-5 command suggestions as JSON: {"suggestions": [{"command": "...", "explanation": "..."}]}
"@
}

function Invoke-LLMCompletion {
    param([string]$UserInput)
    
    Import-ACSHConfig
    $provider = if ($script:ACSH_CONFIG.PROVIDER) { $script:ACSH_CONFIG.PROVIDER.ToUpper() } else { "OPENAI" }
    $endpoint = if ($script:ACSH_CONFIG.ENDPOINT) { $script:ACSH_CONFIG.ENDPOINT } else { "https://api.openai.com/v1/chat/completions" }
    $model = if ($script:ACSH_CONFIG.MODEL) { $script:ACSH_CONFIG.MODEL } else { "gpt-4o" }
    $apiKey = $script:ACSH_CONFIG.ACTIVE_API_KEY
    
    if ([string]::IsNullOrEmpty($apiKey) -and $provider -ne "OLLAMA") {
        Write-ErrorMessage "API key not set. Run: autocomplete config"
        return $null
    }
    
    $prompt = Build-Prompt -UserInput $UserInput
    $systemPrompt = "You are a PowerShell completion assistant. Return JSON with command suggestions."
    
    $payload = @{
        model = $model
        messages = @(
            @{ role = "system"; content = $systemPrompt }
            @{ role = "user"; content = $prompt }
        )
        temperature = 0.0
    }
    
    if ($provider -eq "OPENAI" -or $provider -eq "GROQ") {
        $payload.response_format = @{ type = "json_object" }
    }
    
    $headers = @{ "Content-Type" = "application/json" }
    if ($provider -eq "ANTHROPIC") {
        $headers["anthropic-version"] = "2023-06-01"
        $headers["x-api-key"] = $apiKey
        $payload = @{
            model = $model
            max_tokens = 1024
            system = $systemPrompt
            messages = @(@{ role = "user"; content = $prompt })
        }
    } else {
        $headers["Authorization"] = "Bearer $apiKey"
    }
    
    try {
        $response = Invoke-RestMethod -Uri $endpoint -Method Post -Headers $headers -Body ($payload | ConvertTo-Json -Depth 10) -TimeoutSec 30
        
        if ($provider -eq "ANTHROPIC") {
            $content = $response.content[0].text | ConvertFrom-Json
        } else {
            $content = $response.choices[0].message.content | ConvertFrom-Json
        }
        
        $completions = @()
        foreach ($item in $content.suggestions) {
            $completions += "$($item.command)|||$($item.explanation)"
        }
        return $completions -join "`n"
    } catch {
        Write-ErrorMessage "API call failed: $_"
        return $null
    }
}

function Show-Help {
    Write-GreenMessage "Autocomplete.ps1 - LLM Powered PowerShell Completion"
    Write-Host @"
Usage: autocomplete [command]

Commands:
  --help      Show this help
  system      Show system info
  config      Show configuration
  install     Install to profile
  command     Run completion (e.g., autocomplete command "list files")
"@
}

function Install-Autocomplete {
    $configDir = Get-ConfigDirectory
    if (-not (Test-Path $configDir)) { New-Item -ItemType Directory -Path $configDir -Force | Out-Null }
    Build-Config
    Import-ACSHConfig
    Write-GreenMessage "Autocomplete.ps1 installed. Restart PowerShell to use."
}

function autocomplete {
    param([Parameter(Position=0)][string]$Command, [Parameter(Position=1, ValueFromRemainingArguments)][string[]]$Arguments)
    
    switch ($Command) {
        "--help" { Show-Help }
        "help" { Show-Help }
        "system" { Get-SystemInfo }
        "config" { Show-Config }
        "install" { Install-Autocomplete }
        "command" {
            Import-ACSHConfig
            $userInput = $Arguments -join " "
            Write-Host "Getting suggestions for: $userInput" -ForegroundColor Cyan
            $result = Invoke-LLMCompletion -UserInput $userInput
            if ($result) {
                Write-Host "`nSuggestions:" -ForegroundColor Green
                $result -split "`n" | ForEach-Object {
                    $parts = $_ -split '\|\|\|'
                    Write-Host "  $($parts[0])" -ForegroundColor White
                    if ($parts.Count -gt 1) { Write-Host "    $($parts[1])" -ForegroundColor Gray }
                }
            }
        }
        default {
            if ($Command) { Write-ErrorMessage "Unknown command: $Command" }
            else { Write-GreenMessage "Autocomplete.ps1 - Version $script:ACSH_VERSION - https://autocomplete.sh" }
        }
    }
}

# Run if invoked directly
if ($MyInvocation.InvocationName -ne '.') {
    if ($args.Count -gt 0) { autocomplete @args }
}
