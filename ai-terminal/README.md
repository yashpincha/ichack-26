# AI Terminal

A cross-platform terminal application with AI-powered inline autocomplete suggestions, similar to GitHub Copilot but for shell commands.

## Features

- **Ghost Text Autocomplete**: Real-time inline suggestions appear as you type, just like Copilot
- **Command Explanations**: Hover over suggestions to see why they were recommended
- **Harm Detection**: AI-powered analysis warns you before running dangerous commands
- **Safeguards**: Pattern-based protection against destructive commands (rm -rf, chmod 777, etc.)
- **Fix Error Please (FEP)**: Press Ctrl+F after a failed command to get AI-suggested fixes
- **Usage Statistics**: Track API usage and costs
- **Multiple AI Providers**: Support for OpenAI, Anthropic, Groq, and local Ollama models
- **Cross-Platform**: Works on Windows, macOS, and Linux
- **Context-Aware**: Considers command history, current directory, and environment
- **Privacy-Focused**: Sensitive data is sanitized before sending to AI providers
- **Lightweight**: Built with Tauri for a small footprint (~10MB vs Electron's 150MB+)

---

## Installation

### Linux (Ubuntu/Debian)

#### Step 1: Install System Dependencies

```bash
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
```

#### Step 2: Install Node.js

```bash
# Install nvm (Node Version Manager)
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.40.1/install.sh | bash

# Reload shell
source ~/.bashrc

# Install Node.js 18
nvm install 18

# Verify
node --version   # Should show v18.x.x
```

#### Step 3: Install Rust

```bash
# Install Rust
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh

# Press 1 for default installation when prompted

# Reload shell
source ~/.cargo/env

# Verify
rustc --version   # Should show 1.70.0 or higher
```

#### Step 4: Clone and Run

```bash
# Clone the repository
git clone https://github.com/yashpincha/ichack-26.git
cd ichack-26/ai-terminal

# Install dependencies
npm install

# Run in development mode
npm run tauri dev

# OR build for production
npm run tauri build
```

---

### Linux (Fedora)

```bash
# System dependencies
sudo dnf install -y @development-tools curl wget file openssl-devel gtk3-devel webkit2gtk4.1-devel libappindicator-gtk3-devel librsvg2-devel git

# Then follow Steps 2-4 above
```

### Linux (Arch)

```bash
# System dependencies
sudo pacman -S --noconfirm base-devel curl wget file openssl gtk3 webkit2gtk-4.1 appmenu-gtk-module libappindicator-gtk3 librsvg git

# Then follow Steps 2-4 above
```

---

### Windows

#### Prerequisites
- [Node.js 18+](https://nodejs.org/)
- [Rust](https://rustup.rs/)
- [Visual Studio Build Tools](https://visualstudio.microsoft.com/visual-cpp-build-tools/)

```powershell
# Clone and run
git clone https://github.com/yashpincha/ichack-26.git
cd ichack-26\ai-terminal
npm install
npm run tauri dev
```

---

### macOS

```bash
# Install Xcode Command Line Tools
xcode-select --install

# Install Homebrew (if not installed)
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install Node.js and Rust
brew install node
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
source ~/.cargo/env

# Clone and run
git clone https://github.com/yashpincha/ichack-26.git
cd ichack-26/ai-terminal
npm install
npm run tauri dev
```

---

## Quick Start Script (Linux)

Copy and paste this entire script for Ubuntu/Debian:

```bash
#!/bin/bash
set -e

echo "Installing system dependencies..."
sudo apt update
sudo apt install -y build-essential curl wget file libssl-dev libgtk-3-dev libwebkit2gtk-4.1-dev libayatana-appindicator3-dev librsvg2-dev git

echo "Installing Node.js..."
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.40.1/install.sh | bash
export NVM_DIR="$HOME/.nvm"
[ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"
nvm install 18

echo "Installing Rust..."
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y
source ~/.cargo/env

echo "Cloning repository..."
git clone https://github.com/yashpincha/ichack-26.git
cd ichack-26/ai-terminal

echo "Installing npm packages..."
npm install

echo "Starting AI Terminal..."
npm run tauri dev
```

---

## Usage

### Keyboard Shortcuts

| Key | Action |
|-----|--------|
| Tab | Accept suggestion |
| Right Arrow | Accept suggestion |
| Esc | Dismiss suggestion / Close modal |
| Ctrl+F | Fix Error Please (after failed command) |
| Ctrl+C | Cancel current command |
| Ctrl+U | Clear current line |
| Enter | Execute command |

### Autocomplete

1. Start typing a command
2. Ghost text appears with suggestion
3. Hover to see explanation (if enabled)
4. Press **Tab** or **Right Arrow** to accept
5. Press **Esc** to dismiss

### Safety Features

**Pattern Safeguards** (instant, local):
- Triggers on dangerous patterns like `rm -rf /`, `chmod 777`, fork bombs
- Shows confirmation modal before execution

**AI Harm Detection** (intelligent, requires API):
- Analyzes commands for potential risks
- Categories: destructive operations, permission changes, network risks
- Shows detailed warning with severity level

**Fix Error Please (FEP)**:
1. Run a command that fails
2. See "Error detected" in status bar
3. Press **Ctrl+F**
4. Review the suggested fix
5. Click "Apply Fix" to use it

---

## Configuration

### Via Settings UI

Click the ⚙️ settings button in the app to configure:

**General Tab:**
- AI Provider (OpenAI, Anthropic, Groq, Ollama)
- Model selection
- API Key
- Ghost text toggle
- Show explanations toggle
- Debounce time
- Temperature

**Safety Tab:**
- Enable/disable pattern safeguards
- Enable/disable AI harm detection

**Usage Tab:**
- View request counts and costs
- Clear statistics

### Config File Location

| OS | Path |
|----|------|
| Linux | `~/.config/ai-terminal/config.json` |
| macOS | `~/Library/Application Support/ai-terminal/config.json` |
| Windows | `%APPDATA%\ai-terminal\config.json` |

### Example Config

```json
{
  "provider": "openai",
  "model": "gpt-4o-mini",
  "api_key": "sk-your-api-key-here",
  "endpoint": null,
  "debounce_ms": 300,
  "ghost_text_enabled": true,
  "temperature": 0.0,
  "max_suggestions": 1,
  "max_history_commands": 20,
  "safeguards_enabled": true,
  "harm_detection_enabled": true,
  "show_explanations": true
}
```

---

## Supported AI Providers

| Provider | Models | API Key Required | Cost |
|----------|--------|------------------|------|
| OpenAI | GPT-4o, GPT-4o Mini, O1 Mini | Yes | Paid |
| Anthropic | Claude 3.5 Sonnet, Claude 3.5 Haiku | Yes | Paid |
| Groq | Llama 3 70B, Llama 3 8B, Mixtral 8x7B | Yes | Free |
| Ollama | Any local model | No | Free |

### Getting API Keys

- **OpenAI**: [platform.openai.com/api-keys](https://platform.openai.com/api-keys)
- **Anthropic**: [console.anthropic.com/settings/keys](https://console.anthropic.com/settings/keys)
- **Groq**: [console.groq.com/keys](https://console.groq.com/keys) (Free!)
- **Ollama**: Install from [ollama.ai](https://ollama.ai/) - No key needed

---

## Architecture

```
ai-terminal/
├── src-tauri/              # Rust backend
│   ├── src/
│   │   ├── main.rs         # Entry point
│   │   ├── lib.rs          # Tauri commands
│   │   ├── pty.rs          # PTY management
│   │   ├── config.rs       # Configuration
│   │   ├── cache.rs        # Response caching
│   │   ├── context.rs      # Terminal context
│   │   ├── harm.rs         # Harm detection
│   │   ├── safeguard.rs    # Pattern safeguards
│   │   ├── fep.rs          # Fix Error Please
│   │   ├── usage.rs        # Usage statistics
│   │   └── llm/            # LLM providers
│   └── Cargo.toml
├── src/                    # React frontend
│   ├── components/
│   │   ├── Terminal.tsx    # xterm.js wrapper
│   │   ├── GhostText.tsx   # Inline suggestions
│   │   ├── Settings.tsx    # Config UI
│   │   ├── HarmWarning.tsx # Harm warning modal
│   │   ├── SafeguardConfirm.tsx  # Safeguard modal
│   │   ├── FixSuggestion.tsx     # FEP modal
│   │   └── UsageStats.tsx  # Usage display
│   ├── hooks/
│   │   └── useAutocomplete.ts
│   └── styles/
│       └── global.css
└── package.json
```

---

## Development

### Building

```bash
# Development (hot reload)
npm run tauri dev

# Production build
npm run tauri build

# Built app location: src-tauri/target/release/
```

### Testing

```bash
# Rust tests
cd src-tauri && cargo test

# Type checking
npm run build
```

---

## Troubleshooting

### Linux: WebKit not found

```bash
# Ubuntu/Debian
sudo apt install libwebkit2gtk-4.1-dev

# Fedora
sudo dnf install webkit2gtk4.1-devel

# Arch
sudo pacman -S webkit2gtk-4.1
```

### Node.js version too old

```bash
nvm install 18
nvm use 18
```

### Rust not found after install

```bash
source ~/.cargo/env
# Or add to ~/.bashrc:
# export PATH="$HOME/.cargo/bin:$PATH"
```

### API key not working

1. Check the key is correct (no extra spaces)
2. Verify the provider matches the key type
3. Check your API quota/credits

---

## License

MIT License - see [LICENSE](LICENSE) for details.

## Acknowledgments

- Built with [Tauri](https://tauri.app/)
- Terminal emulation by [xterm.js](https://xtermjs.org/)
- Inspired by [autocomplete.sh](https://autocomplete.sh/)
