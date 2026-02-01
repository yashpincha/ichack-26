use std::collections::HashMap;
use std::time::{Duration, Instant};
use reqwest::Client;
use serde::{Deserialize, Serialize};
use serde_json::json;

use crate::config::AppConfig;
use crate::llm::Provider;

const HARM_CACHE_TTL_SECS: u64 = 3600; // 1 hour
const MAX_HARM_CACHE_SIZE: usize = 100;
const HARM_CHECK_TIMEOUT_SECS: u64 = 3;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct HarmResult {
    pub is_harmful: bool,
    pub reason: String,
    pub severity: String, // "low", "medium", "high", "critical"
}

impl Default for HarmResult {
    fn default() -> Self {
        Self {
            is_harmful: false,
            reason: String::new(),
            severity: "low".to_string(),
        }
    }
}

struct HarmCacheEntry {
    result: HarmResult,
    created_at: Instant,
}

pub struct HarmCache {
    entries: HashMap<String, HarmCacheEntry>,
}

impl HarmCache {
    pub fn new() -> Self {
        Self {
            entries: HashMap::new(),
        }
    }

    pub fn get(&self, command: &str) -> Option<HarmResult> {
        let hash = format!("{:x}", md5::compute(command.as_bytes()));
        if let Some(entry) = self.entries.get(&hash) {
            if entry.created_at.elapsed() < Duration::from_secs(HARM_CACHE_TTL_SECS) {
                return Some(entry.result.clone());
            }
        }
        None
    }

    pub fn set(&mut self, command: &str, result: HarmResult) {
        // Evict old entries if cache is full
        if self.entries.len() >= MAX_HARM_CACHE_SIZE {
            self.evict_oldest();
        }
        self.evict_expired();

        let hash = format!("{:x}", md5::compute(command.as_bytes()));
        self.entries.insert(
            hash,
            HarmCacheEntry {
                result,
                created_at: Instant::now(),
            },
        );
    }

    fn evict_oldest(&mut self) {
        if let Some(oldest_key) = self
            .entries
            .iter()
            .min_by_key(|(_, v)| v.created_at)
            .map(|(k, _)| k.clone())
        {
            self.entries.remove(&oldest_key);
        }
    }

    fn evict_expired(&mut self) {
        let now = Instant::now();
        let ttl = Duration::from_secs(HARM_CACHE_TTL_SECS);
        self.entries.retain(|_, entry| now.duration_since(entry.created_at) < ttl);
    }

    pub fn clear(&mut self) {
        self.entries.clear();
    }
}

impl Default for HarmCache {
    fn default() -> Self {
        Self::new()
    }
}

/// Check if a command is potentially harmful using LLM
pub async fn check_command_harm(
    config: &AppConfig,
    command: &str,
) -> Result<HarmResult, String> {
    // Skip check for empty commands
    if command.trim().is_empty() {
        return Ok(HarmResult::default());
    }

    let provider = Provider::from_str(&config.provider);

    // Check API key requirement
    if provider.requires_api_key() && config.api_key.is_empty() {
        // If no API key, fail safe (allow execution)
        return Ok(HarmResult::default());
    }

    let endpoint = config
        .endpoint
        .clone()
        .unwrap_or_else(|| provider.default_endpoint().to_string());

    let client = Client::builder()
        .timeout(Duration::from_secs(HARM_CHECK_TIMEOUT_SECS))
        .build()
        .map_err(|e| e.to_string())?;

    let system_prompt = get_harm_system_prompt();
    let user_prompt = get_harm_user_prompt(command);

    let response = match provider {
        Provider::OpenAI | Provider::Groq => {
            send_harm_check_openai(&client, &endpoint, &config.api_key, &config.model, &system_prompt, &user_prompt).await
        }
        Provider::Anthropic => {
            send_harm_check_anthropic(&client, &endpoint, &config.api_key, &config.model, &system_prompt, &user_prompt).await
        }
        Provider::Ollama => {
            send_harm_check_ollama(&client, &endpoint, &config.model, &system_prompt, &user_prompt).await
        }
    };

    // On any error, fail safe (allow execution)
    match response {
        Ok(result) => Ok(parse_harm_response(&result)),
        Err(_) => Ok(HarmResult::default()),
    }
}

fn get_harm_system_prompt() -> String {
    r#"You are a security analyzer for shell commands. Your job is to detect potentially harmful or dangerous commands.

Analyze commands for these categories of harm:
1. DESTRUCTIVE FILE OPERATIONS: rm -rf, rm -r, shred, wipe operations that can delete important files
2. SYSTEM MODIFICATIONS: Commands that modify system files, bootloader, partition tables
3. PERMISSION CHANGES: chmod 777, chown operations that weaken security
4. NETWORK RISKS: curl/wget piped to shell, reverse shells, unexpected network connections
5. RESOURCE ATTACKS: Fork bombs, infinite loops, memory exhaustion
6. DANGEROUS CHAINING: Commands using && or | that combine risky operations

Output format (JSON):
{
  "is_harmful": true/false,
  "reason": "Brief explanation of the risk",
  "severity": "low|medium|high|critical"
}

Severity levels:
- low: Minor risk, proceed with caution
- medium: Moderate risk, user should understand implications
- high: Significant risk, could cause data loss or system issues
- critical: Severe risk, could destroy system or compromise security

Be conservative - only flag truly dangerous commands. Common safe operations should not be flagged."#.to_string()
}

fn get_harm_user_prompt(command: &str) -> String {
    format!("Analyze this shell command for potential harm:\n\n```\n{}\n```\n\nRespond with JSON only.", command)
}

fn parse_harm_response(response: &str) -> HarmResult {
    // Try to parse as JSON
    if let Ok(parsed) = serde_json::from_str::<HarmResult>(response) {
        return parsed;
    }

    // Try to extract JSON from response
    if let Some(start) = response.find('{') {
        if let Some(end) = response.rfind('}') {
            let json_str = &response[start..=end];
            if let Ok(parsed) = serde_json::from_str::<HarmResult>(json_str) {
                return parsed;
            }
        }
    }

    // Default to safe if parsing fails
    HarmResult::default()
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

async fn send_harm_check_openai(
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
        "max_tokens": 200
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
        return Err("API error".to_string());
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

async fn send_harm_check_anthropic(
    client: &Client,
    endpoint: &str,
    api_key: &str,
    model: &str,
    system_prompt: &str,
    user_prompt: &str,
) -> Result<String, String> {
    let payload = json!({
        "model": model,
        "max_tokens": 200,
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
        return Err("API error".to_string());
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

async fn send_harm_check_ollama(
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
        return Err("API error".to_string());
    }

    let data: OllamaResponse = response
        .json()
        .await
        .map_err(|e| format!("Failed to parse response: {}", e))?;

    Ok(data.message.content)
}
