#Requires -Version 5.1
<#
.SYNOPSIS
    Autocomplete.ps1 - LLM Powered PowerShell Completion
.DESCRIPTION
    This script provides PowerShell completion suggestions using an LLM.
    It includes enhanced error handling, configuration management, caching,
    and an interactive completion menu.
.NOTES
    MIT License - ClosedLoop Technologies, Inc.
    Sean Kruzel 2024-2025
    PowerShell port for cross-platform support
#>

#region Global Variables & Model Definitions

$script:ACSH_VERSION = "0.5.0"

# Model definitions as a hashtable
$script:AutocompleteModelList = @{
    # OpenAI models
    'openai:gpt-4o' = @{
        completion_cost = 0.0000100
        prompt_cost = 0.00000250
        endpoint = "https://api.openai.com/v1/chat/completions"
        model = "gpt-4o"
        provider = "openai"
    }
    'openai:gpt-4o-mini' = @{
        completion_cost = 0.0000060
        prompt_cost = 0.00000015
        endpoint = "https://api.openai.com/v1/chat/completions"
        model = "gpt-4o-mini"
        provider = "openai"
    }
    'openai:o1' = @{
        completion_cost = 0.0000600
        prompt_cost = 0.00001500
        endpoint = "https://api.openai.com/v1/chat/completions"
        model = "o1"
        provider = "openai"
    }
    'openai:o1-mini' = @{
        completion_cost = 0.0000440
        prompt_cost = 0.00001100
        endpoint = "https://api.openai.com/v1/chat/completions"
        model = "o1-mini"
        provider = "openai"
    }
    'openai:o3-mini' = @{
        completion_cost = 0.0000440
        prompt_cost = 0.00001100
        endpoint = "https://api.openai.com/v1/chat/completions"
        model = "o3-mini"
        provider = "openai"
    }
    # Anthropic models
    'anthropic:claude-3-7-sonnet-20250219' = @{
        completion_cost = 0.0000150
        prompt_cost = 0.0000030
        endpoint = "https://api.anthropic.com/v1/messages"
        model = "claude-3-7-sonnet-20240219"
        provider = "anthropic"
    }
    'anthropic:claude-3-5-sonnet-20241022' = @{
        completion_cost = 0.0000150
        prompt_cost = 0.0000030
        endpoint = "https://api.anthropic.com/v1/messages"
        model = "claude-3-5-sonnet-20241022"
        provider = "anthropic"
    }
    'anthropic:claude-3-5-haiku-20241022' = @{
        completion_cost = 0.0000040
        prompt_cost = 0.0000008
        endpoint = "https://api.anthropic.com/v1/messages"
        model = "claude-3-5-haiku-20241022"
        provider = "anthropic"
    }
    # Groq models
    'groq:llama3-8b-8192' = @{
        completion_cost = 0.0000000
        prompt_cost = 0.0000000
        endpoint = "https://api.groq.com/openai/v1/chat/completions"
        model = "llama3-8b-8192"
        provider = "groq"
    }
    'groq:llama3-70b-8192' = @{
        completion_cost = 0.0000000
        prompt_cost = 0.0000000
        endpoint = "https://api.groq.com/openai/v1/chat/completions"
        model = "llama3-70b-8192"
        provider = "groq"
    }
    'groq:llama-3.3-70b-versatile' = @{
        completion_cost = 0.0000000
        prompt_cost = 0.0000000
        endpoint = "https://api.groq.com/openai/v1/chat/completions"
        model = "llama-3.3-70b-versatile"
        provider = "groq"
    }
    'groq:llama-3.1-8b-instant' = @{
        completion_cost = 0.0000000
        prompt_cost = 0.0000000
        endpoint = "https://api.groq.com/openai/v1/chat/completions"
        model = "llama-3.1-8b-instant"
        provider = "groq"
    }
    'groq:mixtral-8x7b-32768' = @{
        completion_cost = 0.0000000
        prompt_cost = 0.0000000
        endpoint = "https://api.groq.com/openai/v1/chat/completions"
        model = "mixtral-8x7b-32768"
        provider = "groq"
    }
    'groq:gemma2-9b-it' = @{
        completion_cost = 0.0000000
        prompt_cost = 0.0000000
        endpoint = "https://api.groq.com/openai/v1/chat/completions"
        model = "gemma2-9b-it"
        provider = "groq"
    }
    'groq:deepseek-r1-distill-qwen-32b' = @{
        completion_cost = 0.0000000
        prompt_cost = 0.0000000
        endpoint = "https://api.groq.com/openai/v1/chat/completions"
        model = "deepseek-r1-distill-qwen-32b"
        provider = "groq"
    }
    'groq:qwen-2.5-coder-32b' = @{
        completion_cost = 0.0000000
        prompt_cost = 0.0000000
        endpoint = "https://api.groq.com/openai/v1/chat/completions"
        model = "qwen-2.5-coder-32b"
        provider = "groq"
    }
    # Ollama model
    'ollama:codellama' = @{
        completion_cost = 0.0000000
        prompt_cost = 0.0000000
        endpoint = "http://localhost:11434/api/chat"
        model = "codellama"
        provider = "ollama"
    }
}

# Script-level configuration variables
$script:ACSH_CONFIG = @{}

#endregion

#region Helper Functions

function Write-ErrorMessage {
    param([string]$Message)
    Write-Host "Autocomplete.sh - $Message" -ForegroundColor Red
}

function Write-GreenMessage {
    param([string]$Message)
    Write-Host $Message -ForegroundColor Green
}

function Get-ConfigDirectory {
    $configDir = Join-Path $env:USERPROFILE ".autocomplete"
    return $configDir
}

function Get-ConfigFilePath {
    return Join-Path (Get-ConfigDirectory) "config"
}

function Get-CacheDirectory {
    if ($script:ACSH_CONFIG.CACHE_DIR) {
        return $script:ACSH_CONFIG.CACHE_DIR
    }
    return Join-Path (Get-ConfigDirectory) "cache"
}

function Get-LogFilePath {
    if ($script:ACSH_CONFIG.LOG_FILE) {
        return $script:ACSH_CONFIG.LOG_FILE
    }
    return Join-Path (Get-ConfigDirectory) "autocomplete.log"
}

function Get-MD5Hash {
    param([string]$InputString)
    $md5 = [System.Security.Cryptography.MD5]::Create()
    $bytes = [System.Text.Encoding]::UTF8.GetBytes($InputString)
    $hash = $md5.ComputeHash($bytes)
    return [BitConverter]::ToString($hash).Replace("-", "").ToLower()
}

function Get-MachineSignature {
    $info = "$env:COMPUTERNAME|$env:USERNAME"
    return Get-MD5Hash -InputString $info
}

#endregion

#region System Information Functions

function Get-TerminalInfo {
    $info = @"
 * User name: `$env:USERNAME=$env:USERNAME
 * Current directory: `$PWD=$PWD
 * Home directory: `$env:USERPROFILE=$env:USERPROFILE
 * Computer name: `$env:COMPUTERNAME=$env:COMPUTERNAME
 * OS: $([System.Environment]::OSVersion.VersionString)
 * PowerShell Version: $($PSVersionTable.PSVersion)
"@
    return $info
}

