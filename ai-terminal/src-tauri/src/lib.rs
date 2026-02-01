mod pty;
mod config;
mod cache;
mod context;
mod llm;
mod harm;
mod safeguard;
mod fep;
mod usage;

use std::sync::Mutex;
use tauri::State;

pub struct AppState {
    pub pty_manager: Mutex<Option<pty::PtyManager>>,
    pub config: Mutex<config::AppConfig>,
    pub cache: Mutex<cache::SuggestionCache>,
    pub harm_cache: Mutex<harm::HarmCache>,
    pub command_history: Mutex<Vec<String>>,
    pub usage_stats: Mutex<usage::UsageStats>,
    pub last_command: Mutex<Option<String>>,
    pub last_exit_code: Mutex<Option<i32>>,
    pub last_output: Mutex<String>,
}

#[tauri::command]
async fn spawn_shell(state: State<'_, AppState>) -> Result<(), String> {
    let mut pty_guard = state.pty_manager.lock().map_err(|e| e.to_string())?;
    
    if pty_guard.is_none() {
        let manager = pty::PtyManager::new().map_err(|e| e.to_string())?;
        *pty_guard = Some(manager);
    }
    
    Ok(())
}

#[tauri::command]
async fn write_to_pty(state: State<'_, AppState>, data: String) -> Result<(), String> {
    let mut pty_guard = state.pty_manager.lock().map_err(|e| e.to_string())?;
    
    if let Some(ref mut manager) = *pty_guard {
        manager.write(data.as_bytes()).map_err(|e| e.to_string())?;
    }
    
    Ok(())
}

#[tauri::command]
async fn read_from_pty(state: State<'_, AppState>) -> Result<String, String> {
    let mut pty_guard = state.pty_manager.lock().map_err(|e| e.to_string())?;
    
    if let Some(ref mut manager) = *pty_guard {
        manager.read().map_err(|e| e.to_string())
    } else {
        Ok(String::new())
    }
}

#[tauri::command]
async fn resize_pty(state: State<'_, AppState>, cols: u16, rows: u16) -> Result<(), String> {
    let mut pty_guard = state.pty_manager.lock().map_err(|e| e.to_string())?;
    
    if let Some(ref mut manager) = *pty_guard {
        manager.resize(cols, rows).map_err(|e| e.to_string())?;
    }
    
    Ok(())
}

#[tauri::command]
async fn get_suggestion(
    state: State<'_, AppState>,
    current_input: String,
) -> Result<llm::Suggestion, String> {
    // Check cache first
    {
        let cache = state.cache.lock().map_err(|e| e.to_string())?;
        if let Some(cached) = cache.get(&current_input) {
            return Ok(cached);
        }
    }
    
    // Get config
    let config = {
        let cfg = state.config.lock().map_err(|e| e.to_string())?;
        cfg.clone()
    };
    
    // Get command history
    let history = {
        let hist = state.command_history.lock().map_err(|e| e.to_string())?;
        hist.clone()
    };
    
    // Get current working directory from PTY
    let cwd = {
        let pty_guard = state.pty_manager.lock().map_err(|e| e.to_string())?;
        if let Some(ref manager) = *pty_guard {
            manager.get_cwd()
        } else {
            std::env::current_dir()
                .map(|p| p.to_string_lossy().to_string())
                .unwrap_or_default()
        }
    };
    
    // Build context
    let ctx = context::TerminalContext {
        current_input: current_input.clone(),
        command_history: history,
        cwd,
        env_vars: std::env::vars().collect(),
    };
    
    // Get suggestion from LLM
    let suggestion = llm::get_completion(&config, &ctx).await?;
    
    // Cache the result
    {
        let mut cache = state.cache.lock().map_err(|e| e.to_string())?;
        cache.set(&current_input, suggestion.clone());
    }
    
    Ok(suggestion)
}

#[tauri::command]
async fn add_to_history(state: State<'_, AppState>, command: String) -> Result<(), String> {
    let mut history = state.command_history.lock().map_err(|e| e.to_string())?;
    history.push(command);
    
    // Keep only last 100 commands
    if history.len() > 100 {
        history.remove(0);
    }
    
    Ok(())
}

#[tauri::command]
async fn get_config(state: State<'_, AppState>) -> Result<config::AppConfig, String> {
    let config = state.config.lock().map_err(|e| e.to_string())?;
    Ok(config.clone())
}

