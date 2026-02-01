import { useState, useCallback } from 'react';
import Terminal from './components/Terminal';
import Settings from './components/Settings';
import './styles/global.css';

function App() {
  const [showSettings, setShowSettings] = useState(false);

  const toggleSettings = useCallback(() => {
    setShowSettings(prev => !prev);
  }, []);

  return (
    <div className="app-container">
      <header className="app-header">
        <div className="header-title">
          <span className="header-icon">⚡</span>
          <span>AI Terminal</span>
        </div>
        <div className="header-actions">
          <button 
            className="settings-button"
            onClick={toggleSettings}
            title="Settings"
          >
            ⚙️
          </button>
        </div>
      </header>
      
      <main className="app-main">
        <Terminal />
      </main>
      
      {showSettings && (
        <Settings onClose={() => setShowSettings(false)} />
      )}
    </div>
  );
}

export default App;
