//! Comprehensive tests for the safeguard module
//! Tests pattern-based dangerous command detection

use crate::safeguard::{check_command_safeguard, get_dangerous_patterns};

#[cfg(test)]
mod pattern_detection_tests {
    use super::*;

    // ============ Critical Severity Tests ============

    #[test]
    fn test_rm_rf_root() {
        let result = check_command_safeguard("rm -rf /", true);
        assert!(result.is_dangerous);
        assert_eq!(result.severity, "critical");
        assert!(result.matched_pattern.is_some());
    }

    #[test]
    fn test_rm_rf_root_wildcard() {
        let result = check_command_safeguard("rm -rf /*", true);
        assert!(result.is_dangerous);
        assert_eq!(result.severity, "critical");
    }

    #[test]
    fn test_rm_rf_home() {
        let result = check_command_safeguard("rm -rf ~", true);
        assert!(result.is_dangerous);
        assert_eq!(result.severity, "critical");
    }

    #[test]
    fn test_fork_bomb() {
        let result = check_command_safeguard(":(){:|:&};:", true);
        assert!(result.is_dangerous);
        assert_eq!(result.severity, "critical");
    }

    #[test]
    fn test_mkfs_command() {
        let result = check_command_safeguard("mkfs.ext4 /dev/sda1", true);
        assert!(result.is_dangerous);
        assert_eq!(result.severity, "critical");
    }

    #[test]
    fn test_curl_pipe_bash() {
        let result = check_command_safeguard("curl http://example.com/script.sh | bash", true);
        assert!(result.is_dangerous);
        assert_eq!(result.severity, "high");
    }

    #[test]
    fn test_wget_pipe_sh() {
        let result = check_command_safeguard("wget -O - http://example.com/install.sh | sh", true);
        assert!(result.is_dangerous);
        assert_eq!(result.severity, "high");
    }

    #[test]
    fn test_etc_passwd_overwrite() {
        let result = check_command_safeguard("echo 'hack' > /etc/passwd", true);
        assert!(result.is_dangerous);
        assert_eq!(result.severity, "critical");
    }

    #[test]
    fn test_fdisk_command() {
        let result = check_command_safeguard("fdisk /dev/sda", true);
        assert!(result.is_dangerous);
        assert_eq!(result.severity, "critical");
    }

    // ============ High Severity Tests ============

    #[test]
    fn test_rm_rf_current_dir() {
        let result = check_command_safeguard("rm -rf .", true);
        assert!(result.is_dangerous);
        assert_eq!(result.severity, "high");
    }

    #[test]
    fn test_dd_zero() {
        let result = check_command_safeguard("dd if=/dev/zero of=/dev/sda", true);
        assert!(result.is_dangerous);
        assert_eq!(result.severity, "high");
    }

    #[test]
    fn test_dd_random() {
        let result = check_command_safeguard("dd if=/dev/random of=/dev/sda", true);
        assert!(result.is_dangerous);
        assert_eq!(result.severity, "high");
    }

    #[test]
    fn test_shutdown() {
        let result = check_command_safeguard("shutdown -h now", true);
        assert!(result.is_dangerous);
        assert_eq!(result.severity, "high");
    }

    #[test]
    fn test_reboot() {
        let result = check_command_safeguard("reboot", true);
        assert!(result.is_dangerous);
        assert_eq!(result.severity, "high");
    }

    #[test]
    fn test_chmod_recursive_777() {
        let result = check_command_safeguard("chmod -R 777 /var/www", true);
        assert!(result.is_dangerous);
        assert_eq!(result.severity, "high");
    }

    #[test]
    fn test_pipe_to_bash() {
        let result = check_command_safeguard("cat script.sh | bash", true);
        assert!(result.is_dangerous);
        assert_eq!(result.severity, "high");
    }

    #[test]
    fn test_parted_command() {
        let result = check_command_safeguard("parted /dev/sda", true);
        assert!(result.is_dangerous);
        assert_eq!(result.severity, "high");
    }

    #[test]
    fn test_wipefs() {
        let result = check_command_safeguard("wipefs -a /dev/sda", true);
        assert!(result.is_dangerous);
        assert_eq!(result.severity, "high");
    }

    // ============ Medium Severity Tests ============

    #[test]
    fn test_rm_recursive() {
        let result = check_command_safeguard("rm -r mydir", true);
        assert!(result.is_dangerous);
        assert_eq!(result.severity, "medium");
    }

