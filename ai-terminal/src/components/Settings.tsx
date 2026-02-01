import { useState, useEffect } from 'react';
import { invoke } from '@tauri-apps/api/core';
import UsageStats from './UsageStats';

interface AppConfig {
  provider: string;
  model: string;
  api_key: string;
  endpoint: string | null;
  debounce_ms: number;
  ghost_text_enabled: boolean;
  temperature: number;
  max_suggestions: number;
  max_history_commands: number;
  safeguards_enabled: boolean;
  harm_detection_enabled: boolean;
  show_explanations: boolean;
}

interface SettingsProps {
  onClose: () => void;
}

const PROVIDERS = [
  { value: 'openai', label: 'OpenAI', keyName: 'OPENAI_API_KEY' },
  { value: 'anthropic', label: 'Anthropic', keyName: 'ANTHROPIC_API_KEY' },
  { value: 'groq', label: 'Groq', keyName: 'GROQ_API_KEY' },
  { value: 'ollama', label: 'Ollama (Local)', keyName: null },
];

const MODELS: Record<string, { value: string; label: string }[]> = {
  openai: [
    { value: 'gpt-4o', label: 'GPT-4o' },
    { value: 'gpt-4o-mini', label: 'GPT-4o Mini (Recommended)' },
    { value: 'o1-mini', label: 'O1 Mini' },
  ],
  anthropic: [
    { value: 'claude-3-5-sonnet-20241022', label: 'Claude 3.5 Sonnet' },
    { value: 'claude-3-5-haiku-20241022', label: 'Claude 3.5 Haiku (Fast)' },
  ],
  groq: [
    { value: 'llama3-70b-8192', label: 'Llama 3 70B' },
    { value: 'llama3-8b-8192', label: 'Llama 3 8B (Fast)' },
    { value: 'mixtral-8x7b-32768', label: 'Mixtral 8x7B' },
  ],
  ollama: [
    { value: 'codellama', label: 'CodeLlama' },
    { value: 'llama2', label: 'Llama 2' },
    { value: 'mistral', label: 'Mistral' },
  ],
};

