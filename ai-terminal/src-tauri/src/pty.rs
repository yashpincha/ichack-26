use portable_pty::{native_pty_system, CommandBuilder, PtyPair, PtySize};
use std::io::{Read, Write};
use std::sync::{Arc, Mutex};
use std::time::Duration;

pub struct PtyManager {
    pair: PtyPair,
    writer: Arc<Mutex<Box<dyn Write + Send>>>,
    #[allow(dead_code)]
    reader: Arc<Mutex<Box<dyn Read + Send>>>,
    cwd: String,
    read_buffer: Arc<Mutex<Vec<u8>>>,
}

impl PtyManager {
    pub fn new() -> Result<Self, Box<dyn std::error::Error>> {
        eprintln!("[PTY] Creating new PTY manager...");
        let pty_system = native_pty_system();
        
        eprintln!("[PTY] Opening PTY with size 80x24...");
        let pair = pty_system.openpty(PtySize {
            rows: 24,
            cols: 80,
            pixel_width: 0,
            pixel_height: 0,
        })?;
        eprintln!("[PTY] PTY opened successfully");
        
        // Determine the shell based on the OS
        #[cfg(target_os = "windows")]
        let shell = {
            // Prefer PowerShell on Windows for better experience - use FULL PATH
            let ps_path = "C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe";
            if std::path::Path::new(ps_path).exists() {
                ps_path.to_string()
            } else {
                // Fall back to COMSPEC (usually cmd.exe) with full path
                std::env::var("COMSPEC").unwrap_or_else(|_| "C:\\Windows\\System32\\cmd.exe".to_string())
            }
        };
        
        #[cfg(target_os = "macos")]
        let shell = std::env::var("SHELL").unwrap_or_else(|_| "/bin/zsh".to_string());
        
        #[cfg(target_os = "linux")]
        let shell = std::env::var("SHELL").unwrap_or_else(|_| "/bin/bash".to_string());
        
        #[cfg(not(any(target_os = "windows", target_os = "macos", target_os = "linux")))]
        let shell = std::env::var("SHELL").unwrap_or_else(|_| "/bin/sh".to_string());
        
        eprintln!("[PTY] Using shell: {}", shell);
        let mut cmd = CommandBuilder::new(&shell);
        
        // Set initial directory to home
        let home_dir = dirs::home_dir()
            .map(|p| p.to_string_lossy().to_string())
            .unwrap_or_else(|| ".".to_string());
        
        eprintln!("[PTY] Setting CWD to: {}", home_dir);
        cmd.cwd(&home_dir);
        
        // Set environment variables for proper terminal behavior
        cmd.env("TERM", "xterm-256color");
        cmd.env("COLORTERM", "truecolor");
        
        // Add shell-specific arguments for better behavior
        #[cfg(target_os = "windows")]
        {
            // Set Windows-specific environment variables
            cmd.env("TERM_PROGRAM", "ai-terminal");
            
            if shell.to_lowercase().contains("powershell") {
                cmd.arg("-NoLogo");
                cmd.arg("-NoExit");
                // Enable VT processing for proper ANSI escape sequence handling
                cmd.env("VIRTUAL_TERMINAL_LEVEL", "1");
            }
        }
        
        #[cfg(not(target_os = "windows"))]
        {
            // Enable interactive mode for bash/zsh
            if shell.contains("bash") || shell.contains("zsh") {
                cmd.arg("-i");
            }
        }
        
        // Spawn the child process
        eprintln!("[PTY] Spawning shell process...");
        let _child = pair.slave.spawn_command(cmd)?;
        eprintln!("[PTY] Shell process spawned successfully");
        
        // Get reader and writer
        eprintln!("[PTY] Getting reader and writer...");
        let reader = pair.master.try_clone_reader()?;
        let writer = pair.master.take_writer()?;
        eprintln!("[PTY] Reader and writer obtained");
        
        let read_buffer = Arc::new(Mutex::new(Vec::new()));
        let reader_arc = Arc::new(Mutex::new(reader));
        
        // Spawn a background thread to continuously read from PTY
        let buffer_clone = Arc::clone(&read_buffer);
        let reader_clone = Arc::clone(&reader_arc);
        eprintln!("[PTY] Starting background reader thread...");
        std::thread::spawn(move || {
            eprintln!("[PTY Reader] Thread started");
            let mut local_buffer = [0u8; 4096];
            let mut total_bytes_read: usize = 0;
            loop {
                let result = {
                    let mut reader_guard = match reader_clone.lock() {
                        Ok(guard) => guard,
                        Err(e) => {
                            eprintln!("[PTY Reader] Failed to lock reader: {}", e);
                            break;
                        }
                    };
                    reader_guard.read(&mut local_buffer)
                };
                
                match result {
                    Ok(0) => {
                        // EOF - shell exited
                        eprintln!("[PTY Reader] EOF received, shell may have exited");
                        std::thread::sleep(Duration::from_millis(100));
                    }
                    Ok(n) => {
                        total_bytes_read += n;
                        eprintln!("[PTY Reader] Read {} bytes (total: {})", n, total_bytes_read);
                        if let Ok(mut buf) = buffer_clone.lock() {
                            buf.extend_from_slice(&local_buffer[..n]);
                        }
                    }
                    Err(e) if e.kind() == std::io::ErrorKind::WouldBlock => {
                        std::thread::sleep(Duration::from_millis(10));
                    }
                    Err(e) => {
                        eprintln!("[PTY Reader] Read error: {}", e);
                        std::thread::sleep(Duration::from_millis(100));
                    }
                }
            }
            eprintln!("[PTY Reader] Thread exiting");
        });
        
        Ok(Self {
            pair,
            writer: Arc::new(Mutex::new(writer)),
            reader: reader_arc,
            cwd: home_dir,
            read_buffer,
        })
    }
    