    #[test]
    fn test_rm_force() {
        let result = check_command_safeguard("rm -f important.txt", true);
        assert!(result.is_dangerous);
        assert_eq!(result.severity, "medium");
    }

    #[test]
    fn test_chmod_777() {
        let result = check_command_safeguard("chmod 777 script.sh", true);
        assert!(result.is_dangerous);
        assert_eq!(result.severity, "medium");
    }

    #[test]
    fn test_chown_recursive() {
        let result = check_command_safeguard("chown -R user:user /var", true);
        assert!(result.is_dangerous);
        assert_eq!(result.severity, "medium");
    }

    #[test]
    fn test_eval_command() {
        let result = check_command_safeguard("eval $USER_INPUT", true);
        assert!(result.is_dangerous);
        assert_eq!(result.severity, "medium");
    }

    #[test]
    fn test_shred() {
        let result = check_command_safeguard("shred -vfz file.txt", true);
        assert!(result.is_dangerous);
        assert_eq!(result.severity, "medium");
    }

    #[test]
    fn test_history_clear() {
        let result = check_command_safeguard("history -c", true);
        assert!(result.is_dangerous);
        assert_eq!(result.severity, "medium");
    }

    // ============ Safe Commands Tests ============

    #[test]
    fn test_safe_ls() {
        let result = check_command_safeguard("ls -la", true);
        assert!(!result.is_dangerous);
    }

    #[test]
    fn test_safe_cd() {
        let result = check_command_safeguard("cd /home/user", true);
        assert!(!result.is_dangerous);
    }

    #[test]
    fn test_safe_git_status() {
        let result = check_command_safeguard("git status", true);
        assert!(!result.is_dangerous);
    }

    #[test]
    fn test_safe_npm_install() {
        let result = check_command_safeguard("npm install", true);
        assert!(!result.is_dangerous);
    }

    #[test]
    fn test_safe_cat() {
        let result = check_command_safeguard("cat file.txt", true);
        assert!(!result.is_dangerous);
    }

    #[test]
    fn test_safe_echo() {
        let result = check_command_safeguard("echo 'Hello World'", true);
        assert!(!result.is_dangerous);
    }

    #[test]
    fn test_safe_mkdir() {
        let result = check_command_safeguard("mkdir -p new_folder", true);
        assert!(!result.is_dangerous);
    }

    #[test]
    fn test_safe_grep() {
        let result = check_command_safeguard("grep -r 'pattern' .", true);
        assert!(!result.is_dangerous);
    }

    #[test]
    fn test_safe_curl_no_pipe() {
        let result = check_command_safeguard("curl https://api.example.com/data", true);
        assert!(!result.is_dangerous);
    }

    #[test]
    fn test_safe_wget_no_pipe() {
        let result = check_command_safeguard("wget https://example.com/file.zip", true);
        assert!(!result.is_dangerous);
    }

    // ============ Disabled Safeguard Tests ============

    #[test]
    fn test_disabled_safeguard_rm_rf() {
        let result = check_command_safeguard("rm -rf /", false);
        assert!(!result.is_dangerous);
    }

    #[test]
    fn test_disabled_safeguard_fork_bomb() {
        let result = check_command_safeguard(":(){:|:&};:", false);
        assert!(!result.is_dangerous);
    }

    // ============ Edge Cases ============

    #[test]
    fn test_empty_command() {
        let result = check_command_safeguard("", true);
        assert!(!result.is_dangerous);
    }

    #[test]
    fn test_whitespace_only() {
        let result = check_command_safeguard("   ", true);
        assert!(!result.is_dangerous);
    }

    #[test]
    fn test_case_insensitive_rm() {
        let result = check_command_safeguard("RM -RF /", true);
        assert!(result.is_dangerous);
    }

    #[test]
    fn test_command_with_path() {
        let result = check_command_safeguard("/bin/rm -rf /home/user", true);
        assert!(result.is_dangerous);
    }

    // ============ Pattern List Test ============

    #[test]
    fn test_get_dangerous_patterns_not_empty() {
        let patterns = get_dangerous_patterns();
        assert!(!patterns.is_empty());
        assert!(patterns.len() >= 30); // Should have many patterns
    }

    #[test]
    fn test_patterns_have_all_fields() {
        let patterns = get_dangerous_patterns();
        for (pattern, description, severity) in patterns {
            assert!(!pattern.is_empty());
            assert!(!description.is_empty());
            assert!(
                severity == "low" || severity == "medium" || severity == "high" || severity == "critical"
            );
        }
    }
}