function Get-SystemInfo {
    Write-Output "# System Information"
    Write-Output ""
    Write-Output "Computer: $env:COMPUTERNAME"
    Write-Output "OS: $([System.Environment]::OSVersion.VersionString)"
    Write-Output "SIGNATURE: $(Get-MachineSignature)"
    Write-Output ""
    Write-Output "PowerShell Version: $($PSVersionTable.PSVersion)"
    Write-Output ""
    Write-Output "## Terminal Information"
    Get-TerminalInfo
}

#endregion

#region Configuration Management

function Build-Config {
    $configFile = Get-ConfigFilePath
    $configDir = Get-ConfigDirectory
    
    if (-not (Test-Path $configDir)) {
        New-Item -ItemType Directory -Path $configDir -Force | Out-Null
    }
    
    if (-not (Test-Path $configFile)) {
        Write-Host "Creating default configuration file at $configFile"
        
        $defaultConfig = @"
# ~/.autocomplete/config
# Autocomplete.ps1 Configuration

# OpenAI API Key
openai_api_key: $env:OPENAI_API_KEY

# Anthropic API Key
anthropic_api_key: $env:ANTHROPIC_API_KEY

# Groq API Key
groq_api_key: $env:GROQ_API_KEY

# Custom API Key for Ollama
custom_api_key: $env:LLM_API_KEY

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
cache_dir: $(Join-Path (Get-ConfigDirectory) "cache")
cache_size: 10

# Logging settings
log_file: $(Join-Path (Get-ConfigDirectory) "autocomplete.log")
"@
        Set-Content -Path $configFile -Value $defaultConfig -Encoding UTF8
    }
}

function Import-ACSHConfig {
    $configFile = Get-ConfigFilePath
    $script:ACSH_CONFIG = @{}
    
    if (Test-Path $configFile) {
        $content = Get-Content $configFile -Encoding UTF8
        foreach ($line in $content) {
            # Skip comments and empty lines
            if ($line -match '^\s*#' -or [string]::IsNullOrWhiteSpace($line)) {
                continue
            }
            
            # Parse key: value format
            if ($line -match '^([^:]+):\s*(.*)$') {
                $key = $Matches[1].Trim().ToUpper() -replace '[^A-Z0-9]', '_'
                $value = $Matches[2].Trim()
                
                if (-not [string]::IsNullOrEmpty($value)) {
                    $script:ACSH_CONFIG[$key] = $value
                }
            }
        }
        
        # Set environment variable fallbacks
        if (-not $script:ACSH_CONFIG.OPENAI_API_KEY -and $env:OPENAI_API_KEY) {
            $script:ACSH_CONFIG.OPENAI_API_KEY = $env:OPENAI_API_KEY
        }
        if (-not $script:ACSH_CONFIG.ANTHROPIC_API_KEY -and $env:ANTHROPIC_API_KEY) {
            $script:ACSH_CONFIG.ANTHROPIC_API_KEY = $env:ANTHROPIC_API_KEY
        }
        if (-not $script:ACSH_CONFIG.GROQ_API_KEY -and $env:GROQ_API_KEY) {
            $script:ACSH_CONFIG.GROQ_API_KEY = $env:GROQ_API_KEY
        }
        if (-not $script:ACSH_CONFIG.OLLAMA_API_KEY -and $env:LLM_API_KEY) {
            $script:ACSH_CONFIG.OLLAMA_API_KEY = $env:LLM_API_KEY
        }
        
        # Set active API key based on provider
        $provider = if ($script:ACSH_CONFIG.PROVIDER) { $script:ACSH_CONFIG.PROVIDER } else { "openai" }
        switch ($provider.ToLower()) {
            "openai" { $script:ACSH_CONFIG.ACTIVE_API_KEY = $script:ACSH_CONFIG.OPENAI_API_KEY }
            "anthropic" { $script:ACSH_CONFIG.ACTIVE_API_KEY = $script:ACSH_CONFIG.ANTHROPIC_API_KEY }
            "groq" { $script:ACSH_CONFIG.ACTIVE_API_KEY = $script:ACSH_CONFIG.GROQ_API_KEY }
            "ollama" { $script:ACSH_CONFIG.ACTIVE_API_KEY = $script:ACSH_CONFIG.OLLAMA_API_KEY }
        }
    } else {
        Write-Host "Configuration file not found: $configFile"
    }
}

function Set-ACSHConfig {
    param(
        [string]$Key,
        [string]$Value
    )
    
    $configFile = Get-ConfigFilePath
    $key = $Key.Trim().ToUpper() -replace '[^A-Z0-9]', '_'
    
    if ([string]::IsNullOrEmpty($key)) {
        Write-ErrorMessage "SyntaxError: expected 'autocomplete config set <key> <value>'"
        return
    }
    
    if (-not (Test-Path $configFile)) {
        Write-ErrorMessage "Configuration file not found: $configFile. Run autocomplete install."
        return
    }
    
    $content = Get-Content $configFile -Encoding UTF8
    $keyLower = $Key.ToLower() -replace '_', '_'
    $found = $false
    
    $newContent = $content | ForEach-Object {
        if ($_ -match "^$keyLower\s*:" -or $_ -match "^$($Key.ToLower())\s*:") {
            $found = $true
            "$($Key.ToLower()): $Value"
        } else {
            $_
        }
    }
    
    if (-not $found) {
        $newContent += "$($Key.ToLower()): $Value"
    }
    
    Set-Content -Path $configFile -Value $newContent -Encoding UTF8
    Import-ACSHConfig
}

function Show-Config {
    $configFile = Get-ConfigFilePath
    Write-GreenMessage "Autocomplete.ps1 - Configuration and Settings - Version $script:ACSH_VERSION"
    
    if (-not (Test-Path $configFile)) {
        Write-ErrorMessage "Configuration file not found: $configFile. Run autocomplete install."
        return
    }
    
    Import-ACSHConfig
    
    $termWidth = $Host.UI.RawUI.WindowSize.Width
    if ($termWidth -gt 70) { $termWidth = 70 }
    if ($termWidth -lt 40) { $termWidth = 70 }
    
    foreach ($key in $script:ACSH_CONFIG.Keys | Sort-Object) {
        if ($key -eq "INPUT" -or $key -eq "PROMPT" -or $key -eq "RESPONSE") {
            continue
        }
        
        $value = $script:ACSH_CONFIG[$key]
        
        # Skip API keys in main display
        if ($key -match '_API_KEY$' -or $key -eq 'ACTIVE_API_KEY') {
            continue
        }
        
        $padding = $termWidth - $key.Length - $value.ToString().Length - 5
        if ($padding -lt 1) { $padding = 1 }
        
        Write-Host "  ACSH_${key}: " -NoNewline
        Write-Host (" " * $padding) -NoNewline
        Write-Host $value -ForegroundColor DarkGray
    }
    
    Write-Host "  ===================================================================="
    
    # Display API keys (masked)
    foreach ($key in $script:ACSH_CONFIG.Keys | Sort-Object) {
        if ($key -notmatch '_API_KEY$') {
            continue
        }
        if ($key -eq 'ACTIVE_API_KEY') {
            continue
        }
        
        $value = $script:ACSH_CONFIG[$key]
        
        Write-Host "  ACSH_${key}: " -NoNewline
        
        if ([string]::IsNullOrEmpty($value)) {
            Write-Host "UNSET" -ForegroundColor Red
        } else {
            $masked = $value.Substring(0, [Math]::Min(4, $value.Length)) + "..." + $value.Substring([Math]::Max(0, $value.Length - 4))
            Write-Host $masked -ForegroundColor Green
        }
    }
}

