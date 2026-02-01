use serde::{Deserialize, Serialize};

/// List of dangerous command patterns
const DANGEROUS_PATTERNS: &[(&str, &str, &str)] = &[
    // (pattern, description, severity)
    ("rm -rf /", "Recursive deletion of root filesystem", "critical"),
    ("rm -rf /*", "Recursive deletion of root filesystem", "critical"),
    ("rm -rf ~", "Recursive deletion of home directory", "critical"),
    ("rm -rf .", "Recursive deletion of current directory", "high"),
    ("rm -r ", "Recursive file deletion", "medium"),
    ("rm -f ", "Force file deletion", "medium"),
    (":(){:|:&};:", "Fork bomb", "critical"),
    ("dd if=/dev/zero", "Disk write operation", "high"),
    ("dd if=/dev/random", "Disk write operation", "high"),
    ("mkfs.", "Filesystem formatting", "critical"),
    ("fdisk ", "Disk partitioning", "critical"),
    ("parted ", "Disk partitioning", "high"),
    ("> /dev/sd", "Direct disk write", "critical"),
    ("chmod 777", "World-writable permissions", "medium"),
    ("chmod -R 777", "Recursive world-writable permissions", "high"),
    ("chown -R", "Recursive ownership change", "medium"),
    ("shutdown", "System shutdown", "high"),
    ("reboot", "System reboot", "high"),
    ("init 0", "System shutdown", "high"),
    ("init 6", "System reboot", "high"),
    ("halt", "System halt", "high"),
    ("poweroff", "System poweroff", "high"),
    ("curl | sh", "Remote code execution", "critical"),
    ("curl | bash", "Remote code execution", "critical"),
    ("wget | sh", "Remote code execution", "critical"),
    ("wget | bash", "Remote code execution", "critical"),
    ("| sh", "Piped shell execution", "high"),
    ("| bash", "Piped shell execution", "high"),
    ("eval ", "Dynamic code execution", "medium"),
    ("> /etc/passwd", "Passwd file modification", "critical"),
    ("> /etc/shadow", "Shadow file modification", "critical"),
    ("mv /* ", "Moving root filesystem", "critical"),
    ("cp /dev/null ", "Overwriting with null", "high"),
    (":(){ :|:& };:", "Fork bomb variant", "critical"),
    ("history -c", "Command history deletion", "medium"),
    ("shred ", "Secure file deletion", "medium"),
    ("wipefs ", "Filesystem signature wiping", "high"),
];

/// Windows-specific dangerous patterns
#[cfg(target_os = "windows")]
const WINDOWS_DANGEROUS_PATTERNS: &[(&str, &str, &str)] = &[
    ("del /f /s /q C:\\", "Recursive deletion of C drive", "critical"),
    ("rd /s /q C:\\", "Recursive directory deletion", "critical"),
    ("format C:", "Disk formatting", "critical"),
    ("format D:", "Disk formatting", "critical"),
    ("Remove-Item -Recurse -Force C:\\", "PowerShell recursive deletion", "critical"),
    ("rm -Recurse -Force C:\\", "PowerShell recursive deletion", "critical"),
    ("Stop-Computer", "System shutdown", "high"),
    ("Restart-Computer", "System restart", "high"),
    ("shutdown /s", "System shutdown", "high"),
    ("shutdown /r", "System restart", "high"),
    ("reg delete", "Registry deletion", "high"),
    ("bcdedit", "Boot configuration edit", "critical"),
];

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SafeguardResult {
    pub is_dangerous: bool,
    pub matched_pattern: Option<String>,
    pub description: String,
    pub severity: String,
}

impl Default for SafeguardResult {
    fn default() -> Self {
        Self {
            is_dangerous: false,
            matched_pattern: None,
            description: String::new(),
            severity: "low".to_string(),
        }
    }
}

/// Check if a command matches any dangerous patterns
pub fn check_command_safeguard(command: &str, enabled: bool) -> SafeguardResult {
    if !enabled {
        return SafeguardResult::default();
    }

    let command_lower = command.to_lowercase();

    // Check Unix patterns
    for (pattern, description, severity) in DANGEROUS_PATTERNS {
        if command_lower.contains(&pattern.to_lowercase()) {
            return SafeguardResult {
                is_dangerous: true,
                matched_pattern: Some(pattern.to_string()),
                description: description.to_string(),
                severity: severity.to_string(),
            };
        }
    }

    // Check Windows patterns on Windows
    #[cfg(target_os = "windows")]
    {
        for (pattern, description, severity) in WINDOWS_DANGEROUS_PATTERNS {
            if command_lower.contains(&pattern.to_lowercase()) {
                return SafeguardResult {
                    is_dangerous: true,
                    matched_pattern: Some(pattern.to_string()),
                    description: description.to_string(),
                    severity: severity.to_string(),
                };
            }
        }
    }

    SafeguardResult::default()
}

/// Get list of all dangerous patterns for settings UI
pub fn get_dangerous_patterns() -> Vec<(String, String, String)> {
    let mut patterns: Vec<(String, String, String)> = DANGEROUS_PATTERNS
        .iter()
        .map(|(p, d, s)| (p.to_string(), d.to_string(), s.to_string()))
        .collect();

    #[cfg(target_os = "windows")]
    {
        patterns.extend(
            WINDOWS_DANGEROUS_PATTERNS
                .iter()
                .map(|(p, d, s)| (p.to_string(), d.to_string(), s.to_string())),
        );
    }

    patterns
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_dangerous_rm() {
        let result = check_command_safeguard("rm -rf /", true);
        assert!(result.is_dangerous);
        assert_eq!(result.severity, "critical");
    }

    #[test]
    fn test_safe_command() {
        let result = check_command_safeguard("ls -la", true);
        assert!(!result.is_dangerous);
    }

    #[test]
    fn test_disabled_safeguard() {
        let result = check_command_safeguard("rm -rf /", false);
        assert!(!result.is_dangerous);
    }

    #[test]
    fn test_fork_bomb() {
        let result = check_command_safeguard(":(){:|:&};:", true);
        assert!(result.is_dangerous);
        assert_eq!(result.severity, "critical");
    }
}
