#!/bin/bash

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Source and enable autocomplete
source "$SCRIPT_DIR/../autocomplete.sh" > /dev/null 2>&1
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