#endregion

#region LLM Completion Functions

function Get-SystemMessagePrompt {
    return "You are a helpful PowerShell completion script. Generate relevant and concise auto-complete suggestions for the given user command in the context of the current directory, operating system, command history, and environment variables. For each suggestion, provide both the command and a brief one-line explanation of what it does. The output must be a list of two to five possible completions or rewritten commands. Each must be a valid command or chain of commands. Do not include backticks or quotes in the commands."
}

function Get-OutputInstructions {
    return "Provide a list of suggested completions or commands that could be run in the terminal. YOU MUST provide a list of two to five possible completions or rewritten commands. For each command, include a brief one-line explanation (max 60 characters) of what it does. DO NOT wrap the commands in backticks or quotes. Each must be a valid command or chain of commands. Focus on the user's intent, recent commands, and the current environment. RETURN A JSON OBJECT WITH THE COMPLETIONS AND THEIR EXPLANATIONS."
}

function Get-CommandHistory {
    $historyLimit = if ($script:ACSH_CONFIG.MAX_HISTORY_COMMANDS) { 
        [int]$script:ACSH_CONFIG.MAX_HISTORY_COMMANDS 
    } else { 
        20 
    }
    
    try {
        $history = Get-History -Count $historyLimit -ErrorAction SilentlyContinue
        if ($history) {
            return ($history | ForEach-Object { "  $($_.Id)  $($_.CommandLine)" }) -join "`n"
        }
    } catch {
        # Ignore errors
    }
    return ""
}

function Get-CleanCommandHistory {
    $history = Get-CommandHistory
    # Redact potential secrets
    $history = $history -replace '\b[0-9a-fA-F]{32,40}\b', 'REDACTED_HASH'
    $history = $history -replace '\b[0-9a-fA-F-]{36}\b', 'REDACTED_UUID'
    $history = $history -replace '\b[A-Za-z0-9]{16,40}\b', 'REDACTED_APIKEY'
    return $history
}

function Get-RecentFiles {
    $fileLimit = if ($script:ACSH_CONFIG.MAX_RECENT_FILES) { 
        [int]$script:ACSH_CONFIG.MAX_RECENT_FILES 
    } else { 
        20 
    }
    
    try {
        $files = Get-ChildItem -Path . -File -ErrorAction SilentlyContinue | 
            Sort-Object LastWriteTime -Descending | 
            Select-Object -First $fileLimit |
            ForEach-Object { "$($_.LastWriteTime.ToString('yyyy-MM-dd HH:mm:ss')) $($_.Length.ToString().PadLeft(10)) $($_.Name)" }
        return $files -join "`n"
    } catch {
        return ""
    }
}

function Get-HelpMessage {
    param([string]$Command)
    
    $cmd = ($Command -split '\s+')[0]
    
    try {
        $help = Get-Help $cmd -ErrorAction SilentlyContinue | Out-String
        if ($help) {
            return $help.Substring(0, [Math]::Min(2000, $help.Length))
        }
    } catch {
        # Ignore errors
    }
    
    return "'$cmd' help not available"
}

function Build-Prompt {
    param([string]$UserInput)
    
    $commandHistory = Get-CleanCommandHistory
    $terminalContext = Get-TerminalInfo
    $helpMessage = Get-HelpMessage -Command $UserInput
    $recentFiles = Get-RecentFiles
    $outputInstructions = Get-OutputInstructions
    
    # Get other environment variables
    $otherEnvVars = Get-ChildItem Env: | 
        Where-Object { $_.Name -notmatch '^ACSH_' -and $_.Name -notmatch 'PWD|USERNAME|USERPROFILE|COMPUTERNAME' } |
        Select-Object -ExpandProperty Name |
        Select-Object -First 30
    $otherEnvVars = $otherEnvVars -join "`n"
    
    $prompt = @"
User command: ``$UserInput``

# Terminal Context
## Environment variables
$terminalContext

Other defined environment variables
``````
$otherEnvVars
``````

## History
Recently run commands (some information redacted):
``````
$commandHistory
``````

## File system
Most recently modified files:
``````
$recentFiles
``````

## Help Information
$helpMessage

# Instructions
$outputInstructions
"@
    
    return $prompt
}

function Build-Payload {
    param([string]$UserInput)
    
    $model = if ($script:ACSH_CONFIG.MODEL) { $script:ACSH_CONFIG.MODEL } else { "gpt-4o" }
    $temperature = if ($script:ACSH_CONFIG.TEMPERATURE) { [double]$script:ACSH_CONFIG.TEMPERATURE } else { 0.0 }
    
    $prompt = Build-Prompt -UserInput $UserInput
    $systemPrompt = Get-SystemMessagePrompt
    
    $provider = if ($script:ACSH_CONFIG.PROVIDER) { $script:ACSH_CONFIG.PROVIDER.ToUpper() } else { "OPENAI" }
    
    $basePayload = @{
        model = $model
        messages = @(
            @{ role = "system"; content = $systemPrompt }
            @{ role = "user"; content = $prompt }
        )
        temperature = $temperature
    }
    
    switch ($provider) {
        "ANTHROPIC" {
            $payload = @{
                model = $model
                system = $systemPrompt
                messages = @(
                    @{ role = "user"; content = $prompt }
                )
                max_tokens = 1024
                temperature = $temperature
                tool_choice = @{ type = "tool"; name = "bash_completions" }
                tools = @(
                    @{
                        name = "bash_completions"
                        description = "syntactically correct command-line suggestions with explanations"
                        input_schema = @{
                            type = "object"
                            properties = @{
                                suggestions = @{
                                    type = "array"
                                    items = @{
                                        type = "object"
                                        properties = @{
                                            command = @{ type = "string"; description = "The suggested command" }
                                            explanation = @{ type = "string"; description = "Brief explanation of what the command does" }
                                        }
                                        required = @("command", "explanation")
                                    }
                                }
                            }
                            required = @("suggestions")
                        }
                    }
                )
            }
        }
        "GROQ" {
            $payload = $basePayload.Clone()
            $payload.response_format = @{ type = "json_object" }
        }
        "OLLAMA" {
            $payload = @{
                model = $model
                messages = $basePayload.messages
                format = "json"
                stream = $false
                options = @{ temperature = $temperature }
            }
        }
        default {
            # OpenAI
            $payload = $basePayload.Clone()
            $payload.response_format = @{ type = "json_object" }
            $payload.tool_choice = @{
                type = "function"
                function = @{
                    name = "bash_completions"
                    description = "syntactically correct command-line suggestions with explanations"
                    parameters = @{
                        type = "object"
                        properties = @{
                            suggestions = @{
                                type = "array"
                                items = @{
                                    type = "object"
                                    properties = @{
                                        command = @{ type = "string"; description = "The suggested command" }
                                        explanation = @{ type = "string"; description = "Brief explanation of what the command does" }
                                    }
                                    required = @("command", "explanation")
                                }
                            }
                        }
                        required = @("suggestions")
                    }
                }
            }
            $payload.tools = @(
                @{
                    type = "function"
                    function = @{
                        name = "bash_completions"
                        description = "syntactically correct command-line suggestions with explanations"
                        parameters = @{
                            type = "object"
                            properties = @{
                                suggestions = @{
                                    type = "array"
                                    items = @{
                                        type = "object"
                                        properties = @{
                                            command = @{ type = "string"; description = "The suggested command" }
                                            explanation = @{ type = "string"; description = "Brief explanation of what the command does" }
                                        }
                                        required = @("command", "explanation")
                                    }
                                }
                            }
                            required = @("suggestions")
                        }
                    }
                }
            )
        }
    }
    
    return $payload
}

