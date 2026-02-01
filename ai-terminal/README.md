# AI Terminal

A cross-platform terminal application with AI-powered inline autocomplete suggestions, similar to GitHub Copilot but for shell commands.

![AI Terminal](docs/screenshot.png)

## Features

- **Ghost Text Autocomplete**: Real-time inline suggestions appear as you type, just like Copilot
- **Multiple AI Providers**: Support for OpenAI, Anthropic, Groq, and local Ollama models
- **Cross-Platform**: Works on Windows, macOS, and Linux
- **Context-Aware**: Considers command history, current directory, and environment
- **Privacy-Focused**: Sensitive data is sanitized before sending to AI providers
- **Lightweight**: Built with Tauri for a small footprint (~10MB vs Electron's 150MB+)

## Quick Start

### Prerequisites

- [Node.js](https://nodejs.org/) 18+
- [Rust](https://rustup.rs/) 1.70+
- [Tauri CLI](https://tauri.app/v2/guides/getting-started/prerequisites)

### Installation

```bash
# Clone the repository
git clone https://github.com/your-org/ai-terminal.git
cd ai-terminal

# Install dependencies
npm install

# Run in development mode
npm run tauri dev

# Build for production
npm run tauri build
```

## Usage

### Accepting Suggestions

- **Tab** or **Right Arrow**: Accept the full suggestion
- **Escape**: Dismiss the suggestion
- Keep typing to update or dismiss suggestions

### Keyboard Shortcuts

| Key | Action |
|-----|--------|
| Tab | Accept suggestion |
| → (Right Arrow) | Accept suggestion |
| Esc | Dismiss suggestion |
| Ctrl+C | Cancel current command |
| Ctrl+U | Clear current line |

### Configuration

Click the ⚙️ settings button to configure:

- **AI Provider**: Choose between OpenAI, Anthropic, Groq, or Ollama
- **Model**: Select the specific model to use
- **API Key**: Enter your API key (not required for Ollama)
- **Temperature**: Adjust creativity (0 = deterministic, 1 = creative)
- **Debounce Time**: How long to wait before fetching suggestions

Configuration is stored in:
- Windows: `%APPDATA%\ai-terminal\config.json`
- macOS: `~/Library/Application Support/ai-terminal/config.json`
- Linux: `~/.config/ai-terminal/config.json`

## Supported AI Providers

### OpenAI
- GPT-4o, GPT-4o Mini, O1 Mini
- Requires API key from [platform.openai.com](https://platform.openai.com/api-keys)

### Anthropic
- Claude 3.5 Sonnet, Claude 3.5 Haiku
- Requires API key from [console.anthropic.com](https://console.anthropic.com/settings/keys)

### Groq (Free!)
- Llama 3 70B, Llama 3 8B, Mixtral 8x7B
- Requires API key from [console.groq.com](https://console.groq.com/keys)

### Ollama (Local)
- CodeLlama, Llama 2, Mistral, and any model you have installed
- Requires [Ollama](https://ollama.ai/) running locally
- No API key needed!

## Architecture

```
ai-terminal/
├── src-tauri/           # Rust backend
│   ├── src/
│   │   ├── main.rs      # Entry point
│   │   ├── lib.rs       # Tauri commands
│   │   ├── pty.rs       # PTY management
│   │   ├── config.rs    # Configuration
│   │   ├── cache.rs     # Response caching
│   │   ├── context.rs   # Terminal context
│   │   └── llm/         # LLM providers
│   └── Cargo.toml
├── src/                 # React frontend
│   ├── components/
│   │   ├── Terminal.tsx # xterm.js wrapper
│   │   ├── GhostText.tsx# Inline suggestions
│   │   └── Settings.tsx # Config UI
│   ├── hooks/
│   │   └── useAutocomplete.ts
│   └── styles/
└── package.json
```

## Development

### Project Structure

- **Frontend**: React + TypeScript + xterm.js
- **Backend**: Rust + Tauri + portable-pty
- **Build**: Vite + Tauri CLI

### Building

```bash
# Development
npm run tauri dev

# Production build
npm run tauri build

# The built app will be in src-tauri/target/release/
```

### Testing

```bash
# Run Rust tests
cd src-tauri && cargo test

# Type checking
npm run build
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

MIT License - see [LICENSE](LICENSE) for details.

## Acknowledgments

- Built with [Tauri](https://tauri.app/)
- Terminal emulation by [xterm.js](https://xtermjs.org/)
- Inspired by [autocomplete.sh](https://autocomplete.sh/)
