use serde::{Deserialize, Serialize};
use std::fs;
use std::path::PathBuf;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AppConfig {
    pub provider: String,
    pub model: String,
    pub api_key: String,
    pub endpoint: Option<String>,
    pub debounce_ms: u32,
    pub ghost_text_enabled: bool,
    pub temperature: f32,
    pub max_suggestions: u32,
    pub max_history_commands: u32,
    // Safety features
    #[serde(default = "default_true")]
    pub safeguards_enabled: bool,
    #[serde(default = "default_true")]
    pub harm_detection_enabled: bool,
    #[serde(default = "default_true")]
    pub show_explanations: bool,
}

fn default_true() -> bool {
    true
}

impl Default for AppConfig {
    fn default() -> Self {
        Self {
            provider: "openai".to_string(),
            model: "gpt-4o-mini".to_string(),
            api_key: String::new(),
            endpoint: None,
            debounce_ms: 300,
            ghost_text_enabled: true,
            temperature: 0.0,
            max_suggestions: 1,
            max_history_commands: 20,
            safeguards_enabled: true,
            harm_detection_enabled: true,
            show_explanations: true,
        }
    }
}

pub fn get_config_path() -> PathBuf {
    let config_dir = dirs::config_dir()
        .unwrap_or_else(|| PathBuf::from("."))
        .join("ai-terminal");
    
    // Ensure directory exists
    let _ = fs::create_dir_all(&config_dir);
    
    config_dir.join("config.json")
}

pub fn load_config() -> Result<AppConfig, Box<dyn std::error::Error>> {
    let path = get_config_path();
    
    if path.exists() {
        let content = fs::read_to_string(&path)?;
        let config: AppConfig = serde_json::from_str(&content)?;
        Ok(config)
    } else {
        // Create default config
        let config = AppConfig::default();
        save_config(&config)?;
        Ok(config)
    }
}

pub fn save_config(config: &AppConfig) -> Result<(), Box<dyn std::error::Error>> {
    let path = get_config_path();
    let content = serde_json::to_string_pretty(config)?;
    fs::write(&path, content)?;
    Ok(())
}

#[allow(dead_code)]
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ModelInfo {
    pub provider: String,
    pub model: String,
    pub endpoint: String,
    pub prompt_cost: f64,
    pub completion_cost: f64,
}

// Available models (matching autocomplete.sh)
#[allow(dead_code)]
pub fn get_available_models() -> Vec<ModelInfo> {
    vec![
        // OpenAI models
        ModelInfo {
            provider: "openai".to_string(),
            model: "gpt-4o".to_string(),
            endpoint: "https://api.openai.com/v1/chat/completions".to_string(),
            prompt_cost: 0.0000025,
            completion_cost: 0.00001,
        },
        ModelInfo {
            provider: "openai".to_string(),
            model: "gpt-4o-mini".to_string(),
            endpoint: "https://api.openai.com/v1/chat/completions".to_string(),
            prompt_cost: 0.00000015,
            completion_cost: 0.0000006,
        },
        ModelInfo {
            provider: "openai".to_string(),
            model: "o1-mini".to_string(),
            endpoint: "https://api.openai.com/v1/chat/completions".to_string(),
            prompt_cost: 0.000011,
            completion_cost: 0.000044,
        },
        // Anthropic models
        ModelInfo {
            provider: "anthropic".to_string(),
            model: "claude-3-5-sonnet-20241022".to_string(),
            endpoint: "https://api.anthropic.com/v1/messages".to_string(),
            prompt_cost: 0.000003,
            completion_cost: 0.000015,
        },
        ModelInfo {
            provider: "anthropic".to_string(),
            model: "claude-3-5-haiku-20241022".to_string(),
            endpoint: "https://api.anthropic.com/v1/messages".to_string(),
            prompt_cost: 0.0000008,
            completion_cost: 0.000004,
        },
        // Groq models (free)
        ModelInfo {
            provider: "groq".to_string(),
            model: "llama3-70b-8192".to_string(),
            endpoint: "https://api.groq.com/openai/v1/chat/completions".to_string(),
            prompt_cost: 0.0,
            completion_cost: 0.0,
        },
        ModelInfo {
            provider: "groq".to_string(),
            model: "llama3-8b-8192".to_string(),
            endpoint: "https://api.groq.com/openai/v1/chat/completions".to_string(),
            prompt_cost: 0.0,
            completion_cost: 0.0,
        },
        ModelInfo {
            provider: "groq".to_string(),
            model: "mixtral-8x7b-32768".to_string(),
            endpoint: "https://api.groq.com/openai/v1/chat/completions".to_string(),
            prompt_cost: 0.0,
            completion_cost: 0.0,
        },
        // Ollama (local)
        ModelInfo {
            provider: "ollama".to_string(),
            model: "codellama".to_string(),
            endpoint: "http://localhost:11434/api/chat".to_string(),
            prompt_cost: 0.0,
            completion_cost: 0.0,
        },
    ]
}