function Write-RequestLog {
    param(
        [string]$UserInput,
        [object]$ResponseBody
    )
    
    $userInputHash = Get-MD5Hash -InputString $UserInput
    $logFile = Get-LogFilePath
    
    $provider = if ($script:ACSH_CONFIG.PROVIDER) { $script:ACSH_CONFIG.PROVIDER.ToUpper() } else { "OPENAI" }
    
    if ($provider -eq "ANTHROPIC") {
        $promptTokens = $ResponseBody.usage.input_tokens
        $completionTokens = $ResponseBody.usage.output_tokens
    } else {
        $promptTokens = $ResponseBody.usage.prompt_tokens
        $completionTokens = $ResponseBody.usage.completion_tokens
    }
    
    $created = [int][double]::Parse((Get-Date -UFormat %s))
    if ($ResponseBody.created) {
        $created = $ResponseBody.created
    }
    
    $promptCost = if ($script:ACSH_CONFIG.API_PROMPT_COST) { [double]$script:ACSH_CONFIG.API_PROMPT_COST } else { 0.000005 }
    $completionCost = if ($script:ACSH_CONFIG.API_COMPLETION_COST) { [double]$script:ACSH_CONFIG.API_COMPLETION_COST } else { 0.000015 }
    
    $apiCost = ($promptTokens * $promptCost) + ($completionTokens * $completionCost)
    
    $logEntry = "$created,$userInputHash,$promptTokens,$completionTokens,$apiCost"
    Add-Content -Path $logFile -Value $logEntry -Encoding UTF8
}

function Invoke-LLMCompletion {
    param([string]$UserInput)
    
    if ([string]::IsNullOrEmpty($UserInput)) {
        $UserInput = "Write two to six most likely commands given the provided information"
    }
    
    $provider = if ($script:ACSH_CONFIG.PROVIDER) { $script:ACSH_CONFIG.PROVIDER.ToUpper() } else { "OPENAI" }
    $endpoint = if ($script:ACSH_CONFIG.ENDPOINT) { $script:ACSH_CONFIG.ENDPOINT } else { "https://api.openai.com/v1/chat/completions" }
    $apiKey = $script:ACSH_CONFIG.ACTIVE_API_KEY
    $timeout = if ($script:ACSH_CONFIG.TIMEOUT) { [int]$script:ACSH_CONFIG.TIMEOUT } else { 30 }
    
    if ([string]::IsNullOrEmpty($apiKey) -and $provider -ne "OLLAMA") {
        Write-ErrorMessage "API key not set. Please configure with: autocomplete config set ${provider}_api_key <your-api-key>"
        return $null
    }
    
    $payload = Build-Payload -UserInput $UserInput
    $jsonPayload = $payload | ConvertTo-Json -Depth 10 -Compress
    
    $headers = @{
        "Content-Type" = "application/json"
    }
    
    switch ($provider) {
        "ANTHROPIC" {
            $headers["anthropic-version"] = "2023-06-01"
            $headers["x-api-key"] = $apiKey
        }
        "OLLAMA" {
            # No auth needed for Ollama
        }
        default {
            $headers["Authorization"] = "Bearer $apiKey"
        }
    }
    
    $maxAttempts = 2
    $attempt = 1
    $response = $null
    
    while ($attempt -le $maxAttempts) {
        try {
            $response = Invoke-RestMethod -Uri $endpoint -Method Post -Headers $headers -Body $jsonPayload -TimeoutSec $timeout -ErrorAction Stop
            break
        } catch {
            $statusCode = $_.Exception.Response.StatusCode.value__
            Write-ErrorMessage "API call failed with status $statusCode. Retrying... (Attempt $attempt of $maxAttempts)"
            Start-Sleep -Seconds 1
            $attempt++
        }
    }
    
    if ($null -eq $response) {
        Write-ErrorMessage "Failed to get response from API after $maxAttempts attempts"
        return $null
    }
    
    # Extract content based on provider
    $content = $null
    switch ($provider) {
        "ANTHROPIC" {
            $content = $response.content[0].input.suggestions
        }
        "GROQ" {
            $rawContent = $response.choices[0].message.content | ConvertFrom-Json
            $content = if ($rawContent.suggestions) { $rawContent.suggestions } else { $rawContent.completions }
        }
        "OLLAMA" {
            $rawContent = $response.message.content | ConvertFrom-Json
            $content = if ($rawContent.suggestions) { $rawContent.suggestions } else { $rawContent.completions }
        }
        default {
            $rawContent = $response.choices[0].message.tool_calls[0].function.arguments | ConvertFrom-Json
            $content = if ($rawContent.suggestions) { $rawContent.suggestions } else { $rawContent.commands }
        }
    }
    
    # Format completions as "command|||explanation"
    $completions = @()
    foreach ($item in $content) {
        if ($item.command) {
            $completions += "$($item.command)|||$($item.explanation)"
        } elseif ($item -is [string]) {
            $completions += "$item|||"
        }
    }
    
    # Log the request
    try {
        Write-RequestLog -UserInput $UserInput -ResponseBody $response
    } catch {
        # Ignore logging errors
    }
    
    return $completions -join "`n"
}

#endregion

#region Caching Functions

function Get-CacheList {
    $cacheDir = Get-CacheDirectory
    if (Test-Path $cacheDir) {
        return Get-ChildItem -Path $cacheDir -Filter "acsh-*.txt" | Sort-Object LastWriteTime
    }
    return @()
}

