//! Comprehensive tests for the context module

use crate::context::TerminalContext;

#[cfg(test)]
mod context_tests {
    use super::*;

    fn create_test_context() -> TerminalContext {
        TerminalContext {
            current_input: "git ".to_string(),
            command_history: vec![
                "ls -la".to_string(),
                "cd project".to_string(),
                "npm install".to_string(),
            ],
            cwd: "/home/user/project".to_string(),
            env_vars: vec![
                ("HOME".to_string(), "/home/user".to_string()),
                ("PATH".to_string(), "/usr/bin:/bin".to_string()),
                ("USER".to_string(), "testuser".to_string()),
                ("API_KEY".to_string(), "secret123".to_string()),
                ("AWS_SECRET_KEY".to_string(), "aws-secret".to_string()),
            ],
        }
    }

    // ============ Sanitization Tests ============

    #[test]
    fn test_sanitize_history_removes_hex_hashes() {
        let ctx = TerminalContext {
            current_input: "".to_string(),
            command_history: vec![
                "git commit -m 'fix' abc123def456789012345678901234567890".to_string(),
            ],
            cwd: "/home/user".to_string(),
            env_vars: vec![],
        };

        let sanitized = ctx.get_sanitized_history();
        assert!(sanitized[0].contains("REDACTED"));
        assert!(!sanitized[0].contains("abc123def456789012345678901234567890"));
    }

    #[test]
    fn test_sanitize_history_removes_uuids() {
        let ctx = TerminalContext {
            current_input: "".to_string(),
            command_history: vec![
                "curl api.com/users/550e8400-e29b-41d4-a716-446655440000".to_string(),
            ],
            cwd: "/home/user".to_string(),
            env_vars: vec![],
        };

        let sanitized = ctx.get_sanitized_history();
        assert!(sanitized[0].contains("REDACTED_UUID"));
        assert!(!sanitized[0].contains("550e8400-e29b-41d4-a716-446655440000"));
    }

    #[test]
    fn test_sanitize_history_removes_api_keys() {
        let ctx = TerminalContext {
            current_input: "".to_string(),
            command_history: vec![
                "export OPENAI_KEY=sk-1234567890abcdefghijklmnopqrstuvwxyz".to_string(),
            ],
            cwd: "/home/user".to_string(),
            env_vars: vec![],
        };

        let sanitized = ctx.get_sanitized_history();
        assert!(sanitized[0].contains("REDACTED"));
        assert!(!sanitized[0].contains("sk-1234567890abcdefghijklmnopqrstuvwxyz"));
    }

    #[test]
    fn test_sanitize_keeps_normal_commands() {
        let ctx = TerminalContext {
            current_input: "".to_string(),
            command_history: vec![
                "git status".to_string(),
                "ls -la".to_string(),
                "npm run build".to_string(),
            ],
            cwd: "/home/user".to_string(),
            env_vars: vec![],
        };

        let sanitized = ctx.get_sanitized_history();
        assert_eq!(sanitized[0], "git status");
        assert_eq!(sanitized[1], "ls -la");
        assert_eq!(sanitized[2], "npm run build");
    }

    // ============ Environment Variable Filtering Tests ============

    #[test]
    fn test_safe_env_vars_excludes_sensitive() {
        let ctx = create_test_context();
        let safe_vars = ctx.get_safe_env_vars();

        // Should include safe vars
        assert!(safe_vars.contains(&"HOME".to_string()));
        assert!(safe_vars.contains(&"PATH".to_string()));
        assert!(safe_vars.contains(&"USER".to_string()));

        // Should exclude sensitive vars
        assert!(!safe_vars.contains(&"API_KEY".to_string()));
        assert!(!safe_vars.contains(&"AWS_SECRET_KEY".to_string()));
    }

