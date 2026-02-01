#!/bin/bash

# Detect the current shell
detect_shell() {
    if [ -n "$BASH_VERSION" ]; then
        echo "bash"
    else
        # Check the parent process's shell
        parent_shell=$(ps -p $PPID -o comm=)
        case "$parent_shell" in
            *bash*) echo "bash" ;;
            *) echo "unknown" ;;
        esac
    fi
}

SHELL_TYPE=$(detect_shell)
case "$SHELL_TYPE" in
    bash)
        SCRIPT_NAME="clam.sh"
        ;;
    *)
        echo "ERROR: Unsupported shell. Currently only bash is supported."
        exit 1
        ;;
esac

# The default location to install the LLMs
INSTALL_LOCATION="$HOME/.local/bin/$SCRIPT_NAME"

# Check if INSTALL_LOCATION exists, if not, set to /usr/local/bin
if [ ! -d "$(dirname "$INSTALL_LOCATION")" ]; then
    INSTALL_LOCATION="/usr/local/bin/$SCRIPT_NAME"
fi

# Copy local clam.sh file
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cp "$SCRIPT_DIR/clam.sh" "$INSTALL_LOCATION"

# Install the LLMs
chmod +x "$INSTALL_LOCATION"

# Create symlink without .sh extension for easier command usage
SYMLINK_LOCATION="$(dirname "$INSTALL_LOCATION")/clam"
rm -f "$SYMLINK_LOCATION"
ln -s "$INSTALL_LOCATION" "$SYMLINK_LOCATION"

# Check if jq is installed
if ! command -v jq > /dev/null 2>&1; then
    echo "ERROR: jq is not installed. Please install jq to continue."
    echo "For Ubuntu/Debian: sudo apt-get install jq"
    echo "For CentOS/RHEL: sudo yum install jq"
    echo "For macOS (using Homebrew): brew install jq"
    exit 1
fi

# Source bash-completion if _init_completion function does not exist
if ! command -v _init_completion > /dev/null 2>&1; then
    # shellcheck disable=SC1091
    if [ -f /usr/share/bash-completion/bash_completion ]; then
        . /usr/share/bash-completion/bash_completion
    elif [ -f /etc/bash_completion ]; then
        . /etc/bash_completion
    else
        echo "ERROR: Please ensure you have bash-completion installed and sourced."
        exit 1
    fi
fi

# Proceed with installation
"$INSTALL_LOCATION" install