function Get-CachedCompletion {
    param([string]$UserInput)
    
    $cacheDir = Get-CacheDirectory
    $cacheSize = if ($script:ACSH_CONFIG.CACHE_SIZE) { [int]$script:ACSH_CONFIG.CACHE_SIZE } else { 10 }
    
    if ($cacheSize -le 0) {
        return $null
    }
    
    $hash = Get-MD5Hash -InputString $UserInput
    $cacheFile = Join-Path $cacheDir "acsh-$hash.txt"
    
    if (Test-Path $cacheFile) {
        # Update last access time
        (Get-Item $cacheFile).LastWriteTime = Get-Date
        return Get-Content $cacheFile -Raw -Encoding UTF8
    }
    
    return $null
}

function Set-CachedCompletion {
    param(
        [string]$UserInput,
        [string]$Completions
    )
    
    $cacheDir = Get-CacheDirectory
    $cacheSize = if ($script:ACSH_CONFIG.CACHE_SIZE) { [int]$script:ACSH_CONFIG.CACHE_SIZE } else { 10 }
    
    if ($cacheSize -le 0) {
        return
    }
    
    # Ensure cache directory exists
    if (-not (Test-Path $cacheDir)) {
        New-Item -ItemType Directory -Path $cacheDir -Force | Out-Null
    }
    
    $hash = Get-MD5Hash -InputString $UserInput
    $cacheFile = Join-Path $cacheDir "acsh-$hash.txt"
    
    Set-Content -Path $cacheFile -Value $Completions -Encoding UTF8
    
    # Evict old cache entries
    $cacheFiles = Get-CacheList
    while ($cacheFiles.Count -gt $cacheSize) {
        $oldest = $cacheFiles | Select-Object -First 1
        Remove-Item $oldest.FullName -Force -ErrorAction SilentlyContinue
        $cacheFiles = Get-CacheList
    }
}

#endregion

#region CLI Commands

function Show-Help {
    Write-GreenMessage "Autocomplete.ps1 - LLM Powered PowerShell Completion"
    Write-Host "Usage: autocomplete [options] command"
    Write-Host "       autocomplete [options] install|remove|config|model|enable|disable|clear|usage|system|command|--help"
    Write-Host ""
    Write-Host "Autocomplete.ps1 enhances PowerShell completion with LLM capabilities."
    Write-Host ""
    Write-Host "Usage:" -ForegroundColor Green
    Write-Host "  - Press Ctrl+Space for interactive suggestions"
    Write-Host "  - Add '--explain' to your command to show explanations in the interactive menu"
    Write-Host ""
    Write-Host "Commands:"
    Write-Host "  command             Run autocomplete"
    Write-Host "  command --dry-run   Show prompt without executing"
    Write-Host "  model               Change language model"
    Write-Host "  usage               Display usage stats"
    Write-Host "  system              Display system information"
    Write-Host "  config              Show or set configuration values"
    Write-Host "    config set <key> <value>  Set a config value"
    Write-Host "    config reset             Reset config to defaults"
    Write-Host "  install             Install autocomplete to PowerShell profile"
    Write-Host "  remove              Remove installation from PowerShell profile"
    Write-Host "  enable              Enable autocomplete"
    Write-Host "  disable             Disable autocomplete"
    Write-Host "  clear               Clear cache and log files"
    Write-Host "  --help              Show this help message"
    Write-Host ""
    Write-Host "Submit issues at: https://github.com/closedloop-technologies/autocomplete-sh/issues"
}

function Install-Autocomplete {
    $scriptPath = $MyInvocation.MyCommand.Path
    if (-not $scriptPath) {
        $scriptPath = $PSCommandPath
    }
    
    # Create config directory
    $configDir = Get-ConfigDirectory
    if (-not (Test-Path $configDir)) {
        Write-Host "Creating $configDir directory"
        New-Item -ItemType Directory -Path $configDir -Force | Out-Null
    }
    
    # Create cache directory
    $cacheDir = Get-CacheDirectory
    if (-not (Test-Path $cacheDir)) {
        New-Item -ItemType Directory -Path $cacheDir -Force | Out-Null
    }
    
    # Build config
    Build-Config
    Import-ACSHConfig
    
    # Add to PowerShell profile
    $profilePath = $PROFILE.CurrentUserCurrentHost
    $profileDir = Split-Path $profilePath -Parent
    
    if (-not (Test-Path $profileDir)) {
        New-Item -ItemType Directory -Path $profileDir -Force | Out-Null
    }
    
    $autocompleteSetup = ". '$scriptPath'"
    $enableSetup = "Enable-AutocompletePS"
    
    if (-not (Test-Path $profilePath)) {
        New-Item -ItemType File -Path $profilePath -Force | Out-Null
    }
    
    $profileContent = Get-Content $profilePath -Raw -ErrorAction SilentlyContinue
    
    if ($profileContent -notmatch [regex]::Escape($scriptPath)) {
        Add-Content -Path $profilePath -Value "`n# Autocomplete.ps1"
        Add-Content -Path $profilePath -Value $autocompleteSetup
        Add-Content -Path $profilePath -Value $enableSetup
        Write-Host "Added autocomplete.ps1 setup to $profilePath"
    } else {
        Write-Host "Autocomplete.ps1 setup already exists in $profilePath"
    }
    
    Write-Host ""
    Write-GreenMessage "Autocomplete.ps1 - Version $script:ACSH_VERSION installation complete."
    Write-Host "Restart PowerShell or run: . `$PROFILE"
    Write-Host "Then run: autocomplete model to select a language model."
}

function Uninstall-Autocomplete {
    param([switch]$Confirm)
    
    Write-GreenMessage "Removing Autocomplete.ps1 installation..."
    
    $configFile = Get-ConfigFilePath
    $cacheDir = Get-CacheDirectory
    $logFile = Get-LogFilePath
    $configDir = Get-ConfigDirectory
    
    if (Test-Path $configFile) {
        Remove-Item $configFile -Force
        Write-Host "Removed: $configFile"
    }
    
    if (Test-Path $cacheDir) {
        Remove-Item $cacheDir -Recurse -Force
        Write-Host "Removed: $cacheDir"
    }
    
    if (Test-Path $logFile) {
        Remove-Item $logFile -Force
        Write-Host "Removed: $logFile"
    }
    
    if (Test-Path $configDir) {
        $remaining = Get-ChildItem $configDir -ErrorAction SilentlyContinue
        if ($remaining.Count -eq 0) {
            Remove-Item $configDir -Force
            Write-Host "Removed: $configDir"
        } else {
            Write-Host "Skipped removing $configDir (not empty)"
        }
    }
    
    # Remove from profile
    $profilePath = $PROFILE.CurrentUserCurrentHost
    if (Test-Path $profilePath) {
        $content = Get-Content $profilePath
        $newContent = $content | Where-Object { 
            $_ -notmatch 'autocomplete\.ps1' -and 
            $_ -notmatch 'Enable-AutocompletePS' -and 
            $_ -notmatch '# Autocomplete\.ps1'
        }
        Set-Content -Path $profilePath -Value $newContent
        Write-Host "Removed autocomplete.ps1 setup from $profilePath"
    }
    
    Write-Host "Uninstallation complete."
}

