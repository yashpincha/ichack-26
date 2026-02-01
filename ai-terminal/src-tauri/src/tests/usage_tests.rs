//! Comprehensive tests for the usage statistics module

use crate::usage::{UsageStats, get_model_costs};

#[cfg(test)]
mod usage_stats_tests {
    use super::*;

    // ============ Basic Recording Tests ============

    #[test]
    fn test_new_stats_are_empty() {
        let stats = UsageStats::default();
        assert_eq!(stats.total_requests, 0);
        assert_eq!(stats.total_prompt_tokens, 0);
        assert_eq!(stats.total_completion_tokens, 0);
        assert_eq!(stats.total_cost, 0.0);
        assert_eq!(stats.cache_hits, 0);
        assert_eq!(stats.cache_misses, 0);
    }

    #[test]
    fn test_record_single_request() {
        let mut stats = UsageStats::default();
        stats.record_request("openai", 100, 50, 0.0000025, 0.00001);

        assert_eq!(stats.total_requests, 1);
        assert_eq!(stats.total_prompt_tokens, 100);
        assert_eq!(stats.total_completion_tokens, 50);
        assert!(stats.total_cost > 0.0);
    }

    #[test]
    fn test_record_multiple_requests() {
        let mut stats = UsageStats::default();
        stats.record_request("openai", 100, 50, 0.0000025, 0.00001);
        stats.record_request("openai", 200, 100, 0.0000025, 0.00001);
        stats.record_request("anthropic", 150, 75, 0.000003, 0.000015);

        assert_eq!(stats.total_requests, 3);
        assert_eq!(stats.total_prompt_tokens, 450);
        assert_eq!(stats.total_completion_tokens, 225);
    }

    #[test]
    fn test_record_request_updates_provider_stats() {
        let mut stats = UsageStats::default();
        stats.record_request("openai", 100, 50, 0.0000025, 0.00001);
        stats.record_request("openai", 200, 100, 0.0000025, 0.00001);

        let openai_stats = stats.by_provider.get("openai").unwrap();
        assert_eq!(openai_stats.request_count, 2);
        assert_eq!(openai_stats.prompt_tokens, 300);
        assert_eq!(openai_stats.completion_tokens, 150);
    }

    #[test]
    fn test_multiple_providers() {
        let mut stats = UsageStats::default();
        stats.record_request("openai", 100, 50, 0.0000025, 0.00001);
        stats.record_request("anthropic", 100, 50, 0.000003, 0.000015);
        stats.record_request("groq", 100, 50, 0.0, 0.0);

        assert_eq!(stats.by_provider.len(), 3);
        assert!(stats.by_provider.contains_key("openai"));
        assert!(stats.by_provider.contains_key("anthropic"));
        assert!(stats.by_provider.contains_key("groq"));
    }

    // ============ Cost Calculation Tests ============

    #[test]
    fn test_cost_calculation() {
        let mut stats = UsageStats::default();
        // 100 prompt tokens at $0.0000025 = $0.00025
        // 50 completion tokens at $0.00001 = $0.0005
        // Total = $0.00075
        stats.record_request("openai", 100, 50, 0.0000025, 0.00001);
        
        let expected_cost = (100.0 * 0.0000025) + (50.0 * 0.00001);
        assert!((stats.total_cost - expected_cost).abs() < 0.0000001);
    }

    #[test]
    fn test_zero_cost_for_free_providers() {
        let mut stats = UsageStats::default();
        stats.record_request("groq", 1000, 500, 0.0, 0.0);

        assert_eq!(stats.total_cost, 0.0);
        let groq_stats = stats.by_provider.get("groq").unwrap();
        assert_eq!(groq_stats.total_cost, 0.0);
    }

    // ============ Cache Tests ============

    #[test]
    fn test_record_cache_hit() {
        let mut stats = UsageStats::default();
        stats.record_cache_hit();
        stats.record_cache_hit();

        assert_eq!(stats.cache_hits, 2);
    }