export default function Settings({ onClose }: SettingsProps) {
  const [config, setConfig] = useState<AppConfig>({
    provider: 'openai',
    model: 'gpt-4o-mini',
    api_key: '',
    endpoint: null,
    debounce_ms: 300,
    ghost_text_enabled: true,
    temperature: 0.0,
    max_suggestions: 1,
    max_history_commands: 20,
    safeguards_enabled: true,
    harm_detection_enabled: true,
    show_explanations: true,
  });
  const [isSaving, setIsSaving] = useState(false);
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);
  const [activeTab, setActiveTab] = useState<'general' | 'safety' | 'usage'>('general');

  useEffect(() => {
    loadConfig();
  }, []);

  const loadConfig = async () => {
    try {
      const savedConfig = await invoke<AppConfig>('get_config');
      setConfig(savedConfig);
    } catch (err) {
      console.error('Failed to load config:', err);
      setMessage({ type: 'error', text: 'Failed to load settings' });
    }
  };

  const handleSave = async () => {
    setIsSaving(true);
    setMessage(null);

    try {
      await invoke('set_config', { newConfig: config });
      setMessage({ type: 'success', text: 'Settings saved successfully!' });
      setTimeout(() => {
        onClose();
      }, 1000);
    } catch (err) {
      console.error('Failed to save config:', err);
      setMessage({ type: 'error', text: `Failed to save: ${err}` });
    } finally {
      setIsSaving(false);
    }
  };

  const handleProviderChange = (provider: string) => {
    const models = MODELS[provider] || [];
    const defaultModel = models[0]?.value || '';
    
    setConfig(prev => ({
      ...prev,
      provider,
      model: defaultModel,
      // Clear endpoint for non-Ollama providers
      endpoint: provider === 'ollama' ? 'http://localhost:11434/api/chat' : null,
    }));
  };

  const currentProvider = PROVIDERS.find(p => p.value === config.provider);
  const availableModels = MODELS[config.provider] || [];

  return (
    <div className="settings-overlay" onClick={(e) => e.target === e.currentTarget && onClose()}>
      <div className="settings-modal">
        <div className="settings-header">
          <h2>Settings</h2>
          <button className="close-button" onClick={onClose}>&times;</button>
        </div>

        {/* Tabs */}
        <div className="settings-tabs">
          <button 
            className={`tab ${activeTab === 'general' ? 'active' : ''}`}
            onClick={() => setActiveTab('general')}
          >
            General
          </button>
          <button 
            className={`tab ${activeTab === 'safety' ? 'active' : ''}`}
            onClick={() => setActiveTab('safety')}
          >
            Safety
          </button>
          <button 
            className={`tab ${activeTab === 'usage' ? 'active' : ''}`}
            onClick={() => setActiveTab('usage')}
          >
            Usage
          </button>
        </div>

        <div className="settings-content">
          {/* General Tab */}
          {activeTab === 'general' && (
            <>
              {/* Provider Selection */}
              <div className="setting-group">
                <label className="setting-label">AI Provider</label>
                <select
                  className="setting-select"
                  value={config.provider}
                  onChange={(e) => handleProviderChange(e.target.value)}
                >
                  {PROVIDERS.map(provider => (
                    <option key={provider.value} value={provider.value}>
                      {provider.label}
                    </option>
                  ))}
                </select>
              </div>

              {/* Model Selection */}
              <div className="setting-group">
                <label className="setting-label">Model</label>
                <select
                  className="setting-select"
                  value={config.model}
                  onChange={(e) => setConfig(prev => ({ ...prev, model: e.target.value }))}
                >
                  {availableModels.map(model => (
                    <option key={model.value} value={model.value}>
                      {model.label}
                    </option>
                  ))}
                </select>
              </div>

              {/* API Key (not for Ollama) */}
              {config.provider !== 'ollama' && (
                <div className="setting-group">
                  <label className="setting-label">API Key</label>
                  <p className="setting-description">
                    {currentProvider?.keyName ? `Your ${currentProvider.label} API key` : 'API key for the selected provider'}
                  </p>
                  <input
                    type="password"
                    className="setting-input"
                    value={config.api_key}
                    onChange={(e) => setConfig(prev => ({ ...prev, api_key: e.target.value }))}
                    placeholder="sk-..."
                  />
                </div>
              )}

              {/* Custom Endpoint (for Ollama) */}
              {config.provider === 'ollama' && (
                <div className="setting-group">
                  <label className="setting-label">Ollama Endpoint</label>
                  <p className="setting-description">
                    URL of your local Ollama server
                  </p>
                  <input
                    type="text"
                    className="setting-input"
                    value={config.endpoint || ''}
                    onChange={(e) => setConfig(prev => ({ ...prev, endpoint: e.target.value }))}
                    placeholder="http://localhost:11434/api/chat"
                  />
                </div>
              )}

              {/* Ghost Text Toggle */}
              <div className="setting-group">
                <label className="setting-checkbox">
                  <input
                    type="checkbox"
                    checked={config.ghost_text_enabled}
                    onChange={(e) => setConfig(prev => ({ ...prev, ghost_text_enabled: e.target.checked }))}
                  />
                  <span>Enable Ghost Text Autocomplete</span>
                </label>
              </div>

              {/* Show Explanations Toggle */}
              <div className="setting-group">
                <label className="setting-checkbox">
                  <input
                    type="checkbox"
                    checked={config.show_explanations}
                    onChange={(e) => setConfig(prev => ({ ...prev, show_explanations: e.target.checked }))}
                  />
                  <span>Show Explanations for Suggestions</span>
                </label>
                <p className="setting-description">
                  Display a brief explanation of why each suggestion was made
                </p>
              </div>

              {/* Debounce Time */}
              <div className="setting-group">
                <label className="setting-label">Debounce Time (ms)</label>
                <p className="setting-description">
                  How long to wait after typing before fetching suggestions
                </p>
                <input
                  type="number"
                  className="setting-input"
                  value={config.debounce_ms}
                  onChange={(e) => setConfig(prev => ({ ...prev, debounce_ms: parseInt(e.target.value) || 300 }))}
                  min={100}
                  max={2000}
                  step={50}
                />
              </div>

              {/* Temperature */}
              <div className="setting-group">
                <label className="setting-label">Temperature: {config.temperature.toFixed(1)}</label>
                <p className="setting-description">
                  Lower = more deterministic, Higher = more creative
                </p>
                <input
                  type="range"
                  className="setting-input"
                  value={config.temperature}
                  onChange={(e) => setConfig(prev => ({ ...prev, temperature: parseFloat(e.target.value) }))}
                  min={0}
                  max={1}
                  step={0.1}
                  style={{ cursor: 'pointer' }}
                />
              </div>
            </>
          )}

          {/* Safety Tab */}
          {activeTab === 'safety' && (
            <>
              <div className="setting-group">
                <h3 className="setting-section-title">Command Safety Features</h3>
                <p className="setting-description">
                  These features help protect you from accidentally running dangerous commands.
                </p>
              </div>

              {/* Safeguards Toggle */}
              <div className="setting-group">
                <label className="setting-checkbox">
                  <input
                    type="checkbox"
                    checked={config.safeguards_enabled}
                    onChange={(e) => setConfig(prev => ({ ...prev, safeguards_enabled: e.target.checked }))}
                  />
                  <span>Enable Pattern-Based Safeguards</span>
                </label>
                <p className="setting-description">
                  Show confirmation prompts for commands matching dangerous patterns (rm -rf, chmod 777, etc.)
                </p>
              </div>

              {/* Harm Detection Toggle */}
              <div className="setting-group">
                <label className="setting-checkbox">
                  <input
                    type="checkbox"
                    checked={config.harm_detection_enabled}
                    onChange={(e) => setConfig(prev => ({ ...prev, harm_detection_enabled: e.target.checked }))}
                  />
                  <span>Enable AI-Based Harm Detection</span>
                </label>
                <p className="setting-description">
                  Use AI to analyze commands for potential risks before execution. This provides more intelligent detection but requires API calls.
                </p>
              </div>

              <div className="setting-group info-box">
                <h4>Safety Feature Comparison</h4>
                <table className="feature-comparison">
                  <thead>
                    <tr>
                      <th>Feature</th>
                      <th>Speed</th>
                      <th>Intelligence</th>
                      <th>API Cost</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr>
                      <td>Pattern Safeguards</td>
                      <td>Instant</td>
                      <td>Basic</td>
                      <td>None</td>
                    </tr>
                    <tr>
                      <td>AI Harm Detection</td>
                      <td>1-3 seconds</td>
                      <td>Advanced</td>
                      <td>Low</td>
                    </tr>
                  </tbody>
                </table>
              </div>

              <div className="setting-group">
                <h4>Error Recovery (FEP)</h4>
                <p className="setting-description">
                  When a command fails, press <kbd>Ctrl+F</kbd> to analyze the error and get a suggested fix.
                  This feature uses AI to understand the error and propose a corrected command.
                </p>
              </div>
            </>
          )}

          {/* Usage Tab */}
          {activeTab === 'usage' && (
            <UsageStats />
          )}

          {/* Message */}
          {message && (
            <div className="setting-group" style={{ 
              color: message.type === 'success' ? 'var(--success-color)' : 'var(--error-color)',
              fontSize: '13px',
              padding: '8px 12px',
              borderRadius: '4px',
              backgroundColor: message.type === 'success' ? 'rgba(78, 201, 176, 0.1)' : 'rgba(241, 76, 76, 0.1)',
            }}>
              {message.text}
            </div>
          )}
        </div>

        <div className="settings-footer">
          <button className="btn btn-secondary" onClick={onClose}>
            Cancel
          </button>
          <button 
            className="btn btn-primary" 
            onClick={handleSave}
            disabled={isSaving}
          >
            {isSaving ? 'Saving...' : 'Save'}
          </button>
        </div>
      </div>
    </div>
  );
}
