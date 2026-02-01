import { useEffect, useRef, useState, useCallback } from 'react';
import { Terminal as XTerm } from 'xterm';
import { FitAddon } from 'xterm-addon-fit';
import { WebLinksAddon } from 'xterm-addon-web-links';
import { invoke } from '@tauri-apps/api/core';
import GhostText from './GhostText';
import { useAutocomplete } from '../hooks/useAutocomplete';
import 'xterm/css/xterm.css';

interface TerminalProps {
  className?: string;
}

export default function Terminal({ className }: TerminalProps) {
  const terminalRef = useRef<HTMLDivElement>(null);
  const xtermRef = useRef<XTerm | null>(null);
  const fitAddonRef = useRef<FitAddon | null>(null);
  const isMountedRef = useRef(true); // Track if component is mounted
  const [isConnected, setIsConnected] = useState(false);
  const isConnectedRef = useRef(false); // Ref to avoid stale closure issues
  const [currentInput, setCurrentInput] = useState('');
  const [cursorPosition, setCursorPosition] = useState({ x: 0, y: 0 });
  const inputBufferRef = useRef('');
  const readIntervalRef = useRef<number | null>(null);
  const { suggestion, isLoading, clearSuggestion } = useAutocomplete(currentInput);
  
  // Ref to hold the latest input handler - start with a basic forwarder
  const inputHandlerRef = useRef<(data: string) => Promise<void>>(async (data: string) => {
    console.log('Initial handler - forwarding input to PTY:', data);
    try {
      await invoke('write_to_pty', { data });
    } catch (err) {
      console.error('Initial handler write error:', err);
    }
  });

  // Initialize terminal
  useEffect(() => {
    if (!terminalRef.current || xtermRef.current) return;
    
    isMountedRef.current = true;

    const xterm = new XTerm({
      theme: {
        background: '#1e1e1e',
        foreground: '#cccccc',
        cursor: '#ffffff',
        cursorAccent: '#000000',
        selectionBackground: '#264f78',
        black: '#000000',
        red: '#cd3131',
        green: '#0dbc79',
        yellow: '#e5e510',
        blue: '#2472c8',
        magenta: '#bc3fbc',
        cyan: '#11a8cd',
        white: '#e5e5e5',
        brightBlack: '#666666',
        brightRed: '#f14c4c',
        brightGreen: '#23d18b',
        brightYellow: '#f5f543',
        brightBlue: '#3b8eea',
        brightMagenta: '#d670d6',
        brightCyan: '#29b8db',
        brightWhite: '#ffffff',
      },
      fontFamily: "'Consolas', 'Monaco', 'Courier New', monospace",
      fontSize: 14,
      lineHeight: 1.2,
      cursorBlink: true,
      cursorStyle: 'block',
      allowProposedApi: true,
    });

    const fitAddon = new FitAddon();
    const webLinksAddon = new WebLinksAddon();

    xterm.loadAddon(fitAddon);
    xterm.loadAddon(webLinksAddon);

    xterm.open(terminalRef.current);
    
    xtermRef.current = xterm;
    fitAddonRef.current = fitAddon;

    // Delay fit() to ensure renderer is ready - fixes "dimensions undefined" error
    requestAnimationFrame(() => {
      // Check if component is still mounted before proceeding
      if (!isMountedRef.current) return;
      
      if (fitAddonRef.current && xtermRef.current) {
        fitAddonRef.current.fit();
        
        // Write a test message to verify xterm is working
        xtermRef.current.write('\x1b[32m[AI Terminal] Initializing...\x1b[0m\r\n');
        
        // Spawn shell after terminal is ready
        spawnShell();
      }
    });

    // Handle resize
    const handleResize = () => {
      if (fitAddonRef.current && xtermRef.current) {
        fitAddonRef.current.fit();
        const { cols, rows } = xtermRef.current;
        invoke('resize_pty', { cols, rows }).catch(console.error);
      }
    };

    window.addEventListener('resize', handleResize);

    // Handle input - use a wrapper that calls the ref so it always uses the latest handler
    xterm.onData((data) => {
      inputHandlerRef.current(data);
    });

    // Update cursor position for ghost text
    xterm.onCursorMove(() => {
      updateCursorPosition();
    });

    return () => {
      isMountedRef.current = false;
      window.removeEventListener('resize', handleResize);
      if (readIntervalRef.current) {
        clearInterval(readIntervalRef.current);
      }
      xterm.dispose();
    };
  }, []);

  const spawnShell = async () => {
    try {
      console.log('Spawning shell...');
      await invoke('spawn_shell');
      console.log('Shell spawned, starting read loop...');
      
      // Start reading from PTY immediately
      console.log('Starting read interval...');
      readIntervalRef.current = window.setInterval(async () => {
        try {
          const output = await invoke<string>('read_from_pty');
          if (output) {
            console.log('PTY output received:', output.length, 'bytes, content:', output.substring(0, 50));
            if (xtermRef.current) {
              xtermRef.current.write(output);
              console.log('Written to xterm');
            } else {
              console.error('xtermRef.current is null!');
            }
            
            // Mark as connected once we get first output (shell prompt)
            if (!isConnectedRef.current) {
              console.log('First output received, marking as connected');
              isConnectedRef.current = true;
              setIsConnected(true);
            }
            
            // Try to detect command completion (prompt returned)
            if (output.includes('\n') || output.includes('\r')) {
              // Command might have been executed, clear input buffer
              inputBufferRef.current = '';
              setCurrentInput('');
              clearSuggestion();
            }
          }
        } catch (err) {
          console.error('Read error:', err);
        }
      }, 50);

      // Initial resize
      if (fitAddonRef.current && xtermRef.current) {
        fitAddonRef.current.fit();
        const { cols, rows } = xtermRef.current;
        console.log('Resizing PTY to', cols, 'x', rows);
        await invoke('resize_pty', { cols, rows });
      }
      
      // Set connected after a short delay if we haven't received output yet
      // This allows typing even if shell prompt is slow
      setTimeout(() => {
        if (!isConnectedRef.current) {
          console.log('Timeout: marking as connected anyway');
          isConnectedRef.current = true;
          setIsConnected(true);
        }
      }, 2000);
      
    } catch (err) {
      console.error('Failed to spawn shell:', err);
      isConnectedRef.current = false;
      setIsConnected(false);
      // Show error in terminal
      if (xtermRef.current) {
        xtermRef.current.write(`\r\n\x1b[31mError: Failed to spawn shell: ${err}\x1b[0m\r\n`);
      }
    }
  };

  // Input handler - defined inline and kept in ref so xterm.onData always uses the latest version
  const handleTerminalInput = useCallback(async (data: string) => {
    console.log('Input received:', data.length, 'chars, code:', data.charCodeAt(0));

    // Check for special keys
    const code = data.charCodeAt(0);
    
    // Tab key - accept suggestion
    if (code === 9 && suggestion) {
      // Insert the suggestion
      await invoke('write_to_pty', { data: suggestion });
      inputBufferRef.current += suggestion;
      setCurrentInput(inputBufferRef.current);
      clearSuggestion();
      return;
    }
    
    // Right arrow - accept suggestion (when at end of line)
    if (data === '\x1b[C' && suggestion) {
      await invoke('write_to_pty', { data: suggestion });
      inputBufferRef.current += suggestion;
      setCurrentInput(inputBufferRef.current);
      clearSuggestion();
      return;
    }
    
    // Escape - clear suggestion
    if (code === 27 && suggestion) {
      clearSuggestion();
    }
    
    // Enter key - execute command
    if (code === 13) {
      // Add to history
      if (inputBufferRef.current.trim()) {
        await invoke('add_to_history', { command: inputBufferRef.current.trim() });
      }
      inputBufferRef.current = '';
      setCurrentInput('');
      clearSuggestion();
    }
    // Backspace
    else if (code === 127 || code === 8) {
      inputBufferRef.current = inputBufferRef.current.slice(0, -1);
      setCurrentInput(inputBufferRef.current);
    }
    // Ctrl+C
    else if (code === 3) {
      inputBufferRef.current = '';
      setCurrentInput('');
      clearSuggestion();
    }
    // Ctrl+U - clear line
    else if (code === 21) {
      inputBufferRef.current = '';
      setCurrentInput('');
      clearSuggestion();
    }
    // Regular printable character
    else if (code >= 32 && code < 127) {
      inputBufferRef.current += data;
      setCurrentInput(inputBufferRef.current);
    }

    // Send to PTY
    try {
      console.log('Sending to PTY:', JSON.stringify(data));
      await invoke('write_to_pty', { data });
    } catch (err) {
      console.error('Write error:', err);
    }
  }, [suggestion, clearSuggestion]);

  // Keep the ref updated with the latest handler
  useEffect(() => {
    inputHandlerRef.current = handleTerminalInput;
  }, [handleTerminalInput]);

  const updateCursorPosition = useCallback(() => {
    if (!xtermRef.current || !terminalRef.current) return;
    
    const term = xtermRef.current;
    const container = terminalRef.current;
    const cellWidth = term.options.fontSize! * 0.6; // Approximate
    const cellHeight = term.options.fontSize! * term.options.lineHeight!;
    
    // Get cursor position in terminal grid
    const cursorX = term.buffer.active.cursorX;
    const cursorY = term.buffer.active.cursorY;
    
    // Calculate pixel position
    const rect = container.getBoundingClientRect();
    const x = rect.left + (cursorX * cellWidth) + 8; // 8px padding
    const y = rect.top + (cursorY * cellHeight) + 8;
    
    setCursorPosition({ x, y });
  }, []);

  return (
    <div className={`terminal-container ${className || ''}`}>
      <div 
        ref={terminalRef} 
        className="terminal-wrapper"
      />
      
      {suggestion && !isLoading && (
        <GhostText 
          text={suggestion}
          position={cursorPosition}
          fontSize={xtermRef.current?.options.fontSize || 14}
        />
      )}
      
      <div className="status-bar">
        <div className="status-item">
          <span className={`status-dot ${isConnected ? 'connected' : 'disconnected'}`} />
          <span>{isConnected ? 'Connected' : 'Disconnected'}</span>
        </div>
        {isLoading && (
          <div className="status-item">
            <span className="status-dot loading" />
            <span>Getting suggestion...</span>
          </div>
        )}
        {currentInput && (
          <div className="status-item">
            <span style={{ color: '#808080' }}>Input: {currentInput.slice(0, 30)}{currentInput.length > 30 ? '...' : ''}</span>
          </div>
        )}
      </div>
    </div>
  );
}
