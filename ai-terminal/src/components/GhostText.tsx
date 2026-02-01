import { memo, useState } from 'react';

interface GhostTextProps {
  text: string;
  explanation?: string | null;
  position: { x: number; y: number };
  fontSize: number;
}

/**
 * GhostText component displays the autocomplete suggestion
 * as semi-transparent text that appears after the cursor.
 * Includes an optional explanation tooltip on hover.
 */
function GhostText({ text, explanation, position, fontSize }: GhostTextProps) {
  const [showTooltip, setShowTooltip] = useState(false);

  if (!text) return null;

  const style: React.CSSProperties = {
    position: 'fixed',
    left: `${position.x}px`,
    top: `${position.y}px`,
    fontSize: `${fontSize}px`,
    fontFamily: "'Consolas', 'Monaco', 'Courier New', monospace",
    color: 'rgba(150, 150, 150, 0.6)',
    fontStyle: 'italic',
    pointerEvents: explanation ? 'auto' : 'none',
    whiteSpace: 'pre',
    zIndex: 100,
    lineHeight: 1.2,
    textShadow: '0 0 1px rgba(0, 0, 0, 0.3)',
    cursor: explanation ? 'help' : 'default',
  };

  const tooltipStyle: React.CSSProperties = {
    position: 'absolute',
    left: '0',
    top: `${fontSize * 1.5}px`,
    backgroundColor: 'rgba(30, 30, 30, 0.95)',
    color: '#e0e0e0',
    padding: '6px 10px',
    borderRadius: '4px',
    fontSize: '12px',
    fontStyle: 'normal',
    whiteSpace: 'nowrap',
    maxWidth: '300px',
    overflow: 'hidden',
    textOverflow: 'ellipsis',
    boxShadow: '0 2px 8px rgba(0, 0, 0, 0.3)',
    border: '1px solid rgba(100, 100, 100, 0.3)',
    zIndex: 101,
  };

  const infoIconStyle: React.CSSProperties = {
    display: 'inline-block',
    marginLeft: '4px',
    fontSize: `${fontSize * 0.7}px`,
    color: 'rgba(100, 150, 255, 0.6)',
    verticalAlign: 'super',
  };

  return (
    <div 
      className="ghost-text-overlay" 
      style={style}
      onMouseEnter={() => explanation && setShowTooltip(true)}
      onMouseLeave={() => setShowTooltip(false)}
    >
      {text}
      {explanation && (
        <span style={infoIconStyle}>ⓘ</span>
      )}
      {showTooltip && explanation && (
        <div style={tooltipStyle}>
          {explanation}
        </div>
      )}
    </div>
  );
}

// Memoize to prevent unnecessary re-renders
export default memo(GhostText);
