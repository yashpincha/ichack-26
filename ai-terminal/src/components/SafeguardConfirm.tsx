import { memo, useState } from 'react';

interface SafeguardResult {
  is_dangerous: boolean;
  matched_pattern: string | null;
  description: string;
  severity: string;
}

interface SafeguardConfirmProps {
  command: string;
  safeguardResult: SafeguardResult;
  onProceed: () => void;
  onCancel: () => void;
  onDisableForSession?: () => void;
}

function SafeguardConfirm({ 
  command, 
  safeguardResult, 
  onProceed, 
  onCancel,
  onDisableForSession 
}: SafeguardConfirmProps) {
  const [dontAskAgain, setDontAskAgain] = useState(false);

  const getSeverityColor = (severity: string): string => {
    switch (severity.toLowerCase()) {
      case 'critical':
        return '#dc2626';
      case 'high':
        return '#ea580c';
      case 'medium':
        return '#ca8a04';
      case 'low':
        return '#65a30d';
      default:
        return '#ca8a04';
    }
  };

  const handleProceed = () => {
    if (dontAskAgain && onDisableForSession) {
      onDisableForSession();
    }
    onProceed();
  };

  return (
    <div className="modal-overlay">
      <div className="modal safeguard-modal">
        <div className="modal-header" style={{ borderColor: getSeverityColor(safeguardResult.severity) }}>
          <span className="modal-icon">🛡️</span>
          <h2>Command Safeguard</h2>
        </div>

        <div className="modal-content">
          <div className="severity-badge" style={{ backgroundColor: getSeverityColor(safeguardResult.severity) }}>
            {safeguardResult.severity.toUpperCase()} RISK
          </div>

          <div className="command-preview">
            <label>Command:</label>
            <code>{command}</code>
          </div>

          {safeguardResult.matched_pattern && (
            <div className="pattern-match">
              <label>Matched Pattern:</label>
              <code>{safeguardResult.matched_pattern}</code>
            </div>
          )}

          <div className="safeguard-description">
            <label>Risk:</label>
            <p>{safeguardResult.description}</p>
          </div>

          <div className="safeguard-warning">
            <p>This command has been flagged by the pattern-based safeguard system. 
               Are you sure you want to proceed?</p>
          </div>

          {onDisableForSession && (
            <div className="dont-ask-checkbox">
              <label>
                <input 
                  type="checkbox" 
                  checked={dontAskAgain}
                  onChange={(e) => setDontAskAgain(e.target.checked)}
                />
                Don't ask again this session
              </label>
            </div>
          )}
        </div>

        <div className="modal-actions">
          <button className="btn btn-danger" onClick={handleProceed}>
            I Understand, Proceed
          </button>
          <button className="btn btn-primary" onClick={onCancel} autoFocus>
            Cancel
          </button>
        </div>
      </div>
    </div>
  );
}

export default memo(SafeguardConfirm);
