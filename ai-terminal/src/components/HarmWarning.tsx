import { memo } from 'react';

interface HarmResult {
  is_harmful: boolean;
  reason: string;
  severity: string;
}

interface HarmWarningProps {
  command: string;
  harmResult: HarmResult;
  onProceed: () => void;
  onCancel: () => void;
}

function HarmWarning({ command, harmResult, onProceed, onCancel }: HarmWarningProps) {
  const getSeverityColor = (severity: string): string => {
    switch (severity.toLowerCase()) {
      case 'critical':
        return '#ff4444';
      case 'high':
        return '#ff8800';
      case 'medium':
        return '#ffcc00';
      case 'low':
        return '#88cc00';
      default:
        return '#ffcc00';
    }
  };

  const getSeverityIcon = (severity: string): string => {
    switch (severity.toLowerCase()) {
      case 'critical':
        return '⛔';
      case 'high':
        return '🚨';
      case 'medium':
        return '⚠️';
      case 'low':
        return '⚡';
      default:
        return '⚠️';
    }
  };

  return (
    <div className="modal-overlay">
      <div className="modal harm-warning-modal">
        <div className="modal-header" style={{ borderColor: getSeverityColor(harmResult.severity) }}>
          <span className="modal-icon">{getSeverityIcon(harmResult.severity)}</span>
          <h2>Potentially Harmful Command Detected</h2>
        </div>

        <div className="modal-content">
          <div className="severity-badge" style={{ backgroundColor: getSeverityColor(harmResult.severity) }}>
            {harmResult.severity.toUpperCase()} RISK
          </div>

          <div className="command-preview">
            <label>Command:</label>
            <code>{command}</code>
          </div>

          <div className="harm-reason">
            <label>Warning:</label>
            <p>{harmResult.reason}</p>
          </div>

          <div className="warning-text">
            <p>This command has been flagged as potentially dangerous. Proceeding may cause:</p>
            <ul>
              <li>Data loss or corruption</li>
              <li>System instability</li>
              <li>Security vulnerabilities</li>
            </ul>
          </div>
        </div>

        <div className="modal-actions">
          <button className="btn btn-danger" onClick={onProceed}>
            Proceed Anyway
          </button>
          <button className="btn btn-primary" onClick={onCancel} autoFocus>
            Cancel
          </button>
        </div>
      </div>
    </div>
  );
}

export default memo(HarmWarning);
