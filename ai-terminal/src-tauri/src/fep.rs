use reqwest::Client;
use serde::{Deserialize, Serialize};
use serde_json::json;
use std::time::Duration;

use crate::config::AppConfig;
use crate::llm::Provider;

const FEP_TIMEOUT_SECS: u64 = 30;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct FixSuggestion {
    pub fixed_command: String,
    pub explanation: String,
    pub confidence: String, // "low", "medium", "high"
}

impl Default for FixSuggestion {
    fn default() -> Self {
        Self {
            fixed_command: String::new(),
            explanation: "Unable to suggest a fix.".to_string(),
            confidence: "low".to_string(),
        }
    }
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ErrorContext {
    pub command: String,
    pub exit_code: i32,
    pub output: String,
    pub cwd: String,
    pub history: Vec<String>,
}

/// Get a fix suggestion for a failed command
pub async fn get_error_fix(
    config: &AppConfig,
    ctx: &ErrorContext,
) -> Result<FixSuggestion, String> {
    let provider = Provider::from_str(&config.provider);

    // Check API key requirement
    if provider.requires_api_key() && config.api_key.is_empty() {
        return Err("API key is required for error analysis.".to_string());
    }

    let endpoint = config
        .endpoint
        .clone()
        .unwrap_or_else(|| provider.default_endpoint().to_string());

    let client = Client::builder()
        .timeout(Duration::from_secs(FEP_TIMEOUT_SECS))
        .build()
        .map_err(|e| e.to_string())?;

    let system_prompt = get_fep_system_prompt();
    let user_prompt = get_fep_user_prompt(ctx);

    let response = match provider {
        Provider::OpenAI | Provider::Groq => {
            send_fep_openai(&client, &endpoint, &config.api_key, &config.model, &system_prompt, &user_prompt).await?
        }
        Provider::Anthropic => {
            send_fep_anthropic(&client, &endpoint, &config.api_key, &config.model, &system_prompt, &user_prompt).await?
        }
        Provider::Ollama => {
            send_fep_ollama(&client, &endpoint, &config.model, &system_prompt, &user_prompt).await?
        }
    };

    Ok(parse_fep_response(&response))
}

fn get_fep_system_prompt() -> String {
    r#"You are an expert shell command debugger. When a command fails, you analyze the error and provide a corrected command.

Your task:
1. Analyze the failed command and its error output
2. Identify the root cause of the failure
3. Provide a corrected command that should work
4. Explain what was wrong and how the fix addresses it

Output format (JSON):
{
  "fixed_command": "the corrected command",
  "explanation": "Brief explanation of what was wrong and how the fix addresses it",
  "confidence": "low|medium|high"
}

Confidence levels:
- low: The fix is a guess, user should verify
- medium: The fix should likely work but may need adjustment
- high: The fix directly addresses the identified error

Common error categories:
- Typos in command or arguments
- Missing dependencies or packages
- Permission issues (suggest sudo if appropriate)
- Incorrect paths or file not found
- Syntax errors
- Wrong flags or options
- Missing quotes or escaping issues

Be concise but helpful. Only provide the JSON output."#.to_string()
}

fn get_fep_user_prompt(ctx: &ErrorContext) -> String {
    let history_str = if ctx.history.is_empty() {
        "No recent commands".to_string()
    } else {
        ctx.history.iter().take(5).cloned().collect::<Vec<_>>().join("\n")
    };

    // Truncate output if too long
    let output_truncated = if ctx.output.len() > 2000 {
        format!("{}...(truncated)", &ctx.output[..2000])
    } else {
        ctx.output.clone()
    };

    format!(
        r#"A shell command failed. Please analyze and provide a fix.

Failed command: `{}`
Exit code: {}
Current directory: {}

Error output:
```
{}
```

Recent command history:
{}

Provide a JSON response with the fixed command and explanation."#,
        ctx.command,
        ctx.exit_code,
        ctx.cwd,
        output_truncated,
        history_str
    )
}

fn parse_fep_response(response: &str) -> FixSuggestion {
    // Try to parse as JSON
    if let Ok(parsed) = serde_json::from_str::<FixSuggestion>(response) {
        return parsed;
    }

    // Try to extract JSON from response
    if let Some(start) = response.find('{') {
        if let Some(end) = response.rfind('}') {
            let json_str = &response[start..=end];
            if let Ok(parsed) = serde_json::from_str::<FixSuggestion>(json_str) {
                return parsed;
            }
        }
    }

    // Default if parsing fails
    FixSuggestion::default()
}

#[derive(Debug, Deserialize)]
struct OpenAIResponse {
    choices: Vec<OpenAIChoice>,
}

#[derive(Debug, Deserialize)]
struct OpenAIChoice {
    message: OpenAIMessage,
}

#[derive(Debug, Deserialize)]
struct OpenAIMessage {
    content: String,
}

#[derive(Debug, Deserialize)]
struct AnthropicResponse {
    content: Vec<AnthropicContent>,
}

#[derive(Debug, Deserialize)]
struct AnthropicContent {
    text: Option<String>,
}

#[derive(Debug, Deserialize)]
struct OllamaResponse {
    message: OllamaMessage,
}

#[derive(Debug, Deserialize)]
struct OllamaMessage {
    content: String,
}

async fn send_fep_openai(
    client: &Client,
    endpoint: &str,
    api_key: &str,
    model: &str,
    system_prompt: &str,
    user_prompt: &str,
) -> Result<String, String> {
    let payload = json!({
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        "temperature": 0.0,
        "max_tokens": 500
    });

    let response = client
        .post(endpoint)
        .header("Content-Type", "application/json")
        .header("Authorization", format!("Bearer {}", api_key))
        .json(&payload)
        .send()
        .await
        .map_err(|e| format!("Request failed: {}", e))?;

    if !response.status().is_success() {
        let status = response.status();
        let body = response.text().await.unwrap_or_default();
        return Err(format!("API error ({}): {}", status, body));
    }

    let data: OpenAIResponse = response
        .json()
        .await
        .map_err(|e| format!("Failed to parse response: {}", e))?;

    data.choices
        .first()
        .map(|c| c.message.content.clone())
        .ok_or_else(|| "No response".to_string())
}

async fn send_fep_anthropic(
    client: &Client,
    endpoint: &str,
    api_key: &str,
    model: &str,
    system_prompt: &str,
    user_prompt: &str,
) -> Result<String, String> {
    let payload = json!({
        "model": model,
        "max_tokens": 500,
        "system": system_prompt,
        "messages": [
            {"role": "user", "content": user_prompt}
        ],
        "temperature": 0.0
    });

    let response = client
        .post(endpoint)
        .header("Content-Type", "application/json")
        .header("x-api-key", api_key)
        .header("anthropic-version", "2023-06-01")
        .json(&payload)
        .send()
        .await
        .map_err(|e| format!("Request failed: {}", e))?;

    if !response.status().is_success() {
        let status = response.status();
        let body = response.text().await.unwrap_or_default();
        return Err(format!("API error ({}): {}", status, body));
    }

    let data: AnthropicResponse = response
        .json()
        .await
        .map_err(|e| format!("Failed to parse response: {}", e))?;

    data.content
        .first()
        .and_then(|c| c.text.clone())
        .ok_or_else(|| "No response".to_string())
}

async fn send_fep_ollama(
    client: &Client,
    endpoint: &str,
    model: &str,
    system_prompt: &str,
    user_prompt: &str,
) -> Result<String, String> {
    let payload = json!({
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        "stream": false,
        "options": {
            "temperature": 0.0
        }
    });

    let response = client
        .post(endpoint)
        .header("Content-Type", "application/json")
        .json(&payload)
        .send()
        .await
        .map_err(|e| format!("Request failed: {}", e))?;

    if !response.status().is_success() {
        let status = response.status();
        let body = response.text().await.unwrap_or_default();
        return Err(format!("API error ({}): {}", status, body));
    }

    let data: OllamaResponse = response
        .json()
        .await
        .map_err(|e| format!("Failed to parse response: {}", e))?;

    Ok(data.message.content)
}