    #[test]
    fn test_safe_env_vars_excludes_key_pattern() {
        let ctx = TerminalContext {
            current_input: "".to_string(),
            command_history: vec![],
            cwd: "/home/user".to_string(),
            env_vars: vec![
                ("DATABASE_PASSWORD".to_string(), "secret".to_string()),
                ("AUTH_TOKEN".to_string(), "token123".to_string()),
                ("PRIVATE_KEY".to_string(), "key".to_string()),
                ("NORMAL_VAR".to_string(), "value".to_string()),
            ],
        };

        let safe_vars = ctx.get_safe_env_vars();
        
        assert!(!safe_vars.contains(&"DATABASE_PASSWORD".to_string()));
        assert!(!safe_vars.contains(&"AUTH_TOKEN".to_string()));
        assert!(!safe_vars.contains(&"PRIVATE_KEY".to_string()));
        assert!(safe_vars.contains(&"NORMAL_VAR".to_string()));
    }

    #[test]
    fn test_safe_env_vars_excludes_aws() {
        let ctx = TerminalContext {
            current_input: "".to_string(),
            command_history: vec![],
            cwd: "/home/user".to_string(),
            env_vars: vec![
                ("AWS_ACCESS_KEY_ID".to_string(), "AKIA...".to_string()),
                ("AWS_SECRET_ACCESS_KEY".to_string(), "secret".to_string()),
                ("AWS_REGION".to_string(), "us-east-1".to_string()),
            ],
        };

        let safe_vars = ctx.get_safe_env_vars();
        
        // All AWS vars should be excluded due to containing AWS_ prefix
        assert!(safe_vars.is_empty() || !safe_vars.iter().any(|v| v.starts_with("AWS_")));
    }

    #[test]
    fn test_safe_env_vars_only_returns_names() {
        let ctx = create_test_context();
        let safe_vars = ctx.get_safe_env_vars();

        // Should not contain any values
        assert!(!safe_vars.contains(&"/home/user".to_string()));
        assert!(!safe_vars.contains(&"/usr/bin:/bin".to_string()));
    }

    // ============ Edge Cases ============

    #[test]
    fn test_empty_history() {
        let ctx = TerminalContext {
            current_input: "git".to_string(),
            command_history: vec![],
            cwd: "/home/user".to_string(),
            env_vars: vec![],
        };

        let sanitized = ctx.get_sanitized_history();
        assert!(sanitized.is_empty());
    }

    #[test]
    fn test_empty_env_vars() {
        let ctx = TerminalContext {
            current_input: "git".to_string(),
            command_history: vec!["ls".to_string()],
            cwd: "/home/user".to_string(),
            env_vars: vec![],
        };

        let safe_vars = ctx.get_safe_env_vars();
        assert!(safe_vars.is_empty());
    }

    #[test]
    fn test_special_characters_in_command() {
        let ctx = TerminalContext {
            current_input: "".to_string(),
            command_history: vec![
                r#"echo "hello 'world'" | grep -E "test.*pattern""#.to_string(),
            ],
            cwd: "/home/user".to_string(),
            env_vars: vec![],
        };

        let sanitized = ctx.get_sanitized_history();
        // Should preserve special characters that aren't sensitive
        assert!(sanitized[0].contains("echo"));
        assert!(sanitized[0].contains("grep"));
    }

    #[test]
    fn test_mixed_sensitive_data() {
        let ctx = TerminalContext {
            current_input: "".to_string(),
            command_history: vec![
                "curl -H 'Authorization: Bearer sk-abcdefghijklmnopqrstuvwxyz1234567890' https://api.example.com/users/550e8400-e29b-41d4-a716-446655440000".to_string(),
            ],
            cwd: "/home/user".to_string(),
            env_vars: vec![],
        };

        let sanitized = ctx.get_sanitized_history();
        // Both API key and UUID should be redacted
        assert!(sanitized[0].contains("REDACTED"));
        assert!(!sanitized[0].contains("sk-"));
        assert!(!sanitized[0].contains("550e8400"));
    }
}
