# Autocomplete.sh Usage

## Cross-Platform Installation

### Linux / macOS

```bash
# Install using curl
curl -fsSL https://autocomplete.sh/install.sh | bash

# Or using wget
wget -qO- https://autocomplete.sh/install.sh | bash
```

### Windows PowerShell

```powershell
# Install using PowerShell
irm https://autocomplete.sh/install.ps1 | iex
```

### Windows (Git Bash / WSL)

```bash
# Same as Linux
curl -fsSL https://autocomplete.sh/install.sh | bash
```

---

## Basic Commands

1. **Display Help Information**  

   ```bash
   # Linux/macOS/Git Bash
   autocomplete --help
   ```  
   
   ```powershell
   # Windows PowerShell
   autocomplete --help
   ```

   *Check that the help text is clear and lists all available commands.*

2. **Install the Script**  

   ```bash
   # Linux/macOS/Git Bash
   autocomplete install
   ```  

   ```powershell
   # Windows PowerShell
   autocomplete install
   ```

   *This adds the necessary lines to your shell configuration file.*

3. **Reload Your Shell**  

   ```bash
   # Linux (Bash)
   source ~/.bashrc
   
   # macOS (Zsh)
   source ~/.zshrc
   ```
   
   ```powershell
   # Windows PowerShell
   . $PROFILE
   ```

   *Reload your shell configuration to activate Autocomplete.*

4. **Show Current Configuration**  

   ```bash
   autocomplete config
   ```  

   *Verify that your configuration (including API keys, model settings, etc.) is loaded correctly.*

5. **Update a Configuration Value**  

   ```bash
   autocomplete config set temperature 0.5
   ```  

   *Change the temperature setting to test the config update and then run `autocomplete config` again to confirm the change.*

6. **Display Usage Statistics**  

   ```bash
   autocomplete usage
   ```  

   *View log and cost metrics as well as cache information.*

7. **Display System Information**  

   ```bash
   autocomplete system
   ```  

   *Ensure that system and terminal details are being reported correctly.*

8. **Test Command Completion (Dry Run)**  

   ```bash
   autocomplete command --dry-run "ls -la"
   ```  

   *Run a dry-run to see the generated prompt and suggestions without executing any real command.*

9. **Interact with the Model Selection Menu**  

   ```bash
   autocomplete model
   ```  

   *This will open an interactive menu—use your arrow keys to navigate and press Enter to select a model (or press “q” to cancel).*

10. **Disable Autocomplete**  

    ```bash
    autocomplete disable
    ```  

    *Temporarily disable the Autocomplete.sh completion function.*

11. **Enable Autocomplete**  

    ```bash
    autocomplete enable
    ```  

    *Re-enable the autocomplete functionality and verify that it is active.*

12. **Clear Cache and Logs**  

    ```bash
    autocomplete clear
    ```  

    *This will purge cached completions and log data—confirm the action when prompted.*

13. **Remove the Installation**  

    ```bash
    autocomplete remove
    ```  

    *Clean up by removing the configuration, cache, log files, and the bashrc modifications.*

Running these commands sequentially (or in various orders to simulate different user scenarios) will help you put the script through its paces and ensure that all functionality works as expected.

---

## Interactive Mode (Ctrl+Space)

The interactive mode provides a menu-based selection of LLM suggestions.

### Using Interactive Mode

1. **Type your partial command**
   ```
   git comm
   ```

2. **Press Ctrl+Space** to trigger the interactive menu

3. **Navigate suggestions** using arrow keys (↑/↓)

4. **Press Enter** to execute the selected command

5. **Press Esc or 'q'** to cancel

### Explanation Mode

Add `--explain` to your command to see explanations for each suggestion:

```bash
# Linux/macOS
git commit --explain <Ctrl+Space>

# Windows PowerShell
git commit --explain <Ctrl+Space>
```

---

## Platform-Specific Notes

### Linux (Bash)
- Tab completion: Press `<TAB><TAB>` for suggestions
- Interactive mode: Press `Ctrl+Space`
- Configuration file: `~/.autocomplete/config`
- Shell config: `~/.bashrc`

### macOS (Zsh)
- Tab completion: Press `<TAB><TAB>` for suggestions
- Interactive mode: Press `Ctrl+Space`
- Configuration file: `~/.autocomplete/config`
- Shell config: `~/.zshrc`
- Note: macOS uses BSD versions of commands (sed, find, md5). The script handles these differences automatically.

### Windows (PowerShell)
- Interactive mode: Press `Ctrl+Space`
- Configuration file: `%USERPROFILE%\.autocomplete\config`
- Shell config: `$PROFILE`
- Note: Tab completion uses PowerShell's native `Register-ArgumentCompleter`

### Windows (Git Bash / WSL)
- Same as Linux Bash
- Configuration stored in `~/.autocomplete/config`

---

Absolutely, let's revise the commands and questions to better suit each persona's voice and language:

### Data Engineer

1. **ls**: "Hey, what files are hanging around in this folder?"
2. **awk**: "Yo, can you pull out the first column from that CSV and find entries with a specific keyword?"
3. **spark-submit**: "Can you fire up Spark on that dataset and point it to where it needs to go?"
4. **python**: "Merge those CSV files based on that common column and save the result somewhere."

### Backend Developer

1. **git init**: "Yo, let's kickstart a new Git repo right here."
2. **gcc**: "Compile this C code into a usable program, please."
3. **pytest**: "Hey, could you run those tests we've got lying around?"
4. **docker**: "Build that Docker image and let's spin it up on port 8080."

### Linux User

1. **top**: "What's hogging all the resources on my system right now?"
2. **apt install**: "Can you hook me up with that package using APT?"
3. **chmod**: "Let's make sure this script is ready to roll by tweaking its permissions."
4. **systemctl start**: "Fire up that service we've been talking about."

### Terminal Novice

1. **cd**: "Take me to that other folder, please."
2. **touch**: "Can we create a new file with this name?"
3. **cp**: "Can you copy this file over to that place?"
4. **cat**: "What's inside this file? Show me."

### Efficiency Seeker

1. **sed**: "Can you swap out that text across all these files at once?"
2. **tar**: "Bundle up this directory into a nice little package, would you?"
3. **tar**: "Let's open up that compressed file and see what's inside."
4. **grep**: "Hey, can you find all instances of this word in that file and count them?"

### Documentation Seeker

1. **man**: "Can you tell me more about how this command works?"
2. **apropos**: "I'm looking for something related to this keyword; got any leads?"
3. **help**: "Give me a hand understanding these built-in shell commands, please."
4. **dpkg**: "Show me everything we've got installed, especially that package."
