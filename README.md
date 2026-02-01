IC Hack 2026: autocomplete.sh
========================================================

## CLAM (Command Line Assistance Module)

The command line is one of the most powerful tools in software engineering, yet it remains one of the least accessible. Even experienced developers forget command syntax, mistype flags, or constantly switch between the terminal and external resources just to debug errors. For beginners, the experience can feel intimidating and error-prone, where small mistakes can lead to destructive outcomes.

As students and developers who spend much of our day in Bash, we faced this friction daily — searching for flags, copying commands from documentation, and relying on AI tools outside the terminal. That constant context switching broke our flow and slowed us down. We kept asking ourselves: why can’t the terminal just help us directly?

So we built CLAM (Command Line Assistant Model) — an AI-powered assistant embedded directly into the shell that provides real-time autocomplete, safety checks, and automatic error fixes. By bringing intelligence inside the terminal, CLAM reduces friction and lets developers focus on building instead of memorizing commands.

## Quick Start

Installing our tool is incredibly simple:
```bash
git clone https://github.com/yashpincha/ichack-26.git
cd ichack-26
./install-sh
```

## Features

- **Context-Aware**: Considers terminal state, recent commands, and `--help` information
- **Flexible**: Supports various LLM models, from fast and cheap to powerful (and even local!)
- **Secure**: Enables local LLMs and sanitizes prompts for sensitive information
- **Efficient**: Caches recent queries for speed and convenience
- **Cost-Effective**: Monitors API call sizes and costs

## Supported Models

We support OpenAI, Groq, Anthropic, and Ollama models, and even local models. Configure your model with:

```bash
autocomplete model
```

## How It Works

`autocomplete.sh` provides faster, more accurate suggestions by considering:

- Your machine's environment
- Recently executed commands
- Current directory contents
- Command-specific help information

View the full prompt with:

```bash
autocomplete command --dry-run "your command here"
```

## Tips and Tricks

### **Interactive Autocompletion**
Receive AI-assisted autocompletions, right in the terminal!

Use **Ctrl+Space** to enter an interactive session. Use `--explain` to receive short explanations for each autocompletion.
Navigate between suggestions using your keyboard.

```
$ ls # with file sizes in human-readable format

Generating suggestions...

╔════════════════════════════════════════════════════════════════════╗
║  Autocomplete Suggestions                                        ║
╠════════════════════════════════════════════════════════════════════╣
║  Use ↑/↓ to navigate, Enter to execute, Esc to cancel          ║
╚════════════════════════════════════════════════════════════════════╝

  ▶ ls -lh
    List files with sizes in human-readable format.

    ls -lhS
    List files by size, human-readable format.

    ls -lh --color=auto
    List files with color, human-readable sizes.

    ls -lh --group-directories-first
    List files with dirs first, human-readable sizes.

    ls -lh --time-style=long-iso
    List files with long ISO date, human-readable sizes.
```


### 🛡️ **Two-Layer Safety System**
Never accidentally run a dangerous command again.

- **Pattern Safeguards** (Fast, Local): Catches known dangerous patterns like `rm -rf /`
- **AI Harm Detection** (Intelligent): Analyzes commands for potential risks

```
$ rm temp
⚠ WARNING: Potentially harmful command detected!
▶ Command: rm important-file
▶ Reason: Deletes the 'important-file' file or directory, causing data loss.

Are you sure you want to continue? (y/N): 
```

### 🔧 **Fix Error Please (FEP)**
When a command fails, press `autocomplete fep` to get an AI-suggested fix.

```
$ gitt push origin main
Command 'gitt' not found, did you mean:
  command 'gitu' from snap gitu (v0.39.0)
  command 'gitk' from deb gitk (1:2.43.0-1ubuntu7.3)
  command 'gitg' from deb gitg (44-1)
  command 'gita' from deb gita (0.16.6.1-2)
  command 'gist' from deb yorick (2.2.04+dfsg1-12)
  command 'gitit' from deb gitit (0.15.1.1+dfsg-1build2)
  command 'git' from deb git (1:2.43.0-1ubuntu7.3)
See 'snap info <snapname>' for additional versions.

$ autocomplete fep
Analyzing error and generating fix...

━━━ Recommended Command ━━━
git push origin main

━━━ Explanation ━━━
The command failed because 'gitt' is not a recognized command. The correct command is 'git', which is the version control system used to push changes to a remote repository.

Run this command? [Y/n]
```

## Configuration

```bash
source autocomplete config
```

Update settings with:

```bash
autocomplete config set <key> <value>
```

Enable, disable, or check safeguarding status with:
```bash
autocomplete safeguarding enable
autocomplete safeguarding disable
autocomplete safeguarding status
```

## Usage Tracking

```bash
autocomplete usage
```

## Use Cases

- **Data Engineers**: Manipulate datasets efficiently
- **Backend Developers**: Deploy updates swiftly
- **Linux Users**: Navigate systems seamlessly
- **Terminal Novices**: Build command-line confidence
- **Efficiency Seekers**: Streamline repetitive tasks
- **Documentation Seekers**: Quickly understand commands

## Development

### Testing

To test the tool, just execute `./run_tests.sh`. It will automatically install `bats` if you do not already have it.

## Developers

Developers:
- Arya Golkari
- Andras Bard
- James Yang
- Kuzey Korel
- Syed Sameer Faisal
- Yash Bincha

This project was influenced by [`autocomplete.sh`](https://github.com/closedloop-technologies/autocomplete-sh/tree/main).

## License

See the [MIT-LICENSE](./LICENSE) file for details.