    pub fn write(&mut self, data: &[u8]) -> Result<(), Box<dyn std::error::Error>> {
        eprintln!("[PTY] Writing {} bytes to PTY", data.len());
        let mut writer = self.writer.lock().map_err(|e| e.to_string())?;
        writer.write_all(data)?;
        writer.flush()?;
        eprintln!("[PTY] Write successful");
        Ok(())
    }
    
    pub fn read(&mut self) -> Result<String, Box<dyn std::error::Error>> {
        // Read from the buffer (populated by background thread)
        let output = {
            let mut buf = self.read_buffer.lock().map_err(|e| e.to_string())?;
            if buf.is_empty() {
                String::new()
            } else {
                let data = std::mem::take(&mut *buf);
                let output = String::from_utf8_lossy(&data).to_string();
                eprintln!("[PTY] Returning {} bytes from buffer", output.len());
                output
            }
        };
        
        // Try to detect CWD changes from common shell prompts
        // This is a simplified approach - real implementation would use shell integration
        if !output.is_empty() {
            self.try_update_cwd(&output);
        }
        
        Ok(output)
    }
    
    pub fn resize(&mut self, cols: u16, rows: u16) -> Result<(), Box<dyn std::error::Error>> {
        self.pair.master.resize(PtySize {
            rows,
            cols,
            pixel_width: 0,
            pixel_height: 0,
        })?;
        Ok(())
    }
    
    pub fn get_cwd(&self) -> String {
        self.cwd.clone()
    }
    
    pub fn has_output(&self) -> bool {
        if let Ok(buf) = self.read_buffer.lock() {
            !buf.is_empty()
        } else {
            false
        }
    }
    
    fn try_update_cwd(&mut self, output: &str) {
        // Look for common patterns that might indicate a directory change
        // This is a heuristic - proper shell integration would be better
        
        // Check for PWD environment variable updates (zsh/bash)
        if let Some(start) = output.find("PWD=") {
            if let Some(end) = output[start..].find('\n') {
                let pwd = &output[start + 4..start + end];
                if !pwd.is_empty() && std::path::Path::new(pwd).exists() {
                    self.cwd = pwd.to_string();
                }
            }
        }
    }
}

impl Drop for PtyManager {
    fn drop(&mut self) {
        // The PTY will be cleaned up automatically when dropped
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    
    #[test]
    fn test_pty_creation() {
        let result = PtyManager::new();
        assert!(result.is_ok());
    }
}
