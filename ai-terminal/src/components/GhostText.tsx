import { memo } from 'react';

interface GhostTextProps {
  text: string;
  position: { x: number; y: number };
  fontSize: number;
}

/**
 * GhostText component displays the autocomplete suggestion
 * as semi-transparent text that appears after the cursor.
 */
function GhostText({ text, position, fontSize }: GhostTextProps) {
  if (!text) return null;

  const style: React.CSSProperties = {
    position: 'fixed',
    left: `${position.x}px`,
    top: `${position.y}px`,
    fontSize: `${fontSize}px`,
    fontFamily: "'Consolas', 'Monaco', 'Courier New', monospace",
    color: 'rgba(150, 150, 150, 0.6)',
    fontStyle: 'italic',
    pointerEvents: 'none',
    whiteSpace: 'pre',
    zIndex: 100,
    lineHeight: 1.2,
    // Add a subtle text shadow for better visibility
    textShadow: '0 0 1px rgba(0, 0, 0, 0.3)',
  };

  return (
    <div className="ghost-text-overlay" style={style}>
      {text}
    </div>
  );
}

// Memoize to prevent unnecessary re-renders
export default memo(GhostText);
