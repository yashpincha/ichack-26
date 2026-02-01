<div align="center">

# ⚡ AI Terminal

### Your Intelligent Command-Line Companion

[![Build Status](https://img.shields.io/badge/build-passing-brightgreen?style=flat-square)](https://github.com/yashpincha/ichack-26)
[![Version](https://img.shields.io/badge/version-0.1.0-blue?style=flat-square)](https://github.com/yashpincha/ichack-26/releases)
[![License](https://img.shields.io/badge/license-MIT-green?style=flat-square)](./LICENSE)
[![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey?style=flat-square)](https://github.com/yashpincha/ichack-26)
[![Made with Tauri](https://img.shields.io/badge/made%20with-Tauri-orange?style=flat-square)](https://tauri.app)
[![ICHack '26](https://img.shields.io/badge/ICHack-'26-purple?style=flat-square)](https://ichack.org)

**Type less. Do more. Stay safe.**

[Features](#-features) • [Installation](#-installation) • [Quick Start](#-quick-start) • [Documentation](#-documentation) • [Contributing](#-contributing)

</div>

---

## 🎯 What is AI Terminal?

**AI Terminal** is a modern, AI-powered terminal application designed to make the command line accessible and safe for everyone—especially beginners. It provides **real-time autocomplete suggestions**, **safety warnings for dangerous commands**, and **intelligent error fixing**—all powered by state-of-the-art AI models.

> 💡 **Perfect for beginners**: No more memorizing complex commands or worrying about accidentally breaking your system!

### Why AI Terminal?

| Problem | AI Terminal Solution |
|---------|---------------------|
| 😰 Can't remember command syntax | ✅ Ghost text shows suggestions as you type |
| 😱 Afraid of running dangerous commands | ✅ Two-layer safety system warns you first |
| 😤 Cryptic error messages | ✅ Press **Ctrl+F** to get AI-powered fixes |
| 💸 Worried about API costs | ✅ Built-in usage tracking and caching |

---

## ✨ Features

### 🔮 **Intelligent Autocomplete**
See AI-powered suggestions appear as ghost text while you type. Press **Tab** to accept instantly.

```
$ git ch░                    
       └── eckout main   ← Ghost text suggestion (press Tab to accept)
```

### 🛡️ **Two-Layer Safety System**
Never accidentally run a dangerous command again.

- **Pattern Safeguards** (Fast, Local): Catches known dangerous patterns like `rm -rf /`
- **AI Harm Detection** (Intelligent): Analyzes commands for potential risks

```
⚠️ CRITICAL RISK
Command: rm -rf /
Warning: Recursive deletion of root filesystem
[Cancel] [Proceed Anyway]
```

### 🔧 **Fix Error Please (FEP)**
When a command fails, press **Ctrl+F** to get an AI-suggested fix.

```
❌ Failed: git pussh origin main
   Exit code: 1

🔧 Suggested Fix: git push origin main
   Explanation: Fixed typo in 'push' command
   Confidence: HIGH
   
   [Apply Fix] [Dismiss]
```

### 📊 **Usage & Cost Tracking**
Monitor your API usage and estimated costs in real-time.

### 🌐 **Multi-Provider Support**
Choose your preferred AI provider:
- **OpenAI** (GPT-4o, GPT-4o-mini)
- **Anthropic** (Claude 3.5 Sonnet, Haiku)
- **Groq** (Llama 3, Mixtral) — *Free!*
- **Ollama** (Local models) — *Free!*

---

## 📋 Table of Contents

- [Features](#-features)
- [Installation](#-installation)
  - [Windows](#windows)
  - [macOS](#macos)
  - [Linux](#linux)
  - [Building from Source](#building-from-source)
- [Quick Start](#-quick-start)
- [Documentation](#-documentation)
  - [Using Autocomplete](#using-autocomplete)
  - [Safety Features](#safety-features)
  - [Fix Error Please (FEP)](#fix-error-please-fep)
  - [Keyboard Shortcuts](#keyboard-shortcuts)
- [Configuration](#️-configuration)
- [Examples](#-examples)
- [Troubleshooting](#-troubleshooting)
- [Contributing](#-contributing)
- [License](#-license)
- [Acknowledgments](#-acknowledgments)

---

## 📦 Installation

### Prerequisites

- An API key from one of the supported providers (or use Ollama for free local inference)

### Windows

1. **Download the installer** from the [Releases](https://github.com/yashpincha/ichack-26/releases) page
2. Run `AI-Terminal_x.x.x_x64-setup.exe`
3. Follow the installation wizard
4. Launch **AI Terminal** from the Start Menu

### macOS

1. **Download the DMG** from the [Releases](https://github.com/yashpincha/ichack-26/releases) page
2. Open the `.dmg` file
3. Drag **AI Terminal** to your Applications folder
4. Launch from Applications or Spotlight

### Linux

**Debian/Ubuntu (.deb):**
```bash
wget https://github.com/yashpincha/ichack-26/releases/download/v0.1.0/ai-terminal_0.1.0_amd64.deb
sudo dpkg -i ai-terminal_0.1.0_amd64.deb
```

**Fedora/RHEL (.rpm):**
```bash
wget https://github.com/yashpincha/ichack-26/releases/download/v0.1.0/ai-terminal-0.1.0.x86_64.rpm
sudo rpm -i ai-terminal-0.1.0.x86_64.rpm
```

**AppImage (Universal):**
```bash
wget https://github.com/yashpincha/ichack-26/releases/download/v0.1.0/ai-terminal_0.1.0_amd64.AppImage
chmod +x ai-terminal_0.1.0_amd64.AppImage
./ai-terminal_0.1.0_amd64.AppImage
```

### Building from Source

**Requirements:**
- [Node.js](https://nodejs.org/) (v18+)
- [Rust](https://rustup.rs/) (latest stable)
- [Tauri CLI](https://tauri.app/v1/guides/getting-started/prerequisites)

```bash
# Clone the repository
git clone https://github.com/yashpincha/ichack-26.git
cd ichack-26/ai-terminal

# Install dependencies
npm install

# Run in development mode
npm run tauri dev

# Build for production
npm run tauri build
```

---

## 🚀 Quick Start

### 1. Launch AI Terminal

Open AI Terminal from your applications menu or run the executable.

### 2. Configure Your API Key

Click the **⚙️ Settings** button in the top-right corner:

1. Select your **AI Provider** (e.g., OpenAI, Groq)
2. Enter your **API Key**
3. Choose a **Model** (we recommend GPT-4o-mini for speed/cost balance)
4. Click **Save**

> 💡 **Tip:** Use **Groq** or **Ollama** for free API access!

### 3. Start Typing!

```bash
# Start typing a command...
$ git che

# You'll see ghost text appear:
$ git che░ckout main

# Press Tab to accept the suggestion!
$ git checkout main
```

### 4. Stay Safe

If you try to run a potentially dangerous command, you'll see a warning:

```bash
$ rm -rf /
# ⚠️ A warning modal appears before execution
```

### 5. Fix Errors Instantly

```bash
$ pythno script.py
# Error: command not found

# Press Ctrl+F to get a fix suggestion!
# 🔧 Suggested: python script.py
```

---

## 📖 Documentation

### Using Autocomplete

AI Terminal provides **ghost text** autocomplete suggestions as you type. The suggestions appear in a lighter color after your cursor.

**How it works:**
1. Start typing a command (minimum 2 characters)
2. Wait ~300ms for suggestions to appear
3. The AI considers:
   - Your command history
   - Current working directory
   - Environment variables
   - Common command patterns

**Accepting Suggestions:**

| Action | Key |
|--------|-----|
| Accept full suggestion | `Tab` or `→` (Right Arrow) |
| Dismiss suggestion | `Escape` |
| Continue typing | Just keep typing |

**Understanding Explanations:**

Hover over the **ⓘ** icon next to suggestions to see why the AI recommended it:

```
$ git ch░eckout main  ⓘ
                      └── "Switch to the main branch"
```

---

### Safety Features

AI Terminal has **two layers** of protection:

#### Layer 1: Pattern Safeguards (Local, Instant)

Checks commands against known dangerous patterns:

| Pattern | Risk Level | Description |
|---------|------------|-------------|
| `rm -rf /` | 🔴 Critical | Deletes entire filesystem |
| `rm -rf ~` | 🔴 Critical | Deletes home directory |
| `:(){:\|:&};:` | 🔴 Critical | Fork bomb |
| `curl \| bash` | 🔴 Critical | Remote code execution |
| `chmod 777` | 🟡 Medium | Insecure permissions |
| `shutdown` | 🟠 High | System shutdown |

#### Layer 2: AI Harm Detection (Intelligent)

Uses AI to analyze commands for potential harm, catching risks that pattern matching might miss.

**Toggling Safety Features:**

1. Open **Settings** (⚙️)
2. Go to the **Safety** tab
3. Toggle:
   - ✅ **Safeguards Enabled** (pattern-based)
   - ✅ **Harm Detection Enabled** (AI-based)

---

### Fix Error Please (FEP)

When a command fails, AI Terminal can suggest fixes:

1. Run a command that fails
2. Notice the **"Error detected"** indicator in the status bar
3. Press **Ctrl+F** to open the Fix Suggestion modal
4. Review the suggested fix and explanation
5. Click **Apply Fix** to paste the corrected command

**Example:**

```bash
$ git comit -m "Update readme"
# Error: git: 'comit' is not a git command

# Press Ctrl+F...
# 🔧 Suggested: git commit -m "Update readme"
# Explanation: Fixed typo - 'comit' should be 'commit'
# Confidence: HIGH
```

---

### Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `Tab` | Accept autocomplete suggestion |
| `→` (Right Arrow) | Accept autocomplete suggestion |
| `Escape` | Dismiss suggestion or close modal |
| `Ctrl+F` | Get fix for last failed command |
| `Ctrl+C` | Cancel current command |
| `Ctrl+U` | Clear current line |

---

## ⚙️ Configuration

### Settings Location

Configuration is stored at:
- **Windows:** `%APPDATA%\ai-terminal\config.json`
- **macOS:** `~/Library/Application Support/ai-terminal/config.json`
- **Linux:** `~/.config/ai-terminal/config.json`

### Configuration Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `provider` | string | `"openai"` | AI provider (`openai`, `anthropic`, `groq`, `ollama`) |
| `model` | string | `"gpt-4o-mini"` | Model to use for completions |
| `api_key` | string | `""` | Your API key |
| `endpoint` | string | `null` | Custom API endpoint (optional) |
| `debounce_ms` | number | `300` | Delay before fetching suggestions |
| `ghost_text_enabled` | boolean | `true` | Show autocomplete ghost text |
| `temperature` | number | `0.0` | Model temperature (0 = deterministic) |
| `safeguards_enabled` | boolean | `true` | Enable pattern-based safeguards |
| `harm_detection_enabled` | boolean | `true` | Enable AI harm detection |
| `show_explanations` | boolean | `true` | Show explanation tooltips |

### Example Configuration

```json
{
  "provider": "openai",
  "model": "gpt-4o-mini",
  "api_key": "sk-...",
  "endpoint": null,
  "debounce_ms": 300,
  "ghost_text_enabled": true,
  "temperature": 0.0,
  "safeguards_enabled": true,
  "harm_detection_enabled": true,
  "show_explanations": true
}
```

### Supported Models

<details>
<summary><b>OpenAI Models</b></summary>

| Model | Speed | Cost | Best For |
|-------|-------|------|----------|
| `gpt-4o` | Medium | $$$ | Complex commands |
| `gpt-4o-mini` | Fast | $ | General use (recommended) |
| `o1-mini` | Slow | $$$$ | Reasoning tasks |

</details>

<details>
<summary><b>Anthropic Models</b></summary>

| Model | Speed | Cost | Best For |
|-------|-------|------|----------|
| `claude-3-5-sonnet-20241022` | Medium | $$$ | Complex analysis |
| `claude-3-5-haiku-20241022` | Fast | $ | Quick suggestions |

</details>

<details>
<summary><b>Groq Models (Free!)</b></summary>

| Model | Speed | Cost | Best For |
|-------|-------|------|----------|
| `llama3-70b-8192` | Very Fast | Free | General use |
| `llama3-8b-8192` | Ultra Fast | Free | Simple commands |
| `mixtral-8x7b-32768` | Fast | Free | Complex tasks |

</details>

<details>
<summary><b>Ollama Models (Local, Free!)</b></summary>

| Model | Speed | Cost | Best For |
|-------|-------|------|----------|
| `codellama` | Varies | Free | Code-focused |
| `llama2` | Varies | Free | General use |
| `mistral` | Varies | Free | Fast inference |

</details>

---

## 💡 Examples

### Example 1: Git Workflow

```bash
# Start typing...
$ git a░dd .
       └── Ghost text: "dd ."

# Accept with Tab, then continue...
$ git add .
$ git co░mmit -m "Initial commit"
         └── Ghost text: "mmit -m \"\""

# The AI learns from your patterns!
```

### Example 2: File Operations

```bash
# Navigate to a directory
$ cd ~/pro░jects/my-app
         └── Suggests based on your filesystem

# List files with details
$ ls -l░a
        └── Suggests common flag combinations
```

### Example 3: Safety in Action

```bash
# Attempting a dangerous command...
$ rm -rf ~/Documents

# 🛡️ Safeguard Modal Appears:
# ┌─────────────────────────────────────────┐
# │ ⚠️ Command Safeguard                    │
# │                                         │
# │ CRITICAL RISK                           │
# │                                         │
# │ Command: rm -rf ~/Documents             │
# │ Pattern: rm -rf ~                       │
# │ Risk: Recursive deletion of home dir    │
# │                                         │
# │ [Cancel]  [I Understand, Proceed]       │
# └─────────────────────────────────────────┘
```

### Example 4: Error Recovery

```bash
$ pythn script.py
bash: pythn: command not found

# Status bar shows: "Error detected - Press Ctrl+F to fix"
# Press Ctrl+F...

# 🔧 Fix Suggestion Modal:
# ┌─────────────────────────────────────────┐
# │ 🔧 Fix Error Please (FEP)              │
# │                                         │
# │ Failed: pythn script.py                 │
# │ Exit code: 127                          │
# │                                         │
# │ Suggested Fix: python script.py    ✓ HIGH │
# │ Explanation: Fixed typo in command     │
# │                                         │
# │ [Apply Fix]  [Dismiss]                  │
# └─────────────────────────────────────────┘
```

---

## 🔧 Troubleshooting

### Common Issues

<details>
<summary><b>❌ "API key is required" error</b></summary>

**Solution:**
1. Open Settings (⚙️)
2. Ensure you've entered a valid API key for your selected provider
3. For Ollama users: Make sure Ollama is running locally (`ollama serve`)

</details>

<details>
<summary><b>❌ No autocomplete suggestions appearing</b></summary>

**Check:**
1. Is `ghost_text_enabled` set to `true` in settings?
2. Are you typing at least 2 characters?
3. Is your API key valid?
4. Check your network connection
5. Look at the status bar for loading indicators

</details>

<details>
<summary><b>❌ Terminal not connecting / "Disconnected" status</b></summary>

**Solutions:**
- **Windows:** Ensure PowerShell is installed at the default location
- **macOS/Linux:** Check that your default shell (`$SHELL`) is accessible
- Try restarting the application

</details>

<details>
<summary><b>❌ Slow suggestions</b></summary>

**Optimize by:**
1. Using a faster model (e.g., `gpt-4o-mini` instead of `gpt-4o`)
2. Using Groq (very fast inference)
3. Reducing `debounce_ms` in settings (may increase API costs)
4. Check your network latency

</details>

<details>
<summary><b>❌ Safety warnings are too aggressive</b></summary>

**Options:**
1. Click "Don't ask again this session" on the Safeguard modal
2. Disable pattern safeguards in Settings → Safety
3. Keep harm detection enabled for AI-level analysis only

</details>

<details>
<summary><b>❌ High API costs</b></summary>

**Reduce costs by:**
1. Using free providers (Groq, Ollama)
2. Using cheaper models (`gpt-4o-mini` vs `gpt-4o`)
3. Increasing `debounce_ms` to reduce requests
4. The built-in cache automatically reduces duplicate requests

**Monitor usage:** Settings → Usage tab shows request counts and estimated costs

</details>

---

## 🤝 Contributing

We welcome contributions from developers of all skill levels! Here's how you can help:

### Ways to Contribute

- 🐛 **Report Bugs:** Open an issue describing the problem
- 💡 **Suggest Features:** Share your ideas for improvements
- 📖 **Improve Docs:** Help make our documentation clearer
- 🔧 **Submit PRs:** Fix bugs or implement features

### Development Setup

```bash
# Fork and clone the repository
git clone https://github.com/YOUR_USERNAME/ichack-26.git
cd ichack-26/ai-terminal

# Install dependencies
npm install

# Run in development mode
npm run tauri dev

# Run tests
npm run test
```

### Pull Request Guidelines

1. **Fork** the repository
2. Create a **feature branch** (`git checkout -b feature/amazing-feature`)
3. **Commit** your changes (`git commit -m 'Add amazing feature'`)
4. **Push** to your branch (`git push origin feature/amazing-feature`)
5. Open a **Pull Request**

### Code Style

- **Frontend:** TypeScript with React best practices
- **Backend:** Rust with standard formatting (`cargo fmt`)
- Run tests before submitting PRs

---

## 📄 License

This project is licensed under the **MIT License** - see the [LICENSE](./LICENSE) file for details.

```
MIT License

Copyright (c) 2026 AI Terminal Team

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software...
```

---

## 🙏 Acknowledgments

### Built With

- [Tauri](https://tauri.app/) - Cross-platform desktop framework
- [React](https://react.dev/) - UI library
- [xterm.js](https://xtermjs.org/) - Terminal emulator
- [portable-pty](https://crates.io/crates/portable-pty) - PTY handling in Rust

### AI Providers

- [OpenAI](https://openai.com/) - GPT models
- [Anthropic](https://anthropic.com/) - Claude models
- [Groq](https://groq.com/) - Fast, free inference
- [Ollama](https://ollama.ai/) - Local model hosting

### Special Thanks

- **ICHack '26** for the hackathon opportunity
- All contributors and testers
- The open-source community

---

## 📞 Contact & Support

### Get Help

- 📖 **Documentation:** You're reading it!
- 🐛 **Bug Reports:** [Open an Issue](https://github.com/yashpincha/ichack-26/issues)
- 💬 **Discussions:** [GitHub Discussions](https://github.com/yashpincha/ichack-26/discussions)

### Connect With Us

- 🌐 **Website:** [Coming Soon]
- 🐦 **Twitter:** [@AI_Terminal](https://twitter.com)
- 📧 **Email:** support@example.com

---

<div align="center">

### ⭐ Star us on GitHub!

If AI Terminal helps you, consider giving us a star. It helps others discover the project!

[![GitHub stars](https://img.shields.io/github/stars/yashpincha/ichack-26?style=social)](https://github.com/yashpincha/ichack-26)

---

**Made with ❤️ at ICHack '26**

*Type less. Do more. Stay safe.*

</div>
