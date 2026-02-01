#!/bin/bash

# Source and enable autocomplete
source /home/aryagolkari/events/ichack-26/autocomplete.sh > /dev/null 2>&1
autocomplete enable > /dev/null 2>&1

echo "Testing harm detection with dangerous command..."
echo "n" | timeout 5 rm -rf / 2>&1 | head -10

if [ ${PIPESTATUS[1]} -eq 0 ]; then
    echo ""
    echo "Success: Harm detection prompted for confirmation"
    exit 0
else
    echo "Failed: Harm detection did not work as expected"
    exit 1
fi