#[tauri::command]
async fn set_config(state: State<'_, AppState>, new_config: config::AppConfig) -> Result<(), String> {
    let mut config = state.config.lock().map_err(|e| e.to_string())?;
    *config = new_config.clone();
    config::save_config(&new_config).map_err(|e| e.to_string())?;
    Ok(())
}

#[tauri::command]
async fn get_cwd(state: State<'_, AppState>) -> Result<String, String> {
    let pty_guard = state.pty_manager.lock().map_err(|e| e.to_string())?;
    
    if let Some(ref manager) = *pty_guard {
        Ok(manager.get_cwd())
    } else {
        std::env::current_dir()
            .map(|p| p.to_string_lossy().to_string())
            .map_err(|e| e.to_string())
    }
}

#[tauri::command]
async fn is_pty_ready(state: State<'_, AppState>) -> Result<bool, String> {
    let pty_guard = state.pty_manager.lock().map_err(|e| e.to_string())?;
    
    if let Some(ref manager) = *pty_guard {
        Ok(manager.has_output())
    } else {
        Ok(false)
    }
}

// ============ Harm Detection Commands ============

#[tauri::command]
async fn check_command_harm(
    state: State<'_, AppState>,
    command: String,
) -> Result<harm::HarmResult, String> {
    // Check cache first
    {
        let cache = state.harm_cache.lock().map_err(|e| e.to_string())?;
        if let Some(cached) = cache.get(&command) {
            return Ok(cached);
        }
    }
    
    let config = {
        let cfg = state.config.lock().map_err(|e| e.to_string())?;
        cfg.clone()
    };
    
    // Skip if harm detection is disabled
    if !config.harm_detection_enabled {
        return Ok(harm::HarmResult::default());
    }
    
    let result = harm::check_command_harm(&config, &command).await?;
    
    // Cache the result
    {
        let mut cache = state.harm_cache.lock().map_err(|e| e.to_string())?;
        cache.set(&command, result.clone());
    }
    
    Ok(result)
}

// ============ Safeguard Commands ============

#[tauri::command]
async fn check_safeguard(
    state: State<'_, AppState>,
    command: String,
) -> Result<safeguard::SafeguardResult, String> {
    let config = state.config.lock().map_err(|e| e.to_string())?;
    Ok(safeguard::check_command_safeguard(&command, config.safeguards_enabled))
}

#[tauri::command]
async fn toggle_safeguards(
    state: State<'_, AppState>,
    enabled: bool,
) -> Result<(), String> {
    let mut config = state.config.lock().map_err(|e| e.to_string())?;
    config.safeguards_enabled = enabled;
    config::save_config(&config).map_err(|e| e.to_string())?;
    Ok(())
}

#[tauri::command]
async fn get_dangerous_patterns() -> Result<Vec<(String, String, String)>, String> {
    Ok(safeguard::get_dangerous_patterns())
}

// ============ FEP (Fix Error Please) Commands ============

#[tauri::command]
async fn record_command_result(
    state: State<'_, AppState>,
    command: String,
    exit_code: i32,
    output: String,
) -> Result<(), String> {
    {
        let mut last_cmd = state.last_command.lock().map_err(|e| e.to_string())?;
        *last_cmd = Some(command);
    }
    {
        let mut last_exit = state.last_exit_code.lock().map_err(|e| e.to_string())?;
        *last_exit = Some(exit_code);
    }
    {
        let mut last_out = state.last_output.lock().map_err(|e| e.to_string())?;
        // Keep output limited to 10KB
        *last_out = if output.len() > 10240 {
            output[..10240].to_string()
        } else {
            output
        };
    }
    Ok(())
}

#[tauri::command]
async fn get_error_fix(
    state: State<'_, AppState>,
    command: String,
    exit_code: i32,
    output: String,
) -> Result<fep::FixSuggestion, String> {
    let config = {
        let cfg = state.config.lock().map_err(|e| e.to_string())?;
        cfg.clone()
    };
    
    let history = {
        let hist = state.command_history.lock().map_err(|e| e.to_string())?;
        hist.clone()
    };
    
    let cwd = {
        let pty_guard = state.pty_manager.lock().map_err(|e| e.to_string())?;
        if let Some(ref manager) = *pty_guard {
            manager.get_cwd()
        } else {
            std::env::current_dir()
                .map(|p| p.to_string_lossy().to_string())
                .unwrap_or_default()
        }
    };
    
    let ctx = fep::ErrorContext {
        command,
        exit_code,
        output,
        cwd,
        history,
    };
    
    fep::get_error_fix(&config, &ctx).await
}

