//! Comprehensive tests for the configuration module

use crate::config::{AppConfig, get_available_models};

#[cfg(test)]
mod config_tests {
    use super::*;

    // ============ Default Config Tests ============

    #[test]
    fn test_default_config() {
        let config = AppConfig::default();
        
        assert_eq!(config.provider, "openai");
        assert_eq!(config.model, "gpt-4o-mini");
        assert!(config.api_key.is_empty());
        assert!(config.endpoint.is_none());
        assert_eq!(config.debounce_ms, 300);
        assert!(config.ghost_text_enabled);
        assert_eq!(config.temperature, 0.0);
        assert_eq!(config.max_suggestions, 1);
        assert_eq!(config.max_history_commands, 20);
    }

    #[test]
    fn test_default_safety_settings() {
        let config = AppConfig::default();
        
        assert!(config.safeguards_enabled);
        assert!(config.harm_detection_enabled);
        assert!(config.show_explanations);
    }

    // ============ Serialization Tests ============

    #[test]
    fn test_config_serialization() {
        let config = AppConfig::default();
        let json = serde_json::to_string(&config);
        
        assert!(json.is_ok());
    }

    #[test]
    fn test_config_deserialization() {
        let json = r#"{
            "provider": "anthropic",
            "model": "claude-3-5-sonnet-20241022",
            "api_key": "test-key",
            "endpoint": null,
            "debounce_ms": 500,
            "ghost_text_enabled": false,
            "temperature": 0.5,
            "max_suggestions": 3,
            "max_history_commands": 50,
            "safeguards_enabled": false,
            "harm_detection_enabled": true,
            "show_explanations": false
        }"#;
        
        let config: Result<AppConfig, _> = serde_json::from_str(json);
        assert!(config.is_ok());
        
        let config = config.unwrap();
        assert_eq!(config.provider, "anthropic");
        assert_eq!(config.model, "claude-3-5-sonnet-20241022");
        assert_eq!(config.api_key, "test-key");
        assert_eq!(config.debounce_ms, 500);
        assert!(!config.ghost_text_enabled);
        assert_eq!(config.temperature, 0.5);
        assert!(!config.safeguards_enabled);
    }

    #[test]
    fn test_config_deserialization_with_defaults() {
        // Test that missing safety fields get defaults
        let json = r#"{
            "provider": "openai",
            "model": "gpt-4o-mini",
            "api_key": "",
            "endpoint": null,
            "debounce_ms": 300,
            "ghost_text_enabled": true,
            "temperature": 0.0,
            "max_suggestions": 1,
            "max_history_commands": 20
        }"#;
        
        let config: Result<AppConfig, _> = serde_json::from_str(json);
        assert!(config.is_ok());
        
        let config = config.unwrap();
        // Safety fields should default to true
        assert!(config.safeguards_enabled);
        assert!(config.harm_detection_enabled);
        assert!(config.show_explanations);
    }

    #[test]
    fn test_config_roundtrip() {
        let original = AppConfig {
            provider: "groq".to_string(),
            model: "llama3-70b-8192".to_string(),
            api_key: "secret-key".to_string(),
            endpoint: Some("https://custom.endpoint.com".to_string()),
            debounce_ms: 400,
            ghost_text_enabled: true,
            temperature: 0.7,
            max_suggestions: 2,
            max_history_commands: 30,
            safeguards_enabled: true,
            harm_detection_enabled: false,
            show_explanations: true,
        };
        
        let json = serde_json::to_string(&original).unwrap();
        let restored: AppConfig = serde_json::from_str(&json).unwrap();
        
        assert_eq!(original.provider, restored.provider);
        assert_eq!(original.model, restored.model);
        assert_eq!(original.api_key, restored.api_key);
        assert_eq!(original.endpoint, restored.endpoint);
        assert_eq!(original.debounce_ms, restored.debounce_ms);
        assert_eq!(original.ghost_text_enabled, restored.ghost_text_enabled);
        assert_eq!(original.temperature, restored.temperature);
        assert_eq!(original.safeguards_enabled, restored.safeguards_enabled);
        assert_eq!(original.harm_detection_enabled, restored.harm_detection_enabled);
    }

    // ============ Available Models Tests ============

    #[test]
    fn test_available_models_not_empty() {
        let models = get_available_models();
        assert!(!models.is_empty());
    }

    #[test]
    fn test_available_models_have_openai() {
        let models = get_available_models();
        let openai_models: Vec<_> = models.iter().filter(|m| m.provider == "openai").collect();
        assert!(!openai_models.is_empty());
    }

    #[test]
    fn test_available_models_have_anthropic() {
        let models = get_available_models();
        let anthropic_models: Vec<_> = models.iter().filter(|m| m.provider == "anthropic").collect();
        assert!(!anthropic_models.is_empty());
    }

    #[test]
    fn test_available_models_have_groq() {
        let models = get_available_models();
        let groq_models: Vec<_> = models.iter().filter(|m| m.provider == "groq").collect();
        assert!(!groq_models.is_empty());
    }

    #[test]
    fn test_available_models_have_ollama() {
        let models = get_available_models();
        let ollama_models: Vec<_> = models.iter().filter(|m| m.provider == "ollama").collect();
        assert!(!ollama_models.is_empty());
    }

    #[test]
    fn test_model_info_has_required_fields() {
        let models = get_available_models();
        for model in models {
            assert!(!model.provider.is_empty());
            assert!(!model.model.is_empty());
            assert!(!model.endpoint.is_empty());
            // Cost should be non-negative
            assert!(model.prompt_cost >= 0.0);
            assert!(model.completion_cost >= 0.0);
        }
    }

    #[test]
    fn test_groq_models_are_free() {
        let models = get_available_models();
        let groq_models: Vec<_> = models.iter().filter(|m| m.provider == "groq").collect();
        
        for model in groq_models {
            assert_eq!(model.prompt_cost, 0.0);
            assert_eq!(model.completion_cost, 0.0);
        }
    }

    #[test]
    fn test_ollama_models_are_free() {
        let models = get_available_models();
        let ollama_models: Vec<_> = models.iter().filter(|m| m.provider == "ollama").collect();
        
        for model in ollama_models {
            assert_eq!(model.prompt_cost, 0.0);
            assert_eq!(model.completion_cost, 0.0);
        }
    }

    // ============ Validation Tests ============

    #[test]
    fn test_temperature_valid_range() {
        let config = AppConfig::default();
        assert!(config.temperature >= 0.0 && config.temperature <= 1.0);
    }

    #[test]
    fn test_debounce_reasonable_value() {
        let config = AppConfig::default();
        assert!(config.debounce_ms >= 100 && config.debounce_ms <= 2000);
    }

    #[test]
    fn test_max_history_positive() {
        let config = AppConfig::default();
        assert!(config.max_history_commands > 0);
    }
}
