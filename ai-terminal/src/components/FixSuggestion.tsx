import { memo } from 'react';

interface FixSuggestionData {
  fixed_command: string;
  explanation: string;
  confidence: string;
}

interface ErrorContext {
  command: string;
  exit_code: number;
  output: string;
}

interface FixSuggestionProps {
  errorContext: ErrorContext;
  suggestion: FixSuggestionData;
  onApply: (fixedCommand: string) => void;
  onDismiss: () => void;
  isLoading?: boolean;
}

function FixSuggestion({ errorContext, suggestion, onApply, onDismiss, isLoading }: FixSuggestionProps) {
  const getConfidenceColor = (confidence: string): string => {
    switch (confidence.toLowerCase()) {
      case 'high':
        return '#22c55e';
      case 'medium':
        return '#eab308';
      case 'low':
        return '#ef4444';
      default:
        return '#6b7280';
    }
  };

  const getConfidenceIcon = (confidence: string): string => {
    switch (confidence.toLowerCase()) {
      case 'high':
        return '✓';
      case 'medium':
        return '~';
      case 'low':
        return '?';
      default:
        return '?';
    }
  };

  if (isLoading) {
    return (
      <div className="modal-overlay">
        <div className="modal fix-suggestion-modal">
          <div className="modal-header">
            <span className="modal-icon">🔧</span>
            <h2>Analyzing Error...</h2>
          </div>
          <div className="modal-content">
            <div className="loading-spinner">
              <div className="spinner"></div>
              <p>Looking for a fix...</p>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="modal-overlay">
      <div className="modal fix-suggestion-modal">
        <div className="modal-header">
          <span className="modal-icon">🔧</span>
          <h2>Fix Error Please (FEP)</h2>
        </div>

        <div className="modal-content">
          <div className="error-section">
            <label>Failed Command:</label>
            <code className="error-command">{errorContext.command}</code>
            <div className="exit-code">Exit code: {errorContext.exit_code}</div>
          </div>

          {errorContext.output && (
            <div className="error-output-section">
              <label>Error Output:</label>
              <pre className="error-output">
                {errorContext.output.length > 500 
                  ? errorContext.output.slice(0, 500) + '...' 
                  : errorContext.output}
              </pre>
            </div>
          )}

          <div className="divider"></div>

          <div className="fix-section">
            <div className="fix-header">
              <label>Suggested Fix:</label>
              <span 
                className="confidence-badge" 
                style={{ backgroundColor: getConfidenceColor(suggestion.confidence) }}
              >
                {getConfidenceIcon(suggestion.confidence)} {suggestion.confidence.toUpperCase()}
              </span>
            </div>
            <code className="fixed-command">{suggestion.fixed_command}</code>
          </div>

          <div className="explanation-section">
            <label>Explanation:</label>
            <p>{suggestion.explanation}</p>
          </div>
        </div>

        <div className="modal-actions">
          <button 
            className="btn btn-primary" 
            onClick={() => onApply(suggestion.fixed_command)}
            disabled={!suggestion.fixed_command}
          >
            Apply Fix
          </button>
          <button className="btn btn-secondary" onClick={onDismiss}>
            Dismiss
          </button>
        </div>

        <div className="modal-hint">
          <span>Tip: Press <kbd>Ctrl+F</kbd> after a command fails to get a fix suggestion</span>
        </div>
      </div>
    </div>
  );
}

export default memo(FixSuggestion);