#[tauri::command]
async fn get_last_error(
    state: State<'_, AppState>,
) -> Result<Option<fep::ErrorContext>, String> {
    let command = {
        let cmd = state.last_command.lock().map_err(|e| e.to_string())?;
        cmd.clone()
    };
    
    let exit_code = {
        let code = state.last_exit_code.lock().map_err(|e| e.to_string())?;
        *code
    };
    
    let output = {
        let out = state.last_output.lock().map_err(|e| e.to_string())?;
        out.clone()
    };
    
    let history = {
        let hist = state.command_history.lock().map_err(|e| e.to_string())?;
        hist.clone()
    };
    
    let cwd = {
        let pty_guard = state.pty_manager.lock().map_err(|e| e.to_string())?;
        if let Some(ref manager) = *pty_guard {
            manager.get_cwd()
        } else {
            std::env::current_dir()
                .map(|p| p.to_string_lossy().to_string())
                .unwrap_or_default()
        }
    };
    
    match (command, exit_code) {
        (Some(cmd), Some(code)) if code != 0 => {
            Ok(Some(fep::ErrorContext {
                command: cmd,
                exit_code: code,
                output,
                cwd,
                history,
            }))
        }
        _ => Ok(None),
    }
}

// ============ Usage Statistics Commands ============

#[tauri::command]
async fn get_usage_stats(
    state: State<'_, AppState>,
) -> Result<usage::UsageStats, String> {
    let stats = state.usage_stats.lock().map_err(|e| e.to_string())?;
    Ok(stats.clone())
}

#[tauri::command]
async fn clear_usage_stats(
    state: State<'_, AppState>,
) -> Result<(), String> {
    {
        let mut stats = state.usage_stats.lock().map_err(|e| e.to_string())?;
        *stats = usage::UsageStats::default();
    }
    usage::clear_usage().map_err(|e| e.to_string())?;
    Ok(())
}

#[tauri::command]
async fn record_api_usage(
    state: State<'_, AppState>,
    provider: String,
    prompt_tokens: u64,
    completion_tokens: u64,
) -> Result<(), String> {
    let (prompt_cost, completion_cost) = {
        let config = state.config.lock().map_err(|e| e.to_string())?;
        usage::get_model_costs(&config.provider, &config.model)
    };
    
    {
        let mut stats = state.usage_stats.lock().map_err(|e| e.to_string())?;
        stats.record_request(&provider, prompt_tokens, completion_tokens, prompt_cost, completion_cost);
    }
    
    // Save usage to disk
    let stats = state.usage_stats.lock().map_err(|e| e.to_string())?;
    usage::save_usage(&stats).map_err(|e| e.to_string())?;
    
    Ok(())
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    // Hide console window on Windows
    #[cfg(target_os = "windows")]
    {
        hide_console::hide_console();
    }
    
    let config = config::load_config().unwrap_or_default();
    let usage_stats = usage::load_usage().unwrap_or_default();
    
    let app_state = AppState {
        pty_manager: Mutex::new(None),
        config: Mutex::new(config),
        cache: Mutex::new(cache::SuggestionCache::new()),
        harm_cache: Mutex::new(harm::HarmCache::new()),
        command_history: Mutex::new(Vec::new()),
        usage_stats: Mutex::new(usage_stats),
        last_command: Mutex::new(None),
        last_exit_code: Mutex::new(None),
        last_output: Mutex::new(String::new()),
    };
    
    tauri::Builder::default()
        .plugin(tauri_plugin_shell::init())
        .manage(app_state)
        .invoke_handler(tauri::generate_handler![
            spawn_shell,
            write_to_pty,
            read_from_pty,
            resize_pty,
            get_suggestion,
            add_to_history,
            get_config,
            set_config,
            get_cwd,
            is_pty_ready,
            // Harm detection
            check_command_harm,
            // Safeguards
            check_safeguard,
            toggle_safeguards,
            get_dangerous_patterns,
            // FEP (Fix Error Please)
            record_command_result,
            get_error_fix,
            get_last_error,
            // Usage statistics
            get_usage_stats,
            clear_usage_stats,
            record_api_usage,
        ])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
