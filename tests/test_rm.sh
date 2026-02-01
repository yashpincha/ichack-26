#!/bin/bash

# Create test file
echo "test" > /tmp/test_rm_file.txt

# Source and enable autocomplete
source /home/aryagolkari/events/ichack-26/autocomplete.sh > /dev/null 2>&1
autocomplete enable > /dev/null 2>&1

echo "Testing rm command..."
echo "y" | timeout 3 rm /tmp/test_rm_file.txt 2>&1

if [ $? -eq 0 ]; then
    echo "Success: rm executed without hanging"
    exit 0
else
    echo "Failed: rm command timed out or errored"
    exit 1
fi
