#!/bin/bash

# Create test file
mkdir -p /tmp/test_dir
echo "test" > /tmp/test_dir/testfile.txt

# Source and enable autocomplete
source /home/aryagolkari/events/ichack-26/autocomplete.sh > /dev/null 2>&1
autocomplete enable > /dev/null 2>&1

echo "Test 1: Safe command (should execute without warning)"
echo "------"
ls /tmp/test_dir/testfile.txt 2>&1 | head -5
echo ""

echo "Test 2: Potentially harmful command (should show warning)"
echo "------"
# Use a command that will be flagged as harmful
# Answer 'n' to cancel it
echo "n" | timeout 5 chmod 777 /etc/passwd 2>&1 | grep -E "WARNING|Risk Level|Command cancelled" | head -5

echo ""
echo "Test 3: Clean up - user says yes to safe rm"
echo "------"
echo "y" | rm /tmp/test_dir/testfile.txt 2>&1 | head -3
rmdir /tmp/test_dir 2>/dev/null

echo ""
echo "All tests completed!"