function Clear-AutocompleteCache {
    $cacheDir = Get-CacheDirectory
    $logFile = Get-LogFilePath
    
    Write-Host "This will clear the cache and log file."
    Write-Host "Cache directory: " -NoNewline
    Write-Host $cacheDir -ForegroundColor Red
    Write-Host "Log file: " -NoNewline
    Write-Host $logFile -ForegroundColor Red
    
    $confirm = Read-Host "Are you sure? (y/n)"
    if ($confirm -ne "y") {
        Write-Host "Aborted."
        return
    }
    
    if (Test-Path $cacheDir) {
        $cacheFiles = Get-CacheList
        foreach ($file in $cacheFiles) {
            Remove-Item $file.FullName -Force
            Write-Host "Removed: $($file.FullName)"
        }
        Write-Host "Cleared cache in: $cacheDir"
    }
    
    if (Test-Path $logFile) {
        Remove-Item $logFile -Force
        Write-Host "Removed: $logFile"
    }
}

function Show-Usage {
    $logFile = Get-LogFilePath
    $cacheDir = Get-CacheDirectory
    
    $cacheFiles = Get-CacheList
    $cacheCount = $cacheFiles.Count
    
    Write-GreenMessage "Autocomplete.ps1 - Usage Information"
    Write-Host ""
    Write-Host "Log file: " -NoNewline
    Write-Host $logFile -ForegroundColor DarkGray
    
    if (-not (Test-Path $logFile)) {
        $numberOfLines = 0
        $apiCost = 0
        $avgApiCost = 0
    } else {
        $logContent = Get-Content $logFile
        $numberOfLines = $logContent.Count
        $apiCost = ($logContent | ForEach-Object { ($_ -split ',')[4] } | Measure-Object -Sum).Sum
        $avgApiCost = if ($numberOfLines -gt 0) { $apiCost / $numberOfLines } else { 0 }
    }
    
    Write-Host ""
    Write-Host "`tUsage count:`t" -NoNewline
    Write-Host $numberOfLines -ForegroundColor Green
    Write-Host "`tAvg Cost:`t`$" -NoNewline
    Write-Host ("{0:F4}" -f $avgApiCost)
    Write-Host "`tTotal Cost:`t" -NoNewline
    Write-Host ("`${0:F4}" -f $apiCost) -ForegroundColor Red
    Write-Host ""
    
    $maxCacheSize = if ($script:ACSH_CONFIG.CACHE_SIZE) { $script:ACSH_CONFIG.CACHE_SIZE } else { 10 }
    Write-Host "Cache Size: $cacheCount of $maxCacheSize in " -NoNewline
    Write-Host $cacheDir -ForegroundColor DarkGray
    Write-Host "To clear log and cache, run: autocomplete clear"
}

function Invoke-ConfigCommand {
    param([string[]]$Args)
    
    if ($Args.Count -eq 0) {
        Show-Config
        return
    }
    
    if ($Args[0] -eq "set" -and $Args.Count -ge 3) {
        $key = $Args[1]
        $value = $Args[2]
        Write-Host "Setting configuration key '$key' to '$value'"
        Set-ACSHConfig -Key $key -Value $value
        Write-GreenMessage "Configuration updated. Run 'autocomplete config' to view changes."
        return
    }
    
    if ($Args[0] -eq "reset") {
        Write-Host "Resetting configuration to default values."
        $configFile = Get-ConfigFilePath
        if (Test-Path $configFile) {
            Remove-Item $configFile -Force
        }
        Build-Config
        return
    }
    
    Write-ErrorMessage "SyntaxError: expected 'autocomplete config set <key> <value>' or 'autocomplete config reset'"
}

function Select-Model {
    param([string]$Provider, [string]$ModelName)
    
    Clear-Host
    
    if ($Provider -and $ModelName) {
        $key = "${Provider}:${ModelName}"
        if (-not $script:AutocompleteModelList.ContainsKey($key)) {
            Write-Host "ERROR: Invalid provider or model name." -ForegroundColor Red
            return
        }
        $selectedValue = $script:AutocompleteModelList[$key]
    } else {
        Write-Host "Autocomplete.ps1 - Model Configuration" -ForegroundColor Green
        Write-Host ""
        Write-Host "Select a Language Model (Up/Down arrows, Enter to select, 'q' to quit):"
        Write-Host ""
        
        $sortedKeys = $script:AutocompleteModelList.Keys | Sort-Object
        $options = @($sortedKeys)
        $selected = 0
        
        # Interactive menu
        $cursorTop = [Console]::CursorTop
        
        while ($true) {
            [Console]::SetCursorPosition(0, $cursorTop)
            
            for ($i = 0; $i -lt $options.Count; $i++) {
                if ($i -eq $selected) {
                    Write-Host "> $($options[$i])" -ForegroundColor Green
                } else {
                    Write-Host "  $($options[$i])"
                }
            }
            
            $keyInfo = [Console]::ReadKey($true)
            
            switch ($keyInfo.Key) {
                "UpArrow" {
                    $selected--
                    if ($selected -lt 0) { $selected = $options.Count - 1 }
                }
                "DownArrow" {
                    $selected++
                    if ($selected -ge $options.Count) { $selected = 0 }
                }
                "Enter" {
                    break
                }
                "Q" {
                    Write-Host "Selection canceled."
                    return
                }
                "Escape" {
                    Write-Host "Selection canceled."
                    return
                }
            }
            
            if ($keyInfo.Key -eq "Enter") { break }
        }
        
        $selectedKey = $options[$selected]
        $selectedValue = $script:AutocompleteModelList[$selectedKey]
    }
    
    Clear-Host
    Write-Host "Autocomplete.ps1 - Model Configuration" -ForegroundColor Green
    
    # Set config values
    Set-ACSHConfig -Key "model" -Value $selectedValue.model
    Set-ACSHConfig -Key "endpoint" -Value $selectedValue.endpoint
    Set-ACSHConfig -Key "provider" -Value $selectedValue.provider
    Set-ACSHConfig -Key "api_prompt_cost" -Value ("{0:F8}" -f $selectedValue.prompt_cost)
    Set-ACSHConfig -Key "api_completion_cost" -Value ("{0:F8}" -f $selectedValue.completion_cost)
    
    Import-ACSHConfig
    
    # Check if API key is needed
    $provider = $script:ACSH_CONFIG.PROVIDER.ToUpper()
    if ([string]::IsNullOrEmpty($script:ACSH_CONFIG.ACTIVE_API_KEY) -and $provider -ne "OLLAMA") {
        Write-Host "Set ${provider}_API_KEY" -ForegroundColor Blue
        Write-Host "Stored in $(Get-ConfigFilePath)"
        
        switch ($provider) {
            "OPENAI" { Write-Host "Create a new one: https://platform.openai.com/settings/profile?tab=api-keys" }
            "ANTHROPIC" { Write-Host "Create a new one: https://console.anthropic.com/settings/keys" }
            "GROQ" { Write-Host "Create a new one: https://console.groq.com/keys" }
        }
        
        $apiKeyInput = Read-Host "Enter your $provider API Key" -AsSecureString
        $BSTR = [System.Runtime.InteropServices.Marshal]::SecureStringToBSTR($apiKeyInput)
        $plainApiKey = [System.Runtime.InteropServices.Marshal]::PtrToStringAuto($BSTR)
        
        if (-not [string]::IsNullOrEmpty($plainApiKey)) {
            $script:ACSH_CONFIG.ACTIVE_API_KEY = $plainApiKey
            Set-ACSHConfig -Key "$($provider.ToLower())_api_key" -Value $plainApiKey
        }
        
        Clear-Host
        Write-Host "Autocomplete.ps1 - Model Configuration" -ForegroundColor Green
    }
    
    $model = if ($script:ACSH_CONFIG.MODEL) { $script:ACSH_CONFIG.MODEL } else { "ERROR" }
    $temperature = if ($script:ACSH_CONFIG.TEMPERATURE) { "{0:F3}" -f [double]$script:ACSH_CONFIG.TEMPERATURE } else { "0.000" }
    
    Write-Host "Provider:`t" -NoNewline
    Write-Host $script:ACSH_CONFIG.PROVIDER -ForegroundColor DarkGray
    Write-Host "Model:`t`t" -NoNewline
    Write-Host $model -ForegroundColor DarkGray
    Write-Host "Temperature:`t" -NoNewline
    Write-Host $temperature -ForegroundColor DarkGray
    Write-Host ""
    Write-Host "Cost/token:`t" -NoNewline
    Write-Host "prompt: `$$($script:ACSH_CONFIG.API_PROMPT_COST), completion: `$$($script:ACSH_CONFIG.API_COMPLETION_COST)" -ForegroundColor DarkGray
    Write-Host "Endpoint:`t" -NoNewline
    Write-Host $script:ACSH_CONFIG.ENDPOINT -ForegroundColor DarkGray
    
    Write-Host "API Key:`t" -NoNewline
    if ([string]::IsNullOrEmpty($script:ACSH_CONFIG.ACTIVE_API_KEY)) {
        if ($provider -eq "OLLAMA") {
            Write-Host "Not Used" -ForegroundColor DarkGray
        } else {
            Write-Host "UNSET" -ForegroundColor Red
        }
    } else {
        $key = $script:ACSH_CONFIG.ACTIVE_API_KEY
        $masked = $key.Substring(0, [Math]::Min(4, $key.Length)) + "..." + $key.Substring([Math]::Max(0, $key.Length - 4))
        Write-Host $masked -ForegroundColor Green
    }
    
    if ([string]::IsNullOrEmpty($script:ACSH_CONFIG.ACTIVE_API_KEY) -and $provider -ne "OLLAMA") {
        Write-Host "To set the API Key, run:"
        Write-Host "`tautocomplete config set ${provider}_api_key <your-api-key>" -ForegroundColor Red
    }
    
    if ($provider -eq "OLLAMA") {
        Write-Host "To set a custom endpoint:"
        Write-Host "`tautocomplete config set endpoint <your-url>" -ForegroundColor Blue
        Write-Host "Other models can be set with:"
        Write-Host "`tautocomplete config set model <model-name>" -ForegroundColor Blue
    }
    
    Write-Host "To change temperature:"
    Write-Host "`tautocomplete config set temperature <temperature>" -ForegroundColor DarkGray
    Write-Host ""
}

