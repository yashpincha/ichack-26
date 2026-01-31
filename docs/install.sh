#!/bin/sh

# AutoComplete - brings LLMs into the Terminal
# This install script downloads the latest version and handles cross-platform installation
# Supports: Linux, macOS, Windows (Git Bash/WSL)

# The URL of the latest version of the LLMs
ACSH_VERSION="v0.5.0"
BRANCH_OR_VERSION=${1:-$ACSH_VERSION}

# Detect the operating system
detect_os() {
    case "$(uname -s)" in
        Linux*)  echo "linux" ;;
        Darwin*) echo "macos" ;;
        CYGWIN*|MINGW*|MSYS*) echo "windows" ;;
        *)       echo "unknown" ;;
    esac
}

# Detect the current shell
detect_shell() {
    if [ -n "$ZSH_VERSION" ]; then
        echo "zsh"
    elif [ -n "$BASH_VERSION" ]; then
        echo "bash"
    else
        # Check the parent process's shell
        if [ "$(detect_os)" = "macos" ]; then
            parent_shell=$(ps -p $PPID -o comm= 2>/dev/null)
        else
            parent_shell=$(ps -p $PPID -o comm= 2>/dev/null)
        fi
        case "$parent_shell" in
            *zsh*) echo "zsh" ;;
            *bash*) echo "bash" ;;
            *) echo "unknown" ;;
        esac
    fi
}

OS_TYPE=$(detect_os)
SHELL_TYPE=$(detect_shell)

echo "Detected OS: $OS_TYPE"
echo "Detected Shell: $SHELL_TYPE"

# Set script name based on shell
case "$SHELL_TYPE" in
    zsh)
        SCRIPT_NAME="autocomplete.zsh"
        ;;
    bash)
        SCRIPT_NAME="autocomplete.sh"
        ;;
    *)
        echo "ERROR: Unsupported shell. Currently only bash and zsh are supported."
        echo "For Windows PowerShell, please use: irm https://autocomplete.sh/install.ps1 | iex"
        exit 1
        ;;
esac

# Set install location based on OS
case "$OS_TYPE" in
    macos)
        # macOS: prefer ~/.local/bin or /usr/local/bin
        if [ -d "$HOME/.local/bin" ]; then
            INSTALL_LOCATION="$HOME/.local/bin/$SCRIPT_NAME"
        elif [ -d "/usr/local/bin" ]; then
            INSTALL_LOCATION="/usr/local/bin/$SCRIPT_NAME"
        else
            mkdir -p "$HOME/.local/bin"
            INSTALL_LOCATION="$HOME/.local/bin/$SCRIPT_NAME"
            echo "Created $HOME/.local/bin directory"
            echo "You may need to add it to your PATH: export PATH=\"\$HOME/.local/bin:\$PATH\""
        fi
        ;;
    windows)
        # Windows (Git Bash/WSL): use ~/.local/bin
        mkdir -p "$HOME/.local/bin" 2>/dev/null
        INSTALL_LOCATION="$HOME/.local/bin/$SCRIPT_NAME"
        ;;
    linux|*)
        # Linux: prefer ~/.local/bin or /usr/local/bin
        if [ -d "$HOME/.local/bin" ]; then
            INSTALL_LOCATION="$HOME/.local/bin/$SCRIPT_NAME"
        elif [ -d "/usr/local/bin" ] && [ -w "/usr/local/bin" ]; then
            INSTALL_LOCATION="/usr/local/bin/$SCRIPT_NAME"
        else
            mkdir -p "$HOME/.local/bin"
            INSTALL_LOCATION="$HOME/.local/bin/$SCRIPT_NAME"
        fi
        ;;
esac

echo "Installing to: $INSTALL_LOCATION"

# Install from local file or download from GitHub
if [ "$BRANCH_OR_VERSION" = "dev" ]; then
    # Use local autocomplete file
    if [ -f "./$SCRIPT_NAME" ]; then
        cp "./$SCRIPT_NAME" "$INSTALL_LOCATION"
        echo "Installed local development version to $INSTALL_LOCATION"
    else
        echo "ERROR: Local $SCRIPT_NAME file not found."
        exit 1
    fi
