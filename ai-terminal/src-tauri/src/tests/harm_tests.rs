//! Tests for the harm detection module
//! Note: Most harm detection tests require mocking the LLM API
//! These tests focus on the caching and parsing logic

use crate::harm::{HarmResult, HarmCache};

#[cfg(test)]
mod harm_cache_tests {
    use super::*;

    #[test]
    fn test_new_cache_is_empty() {
        let cache = HarmCache::new();
        assert!(cache.get("rm -rf /").is_none());
    }

    #[test]
    fn test_cache_set_and_get() {
        let mut cache = HarmCache::new();
        let result = HarmResult {
            is_harmful: true,
            reason: "Deletes entire filesystem".to_string(),
            severity: "critical".to_string(),
        };

        cache.set("rm -rf /", result.clone());
        
        let retrieved = cache.get("rm -rf /");
        assert!(retrieved.is_some());
        let retrieved = retrieved.unwrap();
        assert!(retrieved.is_harmful);
        assert_eq!(retrieved.severity, "critical");
    }

    #[test]
    fn test_cache_different_commands() {
        let mut cache = HarmCache::new();
        
        cache.set("rm -rf /", HarmResult {
            is_harmful: true,
            reason: "Dangerous".to_string(),
            severity: "critical".to_string(),
        });

        cache.set("ls -la", HarmResult {
            is_harmful: false,
            reason: "".to_string(),
            severity: "low".to_string(),
        });

        let rm_result = cache.get("rm -rf /").unwrap();
        let ls_result = cache.get("ls -la").unwrap();

        assert!(rm_result.is_harmful);
        assert!(!ls_result.is_harmful);
    }

    #[test]
    fn test_cache_miss_for_unknown_command() {
        let mut cache = HarmCache::new();
        cache.set("rm -rf /", HarmResult::default());

        assert!(cache.get("different command").is_none());
    }

    #[test]
    fn test_cache_clear() {
        let mut cache = HarmCache::new();
        cache.set("rm -rf /", HarmResult {
            is_harmful: true,
            reason: "Test".to_string(),
            severity: "critical".to_string(),
        });

        assert!(cache.get("rm -rf /").is_some());
        
        cache.clear();
        
        assert!(cache.get("rm -rf /").is_none());
    }

    #[test]
    fn test_cache_uses_hash_key() {
        let mut cache = HarmCache::new();
        
        // Same command should give same cache hit
        cache.set("rm -rf /", HarmResult {
            is_harmful: true,
            reason: "Test".to_string(),
            severity: "critical".to_string(),
        });

        // Should retrieve with exact same command
        assert!(cache.get("rm -rf /").is_some());
        
        // Different command should miss
        assert!(cache.get("rm -rf / ").is_none()); // trailing space
    }
}

#[cfg(test)]
mod harm_result_tests {
    use super::*;

    #[test]
    fn test_default_harm_result() {
        let result = HarmResult::default();
        
        assert!(!result.is_harmful);
        assert!(result.reason.is_empty());
        assert_eq!(result.severity, "low");
    }

    #[test]
    fn test_harm_result_serialization() {
        let result = HarmResult {
            is_harmful: true,
            reason: "This command will delete all files".to_string(),
            severity: "critical".to_string(),
        };

        let json = serde_json::to_string(&result);
        assert!(json.is_ok());
        
        let json = json.unwrap();
        assert!(json.contains("is_harmful"));
        assert!(json.contains("true"));
        assert!(json.contains("critical"));
    }

    #[test]
    fn test_harm_result_deserialization() {
        let json = r#"{
            "is_harmful": true,
            "reason": "Potential data loss",
            "severity": "high"
        }"#;

        let result: Result<HarmResult, _> = serde_json::from_str(json);
        assert!(result.is_ok());
        
        let result = result.unwrap();
        assert!(result.is_harmful);
        assert_eq!(result.reason, "Potential data loss");
        assert_eq!(result.severity, "high");
    }

    #[test]
    fn test_harm_result_clone() {
        let original = HarmResult {
            is_harmful: true,
            reason: "Test reason".to_string(),
            severity: "medium".to_string(),
        };

        let cloned = original.clone();
        
        assert_eq!(original.is_harmful, cloned.is_harmful);
        assert_eq!(original.reason, cloned.reason);
        assert_eq!(original.severity, cloned.severity);
    }
}

#[cfg(test)]
mod harm_severity_tests {
    use super::*;

    #[test]
    fn test_severity_levels() {
        let severities = vec!["low", "medium", "high", "critical"];
        
        for severity in severities {
            let result = HarmResult {
                is_harmful: true,
                reason: "Test".to_string(),
                severity: severity.to_string(),
            };
            
            // Should serialize/deserialize correctly
            let json = serde_json::to_string(&result).unwrap();
            let restored: HarmResult = serde_json::from_str(&json).unwrap();
            assert_eq!(restored.severity, severity);
        }
    }
}