function Invoke-AutocompleteCommand {
    param([string[]]$Args)
    
    $dryRun = $false
    $filteredArgs = @()
    
    foreach ($arg in $Args) {
        if ($arg -eq "--dry-run") {
            $dryRun = $true
        } else {
            $filteredArgs += $arg
        }
    }
    
    $userInput = $filteredArgs -join " "
    
    if ($dryRun) {
        Build-Prompt -UserInput $userInput
        return
    }
    
    Import-ACSHConfig
    $result = Invoke-LLMCompletion -UserInput $userInput
    Write-Host $result
}

#endregion

#region Interactive Completion Menu

function Show-InteractiveMenu {
    param(
        [string]$CompletionsStr,
        [bool]$ShowExplanations = $false
    )
    
    $options = @()
    $explanations = @()
    
    # Parse completions
    $lines = $CompletionsStr -split "`n"
    foreach ($line in $lines) {
        if (-not [string]::IsNullOrWhiteSpace($line)) {
            if ($line -match '\|\|\|') {
                $parts = $line -split '\|\|\|', 2
                $options += $parts[0].Trim()
                $explanations += if ($parts.Count -gt 1) { $parts[1].Trim() } else { "" }
            } else {
                $options += $line.Trim()
                $explanations += ""
            }
        }
    }
    
    if ($options.Count -eq 0) {
        return $null
    }
    
    $selected = 0
    
    # Display header
    Write-Host ""
    Write-Host "+" + ("=" * 68) + "+" -ForegroundColor Cyan
    Write-Host "|  " -ForegroundColor Cyan -NoNewline
    Write-Host "Autocomplete Suggestions" -ForegroundColor Green -NoNewline
    Write-Host (" " * 42) -NoNewline
    Write-Host "|" -ForegroundColor Cyan
    Write-Host "+" + ("=" * 68) + "+" -ForegroundColor Cyan
    Write-Host "|  " -ForegroundColor Cyan -NoNewline
    Write-Host "Use Up/Down to navigate, Enter to execute, Esc to cancel" -ForegroundColor DarkGray -NoNewline
    Write-Host "   |" -ForegroundColor Cyan
    Write-Host "+" + ("=" * 68) + "+" -ForegroundColor Cyan
    Write-Host ""
    
    $menuTop = [Console]::CursorTop
    
    # Menu loop
    while ($true) {
        [Console]::SetCursorPosition(0, $menuTop)
        
        for ($i = 0; $i -lt $options.Count; $i++) {
            # Clear line
            Write-Host (" " * ([Console]::WindowWidth - 1)) -NoNewline
            [Console]::SetCursorPosition(0, [Console]::CursorTop)
            
            if ($i -eq $selected) {
                Write-Host "  > " -ForegroundColor Green -NoNewline
                Write-Host $options[$i] -ForegroundColor Green
                if ($ShowExplanations -and -not [string]::IsNullOrEmpty($explanations[$i])) {
                    Write-Host (" " * ([Console]::WindowWidth - 1)) -NoNewline
                    [Console]::SetCursorPosition(0, [Console]::CursorTop)
                    Write-Host "      $($explanations[$i])" -ForegroundColor White
                }
            } else {
                Write-Host "    $($options[$i])" -ForegroundColor DarkGreen
                if ($ShowExplanations -and -not [string]::IsNullOrEmpty($explanations[$i])) {
                    Write-Host (" " * ([Console]::WindowWidth - 1)) -NoNewline
                    [Console]::SetCursorPosition(0, [Console]::CursorTop)
                    Write-Host "      $($explanations[$i])" -ForegroundColor DarkGray
                }
            }
            
            if ($ShowExplanations -and $i -lt ($options.Count - 1)) {
                Write-Host ""
            }
        }
        
        $keyInfo = [Console]::ReadKey($true)
        
        switch ($keyInfo.Key) {
            "UpArrow" {
                $selected--
                if ($selected -lt 0) { $selected = $options.Count - 1 }
            }
            "DownArrow" {
                $selected++
                if ($selected -ge $options.Count) { $selected = 0 }
            }
            "Enter" {
                $selectedCmd = $options[$selected]
                
                # Check for risky commands
                if ($selectedCmd -match '^\s*Remove-Item|^\s*rm\s|^\s*del\s|^\s*rd\s') {
                    Write-Host ""
                    Write-Host "WARNING: This command may delete files permanently." -ForegroundColor Yellow
                    Write-Host "Command: $selectedCmd" -ForegroundColor Green
                    Write-Host ""
                    $confirm = Read-Host "Are you sure you want to continue? (y/N)"
                    if ($confirm -ne "y") {
                        Write-Host "Command cancelled." -ForegroundColor DarkGray
                        return $null
                    }
                }
                
                Write-Host ""
                Write-Host "Executing: " -ForegroundColor Green -NoNewline
                Write-Host $selectedCmd
                Write-Host ""
                
                return $selectedCmd
            }
            "Escape" {
                Write-Host ""
                Write-Host "Canceled." -ForegroundColor DarkGray
                return $null
            }
            "Q" {
                Write-Host ""
                Write-Host "Canceled." -ForegroundColor DarkGray
                return $null
            }
        }
    }
}

