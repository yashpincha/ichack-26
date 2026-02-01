#!/bin/bash
#
# AI Terminal - Linux Installation Script
# Supports: Ubuntu, Debian, Fedora, Arch
#
set -e

echo "========================================"
echo "   AI Terminal - Linux Installer"
echo "========================================"
echo ""

# Detect distro
if [ -f /etc/os-release ]; then
    . /etc/os-release
    DISTRO=$ID
else
    echo "Cannot detect Linux distribution"
    exit 1
fi

echo "Detected: $DISTRO"
echo ""

# Install system dependencies based on distro
echo "[1/4] Installing system dependencies..."
case $DISTRO in
    ubuntu|debian|pop|linuxmint)
        sudo apt update
        sudo apt install -y \
            build-essential \
            curl \
            wget \
            file \
            libssl-dev \
            libgtk-3-dev \
            libwebkit2gtk-4.1-dev \
            libayatana-appindicator3-dev \
            librsvg2-dev \
            git
        ;;
    fedora)
        sudo dnf install -y \
            @development-tools \
            curl \
            wget \
            file \
            openssl-devel \
            gtk3-devel \
            webkit2gtk4.1-devel \
            libappindicator-gtk3-devel \
            librsvg2-devel \
            git
        ;;
    arch|manjaro|endeavouros)
        sudo pacman -S --noconfirm \
            base-devel \
            curl \
            wget \
            file \
            openssl \
            gtk3 \
            webkit2gtk-4.1 \
            appmenu-gtk-module \
            libappindicator-gtk3 \
            librsvg \
            git
        ;;
    *)
        echo "Unsupported distribution: $DISTRO"
        echo "Please install dependencies manually."
        exit 1
        ;;
esac
echo "System dependencies installed."
echo ""

# Install Node.js via nvm
echo "[2/4] Installing Node.js..."
if command -v node &> /dev/null && [[ $(node -v | cut -d. -f1 | tr -d 'v') -ge 18 ]]; then
    echo "Node.js $(node -v) already installed."
else
    curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.40.1/install.sh | bash
    export NVM_DIR="$HOME/.nvm"
    [ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"
    nvm install 18
    echo "Node.js installed: $(node -v)"
fi
echo ""

# Install Rust
echo "[3/4] Installing Rust..."
if command -v rustc &> /dev/null; then
    echo "Rust $(rustc --version) already installed."
else
    curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y
    source "$HOME/.cargo/env"
    echo "Rust installed: $(rustc --version)"
fi
echo ""

# Install npm dependencies
echo "[4/4] Installing npm dependencies..."
npm install
echo ""

echo "========================================"
echo "   Installation Complete!"
echo "========================================"
echo ""
echo "To run the AI Terminal:"
echo "  npm run tauri dev"
echo ""
echo "To build for production:"
echo "  npm run tauri build"
echo ""
echo "Don't forget to set your API key in Settings!"
echo ""
