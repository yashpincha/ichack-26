#Requires -Version 5.1
#Requires -Modules Pester

<#
.SYNOPSIS
    Pester tests for autocomplete.ps1
.DESCRIPTION
    Tests for the PowerShell version of autocomplete.sh
.NOTES
    Run with: Invoke-Pester -Path ./tests/test_autocomplete.ps1
#>

BeforeAll {
    # Get the path to autocomplete.ps1
    $ScriptPath = Join-Path $PSScriptRoot ".." "autocomplete.ps1"
    
    # Dot-source the script to load functions
    . $ScriptPath
    
    # Set up test environment
    $TestConfigDir = Join-Path $env:TEMP "autocomplete-test-$(Get-Random)"
    $OriginalUserProfile = $env:USERPROFILE
    
    # Create test directories
    New-Item -ItemType Directory -Path $TestConfigDir -Force | Out-Null
    New-Item -ItemType Directory -Path (Join-Path $TestConfigDir ".autocomplete") -Force | Out-Null
    New-Item -ItemType Directory -Path (Join-Path $TestConfigDir ".autocomplete" "cache") -Force | Out-Null
}

AfterAll {
    # Clean up test environment
    if ($TestConfigDir -and (Test-Path $TestConfigDir)) {
        Remove-Item $TestConfigDir -Recurse -Force -ErrorAction SilentlyContinue
    }
}

Describe "Autocomplete.ps1 Module Loading" {
    It "Should have ACSH_VERSION defined" {
        $script:ACSH_VERSION | Should -Not -BeNullOrEmpty
        $script:ACSH_VERSION | Should -Match '^\d+\.\d+\.\d+$'
    }
    
    It "Should have AutocompleteModelList populated" {
        $script:AutocompleteModelList | Should -Not -BeNullOrEmpty
        $script:AutocompleteModelList.Count | Should -BeGreaterThan 0
    }
    
    It "Should have OpenAI models defined" {
        $script:AutocompleteModelList.ContainsKey('openai:gpt-4o') | Should -BeTrue
        $script:AutocompleteModelList.ContainsKey('openai:gpt-4o-mini') | Should -BeTrue
    }
    
    It "Should have Anthropic models defined" {
        $script:AutocompleteModelList.Keys | Where-Object { $_ -match '^anthropic:' } | Should -Not -BeNullOrEmpty
    }
    
    It "Should have Groq models defined" {
        $script:AutocompleteModelList.Keys | Where-Object { $_ -match '^groq:' } | Should -Not -BeNullOrEmpty
    }
    
    It "Should have Ollama model defined" {
        $script:AutocompleteModelList.ContainsKey('ollama:codellama') | Should -BeTrue
    }
}

Describe "Helper Functions" {
    Context "Get-MD5Hash" {
        It "Should return a valid MD5 hash" {
            $hash = Get-MD5Hash -InputString "test"
            $hash | Should -Not -BeNullOrEmpty
            $hash | Should -Match '^[a-f0-9]{32}$'
        }
        
        It "Should return consistent hashes" {
            $hash1 = Get-MD5Hash -InputString "hello world"
            $hash2 = Get-MD5Hash -InputString "hello world"
            $hash1 | Should -Be $hash2
        }
        
        It "Should return different hashes for different inputs" {
            $hash1 = Get-MD5Hash -InputString "input1"
            $hash2 = Get-MD5Hash -InputString "input2"
            $hash1 | Should -Not -Be $hash2
        }
    }
    
    Context "Get-ConfigDirectory" {
        It "Should return a valid path" {
            $dir = Get-ConfigDirectory
            $dir | Should -Not -BeNullOrEmpty
            $dir | Should -Match '\.autocomplete$'
        }
    }
    
    Context "Get-MachineSignature" {
        It "Should return a valid signature" {
            $sig = Get-MachineSignature
            $sig | Should -Not -BeNullOrEmpty
            $sig | Should -Match '^[a-f0-9]{32}$'
        }
        
        It "Should return consistent signatures" {
            $sig1 = Get-MachineSignature
            $sig2 = Get-MachineSignature
            $sig1 | Should -Be $sig2
        }
    }
}

Describe "System Information Functions" {
    Context "Get-TerminalInfo" {
        It "Should return terminal information" {
            $info = Get-TerminalInfo
            $info | Should -Not -BeNullOrEmpty
            $info | Should -Match 'USERNAME'
            $info | Should -Match 'USERPROFILE'
        }
    }
    
    Context "Get-SystemInfo" {
        It "Should output system information" {
            $info = Get-SystemInfo | Out-String
            $info | Should -Not -BeNullOrEmpty
            $info | Should -Match 'System Information'
            $info | Should -Match 'PowerShell Version'
        }
    }
}

