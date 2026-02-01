use reqwest::Client;
use serde::{Deserialize, Serialize};
use serde_json::json;

use crate::config::AppConfig;
use crate::context::TerminalContext;
use super::providers::Provider;
use super::prompt::{build_system_prompt, build_user_prompt};
use super::Suggestion;

const REQUEST_TIMEOUT_SECS: u64 = 30;

#[allow(dead_code)]
#[derive(Debug, Serialize)]
struct ChatMessage {
    role: String,
    content: String,
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

pub async fn get_completion(
    config: &AppConfig,
    ctx: &TerminalContext,
) -> Result<Suggestion, String> {
    let provider = Provider::from_str(&config.provider);
    
    // Check API key requirement
    if provider.requires_api_key() && config.api_key.is_empty() {
        return Err(format!(
            "API key is required for {}. Please set it in settings.",
            config.provider
        ));
    }
    
    // Don't send requests for very short inputs
    if ctx.current_input.trim().len() < 2 {
        return Ok(Suggestion::default());
    }
    
    let endpoint = config
        .endpoint
        .clone()
        .unwrap_or_else(|| provider.default_endpoint().to_string());
    
    let client = Client::builder()
        .timeout(std::time::Duration::from_secs(REQUEST_TIMEOUT_SECS))
        .build()
        .map_err(|e| e.to_string())?;
    
    let system_prompt = build_system_prompt();
    let user_prompt = build_user_prompt(ctx);
    
    let response = match provider {
        Provider::OpenAI | Provider::Groq => {
            send_openai_request(&client, &endpoint, &config.api_key, &config.model, &system_prompt, &user_prompt, config.temperature).await?
        }
        Provider::Anthropic => {
            send_anthropic_request(&client, &endpoint, &config.api_key, &config.model, &system_prompt, &user_prompt, config.temperature).await?
        }
        Provider::Ollama => {
            send_ollama_request(&client, &endpoint, &config.model, &system_prompt, &user_prompt, config.temperature).await?
        }
    };
    
    // Clean up the response
    let completion = response
        .trim()
        .trim_matches('"')
        .trim_matches('`')
        .to_string();
    
    Ok(Suggestion {
        completion,
        explanation: None,
    })
}

async fn send_openai_request(
    client: &Client,
    endpoint: &str,
    api_key: &str,
    model: &str,
    system_prompt: &str,
    user_prompt: &str,
    temperature: f32,
) -> Result<String, String> {
    let payload = json!({
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        "temperature": temperature,
        "max_tokens": 100
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
        .ok_or_else(|| "No completion in response".to_string())
}

async fn send_anthropic_request(
    client: &Client,
    endpoint: &str,
    api_key: &str,
    model: &str,
    system_prompt: &str,
    user_prompt: &str,
    temperature: f32,
) -> Result<String, String> {
    let payload = json!({
        "model": model,
        "max_tokens": 100,
        "system": system_prompt,
        "messages": [
            {"role": "user", "content": user_prompt}
        ],
        "temperature": temperature
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
        .ok_or_else(|| "No completion in response".to_string())
}

async fn send_ollama_request(
    client: &Client,
    endpoint: &str,
    model: &str,
    system_prompt: &str,
    user_prompt: &str,
    temperature: f32,
) -> Result<String, String> {
    let payload = json!({
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        "stream": false,
        "options": {
            "temperature": temperature
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
