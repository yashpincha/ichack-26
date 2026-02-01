use serde::{Deserialize, Serialize};

/// Terminal context for building LLM prompts
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct TerminalContext {
    pub current_input: String,
    pub command_history: Vec<String>,
    pub cwd: String,
    pub env_vars: Vec<(String, String)>,
}

impl TerminalContext {
    /// Sanitize the command history by redacting sensitive information
    pub fn get_sanitized_history(&self) -> Vec<String> {
        self.command_history
            .iter()
            .map(|cmd| sanitize_command(cmd))
            .collect()
    }
    
    /// Get relevant environment variable names (not values for security)
    pub fn get_safe_env_vars(&self) -> Vec<String> {
        // Only include names of env vars, exclude sensitive ones
        let sensitive_patterns = [
            "KEY", "SECRET", "TOKEN", "PASSWORD", "CREDENTIAL", "AUTH",
            "PRIVATE", "API_KEY", "ACCESS_KEY", "AWS_", "AZURE_"
        ];
        
        self.env_vars
            .iter()
            .filter(|(name, _)| {
                let upper = name.to_uppercase();
                !sensitive_patterns.iter().any(|pat| upper.contains(pat))
            })
            .map(|(name, _)| name.clone())
            .collect()
    }
}

/// Sanitize a command by redacting sensitive information
fn sanitize_command(cmd: &str) -> String {
    let mut result = cmd.to_string();
    
    // Redact long hex strings (likely hashes or keys)
    let hex_pattern = regex_lite::Regex::new(r"\b[0-9a-fA-F]{32,}\b").unwrap();
    result = hex_pattern.replace_all(&result, "REDACTED_HASH").to_string();
    
    // Redact UUIDs
    let uuid_pattern = regex_lite::Regex::new(r"\b[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}\b").unwrap();
    result = uuid_pattern.replace_all(&result, "REDACTED_UUID").to_string();
    
    // Redact potential API keys (alphanumeric strings of certain lengths)
    let key_pattern = regex_lite::Regex::new(r"\b(sk-|pk-|api-)?[A-Za-z0-9]{20,}\b").unwrap();
    result = key_pattern.replace_all(&result, "REDACTED_KEY").to_string();
    
    result
}

/// Build the prompt for the LLM with optional explanation
pub fn build_prompt_with_explanation(ctx: &TerminalContext, include_explanation: bool) -> String {
    let sanitized_history = ctx.get_sanitized_history();
    let history_str = if sanitized_history.is_empty() {
        "No recent commands".to_string()
    } else {
        sanitized_history
            .iter()
            .enumerate()
            .map(|(i, cmd)| format!("{}. {}", i + 1, cmd))
            .collect::<Vec<_>>()
            .join("\n")
    };
    
    let env_vars = ctx.get_safe_env_vars();
    let env_str = if env_vars.is_empty() {
        "None".to_string()
    } else {
        env_vars.join(", ")
    };
    
    let output_format = if include_explanation {
        r#"Output format: completion|||explanation
Where:
- completion: The text to complete the command
- explanation: A brief (max 60 chars) explanation of why this suggestion was made

Example: eckout main|||Switch to the main branch"#
    } else {
        "Return ONLY the completion text that should appear after the cursor - do not repeat what the user has already typed.\nIf the input appears complete or you cannot suggest anything useful, return an empty string."
    };
    
    format!(
        r#"User is typing a command in the terminal and needs autocomplete suggestions.

Current input: `{}`

## Terminal Context
- Current directory: {}
- Available environment variables: {}

## Recent Command History (sanitized)
{}

## Instructions
Provide the SINGLE BEST completion for the user's current input. The completion should:
1. Continue from where the user stopped typing
2. Be a valid shell command
3. Consider the context (directory, history, common patterns)

{}

Examples:
- Input: "git ch" -> Completion: "eckout "
- Input: "ls -" -> Completion: "la"
- Input: "docker " -> Completion: "ps"
"#,
        ctx.current_input,
        ctx.cwd,
        env_str,
        history_str,
        output_format
    )
}

/// Build the system prompt
pub fn get_system_prompt() -> &'static str {
    r#"You are an intelligent terminal autocomplete assistant. Your job is to predict and complete shell commands based on context.

Rules:
1. Return ONLY the completion text - the part that comes AFTER the user's cursor
2. Keep completions concise and practical
3. Consider the user's command history and current directory
4. If unsure, prefer common/safe commands
5. Never suggest destructive commands (rm -rf, etc.) without explicit flags from user
6. Return empty string if no good completion exists

Output format: Just the completion text, nothing else. No explanations, no quotes, no markdown."#
}

#[cfg(test)]
mod tests {
    use super::*;
    
    #[test]
    fn test_sanitize_command() {
        let cmd = "export API_KEY=sk-1234567890abcdef1234567890abcdef";
        let sanitized = sanitize_command(cmd);
        assert!(sanitized.contains("REDACTED"));
    }
}