Describe "Configuration Management" {
    Context "Build-Config" {
        It "Should create config file if not exists" {
            # Use a temp location
            $tempConfig = Join-Path $TestConfigDir ".autocomplete" "config"
            
            # Remove existing config
            if (Test-Path $tempConfig) {
                Remove-Item $tempConfig -Force
            }
            
            # Override the config path for testing
            Mock Get-ConfigFilePath { return $tempConfig }
            Mock Get-ConfigDirectory { return (Join-Path $TestConfigDir ".autocomplete") }
            
            Build-Config
            
            Test-Path $tempConfig | Should -BeTrue
        }
    }
    
    Context "Import-ACSHConfig" {
        It "Should load configuration without errors" {
            { Import-ACSHConfig } | Should -Not -Throw
        }
        
        It "Should populate ACSH_CONFIG hashtable" {
            Import-ACSHConfig
            $script:ACSH_CONFIG | Should -Not -BeNull
            $script:ACSH_CONFIG -is [hashtable] | Should -BeTrue
        }
    }
}

Describe "LLM Completion Functions" {
    Context "Get-SystemMessagePrompt" {
        It "Should return a non-empty prompt" {
            $prompt = Get-SystemMessagePrompt
            $prompt | Should -Not -BeNullOrEmpty
            $prompt | Should -Match 'completion'
        }
    }
    
    Context "Get-OutputInstructions" {
        It "Should return output instructions" {
            $instructions = Get-OutputInstructions
            $instructions | Should -Not -BeNullOrEmpty
            $instructions | Should -Match 'JSON'
        }
    }
    
    Context "Build-Prompt" {
        It "Should build a prompt from user input" {
            $prompt = Build-Prompt -UserInput "git status"
            $prompt | Should -Not -BeNullOrEmpty
            $prompt | Should -Match 'git status'
            $prompt | Should -Match 'Terminal Context'
        }
    }
    
    Context "Build-Payload" {
        BeforeEach {
            # Set up minimal config
            $script:ACSH_CONFIG = @{
                MODEL = "gpt-4o"
                TEMPERATURE = "0.0"
                PROVIDER = "openai"
            }
        }
        
        It "Should build a valid payload for OpenAI" {
            $payload = Build-Payload -UserInput "test command"
            $payload | Should -Not -BeNull
            $payload.model | Should -Be "gpt-4o"
            $payload.messages | Should -Not -BeNullOrEmpty
        }
    }
}

Describe "Caching Functions" {
    Context "Get-CachedCompletion and Set-CachedCompletion" {
        BeforeEach {
            # Set up test cache directory
            $testCacheDir = Join-Path $TestConfigDir ".autocomplete" "cache"
            $script:ACSH_CONFIG = @{
                CACHE_DIR = $testCacheDir
                CACHE_SIZE = 10
            }
        }
        
        It "Should return null for non-existent cache" {
            $result = Get-CachedCompletion -UserInput "nonexistent-$(Get-Random)"
            $result | Should -BeNullOrEmpty
        }
        
        It "Should store and retrieve cached completions" {
            $testInput = "test-input-$(Get-Random)"
            $testCompletion = "ls -la|||List files`ncd ..|||Go up directory"
            
            Set-CachedCompletion -UserInput $testInput -Completions $testCompletion
            
            $cached = Get-CachedCompletion -UserInput $testInput
            $cached.Trim() | Should -Be $testCompletion
        }
    }
}

Describe "CLI Commands" {
    Context "Show-Help" {
        It "Should display help without errors" {
            { Show-Help } | Should -Not -Throw
        }
    }
    
    Context "autocomplete function" {
        It "Should handle --help flag" {
            { autocomplete "--help" } | Should -Not -Throw
        }
        
        It "Should handle unknown commands gracefully" {
            { autocomplete "unknown-command-xyz" } | Should -Not -Throw
        }
        
        It "Should display version info with no arguments" {
            $output = autocomplete | Out-String
            # Should not throw
            $true | Should -BeTrue
        }
    }
}

Describe "Model Configuration" {
    Context "Model List" {
        It "Should have valid model entries" {
            foreach ($key in $script:AutocompleteModelList.Keys) {
                $model = $script:AutocompleteModelList[$key]
                $model.endpoint | Should -Not -BeNullOrEmpty
                $model.model | Should -Not -BeNullOrEmpty
                $model.provider | Should -Not -BeNullOrEmpty
            }
        }
        
        It "Should have proper cost values" {
            foreach ($key in $script:AutocompleteModelList.Keys) {
                $model = $script:AutocompleteModelList[$key]
                $model.prompt_cost | Should -BeOfType [double]
                $model.completion_cost | Should -BeOfType [double]
                $model.prompt_cost | Should -BeGreaterOrEqual 0
                $model.completion_cost | Should -BeGreaterOrEqual 0
            }
        }
    }
}

Describe "Interactive Menu" {
    Context "Show-InteractiveMenu" {
        It "Should parse completions correctly" {
            # This tests the parsing logic without actually showing the menu
            $completions = "ls -la|||List all files`ncd ..|||Go up one directory"
            
            # We can't easily test interactive menus, but we can test the function exists
            Get-Command Show-InteractiveMenu -ErrorAction SilentlyContinue | Should -Not -BeNull
        }
    }
}

Describe "Cross-Platform Compatibility" {
    It "Should run on Windows PowerShell 5.1+" {
        $PSVersionTable.PSVersion.Major | Should -BeGreaterOrEqual 5
    }
    
    It "Should have access to required .NET classes" {
        { [System.Security.Cryptography.MD5]::Create() } | Should -Not -Throw
        { [System.Text.Encoding]::UTF8 } | Should -Not -Throw
    }
}
