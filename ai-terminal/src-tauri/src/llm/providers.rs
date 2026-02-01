use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(tag = "type", rename_all = "lowercase")]
pub enum Provider {
    OpenAI,
    Anthropic,
    Groq,
    Ollama,
}

impl Provider {
    pub fn from_str(s: &str) -> Self {
        match s.to_lowercase().as_str() {
            "openai" => Provider::OpenAI,
            "anthropic" => Provider::Anthropic,
            "groq" => Provider::Groq,
            "ollama" => Provider::Ollama,
            _ => Provider::OpenAI, // default
        }
    }
    
    pub fn default_endpoint(&self) -> &'static str {
        match self {
            Provider::OpenAI => "https://api.openai.com/v1/chat/completions",
            Provider::Anthropic => "https://api.anthropic.com/v1/messages",
            Provider::Groq => "https://api.groq.com/openai/v1/chat/completions",
            Provider::Ollama => "http://localhost:11434/api/chat",
        }
    }
    
    pub fn requires_api_key(&self) -> bool {
        !matches!(self, Provider::Ollama)
    }
}
