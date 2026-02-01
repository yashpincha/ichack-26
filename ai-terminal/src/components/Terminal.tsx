import { useEffect, useRef, useState, useCallback } from 'react';
import { Terminal as XTerm } from 'xterm';
import { FitAddon } from 'xterm-addon-fit';
import { WebLinksAddon } from 'xterm-addon-web-links';
import { invoke } from '@tauri-apps/api/core';
import GhostText from './GhostText';
import HarmWarning from './HarmWarning';
import SafeguardConfirm from './SafeguardConfirm';
import FixSuggestion from './FixSuggestion';
import { useAutocomplete } from '../hooks/useAutocomplete';
import 'xterm/css/xterm.css';

interface HarmResult {
  is_harmful: boolean;
  reason: string;
  severity: string;
}

interface SafeguardResult {
  is_dangerous: boolean;
  matched_pattern: string | null;
  description: string;
  severity: string;
}

interface FixSuggestionData {
  fixed_command: string;
  explanation: string;
  confidence: string;
}

interface ErrorContext {
  command: string;
  exit_code: number;
  output: string;
  cwd: string;
  history: string[];
}

interface TerminalProps {
  className?: string;
}

export default function Terminal({ className }: TerminalProps) {
  const terminalRef = useRef<HTMLDivElement>(null);
  const xtermRef = useRef<XTerm | null>(null);
  const fitAddonRef = useRef<FitAddon | null>(null);
  const isMountedRef = useRef(true);
  const [isConnected, setIsConnected] = useState(false);
  const isConnectedRef = useRef(false);
  const [currentInput, setCurrentInput] = useState('');
  const [cursorPosition, setCursorPosition] = useState({ x: 0, y: 0 });
  const inputBufferRef = useRef('');
  const readIntervalRef = useRef<number | null>(null);
  const { suggestion, explanation, isLoading, clearSuggestion } = useAutocomplete(currentInput);
  
  // New state for safety features
  const [showHarmWarning, setShowHarmWarning] = useState(false);
  const [harmResult, setHarmResult] = useState<HarmResult | null>(null);
  const [pendingCommand, setPendingCommand] = useState<string | null>(null);
  
  const [showSafeguardConfirm, setShowSafeguardConfirm] = useState(false);
  const [safeguardResult, setSafeguardResult] = useState<SafeguardResult | null>(null);
  const safeguardsDisabledForSession = useRef(false);
  
  const [showFixSuggestion, setShowFixSuggestion] = useState(false);
  const [fixSuggestion, setFixSuggestion] = useState<FixSuggestionData | null>(null);
  const [lastErrorContext, setLastErrorContext] = useState<ErrorContext | null>(null);
  const [isLoadingFix, setIsLoadingFix] = useState(false);
  
  // Track last command for error detection
  const lastExecutedCommand = useRef<string>('');
  const outputBuffer = useRef<string>('');
  
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
            
            // Capture output for error detection
            if (lastExecutedCommand.current) {
              outputBuffer.current += output;
              // Keep buffer limited
              if (outputBuffer.current.length > 10000) {
                outputBuffer.current = outputBuffer.current.slice(-10000);
              }
            }
            
            // Mark as connected once we get first output (shell prompt)
            if (!isConnectedRef.current) {
              console.log('First output received, marking as connected');
              isConnectedRef.current = true;
              setIsConnected(true);
            }
            
            // Try to detect command completion (prompt returned)
            // Look for common prompt patterns that indicate command finished
            const promptPatterns = [/\$\s*$/, />\s*$/, /#\s*$/, /PS.*>\s*$/];
            const hasPrompt = promptPatterns.some(pattern => pattern.test(output));
            
            if (hasPrompt && lastExecutedCommand.current) {
              // Check for error indicators in output
              const errorIndicators = ['error', 'Error', 'ERROR', 'failed', 'Failed', 'not found', 'No such file', 'Permission denied', 'command not found'];
              const hasError = errorIndicators.some(indicator => outputBuffer.current.includes(indicator));
              
              if (hasError) {
                // Store error context for FEP
                setLastErrorContext({
                  command: lastExecutedCommand.current,
                  exit_code: 1, // Assumed - we can't easily get real exit code in this flow
                  output: outputBuffer.current,
                  cwd: '',
                  history: [],
                });
              } else {
                setLastErrorContext(null);
              }
              
              // Reset tracking
              lastExecutedCommand.current = '';
              outputBuffer.current = '';
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

  // Check command safety before execution
  const checkCommandSafety = async (command: string): Promise<boolean> => {
    // Check pattern-based safeguard first (fast, local)
    if (!safeguardsDisabledForSession.current) {
      try {
        const safeguard = await invoke<SafeguardResult>('check_safeguard', { command });
        if (safeguard.is_dangerous) {
          setPendingCommand(command);
          setSafeguardResult(safeguard);
          setShowSafeguardConfirm(true);
          return false;
        }
      } catch (err) {
        console.error('Safeguard check failed:', err);
      }
    }
    
    // Check LLM-based harm detection (slower, more intelligent)
    try {
      const harm = await invoke<HarmResult>('check_command_harm', { command });
      if (harm.is_harmful) {
        setPendingCommand(command);
        setHarmResult(harm);
        setShowHarmWarning(true);
        return false;
      }
    } catch (err) {
      console.error('Harm check failed:', err);
      // Fail safe - allow execution if check fails
    }
    
    return true;
  };

  // Execute the pending command after user confirmation
  const executePendingCommand = async () => {
    if (pendingCommand) {
      lastExecutedCommand.current = pendingCommand;
      await invoke('add_to_history', { command: pendingCommand });
      await invoke('write_to_pty', { data: '\r' });
    }
    setPendingCommand(null);
    setShowHarmWarning(false);
    setShowSafeguardConfirm(false);
    setHarmResult(null);
    setSafeguardResult(null);
    inputBufferRef.current = '';
    setCurrentInput('');
    clearSuggestion();
  };

  // Cancel the pending command
  const cancelPendingCommand = () => {
    setPendingCommand(null);
    setShowHarmWarning(false);
    setShowSafeguardConfirm(false);
    setHarmResult(null);
    setSafeguardResult(null);
    // Clear the input line in terminal
    if (xtermRef.current) {
      xtermRef.current.write('\x1b[2K\r'); // Clear line
    }
    inputBufferRef.current = '';
    setCurrentInput('');
    clearSuggestion();
  };

  // Handle FEP (Fix Error Please)
  const handleFixError = async () => {
    if (!lastErrorContext) return;
    
    setIsLoadingFix(true);
    setShowFixSuggestion(true);
    
    try {
      const fix = await invoke<FixSuggestionData>('get_error_fix', {
        command: lastErrorContext.command,
        exitCode: lastErrorContext.exit_code,
        output: lastErrorContext.output,
      });
      setFixSuggestion(fix);
    } catch (err) {
      console.error('Failed to get fix:', err);
      setFixSuggestion({
        fixed_command: '',
        explanation: 'Failed to analyze the error. Please try again.',
        confidence: 'low',
      });
    } finally {
      setIsLoadingFix(false);
    }
  };

  // Apply the suggested fix
  const applyFix = async (fixedCommand: string) => {
    setShowFixSuggestion(false);
    setFixSuggestion(null);
    
    if (fixedCommand && xtermRef.current) {
      // Type the fixed command
      inputBufferRef.current = fixedCommand;
      setCurrentInput(fixedCommand);
      await invoke('write_to_pty', { data: fixedCommand });
    }
  };

  // Input handler - defined inline and kept in ref so xterm.onData always uses the latest version
  const handleTerminalInput = useCallback(async (data: string) => {
    console.log('Input received:', data.length, 'chars, code:', data.charCodeAt(0));

    // Check for special keys
    const code = data.charCodeAt(0);
    
    // Ctrl+F - Fix error (FEP)
    if (code === 6) {
      if (lastErrorContext) {
        handleFixError();
      }
      return;
    }
    
    // Tab key - accept suggestion
    if (code === 9 && suggestion) {
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
    
    // Escape - clear suggestion or dismiss modals
    if (code === 27) {
      if (suggestion) {
        clearSuggestion();
      }
      if (showFixSuggestion) {
        setShowFixSuggestion(false);
        setFixSuggestion(null);
      }
      return;
    }
    
    // Enter key - execute command with safety checks
    if (code === 13) {
      const command = inputBufferRef.current.trim();
      if (command) {
        // Store command for potential FEP
        lastExecutedCommand.current = command;
        outputBuffer.current = '';
        
        // Check safety before execution
        const isSafe = await checkCommandSafety(command);
        if (!isSafe) {
          // Command blocked - don't send Enter to PTY
          return;
        }
        
        await invoke('add_to_history', { command });
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
      lastExecutedCommand.current = '';
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
  }, [suggestion, clearSuggestion, showFixSuggestion, lastErrorContext]);

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
          explanation={explanation}
          position={cursorPosition}
          fontSize={xtermRef.current?.options.fontSize || 14}
        />
      )}
      
      {/* Harm Warning Modal */}
      {showHarmWarning && harmResult && pendingCommand && (
        <HarmWarning
          command={pendingCommand}
          harmResult={harmResult}
          onProceed={executePendingCommand}
          onCancel={cancelPendingCommand}
        />
      )}
      
      {/* Safeguard Confirmation Modal */}
      {showSafeguardConfirm && safeguardResult && pendingCommand && (
        <SafeguardConfirm
          command={pendingCommand}
          safeguardResult={safeguardResult}
          onProceed={executePendingCommand}
          onCancel={cancelPendingCommand}
          onDisableForSession={() => { safeguardsDisabledForSession.current = true; }}
        />
      )}
      
      {/* Fix Suggestion Modal */}
      {showFixSuggestion && lastErrorContext && (
        <FixSuggestion
          errorContext={lastErrorContext}
          suggestion={fixSuggestion || { fixed_command: '', explanation: '', confidence: 'low' }}
          onApply={applyFix}
          onDismiss={() => { setShowFixSuggestion(false); setFixSuggestion(null); }}
          isLoading={isLoadingFix}
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
        {lastErrorContext && (
          <div className="status-item error-hint" onClick={handleFixError}>
            <span className="status-dot error" />
            <span>Error detected - Press Ctrl+F to fix</span>
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
