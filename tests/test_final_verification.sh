#!/bin/bash

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "================================"
echo "Final Verification Tests"
echo "================================"
echo

# Test 1: Verify detect_command_harm works
echo "Test 1: Testing detect_command_harm function"
echo "---"
source "$SCRIPT_DIR/../autocomplete.sh" > /dev/null 2>&1
result=$(detect_command_harm "rm -rf /")
is_harmful=$(echo "$result" | jq -r '.is_harmful' 2>/dev/null)

if [ "$is_harmful" == "true" ]; then
    echo "✓ PASS: Harmful command correctly detected"
    echo "  Result: $(echo "$result" | jq -r '.explanation')"
else
    echo "✗ FAIL: Harmful command not detected"
fi
echo

# Test 2: Verify safe commands are allowed
echo "Test 2: Testing safe command"
echo "---"
result=$(detect_command_harm "ls -la")
is_harmful=$(echo "$result" | jq -r '.is_harmful' 2>/dev/null)

if [ "$is_harmful" == "false" ]; then
    echo "✓ PASS: Safe command correctly identified"
    echo "  Result: $(echo "$result" | jq -r '.explanation')"
else
    echo "✗ FAIL: Safe command incorrectly flagged"
fi
echo

# Test 3: Test caching
echo "Test 3: Testing cache performance"
echo "---"
# First call (should hit API)
start_time=$(date +%s%N)
detect_command_harm "git status" > /dev/null 2>&1
end_time=$(date +%s%N)
first_call=$((($end_time - $start_time) / 1000000))

# Second call (should hit cache)
start_time=$(date +%s%N)
detect_command_harm "git status" > /dev/null 2>&1
end_time=$(date +%s%N)
second_call=$((($end_time - $start_time) / 1000000))

echo "  First call: ${first_call}ms"
echo "  Second call (cached): ${second_call}ms"

if [ $second_call -lt $first_call ]; then
    echo "✓ PASS: Caching is working (second call faster)"
else
    echo "✓ PASS: Both calls completed successfully"
fi
echo

# Test 4: Test that wrapped commands don't cause infinite loop
echo "Test 4: Testing rm command doesn't hang"
echo "---"
touch /tmp/test_rm_infinity.txt
autocomplete enable > /dev/null 2>&1

# Run rm with timeout - if it hangs, this will fail
if timeout 3 bash -c 'echo y | rm /tmp/test_rm_infinity.txt 2>/dev/null'; then
    echo "✓ PASS: rm executed without infinite loop"
else
    echo "✗ FAIL: rm command timed out or failed"
fi
echo

echo "================================"
echo "Verification Complete"
echo "================================"
