mod pty;
mod config;
mod cache;
mod context;
mod llm;

use std::sync::Mutex;
use tauri::State;

pub struct AppState {
    pub pty_manager: Mutex<Option<pty::PtyManager>>,
    pub config: Mutex<config::AppConfig>,
    pub cache: Mutex<cache::SuggestionCache>,
    pub command_history: Mutex<Vec<String>>,
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

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    // Hide console window on Windows
    #[cfg(target_os = "windows")]
    {
        hide_console::hide_console();
    }
    
    let config = config::load_config().unwrap_or_default();
    
    let app_state = AppState {
        pty_manager: Mutex::new(None),
        config: Mutex::new(config),
        cache: Mutex::new(cache::SuggestionCache::new()),
        command_history: Mutex::new(Vec::new()),
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
        ])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