    #[test]
    fn test_record_cache_miss() {
        let mut stats = UsageStats::default();
        stats.record_cache_miss();
        stats.record_cache_miss();
        stats.record_cache_miss();

        assert_eq!(stats.cache_misses, 3);
    }

    #[test]
    fn test_cache_hit_rate_empty() {
        let stats = UsageStats::default();
        assert_eq!(stats.get_cache_hit_rate(), 0.0);
    }

    #[test]
    fn test_cache_hit_rate_all_hits() {
        let mut stats = UsageStats::default();
        stats.record_cache_hit();
        stats.record_cache_hit();
        stats.record_cache_hit();

        assert_eq!(stats.get_cache_hit_rate(), 1.0);
    }

    #[test]
    fn test_cache_hit_rate_all_misses() {
        let mut stats = UsageStats::default();
        stats.record_cache_miss();
        stats.record_cache_miss();

        assert_eq!(stats.get_cache_hit_rate(), 0.0);
    }

    #[test]
    fn test_cache_hit_rate_mixed() {
        let mut stats = UsageStats::default();
        stats.record_cache_hit();
        stats.record_cache_hit();
        stats.record_cache_miss();

        let hit_rate = stats.get_cache_hit_rate();
        assert!((hit_rate - 0.666666).abs() < 0.01);
    }

    // ============ Average Cost Tests ============

    #[test]
    fn test_average_cost_empty() {
        let stats = UsageStats::default();
        assert_eq!(stats.get_average_cost_per_request(), 0.0);
    }

    #[test]
    fn test_average_cost_single_request() {
        let mut stats = UsageStats::default();
        stats.record_request("openai", 100, 50, 0.0000025, 0.00001);

        let avg = stats.get_average_cost_per_request();
        assert_eq!(avg, stats.total_cost);
    }

    #[test]
    fn test_average_cost_multiple_requests() {
        let mut stats = UsageStats::default();
        stats.record_request("openai", 100, 50, 0.0000025, 0.00001);
        stats.record_request("openai", 100, 50, 0.0000025, 0.00001);

        let avg = stats.get_average_cost_per_request();
        assert_eq!(avg, stats.total_cost / 2.0);
    }

    // ============ Model Costs Tests ============

    #[test]
    fn test_openai_gpt4o_costs() {
        let (prompt, completion) = get_model_costs("openai", "gpt-4o");
        assert_eq!(prompt, 0.0000025);
        assert_eq!(completion, 0.00001);
    }

    #[test]
    fn test_openai_gpt4o_mini_costs() {
        let (prompt, completion) = get_model_costs("openai", "gpt-4o-mini");
        assert_eq!(prompt, 0.00000015);
        assert_eq!(completion, 0.0000006);
    }

    #[test]
    fn test_anthropic_sonnet_costs() {
        let (prompt, completion) = get_model_costs("anthropic", "claude-3-5-sonnet-20241022");
        assert_eq!(prompt, 0.000003);
        assert_eq!(completion, 0.000015);
    }

    #[test]
    fn test_groq_free() {
        let (prompt, completion) = get_model_costs("groq", "llama3-70b-8192");
        assert_eq!(prompt, 0.0);
        assert_eq!(completion, 0.0);
    }

    #[test]
    fn test_ollama_free() {
        let (prompt, completion) = get_model_costs("ollama", "codellama");
        assert_eq!(prompt, 0.0);
        assert_eq!(completion, 0.0);
    }

    #[test]
    fn test_unknown_provider_defaults_to_free() {
        let (prompt, completion) = get_model_costs("unknown", "unknown-model");
        assert_eq!(prompt, 0.0);
        assert_eq!(completion, 0.0);
    }

    #[test]
    fn test_case_insensitive_provider() {
        let (prompt1, _) = get_model_costs("OpenAI", "gpt-4o");
        let (prompt2, _) = get_model_costs("OPENAI", "gpt-4o");
        let (prompt3, _) = get_model_costs("openai", "gpt-4o");
        
        assert_eq!(prompt1, prompt2);
        assert_eq!(prompt2, prompt3);
    }
}
