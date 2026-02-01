use serde::{Deserialize, Serialize};
use std::fs;
use std::path::PathBuf;
use std::collections::HashMap;

use crate::config::get_config_path;

#[derive(Debug, Clone, Serialize, Deserialize, Default)]
pub struct ProviderUsage {
    pub request_count: u64,
    pub prompt_tokens: u64,
    pub completion_tokens: u64,
    pub total_cost: f64,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct UsageStats {
    pub total_requests: u64,
    pub total_prompt_tokens: u64,
    pub total_completion_tokens: u64,
    pub total_cost: f64,
    pub by_provider: HashMap<String, ProviderUsage>,
    pub cache_hits: u64,
    pub cache_misses: u64,
}

impl Default for UsageStats {
    fn default() -> Self {
        Self {
            total_requests: 0,
            total_prompt_tokens: 0,
            total_completion_tokens: 0,
            total_cost: 0.0,
            by_provider: HashMap::new(),
            cache_hits: 0,
            cache_misses: 0,
        }
    }
}

impl UsageStats {
    pub fn record_request(
        &mut self,
        provider: &str,
        prompt_tokens: u64,
        completion_tokens: u64,
        prompt_cost_per_token: f64,
        completion_cost_per_token: f64,
    ) {
        let request_cost = (prompt_tokens as f64 * prompt_cost_per_token)
            + (completion_tokens as f64 * completion_cost_per_token);

        // Update totals
        self.total_requests += 1;
        self.total_prompt_tokens += prompt_tokens;
        self.total_completion_tokens += completion_tokens;
        self.total_cost += request_cost;

        // Update per-provider stats
        let provider_stats = self
            .by_provider
            .entry(provider.to_string())
            .or_insert_with(ProviderUsage::default);

        provider_stats.request_count += 1;
        provider_stats.prompt_tokens += prompt_tokens;
        provider_stats.completion_tokens += completion_tokens;
        provider_stats.total_cost += request_cost;
    }

    pub fn record_cache_hit(&mut self) {
        self.cache_hits += 1;
    }

    pub fn record_cache_miss(&mut self) {
        self.cache_misses += 1;
    }

    pub fn get_cache_hit_rate(&self) -> f64 {
        let total = self.cache_hits + self.cache_misses;
        if total == 0 {
            0.0
        } else {
            self.cache_hits as f64 / total as f64
        }
    }

    pub fn get_average_cost_per_request(&self) -> f64 {
        if self.total_requests == 0 {
            0.0
        } else {
            self.total_cost / self.total_requests as f64
        }
    }
}

fn get_usage_path() -> PathBuf {
    let config_path = get_config_path();
    config_path.parent().unwrap_or(&config_path).join("usage.json")
}

pub fn load_usage() -> Result<UsageStats, Box<dyn std::error::Error>> {
    let path = get_usage_path();

    if path.exists() {
        let content = fs::read_to_string(&path)?;
        let stats: UsageStats = serde_json::from_str(&content)?;
        Ok(stats)
    } else {
        Ok(UsageStats::default())
    }
}

pub fn save_usage(stats: &UsageStats) -> Result<(), Box<dyn std::error::Error>> {
    let path = get_usage_path();
    let content = serde_json::to_string_pretty(stats)?;
    fs::write(&path, content)?;
    Ok(())
}

pub fn clear_usage() -> Result<(), Box<dyn std::error::Error>> {
    let path = get_usage_path();
    if path.exists() {
        fs::remove_file(&path)?;
    }
    Ok(())
}

/// Get cost info for a provider/model combination
pub fn get_model_costs(provider: &str, model: &str) -> (f64, f64) {
    // Returns (prompt_cost_per_token, completion_cost_per_token)
    match (provider.to_lowercase().as_str(), model) {
        // OpenAI
        ("openai", "gpt-4o") => (0.0000025, 0.00001),
        ("openai", "gpt-4o-mini") => (0.00000015, 0.0000006),
        ("openai", "o1-mini") => (0.000011, 0.000044),
        
        // Anthropic
        ("anthropic", "claude-3-5-sonnet-20241022") => (0.000003, 0.000015),
        ("anthropic", "claude-3-5-haiku-20241022") => (0.0000008, 0.000004),
        
        // Groq (free)
        ("groq", _) => (0.0, 0.0),
        
        // Ollama (local)
        ("ollama", _) => (0.0, 0.0),
        
        // Default
        _ => (0.0, 0.0),
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_record_request() {
        let mut stats = UsageStats::default();
        stats.record_request("openai", 100, 50, 0.0000025, 0.00001);

        assert_eq!(stats.total_requests, 1);
        assert_eq!(stats.total_prompt_tokens, 100);
        assert_eq!(stats.total_completion_tokens, 50);
        assert!(stats.total_cost > 0.0);
    }

    #[test]
    fn test_cache_hit_rate() {
        let mut stats = UsageStats::default();
        stats.record_cache_hit();
        stats.record_cache_hit();
        stats.record_cache_miss();

        let hit_rate = stats.get_cache_hit_rate();
        assert!((hit_rate - 0.666).abs() < 0.01);
    }
}