else
    # Download from GitHub - prefer curl over wget for better cross-platform support
    URL="https://raw.githubusercontent.com/closedloop-technologies/autocomplete-sh/${BRANCH_OR_VERSION}/$SCRIPT_NAME"
    
    if command -v curl > /dev/null 2>&1; then
        curl -fsSL "$URL" -o "$INSTALL_LOCATION"
    elif command -v wget > /dev/null 2>&1; then
        wget -nv -O "$INSTALL_LOCATION" "$URL"
    else
        echo "ERROR: Neither curl nor wget is available. Please install one of them."
        exit 1
    fi
fi

# Make the script executable
chmod +x "$INSTALL_LOCATION"

# Check if jq is installed
if ! command -v jq > /dev/null 2>&1; then
    echo ""
    echo "WARNING: jq is not installed. jq is required for autocomplete to function."
    case "$OS_TYPE" in
        macos)
            echo "Install with: brew install jq"
            ;;
        linux)
            echo "Install with:"
            echo "  Ubuntu/Debian: sudo apt-get install jq"
            echo "  CentOS/RHEL:   sudo yum install jq"
            echo "  Arch Linux:    sudo pacman -S jq"
            ;;
        windows)
            echo "Install with: choco install jq  (or use Git Bash's package manager)"
            ;;
    esac
    echo ""
fi

# Source bash-completion if _init_completion function does not exist (bash only)
if [ "$SHELL_TYPE" = "bash" ]; then
    if ! command -v _init_completion > /dev/null 2>&1; then
        # Try to source bash-completion
        sourced=false
        
        if [ -f /usr/share/bash-completion/bash_completion ]; then
            # shellcheck disable=SC1091
            . /usr/share/bash-completion/bash_completion
            sourced=true
        elif [ -f /etc/bash_completion ]; then
            # shellcheck disable=SC1091
            . /etc/bash_completion
            sourced=true
        elif [ -f /opt/homebrew/etc/profile.d/bash_completion.sh ]; then
            # macOS with Homebrew (Apple Silicon)
            # shellcheck disable=SC1091
            . /opt/homebrew/etc/profile.d/bash_completion.sh
            sourced=true
        elif [ -f /usr/local/etc/profile.d/bash_completion.sh ]; then
            # macOS with Homebrew (Intel)
            # shellcheck disable=SC1091
            . /usr/local/etc/profile.d/bash_completion.sh
            sourced=true
        fi
        
        if [ "$sourced" = false ]; then
            echo ""
            echo "WARNING: bash-completion not found."
            case "$OS_TYPE" in
                macos)
                    echo "Install with: brew install bash-completion@2"
                    ;;
                linux)
                    echo "Install with:"
                    echo "  Ubuntu/Debian: sudo apt-get install bash-completion"
                    echo "  CentOS/RHEL:   sudo yum install bash-completion"
                    ;;
            esac
            echo ""
        fi
    fi
fi

# Create symlink for 'autocomplete' command if needed
AUTOCOMPLETE_SYMLINK=""
case "$OS_TYPE" in
    macos|linux)
        if [ -d "$HOME/.local/bin" ]; then
            AUTOCOMPLETE_SYMLINK="$HOME/.local/bin/autocomplete"
        elif [ -d "/usr/local/bin" ] && [ -w "/usr/local/bin" ]; then
            AUTOCOMPLETE_SYMLINK="/usr/local/bin/autocomplete"
        fi
        ;;
    windows)
        AUTOCOMPLETE_SYMLINK="$HOME/.local/bin/autocomplete"
        ;;
esac

if [ -n "$AUTOCOMPLETE_SYMLINK" ] && [ ! -f "$AUTOCOMPLETE_SYMLINK" ]; then
    ln -sf "$INSTALL_LOCATION" "$AUTOCOMPLETE_SYMLINK" 2>/dev/null || true
fi

echo ""
echo "Installation complete!"

# Proceed with installation
"$INSTALL_LOCATION" install