function Invoke-InteractiveAutocomplete {
    param([string]$UserInput)
    
    if ([string]::IsNullOrWhiteSpace($UserInput)) {
        return
    }
    
    # Check for --explain flag
    $showExplanations = $false
    if ($UserInput -match '--explain') {
        $showExplanations = $true
        $UserInput = $UserInput -replace '--explain', '' -replace '\s+', ' '
        $UserInput = $UserInput.Trim()
    }
    
    Import-ACSHConfig
    
    # Check API key
    $provider = if ($script:ACSH_CONFIG.PROVIDER) { $script:ACSH_CONFIG.PROVIDER.ToUpper() } else { "OPENAI" }
    if ([string]::IsNullOrEmpty($script:ACSH_CONFIG.ACTIVE_API_KEY) -and $provider -ne "OLLAMA") {
        Write-Host ""
        Write-ErrorMessage "API key not set. Configure with: autocomplete config"
        return
    }
    
    # Try cache first
    $completions = Get-CachedCompletion -UserInput $UserInput
    
    if ([string]::IsNullOrEmpty($completions)) {
        Write-Host ""
        Write-Host "Generating suggestions..." -ForegroundColor DarkGray
        $completions = Invoke-LLMCompletion -UserInput $UserInput
        
        if ([string]::IsNullOrEmpty($completions)) {
            Write-Host ""
            Write-ErrorMessage "Failed to generate completions"
            return
        }
        
        # Cache the result
        Set-CachedCompletion -UserInput $UserInput -Completions $completions
    }
    
    # Show interactive menu
    $selectedCmd = Show-InteractiveMenu -CompletionsStr $completions -ShowExplanations $showExplanations
    
    if ($selectedCmd) {
        # Execute the command
        try {
            Invoke-Expression $selectedCmd
        } catch {
            Write-ErrorMessage "Command failed: $_"
        }
    }
}

#endregion

#region PowerShell Completion Integration

function Enable-AutocompletePS {
    Import-ACSHConfig
    
    # Register Ctrl+Space key handler if PSReadLine is available
    if (Get-Module -Name PSReadLine -ErrorAction SilentlyContinue) {
        Set-PSReadLineKeyHandler -Chord 'Ctrl+Spacebar' -ScriptBlock {
            $line = $null
            $cursor = $null
            [Microsoft.PowerShell.PSConsoleReadLine]::GetBufferState([ref]$line, [ref]$cursor)
            
            if (-not [string]::IsNullOrWhiteSpace($line)) {
                Invoke-InteractiveAutocomplete -UserInput $line
                [Microsoft.PowerShell.PSConsoleReadLine]::RevertLine()
            }
        } -Description "Autocomplete.ps1 - Interactive LLM suggestions"
    }
    
    Write-GreenMessage "Interactive autocomplete enabled!"
    Write-Host "Press Ctrl+Space for interactive suggestions (add '--explain' for explanations)" -ForegroundColor DarkGray
}

function Disable-AutocompletePS {
    if (Get-Module -Name PSReadLine -ErrorAction SilentlyContinue) {
        Remove-PSReadLineKeyHandler -Chord 'Ctrl+Spacebar' -ErrorAction SilentlyContinue
    }
    Write-Host "Autocomplete disabled." -ForegroundColor DarkGray
}

# Register argument completer for the autocomplete command
Register-ArgumentCompleter -Native -CommandName autocomplete -ScriptBlock {
    param($wordToComplete, $commandAst, $cursorPosition)
    
    $commands = @(
        'install', 'remove', 'config', 'enable', 'disable', 
        'clear', 'usage', 'system', 'command', 'model', '--help'
    )
    
    $commands | Where-Object { $_ -like "$wordToComplete*" } | ForEach-Object {
        [System.Management.Automation.CompletionResult]::new($_, $_, 'ParameterValue', $_)
    }
}

#endregion

#region Main Entry Point

function autocomplete {
    param(
        [Parameter(Position = 0)]
        [string]$Command,
        
        [Parameter(Position = 1, ValueFromRemainingArguments = $true)]
        [string[]]$Arguments
    )
    
    switch ($Command) {
        "--help" { Show-Help }
        "help" { Show-Help }
        "system" { Get-SystemInfo }
        "install" { Install-Autocomplete }
        "remove" { Uninstall-Autocomplete }
        "clear" { Clear-AutocompleteCache }
        "usage" { Show-Usage }
        "model" { 
            if ($Arguments.Count -ge 2) {
                Select-Model -Provider $Arguments[0] -ModelName $Arguments[1]
            } else {
                Select-Model
            }
        }
        "config" { Invoke-ConfigCommand -Args $Arguments }
        "enable" { Enable-AutocompletePS }
        "disable" { Disable-AutocompletePS }
        "command" { Invoke-AutocompleteCommand -Args $Arguments }
        default {
            if (-not [string]::IsNullOrEmpty($Command)) {
                Write-ErrorMessage "Unknown command $Command - run 'autocomplete --help' for usage or visit https://autocomplete.sh"
            } else {
                Write-GreenMessage "Autocomplete.ps1 - LLM Powered PowerShell Completion - Version $script:ACSH_VERSION - https://autocomplete.sh"
            }
        }
    }
}

# Export functions
Export-ModuleMember -Function autocomplete, Enable-AutocompletePS, Disable-AutocompletePS, Invoke-InteractiveAutocomplete -ErrorAction SilentlyContinue

# If running as script (not dot-sourced), process command line
if ($MyInvocation.InvocationName -ne '.') {
    if ($args.Count -gt 0) {
        autocomplete @args
    }
}

#endregion
